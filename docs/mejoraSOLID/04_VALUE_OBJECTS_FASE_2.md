# 💎 Fase 2: Value Objects Implementados

**Fecha:** 2025-11-20
**Tipo:** Mejora Arquitectónica
**Impacto:** 🟡 MEDIO - Mejora expresividad y seguridad del dominio

---

## 📊 Resumen Ejecutivo

**Qué son los Value Objects:**

Value Objects son objetos inmutables que representan conceptos del dominio por su **valor**, no por su identidad. Encapsulan validaciones y comportamiento rico del dominio.

**Value Objects implementados:**
1. ✅ `CedulaNumber` - Números de cédula con validación automática
2. ✅ `ConfidenceScore` - Puntajes de confianza normalizados (0-1)
3. ✅ `Coordinate` + `Rectangle` - Coordenadas y áreas rectangulares

**Beneficios:**
- ✅ **Validación automática** en construcción
- ✅ **Inmutabilidad** garantizada (frozen=True)
- ✅ **Comportamiento rico** del dominio
- ✅ **Type safety** mejorado
- ✅ **Expresividad** del código

---

## 🎯 Problema que Resuelven

### Antes (Tipos Primitivos)

```python
# ❌ Problemas con tipos primitivos

# 1. Sin validación
cedula: str = "ABC123"  # Inválido pero no falla
confidence: float = 150.0  # Fuera de rango pero no falla

# 2. Validación repetida
def procesar_cedula(cedula: str):
    if not cedula.isdigit():
        raise ValueError("Invalid")
    if not (6 <= len(cedula) <= 15):
        raise ValueError("Invalid length")
    # ... proceso

def otra_funcion(cedula: str):
    # Repetir mismas validaciones ❌
    if not cedula.isdigit():
        raise ValueError("Invalid")
    # ...

# 3. Comportamiento disperso
def formatear_cedula(cedula: str) -> str:
    num = int(cedula)
    return f"{num:,}".replace(',', '.')

# Función suelta, no encapsulada en el concepto

# 4. Sin type safety
def procesar(cedula: str, confidence: float):
    # ¿cedula es válida? ¿confidence está en rango?
    # No hay garantías
    pass
```

---

### Después (Value Objects)

```python
# ✅ Con Value Objects

# 1. Validación automática
cedula = CedulaNumber("12345678")  # ✓ Válido
cedula = CedulaNumber("ABC")       # Raises ValueError automáticamente

confidence = ConfidenceScore(0.85)  # ✓ Válido
confidence = ConfidenceScore(1.5)   # Raises ValueError automáticamente

# 2. Validación centralizada (DRY)
def procesar_cedula(cedula: CedulaNumber):
    # Garantizado que cedula es válida
    # No necesito validar!
    pass

def otra_funcion(cedula: CedulaNumber):
    # Garantizado que es válida
    pass

# 3. Comportamiento encapsulado
cedula = CedulaNumber("12345678")
print(cedula.formatted())  # "12.345.678"
print(cedula.is_colombian())  # True/False

# Todo el comportamiento relacionado está en el objeto

# 4. Type safety completo
def procesar(cedula: CedulaNumber, confidence: ConfidenceScore):
    # Garantizados válidos por type system
    # IDE autocompleta métodos
    # Validaciones en compile-time
    pass
```

---

## 💎 Value Object #1: CedulaNumber

### Propósito

Representa un número de cédula válido con todas las validaciones y comportamiento encapsulado.

### Características

- ✅ Inmutable (frozen=True)
- ✅ Solo dígitos numéricos
- ✅ Longitud 6-15 dígitos
- ✅ Validación de leading zero (configurable)
- ✅ Formateo automático
- ✅ Detección de formato colombiano

---

### Uso Básico

