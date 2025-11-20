"""Diálogos de validación para el sistema OCR dual."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QTextEdit, QFrame, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import Optional

from ...domain.entities import ValidationResult, ValidationStatus


class ValidationAlertDialog(QDialog):
    """
    Diálogo de alerta para validación de datos manuscritos vs digitales.

    Muestra comparación de campos y permite al usuario decidir la acción.
    """

    def __init__(
        self,
        validation_result: ValidationResult,
        row_number: int,
        parent=None
    ):
        """
        Inicializa el diálogo de alerta.

        Args:
            validation_result: Resultado de validación fuzzy
            row_number: Número de renglón (1-indexed)
            parent: Widget padre
        """
        super().__init__(parent)
        self.validation_result = validation_result
        self.row_number = row_number
        self.user_action = None

        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz del diálogo."""
        self.setWindowTitle(f"Validación Requerida - Renglón {self.row_number}")
        self.setMinimumWidth(600)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Título según status
        title = self._create_title_label()
        layout.addWidget(title)

        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # Comparación de datos
        layout.addWidget(self._create_comparison_section())

        # Detalles de matches
        if self.validation_result.matches:
            layout.addWidget(self._create_matches_section())

        # Detalles adicionales
        if self.validation_result.details:
            details_label = QLabel(f"<b>Detalles:</b> {self.validation_result.details}")
            details_label.setWordWrap(True)
            layout.addWidget(details_label)

        # Separador
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator2)

        # Botones de acción
        layout.addWidget(self._create_action_buttons())

        # Aplicar estilos
        self._apply_styles()

    def _create_title_label(self) -> QLabel:
        """Crea el label de título según el status."""
        if self.validation_result.status == ValidationStatus.ERROR:
            icon = "❌"
            text = "ERROR - Validación Fallida"
            color = "#d32f2f"
        elif self.validation_result.status == ValidationStatus.WARNING:
            icon = "⚠️"
            text = "ADVERTENCIA - Requiere Validación Manual"
            color = "#f57c00"
        else:
            icon = "ℹ️"
            text = "INFORMACIÓN"
            color = "#1976d2"

        label = QLabel(f"{icon} <b>{text}</b>")
        label.setStyleSheet(f"color: {color}; font-size: 16px; padding: 10px;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        return label

    def _create_comparison_section(self) -> QGroupBox:
        """Crea la sección de comparación manuscrito vs digital."""
        group = QGroupBox("Comparación de Datos")
        layout = QVBoxLayout()

        # Manuscrito
        manuscrito_label = QLabel(
            f"<b>📝 Manuscrito:</b><br>"
            f"<span style='font-size: 14px; color: #1565c0;'>{self.validation_result.manuscrito_nombres}</span>"
        )
        manuscrito_label.setWordWrap(True)
        layout.addWidget(manuscrito_label)

        # Digital
        digital_label = QLabel(
            f"<b>💻 Digital (BD):</b><br>"
            f"<span style='font-size: 14px; color: #2e7d32;'>{self.validation_result.digital_nombres}</span>"
        )
        digital_label.setWordWrap(True)
        layout.addWidget(digital_label)

        # Confianza
        confidence_text = f"<b>Confianza:</b> {self.validation_result.confidence:.0%}"
        if self.validation_result.confidence >= 0.85:
            confidence_color = "#2e7d32"
        elif self.validation_result.confidence >= 0.70:
            confidence_color = "#f57c00"
        else:
            confidence_color = "#d32f2f"

        confidence_label = QLabel(f"<span style='color: {confidence_color};'>{confidence_text}</span>")
        layout.addWidget(confidence_label)

        group.setLayout(layout)
        return group

    def _create_matches_section(self) -> QGroupBox:
        """Crea la sección de detalles de matches campo por campo."""
        group = QGroupBox("Detalle de Campos")
        layout = QVBoxLayout()

        for field_name, match in self.validation_result.matches.items():
            # Icono según match
            icon = "✓" if match.match else "✗"
            color = "#2e7d32" if match.match else "#d32f2f"

            # Label del campo
            field_label = QLabel(
                f"<span style='color: {color};'><b>{icon} {field_name}:</b></span> "
                f"{match.compared} "
                f"<span style='color: #666;'>({match.similarity:.0%})</span>"
            )
            field_label.setWordWrap(True)
            layout.addWidget(field_label)

        group.setLayout(layout)
        return group

    def _create_action_buttons(self) -> QWidget:
        """Crea los botones de acción."""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Botón guardar de todas formas
        btn_save = QPushButton("✓ Guardar de Todas Formas")
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
        btn_save.clicked.connect(lambda: self._set_action("save"))
        layout.addWidget(btn_save)

        # Botón saltar
        btn_skip = QPushButton("⏭️ Saltar Renglón")
        btn_skip.setStyleSheet("""
            QPushButton {
                background-color: #f57c00;
                color: white;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #fb8c00;
            }
        """)
        btn_skip.clicked.connect(lambda: self._set_action("skip"))
        layout.addWidget(btn_skip)

        # Botón corregir manualmente
        btn_correct = QPushButton("✏️ Corregir Manualmente")
        btn_correct.setStyleSheet("""
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
        btn_correct.clicked.connect(lambda: self._set_action("correct"))
        layout.addWidget(btn_correct)

        # Botón cancelar (pausar proceso)
        btn_cancel = QPushButton("⏸️ Pausar Proceso")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e53935;
            }
        """)
        btn_cancel.clicked.connect(lambda: self._set_action("pause"))
        layout.addWidget(btn_cancel)

        return widget

    def _set_action(self, action: str):
        """
        Establece la acción del usuario y cierra el diálogo.

        Args:
            action: Acción seleccionada (save, skip, correct, pause)
        """
        self.user_action = action
        self.accept()

    def _apply_styles(self):
        """Aplica estilos al diálogo."""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
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
            QLabel {
                padding: 5px;
            }
        """)

    def get_user_action(self) -> Optional[str]:
        """
        Obtiene la acción seleccionada por el usuario.

        Returns:
            Acción seleccionada o None si se cerró el diálogo
        """
        return self.user_action


class PersonNotFoundDialog(QDialog):
    """
    Diálogo de alerta cuando una persona no se encuentra en la base de datos.
    """

    def __init__(
        self,
        cedula: str,
        nombres_manuscritos: str,
        row_number: int,
        parent=None
    ):
        """
        Inicializa el diálogo.

        Args:
            cedula: Cédula consultada
            nombres_manuscritos: Nombres del formulario manuscrito
            row_number: Número de renglón
            parent: Widget padre
        """
        super().__init__(parent)
        self.cedula = cedula
        self.nombres_manuscritos = nombres_manuscritos
        self.row_number = row_number
        self.user_action = None

        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz del diálogo."""
        self.setWindowTitle(f"Persona No Encontrada - Renglón {self.row_number}")
        self.setMinimumWidth(500)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Título
        title = QLabel("❌ <b>PERSONA NO ENCONTRADA EN BASE DE DATOS</b>")
        title.setStyleSheet("color: #d32f2f; font-size: 16px; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # Información
        info_group = QGroupBox("Datos del Formulario Manuscrito")
        info_layout = QVBoxLayout()

        cedula_label = QLabel(f"<b>🔢 Cédula:</b> <span style='font-size: 14px;'>{self.cedula}</span>")
        info_layout.addWidget(cedula_label)

        nombres_label = QLabel(f"<b>📝 Nombres:</b> <span style='font-size: 14px;'>{self.nombres_manuscritos}</span>")
        nombres_label.setWordWrap(True)
        info_layout.addWidget(nombres_label)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Mensaje
        msg_label = QLabel(
            "Esta cédula no existe en la base de datos o no se pudo encontrar información asociada. "
            "Por favor, verifica si:<br><br>"
            "• La cédula fue digitada correctamente<br>"
            "• La persona está registrada en el sistema<br>"
            "• Existe alguna novedad a reportar"
        )
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(msg_label)

        # Separador
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator2)

        # Botones
        layout.addWidget(self._create_action_buttons())

        # Estilos
        self._apply_styles()

    def _create_action_buttons(self) -> QWidget:
        """Crea los botones de acción."""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Botón continuar
        btn_continue = QPushButton("➡️ Continuar con Siguiente")
        btn_continue.setStyleSheet("""
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
        btn_continue.clicked.connect(lambda: self._set_action("continue"))
        layout.addWidget(btn_continue)

        # Botón marcar novedad
        btn_mark_issue = QPushButton("⚠️ Marcar Novedad")
        btn_mark_issue.setStyleSheet("""
            QPushButton {
                background-color: #f57c00;
                color: white;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #fb8c00;
            }
        """)
        btn_mark_issue.clicked.connect(lambda: self._set_action("mark_issue"))
        layout.addWidget(btn_mark_issue)

        # Botón pausar
        btn_pause = QPushButton("⏸️ Pausar Proceso")
        btn_pause.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e53935;
            }
        """)
        btn_pause.clicked.connect(lambda: self._set_action("pause"))
        layout.addWidget(btn_pause)

        return widget

    def _set_action(self, action: str):
        """Establece la acción y cierra el diálogo."""
        self.user_action = action
        self.accept()

    def _apply_styles(self):
        """Aplica estilos al diálogo."""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
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

    def get_user_action(self) -> Optional[str]:
        """Obtiene la acción seleccionada."""
        return self.user_action
