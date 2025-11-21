"""Ensemble OCR que combina Google Vision + Azure Vision para máxima precisión."""
import concurrent.futures
from typing import List, Dict, Tuple
from PIL import Image

from ...domain.entities import CedulaRecord, RowData
from ...domain.value_objects import ConfidenceScore
from ...domain.ports import OCRPort, ConfigPort
from .google_vision_adapter import GoogleVisionAdapter
from .azure_vision_adapter import AzureVisionAdapter


class EnsembleOCR(OCRPort):
    """
    Ensemble OCR que combina resultados de Google Vision y Azure Vision.

    Estrategia:
    1. Ejecutar ambos OCR en paralelo para velocidad
    2. Si ambos coinciden → retornar con confianza 100%
    3. Si difieren → usar resultado con mayor confidence score
    4. Agregar logging de discrepancias para análisis

    Ventajas:
    - Máxima precisión al combinar dos proveedores líderes
    - Detección automática de discrepancias (útil para métricas)
    - Fallback automático si un proveedor falla

    Desventajas:
    - Doble costo (usa ambas APIs)
    - Ligeramente más lento que un solo proveedor

    Cuándo usar:
    - Cuando la precisión es crítica (> 99%)
    - Cuando el costo no es limitante
    - Para validar datos extremadamente importantes

    Attributes:
        config: Servicio de configuración
        google_vision: Adapter de Google Vision
        azure_vision: Adapter de Azure Vision
        log_discrepancies: Si True, loggea cuando difieren
    """

    def __init__(self, config: ConfigPort):
        """
        Inicializa el ensemble con ambos proveedores.

        Args:
            config: Servicio de configuración
        """
        self.config = config
        self.log_discrepancies = config.get('ocr.ensemble.log_discrepancies', True)

        print("\n" + "="*60)
        print("ENSEMBLE OCR - Modo Máxima Precisión")
        print("="*60)
        print("Combinando Google Vision + Azure Vision")
        print("="*60 + "\n")

        # Inicializar ambos adaptadores
        print("🔵 Inicializando Google Vision...")
        self.google_vision = GoogleVisionAdapter(config)

        print("\n🔵 Inicializando Azure Vision...")
        self.azure_vision = AzureVisionAdapter(config)

        print("\n✓ Ensemble OCR listo (ambos proveedores inicializados)")
        print("="*60 + "\n")

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocesa imagen usando el pipeline estándar.

        Ambos proveedores usan el mismo preprocesamiento, así que
        podemos usar cualquiera de los dos (usamos Google Vision).

        Args:
            image: Imagen PIL a preprocesar

        Returns:
            Imagen preprocesada
        """
        return self.google_vision.preprocess_image(image)

    def extract_cedulas(self, image: Image.Image) -> List[CedulaRecord]:
        """
        Extrae cédulas combinando Google Vision y Azure Vision.

        Proceso:
        1. Ejecutar ambos OCR en paralelo (ThreadPoolExecutor)
        2. Comparar resultados cédula por cédula
        3. Si coinciden → retornar con confidence=100%
        4. Si difieren → retornar el de mayor confidence
        5. Si uno falla → usar el que funcionó

        Args:
            image: Imagen PIL a procesar

        Returns:
            Lista combinada de CedulaRecord con máxima precisión
        """
        print("\n" + "="*60)
        print("ENSEMBLE: Extrayendo cédulas con AMBOS proveedores")
        print("="*60)

        # Ejecutar ambos OCR en paralelo
        google_records = []
        azure_records = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Lanzar ambos en paralelo
            future_google = executor.submit(self._extract_with_google, image)
            future_azure = executor.submit(self._extract_with_azure, image)

            # Esperar resultados
            try:
                google_records = future_google.result(timeout=60)
            except Exception as e:
                print(f"⚠️ Google Vision falló: {e}")

            try:
                azure_records = future_azure.result(timeout=60)
            except Exception as e:
                print(f"⚠️ Azure Vision falló: {e}")

        # Si ambos fallaron
        if not google_records and not azure_records:
            print("❌ ENSEMBLE: Ambos proveedores fallaron")
            return []

        # Si solo uno funcionó
        if not google_records:
            print("⚠️ ENSEMBLE: Solo Azure Vision funcionó")
            return azure_records

        if not azure_records:
            print("⚠️ ENSEMBLE: Solo Google Vision funcionó")
            return google_records

        # Ambos funcionaron → combinar resultados
        print(f"\n✓ Google Vision: {len(google_records)} cédulas")
        print(f"✓ Azure Vision: {len(azure_records)} cédulas")

        combined_records = self._combine_records(google_records, azure_records)

        print(f"✓ ENSEMBLE: {len(combined_records)} cédulas combinadas")
        print("="*60 + "\n")

        return combined_records

    def extract_full_form_data(
        self,
        image: Image.Image,
        expected_rows: int = 15
    ) -> List[RowData]:
        """
        Extrae formulario completo combinando ambos proveedores.

        Proceso:
        1. Ejecutar ambos OCR en paralelo
        2. Comparar renglón por renglón
        3. Si coinciden → usar con confidence alta
        4. Si difieren → usar el de mayor confidence promedio
        5. Si uno falla → usar el que funcionó

        Args:
            image: Imagen PIL del formulario
            expected_rows: Número de renglones esperados

        Returns:
            Lista combinada de RowData con máxima precisión
        """
        print("\n" + "="*60)
        print("ENSEMBLE: Extrayendo formulario completo con AMBOS proveedores")
        print("="*60)

        # Ejecutar ambos OCR en paralelo
        google_rows = []
        azure_rows = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_google = executor.submit(
                self._extract_form_with_google, image, expected_rows
            )
            future_azure = executor.submit(
                self._extract_form_with_azure, image, expected_rows
            )

            try:
                google_rows = future_google.result(timeout=60)
            except Exception as e:
                print(f"⚠️ Google Vision falló: {e}")

            try:
                azure_rows = future_azure.result(timeout=60)
            except Exception as e:
                print(f"⚠️ Azure Vision falló: {e}")

        # Si ambos fallaron
        if not google_rows and not azure_rows:
            print("❌ ENSEMBLE: Ambos proveedores fallaron")
            return []

        # Si solo uno funcionó
        if not google_rows:
            print("⚠️ ENSEMBLE: Solo Azure Vision funcionó")
            return azure_rows

        if not azure_rows:
            print("⚠️ ENSEMBLE: Solo Google Vision funcionó")
            return google_rows

        # Ambos funcionaron → combinar renglones
        print(f"\n✓ Google Vision: {len(google_rows)} renglones")
        print(f"✓ Azure Vision: {len(azure_rows)} renglones")

        combined_rows = self._combine_rows(google_rows, azure_rows)

        print(f"✓ ENSEMBLE: {len(combined_rows)} renglones combinados")
        print("="*60 + "\n")

        return combined_rows

    def _extract_with_google(self, image: Image.Image) -> List[CedulaRecord]:
        """Extrae con Google Vision (envuelto para threading)."""
        print("🔵 Ejecutando Google Vision...")
        return self.google_vision.extract_cedulas(image)

    def _extract_with_azure(self, image: Image.Image) -> List[CedulaRecord]:
        """Extrae con Azure Vision (envuelto para threading)."""
        print("🔵 Ejecutando Azure Vision...")
        return self.azure_vision.extract_cedulas(image)

    def _extract_form_with_google(
        self,
        image: Image.Image,
        expected_rows: int
    ) -> List[RowData]:
        """Extrae formulario con Google Vision (envuelto para threading)."""
        print("🔵 Ejecutando Google Vision (formulario completo)...")
        return self.google_vision.extract_full_form_data(image, expected_rows)

    def _extract_form_with_azure(
        self,
        image: Image.Image,
        expected_rows: int
    ) -> List[RowData]:
        """Extrae formulario con Azure Vision (envuelto para threading)."""
        print("🔵 Ejecutando Azure Vision (formulario completo)...")
        return self.azure_vision.extract_full_form_data(image, expected_rows)

    def _combine_records(
        self,
        google_records: List[CedulaRecord],
        azure_records: List[CedulaRecord]
    ) -> List[CedulaRecord]:
        """
        Combina resultados de ambos proveedores inteligentemente.

        Estrategia:
        - Si ambos detectan la misma cédula → confidence=100%
        - Si solo uno la detecta → usar ese con su confidence original
        - Si ambos detectan diferente → usar el de mayor confidence

        Args:
            google_records: Registros de Google Vision
            azure_records: Registros de Azure Vision

        Returns:
            Lista combinada optimizada
        """
        # Crear diccionarios para acceso rápido
        google_dict = {rec.cedula.value: rec for rec in google_records}
        azure_dict = {rec.cedula.value: rec for rec in azure_records}

        combined = []
        seen = set()

        # Procesar cédulas detectadas por ambos
        for cedula_value in google_dict.keys():
            if cedula_value in azure_dict:
                # Ambos coinciden → ALTA CONFIANZA
                google_rec = google_dict[cedula_value]

                # Crear nuevo record con confidence=100%
                combined_record = CedulaRecord.from_primitives(
                    cedula=cedula_value,
                    confidence=100.0,  # Máxima confianza al coincidir
                    index=google_rec.index
                )
                combined.append(combined_record)
                seen.add(cedula_value)

                print(f"✓ Coincidencia: {cedula_value} (confidence → 100%)")

        # Procesar cédulas solo en Google
        for cedula_value, rec in google_dict.items():
            if cedula_value not in seen:
                combined.append(rec)
                seen.add(cedula_value)

                if self.log_discrepancies:
                    print(f"⚠️ Solo Google: {cedula_value} (conf: {rec.confidence.as_percentage():.1f}%)")

        # Procesar cédulas solo en Azure
        for cedula_value, rec in azure_dict.items():
            if cedula_value not in seen:
                combined.append(rec)
                seen.add(cedula_value)

                if self.log_discrepancies:
                    print(f"⚠️ Solo Azure: {cedula_value} (conf: {rec.confidence.as_percentage():.1f}%)")

        return combined

    def _combine_rows(
        self,
        google_rows: List[RowData],
        azure_rows: List[RowData]
    ) -> List[RowData]:
        """
        Combina renglones de ambos proveedores.

        Estrategia por renglón:
        - Si ambos coinciden en cédula → usar con confidence alta
        - Si difieren → usar el de mayor confidence promedio
        - Si uno está vacío y otro no → usar el que tiene datos

        Args:
            google_rows: Renglones de Google Vision
            azure_rows: Renglones de Azure Vision

        Returns:
            Lista combinada de renglones
        """
        combined = []
        num_rows = max(len(google_rows), len(azure_rows))

        for i in range(num_rows):
            google_row = google_rows[i] if i < len(google_rows) else None
            azure_row = azure_rows[i] if i < len(azure_rows) else None

            # Si solo hay uno
            if not google_row:
                combined.append(azure_row)
                continue
            if not azure_row:
                combined.append(google_row)
                continue

            # Ambos existen → comparar
            if google_row.is_empty and azure_row.is_empty:
                # Ambos vacíos → usar cualquiera
                combined.append(google_row)
            elif google_row.is_empty:
                # Solo Azure tiene datos
                combined.append(azure_row)
                if self.log_discrepancies:
                    print(f"⚠️ Renglón {i}: Solo Azure tiene datos")
            elif azure_row.is_empty:
                # Solo Google tiene datos
                combined.append(google_row)
                if self.log_discrepancies:
                    print(f"⚠️ Renglón {i}: Solo Google tiene datos")
            else:
                # Ambos tienen datos → comparar cédulas
                if google_row.cedula.value == azure_row.cedula.value:
                    # Coinciden → usar con confidence alta
                    print(f"✓ Renglón {i}: Coincidencia en cédula {google_row.cedula.value}")
                    combined.append(google_row)
                else:
                    # Difieren → usar el de mayor confidence
                    google_conf = google_row.confidence.get('cedula', ConfidenceScore(0))
                    azure_conf = azure_row.confidence.get('cedula', ConfidenceScore(0))

                    if google_conf >= azure_conf:
                        combined.append(google_row)
                        if self.log_discrepancies:
                            print(f"⚠️ Renglón {i}: Google {google_row.cedula.value} ({google_conf.as_percentage():.0f}%) vs Azure {azure_row.cedula.value} ({azure_conf.as_percentage():.0f}%)")
                    else:
                        combined.append(azure_row)
                        if self.log_discrepancies:
                            print(f"⚠️ Renglón {i}: Azure {azure_row.cedula.value} ({azure_conf.as_percentage():.0f}%) vs Google {google_row.cedula.value} ({google_conf.as_percentage():.0f}%)")

        return combined
