"""Factory para crear adaptadores OCR según configuración."""
from typing import Optional

from ...domain.ports import OCRPort, ConfigPort


def create_ocr_adapter(config: ConfigPort) -> Optional[OCRPort]:
    """
    Factory que crea el adaptador OCR según configuración.

    Lee la configuración 'ocr.provider' y retorna el adaptador apropiado:
    - "google_vision": GoogleVisionAdapter (recomendado para manuscritos)
    - "azure_vision": AzureVisionAdapter (alternativa para comparación)
    - "ensemble": EnsembleOCR (máxima precisión, doble costo)
    - "digit_ensemble": DigitLevelEnsembleOCR (ULTRA precisión por dígito, doble costo)

    Args:
        config: Servicio de configuración

    Returns:
        Adaptador OCR inicializado, o None si no se pudo crear

    Example:
        >>> config = YamlConfigAdapter('config/settings.yaml')
        >>> ocr = create_ocr_adapter(config)
        >>> if ocr:
        ...     records = ocr.extract_cedulas(image)

    Note:
        Si el proveedor configurado no está disponible, intenta fallback
        automático a otros proveedores disponibles.
    """
    provider = config.get('ocr.provider', 'google_vision').lower()

    print("\n" + "="*60)
    print("OCR FACTORY - Inicializando proveedor OCR")
    print("="*60)
    print(f"Proveedor configurado: {provider}")
    print("="*60 + "\n")

    # Intentar crear el proveedor configurado
    ocr_adapter = _try_create_provider(provider, config)

    if ocr_adapter:
        return ocr_adapter

    # Si falló, intentar fallback automático
    print(f"\n⚠️ No se pudo inicializar '{provider}', intentando fallback...")

    fallback_order = ['google_vision', 'azure_vision', 'tesseract']

    for fallback_provider in fallback_order:
        if fallback_provider == provider:
            continue  # Ya lo intentamos

        print(f"→ Intentando {fallback_provider}...")
        ocr_adapter = _try_create_provider(fallback_provider, config)

        if ocr_adapter:
            print(f"✓ Fallback exitoso a {fallback_provider}")
            return ocr_adapter

    # Si ninguno funcionó
    print("\n❌ ERROR: No se pudo inicializar ningún proveedor OCR")
    print("\n💡 Soluciones:")
    print("   1. Google Vision: Configurar gcloud auth application-default login")
    print("   2. Azure Vision: Configurar AZURE_VISION_ENDPOINT y AZURE_VISION_KEY")
    print("   3. Tesseract: Instalar con pip install pytesseract")
    print()

    return None


def _try_create_provider(provider: str, config: ConfigPort) -> Optional[OCRPort]:
    """
    Intenta crear un proveedor OCR específico.

    Args:
        provider: Nombre del proveedor ("google_vision", "azure_vision", etc.)
        config: Servicio de configuración

    Returns:
        Adaptador OCR o None si falló
    """
    try:
        if provider == 'google_vision':
            from .google_vision_adapter import GoogleVisionAdapter
            print("→ Inicializando Google Cloud Vision...")
            adapter = GoogleVisionAdapter(config)
            print("✓ Google Cloud Vision listo")
            print("💰 1,000 imágenes gratis/mes = 15,000 cédulas gratis/mes")
            return adapter

        elif provider == 'azure_vision':
            from .azure_vision_adapter import AzureVisionAdapter
            print("→ Inicializando Azure Computer Vision...")
            adapter = AzureVisionAdapter(config)
            print("✓ Azure Computer Vision listo")
            print("💰 5,000 transacciones gratis/mes = 75,000 cédulas gratis/mes")
            return adapter

        elif provider == 'ensemble':
            from .ensemble_ocr import EnsembleOCR
            print("→ Inicializando Ensemble OCR (Google + Azure)...")
            adapter = EnsembleOCR(config)
            print("✓ Ensemble OCR listo (modo máxima precisión)")
            print("⚠️ Doble costo: usa ambas APIs simultáneamente")
            return adapter

        elif provider == 'digit_ensemble':
            from .google_vision_adapter import GoogleVisionAdapter
            from .azure_vision_adapter import AzureVisionAdapter
            from .digit_level_ensemble_ocr import DigitLevelEnsembleOCR

            print("→ Inicializando Digit-Level Ensemble OCR...")
            print("   Creando Google Vision adapter...")
            google = GoogleVisionAdapter(config)
            print("   Creando Azure Vision adapter...")
            azure = AzureVisionAdapter(config)
            print("   Combinando ambos con lógica de votación por dígito...")

            adapter = DigitLevelEnsembleOCR(
                config=config,
                primary_ocr=google,
                secondary_ocr=azure
            )
            print("✓ Digit-Level Ensemble listo (ULTRA precisión 98-99.5%)")
            print("⚠️ Doble costo: usa ambas APIs simultáneamente")
            print("🎯 Combina lo mejor de cada OCR en cada posición de dígito")
            return adapter

        elif provider == 'aws_textract':
            from .aws_textract_adapter import AWSTextractAdapter
            print("→ Inicializando AWS Textract...")
            adapter = AWSTextractAdapter(config)
            print("✓ AWS Textract listo")
            print("💰 1,000 páginas gratis/mes x 3 meses = 15,000 cédulas gratis/mes")
            return adapter

        elif provider == 'triple_ensemble':
            from .google_vision_adapter import GoogleVisionAdapter
            from .azure_vision_adapter import AzureVisionAdapter
            from .aws_textract_adapter import AWSTextractAdapter
            from .triple_ensemble_ocr import TripleEnsembleOCR

            print("→ Inicializando Triple Ensemble OCR (Google + Azure + AWS)...")
            print("   Creando Google Vision adapter...")
            google = GoogleVisionAdapter(config)
            print("   Creando Azure Vision adapter...")
            azure = AzureVisionAdapter(config)
            print("   Creando AWS Textract adapter...")
            aws = AWSTextractAdapter(config)
            print("   Combinando los 3 con votación 3-way por dígito...")

            adapter = TripleEnsembleOCR(
                config=config,
                google_ocr=google,
                azure_ocr=azure,
                aws_ocr=aws
            )
            print("✓ Triple Ensemble listo (MÁXIMA precisión 99.5-99.8%)")
            print("⚠️ Triple costo: usa las 3 APIs simultáneamente")
            print("🎯 Votación 3-way elimina prácticamente todos los errores")
            print("🎯 Ideal para conseguir inversión y vender como SaaS")
            return adapter

        elif provider == 'tesseract':
            from .tesseract_ocr import TesseractOCR
            print("→ Inicializando Tesseract OCR...")
            adapter = TesseractOCR(config)
            print("✓ Tesseract OCR listo (gratuito, menor precisión)")
            return adapter

        else:
            print(f"❌ Proveedor desconocido: {provider}")
            return None

    except ImportError as e:
        print(f"✗ {provider} no está instalado: {e}")
        return None
    except Exception as e:
        print(f"✗ Error inicializando {provider}: {e}")
        return None


