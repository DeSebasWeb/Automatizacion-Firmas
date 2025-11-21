"""Value Object para coordenadas en pantalla."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Coordinate:
    """
    Value Object que representa una coordenada 2D inmutable.

    Encapsula la lógica de manejo de coordenadas con validación
    automática y métodos de utilidad para cálculos geométricos.

    **Características:**
    - Inmutable (frozen=True)
    - Auto-validación (no negativas)
    - Comparación por valor
    - Operaciones geométricas

    **Reglas de negocio:**
    - x >= 0 (no puede ser negativo)
    - y >= 0 (no puede ser negativo)
    - Valores enteros (píxeles en pantalla)

    Example:
        >>> # Creación válida
        >>> coord = Coordinate(100, 200)
        >>> print(coord)
        (100, 200)
        >>>
        >>> # Validación automática
        >>> coord = Coordinate(-10, 20)  # Raises ValueError
        >>>
        >>> # Operaciones geométricas
        >>> p1 = Coordinate(0, 0)
        >>> p2 = Coordinate(3, 4)
        >>> p1.distance_to(p2)
        5.0
        >>>
        >>> # Comparación por valor
        >>> c1 = Coordinate(10, 20)
        >>> c2 = Coordinate(10, 20)
        >>> assert c1 == c2  # True
    """

    x: int
    """Coordenada X (horizontal, desde izquierda)"""

    y: int
    """Coordenada Y (vertical, desde arriba)"""

    def __post_init__(self):
        """
        Validación automática al construir.

        Raises:
            ValueError: Si las coordenadas son negativas
            TypeError: Si las coordenadas no son enteros
        """
        if not isinstance(self.x, int):
            raise TypeError(
                f"x debe ser entero, recibido: {type(self.x).__name__}"
            )

        if not isinstance(self.y, int):
            raise TypeError(
                f"y debe ser entero, recibido: {type(self.y).__name__}"
            )

        if self.x < 0 or self.y < 0:
            raise ValueError(
                f"Coordenadas no pueden ser negativas: ({self.x}, {self.y})"
            )

    @classmethod
    def origin(cls) -> 'Coordinate':
        """
        Retorna el origen (0, 0).

        Returns:
            Coordinate en (0, 0)
        """
        return cls(0, 0)

    @classmethod
    def from_tuple(cls, coords: tuple[int, int]) -> 'Coordinate':
        """
        Crea Coordinate desde tupla.

        Args:
            coords: Tupla (x, y)

        Returns:
            Coordinate

        Example:
            >>> coord = Coordinate.from_tuple((100, 200))
        """
        return cls(coords[0], coords[1])

    def as_tuple(self) -> tuple[int, int]:
        """
        Convierte a tupla (x, y).

        Returns:
            Tupla con coordenadas

        Example:
            >>> coord = Coordinate(100, 200)
            >>> coord.as_tuple()
            (100, 200)
        """
        return (self.x, self.y)

    def distance_to(self, other: 'Coordinate') -> float:
        """
        Calcula distancia euclidiana a otra coordenada.

        Args:
            other: Otra coordenada

        Returns:
            Distancia en píxeles

        Example:
            >>> p1 = Coordinate(0, 0)
            >>> p2 = Coordinate(3, 4)
            >>> p1.distance_to(p2)
            5.0
        """
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)

    def manhattan_distance_to(self, other: 'Coordinate') -> int:
        """
        Calcula distancia de Manhattan a otra coordenada.

        La distancia Manhattan es la suma de diferencias absolutas
        en X e Y (distancia en movimientos ortogonales).

        Args:
            other: Otra coordenada

        Returns:
            Distancia Manhattan

        Example:
            >>> p1 = Coordinate(0, 0)
            >>> p2 = Coordinate(3, 4)
            >>> p1.manhattan_distance_to(p2)
            7
        """
        return abs(self.x - other.x) + abs(self.y - other.y)

    def is_within_bounds(self, width: int, height: int) -> bool:
        """
        Verifica si la coordenada está dentro de los límites.

        Args:
            width: Ancho máximo
            height: Alto máximo

        Returns:
            True si está dentro de los límites

        Example:
            >>> coord = Coordinate(100, 200)
            >>> coord.is_within_bounds(800, 600)
            True
            >>> coord.is_within_bounds(50, 100)
            False
        """
        return 0 <= self.x < width and 0 <= self.y < height

    def translate(self, dx: int, dy: int) -> 'Coordinate':
        """
        Crea nueva coordenada trasladada por (dx, dy).

        Args:
            dx: Desplazamiento en X
            dy: Desplazamiento en Y

        Returns:
            Nueva coordenada trasladada

        Example:
            >>> coord = Coordinate(100, 200)
            >>> new_coord = coord.translate(50, -30)
            >>> print(new_coord)
            (150, 170)
        """
        new_x = self.x + dx
        new_y = self.y + dy

        # Asegurar que no sean negativas
        if new_x < 0 or new_y < 0:
            raise ValueError(
                f"Traslación resulta en coordenadas negativas: "
                f"({new_x}, {new_y})"
            )

        return Coordinate(new_x, new_y)

    def __str__(self) -> str:
        """String representation."""
        return f"({self.x}, {self.y})"

    def __repr__(self) -> str:
        """Representación para debugging."""
        return f"Coordinate({self.x}, {self.y})"

    def __hash__(self) -> int:
        """Hash para usar en sets/dicts."""
        return hash((self.x, self.y))

    def __iter__(self):
        """Permite desempaquetar: x, y = coordinate"""
        return iter((self.x, self.y))


# ========== VALUE OBJECTS RELACIONADOS ==========

@dataclass(frozen=True)
class Rectangle:
    """
    Value Object que representa un rectángulo inmutable.

    Define un área rectangular usando coordenada de inicio y dimensiones.

    Attributes:
        origin: Coordenada de esquina superior izquierda
        width: Ancho del rectángulo
        height: Alto del rectángulo
    """

    origin: Coordinate
    """Esquina superior izquierda"""

    width: int
    """Ancho del rectángulo"""

    height: int
    """Alto del rectángulo"""

    def __post_init__(self):
        """Validación automática."""
        if self.width <= 0:
            raise ValueError(f"Width debe ser positivo: {self.width}")

        if self.height <= 0:
            raise ValueError(f"Height debe ser positivo: {self.height}")

    @classmethod
    def from_coords(
        cls,
        x: int,
        y: int,
        width: int,
        height: int
    ) -> 'Rectangle':
        """
        Crea Rectangle desde coordenadas individuales.

        Args:
            x: Coordenada X de origen
            y: Coordenada Y de origen
            width: Ancho
            height: Alto

        Returns:
            Rectangle

        Example:
            >>> rect = Rectangle.from_coords(10, 20, 100, 50)
        """
        return cls(Coordinate(x, y), width, height)

    @property
    def top_left(self) -> Coordinate:
        """Esquina superior izquierda."""
        return self.origin

    @property
    def top_right(self) -> Coordinate:
        """Esquina superior derecha."""
        return Coordinate(self.origin.x + self.width, self.origin.y)

    @property
    def bottom_left(self) -> Coordinate:
        """Esquina inferior izquierda."""
        return Coordinate(self.origin.x, self.origin.y + self.height)

    @property
    def bottom_right(self) -> Coordinate:
        """Esquina inferior derecha."""
        return Coordinate(
            self.origin.x + self.width,
            self.origin.y + self.height
        )

    @property
    def center(self) -> Coordinate:
        """Centro del rectángulo."""
        center_x = self.origin.x + (self.width // 2)
        center_y = self.origin.y + (self.height // 2)
        return Coordinate(center_x, center_y)

    @property
    def area(self) -> int:
        """Área del rectángulo."""
        return self.width * self.height

    def contains(self, coord: Coordinate) -> bool:
        """
        Verifica si una coordenada está dentro del rectángulo.

        Args:
            coord: Coordenada a verificar

        Returns:
            True si está dentro

        Example:
            >>> rect = Rectangle.from_coords(10, 10, 100, 50)
            >>> rect.contains(Coordinate(50, 30))
            True
            >>> rect.contains(Coordinate(200, 200))
            False
        """
        return (
            self.origin.x <= coord.x < self.origin.x + self.width and
            self.origin.y <= coord.y < self.origin.y + self.height
        )

    def overlaps(self, other: 'Rectangle') -> bool:
        """
        Verifica si este rectángulo se solapa con otro.

        Args:
            other: Otro rectángulo

        Returns:
            True si hay solapamiento

        Example:
            >>> r1 = Rectangle.from_coords(0, 0, 100, 100)
            >>> r2 = Rectangle.from_coords(50, 50, 100, 100)
            >>> r1.overlaps(r2)
            True
        """
        return not (
            self.origin.x + self.width <= other.origin.x or
            other.origin.x + other.width <= self.origin.x or
            self.origin.y + self.height <= other.origin.y or
            other.origin.y + other.height <= self.origin.y
        )

    def to_dict(self) -> dict:
        """
        Convierte a diccionario para serialización.

        Returns:
            Dict con x, y, width, height

        Example:
            >>> rect = Rectangle.from_coords(10, 20, 100, 50)
            >>> rect.to_dict()
            {'x': 10, 'y': 20, 'width': 100, 'height': 50}
        """
        return {
            'x': self.origin.x,
            'y': self.origin.y,
            'width': self.width,
            'height': self.height
        }

    def __str__(self) -> str:
        """String representation."""
        return f"Rectangle({self.origin.x}, {self.origin.y}, {self.width}x{self.height})"

    def __repr__(self) -> str:
        """Representación para debugging."""
        return f"Rectangle(origin={self.origin}, width={self.width}, height={self.height})"

    def __hash__(self) -> int:
        """Hash para usar en sets/dicts."""
        return hash((self.origin, self.width, self.height))
