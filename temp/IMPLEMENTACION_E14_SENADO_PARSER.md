# Implementación del Parser Adaptativo E14 Senado

## Resumen

Se implementó exitosamente un parser adaptativo para documentos E-14 Senado con Azure Document Intelligence, siguiendo estrictamente la arquitectura hexagonal del proyecto.

## Archivos Creados

### 1. Parsers (Infrastructure Layer)

**`src/infrastructure/ocr/azure_document_intelligence/parsers/`**

- `parsing_utils.py` - Utilidades de parsing reutilizables
  - `parse_votos_preserve_format()` - Preserva formato original de votos (---, ***, ///)
  - `extract_page_number()` - Extrae número de página de cualquier campo
  - `extract_partido_number()` - Extrae número de partido dentro de la página
  - `parse_divipol()` - Parsea información de DIVIPOL
  - `format_page_number()` - Formatea número de página (01 de 11)
  - `extract_total_from_string()` - Extrae total de votos de string

- `partido_parser.py` - Parser especializado para partidos
  - `parse_tipo_voto_partido()` - Extrae info básica del partido (nombre, código, tipo)
  - `parse_tabla_candidatos()` - Extrae tabla de candidatos con votos (O(n))

- `consolidado_parser.py` - Parser para votos consolidados
  - `parse_consolidado_votos()` - Extrae votos en blanco, nulos, no marcados

- `e14_senado_parser.py` - Orchestrator principal
  - `parse()` - Punto de entrada principal
  - `_group_fields_by_page()` - Agrupa campos por número de página
  - `_parse_partidos_in_page()` - Parsea todos los partidos de una página
  - `_parse_metadata_page1()` - Extrae metadata de página 1
  - `_parse_consolidado_in_page()` - Extrae consolidados por página

### 2. Use Case (Application Layer)

**`src/application/use_cases/process_e14_senado_use_case.py`**

- `ProcessE14SenadoUseCase` - Orquesta el proceso completo:
  1. Valida disponibilidad del adapter
  2. Llama a Azure DI para análisis
  3. Valida y limpia response
  4. Parsea con E14SenadoParser
  5. Guarda outputs (debug + resultado final)

### 3. API Integration

**Modificaciones:**

- `src/infrastructure/api/dependencies.py`
  - Agregada función `get_process_e14_senado_use_case()`

- `src/infrastructure/api/routes/documents.py`
  - Actualizado endpoint `/e14/azure-di/senado` para usar nuevo use case

### 4. Tests

**`tests/unit/azure_di/`**

- `test_parsing_utils.py` - 21 tests para utilidades de parsing
- `test_partido_parser.py` - 6 tests para parser de partidos

**`utils/test_e14_senado_parser.py`** - Script de prueba con JSON real

## Arquitectura

### Flujo de Datos

```
PDF File
   ↓
Azure Document Intelligence Adapter
   ↓
Raw Azure Response (JSON)
   ↓
AzureResponseValidator.validate_response()
   ↓
AzureResponseValidator.extract_fields()
   ↓
AzureResponseCleaner.clean()
   ↓
E14SenadoParser.parse()
   ├─ _group_fields_by_page()
   ├─ _parse_metadata_page1()
   └─ For each page:
      ├─ _parse_partidos_in_page()
      │  ├─ PartidoParser.parse_tipo_voto_partido()
      │  └─ PartidoParser.parse_tabla_candidatos()
      └─ _parse_consolidado_in_page()
         └─ ConsolidadoVotosParser.parse_consolidado_votos()
   ↓
Structured JSON Output
```

### Principios SOLID Aplicados

1. **Single Responsibility**
   - Cada parser tiene una responsabilidad única
   - `ParsingUtils` solo maneja utilidades de parsing
   - `PartidoParser` solo parsea partidos
   - `ConsolidadoParser` solo parsea consolidados

2. **Open/Closed**
   - Parsers pueden extenderse sin modificar código existente
   - Fácil agregar nuevos tipos de campos

3. **Dependency Inversion**
   - Use case depende de `AzureDIPort` (interface)
   - No depende de implementación concreta

4. **Interface Segregation**
   - Interfaces pequeñas y específicas
   - Cada parser expone solo métodos necesarios

## Formato de Salida

### Estructura JSON

```json
{
  "e14": {
    "pagina": "01 de 11",
    "divipol": {
      "CodDep": "72",
      "CodMun": "006",
      "zona": "99",
      "Puesto": "48",
      "Mesa": "001"
    },
    "TotalSufragantesE14": "103",
    "TotalVotosEnUrna": "103",
    "TotalIncinerados": "---",
    "Partido": [
      {
        "numPartido": "0013",
        "nombrePartido": "PARTIDO COMUNES",
        "tipoDeVoto": "ListaSinVotoPreferente",
        "id": "0",
        "votosSoloPorLaAgrupacionPolitica": "1",
        "candidatos": [],
        "TotalVotosAgrupacion+VotosCandidatos": "1"
      }
    ],
    "pagina2": "02 de 11",
    "divipol2": { ... },
    "Partido2": [
      {
        "numPartido": "0255",
        "nombrePartido": "COALICIÓN ALIANZA VERDE",
        "tipoDeVoto": "ListaConVotoPreferente",
        "id": "0",
        "votosSoloPorLaAgrupacionPolitica": "0",
        "candidatos": [
          {
            "idcandidato": "34",
            "votos": "12"
          }
        ],
        "TotalVotosAgrupacion+VotosCandidatos": "12"
      }
    ],
    "ConsolidadoVotos11": [
      {
        "tipo": "VOTOS EN BLANCO",
        "votos": "17"
      },
      {
        "tipo": "VOTOS NULOS",
        "votos": "---"
      },
      {
        "tipo": "VOTOS NO MARCADOS",
        "votos": "---"
      }
    ]
  }
}
```

### Reglas Clave

1. **Página 1:** Contiene metadata completa + primer partido
2. **Páginas 2-11:** Contienen `paginaX`, `divipolX`, `PartidoX`
3. **Consolidados:** Solo en páginas donde existen (generalmente página 11)
4. **Votos preservados:** `---`, `***`, `///` se mantienen como están
5. **Candidatos:** Solo en partidos con `ListaConVotoPreferente`

## Características Adaptativas

### 1. Detección Flexible de Páginas

El parser detecta páginas por múltiples patrones:
- `Pag{N}` → `DivipolPag10`
- `Pagina{N}` → `Pagina5`
- `PartidoHoja{N}` → `PartidoHoja2`

### 2. Asociación Inteligente de Tablas

**CRÍTICO:** `PartidoHoja{N}` = Página {N}

Las tablas se asignan a partidos `ListaConVotoPreferente` en orden:
- Página 2 puede tener 1 partido → 1 tabla
- Página 4 puede tener 3 partidos (2 CON voto, 1 SIN) → 2 tablas
- Asignación secuencial a partidos CON VOTO PREFERENTE

### 3. Normalización de Nombres de Columnas

Parser tolera variaciones:
- `ID Candidato1` vs `IDCandidato1`
- `casilla 1` vs `Casilla1`
- `ID candidato2` (minúscula)

### 4. Parsing O(n) de Candidatos

Algoritmo eficiente:
- Itera filas UNA sola vez
- Suma votos de 3 casillas por candidato
- Sin bucles anidados

## Testing

### Tests Unitarios

**Cobertura:**
- `test_parsing_utils.py`: 21 tests ✅
- `test_partido_parser.py`: 6 tests ✅

**Todos pasaron exitosamente**

### Test de Integración

**Script:** `utils/test_e14_senado_parser.py`

**Resultado:**
- ✅ Parseó 94 campos
- ✅ Detectó 11 páginas
- ✅ Extrajo 25 partidos total
- ✅ Identificó consolidados
- ✅ Generó JSON válido

## Salidas de Debug

1. **`temp/cleaned_fields.json`** - Campos limpios de Azure DI
2. **`temp/e14_senado_parsed.json`** - Resultado final parseado
3. **Logs estructurados** con structlog

## Endpoint API

### POST `/e14/azure-di/senado`

**Request:**
- File: PDF (max 50MB)
- Auth: JWT token required

**Response:**
```json
{
  "e14": { ... }
}
```

**Guardado automático:**
- JSON guardado en `temp/`
- Logs de procesamiento

## Próximos Pasos Sugeridos

1. **Validaciones de negocio:**
   - Verificar suma de votos
   - Validar totales por partido
   - Comprobar consistencia entre páginas

2. **Manejo de errores:**
   - Páginas faltantes
   - Campos mal formateados
   - Tablas incompletas

3. **Performance:**
   - Caché de resultados
   - Procesamiento paralelo de páginas

4. **E14 Cámara:**
   - Crear parser específico (estructura diferente)
   - Reutilizar `ParsingUtils`

## Issues Resueltos

### Issue #1: Timeout Infinito en Azure DI (2026-02-06)

**Problema:**
- API no respondía después de 1:30+ minutos
- Logs mostraban polling infinito a Azure DI cada segundo
- SDK de Azure hacía GET requests sin parar a `analyzeResults` endpoint
- Response header `retry-after: 1` indicaba que Azure seguía procesando

**Causa Raíz:**
- `poller.result()` en `azure_di_adapter.py` NO tenía timeout configurado
- Azure DI quedaba atascado en estado `running` indefinidamente
- SDK esperaba sin límite de tiempo

**Solución Implementada:**

1. **Timeout FORZADO con ThreadPoolExecutor:**
   ```python
   with ThreadPoolExecutor(max_workers=1) as executor:
       future = executor.submit(_analyze_with_poller)
       try:
           result = future.result(timeout=timeout_seconds)
       except FuturesTimeoutError:
           future.cancel()
           return None
   ```

   Esta solución usa threading para FORZAR el timeout, ya que el `poller.result(timeout=X)`
   del SDK de Azure no siempre respeta el timeout correctamente.

2. **Configuración en `settings.yaml`:**
   ```yaml
   azure_di:
     model_id: "e14-senado-v1"
     polling_timeout_seconds: 60  # Máximo 60 segundos (Azure responde en 27-32s)
   ```

3. **Script de testing:** `utils/test_azure_di_timeout.py`

**Archivos Modificados:**
- `src/infrastructure/ocr/azure_document_intelligence/azure_di_adapter.py` (imports + método completo)
- `config/settings.yaml` (línea 123: 60 segundos)
- `config/settings.example.yaml` (línea 56: 120 segundos)

**Prevención:**
- **Timeout dual:** `poller.result(timeout=X)` + `future.result(timeout=X)`
- **Cancelación forzada:** `future.cancel()` si excede tiempo
- **Logging detallado:** Logs indican exactamente dónde falló
- **Timeout agresivo:** 60 segundos (Azure DI responde en 27-32s normalmente)
- FastAPI puede responder con error 422 apropiado al cliente

## Conclusión

✅ Parser adaptativo completamente funcional
✅ Respeta arquitectura hexagonal
✅ Tests unitarios pasando
✅ Probado con JSON real
✅ Endpoint integrado
✅ No inventa datos - solo usa lo que Azure provee
✅ Preserva formatos originales
✅ O(n) en extracción de candidatos
✅ Timeout configurado para evitar cuelgues
