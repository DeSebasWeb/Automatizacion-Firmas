"""Componentes para procesamiento de respuestas de Vision APIs."""
from .text_cleaner import TextCleaner
from .google_symbol_extractor import GoogleSymbolExtractor, Symbol
from .azure_word_extractor import AzureWordExtractor, Word
from .confidence_mapper import ConfidenceMapper

__all__ = [
    # Limpieza de texto
    'TextCleaner',

    # Extractores
    'GoogleSymbolExtractor',
    'Symbol',
    'AzureWordExtractor',
    'Word',

    # Mapeador
    'ConfidenceMapper',
]
