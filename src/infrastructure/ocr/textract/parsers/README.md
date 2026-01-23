# E-14 Modular Parser Architecture

## Arquitectura

Sistema modular para parsing de formularios E-14 siguiendo principios SOLID y patrones de diseño.

```
src/infrastructure/ocr/textract/parsers/
├── __init__.py                    # Módulo principal
├── base_parser.py                 # Abstracción base (Template Method)
├── totales_mesa_parser.py         # Parser de totales (IMPLEMENTADO)
├── divipol_parser.py              # Parser de DIVIPOL
├── partido_parser.py              # Parser de partidos (pendiente)
├── pagina_parser.py               # Parser de número de página
├── e14_parser_service.py          # Orquestador (Chain of Responsibility)
└── README.md                      # Esta documentación
```

## Principios SOLID Aplicados

### 1. Single Responsibility Principle (SRP)
Cada parser tiene una única responsabilidad:
- `TotalesMesaParser`: Solo extrae totales de mesa
- `DivipolParser`: Solo extrae códigos DIVIPOL
- `PartidoParser`: Solo extrae partidos y candidatos
- `PaginaParser`: Solo extrae número de página

### 2. Open/Closed Principle (OCP)
- Extensible mediante herencia de `BaseParser`
- Agregar nuevo parser no modifica código existente
- Ejemplo: Crear `VotosEspecialesParser` sin tocar otros parsers

### 3. Liskov Substitution Principle (LSP)
- Todos los parsers son intercambiables vía `BaseParser`
- `E14ParserService` acepta cualquier implementación de `BaseParser`

### 4. Interface Segregation Principle (ISP)
- Interfaz mínima: solo método `parse(lines) -> dict`
- No métodos innecesarios en la abstracción

### 5. Dependency Inversion Principle (DIP)
- `E14ParserService` depende de `BaseParser` (abstracción)
- No depende de parsers concretos
- Inyección de dependencias en constructor

## Patrones de Diseño

### Strategy Pattern
Cada parser es una estrategia para extraer datos específicos:
```python
# Diferentes estrategias intercambiables
totales_parser = TotalesMesaParser()
divipol_parser = DivipolParser()
```

### Template Method
`BaseParser` define el flujo, subclases implementan detalles:
```python
class BaseParser(ABC):
    def parse(self, lines):
        # Template method
        if not self._validate_lines(lines):
            return {}
        return self._extract_data(lines)  # Implementado por subclases
```

### Chain of Responsibility
Parsers procesan texto secuencialmente:
```python
# E14ParserService coordina la cadena
pagina -> divipol -> totales -> partidos
```

### Observer Pattern
Logging estructurado con `structlog`:
```python
self.logger.info("totales_extracted", sufragantes="134")
```

## TotalesMesaParser - Algoritmo Implementado

### Input
Lista de líneas del OCR horizontal (left→right, top→bottom):
```python
lines = [
    "TOTAL",
    "TOTAL",
    "TOTAL",
    "SUFRAGANTES",
    "VOTOS",
    "VOTOS",
    "FORMATO E-11",
    "EN LA URNA",
    "INCINERADOS",
    "134",
    "131",
    "***"
]
```

### Output
```python
{
    "TotalSufragantesE14": "134",
    "TotalVotosEnUrna": "131",
    "TotalIncinerados": "***"
}
```

### Algoritmo Paso a Paso

#### 1. Detectar inicio del bloque
```python
def _find_totales_block_start(lines) -> Optional[int]:
    # Buscar 3 "TOTAL" consecutivos (ventana de 5 líneas)
    # Retorna índice del primer TOTAL
```

#### 2. Extraer líneas del bloque
```python
def _extract_totales_lines(lines, start_idx) -> List[str]:
    # Extraer líneas después de los 3 TOTAL
    # Hasta encontrar marcador de fin:
    # - "CIRCUNSCRIPCIÓN"
    # - Patrón "X digit-digit-digit-digit X"
    # - Línea vacía
```

#### 3. Reconstruir columnas (patrón modulo)
```python
def _reconstruct_columns(totales_lines) -> List[List[str]]:
    # Texto horizontal → columnas
    # lines[0,3,6,9] = columna 1
    # lines[1,4,7,10] = columna 2
    # lines[2,5,8,11] = columna 3
```

#### 4. Identificar y extraer totales
```python
def _identify_and_extract_totales(columns) -> Dict:
    # Identificar por keywords:
    # - SUFRAGANTES + FORMATO/E-11 → TotalSufragantesE14
    # - VOTOS + URNA → TotalVotosEnUrna
    # - INCINERADOS → TotalIncinerados
    #
    # Valor = ÚLTIMO elemento de columna
    # CRÍTICO: Preservar exactamente, no transformar
```

### Preservación de Valores

**REGLA CRÍTICA**: Nunca transformar valores

```python
# TotalIncinerados puede ser:
"134"      # Número
"***"      # Símbolos
"///"      # Otros símbolos
"XX"       # Texto corrupto
""         # Vacío
```

Se preserva exactamente como aparece en el OCR.

## Cómo Probar desde el Endpoint

### 1. Iniciar el servidor FastAPI

