"""Mapeador de texto a confianzas individuales."""
from typing import List, Dict
from .text_cleaner import TextCleaner
from .google_symbol_extractor import GoogleSymbolExtractor, Symbol
from .azure_word_extractor import AzureWordExtractor, Word


class ConfidenceMapper:
    """
    Mapea un texto buscado a sus confianzas individuales.

    Responsabilidad unica: Dado un texto (ej: cedula) y una lista de
    simbolos/palabras con confianzas, encontrar el texto en los simbolos
    y retornar las confianzas correspondientes a cada caracter.
    """

    @staticmethod
    def map_from_symbols(
        target_text: str,
        symbols: List[Symbol]
    ) -> Dict[str, any]:
        """
        Mapea texto a confianzas usando simbolos individuales (Google Vision).

        Args:
            target_text: Texto a buscar (ej: "1234567")
            symbols: Lista de simbolos con confianzas

        Returns:
            Dict con:
            - 'confidences': List[float] confianza por caracter
            - 'positions': List[int] posiciones
            - 'average': float confianza promedio
            - 'found': bool si se encontro el texto
        """
        # Limpiar texto buscado (solo digitos)
        text_clean = TextCleaner.clean_for_digits(target_text)

        # Obtener texto completo de simbolos (solo digitos)
        all_text = GoogleSymbolExtractor.get_full_text(symbols)
        all_text_clean = TextCleaner.clean_for_digits(all_text)

        # Buscar texto en simbolos
        if text_clean in all_text_clean:
            # Encontrado - extraer confianzas correspondientes
            start_idx = all_text_clean.index(text_clean)
            confidences, positions = ConfidenceMapper._extract_confidences_from_symbols(
                symbols, start_idx, len(text_clean)
            )

            return {
                'confidences': confidences,
                'positions': positions,
                'average': sum(confidences) / len(confidences) if confidences else 0.0,
                'found': True
            }
        else:
            # No encontrado - usar promedio de todos los simbolos numericos
            digit_symbols = [s for s in symbols if s.text.isdigit()]
            avg_conf = GoogleSymbolExtractor.get_average_confidence(digit_symbols)

            return {
                'confidences': [avg_conf] * len(text_clean),
                'positions': list(range(len(text_clean))),
                'average': avg_conf,
                'found': False
            }

    @staticmethod
    def map_from_words(
        target_text: str,
        words: List[Word]
    ) -> Dict[str, any]:
        """
        Mapea texto a confianzas usando palabras (Azure Vision).

        IMPORTANTE: Azure da confianza a nivel de palabra, no de caracter.
        Por lo tanto, distribuimos la confianza de la palabra a todos sus
        caracteres.

        Args:
            target_text: Texto a buscar (ej: "1234567")
            words: Lista de palabras con confianzas

        Returns:
            Dict con:
            - 'confidences': List[float] confianza por caracter
            - 'positions': List[int] posiciones
            - 'average': float confianza promedio
            - 'found': bool si se encontro el texto
        """
        # Limpiar texto buscado (solo digitos)
        text_clean = TextCleaner.clean_for_digits(target_text)

        # Obtener texto completo de palabras (solo digitos)
        all_text = AzureWordExtractor.get_full_text(words)
        all_text_clean = TextCleaner.clean_for_digits(all_text)

        # Buscar texto en palabras
        if text_clean in all_text_clean:
            # Encontrado - extraer confianzas correspondientes
            start_idx = all_text_clean.index(text_clean)
            confidences, positions = ConfidenceMapper._extract_confidences_from_words(
                words, start_idx, len(text_clean)
            )

            return {
                'confidences': confidences,
                'positions': positions,
                'average': sum(confidences) / len(confidences) if confidences else 0.0,
                'found': True
            }
        else:
            # No encontrado - usar promedio de palabras numericas
            numeric_words = [w for w in words if any(c.isdigit() for c in w.text)]
            avg_conf = AzureWordExtractor.get_average_confidence(numeric_words)

            return {
                'confidences': [avg_conf] * len(text_clean),
                'positions': list(range(len(text_clean))),
                'average': avg_conf,
                'found': False
            }

    @staticmethod
    def _extract_confidences_from_symbols(
        symbols: List[Symbol],
        start_idx: int,
        length: int
    ) -> tuple:
        """
        Extrae confianzas de simbolos en un rango especifico.

        Args:
            symbols: Lista de simbolos
            start_idx: Indice inicial (en digitos)
            length: Longitud a extraer

        Returns:
            Tupla (confidences, positions)
        """
        confidences = []
        positions = []

        digit_counter = 0
        for symbol in symbols:
            if symbol.text.isdigit():
                if digit_counter >= start_idx and digit_counter < start_idx + length:
                    confidences.append(symbol.confidence)
                    positions.append(digit_counter - start_idx)
                digit_counter += 1

        return confidences, positions

    @staticmethod
    def _extract_confidences_from_words(
        words: List[Word],
        start_idx: int,
        length: int
    ) -> tuple:
        """
        Extrae confianzas de palabras en un rango especifico.

        IMPORTANTE: Cada caracter de una palabra hereda la confianza
        de toda la palabra.

        Args:
            words: Lista de palabras
            start_idx: Indice inicial (en digitos)
            length: Longitud a extraer

        Returns:
            Tupla (confidences, positions)
        """
        confidences = []
        positions = []

        digit_counter = 0
        for word in words:
            # Procesar cada caracter de la palabra
            for char in word.text:
                if char.isdigit():
                    if digit_counter >= start_idx and digit_counter < start_idx + length:
                        # Asignar confianza de la palabra al digito
                        confidences.append(word.confidence)
                        positions.append(digit_counter - start_idx)
                    digit_counter += 1

        return confidences, positions
