"""Extractor de simbolos de Google Cloud Vision API."""
from dataclasses import dataclass
from typing import List


@dataclass
class Symbol:
    """Representa un simbolo (caracter) con su confianza."""
    text: str
    confidence: float


class GoogleSymbolExtractor:
    """
    Extrae simbolos individuales de respuesta de Google Cloud Vision API.

    Responsabilidad unica: Navegar la estructura jerarquica de Google Vision
    (pages -> blocks -> paragraphs -> words -> symbols) y extraer simbolos
    con sus confianzas.
    """

    @staticmethod
    def extract_all_symbols(response) -> List[Symbol]:
        """
        Extrae todos los simbolos de la respuesta de Google Vision.

        Google Vision estructura:
        - response.full_text_annotation.pages[]
          - .blocks[]
            - .paragraphs[]
              - .words[]
                - .symbols[] <- Aqui estan los caracteres individuales

        Args:
            response: Respuesta de Google Vision document_text_detection

        Returns:
            Lista de Symbol con texto y confianza de cada caracter

        Raises:
            ValueError: Si la respuesta no tiene full_text_annotation
        """
        if not hasattr(response, 'full_text_annotation') or not response.full_text_annotation:
            raise ValueError("Respuesta no tiene full_text_annotation")

        all_symbols = []

        # Navegar estructura jerarquica
        for page in response.full_text_annotation.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        # Obtener confianza de la palabra (fallback)
                        word_confidence = word.confidence if hasattr(word, 'confidence') else 0.95

                        # Extraer cada simbolo
                        for symbol in word.symbols:
                            symbol_conf = (
                                symbol.confidence
                                if hasattr(symbol, 'confidence')
                                else word_confidence
                            )

                            all_symbols.append(
                                Symbol(
                                    text=symbol.text,
                                    confidence=symbol_conf
                                )
                            )

        return all_symbols

    @staticmethod
    def extract_digit_symbols(response) -> List[Symbol]:
        """
        Extrae solo simbolos que son digitos.

        Args:
            response: Respuesta de Google Vision

        Returns:
            Lista de Symbol con solo digitos
        """
        all_symbols = GoogleSymbolExtractor.extract_all_symbols(response)
        return [s for s in all_symbols if s.text.isdigit()]

    @staticmethod
    def get_full_text(symbols: List[Symbol]) -> str:
        """
        Concatena el texto de todos los simbolos.

        Args:
            symbols: Lista de simbolos

        Returns:
            Texto completo
        """
        return ''.join([s.text for s in symbols])

    @staticmethod
    def get_average_confidence(symbols: List[Symbol]) -> float:
        """
        Calcula la confianza promedio de los simbolos.

        Args:
            symbols: Lista de simbolos

        Returns:
            Confianza promedio (0.0-1.0)
        """
        if not symbols:
            return 0.0

        total = sum(s.confidence for s in symbols)
        return total / len(symbols)
