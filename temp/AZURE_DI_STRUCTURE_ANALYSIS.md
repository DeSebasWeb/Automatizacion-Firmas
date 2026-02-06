# Análisis de Estructura Azure Document Intelligence - E14 Senado

## Resumen Ejecutivo

Azure DI detectó **13 tablas** correctamente en el documento E14, distribuidas en las páginas 2-11.
Las tablas tienen una estructura consistente de **12 columnas** organizadas en tríadas:
- 1 columna de IDs de candidatos
- 3 columnas de casillas de votos
- (Patrón se repite 3 veces por tabla)

## Campos Top-Level

Total: **94 campos**

### Categorías de Campos

#### 1. Metadata de Páginas (11 campos)
- `Pagina`, `pagina2`, `Pagina3`-`Pagina11`
- `TipoDeDocumento`, `TipoDeDocumentoPag2`-`TipoDeDocumentoPag11`
- `DivipolPag1`-`DivipolPag11`

#### 2. Consolidados y Totales (14 campos)
- `TotalSufragantes`, `TotalVotosUrna`, `TotalVotosIncinerados`
- `ConsolidadoVotos1Pag10`, `ConsolidadoVotos2Pag11`
- `TotalVotosAgrupacion+VotosCandidatosPag2` (múltiples variantes)

#### 3. Información de Partidos (56 campos)
- `TipoDeVotoPartido1Pag1`-`TipoDeVotoPartido8Pag10`
- Información del partido sin estructura de tabla (string)

#### 4. TABLAS DE CANDIDATOS (13 campos) ⭐
**Estos son los campos críticos con estructura `valueObject`:**

| Campo | Página | Columnas | Filas | Descripción |
|-------|--------|----------|-------|-------------|
| `PartidoHoja2` | 2 | 12 | 33 | Lista con voto preferente |
| `PartidoHoja3` | 3 | 12 | 28 | Lista con voto preferente |
| `PartidoHoja4` | 4 | 12 | 32 | Lista con voto preferente |
| `PartidoHoja5` | 5 | 12 | 21 | Lista con voto preferente |
| `PartidoHoja6` | 6 | 12 | 33 | Lista con voto preferente |
| `PartidoHoja7` | 7 | 12 | 25 | Lista con voto preferente |
| `PartidoHoja8` | 8 | 12 | 26 | Lista con voto preferente |
| `PartidoHoja9` | 9 | 12 | 33 | Lista con voto preferente |
| `Partido3Pagina10` | 10 | 12 | 1 | Lista con voto preferente (circunscripción indígena) |
| `Partido4Pag10` | 10 | 12 | 1 | Lista con voto preferente (circunscripción indígena) |
| `Partido5Pagina10` | 10 | 12 | 1 | Lista con voto preferente (circunscripción indígena) |
| `Partido8Hoja10` | 10 | 12 | 1 | Lista con voto preferente (circunscripción indígena) |
| `ConsolidadoVotos2Pag11` | 11 | 4 | 3 | Votos en blanco/nulos/no marcados |

#### 5. Firmas de Jurados (6 campos)
- `FirmaJurado1`-`FirmaJurado6`

## Estructura de Tablas de Partidos

### Patrón Consistente (12 columnas)

```
[ID Candidato1] [casilla 1] [casilla 2] [casilla 3]
[ID Candidato2] [casilla 4] [casilla 5] [casilla 6]
[ID Candidato3] [casilla 7] [casilla 8] [casilla 9]
```

### Variaciones en Nombres de Columnas

Azure DI no es 100% consistente en los nombres:

**Página 2 (PartidoHoja2):**
```python
['ID Candidato1', 'casilla 1', 'casilla 2', 'casilla 3',
 'ID candidato2',  # ⚠️ Minúscula "candidato"
 'casilla 4', 'casilla 5', 'casilla 6',
 'ID Candidato3', 'Casilla 7', 'casilla 8', 'casilla 9']  # ⚠️ Mayúscula "Casilla 7"
```

**Páginas 3-9 (más consistentes):**
```python
['IDCandidato1', 'Casilla1', 'Casilla2', 'Casilla3',  # Sin espacios
 'IDCandidato2', 'Casilla4', 'Casilla5', 'Casilla6',
 'IDCandidato3', 'Casilla7', 'Casilla8', 'Casilla9']
```

### Estructura Interna de Cada Columna

Cada columna es un objeto con `valueObject` que contiene filas:

