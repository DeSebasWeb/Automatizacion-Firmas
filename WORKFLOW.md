# Flujo de Trabajo Detallado

## Diagrama de Flujo General

```
┌─────────────────────────────────────────────────────────────┐
│                     INICIO DE APLICACIÓN                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              1. CONFIGURACIÓN DE ÁREA                       │
│                                                             │
│  ┌──────────────────────────────────────────────┐          │
│  │ Usuario presiona "Seleccionar Área (F4)"     │          │
│  └────────────────┬─────────────────────────────┘          │
│                   │                                         │
│                   ▼                                         │
│  ┌──────────────────────────────────────────────┐          │
│  │ Selector de pantalla completo se muestra     │          │
│  │ con overlay semi-transparente                │          │
│  └────────────────┬─────────────────────────────┘          │
│                   │                                         │
│                   ▼                                         │
│  ┌──────────────────────────────────────────────┐          │
│  │ Usuario arrastra mouse para seleccionar      │          │
│  │ área rectangular sobre la pantalla           │          │
│  └────────────────┬─────────────────────────────┘          │
│                   │                                         │
│                   ▼                                         │
│  ┌──────────────────────────────────────────────┐          │
│  │ Coordenadas (x, y, width, height)            │          │
│  │ se guardan en config/settings.yaml           │          │
│  └──────────────────────────────────────────────┘          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              2. CAPTURA DE PANTALLA                         │
│                                                             │
│  ┌──────────────────────────────────────────────┐          │
│  │ Usuario presiona "Capturar Pantalla"         │          │
│  └────────────────┬─────────────────────────────┘          │
│                   │                                         │
│                   ▼                                         │
│  ┌──────────────────────────────────────────────┐          │
│  │ Ventana se oculta temporalmente (500ms)      │          │
│  └────────────────┬─────────────────────────────┘          │
│                   │                                         │
│                   ▼                                         │
│  ┌──────────────────────────────────────────────┐          │
│  │ PyAutoGUI captura área configurada           │          │
│  └────────────────┬─────────────────────────────┘          │
│                   │                                         │
│                   ▼                                         │
│  ┌──────────────────────────────────────────────┐          │
│  │ Imagen se muestra en Vista Previa            │          │
│  │ Ventana se restaura                          │          │
│  └──────────────────────────────────────────────┘          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              3. EXTRACCIÓN DE CÉDULAS (OCR)                 │
│                                                             │
│  ┌──────────────────────────────────────────────┐          │
│  │ Usuario presiona "Extraer Cédulas"           │          │
│  └────────────────┬─────────────────────────────┘          │
│                   │                                         │
│                   ▼                                         │
│  ┌──────────────────────────────────────────────┐          │
│  │ PRE-PROCESAMIENTO DE IMAGEN:                 │          │
│  │  • Conversión a escala de grises             │          │
│  │  • Redimensionamiento (2x)                   │          │
│  │  • Reducción de ruido                        │          │
│  │  • Binarización adaptativa                   │          │
│  │  • Mejora de contraste (CLAHE)               │          │
│  └────────────────┬─────────────────────────────┘          │
│                   │                                         │
│                   ▼                                         │
│  ┌──────────────────────────────────────────────┐          │
│  │ TESSERACT OCR:                               │          │
│  │  • Extrae texto con coordenadas              │          │
│  │  • Filtra solo números (0-9)                 │          │
│  │  • Valida formato de cédula (6-15 dígitos)   │          │
│  │  • Calcula nivel de confianza                │          │
│  └────────────────┬─────────────────────────────┘          │
│                   │                                         │
│                   ▼                                         │
│  ┌──────────────────────────────────────────────┐          │
│  │ VALIDACIÓN Y FILTRADO:                       │          │
│  │  • Elimina duplicados                        │          │
│  │  • Descarta confianza < min_confidence       │          │
│  │  • Crea CedulaRecord para cada una           │          │
│  └────────────────┬─────────────────────────────┘          │
│                   │                                         │
│                   ▼                                         │
│  ┌──────────────────────────────────────────────┐          │
│  │ Lista de cédulas se muestra en UI            │          │
│  │ Se crea ProcessingSession                    │          │
│  └──────────────────────────────────────────────┘          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              4. PROCESAMIENTO AUTOMÁTICO                    │
│                                                             │
│  ┌──────────────────────────────────────────────┐          │
│  │ Usuario presiona "Iniciar Procesamiento"     │          │
│  └────────────────┬─────────────────────────────┘          │
│                   │                                         │
│                   ▼                                         │
│  ┌──────────────────────────────────────────────┐          │
│  │ Sesión cambia a estado RUNNING               │          │
│  │ current_index = 0                            │          │
│  └────────────────┬─────────────────────────────┘          │
│                   │                                         │
│                   ▼                                         │
│  ┌──────────────────────────────────────────────┐          │
│  │ CICLO DE PROCESAMIENTO:                      │          │
│  │                                              │          │
│  │  ┌────────────────────────────────────┐     │          │
│  │  │ 1. Obtener registro actual         │     │          │
│  │  └───────────────┬────────────────────┘     │          │
│  │                  │                           │          │
│  │                  ▼                           │          │
│  │  ┌────────────────────────────────────┐     │          │
│  │  │ 2. Click en campo de búsqueda      │     │          │
│  │  │    (coordenadas configuradas)      │     │          │
│  │  └───────────────┬────────────────────┘     │          │
│  │                  │                           │          │
│  │                  ▼                           │          │
│  │  ┌────────────────────────────────────┐     │          │
│  │  │ 3. Limpiar campo (Ctrl+A + Del)    │     │          │
│  │  └───────────────┬────────────────────┘     │          │
│  │                  │                           │          │
│  │                  ▼                           │          │
│  │  ┌────────────────────────────────────┐     │          │
│  │  │ 4. Digitar cédula                  │     │          │
│  │  │    (con intervalo configurado)     │     │          │
│  │  └───────────────┬────────────────────┘     │          │
│  │                  │                           │          │
│  │                  ▼                           │          │
│  │  ┌────────────────────────────────────┐     │          │
│  │  │ 5. Esperar pre_enter_delay         │     │          │
│  │  └───────────────┬────────────────────┘     │          │
│  │                  │                           │          │
│  │                  ▼                           │          │
│  │  ┌────────────────────────────────────┐     │          │
│  │  │ 6. Presionar Enter                 │     │          │
│  │  └───────────────┬────────────────────┘     │          │
│  │                  │                           │          │
│  │                  ▼                           │          │
│  │  ┌────────────────────────────────────┐     │          │
│  │  │ 7. Esperar post_enter_delay        │     │          │
│  │  └───────────────┬────────────────────┘     │          │
│  │                  │                           │          │
│  │                  ▼                           │          │
│  │  ┌────────────────────────────────────┐     │          │
│  │  │ 8. Marcar registro como procesado  │     │          │
│  │  └───────────────┬────────────────────┘     │          │
│  │                  │                           │          │
│  │                  ▼                           │          │
│  │  ┌────────────────────────────────────┐     │          │
│  │  │ 9. ESPERAR USUARIO                 │     │          │
│  │  │    (presionar F2 o "Siguiente")    │     │          │
│  │  └───────────────┬────────────────────┘     │          │
│  │                  │                           │          │
│  │                  ▼                           │          │
│  │  ┌────────────────────────────────────┐     │          │
│  │  │ Usuario valida manualmente         │     │          │
│  │  └───────────────┬────────────────────┘     │          │
│  │                  │                           │          │
│  │                  ▼                           │          │
│  │  ┌────────────────────────────────────┐     │          │
│  │  │ Usuario presiona F2                │     │          │
│  │  └───────────────┬────────────────────┘     │          │
│  │                  │                           │          │
│  │                  ▼                           │          │
│  │  ┌────────────────────────────────────┐     │          │
│  │  │ current_index++                    │     │          │
│  │  └───────────────┬────────────────────┘     │          │
│  │                  │                           │          │
│  │                  ▼                           │          │
│  │            ¿Hay más registros?              │          │
│  │                  │                           │          │
│  │         Sí ◄─────┴─────► No                 │          │
│  │         │                │                   │          │
│  │         └────────┐       ▼                   │          │
│  │        (repetir) │  Completar sesión         │          │
│  │                  │                           │          │
│  └──────────────────┴───────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## Estados de la Sesión

```
IDLE ──────► READY ──────► RUNNING ◄──────┐
                              │            │
                              ▼            │
                           PAUSED ─────────┘
                              │
                              ▼
                          COMPLETED
