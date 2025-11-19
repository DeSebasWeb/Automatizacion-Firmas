"""Servicio de validación fuzzy para comparar nombres manuscritos vs digitales."""
from typing import List, Tuple
import re
from unidecode import unidecode

# Importar Levenshtein con fallback
try:
    from Levenshtein import ratio
    LEVENSHTEIN_AVAILABLE = True
except ImportError:
    # Fallback a implementación básica si Levenshtein no está disponible
    LEVENSHTEIN_AVAILABLE = False
    def ratio(s1: str, s2: str) -> float:
        """Implementación básica de similitud de strings."""
        if s1 == s2:
            return 1.0
        if not s1 or not s2:
            return 0.0
        # Similitud simple basada en caracteres compartidos
        s1_lower = s1.lower()
        s2_lower = s2.lower()
        shared = sum(1 for c in s1_lower if c in s2_lower)
        return shared / max(len(s1), len(s2))

from ...domain.entities import (
    RowData,
    FormData,
    ValidationResult,
    ValidationStatus,
    ValidationAction,
    FieldMatch
)


class FuzzyValidator:
    """
    Validador fuzzy para comparar datos manuscritos vs digitales.

    Utiliza algoritmos de similitud de strings para tolerar errores de OCR.
    """

    def __init__(self, min_similarity: float = 0.85):
        """
        Inicializa el validador.

        Args:
            min_similarity: Umbral mínimo de similitud (0.0-1.0). Default: 0.85 (85%)
        """
        self.min_similarity = min_similarity

    def validate_person(
        self,
        manuscrito_data: RowData,
        digital_data: FormData
    ) -> ValidationResult:
        """
        Valida si los datos manuscritos coinciden con los digitales.

        Criterios de validación:
        - Persona NO encontrada: todos los campos digitales vacíos
        - Validación OK: primer apellido >85% match + al menos un nombre >85%
        - Requiere validación: no cumple criterios anteriores

        Args:
            manuscrito_data: Datos extraídos del formulario manuscrito
            digital_data: Datos extraídos del formulario web

        Returns:
            ValidationResult con status, action, y detalles de comparación
        """
        # CASO 1: Persona no encontrada en base de datos
        if digital_data.is_empty:
            return ValidationResult(
                status=ValidationStatus.ERROR,
                action=ValidationAction.ALERT_NOT_FOUND,
                confidence=0.0,
                details=f"Cédula {manuscrito_data.cedula} no existe en base de datos",
                manuscrito_nombres=manuscrito_data.nombres_manuscritos,
                digital_nombres="[NO ENCONTRADO]"
            )

        # Extraer nombres y apellidos del manuscrito
        nombres_manuscritos = self.extract_nombres_from_full_name(
            manuscrito_data.nombres_manuscritos
        )

        # CASO 2: Comparar con datos encontrados
        matches = {}

        # Comparar primer apellido (OBLIGATORIO)
        primer_apellido_match = self._compare_field(
            manuscrito_nombres,
            digital_data.primer_apellido,
            "primer_apellido"
        )
        matches['primer_apellido'] = primer_apellido_match

        # Comparar todos los nombres manuscritos contra nombres digitales
        # Al menos uno debe coincidir
        nombre_matches = []

        # Comparar contra primer nombre digital
        if digital_data.primer_nombre:
            match = self._compare_any_nombre(
                nombres_manuscritos,
                digital_data.primer_nombre,
                "primer_nombre"
            )
            nombre_matches.append(match)
            matches['primer_nombre'] = match

        # Comparar contra segundo nombre digital (si existe)
        if digital_data.segundo_nombre:
            match = self._compare_any_nombre(
                nombres_manuscritos,
                digital_data.segundo_nombre,
                "segundo_nombre"
            )
            nombre_matches.append(match)
            matches['segundo_nombre'] = match

        # Determinar si al menos un nombre coincide
        any_nombre_match = any(m.match for m in nombre_matches) if nombre_matches else False
        best_nombre_match = max(nombre_matches, key=lambda m: m.similarity) if nombre_matches else None

        # DECISIÓN DE VALIDACIÓN
        apellido_ok = primer_apellido_match.match
        nombre_ok = any_nombre_match

        if apellido_ok and nombre_ok:
            # VALIDACIÓN EXITOSA
            avg_confidence = (
                primer_apellido_match.similarity +
                (best_nombre_match.similarity if best_nombre_match else 0)
            ) / 2

            return ValidationResult(
                status=ValidationStatus.OK,
                action=ValidationAction.AUTO_SAVE,
                confidence=avg_confidence,
                matches=matches,
                details=f"Primer apellido y nombre coinciden (confianza: {avg_confidence:.0%})",
                manuscrito_nombres=manuscrito_data.nombres_manuscritos,
                digital_nombres=digital_data.nombre_completo
            )
        else:
            # REQUIERE VALIDACIÓN MANUAL
            reasons = []
            if not apellido_ok:
                reasons.append(f"Primer apellido no coincide ({primer_apellido_match.similarity:.0%})")
            if not nombre_ok:
                reasons.append("Ningún nombre coincide")

            return ValidationResult(
                status=ValidationStatus.WARNING,
                action=ValidationAction.REQUIRE_VALIDATION,
                confidence=primer_apellido_match.similarity,
                matches=matches,
                details="; ".join(reasons),
                manuscrito_nombres=manuscrito_data.nombres_manuscritos,
                digital_nombres=digital_data.nombre_completo
            )

    def _compare_field(
        self,
        manuscrito_nombres: List[str],
        digital_value: str,
        field_name: str
    ) -> FieldMatch:
        """
        Compara un campo digital contra todos los nombres manuscritos.

        Args:
            manuscrito_nombres: Lista de nombres/apellidos manuscritos
            digital_value: Valor digital a comparar
            field_name: Nombre del campo para debugging

        Returns:
            FieldMatch con el mejor resultado
        """
        if not digital_value or not manuscrito_nombres:
            return FieldMatch(
                match=False,
                similarity=0.0,
                compared=f"[VACÍO] vs {digital_value}",
                field_name=field_name
            )

        # Normalizar valor digital
        digital_normalized = self.normalize_text(digital_value)

        # Comparar contra todos los nombres manuscritos
        best_similarity = 0.0
        best_match_text = ""

        for manuscrito in manuscrito_nombres:
            manuscrito_normalized = self.normalize_text(manuscrito)
            similarity = self.fuzzy_compare(manuscrito_normalized, digital_normalized)

            if similarity > best_similarity:
                best_similarity = similarity
                best_match_text = manuscrito

        return FieldMatch(
            match=best_similarity >= self.min_similarity,
            similarity=best_similarity,
            compared=f"{best_match_text} vs {digital_value}",
            field_name=field_name
        )

    def _compare_any_nombre(
        self,
        manuscrito_nombres: List[str],
        digital_nombre: str,
        field_name: str
    ) -> FieldMatch:
        """
        Compara un nombre digital contra cualquier nombre manuscrito.

        Similar a _compare_field pero específico para nombres.
        """
        return self._compare_field(manuscrito_nombres, digital_nombre, field_name)

    def fuzzy_compare(self, text1: str, text2: str) -> float:
        """
        Compara dos textos usando algoritmo fuzzy.

        Args:
            text1: Primer texto
            text2: Segundo texto

        Returns:
            Similitud entre 0.0 y 1.0
        """
        if not text1 or not text2:
            return 0.0

        if text1 == text2:
            return 1.0

        # Usar Levenshtein si está disponible, sino fallback
        return ratio(text1, text2)

    def normalize_text(self, text: str) -> str:
        """
        Normaliza texto para comparación.

        Elimina:
        - Tildes/acentos
        - Caracteres especiales
        - Espacios extra
        - Convierte a mayúsculas

        Args:
            text: Texto a normalizar

        Returns:
            Texto normalizado
        """
        if not text:
            return ""

        # Eliminar tildes usando unidecode
        text = unidecode(text)

        # Convertir a mayúsculas
        text = text.upper()

        # Eliminar caracteres especiales (solo letras, números, espacios)
        text = re.sub(r'[^A-Z0-9\s]', '', text)

        # Eliminar espacios extra
        text = ' '.join(text.split())

        return text.strip()

    def extract_nombres_from_full_name(self, full_name: str) -> List[str]:
        """
        Extrae nombres individuales del nombre completo manuscrito.

        Args:
            full_name: Nombre completo manuscrito (ej: "MARIA DE JESUS BEJARANO JIMENEZ")

        Returns:
            Lista de nombres/apellidos separados (ej: ["MARIA", "DE", "JESUS", "BEJARANO", "JIMENEZ"])
        """
        if not full_name:
            return []

        # Normalizar
        normalized = self.normalize_text(full_name)

        # Separar por espacios
        partes = normalized.split()

        # Filtrar partes muy cortas (conectores como "DE", "LA", etc.)
        # Pero mantenerlas si es el único contenido
        if len(partes) > 2:
            # Filtrar solo si tenemos suficientes partes
            partes = [p for p in partes if len(p) > 2 or p in ['DE', 'LA', 'DEL', 'LOS', 'LAS']]

        return partes
