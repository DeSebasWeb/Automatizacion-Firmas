"""Tests unitarios para FuzzyValidator.

Cobertura:
- Implementación de ValidationPort
- Normalización de texto
- Comparación fuzzy de nombres
- Validación de personas completas
- Caching de normalización
- Configuración de umbral
"""

import pytest
from unittest.mock import Mock

from src.application.services.fuzzy_validator import FuzzyValidator
from src.domain.entities import RowData, FormData, ValidationAction
from src.domain.ports import ValidationPort


class TestFuzzyValidatorInterface:
    """Tests de implementación de ValidationPort interface."""

    def test_implements_validation_port(self):
        """Verifica que FuzzyValidator implementa ValidationPort."""
        validator = FuzzyValidator()
        assert isinstance(validator, ValidationPort)

    def test_has_required_methods(self):
        """Verifica que tiene todos los métodos requeridos."""
        validator = FuzzyValidator()

        # Métodos de ValidationPort
        assert hasattr(validator, 'validate_person')
        assert callable(validator.validate_person)

        assert hasattr(validator, 'get_min_similarity_threshold')
        assert callable(validator.get_min_similarity_threshold)

        assert hasattr(validator, 'set_min_similarity_threshold')
        assert callable(validator.set_min_similarity_threshold)


class TestFuzzyValidatorInitialization:
    """Tests de inicialización y configuración."""

    def test_default_initialization(self):
        """Test inicialización con valores por defecto."""
        validator = FuzzyValidator()
        assert validator.min_similarity == 0.85

    def test_custom_similarity_threshold(self):
        """Test inicialización con umbral personalizado."""
        validator = FuzzyValidator(min_similarity=0.90)
        assert validator.min_similarity == 0.90

    def test_invalid_threshold_too_low(self):
        """Test que rechaza umbral < 0.0."""
        with pytest.raises(ValueError, match="min_similarity debe estar entre 0.0 y 1.0"):
            FuzzyValidator(min_similarity=-0.1)

    def test_invalid_threshold_too_high(self):
        """Test que rechaza umbral > 1.0."""
        with pytest.raises(ValueError, match="min_similarity debe estar entre 0.0 y 1.0"):
            FuzzyValidator(min_similarity=1.5)

    def test_edge_case_threshold_zero(self):
        """Test que acepta umbral = 0.0."""
        validator = FuzzyValidator(min_similarity=0.0)
        assert validator.min_similarity == 0.0

    def test_edge_case_threshold_one(self):
        """Test que acepta umbral = 1.0."""
        validator = FuzzyValidator(min_similarity=1.0)
        assert validator.min_similarity == 1.0


class TestThresholdMethods:
    """Tests de getters y setters de umbral."""

    def test_get_min_similarity_threshold(self):
        """Test getter de umbral."""
        validator = FuzzyValidator(min_similarity=0.75)
        assert validator.get_min_similarity_threshold() == 0.75

    def test_set_min_similarity_threshold(self):
        """Test setter de umbral."""
        validator = FuzzyValidator(min_similarity=0.85)
        validator.set_min_similarity_threshold(0.90)
        assert validator.get_min_similarity_threshold() == 0.90

    def test_set_invalid_threshold(self):
        """Test que setter rechaza valores inválidos."""
        validator = FuzzyValidator()

        with pytest.raises(ValueError):
            validator.set_min_similarity_threshold(-0.1)

        with pytest.raises(ValueError):
            validator.set_min_similarity_threshold(1.5)

    def test_set_threshold_clears_cache(self):
        """Test que cambiar umbral invalida el cache."""
        validator = FuzzyValidator()

        # Normalizar un texto (cachea)
        text1 = validator.normalize_text("José María")
        assert "José María" in validator._normalized_cache

        # Cambiar umbral
        validator.set_min_similarity_threshold(0.90)

        # Cache debe estar vacío
        assert len(validator._normalized_cache) == 0


