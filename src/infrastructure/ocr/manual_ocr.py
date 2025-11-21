"""Adaptador de OCR manual - permite entrada manual de cédulas."""
from PIL import Image
from typing import List

from ...domain.entities import CedulaRecord
from ...domain.ports import OCRPort, ConfigPort


class ManualOCR(OCRPort):
    """
    Implementación manual de OCR - permite al usuario ingresar cédulas manualmente.

    Útil cuando:
    - Los motores de OCR no están disponibles
    - La escritura es muy difícil de reconocer
    - Se prefiere control manual total

    Attributes:
        config: Servicio de configuración
        manual_input_callback: Función para solicitar entrada al usuario
    """

    def __init__(self, config: ConfigPort, manual_input_callback=None):
        """
        Inicializa el OCR manual.

        Args:
            config: Servicio de configuración
            manual_input_callback: Función para obtener entrada del usuario
        """
        self.config = config
        self.manual_input_callback = manual_input_callback
        print("✓ Usando entrada manual de cédulas (sin OCR automático)")

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        No procesa la imagen, la retorna tal cual.

        Args:
            image: Imagen PIL

        Returns:
            Imagen sin cambios
        """
        return image

    def extract_cedulas(self, image: Image.Image) -> List[CedulaRecord]:
        """
        Solicita al usuario que ingrese las cédulas manualmente.

        Args:
            image: Imagen de referencia (se muestra al usuario)

        Returns:
            Lista de registros de cédulas ingresadas manualmente
        """
        print("\n" + "="*60)
        print("MODO MANUAL: Ingrese las cédulas una por una")
        print("="*60)
        print("Instrucciones:")
        print("- Ingrese cada cédula y presione Enter")
        print("- Ingrese una línea vacía para terminar")
        print("- Ingrese 'q' para cancelar")
        print("="*60 + "\n")

        records = []
        index = 0

        while True:
            cedula = input(f"Cédula {index + 1}: ").strip()

            # Terminar si está vacío
            if not cedula:
                print("\n✓ Entrada manual completada")
                break

            # Cancelar si es 'q'
            if cedula.lower() == 'q':
                print("\n✗ Entrada manual cancelada")
                break

            # Limpiar entrada
            cedula = cedula.replace(' ', '').replace('.', '').replace(',', '').replace('-', '')

            # Validar que sea solo números
            if not cedula.isdigit():
                print(f"  ✗ '{cedula}' no es válido (solo números). Intente de nuevo.")
                continue

            # Validar longitud
            if not (3 <= len(cedula) <= 11):
                print(f"  ✗ '{cedula}' tiene longitud inválida ({len(cedula)} dígitos). Debe tener 3-11 dígitos.")
                continue

            # Crear registro usando factory method
            record = CedulaRecord.from_primitives(
                cedula=cedula,
                confidence=100.0,  # Entrada manual = 100% confianza
                index=index
            )
            records.append(record)
            index += 1

            print(f"  ✓ Agregada: {cedula}")

        print(f"\nTotal de cédulas ingresadas: {len(records)}\n")

        return records
