"""
Process E-14 with Textract Use Case.

Caso de uso para procesar formularios E-14 usando AWS Textract.
"""

import structlog
from typing import Dict, Any, Optional
from PIL import Image
from pathlib import Path
import json
from datetime import datetime

from src.infrastructure.ocr.textract.textract_adapter import TextractAdapter
from src.infrastructure.ocr.textract.e14_textract_parser import E14TextractParser

logger = structlog.get_logger(__name__)


class ProcessE14TextractUseCase:
    """
    Caso de uso: Procesar formulario E-14 con AWS Textract.

    Flujo:
    1. Recibir imagen de formulario E-14
    2. Extraer texto usando AWS Textract
    3. Parsear texto a estructura JSON
    4. Guardar resultado en data/results/
    5. Retornar JSON estructurado + texto OCR raw

    Principios SOLID:
    - SRP: Responsabilidad única de orquestar procesamiento E-14
    - DIP: Depende de abstracciones (TextractAdapter, Parser)
    - OCP: Extensible para agregar más validaciones/transformaciones
    """

    def __init__(
        self,
        textract_adapter: TextractAdapter,
        results_dir: str = "data/results"
    ):
        """
        Inicializa el caso de uso.

        Args:
            textract_adapter: Adaptador de AWS Textract
            results_dir: Directorio donde guardar resultados
        """
        self.textract_adapter = textract_adapter
        self.parser = E14TextractParser()
        self.results_dir = Path(results_dir)
        self.logger = logger.bind(use_case="process_e14_textract")

        # Crear directorio de resultados si no existe
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def execute(
        self,
        image: Image.Image,
        save_result: bool = True
    ) -> Dict[str, Any]:
        """
        Ejecuta el procesamiento de un formulario E-14.

        Args:
            image: Imagen PIL del formulario E-14
            save_result: Si True, guarda el resultado en data/results/

        Returns:
            Diccionario con:
            - structured_data: Datos estructurados en formato JSON
            - raw_ocr_text: Texto extraído por Textract (sin procesar)
            - warnings: Lista de advertencias/campos que necesitan auditoría
            - processing_time_ms: Tiempo de procesamiento en milisegundos
        """
        start_time = datetime.now()

        self.logger.info("processing_e14_started", image_size=f"{image.width}x{image.height}")

        # Paso 1: Extraer texto con Textract
        raw_text = self.textract_adapter.extract_text_from_image(image)

        if not raw_text:
            self.logger.error("textract_extraction_failed")
            return {
                "structured_data": None,
                "raw_ocr_text": "",
                "warnings": ["AWS Textract no pudo extraer texto de la imagen"],
                "processing_time_ms": 0,
                "success": False
            }

        self.logger.info("textract_extraction_completed", text_length=len(raw_text))

        # Paso 2: Parsear texto a estructura JSON
        try:
            structured_data = self.parser.parse(raw_text)
            warnings = self.parser.warnings

            self.logger.info(
                "e14_parsing_completed",
                partidos_count=len(structured_data["e14"]["Partido"]),
                warnings_count=len(warnings)
            )

        except Exception as e:
            self.logger.error("parsing_failed", error=str(e), error_type=type(e).__name__)
            return {
                "structured_data": None,
                "raw_ocr_text": raw_text,
                "warnings": [f"Error al parsear: {str(e)}"],
                "processing_time_ms": 0,
                "success": False
            }

        # Calcular tiempo de procesamiento
        end_time = datetime.now()
        processing_time_ms = int((end_time - start_time).total_seconds() * 1000)

        # Paso 3: Guardar resultado (opcional)
        if save_result:
            self._save_result(structured_data, raw_text, warnings)

        # Retornar resultado completo
        return {
            "structured_data": structured_data,
            "raw_ocr_text": raw_text,
            "warnings": warnings,
            "processing_time_ms": processing_time_ms,
            "success": True
        }

    def _save_result(
        self,
        structured_data: Dict[str, Any],
        raw_text: str,
        warnings: list
    ) -> None:
        """
        Guarda el resultado del procesamiento en disco.

        Crea 3 archivos:
        - {timestamp}_structured.json: Datos estructurados
        - {timestamp}_raw_ocr.txt: Texto crudo de Textract
        - {timestamp}_warnings.txt: Advertencias

        Args:
            structured_data: Datos estructurados
            raw_text: Texto OCR crudo
            warnings: Lista de advertencias
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Guardar JSON estructurado
        json_file = self.results_dir / f"{timestamp}_e14_structured.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, ensure_ascii=False, indent=2)

        self.logger.info("structured_data_saved", file=str(json_file))

        # Guardar texto OCR crudo
        raw_file = self.results_dir / f"{timestamp}_e14_raw_ocr.txt"
        with open(raw_file, 'w', encoding='utf-8') as f:
            f.write(raw_text)

        self.logger.info("raw_ocr_saved", file=str(raw_file))

        # Guardar advertencias
        if warnings:
            warnings_file = self.results_dir / f"{timestamp}_e14_warnings.txt"
            with open(warnings_file, 'w', encoding='utf-8') as f:
                f.write("CAMPOS QUE NECESITAN AUDITORÍA:\n\n")
                for warning in warnings:
                    f.write(f"- {warning}\n")

            self.logger.info("warnings_saved", file=str(warnings_file), count=len(warnings))