class TestNormalizeText:
    """Tests de normalización de texto."""

    def test_normalize_removes_accents(self):
        """Test que remueve acentos."""
        validator = FuzzyValidator()
        result = validator.normalize_text("José María Ñoño")
        assert result == "JOSE MARIA NONO"

    def test_normalize_uppercases(self):
        """Test que convierte a mayúsculas."""
        validator = FuzzyValidator()
        result = validator.normalize_text("juan pérez")
        assert result == "JUAN PEREZ"

    def test_normalize_removes_special_chars(self):
        """Test que remueve caracteres especiales."""
        validator = FuzzyValidator()
        result = validator.normalize_text("O'Brien-Smith")
        assert result == "OBRIENSMITH"

    def test_normalize_collapses_whitespace(self):
        """Test que colapsa espacios múltiples."""
        validator = FuzzyValidator()
        result = validator.normalize_text("Juan    Carlos   Pérez")
        assert result == "JUAN CARLOS PEREZ"

    def test_normalize_strips_whitespace(self):
        """Test que remueve espacios al inicio y final."""
        validator = FuzzyValidator()
        result = validator.normalize_text("  Juan Pérez  ")
        assert result == "JUAN PEREZ"

    def test_normalize_empty_string(self):
        """Test que maneja string vacío."""
        validator = FuzzyValidator()
        result = validator.normalize_text("")
        assert result == ""

    def test_normalize_none(self):
        """Test que maneja None."""
        validator = FuzzyValidator()
        result = validator.normalize_text(None)
        assert result == ""

    def test_normalize_keeps_numbers(self):
        """Test que mantiene números."""
        validator = FuzzyValidator()
        result = validator.normalize_text("Juan 123")
        assert result == "JUAN 123"

    def test_normalize_caches_results(self):
        """Test que cachea resultados de normalización."""
        validator = FuzzyValidator()

        # Primera normalización
        text1 = validator.normalize_text("José María")
        assert "José María" in validator._normalized_cache
        assert validator._normalized_cache["José María"] == "JOSE MARIA"

        # Segunda normalización (debe usar cache)
        text2 = validator.normalize_text("José María")
        assert text1 == text2

        # Verificar que el cache tiene solo 1 entrada
        assert len(validator._normalized_cache) == 1


class TestCompareNombres:
    """Tests de comparación fuzzy de nombres."""

    def test_exact_match(self):
        """Test con nombres idénticos."""
        validator = FuzzyValidator()
        similarity = validator._compare_nombres("JUAN PEREZ", "JUAN PEREZ")
        assert similarity == 1.0

    def test_high_similarity(self):
        """Test con nombres muy similares."""
        validator = FuzzyValidator()
        similarity = validator._compare_nombres("JUAN PEREZ", "JUAN PERES")
        assert similarity > 0.90

    def test_low_similarity(self):
        """Test con nombres muy diferentes."""
        validator = FuzzyValidator()
        similarity = validator._compare_nombres("JUAN PEREZ", "MARIA GOMEZ")
        assert similarity < 0.50

    def test_with_accents(self):
        """Test que normaliza antes de comparar."""
        validator = FuzzyValidator()
        # Deben ser idénticos después de normalizar
        similarity = validator._compare_nombres("José María", "Jose Maria")
        assert similarity == 1.0

    def test_case_insensitive(self):
        """Test que ignora mayúsculas/minúsculas."""
        validator = FuzzyValidator()
        similarity = validator._compare_nombres("juan perez", "JUAN PEREZ")
        assert similarity == 1.0

    def test_with_extra_whitespace(self):
        """Test que ignora espacios extra."""
        validator = FuzzyValidator()
        similarity = validator._compare_nombres("Juan   Perez", "Juan Perez")
        assert similarity == 1.0

    def test_partial_match(self):
        """Test con match parcial."""
        validator = FuzzyValidator()
        # "JUAN" vs "JUAN CARLOS" debería tener similitud parcial
        similarity = validator._compare_nombres("JUAN", "JUAN CARLOS")
        assert 0.5 < similarity < 1.0


