import os
from dotenv import load_dotenv
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from PIL import Image
import io

# Cargar variables de entorno desde .env
load_dotenv()

# Leer credenciales
endpoint = os.getenv('AZURE_VISION_ENDPOINT')
key = os.getenv('AZURE_VISION_KEY')

if not endpoint or not key:
    print("❌ Faltan variables de entorno")
    print("Configura AZURE_VISION_ENDPOINT y AZURE_VISION_KEY")
    exit(1)

print(f"✓ Endpoint: {endpoint}")
print(f"✓ Key: {key[:8]}...")

# Crear cliente
client = ImageAnalysisClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(key)
)

print("✓ Cliente creado exitosamente")

# Crear imagen de prueba con texto
from PIL import ImageDraw, ImageFont
img = Image.new('RGB', (400, 100), color='white')
d = ImageDraw.Draw(img)
try:
    # Intentar usar fuente TrueType
    font = ImageFont.truetype("arial.ttf", 40)
except:
    # Fallback a fuente por defecto
    font = ImageFont.load_default()

d.text((10, 30), "1234567890", fill='black', font=font)

# Convertir a bytes
img_bytes = io.BytesIO()
img.save(img_bytes, format='PNG')
img_bytes = img_bytes.getvalue()

print("✓ Imagen de prueba creada")

# Llamar a Azure
print("→ Enviando a Azure Computer Vision...")

result = client.analyze(
    image_data=img_bytes,
    visual_features=[VisualFeatures.READ]
)

print("✓ Respuesta recibida")

# Procesar resultado
if result.read and result.read.blocks:
    print("\n📝 Texto detectado:")
    for block in result.read.blocks:
        for line in block.lines:
            print(f"   Línea: {line.text}")
            # En Azure Read API, el confidence está a nivel de palabra
            if hasattr(line, 'words') and line.words:
                word_confidences = [word.confidence for word in line.words if hasattr(word, 'confidence')]
                if word_confidences:
                    avg_conf = sum(word_confidences) / len(word_confidences)
                    print(f"      Confidence promedio: {avg_conf:.2%}")
    print("\n✅ Azure Computer Vision funciona correctamente!")
else:
    print("⚠️ No se detectó texto")

print("\n🎉 Instalación verificada exitosamente")