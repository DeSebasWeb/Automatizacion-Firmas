"""Puerto para servicios de OCR."""
from abc import ABC, abstractmethod
from typing import List
from PIL import Image

from ..entities import CedulaRecord, RowData


class OCRPort(ABC):
    """
    Interfaz para servicios de reconocimiento óptico de caracteres.

    Soporta dos modos de extracción:
    1. Legacy: Solo extracción de cédulas (extract_cedulas)
    2. Dual OCR: Extracción completa de nombres + cédulas por renglón (extract_full_form_data)
    """

    @abstractmethod
    def extract_cedulas(self, image: Image.Image) -> List[CedulaRecord]:
        """
        Extrae números de cédula de una imagen (modo legacy).

        Este método es el original del sistema, usado para extracción simple
        de cédulas sin nombres asociados.

        Args:
            image: Imagen PIL a procesar

        Returns:
            Lista de registros de cédulas extraídas

        Note:
            Para sistemas nuevos, considere usar extract_full_form_data()
        """
        pass

    @abstractmethod
    def extract_full_form_data(
        self,
        image: Image.Image,
        expected_rows: int = 15
    ) -> List[RowData]:
        """
        Extrae datos completos del formulario (nombres + cédulas) por renglón.

        Este método soporta el sistema OCR dual, extrayendo tanto nombres
        manuscritos como números de cédula, organizados por renglones.

        Args:
            image: Imagen PIL del formulario completo a procesar
            expected_rows: Número esperado de renglones en el formulario

        Returns:
            Lista de RowData, uno por cada renglón detectado.
            Los renglones vacíos tienen is_empty=True.

        Raises:
            OCRExtractionError: Si hay un error crítico durante la extracción

        Example:
            >>> rows = ocr_adapter.extract_full_form_data(form_image, expected_rows=15)
            >>> for row in rows:
            ...     if not row.is_empty:
            ...         print(f"{row.nombres_manuscritos} - {row.cedula}")
        """
        pass

    @abstractmethod
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocesa una imagen para mejorar el OCR.

        Args:
            image: Imagen PIL a preprocesar

        Returns:
            Imagen preprocesada
        """
        pass