class TestValidatePerson:
    """Tests de validación completa de persona."""

    def test_perfect_match_auto_saves(self):
        """Test que match perfecto resulta en AUTO_SAVE."""
        validator = FuzzyValidator(min_similarity=0.85)

        manuscrito = RowData(
            cedula="123456789",
            nombres_manuscritos="JUAN PEREZ GOMEZ"
        )

        digital = FormData(
            primer_nombre="JUAN",
            segundo_nombre="",
            primer_apellido="PEREZ",
            segundo_apellido="GOMEZ"
        )

        result = validator.validate_person(manuscrito, digital)

        assert result.action == ValidationAction.AUTO_SAVE
        assert result.confidence >= 0.85
        assert result.is_valid

    def test_high_confidence_auto_saves(self):
        """Test que alta confianza resulta en AUTO_SAVE."""
        validator = FuzzyValidator(min_similarity=0.85)

        manuscrito = RowData(
            cedula="123456789",
            nombres_manuscritos="JUAN PERES GOMES"  # Pequeño typo
        )

        digital = FormData(
            primer_nombre="JUAN",
            segundo_nombre="",
            primer_apellido="PEREZ",
            segundo_apellido="GOMEZ"
        )

        result = validator.validate_person(manuscrito, digital)

        # Debería ser muy similar (>85%)
        assert result.confidence > 0.85
        assert result.action == ValidationAction.AUTO_SAVE

    def test_low_confidence_requires_validation(self):
        """Test que baja confianza requiere validación."""
        validator = FuzzyValidator(min_similarity=0.85)

        manuscrito = RowData(
            cedula="123456789",
            nombres_manuscritos="JUAN PEREZ"
        )

        digital = FormData(
            primer_nombre="MARIA",  # Nombre completamente diferente
            segundo_nombre="",
            primer_apellido="GOMEZ",
            segundo_apellido="LOPEZ"
        )

        result = validator.validate_person(manuscrito, digital)

        assert result.confidence < 0.85
        assert result.action == ValidationAction.REQUIRE_VALIDATION
        assert not result.is_valid

    def test_empty_digital_data_not_found(self):
        """Test que datos digitales vacíos resultan en NOT_FOUND."""
        validator = FuzzyValidator()

        manuscrito = RowData(
            cedula="123456789",
            nombres_manuscritos="JUAN PEREZ"
        )

        digital = FormData(
            primer_nombre="",
            segundo_nombre="",
            primer_apellido="",
            segundo_apellido=""
        )

        result = validator.validate_person(manuscrito, digital)

        assert result.action == ValidationAction.ALERT_NOT_FOUND
        assert result.confidence == 0.0
        assert not result.is_valid

    def test_with_segundo_nombre(self):
        """Test validación con segundo nombre."""
        validator = FuzzyValidator(min_similarity=0.85)

        manuscrito = RowData(
            cedula="123456789",
            nombres_manuscritos="JUAN CARLOS PEREZ GOMEZ"
        )

        digital = FormData(
            primer_nombre="JUAN",
            segundo_nombre="CARLOS",
            primer_apellido="PEREZ",
            segundo_apellido="GOMEZ"
        )

        result = validator.validate_person(manuscrito, digital)

        assert result.action == ValidationAction.AUTO_SAVE
        assert result.confidence >= 0.95  # Match perfecto

    def test_missing_segundo_nombre_still_matches(self):
        """Test que falta de segundo nombre no rompe validación."""
        validator = FuzzyValidator(min_similarity=0.85)

        manuscrito = RowData(
            cedula="123456789",
            nombres_manuscritos="JUAN PEREZ GOMEZ"
        )

        digital = FormData(
            primer_nombre="JUAN",
            segundo_nombre="CARLOS",  # Extra en digital
            primer_apellido="PEREZ",
            segundo_apellido="GOMEZ"
        )

        result = validator.validate_person(manuscrito, digital)

        # Debería tener alta similitud aunque falte el segundo nombre
        assert result.confidence > 0.75

    def test_threshold_affects_validation(self):
        """Test que el umbral afecta el resultado."""
        manuscrito = RowData(
            cedula="123456789",
            nombres_manuscritos="JUAN PERES"  # Typo leve
        )

        digital = FormData(
            primer_nombre="JUAN",
            segundo_nombre="",
            primer_apellido="PEREZ",
            segundo_apellido=""
        )

        # Con umbral bajo (0.70) debería pasar
        validator_low = FuzzyValidator(min_similarity=0.70)
        result_low = validator_low.validate_person(manuscrito, digital)
        assert result_low.action == ValidationAction.AUTO_SAVE

        # Con umbral alto (0.99) debería fallar
        validator_high = FuzzyValidator(min_similarity=0.99)
        result_high = validator_high.validate_person(manuscrito, digital)
        assert result_high.action == ValidationAction.REQUIRE_VALIDATION


