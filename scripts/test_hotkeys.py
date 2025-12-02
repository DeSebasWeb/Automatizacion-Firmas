"""
Script para probar que las hotkeys funcionen correctamente.
HOTKEYS FINALES (sin conflictos):
- Alt+1: Seleccionar área
- Alt+2: Capturar pantalla
- Alt+3: Extraer cédulas
- Alt+4: Iniciar procesamiento
- Ctrl+Q: Procesar siguiente
- Alt+5: Pausar/Reanudar
- ESC: Salir
"""
from pynput import keyboard
import sys

print("="*70)
print("PRUEBA DE HOTKEYS - ASISTENTE DE DIGITACIÓN DE CÉDULAS")
print("="*70)
print()
print("✨ HOTKEYS OPTIMIZADAS (Alt+números = SIN CONFLICTOS)")
print()
print("Presiona las siguientes combinaciones para probarlas:")
print()
print("  Alt+1     → Seleccionar área de captura")
print("  Alt+2     → Capturar pantalla")
print("  Alt+3     → Extraer cédulas con OCR")
print("  Alt+4     → Iniciar procesamiento")
print("  Alt+5     → Pausar/Reanudar")
print("  Ctrl+Q    → Procesar siguiente cédula")
print("  ESC       → Salir del script")
print()
print("="*70)
print()

# Contador de detecciones
detections = {
    'alt+1': 0,
    'alt+2': 0,
    'alt+3': 0,
    'alt+4': 0,
    'alt+5': 0,
    'ctrl+q': 0,
}

def on_alt_1():
    detections['alt+1'] += 1
    print(f"✅ Alt+1 detectado correctamente! (#{detections['alt+1']}) → Seleccionar área")

def on_alt_2():
    detections['alt+2'] += 1
    print(f"✅ Alt+2 detectado correctamente! (#{detections['alt+2']}) → Capturar pantalla")

def on_alt_3():
    detections['alt+3'] += 1
    print(f"✅ Alt+3 detectado correctamente! (#{detections['alt+3']}) → Extraer cédulas")

def on_alt_4():
    detections['alt+4'] += 1
    print(f"✅ Alt+4 detectado correctamente! (#{detections['alt+4']}) → Iniciar procesamiento")

def on_alt_5():
    detections['alt+5'] += 1
    print(f"✅ Alt+5 detectado correctamente! (#{detections['alt+5']}) → Pausar/Reanudar")

def on_ctrl_q():
    detections['ctrl+q'] += 1
    print(f"✅ Ctrl+Q detectado correctamente! (#{detections['ctrl+q']}) → Procesar siguiente")

def on_esc():
    print()
    print("="*70)
    print("RESUMEN DE DETECCIONES:")
    print("="*70)
    for key, count in detections.items():
        status = "✅" if count > 0 else "❌"
        print(f"  {status} {key.upper()}: {count} detección(es)")
    print("="*70)
    print()
    if all(count > 0 for count in detections.values()):
        print("🎉 ¡PERFECTO! Todas las hotkeys funcionan correctamente")
    else:
        print("⚠️ Algunas hotkeys no fueron probadas")
    print()
    print("👋 Saliendo del script de prueba...")
    sys.exit(0)

# Mapeo de hotkeys
hotkey_map = {
    '<alt>+1': on_alt_1,
    '<alt>+2': on_alt_2,
    '<alt>+3': on_alt_3,
    '<alt>+4': on_alt_4,
    '<alt>+5': on_alt_5,
    '<ctrl>+q': on_ctrl_q,
    '<esc>': on_esc,
}

# Crear listener global
try:
    listener = keyboard.GlobalHotKeys(hotkey_map)
    listener.start()
    print("⏳ Esperando pulsaciones de teclas...")
    print("   (El script está corriendo en segundo plano)")
    print()
    print("💡 VENTAJAS DE USAR ALT+NÚMEROS:")
    print("   ✅ NO interfiere con Alt+F4 (cerrar ventana)")
    print("   ✅ NO interfiere con Ctrl+F5 (recarga forzada)")
    print("   ✅ NO interfiere con F5 del navegador (recargar)")
    print("   ✅ NO interfiere con Discord, OBS, etc.")
    print("   ✅ Fácil de recordar: Alt+1, Alt+2, Alt+3, Alt+4, Alt+5")
    print("   ✅ Secuencia natural: 1→2→3→4 (workflow completo)")
    print()
    print("💡 NOTA:")
    print("   - Si alguna tecla no funciona, ejecuta como administrador")
    print("   - Alt+números es la combinación MÁS SEGURA sin conflictos")
    print()

    # Mantener el script corriendo
    listener.join()
except KeyboardInterrupt:
    print("\n👋 Script interrumpido por usuario (Ctrl+C)")
    sys.exit(0)
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nPosibles causas:")
    print("  1. Ejecuta el script como administrador (Windows)")
    print("  2. Verifica que pynput esté instalado: pip install pynput")
    sys.exit(1)