```python
from domain.value_objects import CedulaNumber

# Creación válida
cedula = CedulaNumber("12345678")
print(cedula)  # 12345678
print(cedula.value)  # "12345678"

# Validación automática
try:
    invalid = CedulaNumber("ABC")  # Raises ValueError
except ValueError as e:
    print(f"Error: {e}")
    # Error: Cédula debe contener solo dígitos numéricos: 'ABC'

try:
    invalid = CedulaNumber("123")  # Raises ValueError (muy corto)
except ValueError as e:
    print(f"Error: {e}")
    # Error: Longitud de cédula inválida: 3 dígitos

# Formateo
cedula = CedulaNumber("12345678")
print(cedula.formatted())  # "12.345.678"
print(cedula.formatted(separator=','))  # "12,345,678"

# Validaciones integradas
print(cedula.is_colombian())  # True/False
print(cedula.length())  # 8
print(int(cedula))  # 12345678

# Comparación por valor
c1 = CedulaNumber("12345678")
c2 = CedulaNumber("12345678")
assert c1 == c2  # True (comparación por valor)
```

---

### Factory Methods

```python
from domain.value_objects import CedulaNumber, CedulaNumbers

# from_string con validaciones extra
cedula = CedulaNumber.from_string("12345678", allow_leading_zero=False)

# try_create (no lanza excepciones)
cedula = CedulaNumber.try_create("12345678")
if cedula:
    process(cedula)
else:
    print("Cédula inválida")

# Factory para cédulas colombianas
cedula_col = CedulaNumbers.colombian("12345678")  # 6-10 dígitos, no leading zero

# from_raw_ocr (limpia y valida output de OCR)
cedula = CedulaNumbers.from_raw_ocr("  1234 5678  ")  # Limpia espacios
cedula = CedulaNumbers.from_raw_ocr("1234-5678")  # Elimina guiones
```

---

### Ejemplos de Uso en el Dominio

```python
# En CedulaRecord
@dataclass
class CedulaRecord:
    cedula: CedulaNumber  # ✅ En lugar de str
    confidence: ConfidenceScore  # ✅ En lugar de float
    # ...

    def is_valid(self) -> bool:
        # No necesitamos validar cedula.value
        # Ya está garantizado por CedulaNumber
        return self.confidence.is_acceptable()

# Creación
record = CedulaRecord(
    cedula=CedulaNumber("12345678"),
    confidence=ConfidenceScore(0.92)
)

# Uso
print(f"Cédula: {record.cedula.formatted()}")
print(f"Confianza: {record.confidence.formatted()}")
```

---

## 💎 Value Object #2: ConfidenceScore

### Propósito

Representa un puntaje de confianza normalizado (0.0-1.0) con validaciones y comparaciones integradas.

### Características

- ✅ Inmutable (frozen=True)
- ✅ Normalizado a 0.0-1.0
- ✅ Conversión a/desde porcentaje (0-100)
- ✅ Umbrales predefinidos
- ✅ Comparaciones ricas
- ✅ Formateo automático

---

### Uso Básico

```python
from domain.value_objects import ConfidenceScore

# Creación desde valor normalizado (0.0-1.0)
conf = ConfidenceScore(0.85)
print(conf)  # "85%"
print(conf.value)  # 0.85

# Creación desde porcentaje (0-100)
conf = ConfidenceScore.from_percentage(85.0)
print(conf.value)  # 0.85

# Conversión a porcentaje
print(conf.as_percentage())  # 85.0

# Validaciones integradas
print(conf.is_high())  # True (>= 85%)
print(conf.is_acceptable())  # True (>= 50%)
print(conf.is_low())  # False (< 30%)
print(conf.meets_threshold(0.80))  # True

# Formateo
print(conf.formatted())  # "85%"
print(conf.formatted(decimals=1))  # "85.0%"
print(conf.formatted(decimals=2))  # "85.00%"

# Comparaciones
conf1 = ConfidenceScore(0.85)
conf2 = ConfidenceScore(0.90)

assert conf2 > conf1  # True
assert conf1 < conf2  # True
assert conf1.meets_threshold(0.80)  # True
```

---

### Umbrales Predefinidos

```python
from domain.value_objects import ConfidenceThresholds

# Umbrales estándar
print(ConfidenceThresholds.VERY_LOW)  # 30%
print(ConfidenceThresholds.LOW)       # 50%
print(ConfidenceThresholds.MEDIUM)    # 70%
print(ConfidenceThresholds.HIGH)      # 85%
print(ConfidenceThresholds.VERY_HIGH) # 95%

# Clasificación automática
score = ConfidenceScore(0.92)
level = ConfidenceThresholds.get_level(score)
print(level)  # "VERY_HIGH"

# Uso en validación
score = ConfidenceScore(0.88)
if score >= ConfidenceThresholds.HIGH:
    auto_save()
elif score >= ConfidenceThresholds.MEDIUM:
    require_validation()
else:
    reject()
```