class TestValidationResultDetails:
    """Tests de detalles en ValidationResult."""

    def test_result_has_confidence(self):
        """Test que el resultado incluye confidence."""
        validator = FuzzyValidator()

        manuscrito = RowData(cedula="123", nombres_manuscritos="JUAN PEREZ")
        digital = FormData(
            primer_nombre="JUAN",
            segundo_nombre="",
            primer_apellido="PEREZ",
            segundo_apellido=""
        )

        result = validator.validate_person(manuscrito, digital)

        assert hasattr(result, 'confidence')
        assert 0.0 <= result.confidence <= 1.0

    def test_result_has_action(self):
        """Test que el resultado incluye action."""
        validator = FuzzyValidator()

        manuscrito = RowData(cedula="123", nombres_manuscritos="JUAN PEREZ")
        digital = FormData(
            primer_nombre="JUAN",
            segundo_nombre="",
            primer_apellido="PEREZ",
            segundo_apellido=""
        )

        result = validator.validate_person(manuscrito, digital)

        assert hasattr(result, 'action')
        assert isinstance(result.action, ValidationAction)

    def test_result_has_details(self):
        """Test que el resultado incluye detalles."""
        validator = FuzzyValidator()

        manuscrito = RowData(cedula="123", nombres_manuscritos="JUAN PEREZ")
        digital = FormData(
            primer_nombre="JUAN",
            segundo_nombre="",
            primer_apellido="PEREZ",
            segundo_apellido=""
        )

        result = validator.validate_person(manuscrito, digital)

        assert hasattr(result, 'details')
        assert isinstance(result.details, dict)


class TestEdgeCases:
    """Tests de casos extremos."""

    def test_very_long_names(self):
        """Test con nombres muy largos."""
        validator = FuzzyValidator()

        manuscrito = RowData(
            cedula="123",
            nombres_manuscritos="JUAN CARLOS SEBASTIAN ALEJANDRO PEREZ GOMEZ LOPEZ MARTINEZ"
        )

        digital = FormData(
            primer_nombre="JUAN CARLOS SEBASTIAN",
            segundo_nombre="ALEJANDRO",
            primer_apellido="PEREZ GOMEZ",
            segundo_apellido="LOPEZ MARTINEZ"
        )

        result = validator.validate_person(manuscrito, digital)

        # No debe crashear
        assert hasattr(result, 'confidence')

    def test_single_char_names(self):
        """Test con nombres de un solo carácter."""
        validator = FuzzyValidator()

        manuscrito = RowData(cedula="123", nombres_manuscritos="J P")
        digital = FormData(
            primer_nombre="J",
            segundo_nombre="",
            primer_apellido="P",
            segundo_apellido=""
        )

        result = validator.validate_person(manuscrito, digital)

        assert result.action in [ValidationAction.AUTO_SAVE, ValidationAction.REQUIRE_VALIDATION]

    def test_only_numbers_in_names(self):
        """Test con nombres que contienen números."""
        validator = FuzzyValidator()

        manuscrito = RowData(cedula="123", nombres_manuscritos="JUAN 2 PEREZ")
        digital = FormData(
            primer_nombre="JUAN",
            segundo_nombre="2",
            primer_apellido="PEREZ",
            segundo_apellido=""
        )

        result = validator.validate_person(manuscrito, digital)

        # Debería funcionar (números se mantienen)
        assert hasattr(result, 'confidence')

    def test_names_with_special_unicode(self):
        """Test con caracteres unicode especiales."""
        validator = FuzzyValidator()

        manuscrito = RowData(cedula="123", nombres_manuscritos="Ñoño Örnëïl")
        digital = FormData(
            primer_nombre="NONO",  # Normalizado
            segundo_nombre="",
            primer_apellido="ORNEIL",  # Normalizado
            segundo_apellido=""
        )

        result = validator.validate_person(manuscrito, digital)

        # Debería tener alta similitud después de normalizar
        assert result.confidence > 0.85


# Fixtures para reutilizar en tests
@pytest.fixture
def validator():
    """Fixture de validator con configuración estándar."""
    return FuzzyValidator(min_similarity=0.85)


@pytest.fixture
def manuscrito_standard():
    """Fixture de datos manuscritos estándar."""
    return RowData(
        cedula="123456789",
        nombres_manuscritos="JUAN CARLOS PEREZ GOMEZ"
    )


@pytest.fixture
def digital_standard():
    """Fixture de datos digitales estándar."""
    return FormData(
        primer_nombre="JUAN",
        segundo_nombre="CARLOS",
        primer_apellido="PEREZ",
        segundo_apellido="GOMEZ"
    )