```json
{
  "ID Candidato1": {
    "type": "object",
    "confidence": 0.299,
    "valueObject": {
      "ROW1": {
        "type": "string",
        "valueString": "1",
        "content": "1",
        "confidence": 0.985
      },
      "ROW2": {
        "type": "string",
        "valueString": "2",
        "content": "2",
        "confidence": 0.985
      },
      ...
      "ROW33": {...}
    }
  },
  "casilla 1": {
    "type": "object",
    "confidence": 0.995,
    "valueObject": {
      "ROW1": {
        "type": "string",
        "valueString": "",  // Vacío si no hay voto
        "content": "",
        "confidence": 0.989
      },
      "ROW6": {
        "type": "string",
        "valueString": "--",  // Guiones = sin voto
        "content": "--",
        "confidence": 0.558
      },
      ...
    }
  }
}
```

### Datos en las Celdas

**Columnas de ID Candidato:**
- Valores: `"1"`, `"2"`, `"3"`, ... `"100"`
- Tipo: Números secuenciales de candidatos

**Columnas de Casillas:**
- Vacío `""`: Sin marca
- Guiones `"--"`: Sin voto o marca inválida
- Números `"1"`, `"2"`, etc.: Votos registrados

## Problemas Detectados

### 1. Inconsistencia en Nombres de Columnas

| Problema | Ejemplos | Impacto |
|----------|----------|---------|
| Case sensitivity | `casilla 1` vs `Casilla1` | Parser debe normalizar |
| Espacios variables | `ID Candidato1` vs `IDCandidato1` | Regex debe ser flexible |
| Minúsculas/mayúsculas | `ID candidato2` vs `ID Candidato2` | Case-insensitive matching |

### 2. Variabilidad en Número de Filas

Las tablas tienen **diferente cantidad de candidatos**:
- Mínimo: 1 fila (página 10, circunscripción indígena)
- Máximo: 33 filas (páginas 2, 6, 9)

### 3. Valores Vacíos vs Nulos

Las casillas pueden tener:
- `valueString: ""` (cadena vacía)
- `valueString: null` (no detectado)
- `valueString: "--"` (explícitamente sin voto)

### 4. Estructura No Encontrada en Primera Versión

**CAUSA RAÍZ**: El parser actual probablemente busca:
- Campos con nombre exacto `"TablaCandidatos"`
- Arrays en lugar de objetos
- Estructura profundamente anidada

**REALIDAD**: Azure DI creó:
- Campos top-level como `PartidoHoja2`
- Objetos directos (no arrays)
- Estructura de 2 niveles (columna → fila)

## Recomendaciones para el Parser

### 1. Detección de Tablas

**Estrategia A: Pattern Matching en Nombres de Campos**

```python
import re

def is_table_field(field_name: str) -> bool:
    patterns = [
        r'^Partido.*Hoja\d+$',           # PartidoHoja2, PartidoHoja3
        r'^Partido\d+.*Pag.*\d+$',       # Partido3Pagina10
        r'^ConsolidadoVotos.*Pag\d+$'   # ConsolidadoVotos2Pag11
    ]
    return any(re.match(pattern, field_name) for pattern in patterns)
```

**Estrategia B: Heurística de Estructura**

```python
def is_candidate_table(field_value: dict) -> bool:
    if field_value.get('type') != 'object':
        return False

    value_obj = field_value.get('valueObject', {})
    if not value_obj:
        return False

    # Verificar patrón de columnas
    col_names = list(value_obj.keys())

    # Debe tener 12 columnas para tablas de partidos
    if len(col_names) != 12:
        return False

    # Verificar patrón: ID + casillas
    has_id_pattern = any('candidato' in col.lower() or 'id' in col.lower()
                          for col in col_names)
    has_casilla_pattern = any('casilla' in col.lower()
                               for col in col_names)

    return has_id_pattern and has_casilla_pattern
```

### 2. Normalización de Nombres de Columnas

```python
def normalize_column_name(col_name: str) -> tuple[str, int]:
    """
    Normaliza nombres de columnas a formato estándar.

    Returns:
        (tipo, numero) donde tipo = 'id_candidato' o 'casilla'
    """
    col_lower = col_name.lower().replace(' ', '')

    # Extraer tipo
    if 'candidato' in col_lower or 'id' in col_lower:
        tipo = 'id_candidato'
    elif 'casilla' in col_lower:
        tipo = 'casilla'
    else:
        tipo = 'unknown'

    # Extraer número
    import re
    match = re.search(r'(\d+)', col_name)
    numero = int(match.group(1)) if match else 0

    return (tipo, numero)

# Uso:
# normalize_column_name("ID Candidato1") → ('id_candidato', 1)
# normalize_column_name("casilla 4") → ('casilla', 4)
# normalize_column_name("Casilla7") → ('casilla', 7)
```