---

### Ejemplos de Uso en el Dominio

```python
# En RowData
@dataclass
class RowData:
    nombres_manuscritos: str
    cedula: CedulaNumber  # ✅ Value Object
    confidence: Dict[str, ConfidenceScore]  # ✅ En lugar de Dict[str, float]

# Creación
row = RowData(
    nombres_manuscritos="MARIA DE JESUS",
    cedula=CedulaNumber("20014807"),
    confidence={
        'nombres': ConfidenceScore(0.96),
        'cedula': ConfidenceScore(0.98)
    }
)

# Uso
if row.confidence['cedula'].is_high():
    print(f"Alta confianza: {row.confidence['cedula'].formatted()}")
```

---

## 💎 Value Object #3: Coordinate + Rectangle

### Propósito

Representa coordenadas 2D y áreas rectangulares inmutables para manejo de posiciones en pantalla.

### Características

- ✅ Inmutables (frozen=True)
- ✅ No negativas (validación automática)
- ✅ Operaciones geométricas
- ✅ Cálculos de distancia
- ✅ Detección de colisiones

---

### Uso Básico: Coordinate

```python
from domain.value_objects import Coordinate

# Creación
coord = Coordinate(100, 200)
print(coord)  # (100, 200)
print(coord.x)  # 100
print(coord.y)  # 200

# Origen
origin = Coordinate.origin()  # (0, 0)

# Desde tupla
coord = Coordinate.from_tuple((100, 200))

# A tupla
x, y = coord.as_tuple()
# O desempaquetar directamente:
x, y = coord

# Operaciones geométricas
p1 = Coordinate(0, 0)
p2 = Coordinate(3, 4)

distance = p1.distance_to(p2)  # 5.0 (euclidiana)
manhattan = p1.manhattan_distance_to(p2)  # 7 (Manhattan)

# Verificar límites
coord = Coordinate(100, 200)
is_valid = coord.is_within_bounds(800, 600)  # True

# Traslación (crea nueva coordenada)
coord = Coordinate(100, 200)
new_coord = coord.translate(50, -30)
print(new_coord)  # (150, 170)

# Inmutabilidad
coord = Coordinate(100, 200)
# coord.x = 150  # ❌ Error: frozen dataclass
```

---

### Uso Básico: Rectangle

```python
from domain.value_objects import Rectangle, Coordinate

# Creación
rect = Rectangle.from_coords(10, 20, 100, 50)  # x, y, width, height

# Propiedades
print(rect.top_left)  # Coordinate(10, 20)
print(rect.top_right)  # Coordinate(110, 20)
print(rect.bottom_left)  # Coordinate(10, 70)
print(rect.bottom_right)  # Coordinate(110, 70)
print(rect.center)  # Coordinate(60, 45)
print(rect.area)  # 5000

# Verificar si contiene coordenada
coord = Coordinate(50, 30)
if rect.contains(coord):
    print("Dentro del rectángulo")

# Detectar solapamiento
r1 = Rectangle.from_coords(0, 0, 100, 100)
r2 = Rectangle.from_coords(50, 50, 100, 100)
if r1.overlaps(r2):
    print("Los rectángulos se solapan")

# Serialización
rect_dict = rect.to_dict()
# {'x': 10, 'y': 20, 'width': 100, 'height': 50}
```

---

### Ejemplos de Uso en el Dominio

```python
# En CaptureArea
@dataclass
class CaptureArea:
    top_left: Coordinate  # ✅ En lugar de x, y separados
    width: int
    height: int

    @property
    def as_rectangle(self) -> Rectangle:
        """Convierte a Rectangle."""
        return Rectangle(self.top_left, self.width, self.height)

    def contains(self, coord: Coordinate) -> bool:
        """Verifica si contiene coordenada."""
        return self.as_rectangle.contains(coord)

# Uso
area = CaptureArea(
    top_left=Coordinate(100, 200),
    width=800,
    height=600
)

mouse_pos = Coordinate(150, 250)
if area.contains(mouse_pos):
    print("Cursor dentro del área")
```

---

## 📊 Beneficios por Principio SOLID

