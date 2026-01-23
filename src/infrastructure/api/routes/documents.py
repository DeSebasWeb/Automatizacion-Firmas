"""Document processing endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Dict
from PIL import Image
import io

from src.infrastructure.api.schemas.e14_schemas import E14ProcessResult, E14TextractResponse
from src.application.use_cases.process_document_use_case import (
    ProcessDocumentUseCase,
    DocumentTypeNotFoundError
)
from src.application.use_cases.process_e14_textract_use_case import ProcessE14TextractUseCase
from src.domain.entities.user import User
from src.infrastructure.api.dependencies import (
    get_current_user,
    get_process_document_use_case,
    get_process_e14_textract_use_case
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


@router.post(
    "/e14/textract",
    response_model=E14TextractResponse,
    status_code=status.HTTP_200_OK,
    summary="Process E-14 with AWS Textract",
    description="""
    Process E-14 electoral form using AWS Textract OCR.

    **Features:**
    - Extracts text horizontally (left-to-right, top-to-bottom)
    - Parses structured data (DIVIPOL, parties, candidates, votes)
    - Marks suspicious data with `necesita_auditoria` flag
    - Returns raw OCR text + structured JSON
    - Saves results to `data/results/` directory

    **File Requirements:**
    - Format: JPEG, PNG, TIFF
    - Max size: 10MB
    - Resolution: 300 DPI recommended
    - Supports both single images and multi-page PDFs (future)

    **Authentication:**
    Requires valid API key or JWT token.

    **Response:**
    - `structured_data`: JSON with parsed E-14 data
    - `raw_ocr_text`: Complete text extracted by Textract
    - `warnings`: List of fields that need manual audit
    - `processing_time_ms`: Time taken to process

    **Audit Flags:**
    Fields with non-numeric symbols (*, /, #, etc.) are marked with
    `necesita_auditoria: true` for manual review.
    """,
    responses={
        200: {
            "description": "E-14 processed successfully with Textract",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
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
                                "Partido": [
                                    {
                                        "numPartido": "0261",
                                        "nombrePartido": "COALICION CENTRO ESPERANZA",
                                        "tipoDeVoto": "ListaConVotoPreferente",
                                        "id": "0",
                                        "votosSoloPorLaAgrupacionPolitica": "1",
                                        "candidatos": [
                                            {
                                                "idcandidato": "101",
                                                "votos": "2",
                                                "necesita_auditoria": False
                                            }
                                        ],
                                        "TotalVotosAgrupacion+VotosCandidatos": "4",
                                        "necesita_auditoria": False
                                    }
                                ]
                            }
                        },
                        "raw_ocr_text": "FORMATO E-14\\nPAGINA 01 de 09\\n...",
                        "warnings": [],
                        "processing_time_ms": 1234
                    }
                }
            }
        },
        400: {"description": "Invalid file format or file too large"},
        401: {"description": "Unauthorized - invalid or missing API key/token"},
        422: {"description": "Could not parse E-14 data"},
        500: {"description": "AWS Textract error or processing failed"}
    }
)
async def process_e14_textract(
    file: UploadFile = File(..., description="E-14 image file (JPEG, PNG, TIFF)"),
    use_case: ProcessE14TextractUseCase = Depends(get_process_e14_textract_use_case),
    current_user: User = Depends(get_current_user)
):
    """
    Process E-14 electoral form using AWS Textract.

    Extracts text with Textract OCR, parses structured data,
    marks audit flags, and saves results.
    """
    # Validate file extension
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif'}
    if file.filename:
        ext = file.filename.lower().split('.')[-1]
        if f'.{ext}' not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )

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

    # Convert bytes to PIL Image
    try:
        image = Image.open(io.BytesIO(file_bytes))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image file: {str(e)}"
        )

    # Process with Textract
    try:
        result = use_case.execute(image, save_result=True)

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=result.get("warnings", ["Processing failed"])[0]
            )

        return result

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )
