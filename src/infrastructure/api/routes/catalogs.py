"""Catalog endpoints (Document Types, Permission Types, Scopes)."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional

from src.infrastructure.api.schemas.catalog_schemas import (
    DocumentTypeResponse,
    PermissionTypeResponse,
    ScopeResponse
)
from src.application.use_cases.list_document_types_use_case import ListDocumentTypesUseCase
from src.application.use_cases.get_document_type_use_case import GetDocumentTypeUseCase
from src.application.use_cases.list_permission_types_use_case import ListPermissionTypesUseCase
from src.application.use_cases.list_available_scopes_use_case import ListAvailableScopesUseCase
from src.infrastructure.api.dependencies import (
    get_list_document_types_use_case,
    get_get_document_type_use_case,
    get_list_permission_types_use_case,
    get_list_available_scopes_use_case
)

router = APIRouter(prefix="/catalogs", tags=["Catalogs"])


@router.get("/document-types", response_model=List[DocumentTypeResponse])
async def list_document_types(
    active_only: bool = Query(True, description="Return only active document types"),
    use_case: ListDocumentTypesUseCase = Depends(get_list_document_types_use_case)
):
    """
    List available document types.

    Returns types of documents that can be processed by the system:
    - cedula_form: Formulario de 15 cédulas
    - e14: E-14 Electoral
    - generic_text: OCR genérico
    """
    document_types = use_case.execute(active_only=active_only)
    return [DocumentTypeResponse(**dt.to_dict()) for dt in document_types]


@router.get("/document-types/{code}", response_model=DocumentTypeResponse)
async def get_document_type(
    code: str,
    use_case: GetDocumentTypeUseCase = Depends(get_get_document_type_use_case)
):
    """
    Get specific document type by code.

    Example codes: 'cedula_form', 'e14', 'generic_text'
    """
    document_type = use_case.execute(code)

    if not document_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document type '{code}' not found"
        )

    return DocumentTypeResponse(**document_type.to_dict())


@router.get("/permission-types", response_model=List[PermissionTypeResponse])
async def list_permission_types(
    active_only: bool = Query(True, description="Return only active permission types"),
    use_case: ListPermissionTypesUseCase = Depends(get_list_permission_types_use_case)
):
    """
    List available permission types.

    Returns types of permissions that can be assigned:
    - read: Leer
    - write: Escribir
    - delete: Eliminar
    - validate: Validar
    - export: Exportar
    - admin: Administrar
    """
    permission_types = use_case.execute(active_only=active_only)
    return [PermissionTypeResponse(**pt) for pt in permission_types]


@router.get("/scopes", response_model=List[ScopeResponse])
async def list_available_scopes(
    document_type: Optional[str] = Query(None, description="Filter by document type code"),
    active_only: bool = Query(True, description="Return only active scopes"),
    use_case: ListAvailableScopesUseCase = Depends(get_list_available_scopes_use_case)
):
    """
    List available permission scopes.

    Scopes define granular permissions for API keys.

    Examples:
    - cedula_form:read - Read cedula forms
    - e14:validate - Validate E-14 documents
    - documents:admin - Admin access to all documents

    Query Parameters:
    - document_type: Filter scopes by document type (e.g., 'cedula_form')
    - active_only: Return only active scopes
    """
    scopes = use_case.execute(
        document_type_code=document_type,
        active_only=active_only
    )
    return [ScopeResponse(**scope) for scope in scopes]