### Single Responsibility (SRP)

**Antes:**
```python
class CedulaRecord:
    def is_valid_cedula(self) -> bool:
        # Validación mezclada con lógica de registro
        return self.cedula.isdigit() and 6 <= len(self.cedula) <= 15
```

**Después:**
```python
class CedulaNumber:
    # Responsabilidad única: representar y validar cédulas
    def __post_init__(self):
        # Validación encapsulada
        ...

class CedulaRecord:
    # Responsabilidad única: representar registro de cédula
    cedula: CedulaNumber  # Validación delegada
```

---

### Open/Closed (OCP)

**Antes:**
```python
# Para agregar nueva regla de validación:
def is_valid(self):
    return (
        self.cedula.isdigit() and
        6 <= len(self.cedula) <= 15
        # ❌ Necesito modificar esta función
    )
```

**Después:**
```python
# Nueva regla: crear nueva especificación
class CedulaFormatColombiano(Specification):
    def is_satisfied_by(self, cedula: CedulaNumber):
        return cedula.is_colombian()

# No modificamos CedulaNumber
```

---

### Liskov Substitution (LSP)

**Antes:**
```python
def procesar(cedula: str):
    # ¿cedula es válida? No hay garantías
    pass

# Puedo pasar cualquier string, incluso inválido
procesar("ABC")  # Falla en runtime
```

**Después:**
```python
def procesar(cedula: CedulaNumber):
    # Garantizado válido por type system
    pass

# Solo puedo pasar CedulaNumber válido
procesar(CedulaNumber("12345678"))  # ✓
# procesar("ABC")  # ❌ Type error en IDE
```

---

### Interface Segregation (ISP)

**Antes:**
```python
# Cédula es un str genérico, con TODA la API de strings
cedula: str = "12345678"
cedula.upper()  # ¿Tiene sentido para una cédula?
cedula.split()  # ¿Útil?
cedula.strip()  # ¿Necesario?
```

**Después:**
```python
# CedulaNumber tiene solo métodos relevantes
cedula = CedulaNumber("12345678")
cedula.formatted()  # ✓ Relevante
cedula.is_colombian()  # ✓ Relevante
# cedula.upper()  # ❌ No existe
```

---

### Dependency Inversion (DIP)

**Antes:**
```python
# Dependencia en implementación concreta (float)
def calculate_score(conf: float) -> str:
    if conf >= 0.85:
        return "HIGH"
    # Lógica acoplada al tipo primitivo
```

**Después:**
```python
# Dependencia en abstracción (ConfidenceScore)
def calculate_score(conf: ConfidenceScore) -> str:
    if conf.is_high():
        return "HIGH"
    # Lógica desacoplada, usa comportamiento del dominio
```

---

## 🧪 Testing de Value Objects

### Test de CedulaNumber

```python
import pytest
from domain.value_objects import CedulaNumber

def test_cedula_number_valid():
    """Test: Cédula válida se crea correctamente."""
    cedula = CedulaNumber("12345678")
    assert cedula.value == "12345678"
    assert str(cedula) == "12345678"

def test_cedula_number_invalid_format():
    """Test: Cédula con letras falla."""
    with pytest.raises(ValueError, match="solo dígitos"):
        CedulaNumber("ABC12345")

def test_cedula_number_invalid_length():
    """Test: Cédula muy corta falla."""
    with pytest.raises(ValueError, match="Longitud"):
        CedulaNumber("123")

def test_cedula_number_formatted():
    """Test: Formateo con separadores."""
    cedula = CedulaNumber("12345678")
    assert cedula.formatted() == "12.345.678"
    assert cedula.formatted(',') == "12,345,678"

def test_cedula_number_is_colombian():
    """Test: Detección de cédula colombiana."""
    cedula_col = CedulaNumber("12345678")  # 8 dígitos, no leading zero
    assert cedula_col.is_colombian() is True

    cedula_long = CedulaNumber("123456789012")  # 12 dígitos
    assert cedula_long.is_colombian() is False

def test_cedula_number_equality():
    """Test: Comparación por valor."""
    c1 = CedulaNumber("12345678")
    c2 = CedulaNumber("12345678")
    c3 = CedulaNumber("87654321")

    assert c1 == c2  # Mismo valor
    assert c1 != c3  # Diferente valor

def test_cedula_number_immutable():
    """Test: Inmutabilidad."""
    cedula = CedulaNumber("12345678")

    with pytest.raises(AttributeError):
        cedula.value = "87654321"  # Frozen dataclass
```

