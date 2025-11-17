"""Controlador principal de la aplicación."""
from PyQt6.QtCore import QObject
from typing import Optional

from ..ui import MainWindow, AreaSelectorWidget
from ...application.use_cases import (
    CaptureScreenUseCase,
    ExtractCedulasUseCase,
    ProcessCedulaUseCase,
    ManageSessionUseCase
)
from ...domain.entities import CaptureArea, SessionStatus
from ...domain.ports import AutomationPort, LoggerPort


class MainController(QObject):
    """
    Controlador principal que conecta la UI con los casos de uso.

    Attributes:
        window: Ventana principal
        capture_use_case: Caso de uso de captura
        extract_use_case: Caso de uso de extracción
        process_use_case: Caso de uso de procesamiento
        session_use_case: Caso de uso de sesión
        automation: Servicio de automatización
        logger: Servicio de logging
    """

    def __init__(
        self,
        window: MainWindow,
        capture_use_case: CaptureScreenUseCase,
        extract_use_case: ExtractCedulasUseCase,
        process_use_case: ProcessCedulaUseCase,
        session_use_case: ManageSessionUseCase,
        automation: AutomationPort,
        logger: LoggerPort
    ):
        """
        Inicializa el controlador.

        Args:
            window: Ventana principal
            capture_use_case: Caso de uso de captura
            extract_use_case: Caso de uso de extracción
            process_use_case: Caso de uso de procesamiento
            session_use_case: Caso de uso de sesión
            automation: Servicio de automatización
            logger: Servicio de logging
        """
        super().__init__()
        self.window = window
        self.capture_use_case = capture_use_case
        self.extract_use_case = extract_use_case
        self.process_use_case = process_use_case
        self.session_use_case = session_use_case
        self.automation = automation
        self.logger = logger.bind(component="MainController")

        self.current_area: Optional[CaptureArea] = None
        self.current_image = None
        self.area_selector = None  # Guardar referencia al selector

        # Throttling para evitar presionar Ctrl+Q demasiado rápido
        self._last_next_record_time = 0
        self._next_record_cooldown = 0.5  # 500ms mínimo entre pulsaciones

        self._connect_signals()
        self._register_hotkeys()

        # Intentar cargar área guardada
        self._load_saved_area()

    def _connect_signals(self):
        """Conecta las señales de la UI con los handlers."""
        self.window.select_area_requested.connect(self.handle_select_area)
        self.window.capture_requested.connect(self.handle_capture)
        self.window.extract_requested.connect(self.handle_extract)
        self.window.start_processing_requested.connect(self.handle_start_processing)
        self.window.next_record_requested.connect(self.handle_next_record)
        self.window.pause_requested.connect(self.handle_pause)
        self.window.resume_requested.connect(self.handle_resume)

    def _register_hotkeys(self):
        """Registra los atajos de teclado globales."""
        try:
            # Envolver handlers en try-except para evitar crashes
            def safe_handle_next():
                try:
                    self.handle_next_record()
                except Exception as e:
                    self.logger.error("Error en hotkey Ctrl+Q", error=str(e))
                    print(f"ERROR en Ctrl+Q: {e}")
                    import traceback
                    traceback.print_exc()

            def safe_toggle_pause():
                try:
                    self._toggle_pause()
                except Exception as e:
                    self.logger.error("Error en hotkey F3", error=str(e))
                    print(f"ERROR en F3: {e}")

            def safe_select_area():
                try:
                    self.handle_select_area()
                except Exception as e:
                    self.logger.error("Error en hotkey F4", error=str(e))
                    print(f"ERROR en F4: {e}")

            self.automation.register_hotkey('<ctrl>+q', safe_handle_next)
            self.automation.register_hotkey('<f3>', safe_toggle_pause)
            self.automation.register_hotkey('<f4>', safe_select_area)

            self.logger.info("Atajos de teclado registrados", hotkeys="Ctrl+Q, F3, F4")
        except Exception as e:
            self.logger.warning("No se pudieron registrar atajos de teclado", error=str(e))

    def _load_saved_area(self):
        """Intenta cargar el área guardada en configuración."""
        try:
            saved_area = self.capture_use_case.get_saved_area()
            if saved_area:
                self.current_area = saved_area
                self.window.set_area_selected(saved_area)
                self.logger.info("Área de captura cargada desde configuración")
        except Exception as e:
            self.logger.debug("No hay área guardada", error=str(e))

    def handle_select_area(self):
        """Maneja la solicitud de seleccionar área."""
        self.logger.info("Iniciando selección de área")
        self.window.add_log("Seleccione el área de la pantalla a capturar...", "INFO")

        try:
            # Crear selector y guardarlo como variable de instancia
            self.area_selector = AreaSelectorWidget(callback=self._on_area_selected)

            # Conectar señal
            self.area_selector.area_selected.connect(self._on_area_selected)

            # Mostrar el selector
            self.area_selector.show()

            self.logger.info("Selector de área creado y mostrado")

        except Exception as e:
            self.logger.error("Error al abrir selector de área", error=str(e))
            self.window.add_log(f"Error: {str(e)}", "ERROR")

    def _on_area_selected(self, area: CaptureArea):
        """Callback cuando se selecciona un área."""
        try:
            self.current_area = area
            self.capture_use_case.config.set('capture_area', area.to_dict())
            self.capture_use_case.config.save()

            self.window.set_area_selected(area)
            self.window.add_log(
                f"Área seleccionada: {area.width}x{area.height}",
                "INFO"
            )

            self.logger.info(
                "Área seleccionada",
                width=area.width,
                height=area.height,
                x=area.x,
                y=area.y
            )

            # Limpiar referencia al selector para liberar memoria
            if self.area_selector:
                self.area_selector.deleteLater()
                self.area_selector = None

        except Exception as e:
            self.logger.error("Error al guardar área", error=str(e))
            self.window.add_log(f"Error al guardar área: {str(e)}", "ERROR")

    def handle_capture(self):
        """Maneja la solicitud de captura de pantalla."""
        if not self.current_area:
            self.window.add_log("Primero seleccione un área", "WARNING")
            return

        self.logger.info("Capturando pantalla")
        self.window.add_log("Capturando pantalla...", "INFO")

        try:
            # Dar tiempo para que la ventana se oculte si es necesario
            self.window.setWindowOpacity(0.0)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(500, self._perform_capture)

        except Exception as e:
            self.logger.error("Error al capturar", error=str(e))
            self.window.add_log(f"Error: {str(e)}", "ERROR")
            self.window.setWindowOpacity(1.0)

    def _perform_capture(self):
        """Realiza la captura después de un delay."""
        try:
            self.current_image = self.capture_use_case.capture(self.current_area)

            self.window.setWindowOpacity(1.0)
            self.window.set_preview_image(self.current_image)
            self.window.add_log("Captura completada", "INFO")

            self.logger.info(
                "Captura exitosa",
                image_size=(self.current_image.width, self.current_image.height)
            )

        except Exception as e:
            self.window.setWindowOpacity(1.0)
            self.logger.error("Error al capturar", error=str(e))
            self.window.add_log(f"Error: {str(e)}", "ERROR")

    def handle_extract(self):
        """Maneja la solicitud de extracción de cédulas."""
        from PyQt6.QtCore import QTimer

        if not self.current_image:
            self.window.add_log("Primero capture una imagen", "WARNING")
            return

        # Desactivar botón inmediatamente para evitar doble clic
        self.window.btn_extract.setEnabled(False)
        self.window.add_log("⏳ Botón bloqueado por 3 segundos para evitar doble llamada a la API...", "INFO")

        self.logger.info("Extrayendo cédulas")
        self.window.add_log("Extrayendo cédulas con OCR...", "INFO")

        try:
            records = self.extract_use_case.execute(self.current_image)

            if not records:
                self.window.add_log("No se encontraron cédulas válidas", "WARNING")
                # Reactivar botón después de 3 segundos incluso si no hay resultados
                QTimer.singleShot(3000, lambda: self.window.btn_extract.setEnabled(True))
                return

            self.window.set_cedulas_list(records)
            self.window.add_log(f"Se extrajeron {len(records)} cédulas", "INFO")

            # Crear sesión con los registros extraídos
            self.session_use_case.create_session(records)
            self.logger.info("Extracción completada", total=len(records))

            # Reactivar botón después de 3 segundos
            QTimer.singleShot(3000, lambda: self.window.btn_extract.setEnabled(True))

        except Exception as e:
            self.logger.error("Error al extraer cédulas", error=str(e))
            self.window.add_log(f"Error: {str(e)}", "ERROR")

            # Reactivar botón después de 3 segundos incluso en caso de error
            QTimer.singleShot(3000, lambda: self.window.btn_extract.setEnabled(True))

    def handle_start_processing(self):
        """Maneja el inicio del procesamiento."""
        self.logger.info("Iniciando procesamiento")
        self.window.add_log("Iniciando procesamiento de cédulas...", "INFO")

        try:
            # Obtener registros de la lista
            list_widget = self.window.list_cedulas
            if list_widget.count() == 0:
                self.window.add_log("No hay cédulas para procesar", "WARNING")
                return

            # Crear sesión desde los registros actuales
            # (los registros ya deberían estar en el session_use_case desde extract)
            session = self.session_use_case.get_session()

            if session.total_records == 0:
                self.window.add_log("No hay registros en la sesión", "WARNING")
                return

            # Iniciar sesión
            self.session_use_case.start_session()
            self.window.update_session_ui(session)

            self.window.add_log(
                f"Procesamiento iniciado. Total: {session.total_records} registros",
                "INFO"
            )
            self.window.add_log(
                "⚠️ IMPORTANTE: Abre la ventana/página donde vas a escribir las cédulas",
                "INFO"
            )
            self.window.add_log(
                "Al presionar Ctrl+Q, se hará Alt+Tab automáticamente para cambiar de ventana",
                "INFO"
            )

            self.logger.info("Sesión iniciada", total_records=session.total_records)

        except Exception as e:
            self.logger.error("Error al iniciar procesamiento", error=str(e))
            self.window.add_log(f"Error: {str(e)}", "ERROR")

    def handle_next_record(self):
        """Maneja el procesamiento del siguiente registro."""
        import time

        try:
            # Throttling: Ignorar si se presionó muy rápido
            current_time = time.time()
            time_since_last = current_time - self._last_next_record_time

            if time_since_last < self._next_record_cooldown:
                self.logger.debug(
                    "Ignorando Ctrl+Q (presionado muy rápido)",
                    time_since_last=f"{time_since_last:.2f}s"
                )
                return

            self._last_next_record_time = current_time

            session = self.session_use_case.get_session()

            if session.status != SessionStatus.RUNNING:
                self.logger.debug("Sesión no está en estado RUNNING, ignorando Ctrl+Q")
                return

            record = session.get_current_record()

            if not record:
                self.window.add_log("No hay más registros para procesar", "INFO")
                self.logger.info("No hay más registros")
                return

            self.logger.info("Procesando registro", cedula=record.cedula, index=record.index)
            self.window.add_log(f"Procesando: {record.cedula}", "INFO")

            # Procesar la cédula
            success = self.process_use_case.execute(record)

            if success:
                self.window.add_log(
                    f"Cédula {record.cedula} procesada correctamente",
                    "INFO"
                )
            else:
                self.window.add_log(
                    f"Error al procesar cédula {record.cedula}",
                    "ERROR"
                )

            # Avanzar al siguiente
            self.session_use_case.advance(success)
            self.window.update_session_ui(session)

        except Exception as e:
            self.logger.error("Error al procesar registro", error=str(e))
            self.window.add_log(f"Error al procesar registro: {str(e)}", "ERROR")
            import traceback
            traceback.print_exc()

    def handle_pause(self):
        """Maneja la pausa del procesamiento."""
        try:
            self.session_use_case.pause_session()
            session = self.session_use_case.get_session()
            self.window.update_session_ui(session)
            self.window.add_log("Procesamiento pausado", "INFO")
            self.logger.info("Procesamiento pausado")
        except Exception as e:
            self.logger.error("Error al pausar", error=str(e))

    def handle_resume(self):
        """Maneja la reanudación del procesamiento."""
        try:
            self.session_use_case.resume_session()
            session = self.session_use_case.get_session()
            self.window.update_session_ui(session)
            self.window.add_log("Procesamiento reanudado", "INFO")
            self.logger.info("Procesamiento reanudado")
        except Exception as e:
            self.logger.error("Error al reanudar", error=str(e))

    def _toggle_pause(self):
        """Alterna entre pausar y reanudar."""
        session = self.session_use_case.get_session()
        if session.status == SessionStatus.RUNNING:
            self.handle_pause()
        elif session.status == SessionStatus.PAUSED:
            self.handle_resume()

    def on_extract_completed(self, records):
        """Callback cuando se completa la extracción."""
        try:
            # Crear sesión con los registros extraídos
            self.session_use_case.create_session(records)
            self.logger.info("Sesión creada con registros extraídos", total=len(records))
        except Exception as e:
            self.logger.error("Error al crear sesión", error=str(e))
