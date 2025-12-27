"""FastAPI dependencies for database sessions."""

from typing import Generator
from sqlalchemy.orm import Session
import structlog

from .session import SessionLocal

logger = structlog.get_logger(__name__)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI endpoints.
    Provides database session with automatic cleanup.

    Usage:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()

    Yields:
        SQLAlchemy Session

    Note:
        - Session is committed only if no exceptions occur
        - Session is always closed (even on errors)
        - Exceptions are re-raised after cleanup
    """
    db = SessionLocal()
    try:
        logger.debug("database_session_created")
        yield db
        db.commit()  # Commit if no exceptions
        logger.debug("database_session_committed")
    except Exception as e:
        db.rollback()
        logger.error("database_session_rollback", error=str(e))
        raise
    finally:
        db.close()
        logger.debug("database_session_closed")