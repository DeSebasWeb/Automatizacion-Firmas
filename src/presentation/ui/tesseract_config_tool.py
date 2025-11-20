"""Herramienta de configuración de regiones para Tesseract OCR."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSpinBox, QGroupBox, QListWidget,
    QListWidgetItem, QMessageBox, QTextEdit, QWidget
)
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QPen, QColor, QPixmap, QImage
from PIL import Image
from typing import Dict, Tuple, Optional
import yaml


class TesseractConfigTool(QDialog):
    """
    Herramienta de configuración de regiones para Tesseract.

    Permite al usuario:
    - Capturar una imagen del formulario web
    - Definir regiones para cada campo (x, y, width, height)
    - Previsualizar las regiones
    - Guardar configuración en settings.yaml
    """

    def __init__(self, parent=None):
        """Inicializa la herramienta."""
        super().__init__(parent)
        self.field_regions: Dict[str, Tuple[int, int, int, int]] = {}
        self.current_field: Optional[str] = None
        self.web_form_image: Optional[QPixmap] = None

        self.setup_ui()
        self._load_default_fields()

    def setup_ui(self):
        """Configura la interfaz."""
        self.setWindowTitle("Configurador de Regiones Tesseract")
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout(self)

        # Título
        title = QLabel("<b>🔧 Configurador de Regiones para Tesseract OCR</b>")
        title.setStyleSheet("font-size: 16px; color: #1976d2; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Instrucciones
        instructions = QLabel(
            "Esta herramienta te ayuda a configurar las regiones de los campos del formulario web "
            "para que Tesseract pueda leerlos correctamente."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(instructions)

        # Sección de captura
        layout.addWidget(self._create_capture_section())

        # Layout horizontal: Lista de campos + Configuración
        content_layout = QHBoxLayout()
        content_layout.addWidget(self._create_fields_section(), 1)
        content_layout.addWidget(self._create_config_section(), 2)
        layout.addLayout(content_layout)

        # Vista previa de configuración
        layout.addWidget(self._create_preview_section())

        # Botones de acción
        layout.addWidget(self._create_action_buttons())

    def _create_capture_section(self) -> QGroupBox:
        """Crea la sección de captura de imagen."""
        group = QGroupBox("1. Captura del Formulario Web")
        layout = QHBoxLayout()

        btn_capture = QPushButton("📸 Capturar Formulario Web")
        btn_capture.clicked.connect(self._capture_web_form)
        btn_capture.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1e88e5;
            }
        """)

        self.lbl_capture_status = QLabel("Sin captura")
        self.lbl_capture_status.setStyleSheet("color: #666;")

        layout.addWidget(btn_capture)
        layout.addWidget(self.lbl_capture_status)
        layout.addStretch()

        group.setLayout(layout)
        return group

    def _create_fields_section(self) -> QGroupBox:
        """Crea la sección de lista de campos."""
        group = QGroupBox("2. Campos del Formulario")
        layout = QVBoxLayout()

        self.list_fields = QListWidget()
        self.list_fields.itemClicked.connect(self._on_field_selected)

        layout.addWidget(self.list_fields)
        group.setLayout(layout)
        return group

    def _create_config_section(self) -> QGroupBox:
        """Crea la sección de configuración de región."""
        group = QGroupBox("3. Configurar Región")
        layout = QVBoxLayout()

        self.lbl_current_field = QLabel("Selecciona un campo de la lista")
        self.lbl_current_field.setStyleSheet("font-weight: bold; color: #1976d2;")
        layout.addWidget(self.lbl_current_field)

        # Spinboxes para coordenadas
        coords_layout = QVBoxLayout()

        # X
        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel("X (horizontal):"))
        self.spin_x = QSpinBox()
        self.spin_x.setRange(0, 3000)
        self.spin_x.setValue(100)
        x_layout.addWidget(self.spin_x)
        coords_layout.addLayout(x_layout)

        # Y
        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel("Y (vertical):"))
        self.spin_y = QSpinBox()
        self.spin_y.setRange(0, 3000)
        self.spin_y.setValue(150)
        y_layout.addWidget(self.spin_y)
        coords_layout.addLayout(y_layout)

        # Width
        w_layout = QHBoxLayout()
        w_layout.addWidget(QLabel("Ancho (width):"))
        self.spin_width = QSpinBox()
        self.spin_width.setRange(10, 1000)
        self.spin_width.setValue(300)
        w_layout.addWidget(self.spin_width)
        coords_layout.addLayout(w_layout)

        # Height
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Alto (height):"))
        self.spin_height = QSpinBox()
        self.spin_height.setRange(10, 500)
        self.spin_height.setValue(40)
        h_layout.addWidget(self.spin_height)
        coords_layout.addLayout(h_layout)

        layout.addLayout(coords_layout)

        # Botón guardar región
        btn_save_region = QPushButton("✓ Guardar Región para Este Campo")
        btn_save_region.clicked.connect(self._save_current_region)
        btn_save_region.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: white;
                padding: 8px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #388e3c;
            }
        """)
        layout.addWidget(btn_save_region)

        layout.addStretch()
        group.setLayout(layout)
        return group

    def _create_preview_section(self) -> QGroupBox:
        """Crea la sección de vista previa."""
        group = QGroupBox("Vista Previa de Configuración")
        layout = QVBoxLayout()

        self.txt_preview = QTextEdit()
        self.txt_preview.setReadOnly(True)
        self.txt_preview.setMaximumHeight(150)
        self.txt_preview.setStyleSheet("font-family: monospace; font-size: 12px;")

        layout.addWidget(self.txt_preview)
        group.setLayout(layout)
        return group

    def _create_action_buttons(self) -> QWidget:
        """Crea los botones de acción final."""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        btn_export = QPushButton("💾 Exportar Configuración a YAML")
        btn_export.clicked.connect(self._export_config)
        btn_export.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1e88e5;
            }
        """)

        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.close)

        layout.addWidget(btn_export)
        layout.addStretch()
        layout.addWidget(btn_close)

        return widget

    def _load_default_fields(self):
        """Carga los campos por defecto."""
        fields = [
            "primer_nombre",
            "segundo_nombre",
            "primer_apellido",
            "segundo_apellido"
        ]

        for field in fields:
            item = QListWidgetItem(field)
            self.list_fields.addItem(item)

        # Configuración por defecto
        self.field_regions = {
            'primer_nombre': (100, 150, 300, 40),
            'segundo_nombre': (100, 200, 300, 40),
            'primer_apellido': (100, 250, 300, 40),
            'segundo_apellido': (100, 300, 300, 40)
        }

        self._update_preview()

    def _capture_web_form(self):
        """Captura el formulario web."""
        # TODO: Implementar captura real de pantalla
        # Por ahora, solo simulamos
        self.lbl_capture_status.setText("✓ Formulario capturado (simulado)")
        self.lbl_capture_status.setStyleSheet("color: #2e7d32; font-weight: bold;")

        QMessageBox.information(
            self,
            "Captura Simulada",
            "En la implementación real, aquí se capturará la región del formulario web.\n\n"
            "Por ahora, puedes configurar las regiones manualmente usando los spinboxes."
        )

    def _on_field_selected(self, item: QListWidgetItem):
        """Maneja la selección de un campo."""
        self.current_field = item.text()
        self.lbl_current_field.setText(f"Configurando: {self.current_field}")

        # Cargar coordenadas actuales si existen
        if self.current_field in self.field_regions:
            x, y, w, h = self.field_regions[self.current_field]
            self.spin_x.setValue(x)
            self.spin_y.setValue(y)
            self.spin_width.setValue(w)
            self.spin_height.setValue(h)

    def _save_current_region(self):
        """Guarda la región actual del campo seleccionado."""
        if not self.current_field:
            QMessageBox.warning(
                self,
                "Sin Campo Seleccionado",
                "Por favor, selecciona un campo de la lista primero."
            )
            return

        # Obtener valores
        x = self.spin_x.value()
        y = self.spin_y.value()
        w = self.spin_width.value()
        h = self.spin_height.value()

        # Guardar región
        self.field_regions[self.current_field] = (x, y, w, h)

        # Actualizar preview
        self._update_preview()

        QMessageBox.information(
            self,
            "Región Guardada",
            f"Región guardada para '{self.current_field}':\n\n"
            f"X: {x}, Y: {y}\n"
            f"Ancho: {w}, Alto: {h}"
        )

    def _update_preview(self):
        """Actualiza la vista previa de configuración."""
        preview_text = "field_regions:\n"

        for field_name, (x, y, w, h) in sorted(self.field_regions.items()):
            preview_text += f"  {field_name}:\n"
            preview_text += f"    x: {x}\n"
            preview_text += f"    y: {y}\n"
            preview_text += f"    width: {w}\n"
            preview_text += f"    height: {h}\n"

        self.txt_preview.setPlainText(preview_text)

    def _export_config(self):
        """Exporta la configuración a YAML."""
        config = {
            'ocr': {
                'tesseract': {
                    'field_regions': {}
                }
            }
        }

        # Convertir tuplas a diccionarios
        for field_name, (x, y, w, h) in self.field_regions.items():
            config['ocr']['tesseract']['field_regions'][field_name] = {
                'x': x,
                'y': y,
                'width': w,
                'height': h
            }

        # Convertir a YAML
        yaml_text = yaml.dump(config, default_flow_style=False, allow_unicode=True)

        # Mostrar en diálogo
        msg = QMessageBox(self)
        msg.setWindowTitle("Configuración YAML Generada")
        msg.setText("Copia esta configuración y agrégala a tu archivo settings.yaml:")
        msg.setDetailedText(yaml_text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

        print("\n" + "="*70)
        print("CONFIGURACIÓN YAML GENERADA:")
        print("="*70)
        print(yaml_text)
        print("="*70)

    def get_field_regions(self) -> Dict[str, Tuple[int, int, int, int]]:
        """
        Obtiene las regiones configuradas.

        Returns:
            Diccionario de {field_name: (x, y, width, height)}
        """
        return self.field_regions.copy()
