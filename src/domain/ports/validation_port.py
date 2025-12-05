"""Puerto para servicios de validación de datos."""
from abc import ABC, abstractmethod

from ..entities import RowData, FormData, ValidationResult


class ValidationPort(ABC):
    """
    Interfaz para servicios de validación de datos manuscritos vs digitales.

    Los servicios de validación comparan datos extraídos por OCR (manuscritos)
    contra datos digitales de bases de datos, determinando si coinciden.

    Implementaciones:
    - FuzzyValidator: Validación basada en similitud de strings (Levenshtein)
    - ExactValidator: Validación exacta (sin tolerancia a errores)
    - MLValidator: Validación usando modelos de machine learning

    Example:
        >>> validator = FuzzyValidator(min_similarity=0.85)
        >>> result = validator.validate_person(manuscrito_data, digital_data)
        >>> if result.action == ValidationAction.AUTO_SAVE:
        ...     save_to_database(digital_data)
    """

    @abstractmethod
    def validate_person(
        self,
        manuscrito_data: RowData,
        digital_data: FormData
    ) -> ValidationResult:
        """
        Valida si los datos manuscritos coinciden con los digitales.

        Args:
            manuscrito_data: Datos extraídos del formulario manuscrito por OCR
            digital_data: Datos extraídos de la base de datos digital

        Returns:
            ValidationResult con:
                - status: OK, WARNING, ERROR
                - action: AUTO_SAVE, REQUIRE_VALIDATION, ALERT_NOT_FOUND
                - confidence: Score de confianza (0.0 - 1.0)
                - matches: Detalles de comparación por campo
                - details: Mensaje descriptivo del resultado

        Example:
            >>> manuscrito = RowData(
            ...     cedula="12345678",
            ...     nombres_manuscritos="MARIA GARCIA LOPEZ"
            ... )
            >>> digital = FormData(
            ...     primer_nombre="MARIA",
            ...     primer_apellido="GARCIA"
            ... )
            >>> result = validator.validate_person(manuscrito, digital)
            >>> print(result.action)  # ValidationAction.AUTO_SAVE
        """
        pass

    @abstractmethod
    def get_min_similarity_threshold(self) -> float:
        """
        Obtiene el umbral mínimo de similitud configurado.

        Returns:
            Valor entre 0.0 y 1.0 que representa el % mínimo de similitud
            requerido para considerar una coincidencia válida.

        Example:
            >>> validator = FuzzyValidator(min_similarity=0.85)
            >>> validator.get_min_similarity_threshold()
            0.85
        """
        pass

    @abstractmethod
    def set_min_similarity_threshold(self, threshold: float) -> None:
        """
        Configura el umbral mínimo de similitud.

        Args:
            threshold: Nuevo umbral (0.0 - 1.0)

        Raises:
            ValueError: Si threshold está fuera del rango [0.0, 1.0]

        Example:
            >>> validator.set_min_similarity_threshold(0.90)
            >>> validator.get_min_similarity_threshold()
            0.90
        """
        pass
