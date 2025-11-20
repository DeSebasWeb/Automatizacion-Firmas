"""Selector visual de campos para Tesseract OCR."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QListWidget, QListWidgetItem, QMessageBox, QDialog
)
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap, QImage, QFont
from PIL import Image
from typing import Dict, Tuple, Optional
import yaml


class TesseractFieldSelector(QDialog):
    """
    Selector visual de campos para Tesseract.

    Permite al usuario:
    1. Capturar formulario web
    2. Seleccionar visualmente cada campo dibujando rectángulos
    3. Etiquetar cada campo
    4. Guardar configuración
    """

    def __init__(self, parent=None):
        """Inicializa el selector."""
        super().__init__(parent)
        self.field_regions: Dict[str, Tuple[int, int, int, int]] = {}
        self.current_field_name: Optional[str] = None
        self.web_form_image: Optional[QPixmap] = None

        # Estado de selección
        self.selecting = False
        self.selection_start = None
        self.selection_end = None

        # Lista de campos a configurar
        self.pending_fields = [
            "primer_nombre",
            "segundo_nombre",
            "primer_apellido",
            "segundo_apellido"
        ]

        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz."""
        self.setWindowTitle("Selector de Campos Tesseract")
        self.setMinimumSize(1000, 700)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Título
        title = QLabel("<b>📐 Selector Visual de Campos para Tesseract</b>")
        title.setStyleSheet("font-size: 16px; color: #1976d2; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Instrucciones
        self.lbl_instructions = QLabel(
            "1. Captura el formulario web\n"
            "2. Selecciona cada campo dibujando un rectángulo con el mouse\n"
            "3. Guarda la configuración"
        )
        self.lbl_instructions.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(self.lbl_instructions)

        # Botón capturar
        btn_layout = QHBoxLayout()

        self.btn_capture = QPushButton("📸 Capturar Formulario Web")
        self.btn_capture.clicked.connect(self._capture_web_form)
        self.btn_capture.setStyleSheet("""
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
        btn_layout.addWidget(self.btn_capture)

        self.lbl_capture_status = QLabel("Sin captura")
        self.lbl_capture_status.setStyleSheet("color: #666;")
        btn_layout.addWidget(self.lbl_capture_status)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # Layout horizontal: Lista de campos + Canvas
        content_layout = QHBoxLayout()

        # Panel izquierdo: Lista de campos
        left_panel = QVBoxLayout()

        lbl_fields = QLabel("<b>Campos a configurar:</b>")
        left_panel.addWidget(lbl_fields)

        self.list_fields = QListWidget()
        self.list_fields.itemClicked.connect(self._on_field_clicked)
        for field in self.pending_fields:
            item = QListWidgetItem(f"⭕ {field}")
            self.list_fields.addItem(item)
        left_panel.addWidget(self.list_fields)

        self.lbl_current_field = QLabel("Selecciona un campo de la lista")
        self.lbl_current_field.setStyleSheet("font-weight: bold; color: #1976d2; padding: 5px;")
        left_panel.addWidget(self.lbl_current_field)

        content_layout.addLayout(left_panel, 1)

        # Panel derecho: Canvas de selección
        self.canvas = SelectionCanvas()
        self.canvas.selection_completed.connect(self._on_selection_completed)
        self.canvas.setMinimumSize(600, 400)
        content_layout.addWidget(self.canvas, 2)

        layout.addLayout(content_layout)

        # Botones de acción
        action_layout = QHBoxLayout()

        btn_save = QPushButton("💾 Guardar Configuración")
        btn_save.clicked.connect(self._save_configuration)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: white;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #388e3c;
            }
        """)
        action_layout.addWidget(btn_save)

        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.close)
        action_layout.addWidget(btn_close)

        action_layout.addStretch()
        layout.addLayout(action_layout)

    def _capture_web_form(self):
        """Captura el formulario web usando area selector."""
        # Importar area selector
        from .area_selector import AreaSelectorWidget
        from ...domain.entities import CaptureArea
        from PyQt6.QtCore import QTimer

        def on_area_selected(area: CaptureArea):
            """Callback cuando se selecciona el área."""
            try:
                # Capturar la región seleccionada
                from ...infrastructure.capture.pyautogui_capture import PyAutoGUICapture

                capture_service = PyAutoGUICapture()
                captured_image = capture_service.capture_area(area)

                # Convertir PIL a QPixmap
                captured_image = captured_image.convert('RGB')
                data = captured_image.tobytes('raw', 'RGB')
                qimage = QImage(
                    data,
                    captured_image.width,
                    captured_image.height,
                    captured_image.width * 3,
                    QImage.Format.Format_RGB888
                )
                self.web_form_image = QPixmap.fromImage(qimage)

                # Mostrar en canvas
                self.canvas.set_image(self.web_form_image)

                # Actualizar estado
                self.lbl_capture_status.setText("✓ Formulario capturado")
                self.lbl_capture_status.setStyleSheet("color: #2e7d32; font-weight: bold;")

                print("✓ Captura completada exitosamente")

            except Exception as e:
                print(f"ERROR al capturar: {e}")
                self.lbl_capture_status.setText("✗ Error al capturar")
                self.lbl_capture_status.setStyleSheet("color: #d32f2f; font-weight: bold;")

            finally:
                # SIEMPRE mostrar el diálogo de nuevo después de un delay
                QTimer.singleShot(200, lambda: self._restore_dialog())

        # Ocultar este diálogo temporalmente
        self.hide()

        # Dar tiempo para que se oculte antes de mostrar selector
        QTimer.singleShot(300, lambda: self._show_area_selector(on_area_selected))

    def _show_area_selector(self, callback):
        """Muestra el selector de área."""
        from .area_selector import AreaSelectorWidget

        # Guardar referencia para evitar que sea destruido por GC
        self.area_selector = AreaSelectorWidget(callback=callback)

        # Conectar evento de cierre para restaurar diálogo
        self.area_selector.destroyed.connect(self._restore_dialog)

        self.area_selector.showFullScreen()
        print("Selector de área mostrado - Dibuja un rectángulo sobre el formulario web")

    def _restore_dialog(self):
        """Restaura el diálogo principal."""
        if not self.isVisible():
            self.show()
            self.raise_()
            self.activateWindow()
            print("Diálogo restaurado")

    def _on_field_clicked(self, item: QListWidgetItem):
        """Maneja click en un campo de la lista."""
        # Extraer nombre del campo (quitar emoji)
        field_text = item.text()
        self.current_field_name = field_text.split(" ", 1)[1] if " " in field_text else field_text

        self.lbl_current_field.setText(f"Dibuja un rectángulo para: {self.current_field_name}")
        self.canvas.set_current_field(self.current_field_name)

        # Activar modo de selección en canvas
        if self.web_form_image:
            self.canvas.enable_selection()
        else:
            QMessageBox.warning(
                self,
                "Sin Captura",
                "Primero debes capturar el formulario web."
            )

    def _on_selection_completed(self, field_name: str, rect: QRect):
        """Maneja cuando se completa una selección."""
        # Guardar región
        self.field_regions[field_name] = (rect.x(), rect.y(), rect.width(), rect.height())

        # Marcar campo como completado en la lista
        for i in range(self.list_fields.count()):
            item = self.list_fields.item(i)
            item_field = item.text().split(" ", 1)[1] if " " in item.text() else item.text()
            if item_field == field_name:
                item.setText(f"✓ {field_name}")
                item.setForeground(QColor("#2e7d32"))
                break

        # Limpiar selección actual
        self.current_field_name = None
        self.lbl_current_field.setText("Selecciona otro campo de la lista")

        # Mensaje
        QMessageBox.information(
            self,
            "Campo Guardado",
            f"Región guardada para '{field_name}':\n\n"
            f"X: {rect.x()}, Y: {rect.y()}\n"
            f"Ancho: {rect.width()}, Alto: {rect.height()}"
        )

    def _save_configuration(self):
        """Guarda la configuración a YAML."""
        if not self.field_regions:
            QMessageBox.warning(
                self,
                "Sin Campos",
                "No hay campos configurados para guardar."
            )
            return

        config = {
            'ocr': {
                'tesseract': {
                    'field_regions': {}
                }
            }
        }

        for field_name, (x, y, w, h) in self.field_regions.items():
            config['ocr']['tesseract']['field_regions'][field_name] = {
                'x': x,
                'y': y,
                'width': w,
                'height': h
            }

        yaml_text = yaml.dump(config, default_flow_style=False, allow_unicode=True)

        # Mostrar configuración
        msg = QMessageBox(self)
        msg.setWindowTitle("Configuración Generada")
        msg.setText(
            f"Se configuraron {len(self.field_regions)} campos.\n\n"
            "Copia esta configuración a config/settings.yaml:"
        )
        msg.setDetailedText(yaml_text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

        print("\n" + "="*70)
        print("CONFIGURACIÓN YAML GENERADA:")
        print("="*70)
        print(yaml_text)
        print("="*70)

    def get_field_regions(self) -> Dict[str, Tuple[int, int, int, int]]:
        """Obtiene las regiones configuradas."""
        return self.field_regions.copy()


class SelectionCanvas(QWidget):
    """Canvas para dibujar selecciones de campos."""

    selection_completed = pyqtSignal(str, QRect)  # field_name, rect

    def __init__(self, parent=None):
        """Inicializa el canvas."""
        super().__init__(parent)
        self.image: Optional[QPixmap] = None
        self.saved_regions: Dict[str, QRect] = {}
        self.current_field: Optional[str] = None

        # Estado de selección
        self.selecting = False
        self.selection_start: Optional[QPoint] = None
        self.selection_end: Optional[QPoint] = None
        self.selection_enabled = False

        self.setMinimumSize(600, 400)
        self.setStyleSheet("background-color: #f0f0f0; border: 2px solid #ccc;")
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def set_image(self, pixmap: QPixmap):
        """Establece la imagen de fondo."""
        self.image = pixmap
        self.update()

    def set_current_field(self, field_name: str):
        """Establece el campo actual a seleccionar."""
        self.current_field = field_name

    def enable_selection(self):
        """Habilita el modo de selección."""
        self.selection_enabled = True
        self.setCursor(Qt.CursorShape.CrossCursor)

    def mousePressEvent(self, event):
        """Inicia la selección."""
        if not self.selection_enabled or not self.current_field:
            return

        if event.button() == Qt.MouseButton.LeftButton:
            self.selecting = True
            self.selection_start = event.pos()
            self.selection_end = event.pos()

    def mouseMoveEvent(self, event):
        """Actualiza la selección."""
        if self.selecting:
            self.selection_end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        """Finaliza la selección."""
        if not self.selecting:
            return

        if event.button() == Qt.MouseButton.LeftButton:
            self.selecting = False
            self.selection_end = event.pos()

            # Crear rectángulo
            rect = QRect(self.selection_start, self.selection_end).normalized()

            # Guardar región
            if self.current_field:
                self.saved_regions[self.current_field] = rect
                self.selection_completed.emit(self.current_field, rect)

            # Limpiar selección temporal
            self.selection_start = None
            self.selection_end = None
            self.selection_enabled = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.update()

    def paintEvent(self, event):
        """Dibuja el canvas."""
        super().paintEvent(event)

        painter = QPainter(self)

        # Dibujar imagen de fondo
        if self.image:
            # Escalar imagen para que quepa en el widget
            scaled_image = self.image.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            # Centrar imagen
            x = (self.width() - scaled_image.width()) // 2
            y = (self.height() - scaled_image.height()) // 2
            painter.drawPixmap(x, y, scaled_image)
        else:
            # Sin imagen
            painter.setPen(QColor("#999"))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "Captura el formulario web primero"
            )
            return

        # Dibujar regiones guardadas
        for field_name, rect in self.saved_regions.items():
            painter.setPen(QPen(QColor("#2e7d32"), 2, Qt.PenStyle.SolidLine))
            painter.setBrush(QColor(46, 125, 50, 50))  # Verde semi-transparente
            painter.drawRect(rect)

            # Etiqueta
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.setPen(QColor("#ffffff"))
            painter.drawText(
                rect.x() + 5,
                rect.y() + 15,
                field_name
            )

        # Dibujar selección actual
        if self.selecting and self.selection_start and self.selection_end:
            rect = QRect(self.selection_start, self.selection_end).normalized()
            painter.setPen(QPen(QColor("#1976d2"), 2, Qt.PenStyle.DashLine))
            painter.setBrush(QColor(25, 118, 210, 50))  # Azul semi-transparente
            painter.drawRect(rect)

            # Mostrar dimensiones
            painter.setFont(QFont("Arial", 9))
            painter.setPen(QColor("#ffffff"))
            painter.drawText(
                rect.x() + 5,
                rect.y() - 5,
                f"{rect.width()}x{rect.height()}"
            )
