"""Document processing endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Dict

from src.infrastructure.api.schemas.e14_schemas import E14ProcessResult
from src.application.use_cases.process_document_use_case import (
    ProcessDocumentUseCase,
    DocumentTypeNotFoundError
)
from src.domain.entities.user import User
from src.infrastructure.api.dependencies import (
    get_current_user,
    get_process_document_use_case
)
from src.infrastructure.storage.json_storage import JSONStorage

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/process",
    response_model=Dict,
    status_code=status.HTTP_200_OK,
    summary="Process Document",
    description="""
    Process document and extract structured data.

    **Supported Document Types:**
    - `e14`: Electoral E-14 forms (PDF or image)
    - `cedula_form`: Cédula forms (coming soon)
    - `generic_text`: Generic text extraction (coming soon)

    **File Requirements:**
    - E-14: PDF (recommended) or image (JPEG, PNG, TIFF)
    - Max file size: 10MB
    - For best results, use 300 DPI scans

    **Authentication:**
    Requires valid API key or JWT token.

    **Response:**
    Returns structured data based on document type.
    Results are also saved as JSON files in `data/results/` for validation.
    """,
    responses={
        200: {
            "description": "Document processed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "metadata": {
                            "pdf_filename": "e14_camara_066.pdf",
                            "tipo_documento": "E-14",
                            "tipo_eleccion": "CAMARA",
                            "processed_at": "2025-01-21T10:30:00Z"
                        },
                        "divipol": {
                            "departamento_codigo": "16",
                            "departamento_nombre": "BOGOTA D.C.",
                            "municipio_codigo": "001",
                            "municipio_nombre": "BOGOTA. D.C.",
                            "lugar": "USAQUÉN",
                            "zona": "01",
                            "puesto": "01",
                            "mesa": "066"
                        },
                        "partidos": [],
                        "votos_especiales": {
                            "votos_blanco": 6,
                            "votos_nulos": 3,
                            "votos_no_marcados": 1
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid file or document type"},
        404: {"description": "Document type not found"},
        422: {"description": "Could not extract required data"},
        500: {"description": "Processing failed"}
    }
)
async def process_document(
    document_type: str = Form(..., description="Document type code (e.g., 'e14')"),
    file: UploadFile = File(..., description="Document file (PDF or image)"),
    use_case: ProcessDocumentUseCase = Depends(get_process_document_use_case),
    current_user: User = Depends(get_current_user)
):
    """
    Process document and extract structured data.

    Validates document type, processes file with appropriate processor,
    saves result as JSON, and returns structured data.
    """
    # Read file content
    try:
        file_bytes = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file: {str(e)}"
        )

    # Validate file size (10MB max)
    max_size = 10 * 1024 * 1024  # 10MB
    if len(file_bytes) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size: 10MB, got: {len(file_bytes) / 1024 / 1024:.2f}MB"
        )

    # Validate file not empty
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file"
        )

    # Process document
    try:
        result = use_case.execute(
            file_bytes=file_bytes,
            filename=file.filename or "unknown",
            document_type_code=document_type
        )

        # Save result as JSON for validation
        json_storage = JSONStorage()
        json_path = json_storage.save_result(result, file.filename)

        # Add save path to result metadata (for debugging)
        if 'metadata' in result and isinstance(result['metadata'], dict):
            result['metadata']['saved_to'] = json_path

        return result

    except DocumentTypeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    except ValueError as e:
        # Invalid file format or insufficient data extracted
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )

    except NotImplementedError as e:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )


@router.get(
    "/supported-types",
    response_model=list[str],
    summary="List Supported Document Types",
    description="Get list of document types that can be processed."
)
async def list_supported_types(
    use_case: ProcessDocumentUseCase = Depends(get_process_document_use_case)
):
    """List supported document types."""
    # Get supported types from factory
    supported = use_case._processor_factory.get_supported_types()
    return supported
