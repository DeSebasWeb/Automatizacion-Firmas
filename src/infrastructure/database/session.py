"""Database session configuration and management."""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool


class DatabaseSession:
    """Database session manager following best practices."""

    def __init__(self, database_url: str, echo: bool = False):
        """
        Initialize database session manager.

        Args:
            database_url: PostgreSQL connection string
            echo: Enable SQL query logging
        """
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # Verify connections before using
            echo=echo,
        )
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get a database session with automatic cleanup.

        Yields:
            SQLAlchemy Session

        Example:
            with db.get_session() as session:
                user = session.query(User).first()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_all(self):
        """Create all tables (use only for testing)."""
        from src.infrastructure.database.base import Base

        Base.metadata.create_all(bind=self.engine)

    def drop_all(self):
        """Drop all tables (use only for testing)."""
        from src.infrastructure.database.base import Base

        Base.metadata.drop_all(bind=self.engine)