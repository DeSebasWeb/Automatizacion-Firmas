"""Caso de uso para extraer cédulas de una imagen."""
from typing import List
from PIL import Image

from ...domain.entities import CedulaRecord
from ...domain.ports import OCRPort, LoggerPort


class ExtractCedulasUseCase:
    """
    Caso de uso para extraer números de cédula de una imagen usando OCR.

    Attributes:
        ocr_service: Servicio de OCR
        logger: Servicio de logging
    """

    def __init__(self, ocr_service: OCRPort, logger: LoggerPort):
        """
        Inicializa el caso de uso.

        Args:
            ocr_service: Servicio de OCR
            logger: Servicio de logging
        """
        self.ocr_service = ocr_service
        self.logger = logger.bind(use_case="ExtractCedulas")

    def execute(self, image: Image.Image) -> List[CedulaRecord]:
        """
        Extrae números de cédula de una imagen.

        Args:
            image: Imagen a procesar

        Returns:
            Lista de registros de cédulas extraídas

        Raises:
            ValueError: Si la imagen es inválida
        """
        if image is None:
            self.logger.error("Imagen inválida proporcionada")
            raise ValueError("La imagen no puede ser None")

        self.logger.info(
            "Iniciando extracción de cédulas",
            image_size=(image.width, image.height)
        )

        try:
            # Preprocesar la imagen
            processed_image = self.ocr_service.preprocess_image(image)

            self.logger.debug("Imagen preprocesada para OCR")

            # Extraer cédulas
            records = self.ocr_service.extract_cedulas(processed_image)

            # Filtrar registros válidos
            valid_records = [r for r in records if r.is_valid()]
            invalid_count = len(records) - len(valid_records)

            self.logger.info(
                "Extracción completada",
                total_extracted=len(records),
                valid_records=len(valid_records),
                invalid_records=invalid_count
            )

            if invalid_count > 0:
                self.logger.warning(
                    f"Se descartaron {invalid_count} registros inválidos"
                )

            # Loguear cada cédula extraída
            for record in valid_records:
                self.logger.debug(
                    "Cédula extraída",
                    cedula=record.cedula.value,
                    confidence=record.confidence.as_percentage(),
                    index=record.index
                )

            return valid_records

        except Exception as e:
            self.logger.error("Error durante la extracción de cédulas", error=str(e))
            raise
