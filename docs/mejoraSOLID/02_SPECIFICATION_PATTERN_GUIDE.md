# 📘 Guía Rápida: Specification Pattern

**Audiencia:** Desarrolladores del proyecto
**Nivel:** Intermedio
**Tiempo de lectura:** 10 minutos

---

## 🎯 ¿Qué es el Specification Pattern?

El **Specification Pattern** es un patrón de diseño que encapsula reglas de negocio en objetos reutilizables y componibles.

### Problema que Resuelve

**❌ Antes (Código acoplado):**
```python
class CedulaRecord:
    def is_valid(self) -> bool:
        # Lógica hardcodeada
        return (
            self.cedula.isdigit() and
            6 <= len(self.cedula) <= 15 and
            self.confidence >= 50.0
        )
```

**Problemas:**
- Lógica no reutilizable
- Difícil de testear aisladamente
- Viola OCP (cambiar reglas = modificar clase)
- No se puede combinar con otras validaciones

**✅ Después (Specification Pattern):**
```python
class CedulaRecord:
    def is_valid(self, specification=None) -> bool:
        if specification is None:
            specification = CedulaSpecifications.valid_for_processing()
        return specification.is_satisfied_by(self)
```

**Beneficios:**
- Validaciones reutilizables
- Fácil de testear
- Respeta OCP (agregar reglas sin modificar clase)
- Combinable con otras especificaciones

---

## 🏗️ Estructura Básica

### 1. Clase Base Abstracta

```python
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar('T')

class Specification(ABC, Generic[T]):
    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool:
        """Verifica si el candidato satisface la especificación."""
        pass

    def and_(self, other: 'Specification[T]') -> 'Specification[T]':
        """Combina con AND lógico."""
        return AndSpecification(self, other)

    def or_(self, other: 'Specification[T]') -> 'Specification[T]':
        """Combina con OR lógico."""
        return OrSpecification(self, other)

    def not_(self) -> 'Specification[T]':
        """Invierte la especificación."""
        return NotSpecification(self)
```

### 2. Especificación Concreta

```python
class CedulaFormatSpecification(Specification['CedulaRecord']):
    """Verifica que la cédula contenga solo dígitos."""

    def is_satisfied_by(self, record: 'CedulaRecord') -> bool:
        return record.cedula.isdigit()
```

### 3. Especificaciones Compuestas

```python
class AndSpecification(Specification[T]):
    def __init__(self, left: Specification[T], right: Specification[T]):
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        return (
            self.left.is_satisfied_by(candidate) and
            self.right.is_satisfied_by(candidate)
        )
```

---

## 🚀 Uso Básico

### Ejemplo 1: Validación Simple

```python
from domain.specifications import CedulaFormatSpecification

# Crear especificación
format_spec = CedulaFormatSpecification()

# Crear registro
record = CedulaRecord(cedula="12345678", confidence=90)

# Validar
if format_spec.is_satisfied_by(record):
    print("Formato válido")
else:
    print("Formato inválido")
```

### Ejemplo 2: Combinar Especificaciones

```python
from domain.specifications import (
    CedulaFormatSpecification,
    CedulaLengthSpecification,
    ConfidenceSpecification
)

# Combinar con and_()
valid_cedula = (
    CedulaFormatSpecification()
    .and_(CedulaLengthSpecification(6, 15))
    .and_(ConfidenceSpecification(50.0))
)

# Validar
record = CedulaRecord(cedula="12345678", confidence=90)
if valid_cedula.is_satisfied_by(record):
    process(record)
```

### Ejemplo 3: Usar Factory

```python
from domain.specifications import CedulaSpecifications

# Usar especificación pre-configurada
standard_validation = CedulaSpecifications.valid_for_processing()

# Aplicar
if standard_validation.is_satisfied_by(record):
    process(record)
```

---

## 🎨 Patrones de Uso Comunes

### Patrón 1: Filtrado de Listas

```python
from domain.specifications import CedulaSpecifications

# Obtener solo registros válidos
high_confidence = CedulaSpecifications.high_confidence_only(min_confidence=85.0)

valid_records = [
    record for record in all_records
    if high_confidence.is_satisfied_by(record)
]
```

### Patrón 2: Validación Contextual

```python
def process_records(records: List[CedulaRecord], context: str):
    if context == "colombia":
        spec = CedulaSpecifications.valid_colombian_cedula()
    elif context == "high_accuracy":
        spec = CedulaSpecifications.high_confidence_only(90.0)
    else:
        spec = CedulaSpecifications.valid_for_processing()

    for record in records:
        if spec.is_satisfied_by(record):
            process(record)
```

### Patrón 3: Validación por Etapas