### 3. Extracción de Datos de Tabla

```python
from typing import List, Dict, Optional

def extract_table_data(field_value: dict) -> List[Dict[str, str]]:
    """
    Extrae datos de una tabla de Azure DI.

    Returns:
        Lista de registros con estructura:
        [
            {'candidato_id': '1', 'casilla_1': '', 'casilla_2': '--', 'casilla_3': '1'},
            {'candidato_id': '2', 'casilla_1': '2', 'casilla_2': '', 'casilla_3': ''},
            ...
        ]
    """
    value_obj = field_value.get('valueObject', {})
    if not value_obj:
        return []

    # Agrupar columnas por grupo (cada grupo = 1 ID + 3 casillas)
    grupos = []
    for i in range(3):  # 3 grupos de candidatos
        grupo = {
            'id_col': None,
            'casilla_cols': []
        }

        # Buscar columnas de este grupo
        for col_name, col_data in value_obj.items():
            tipo, num = normalize_column_name(col_name)

            if tipo == 'id_candidato' and num == i + 1:
                grupo['id_col'] = col_data
            elif tipo == 'casilla' and (i * 3 + 1) <= num <= (i * 3 + 3):
                grupo['casilla_cols'].append((num, col_data))

        # Ordenar casillas por número
        grupo['casilla_cols'].sort(key=lambda x: x[0])
        grupos.append(grupo)

    # Extraer filas
    registros = []

    for grupo in grupos:
        if grupo['id_col'] is None:
            continue

        id_rows = grupo['id_col'].get('valueObject', {})
        num_rows = len(id_rows)

        for row_name in id_rows.keys():
            registro = {}

            # ID de candidato
            id_cell = id_rows[row_name]
            registro['candidato_id'] = id_cell.get('valueString', '')

            # Casillas
            for idx, (num_casilla, col_data) in enumerate(grupo['casilla_cols'], 1):
                casilla_rows = col_data.get('valueObject', {})
                if row_name in casilla_rows:
                    casilla_cell = casilla_rows[row_name]
                    voto = casilla_cell.get('valueString', '')

                    # Normalizar valores vacíos
                    if voto in ['', '--', None]:
                        voto = None

                    registro[f'casilla_{idx}'] = voto
                else:
                    registro[f'casilla_{idx}'] = None

            registros.append(registro)

    return registros
```

### 4. Validación de Datos Extraídos

```python
def validate_table_data(registros: List[Dict]) -> Dict[str, any]:
    """
    Valida la consistencia de los datos extraídos.
    """
    if not registros:
        return {
            'valid': False,
            'error': 'No se extrajeron registros'
        }

    # Verificar IDs secuenciales
    ids = [int(r['candidato_id']) for r in registros if r['candidato_id']]
    if ids != sorted(ids):
        return {
            'valid': False,
            'error': f'IDs no secuenciales: {ids}'
        }

    # Verificar cantidad de casillas por registro
    num_casillas = len([k for k in registros[0].keys() if k.startswith('casilla_')])
    if num_casillas != 3:
        return {
            'valid': False,
            'error': f'Esperado 3 casillas, encontrado {num_casillas}'
        }

    return {
        'valid': True,
        'num_candidatos': len(registros),
        'num_casillas': num_casillas,
        'ids_range': (min(ids), max(ids)) if ids else (None, None)
    }
```

### 5. Manejo de Casos Edge

```python
def extract_all_tables(fields: dict) -> Dict[str, List[Dict]]:
    """
    Extrae todas las tablas del documento E14.

    Returns:
        {
            'PartidoHoja2': [...],
            'PartidoHoja3': [...],
            ...
        }
    """
    tablas = {}

    for field_name, field_value in fields.items():
        # Detectar si es una tabla
        if not is_table_field(field_name):
            continue

        if not is_candidate_table(field_value):
            continue

        # Extraer datos
        try:
            registros = extract_table_data(field_value)

            # Validar
            validacion = validate_table_data(registros)

            if validacion['valid']:
                tablas[field_name] = registros
            else:
                print(f"⚠️ Tabla {field_name} inválida: {validacion['error']}")
                # Guardar de todos modos para debug
                tablas[field_name] = {
                    'error': validacion['error'],
                    'raw_data': registros
                }

        except Exception as e:
            print(f"❌ Error extrayendo {field_name}: {e}")
            tablas[field_name] = {'error': str(e)}

    return tablas
```

## Integración con la Arquitectura Actual

### Ubicación del Parser

Crear nuevo adapter en la capa de infraestructura:

```
src/infrastructure/ocr/azure_document_intelligence/
├── __init__.py
├── azure_di_adapter.py          # Adapter principal (ya existe)
├── response_cleaner.py           # Limpieza (ya existe)
├── table_parser.py               # ⭐ NUEVO: Parser de tablas
└── field_extractors.py           # ⭐ NUEVO: Extractores especializados
```

### Nuevo TableParser

```python
# src/infrastructure/ocr/azure_document_intelligence/table_parser.py

from typing import List, Dict, Optional
import re
import structlog

logger = structlog.get_logger(__name__)


class AzureTableParser:
    """
    Parser especializado para tablas de Azure Document Intelligence.

    Maneja las estructuras tipo valueObject con columnas y ROWs.
    """

    def parse_fields(self, fields: dict) -> Dict[str, any]:
        """
        Punto de entrada principal.

        Args:
            fields: Dict con fields de Azure DI (limpio)

        Returns:
            {
                'metadata': {...},
                'tablas_partidos': [...],
                'consolidados': {...},
                'firmas': [...]
            }
        """
        result = {
            'metadata': self._extract_metadata(fields),
            'tablas_partidos': self._extract_partido_tables(fields),
            'consolidados': self._extract_consolidados(fields),
            'firmas': self._extract_firmas(fields)
        }

        return result

    def _extract_partido_tables(self, fields: dict) -> List[Dict]:
        # Implementar extracción como se describió arriba
        pass

    # ... otros métodos
```

### Integración con Use Case

```python
# src/application/use_cases/process_e14_azure_di_use_case.py

from src.infrastructure.ocr.azure_document_intelligence.response_cleaner import (
    AzureResponseCleaner,
    AzureResponseValidator
)
from src.infrastructure.ocr.azure_document_intelligence.table_parser import (
    AzureTableParser
)

class ProcessE14AzureDIUseCase:

    def __init__(self):
        self.cleaner = AzureResponseCleaner()
        self.validator = AzureResponseValidator()
        self.parser = AzureTableParser()

    def execute(self, azure_response: dict) -> dict:
        # 1. Validar estructura
        if not self.validator.validate_response(azure_response):
            raise ValueError("Invalid response")

        # 2. Extraer fields
        fields = self.validator.extract_fields(azure_response)

        # 3. Limpiar
        cleaned_fields = self.cleaner.clean(fields)

        # 4. Parsear tablas
        parsed_data = self.parser.parse_fields(cleaned_fields)

        return parsed_data
```

## Próximos Pasos

1. **Crear TableParser** con las funciones recomendadas
2. **Escribir tests unitarios** con datos del JSON limpio
3. **Probar con múltiples documentos** para validar robustez
4. **Ajustar patrones de detección** según casos reales
5. **Implementar extractor de metadata** (Divipol, tipo de voto, etc.)
6. **Validar datos contra reglas de negocio** del E14

## Tests Recomendados

```python
# tests/unit/azure_di/test_table_parser.py

def test_detect_table_fields():
    assert is_table_field("PartidoHoja2") == True
    assert is_table_field("Partido3Pagina10") == True
    assert is_table_field("TipoDeVotoPartido1Pag1") == False

def test_normalize_column_names():
    assert normalize_column_name("ID Candidato1") == ('id_candidato', 1)
    assert normalize_column_name("casilla 4") == ('casilla', 4)
    assert normalize_column_name("Casilla7") == ('casilla', 7)

def test_extract_table_data_partidohoja2():
    # Cargar datos reales del JSON limpio
    with open("temp/cleaned_fields.json") as f:
        data = json.load(f)

    table = data['fields']['PartidoHoja2']
    registros = extract_table_data(table)

    assert len(registros) > 0
    assert 'candidato_id' in registros[0]
    assert 'casilla_1' in registros[0]

def test_validate_sequential_ids():
    registros = [
        {'candidato_id': '1', 'casilla_1': None},
        {'candidato_id': '2', 'casilla_1': '3'},
        {'candidato_id': '3', 'casilla_1': None}
    ]

    validation = validate_table_data(registros)
    assert validation['valid'] == True
```

## Conclusión

Azure DI **SÍ detectó correctamente las tablas**, pero:
- Estructura diferente a la esperada (objeto con columnas, no array de filas)
- Nombres inconsistentes requieren normalización
- Parser actual probablemente busca estructura incorrecta

Con las recomendaciones anteriores, deberías poder extraer todas las tablas exitosamente.
