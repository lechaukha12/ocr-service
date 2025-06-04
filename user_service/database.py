from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from psycopg2.errors import OperationalError
from config import settings
import logging

logger = logging.getLogger(__name__)

# Configure PostgreSQL connection settings with connection pooling
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=5,  # Maximum number of connections in the pool
    max_overflow=10,  # Maximum number of connections that can be created beyond pool_size
    pool_timeout=30,  # Timeout for getting a connection from the pool
    pool_recycle=1800,  # Recycle connections after 30 minutes
    pool_pre_ping=True  # Enable connection health checks
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        # Test the connection
        db.execute("SELECT 1")
        yield db
    except OperationalError as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        db.close()

def create_db_tables():
    retries = 3
    for attempt in range(retries):
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Successfully created database tables")
            break
        except OperationalError as e:
            if attempt == retries - 1:
                logger.error(f"Failed to create database tables after {retries} attempts")
                raise
            logger.warning(f"Failed to create tables (attempt {attempt + 1}/{retries}): {e}")
