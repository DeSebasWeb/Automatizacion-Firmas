"""Script de prueba para el selector visual de campos Tesseract."""
from PyQt6.QtWidgets import QApplication
from src.presentation.ui import TesseractFieldSelector
import sys


def main():
    """Ejecuta el selector de campos Tesseract."""
    app = QApplication(sys.argv)

    print("="*70)
    print("SELECTOR VISUAL DE CAMPOS TESSERACT")
    print("="*70)
    print("\nInstrucciones:")
    print("1. Haz click en 'Capturar Formulario Web'")
    print("2. Selecciona el área del formulario web con el mouse")
    print("3. Haz click en cada campo de la lista (primer_nombre, etc.)")
    print("4. Dibuja un rectángulo sobre cada campo en la imagen")
    print("5. Guarda la configuración al finalizar")
    print("\n" + "="*70 + "\n")

    # Crear selector
    selector = TesseractFieldSelector()
    selector.exec()

    # Al cerrar, mostrar regiones configuradas
    regions = selector.get_field_regions()

    if regions:
        print("\n" + "="*70)
        print("REGIONES CONFIGURADAS:")
        print("="*70)
        for field_name, (x, y, w, h) in regions.items():
            print(f"  {field_name}:")
            print(f"    x: {x}")
            print(f"    y: {y}")
            print(f"    width: {w}")
            print(f"    height: {h}")
        print("="*70)
    else:
        print("\nNo se configuraron regiones.")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
