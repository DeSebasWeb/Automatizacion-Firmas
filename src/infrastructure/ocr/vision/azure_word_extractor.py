"""Extractor de palabras de Azure Computer Vision Read API."""
from dataclasses import dataclass
from typing import List


@dataclass
class Word:
    """Representa una palabra con su confianza."""
    text: str
    confidence: float


class AzureWordExtractor:
    """
    Extrae palabras de respuesta de Azure Computer Vision Read API.

    Responsabilidad unica: Navegar la estructura de Azure Vision
    (result.read.blocks[] -> lines[] -> words[]) y extraer palabras
    con sus confianzas.

    NOTA: Azure Vision v4.0 da confianza a nivel de palabra, no de caracter.
    Por eso este extractor trabaja con palabras en lugar de simbolos.
    """

    @staticmethod
    def extract_all_words(result) -> List[Word]:
        """
        Extrae todas las palabras de la respuesta de Azure Vision.

        Azure Vision estructura:
        - result.read.blocks[]
          - .lines[]
            - .words[] <- Aqui estan las palabras con confianza

        Args:
            result: Resultado de Azure analyze() con feature READ

        Returns:
            Lista de Word con texto y confianza de cada palabra

        Raises:
            ValueError: Si el resultado no tiene datos de lectura
        """
        if not hasattr(result, 'read') or not result.read:
            raise ValueError("Resultado no tiene datos de lectura")

        if not hasattr(result.read, 'blocks') or not result.read.blocks:
            raise ValueError("Resultado no tiene bloques de texto")

        all_words = []

        # Navegar estructura de Azure
        for block in result.read.blocks:
            for line in block.lines:
                # Verificar si la linea tiene palabras
                if hasattr(line, 'words') and line.words:
                    for word in line.words:
                        word_text = word.text
                        word_confidence = (
                            word.confidence
                            if hasattr(word, 'confidence')
                            else 0.95
                        )

                        all_words.append(
                            Word(
                                text=word_text,
                                confidence=word_confidence
                            )
                        )

        return all_words

    @staticmethod
    def extract_numeric_words(result) -> List[Word]:
        """
        Extrae solo palabras que contienen digitos.

        Args:
            result: Resultado de Azure Vision

        Returns:
            Lista de Word con solo palabras numericas
        """
        all_words = AzureWordExtractor.extract_all_words(result)
        return [w for w in all_words if any(c.isdigit() for c in w.text)]

    @staticmethod
    def get_full_text(words: List[Word]) -> str:
        """
        Concatena el texto de todas las palabras.

        Args:
            words: Lista de palabras

        Returns:
            Texto completo concatenado
        """
        return ''.join([w.text for w in words])

    @staticmethod
    def get_average_confidence(words: List[Word]) -> float:
        """
        Calcula la confianza promedio de las palabras.

        Args:
            words: Lista de palabras

        Returns:
            Confianza promedio (0.0-1.0)
        """
        if not words:
            return 0.0

        total = sum(w.confidence for w in words)
        return total / len(words)
