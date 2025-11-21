"""Ventana principal de la aplicación."""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QListWidgetItem,
    QTextEdit, QGroupBox, QProgressBar, QMessageBox,
    QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QImage, QFont
from PIL import Image
from typing import Optional, List

from ...domain.entities import CedulaRecord, ProcessingSession, SessionStatus
from .progress_panel import ProgressPanel


class MainWindow(QMainWindow):
    """
    Ventana principal de la aplicación.

    Signals:
        select_area_requested: Solicita selección de área
        capture_requested: Solicita captura de pantalla
        extract_requested: Solicita extracción de cédulas
        start_processing_requested: Solicita inicio de procesamiento
        next_record_requested: Solicita procesar siguiente registro
        pause_requested: Solicita pausar procesamiento
        resume_requested: Solicita reanudar procesamiento
    """

    select_area_requested = pyqtSignal()
    capture_requested = pyqtSignal()
    extract_requested = pyqtSignal()
    start_processing_requested = pyqtSignal()
    next_record_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    resume_requested = pyqtSignal()
    ocr_dual_processing_requested = pyqtSignal()  # NUEVO: OCR Dual

    def __init__(self):
        """Inicializa la ventana principal."""
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz de usuario."""
        self.setWindowTitle("Asistente de Digitación de Cédulas")
        self.setMinimumSize(1200, 800)  # Ventana más grande
        self.resize(1200, 800)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Sección de captura
        main_layout.addWidget(self._create_capture_section())

        # Sección de vista previa y lista
        content_layout = QHBoxLayout()
        content_layout.addWidget(self._create_preview_section(), 1)
        content_layout.addWidget(self._create_list_section(), 1)
        main_layout.addLayout(content_layout)

        # Sección de control
        main_layout.addWidget(self._create_control_section())

        # NUEVO: Panel de progreso OCR Dual
        self.progress_panel = ProgressPanel()
        self.progress_panel.hide()  # Oculto por defecto, se muestra al iniciar OCR dual
        main_layout.addWidget(self.progress_panel)

        # Sección de logs
        main_layout.addWidget(self._create_log_section())

        # Aplicar estilos
        self._apply_styles()

    def _create_capture_section(self) -> QGroupBox:
        """Crea la sección de captura."""
        group = QGroupBox("1. Captura de Área")
        layout = QHBoxLayout()

        self.btn_select_area = QPushButton("Seleccionar Área (F4)")
        self.btn_select_area.clicked.connect(self.select_area_requested.emit)

        self.btn_capture = QPushButton("Capturar Pantalla")
        self.btn_capture.clicked.connect(self.capture_requested.emit)
        self.btn_capture.setEnabled(False)

        self.btn_extract = QPushButton("Extraer Cédulas")
        self.btn_extract.clicked.connect(self.extract_requested.emit)
        self.btn_extract.setEnabled(False)

        self.lbl_area_info = QLabel("No hay área seleccionada")
        self.lbl_area_info.setStyleSheet("color: #666;")

        layout.addWidget(self.btn_select_area)
        layout.addWidget(self.btn_capture)
        layout.addWidget(self.btn_extract)
        layout.addStretch()
        layout.addWidget(self.lbl_area_info)

        group.setLayout(layout)
        return group

    def _create_preview_section(self) -> QGroupBox:
        """Crea la sección de vista previa."""
        group = QGroupBox("Vista Previa de Captura")
        layout = QVBoxLayout()

        self.lbl_preview = QLabel("Sin captura")
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview.setMinimumSize(500, 400)  # Tamaño más grande
        self.lbl_preview.setScaledContents(False)  # No estirar contenido
        self.lbl_preview.setStyleSheet(
            "QLabel { background-color: #f0f0f0; border: 2px dashed #ccc; padding: 5px; }"
        )

        layout.addWidget(self.lbl_preview)
        group.setLayout(layout)
        return group

    def _create_list_section(self) -> QGroupBox:
        """Crea la sección de lista de cédulas."""
        group = QGroupBox("Cédulas Extraídas")
        layout = QVBoxLayout()

        self.list_cedulas = QListWidget()
        self.list_cedulas.setAlternatingRowColors(True)

        self.lbl_count = QLabel("Total: 0 cédulas")
        self.lbl_count.setStyleSheet("font-weight: bold;")

        layout.addWidget(self.list_cedulas)
        layout.addWidget(self.lbl_count)

        group.setLayout(layout)
        return group

    def _create_control_section(self) -> QGroupBox:
        """Crea la sección de control de procesamiento."""
        group = QGroupBox("2. Control de Procesamiento")
        layout = QVBoxLayout()

        # Botones de control
        btn_layout = QHBoxLayout()

        self.btn_start = QPushButton("Iniciar Procesamiento")
        self.btn_start.clicked.connect(self.start_processing_requested.emit)
        self.btn_start.setEnabled(False)
        self.btn_start.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; }"
            "QPushButton:hover { background-color: #45a049; }"
            "QPushButton:disabled { background-color: #ccc; }"
        )

        self.btn_next = QPushButton("Siguiente (Ctrl+Q)")
        self.btn_next.clicked.connect(self.next_record_requested.emit)
        self.btn_next.setEnabled(False)
        self.btn_next.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 10px; }"
            "QPushButton:hover { background-color: #0b7dda; }"
            "QPushButton:disabled { background-color: #ccc; }"
        )

        self.btn_pause = QPushButton("Pausar (F3)")
        self.btn_pause.clicked.connect(self._toggle_pause)
        self.btn_pause.setEnabled(False)

        # NUEVO: Botón OCR Dual
        self.btn_ocr_dual = QPushButton("🚀 OCR Dual Automático")
        self.btn_ocr_dual.clicked.connect(self.ocr_dual_processing_requested.emit)
        self.btn_ocr_dual.setEnabled(False)
        self.btn_ocr_dual.setStyleSheet(
            "QPushButton { background-color: #9c27b0; color: white; font-weight: bold; padding: 10px; }"
            "QPushButton:hover { background-color: #7b1fa2; }"
            "QPushButton:disabled { background-color: #ccc; }"
        )
        self.btn_ocr_dual.setToolTip("Procesamiento automático con validación inteligente (ESC para pausar)")

        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_next)
        btn_layout.addWidget(self.btn_pause)
        btn_layout.addWidget(self.btn_ocr_dual)

        # Información de progreso
        info_layout = QHBoxLayout()

        self.lbl_current = QLabel("Registro actual: -")
        self.lbl_progress = QLabel("Progreso: 0/0")

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)

        info_layout.addWidget(self.lbl_current)
        info_layout.addStretch()
        info_layout.addWidget(self.lbl_progress)

        layout.addLayout(btn_layout)
        layout.addWidget(self.progress_bar)
        layout.addLayout(info_layout)

        group.setLayout(layout)
        return group

    def _create_log_section(self) -> QGroupBox:
        """Crea la sección de logs."""
        group = QGroupBox("Registro de Actividad")
        layout = QVBoxLayout()

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setMaximumHeight(150)
        self.txt_log.setStyleSheet(
            "QTextEdit { background-color: #1e1e1e; color: #d4d4d4; font-family: Consolas, monospace; }"
        )

        layout.addWidget(self.txt_log)
        group.setLayout(layout)
        return group

    def _apply_styles(self):
        """Aplica estilos globales a la ventana."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QWidget {
                color: #333;
                font-size: 10pt;
            }
            QGroupBox {
                font-weight: bold;
                color: #000;
                border: 2px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #000;
            }
            QLabel {
                color: #333;
            }
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                border: 1px solid #ccc;
                background-color: white;
                color: #000;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
            QPushButton:disabled {
                background-color: #f0f0f0;
                color: #999;
            }
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                color: #000;
            }
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: white;
                text-align: center;
                color: #000;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)

    def _toggle_pause(self):
        """Alterna entre pausar y reanudar."""
        if self.btn_pause.text().startswith("Pausar"):
            self.pause_requested.emit()
        else:
            self.resume_requested.emit()

    def set_area_selected(self, area):
        """Actualiza la información del área seleccionada."""
        self.lbl_area_info.setText(f"Área: {area.width}x{area.height} en ({area.x}, {area.y})")
        self.lbl_area_info.setStyleSheet("color: #4CAF50; font-weight: bold;")
        self.btn_capture.setEnabled(True)

    def set_preview_image(self, image: Image.Image):
        """Muestra la imagen capturada en el preview."""
        # Convertir PIL a QPixmap
        img_rgb = image.convert('RGB')

        # Calcular el stride correcto (bytes por línea)
        bytes_per_line = img_rgb.width * 3
        data = img_rgb.tobytes('raw', 'RGB')

        qimage = QImage(
            data,
            img_rgb.width,
            img_rgb.height,
            bytes_per_line,  # Importante: especificar bytes por línea
            QImage.Format.Format_RGB888
        )
        pixmap = QPixmap.fromImage(qimage)

        # Guardar el pixmap original como atributo para evitar que se destruya
        self.original_pixmap = pixmap

        # Escalar para ajustar al tamaño del label manteniendo aspect ratio
        scaled_pixmap = pixmap.scaled(
            self.lbl_preview.width(),
            self.lbl_preview.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.lbl_preview.setPixmap(scaled_pixmap)
        self.lbl_preview.setScaledContents(False)  # No estirar el contenido
        self.btn_extract.setEnabled(True)

    def set_cedulas_list(self, records: List[CedulaRecord]):
        """Actualiza la lista de cédulas."""
        self.list_cedulas.clear()

        for record in records:
            item_text = f"{record.cedula.value} (Confianza: {record.confidence:.1f}%)"
            item = QListWidgetItem(item_text)
            self.list_cedulas.addItem(item)

        self.lbl_count.setText(f"Total: {len(records)} cédulas")

        if records:
            self.btn_start.setEnabled(True)

    def update_session_ui(self, session: ProcessingSession):
        """Actualiza la UI según el estado de la sesión."""
        if session.status == SessionStatus.RUNNING:
            self.btn_start.setEnabled(False)
            self.btn_next.setEnabled(True)
            self.btn_pause.setEnabled(True)
            self.btn_pause.setText("Pausar (F3)")

            # Destacar registro actual
            current_record = session.get_current_record()
            if current_record:
                self.list_cedulas.setCurrentRow(current_record.index)
                self.lbl_current.setText(f"Registro actual: {current_record.cedula.value}")

        elif session.status == SessionStatus.PAUSED:
            self.btn_pause.setText("Reanudar (F3)")
            self.btn_next.setEnabled(False)

        elif session.status == SessionStatus.COMPLETED:
            self.btn_next.setEnabled(False)
            self.btn_pause.setEnabled(False)
            QMessageBox.information(
                self,
                "Procesamiento Completo",
                f"Se procesaron {session.total_processed} registros.\n"
                f"Errores: {session.total_errors}"
            )

        # Actualizar progreso
        self.lbl_progress.setText(
            f"Progreso: {session.current_index}/{session.total_records}"
        )
        self.progress_bar.setValue(int(session.progress_percentage))

    def add_log(self, message: str, level: str = "INFO"):
        """Agrega un mensaje al log."""
        colors = {
            "INFO": "#4CAF50",
            "WARNING": "#FF9800",
            "ERROR": "#F44336",
            "DEBUG": "#2196F3"
        }

        color = colors.get(level, "#d4d4d4")
        formatted_message = f'<span style="color: {color};">[{level}]</span> {message}'

        self.txt_log.append(formatted_message)

        # Auto-scroll al final
        scrollbar = self.txt_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