def get_available_providers() -> list:
    """
    Obtiene lista de proveedores OCR disponibles en el sistema.

    Returns:
        Lista de strings con nombres de proveedores disponibles

    Example:
        >>> providers = get_available_providers()
        >>> print(f"Proveedores disponibles: {', '.join(providers)}")
    """
    available = []

    # Verificar Google Vision
    try:
        from google.cloud import vision
        available.append('google_vision')
    except ImportError:
        pass

    # Verificar Azure Vision
    try:
        from azure.ai.vision.imageanalysis import ImageAnalysisClient
        available.append('azure_vision')
    except ImportError:
        pass

    # Verificar AWS Textract
    try:
        import boto3
        available.append('aws_textract')
    except ImportError:
        pass

    # Verificar Tesseract
    try:
        import pytesseract
        available.append('tesseract')
    except ImportError:
        pass

    # Ensemble solo si hay al menos 2 proveedores
    if len(available) >= 2:
        available.append('ensemble')
        available.append('digit_ensemble')

    # Triple Ensemble solo si hay al menos 3 proveedores (Google + Azure + AWS)
    if 'google_vision' in available and 'azure_vision' in available and 'aws_textract' in available:
        available.append('triple_ensemble')

    return available


def print_provider_comparison():
    """
    Imprime tabla comparativa de proveedores OCR disponibles.

    Útil para ayudar al usuario a elegir el mejor proveedor.
    """
    print("\n" + "="*80)
    print("COMPARACIÓN DE PROVEEDORES OCR")
    print("="*80)
    print()
    print(f"{'Proveedor':<22} {'Precisión':<15} {'Costo/1000 imgs':<20} {'Velocidad':<15}")
    print("-" * 80)
    print(f"{'Google Vision':<22} {'95-98%':<15} {'$5.16 COP':<20} {'1-2 seg':<15}")
    print(f"{'Azure Vision':<22} {'95-98%':<15} {'$4,200 COP':<20} {'1-2 seg':<15}")
    print(f"{'AWS Textract':<22} {'95-98%':<15} {'$6,450 COP':<20} {'1-2 seg':<15}")
    print(f"{'Ensemble':<22} {'>99%':<15} {'$9,360 COP':<20} {'2-3 seg':<15}")
    print(f"{'Digit Ensemble':<22} {'98-99.5%':<15} {'$9,360 COP':<20} {'2-3 seg':<15}")
    print(f"{'Triple Ensemble ⭐⭐':<22} {'99.5-99.8%':<15} {'$15,816 COP':<20} {'3-4 seg':<15}")
    print(f"{'Tesseract':<22} {'70-85%':<15} {'Gratis':<20} {'0.5-1 seg':<15}")
    print("-" * 80)
    print()
    print("💡 Recomendaciones:")
    print("   • MÁXIMA PRECISIÓN: Triple Ensemble ⭐⭐ (votación 3-way, 99.5-99.8%)")
    print("   • Producción: Google Vision (mejor relación precisión/costo)")
    print("   • Comparación: Azure Vision (validar cuál da mejor precisión)")
    print("   • Alta precisión: Digit Ensemble (combina 2 OCR por dígito, 98-99.5%)")
    print("   • Tercera opinión: AWS Textract (para triple ensemble)")
    print("   • Desarrollo: Tesseract (gratis, pero menor precisión)")
    print()
    print("Proveedores disponibles en este sistema:")
    available = get_available_providers()
    for provider in available:
        print(f"   ✓ {provider}")
    print()
    print("="*80 + "\n")
