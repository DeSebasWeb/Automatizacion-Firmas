"""Catalog DTOs (Document Types, Permission Types, Scopes)."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DocumentTypeResponse(BaseModel):
    """Document type response."""
    id: int
    code: str
    name: str
    description: Optional[str]
    category: str
    expected_rows: Optional[int] = Field(None, description="Expected number of rows for this document type")
    validate_totals: bool = Field(description="Whether totals should be validated")
    base_cost: float = Field(description="Base cost per page")
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PermissionTypeResponse(BaseModel):
    """Permission type response."""
    id: int
    code: str
    name: str
    description: Optional[str]
    is_active: bool


class ScopeResponse(BaseModel):
    """Permission scope response."""
    id: int
    code: str = Field(..., description="Scope code (e.g., 'cedula_form:read')")
    name: str
    description: Optional[str]
    category: Optional[str]
    document_type: Optional[str] = Field(None, description="Document type code (null for generic scopes)")
    permission_type: Optional[str] = Field(None, description="Permission type code")
    is_active: bool
