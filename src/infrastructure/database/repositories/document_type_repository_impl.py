"""Document Type repository implementation."""
from typing import List, Optional
import structlog
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.domain.repositories.document_type_repository import IDocumentTypeRepository
from src.domain.entities.document_type import DocumentType as DomainDocumentType
from src.domain.exceptions.exceptions import RepositoryError
from src.infrastructure.database.models.document_type import DocumentType as DBDocumentType

logger = structlog.get_logger(__name__)


class DocumentTypeRepository(IDocumentTypeRepository):
    """SQLAlchemy implementation of IDocumentTypeRepository."""

    def __init__(self, session: Session):
        self._session = session

    def list_all(self, active_only: bool = True) -> List[DomainDocumentType]:
        """List all document types."""
        try:
            query = self._session.query(DBDocumentType)

            if active_only:
                query = query.filter(DBDocumentType.is_active == True)

            db_doc_types = query.order_by(DBDocumentType.category, DBDocumentType.code).all()

            logger.debug("document_types_listed", count=len(db_doc_types), active_only=active_only)

            return [self._to_domain(dt) for dt in db_doc_types]

        except SQLAlchemyError as e:
            logger.error("list_document_types_failed", error=str(e))
            raise RepositoryError(f"Failed to list document types: {e}") from e

    def find_by_code(self, code: str) -> Optional[DomainDocumentType]:
        """Find document type by code."""
        try:
            db_doc_type = self._session.query(DBDocumentType).filter(
                DBDocumentType.code == code
            ).first()

            if db_doc_type is None:
                logger.debug("document_type_not_found", code=code)
                return None

            logger.debug("document_type_found", code=code)
            return self._to_domain(db_doc_type)

        except SQLAlchemyError as e:
            logger.error("find_document_type_failed", code=code, error=str(e))
            raise RepositoryError(f"Failed to find document type: {e}") from e

    def find_by_id(self, document_type_id: int) -> Optional[DomainDocumentType]:
        """Find document type by ID."""
        try:
            db_doc_type = self._session.query(DBDocumentType).filter(
                DBDocumentType.id == document_type_id
            ).first()

            return self._to_domain(db_doc_type) if db_doc_type else None

        except SQLAlchemyError as e:
            logger.error("find_document_type_by_id_failed", id=document_type_id, error=str(e))
            raise RepositoryError(f"Failed to find document type: {e}") from e

    def exists_by_code(self, code: str) -> bool:
        """Check if document type exists."""
        try:
            exists = self._session.query(DBDocumentType).filter(
                DBDocumentType.code == code
            ).first() is not None

            logger.debug("document_type_exists_check", code=code, exists=exists)
            return exists

        except SQLAlchemyError as e:
            logger.error("exists_check_failed", code=code, error=str(e))
            raise RepositoryError(f"Failed to check existence: {e}") from e

    @staticmethod
    def _to_domain(db_doc_type: DBDocumentType) -> DomainDocumentType:
        """Convert database model to domain entity."""
        return DomainDocumentType(
            id=db_doc_type.id,
            code=db_doc_type.code,
            name=db_doc_type.name,
            description=db_doc_type.description,
            category=db_doc_type.category,
            expected_rows=db_doc_type.expected_rows,
            validate_totals=db_doc_type.validate_totals,
            base_cost=float(db_doc_type.base_cost) if db_doc_type.base_cost else 0.0,
            is_active=db_doc_type.is_active,
            created_at=db_doc_type.created_at,
            updated_at=db_doc_type.updated_at
        )