```bash
cd d:/ProyectoFirmasAutomatizacion
python -m uvicorn src.infrastructure.api.main:app --reload
```

### 2. Obtener un token JWT

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "tu_usuario", "password": "tu_password"}'
```

### 3. Procesar un documento E-14 con Textract

```bash
curl -X POST "http://localhost:8000/api/v1/documents/e14/textract" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@ruta/al/e14_sample.jpg"
```

### 4. Verificar la respuesta

```json
{
  "success": true,
  "structured_data": {
    "e14": {
      "pagina": "01 de 09",
      "divipol": {
        "CodDep": "16",
        "CodMun": "001",
        "zona": "01",
        "Puesto": "01",
        "Mesa": "001"
      },
      "TotalSufragantesE14": "134",
      "TotalVotosEnUrna": "131",
      "TotalIncinerados": "***",
      "Partido": [...]
    }
  },
  "raw_ocr_text": "...",
  "warnings": [],
  "processing_time_ms": 1234
}
```

### 5. Verificar logs estructurados

Los logs mostrarán el proceso detallado:

```
totales_block_detected start_line=17
totales_lines_extracted lines=['SUFRAGANTES', 'VOTOS', ...] count=9
columns_reconstructed col1=['SUFRAGANTES', 'FORMATO E-11', '134'] ...
total_sufragantes_detected value='134' column=['SUFRAGANTES', 'FORMATO E-11', '134']
total_votos_urna_detected value='131' column=['VOTOS', 'EN LA URNA', '131']
total_incinerados_detected value='***' column=['VOTOS', 'INCINERADOS', '***']
totales_extracted sufragantes='134' votos_urna='131' incinerados='***'
```

## Ejemplo Completo con Swagger UI

1. Abrir en navegador: `http://localhost:8000/docs`
2. Click en "Authorize" y pegar el JWT token
3. Expandir `/api/v1/documents/e14/textract`
4. Click en "Try it out"
5. Seleccionar archivo E-14
6. Click en "Execute"
7. Ver respuesta JSON estructurada

## Tests

### Ejecutar tests unitarios

```bash
# Con pytest (si está instalado)
pytest tests/parsers/test_totales_mesa_parser.py -v

# Con unittest
python -m unittest discover tests/parsers
```

### Casos de prueba cubiertos

- [x] Patrón horizontal estándar
- [x] TotalIncinerados con números
- [x] TotalIncinerados con símbolos (*, /, #)
- [x] TotalIncinerados vacío
- [x] Múltiples TOTAL en documento
- [x] Columnas incompletas
- [x] Marcadores de fin (CIRCUNSCRIPCIÓN, X-X-X-X)
- [x] Performance < 100ms

## Rendimiento

### Métricas esperadas

- **Parsing por página**: < 100ms
- **Memoria por documento**: < 50MB
- **Cobertura de tests**: > 80%

### Optimizaciones aplicadas

1. **Búsqueda temprana de TOTAL**: Ventana de 5 líneas
2. **Límite de extracción**: Máximo 15 líneas después de TOTAL
3. **Patrón modulo**: O(n) para reconstruir columnas
4. **Sin loops innecesarios**: Comprensiones de listas

## Logging Estructurado

Todos los parsers usan `structlog` para logging estructurado:

```python
import structlog

logger = structlog.get_logger(__name__)

# Logs con contexto
logger.info("totales_extracted",
           sufragantes="134",
           votos_urna="131",
           incinerados="***")

logger.warning("campo_vacio", field="TotalIncinerados")

logger.debug("columns_reconstructed",
            col1=["SUFRAGANTES", "134"],
            col2=["VOTOS", "131"])
```

## Roadmap

### Implementado
- [x] BaseParser (abstracción)
- [x] TotalesMesaParser (algoritmo completo)
- [x] DivipolParser
- [x] PaginaParser
- [x] E14ParserService (orquestador)
- [x] Tests unitarios > 80% cobertura
- [x] Integración con E14TextractParser existente

### Pendiente
- [ ] PartidoParser (migrar lógica de E14TextractParser)
- [ ] VotosEspecialesParser (votos blancos, nulos, no marcados)
- [ ] ValidationService (validar consistencia entre totales)
- [ ] CacheService (caché de parseos recientes)

## Contribuir

### Agregar nuevo parser

1. Crear clase heredando de `BaseParser`:
```python
from .base_parser import BaseParser

class MiNuevoParser(BaseParser):
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        # Implementar lógica
        pass
```

2. Agregar a `__init__.py`:
```python
from .mi_nuevo_parser import MiNuevoParser

__all__ = [..., "MiNuevoParser"]
```

3. Crear tests en `tests/parsers/test_mi_nuevo_parser.py`

4. Integrar en `E14ParserService`:
```python
class E14ParserService:
    def __init__(self, ..., mi_parser: BaseParser = None):
        self.mi_parser = mi_parser or MiNuevoParser()
```

## Referencias

- [AWS Textract Docs](https://docs.aws.amazon.com/textract/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Design Patterns (Gang of Four)](https://en.wikipedia.org/wiki/Design_Patterns)
- [structlog Documentation](https://www.structlog.org/)