```python
# Validación básica
basic = CedulaFormatSpecification()
basic_valid = [r for r in records if basic.is_satisfied_by(r)]

# Validación intermedia
medium = basic.and_(CedulaLengthSpecification(6, 15))
medium_valid = [r for r in basic_valid if medium.is_satisfied_by(r)]

# Validación estricta
strict = medium.and_(ConfidenceSpecification(85.0))
strict_valid = [r for r in medium_valid if strict.is_satisfied_by(r)]
```

### Patrón 4: Especificaciones Dinámicas

```python
def create_validation(config: dict) -> Specification:
    """Crea especificación desde configuración."""
    spec = CedulaFormatSpecification()

    if config.get('check_length'):
        min_len = config.get('min_length', 6)
        max_len = config.get('max_length', 15)
        spec = spec.and_(CedulaLengthSpecification(min_len, max_len))

    if config.get('check_confidence'):
        min_conf = config.get('min_confidence', 50.0)
        spec = spec.and_(ConfidenceSpecification(min_conf))

    if config.get('no_leading_zero'):
        spec = spec.and_(CedulaNotStartsWithZeroSpecification())

    return spec

# Uso
config = {'check_length': True, 'min_length': 8, 'check_confidence': True}
dynamic_spec = create_validation(config)
```

---

## 🔧 Crear Nuevas Especificaciones

### Template para Nueva Especificación

```python
from domain.specifications import Specification
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.entities import CedulaRecord

class MiNuevaSpecification(Specification['CedulaRecord']):
    """
    Descripción de qué valida esta especificación.

    Args:
        param1: Descripción del parámetro
    """

    def __init__(self, param1: int):
        self.param1 = param1

    def is_satisfied_by(self, record: 'CedulaRecord') -> bool:
        """
        Verifica si el registro satisface la condición.

        Args:
            record: Registro a validar

        Returns:
            True si satisface, False en caso contrario
        """
        # Implementar lógica aquí
        return record.cedula.startswith(str(self.param1))

    def __repr__(self) -> str:
        return f"MiNuevaSpecification(param1={self.param1})"
```

### Ejemplo: Especificación de Rango de Fechas

```python
from datetime import datetime

class DateRangeSpecification(Specification['CedulaRecord']):
    """Valida que el registro esté dentro de un rango de fechas."""

    def __init__(self, start_date: datetime, end_date: datetime):
        if start_date > end_date:
            raise ValueError("start_date debe ser anterior a end_date")

        self.start_date = start_date
        self.end_date = end_date

    def is_satisfied_by(self, record: 'CedulaRecord') -> bool:
        return self.start_date <= record.created_at <= self.end_date

    def __repr__(self) -> str:
        return f"DateRangeSpecification({self.start_date}, {self.end_date})"
```

---

## 🧪 Testing de Especificaciones

### Test Unitario Básico

```python
import pytest
from domain.entities import CedulaRecord
from domain.specifications import CedulaFormatSpecification

def test_cedula_format_valid():
    """Test: Cédula con solo dígitos pasa validación."""
    spec = CedulaFormatSpecification()
    record = CedulaRecord(cedula="12345678", confidence=90)

    assert spec.is_satisfied_by(record) is True

def test_cedula_format_invalid():
    """Test: Cédula con letras falla validación."""
    spec = CedulaFormatSpecification()
    record = CedulaRecord(cedula="1234ABC8", confidence=90)

    assert spec.is_satisfied_by(record) is False

def test_cedula_format_empty():
    """Test: Cédula vacía falla validación."""
    spec = CedulaFormatSpecification()
    record = CedulaRecord(cedula="", confidence=90)

    assert spec.is_satisfied_by(record) is False
```

### Test de Combinaciones

```python
def test_combined_specifications_and():
    """Test: Combinación AND de especificaciones."""
    spec = (
        CedulaFormatSpecification()
        .and_(CedulaLengthSpecification(6, 10))
        .and_(ConfidenceSpecification(50.0))
    )

    # Caso válido
    valid_record = CedulaRecord(cedula="12345678", confidence=90)
    assert spec.is_satisfied_by(valid_record) is True

    # Caso inválido: longitud incorrecta
    invalid_length = CedulaRecord(cedula="123", confidence=90)
    assert spec.is_satisfied_by(invalid_length) is False

    # Caso inválido: confianza baja
    invalid_conf = CedulaRecord(cedula="12345678", confidence=30)
    assert spec.is_satisfied_by(invalid_conf) is False
```

### Test de Operadores

```python
def test_specification_operators():
    """Test: Operadores sobrecargados (&, |, ~)."""
    # AND operator
    spec_and = CedulaFormatSpecification() & CedulaLengthSpecification(6, 10)
    record = CedulaRecord(cedula="12345678", confidence=90)
    assert spec_and.is_satisfied_by(record) is True

    # OR operator
    spec_or = ConfidenceSpecification(90) | ConfidenceSpecification(30)
    assert spec_or.is_satisfied_by(record) is True

    # NOT operator
    spec_not = ~CedulaFormatSpecification()
    invalid = CedulaRecord(cedula="ABC", confidence=90)
    assert spec_not.is_satisfied_by(invalid) is True
```

