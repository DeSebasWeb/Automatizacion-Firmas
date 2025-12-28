"""Database session management - Production grade."""

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import DisconnectionError
import structlog

from ..config import settings

logger = structlog.get_logger(__name__)

# =========================================================================
# GLOBAL ENGINE (Singleton - se crea UNA sola vez)
# =========================================================================

engine = create_engine(
    settings.DATABASE_URL,

    # Pool configuration
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    pool_pre_ping=True,  # Verify connections before use

    # Logging
    echo=settings.DATABASE_ECHO,

    # Performance
    connect_args={
        "connect_timeout": 10,
        "options": "-c timezone=utc"
    }
)

# =========================================================================
# SESSION FACTORY (Singleton)
# =========================================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# =========================================================================
# CONNECTION POOL MONITORING
# =========================================================================

@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log successful connections."""
    logger.debug("database_connection_established")

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log connection checkout from pool."""
    logger.debug("database_connection_checkout")

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """Log connection return to pool."""
    logger.debug("database_connection_checkin")

# =========================================================================
# HEALTH CHECK
# =========================================================================

def check_database_connection() -> bool:
    """
    Verify database connectivity.

    Returns:
        True if connection is healthy, False otherwise.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        return False

# =========================================================================
# LIFECYCLE MANAGEMENT (for FastAPI lifespan events)
# =========================================================================

def init_db():
    """Initialize database connection pool (called at app startup)."""
    try:
        logger.info("initializing_database_connection_pool")
        # Test connection
        if check_database_connection():
            logger.info("database_connection_pool_initialized",
                       pool_size=settings.DATABASE_POOL_SIZE)
        else:
            logger.error("database_connection_pool_initialization_failed")
    except Exception as e:
        logger.error("database_initialization_error", error=str(e))
        raise

def close_db():
    """Close database connections (called at app shutdown)."""
    try:
        logger.info("closing_database_connections")
        engine.dispose()
        logger.info("database_connections_closed")
    except Exception as e:
        logger.error("database_close_error", error=str(e))