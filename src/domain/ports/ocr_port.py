"""Puerto para servicios de OCR."""
from abc import ABC, abstractmethod
from typing import List
from PIL import Image

from ..entities import CedulaRecord


class OCRPort(ABC):
    """
    Interfaz para servicios de reconocimiento óptico de caracteres.

    Extrae números de cédula de imágenes.
    """

    @abstractmethod
    def extract_cedulas(self, image: Image.Image) -> List[CedulaRecord]:
        """
        Extrae números de cédula de una imagen.

        Args:
            image: Imagen PIL a procesar

        Returns:
            Lista de registros de cédulas extraídas
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