```

## Estados de un Registro

```
PENDING ──► PROCESSING ──► COMPLETED
                │
                ├──────► ERROR
                │
                └──────► SKIPPED
```

## Diagrama de Secuencia - Procesamiento de Cédula

```
Usuario    MainWindow    Controller    ProcessUseCase    Automation
   │            │             │                │              │
   │ Click F2   │             │                │              │
   ├───────────►│             │                │              │
   │            │ Signal      │                │              │
   │            ├────────────►│                │              │
   │            │             │ execute()      │              │
   │            │             ├───────────────►│              │
   │            │             │                │ click()      │
   │            │             │                ├─────────────►│
   │            │             │                │ type_text()  │
   │            │             │                ├─────────────►│
   │            │             │                │ press_key()  │
   │            │             │                ├─────────────►│
   │            │             │   success      │              │
   │            │             │◄───────────────┤              │
   │            │ update_ui() │                │              │
   │            │◄────────────┤                │              │
   │ UI Update  │             │                │              │
   │◄───────────┤             │                │              │
   │            │             │                │              │
```

## Flujo de Datos

```
Imagen Capturada
       │
       ▼
Pre-procesamiento
       │
       ▼
OCR (Tesseract)
       │
       ▼
Texto Crudo + Confianza
       │
       ▼
