"""Panel de progreso para el procesamiento OCR dual."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QGroupBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class ProgressPanel(QWidget):
    """
    Panel de progreso en tiempo real para el procesamiento OCR dual.

    Muestra estadísticas del procesamiento:
    - Total de renglones
    - Renglones procesados
    - Guardados automáticamente
    - Requirieron validación
    - Renglones vacíos
    - No encontrados
    - Errores
    """

    def __init__(self, parent=None):
        """Inicializa el panel de progreso."""
        super().__init__(parent)
        self.setup_ui()
        self.reset_stats()

    def setup_ui(self):
        """Configura la interfaz del panel."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Título
        title = QLabel("<b>📊 Progreso del Procesamiento OCR Dual</b>")
        title.setStyleSheet("font-size: 14px; color: #1976d2; padding: 5px;")
        layout.addWidget(title)

        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e0e0e0;
                border-radius: 5px;
                text-align: center;
                height: 30px;
            }
            QProgressBar::chunk {
                background-color: #1976d2;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Label de estado actual
        self.lbl_current_state = QLabel("Esperando inicio...")
        self.lbl_current_state.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        self.lbl_current_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_current_state)

        # Estadísticas
        stats_group = QGroupBox("Estadísticas")
        stats_layout = QVBoxLayout()

        # Total de renglones
        self.lbl_total = self._create_stat_label("📋 Total de renglones:", "0", "#666")
        stats_layout.addWidget(self.lbl_total)

        # Procesados
        self.lbl_processed = self._create_stat_label("⚙️ Procesados:", "0 / 0", "#1976d2")
        stats_layout.addWidget(self.lbl_processed)

        # Separador
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        stats_layout.addWidget(separator2)

        # Guardados automáticamente
        self.lbl_auto_saved = self._create_stat_label("✓ Guardados automáticamente:", "0", "#2e7d32")
        stats_layout.addWidget(self.lbl_auto_saved)

        # Requirieron validación
        self.lbl_required_validation = self._create_stat_label("⚠ Requirieron validación:", "0", "#f57c00")
        stats_layout.addWidget(self.lbl_required_validation)

        # Renglones vacíos
        self.lbl_empty_rows = self._create_stat_label("○ Renglones vacíos:", "0", "#9e9e9e")
        stats_layout.addWidget(self.lbl_empty_rows)

        # No encontrados
        self.lbl_not_found = self._create_stat_label("✗ No encontrados:", "0", "#d32f2f")
        stats_layout.addWidget(self.lbl_not_found)

        # Errores
        self.lbl_errors = self._create_stat_label("⚠ Errores:", "0", "#c62828")
        stats_layout.addWidget(self.lbl_errors)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Aplicar estilos
        self._apply_styles()

    def _create_stat_label(self, label_text: str, value: str, color: str) -> QWidget:
        """
        Crea un widget de estadística.

        Args:
            label_text: Texto de la etiqueta
            value: Valor inicial
            color: Color del valor

        Returns:
            Widget contenedor
        """
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 2, 0, 2)

        label = QLabel(label_text)
        label.setStyleSheet("color: #424242;")

        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-weight: bold;")

        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(value_label)

        return widget

    def _apply_styles(self):
        """Aplica estilos al panel."""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

    def reset_stats(self):
        """Resetea las estadísticas a cero."""
        self.update_progress(0, 0, "Esperando inicio...")
        self.update_stats(0, 0, 0, 0, 0, 0, 0)

    def update_progress(self, current: int, total: int, state_text: str = ""):
        """
        Actualiza la barra de progreso.

        Args:
            current: Renglones procesados
            total: Total de renglones
            state_text: Texto de estado actual
        """
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            self.progress_bar.setFormat(f"{current} / {total} ({percentage}%)")
        else:
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("0 / 0 (0%)")

        if state_text:
            self.lbl_current_state.setText(state_text)

    def update_stats(
        self,
        total: int,
        processed: int,
        auto_saved: int,
        required_validation: int,
        empty_rows: int,
        not_found: int,
        errors: int
    ):
        """
        Actualiza todas las estadísticas.

        Args:
            total: Total de renglones
            processed: Renglones procesados
            auto_saved: Guardados automáticamente
            required_validation: Requirieron validación
            empty_rows: Renglones vacíos
            not_found: No encontrados
            errors: Errores
        """
        # Actualizar labels
        self._update_stat_value(self.lbl_total, str(total))
        self._update_stat_value(self.lbl_processed, f"{processed} / {total}")
        self._update_stat_value(self.lbl_auto_saved, str(auto_saved))
        self._update_stat_value(self.lbl_required_validation, str(required_validation))
        self._update_stat_value(self.lbl_empty_rows, str(empty_rows))
        self._update_stat_value(self.lbl_not_found, str(not_found))
        self._update_stat_value(self.lbl_errors, str(errors))

    def _update_stat_value(self, widget: QWidget, value: str):
        """
        Actualiza el valor de una estadística.

        Args:
            widget: Widget contenedor
            value: Nuevo valor
        """
        # El widget es un QWidget con QHBoxLayout
        # El segundo elemento es el label del valor
        layout = widget.layout()
        if layout and layout.count() >= 2:
            value_label = layout.itemAt(layout.count() - 1).widget()
            if isinstance(value_label, QLabel):
                value_label.setText(value)

    def set_state_text(self, text: str, color: str = "#666"):
        """
        Establece el texto de estado actual.

        Args:
            text: Texto de estado
            color: Color del texto
        """
        self.lbl_current_state.setText(text)
        self.lbl_current_state.setStyleSheet(f"color: {color}; font-style: italic; padding: 5px;")

    def set_processing_state(self):
        """Establece el estado a procesando."""
        self.set_state_text("⚙️ Procesando...", "#1976d2")

    def set_paused_state(self):
        """Establece el estado a pausado."""
        self.set_state_text("⏸️ PAUSADO - Presiona F9 para continuar", "#f57c00")

    def set_completed_state(self):
        """Establece el estado a completado."""
        self.set_state_text("✓ COMPLETADO", "#2e7d32")

    def set_error_state(self):
        """Establece el estado a error."""
        self.set_state_text("❌ ERROR", "#d32f2f")