---

## 📊 Ventajas vs Desventajas

### ✅ Ventajas

1. **Reutilización**
   - Especificaciones se usan en múltiples contextos

2. **Testabilidad**
   - Cada especificación se testea independientemente

3. **Composición**
   - Combinar reglas simples para crear reglas complejas

4. **Expresividad**
   - Código más legible y declarativo

5. **Open/Closed Principle**
   - Agregar reglas sin modificar código existente

6. **Flexibilidad**
   - Cambiar reglas en runtime según contexto

### ⚠️ Desventajas (Menores)

1. **Más clases**
   - Una clase por especificación

2. **Indirección**
   - Lógica distribuida en múltiples archivos

3. **Curva de aprendizaje**
   - Requiere entender el patrón

**Conclusión:** Las ventajas superan ampliamente las desventajas.

---

## 🎓 Principios SOLID Aplicados

### Single Responsibility (SRP)
- Cada especificación tiene una única responsabilidad

### Open/Closed (OCP)
- Abierto a extensión (nuevas specs), cerrado a modificación

### Liskov Substitution (LSP)
- Todas las especificaciones son intercambiables

### Interface Segregation (ISP)
- Interface minimalista: solo `is_satisfied_by()`

### Dependency Inversion (DIP)
- Entidades dependen de abstracción (Specification), no de concreciones

---

## 📚 Referencias

### Documentación del Proyecto

- **Resumen:** `docs/mejoraSOLID/00_RESUMEN_MEJORAS_CRITICAS.md`
- **Código:** `src/domain/specifications/`

### Libros y Artículos

- **Domain-Driven Design** - Eric Evans (2003)
- **Patterns of Enterprise Application Architecture** - Martin Fowler
- **Specification Pattern** - Eric Evans & Martin Fowler

### Online

- [Specification Pattern - Wikipedia](https://en.wikipedia.org/wiki/Specification_pattern)
- [Martin Fowler - Specification](https://www.martinfowler.com/apsupp/spec.pdf)

---

## 💡 Tips y Mejores Prácticas

### ✅ DO

1. **Nombrar específicamente**
   ```python
   CedulaLengthSpecification  # ✅ Claro
   ```

2. **Una responsabilidad por especificación**
   ```python
   CedulaFormatSpecification  # ✅ Solo formato
   ```

3. **Hacer especificaciones inmutables**
   ```python
   class MySpec(Specification):
       def __init__(self, value: int):
           self._value = value  # ✅ Privado
   ```

4. **Proveer __repr__**
   ```python
   def __repr__(self):
       return f"MySpec(value={self._value})"
   ```

5. **Documentar qué valida**
   ```python
   """Verifica que la cédula no empiece con 0."""
   ```

### ❌ DON'T

1. **No modificar estado**
   ```python
   def is_satisfied_by(self, candidate):
       self.last_checked = candidate  # ❌ Efecto secundario
   ```

2. **No hacer especificaciones muy complejas**
   ```python
   # ❌ Demasiadas responsabilidades
   class AllValidationsSpecification
   ```

3. **No hardcodear valores en `is_satisfied_by()`**
   ```python
   def is_satisfied_by(self, candidate):
       return candidate.value > 50  # ❌ Hardcodeado
   ```

4. **No lanzar excepciones en validación**
   ```python
   def is_satisfied_by(self, candidate):
       if not candidate.valid:
           raise ValueError()  # ❌ Solo retornar bool
       return True
   ```

---

## 🚀 Ejercicios

### Ejercicio 1: Crear Especificación Básica

Crear `CedulaEvenSpecification` que valida cédulas con último dígito par.

<details>
<summary>Solución</summary>

```python
class CedulaEvenSpecification(Specification['CedulaRecord']):
    """Valida que la cédula termine en dígito par."""

    def is_satisfied_by(self, record: 'CedulaRecord') -> bool:
        if not record.cedula or not record.cedula.isdigit():
            return False
        last_digit = int(record.cedula[-1])
        return last_digit % 2 == 0
```
</details>

### Ejercicio 2: Combinar Especificaciones

Crear validación que acepte cédulas de 8-10 dígitos con confianza >80% o cédulas de 6-7 dígitos con confianza >95%.

<details>
<summary>Solución</summary>

```python
spec = (
    (
        CedulaLengthSpecification(8, 10)
        .and_(ConfidenceSpecification(80.0))
    )
    .or_(
        CedulaLengthSpecification(6, 7)
        .and_(ConfidenceSpecification(95.0))
    )
)
```
</details>

---

**¡Ahora estás listo para usar Specification Pattern en el proyecto!** 🎉