Validación de Formato
       │
       ▼
CedulaRecord Objects
       │
       ▼
ProcessingSession
       │
       ▼
Automatización de Digitación
       │
       ▼
Logging + Estadísticas
```

## Manejo de Errores

```
Operación ───► ¿Éxito? ───► Sí ───► Continuar
                  │
                  No
                  │
                  ▼
            Catch Exception
                  │
                  ▼
            Log Error
                  │
                  ▼
         Mostrar en UI
                  │
                  ▼
      ¿Crítico? ───► Sí ───► Detener
          │
          No
          │
          ▼
      Continuar con siguiente
```

## Ciclo de Vida de la Aplicación

```
1. Inicialización
   ├─ Cargar configuración
   ├─ Crear logger
   ├─ Inyectar dependencias
   └─ Crear UI

2. Configuración
   ├─ Seleccionar área
   └─ Guardar configuración

3. Procesamiento
   ├─ Capturar
   ├─ Extraer
   └─ Automatizar

4. Finalización
   ├─ Completar sesión
   ├─ Guardar logs
   └─ Cleanup
```

## Interacción Usuario-Sistema

```
┌─────────────────────────────────────────────────┐
│              INTERFAZ DE USUARIO                │
├─────────────────────────────────────────────────┤
│                                                 │
│  [Seleccionar Área]  [Capturar]  [Extraer]     │
│                                                 │
│  ┌──────────────┐  ┌──────────────────────┐    │
│  │  Vista       │  │  Lista de Cédulas    │    │
│  │  Previa      │  │  ┌────────────────┐  │    │
│  │              │  │  │ 12345678 (95%) │  │    │
│  │   [Imagen]   │  │  │ 87654321 (92%) │  │    │
│  │              │  │  │ 11223344 (88%) │◄─┼─── Registro actual
│  │              │  │  └────────────────┘  │    │
│  └──────────────┘  └──────────────────────┘    │
│                                                 │
│  [Iniciar] [Siguiente (F2)] [Pausar (F3)]      │
│                                                 │
│  Progreso: ████████░░░░░░░░░ 50%               │
│  Registro actual: 11223344                      │
│                                                 │
│  ┌──────────────── LOGS ──────────────────┐    │
│  │ [INFO] Cédula procesada: 12345678      │    │
│  │ [INFO] Cédula procesada: 87654321      │    │
│  └─────────────────────────────────────────┘    │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Timing y Delays

```
Operación                      Delay (s)
─────────────────────────────────────────
Click en campo                 0.0
Espera post-click              0.3
Limpiar campo (Ctrl+A)         0.1
Delete                         0.2
Typing (entre teclas)          0.05
Pre-Enter delay                0.3
Press Enter                    0.0
Post-Enter delay               0.5
─────────────────────────────────────────
Total por registro:            ~1.5s + (length * 0.05)
```

## Configuraciones Críticas

| Parámetro | Valor Default | Propósito |
|-----------|---------------|-----------|
| `typing_interval` | 0.05 | Velocidad de tipeo natural |
| `pre_enter_delay` | 0.3 | Asegurar texto completo |
| `post_enter_delay` | 0.5 | Esperar carga del sistema |
| `min_confidence` | 50.0 | Balance precisión/recall |
| `psm` | 6 | Modo de segmentación OCR |

## Puntos de Personalización

1. **OCR**: Cambiar TesseractOCR por EasyOCR
2. **Captura**: Cambiar PyAutoGUI por MSS
3. **Automation**: Cambiar PyAutoGUI por Keyboard
4. **UI**: Cambiar PyQt6 por Tkinter/CustomTkinter
5. **Config**: Cambiar YAML por JSON/TOML
6. **Logging**: Cambiar Structlog por loguru

Todos los cambios se hacen en `main.py` por inyección de dependencias.
