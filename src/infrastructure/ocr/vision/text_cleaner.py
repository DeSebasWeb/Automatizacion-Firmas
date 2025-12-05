"""Limpieza y normalizacion de texto para Vision APIs."""
from typing import List


class TextCleaner:
    """
    Limpia y normaliza texto para comparacion y busqueda.

    Responsabilidad unica: Normalizar texto eliminando caracteres
    especiales y espacios, preservando solo digitos o caracteres
    relevantes para comparacion.
    """

    # Caracteres comunes a eliminar en limpieza
    DEFAULT_REMOVE_CHARS = [' ', '.', ',', '-', '_', '/', '\\']

    @staticmethod
    def clean_for_digits(text: str) -> str:
        """
        Limpia texto preservando solo digitos.

        Args:
            text: Texto a limpiar

        Returns:
            Texto con solo digitos

        Examples:
            >>> TextCleaner.clean_for_digits("1.234-567")
            '1234567'
            >>> TextCleaner.clean_for_digits("ID: 12345")
            '12345'
        """
        return ''.join([c for c in text if c.isdigit()])

    @staticmethod
    def clean_general(text: str, remove_chars: List[str] = None) -> str:
        """
        Limpia texto eliminando caracteres especificados.

        Args:
            text: Texto a limpiar
            remove_chars: Lista de caracteres a eliminar (usa DEFAULT_REMOVE_CHARS si es None)

        Returns:
            Texto limpio

        Examples:
            >>> TextCleaner.clean_general("Hello, World!")
            'HelloWorld!'
            >>> TextCleaner.clean_general("a-b_c", ['-', '_'])
            'abc'
        """
        if remove_chars is None:
            remove_chars = TextCleaner.DEFAULT_REMOVE_CHARS

        result = text
        for char in remove_chars:
            result = result.replace(char, '')

        return result

    @staticmethod
    def extract_digits_only(text: str) -> str:
        """
        Extrae solo digitos de un texto.

        Alias de clean_for_digits() para claridad semantica.

        Args:
            text: Texto fuente

        Returns:
            String con solo digitos
        """
        return TextCleaner.clean_for_digits(text)

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """
        Normaliza espacios en blanco (multiples espacios -> un espacio).

        Args:
            text: Texto a normalizar

        Returns:
            Texto con espacios normalizados

        Examples:
            >>> TextCleaner.normalize_whitespace("Hello    World")
            'Hello World'
        """
        return ' '.join(text.split())
