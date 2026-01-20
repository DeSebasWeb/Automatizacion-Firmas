"""Permission Type repository implementation."""
from typing import List, Optional
import structlog
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.domain.repositories.permission_type_repository import IPermissionTypeRepository
from src.domain.exceptions.exceptions import RepositoryError
from src.infrastructure.database.models.permission_type import PermissionType as DBPermissionType
from src.infrastructure.database.models.api_permission_scope import APIPermissionScope as DBAPIPermissionScope
from src.infrastructure.database.models.document_type import DocumentType as DBDocumentType

logger = structlog.get_logger(__name__)


class PermissionTypeRepository(IPermissionTypeRepository):
    """SQLAlchemy implementation of IPermissionTypeRepository."""

    def __init__(self, session: Session):
        self._session = session

    def list_all(self, active_only: bool = True) -> List[dict]:
        """List all permission types."""
        try:
            query = self._session.query(DBPermissionType)

            if active_only:
                query = query.filter(DBPermissionType.is_active == True)

            db_perm_types = query.order_by(DBPermissionType.code).all()

            return [self._to_dict(pt) for pt in db_perm_types]

        except SQLAlchemyError as e:
            logger.error("repository_query_failed", operation="list_permission_types", error=str(e))
            raise RepositoryError(f"Failed to list permission types: {e}") from e

    def find_by_code(self, code: str) -> Optional[dict]:
        """Find permission type by code."""
        try:
            db_perm_type = self._session.query(DBPermissionType).filter(
                DBPermissionType.code == code
            ).first()

            return self._to_dict(db_perm_type) if db_perm_type else None

        except SQLAlchemyError as e:
            logger.error("repository_query_failed", operation="find_permission_type", code=code, error=str(e))
            raise RepositoryError(f"Failed to find permission type: {e}") from e

    def list_scopes_by_document_type(self, document_type_code: str) -> List[dict]:
        """List scopes for a specific document type."""
        try:
            scopes = self._session.query(DBAPIPermissionScope).join(
                DBDocumentType,
                DBAPIPermissionScope.document_type_id == DBDocumentType.id
            ).filter(
                DBDocumentType.code == document_type_code,
                DBAPIPermissionScope.is_active == True
            ).all()

            return [self._scope_to_dict(scope) for scope in scopes]

        except SQLAlchemyError as e:
            logger.error("repository_query_failed", operation="list_scopes_by_document_type", document_type=document_type_code, error=str(e))
            raise RepositoryError(f"Failed to list scopes: {e}") from e

    def list_all_scopes(self, active_only: bool = True) -> List[dict]:
        """List all available scopes."""
        try:
            query = self._session.query(DBAPIPermissionScope)

            if active_only:
                query = query.filter(DBAPIPermissionScope.is_active == True)

            scopes = query.order_by(DBAPIPermissionScope.code).all()

            return [self._scope_to_dict(scope) for scope in scopes]

        except SQLAlchemyError as e:
            logger.error("repository_query_failed", operation="list_all_scopes", error=str(e))
            raise RepositoryError(f"Failed to list scopes: {e}") from e

    @staticmethod
    def _to_dict(db_perm_type: DBPermissionType) -> dict:
        """Convert database model to dictionary."""
        return {
            'id': db_perm_type.id,
            'code': db_perm_type.code,
            'name': db_perm_type.name,
            'description': db_perm_type.description,
            'is_active': db_perm_type.is_active
        }

    @staticmethod
    def _scope_to_dict(db_scope: DBAPIPermissionScope) -> dict:
        """Convert scope model to dictionary."""
        return {
            'id': db_scope.id,
            'code': db_scope.code,
            'name': db_scope.name,
            'description': db_scope.description,
            'category': db_scope.category,
            'document_type': db_scope.document_type.code if db_scope.document_type else None,
            'permission_type': db_scope.permission_type.code if db_scope.permission_type else None,
            'is_active': db_scope.is_active
        }
