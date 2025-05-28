from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DB_SUB_DIR = "db"
if not os.path.exists(DB_SUB_DIR):
    os.makedirs(DB_SUB_DIR)

SQLALCHEMY_DATABASE_URL = f"sqlite:///./{DB_SUB_DIR}/user_service.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_db_tables():
    Base.metadata.create_all(bind=engine)
