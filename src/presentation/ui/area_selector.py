"""Widget para seleccionar área de captura de pantalla."""
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QRect, pyqtSignal, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QScreen, QFont
from typing import Optional, Callable

from ...domain.entities import CaptureArea


class AreaSelectorWidget(QWidget):
    """
    Widget de pantalla completa para seleccionar área de captura.

    Signals:
        area_selected: Emitido cuando se selecciona un área
    """

    area_selected = pyqtSignal(CaptureArea)

    def __init__(self, callback: Optional[Callable[[CaptureArea], None]] = None):
        """
        Inicializa el selector de área.

        Args:
            callback: Función a llamar cuando se seleccione el área
        """
        super().__init__()
        self.callback = callback
        self.begin = None
        self.end = None
        self._closing = False  # Flag para prevenir repintado durante cierre

        # Configurar ventana - Sin WA_TranslucentBackground para mejor compatibilidad en Windows
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )

        # Fondo semi-transparente usando setWindowOpacity
        self.setWindowOpacity(0.3)
        self.setCursor(Qt.CursorShape.CrossCursor)

        # Color de fondo
        self.setStyleSheet("background-color: black;")

        # Hacer pantalla completa - obtener geometría de la pantalla
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.geometry()
            self.setGeometry(geometry)
            print(f"DEBUG: Screen geometry: {geometry.width()}x{geometry.height()}")

        # Configurar tamaño mínimo para asegurar visibilidad
        self.setMinimumSize(800, 600)

    def showEvent(self, event):
        """Se ejecuta cuando el widget se muestra."""
        super().showEvent(event)
        print("DEBUG: AreaSelector showEvent - Widget mostrado")
        self.raise_()
        self.activateWindow()

    def paintEvent(self, event):
        """Dibuja la selección en pantalla."""
        # IMPORTANTE: Prevenir cualquier repintado después de cerrar
        if hasattr(self, '_closing') and self._closing:
            print("DEBUG: paintEvent ignorado - widget cerrándose")
            event.accept()
            return

        # Verificar que el widget esté en estado válido
        if not self.isVisible():
            print("DEBUG: paintEvent ignorado - widget no visible")
            event.accept()
            return

        # Usar super().paintEvent primero
        try:
            super().paintEvent(event)
        except Exception as e:
            print(f"DEBUG: Error en super().paintEvent: {e}")

        # Crear painter y asegurar que se cierre
        painter = QPainter()
        try:
            if not painter.begin(self):
                print("DEBUG: No se pudo iniciar painter")
                event.accept()
                return  # No se pudo iniciar el painter

            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            if self.begin and self.end:
                # Calcular rectángulo de selección
                rect = QRect(self.begin, self.end).normalized()

                # Dibujar área seleccionada con borde verde brillante
                pen = QPen(QColor(0, 255, 0), 3, Qt.PenStyle.SolidLine)
                painter.setPen(pen)
                painter.setBrush(QColor(0, 255, 0, 30))  # Relleno verde semi-transparente
                painter.drawRect(rect)

                # Mostrar dimensiones y posición
                painter.setPen(QColor(255, 255, 255))
                font = QFont("Arial", 12, QFont.Weight.Bold)
                painter.setFont(font)

                text = f"{rect.width()} x {rect.height()}"
                text_pos = QPoint(rect.left() + 5, rect.top() - 5)

                # Fondo para el texto
                painter.fillRect(
                    QRect(text_pos.x() - 3, text_pos.y() - 15, 150, 20),
                    QColor(0, 0, 0, 200)
                )
                painter.drawText(text_pos, text)
            else:
                # Mostrar instrucciones
                painter.setPen(QColor(255, 255, 255))
                font = QFont("Arial", 16, QFont.Weight.Bold)
                painter.setFont(font)

                instructions = "Arrastra el mouse para seleccionar el área - Presiona ESC para cancelar"
                text_rect = self.rect()
                text_rect.setTop(50)

                # Fondo para las instrucciones
                painter.fillRect(
                    QRect(self.width() // 2 - 400, 40, 800, 40),
                    QColor(0, 0, 0, 200)
                )
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, instructions)
        except Exception as e:
            print(f"ERROR en paintEvent: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # CRÍTICO: SIEMPRE cerrar el painter
            if painter.isActive():
                painter.end()
            # Aceptar el evento para indicar que lo procesamos
            event.accept()

    def mousePressEvent(self, event):
        """Maneja el evento de presionar el mouse."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.begin = event.pos()
            self.end = event.pos()
            self.update()

    def mouseMoveEvent(self, event):
        """Maneja el evento de mover el mouse."""
        if self.begin:
            self.end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        """Maneja el evento de soltar el mouse."""
        if event.button() == Qt.MouseButton.LeftButton and self.begin and self.end:
            # Calcular área seleccionada
            rect = QRect(self.begin, self.end).normalized()

            area = CaptureArea(
                x=rect.x(),
                y=rect.y(),
                width=rect.width(),
                height=rect.height()
            )

            # Marcar como cerrando para prevenir repintado
            self._closing = True

            # Emitir señal
            self.area_selected.emit(area)

            # Llamar callback si existe
            if self.callback:
                self.callback(area)

            # Cerrar widget
            self.close()

    def keyPressEvent(self, event):
        """Maneja el evento de presionar tecla."""
        if event.key() == Qt.Key.Key_Escape:
            self._closing = True
            self.close()

    def closeEvent(self, event):
        """Maneja el evento de cierre del widget."""
        self._closing = True
        # Desconectar todas las señales para evitar referencias
        try:
            self.area_selected.disconnect()
        except:
            pass
        super().closeEvent(event)
        # Marcar para eliminación inmediata
        self.deleteLater()