---

## 📝 Migración de Código Existente

### Ejemplo: Refactorizar CedulaRecord

**Antes:**
```python
@dataclass
class CedulaRecord:
    cedula: str  # ❌ Tipo primitivo
    confidence: float  # ❌ Tipo primitivo
    # ...

    def is_valid(self) -> bool:
        return (
            self.cedula.isdigit() and
            6 <= len(self.cedula) <= 15 and
            self.confidence >= 50.0  # ❌ Hardcodeado
        )
```

**Después:**
```python
@dataclass
class CedulaRecord:
    cedula: CedulaNumber  # ✅ Value Object
    confidence: ConfidenceScore  # ✅ Value Object
    # ...

    def is_valid(self, specification=None) -> bool:
        # Validación delegada a Specification Pattern
        if specification is None:
            specification = CedulaSpecifications.valid_for_processing()
        return specification.is_satisfied_by(self)

# Creación
record = CedulaRecord(
    cedula=CedulaNumber("12345678"),
    confidence=ConfidenceScore(0.92)
)
```

---

## 📚 Checklist de Implementación

Para usar Value Objects en tu código:

- [ ] Identificar conceptos del dominio usados como tipos primitivos
- [ ] ¿El concepto tiene reglas de validación? → Candidate for Value Object
- [ ] ¿El concepto tiene comportamiento relacionado? → Candidate for Value Object
- [ ] Crear Value Object con validación en `__post_init__`
- [ ] Hacer inmutable (frozen=True)
- [ ] Implementar `__str__`, `__repr__`, `__hash__`
- [ ] Agregar métodos de conveniencia (formatted, is_*, etc.)
- [ ] Crear factory methods si es útil
- [ ] Escribir tests completos
- [ ] Actualizar code existente para usar Value Object

---

## 💡 Tips y Mejores Prácticas

### ✅ DO

1. **Hacer Value Objects inmutables**
   ```python
   @dataclass(frozen=True)  # ✅
   class CedulaNumber:
       value: str
   ```

2. **Validar en construcción**
   ```python
   def __post_init__(self):
       if not self.value.isdigit():
           raise ValueError(...)  # ✅ Fallar early
   ```

3. **Proveer factory methods**
   ```python
   @classmethod
   def from_string(cls, value: str):
       # Lógica de creación
   ```

4. **Encapsular comportamiento relacionado**
   ```python
   class CedulaNumber:
       def formatted(self): ...  # ✅
       def is_colombian(self): ...  # ✅
   ```

---

### ❌ DON'T

1. **No hacer Value Objects mutables**
   ```python
   @dataclass  # ❌ Sin frozen=True
   class CedulaNumber:
       value: str
   ```

2. **No agregar lógica de negocio compleja**
   ```python
   class CedulaNumber:
       def save_to_database(self):  # ❌ No es responsabilidad del VO
           ...
   ```

3. **No usar para entidades con identidad**
   ```python
   # ❌ MAL - User tiene identidad
   @dataclass(frozen=True)
   class User:
       id: int
       name: str

   # ✅ BIEN - User es entidad, NO value object
   @dataclass
   class User:
       id: int
       name: str
   ```

---

## 🎯 Conclusión

Los Value Objects son una herramienta poderosa para:

1. ✅ **Expresar conceptos del dominio** claramente
2. ✅ **Encapsular validaciones** en un solo lugar
3. ✅ **Garantizar inmutabilidad** y thread-safety
4. ✅ **Mejorar type safety** del código
5. ✅ **Reducir bugs** por validaciones olvidadas

**Implementados en este proyecto:**
- ✅ CedulaNumber (números de cédula)
- ✅ ConfidenceScore (puntajes 0-1)
- ✅ Coordinate + Rectangle (geometría)

**Listo para usar en todo el dominio.**

---

**Última actualización:** 2025-11-20
**Desarrollado por:** Juan Sebastian Lopez Hernandez + Claude Code
**Estado:** ✅ Completado
**Impacto:** 🟡 MEDIO - Mejora expresividad y seguridad
