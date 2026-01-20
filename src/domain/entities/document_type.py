"""Document Type domain entity."""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class DocumentType:
    """
    Document Type entity - Represents a processable document type.

    This is a SIMPLE entity (mostly catalog data).
    Business logic will be in processors, not here.
    """

    id: int
    code: str
    name: str
    description: Optional[str]
    category: str
    expected_rows: Optional[int]
    validate_totals: bool
    base_cost: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'expected_rows': self.expected_rows,
            'validate_totals': self.validate_totals,
            'base_cost': float(self.base_cost),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
