"""
Script para configurar automáticamente las coordenadas del campo de búsqueda.

Uso:
1. Ejecuta este script: python scripts/configure_search_field.py
2. Posiciona el mouse sobre el campo de búsqueda de cédulas
3. Espera 3 segundos (el script detectará la posición)
4. Las coordenadas se guardarán automáticamente en config/settings.yaml
"""
import pyautogui
import time
import yaml
import os

print("="*60)
print("CONFIGURACIÓN DE COORDENADAS DEL CAMPO DE BÚSQUEDA")
print("="*60)
print()
print("Instrucciones:")
print("1. Abre el navegador/aplicación donde buscas cédulas")
print("2. Posiciona el mouse EXACTAMENTE sobre el campo de búsqueda")
print("3. NO muevas el mouse durante los próximos 3 segundos")
print()
print("Detectando coordenadas en:")

for i in range(3, 0, -1):
    print(f"  {i}...")
    time.sleep(1)

# Detectar posición del mouse
x, y = pyautogui.position()

print()
print("="*60)
print("COORDENADAS DETECTADAS:")
print("="*60)
print(f"  X: {x}")
print(f"  Y: {y}")
print()

# Preguntar si desea guardar
respuesta = input("¿Guardar estas coordenadas en config/settings.yaml? (s/n): ")

if respuesta.lower() in ['s', 'si', 'sí', 'y', 'yes']:
    try:
        # Leer archivo YAML actual
        config_path = 'config/settings.yaml'

        if not os.path.exists(config_path):
            print(f"❌ Error: No se encontró {config_path}")
            exit(1)

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Actualizar coordenadas
        if 'search_field' not in config:
            config['search_field'] = {}

        config['search_field']['x'] = int(x)
        config['search_field']['y'] = int(y)

        # Guardar archivo YAML
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

        print()
        print("✅ Coordenadas guardadas exitosamente!")
        print()
        print(f"Archivo actualizado: {config_path}")
        print()
        print("Ahora puedes ejecutar la aplicación:")
        print("  python main.py")
        print()
        print("Y las hotkeys funcionarán correctamente haciendo click automático")
        print("en el campo de búsqueda.")

    except Exception as e:
        print(f"❌ Error al guardar coordenadas: {e}")
        print()
        print("Puedes copiar manualmente las coordenadas a config/settings.yaml:")
        print(f"search_field:")
        print(f"  x: {x}")
        print(f"  y: {y}")

else:
    print()
    print("❌ Coordenadas NO guardadas.")
    print()
    print("Puedes copiar manualmente las coordenadas a config/settings.yaml:")
    print(f"search_field:")
    print(f"  x: {x}")
    print(f"  y: {y}")

print()
print("="*60)
print("Script finalizado")
print("="*60)
