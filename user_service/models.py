from sqlalchemy import Boolean, Column, Integer, String, DateTime, Float, ForeignKey, JSON
from sqlalchemy.sql import func 
from sqlalchemy.orm import relationship
from database import Base
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), index=True, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(min_length=8)

class User(UserBase):
    id: int
    is_active: bool = True
    created_at: Optional[datetime] = None
    ekyc_records: List["EkycRecord"] = []

    model_config = {
        "from_attributes": True
    }

class UserPage(BaseModel):
    items: List[User]
    total: int
    page: int
    limit: int
    pages: int

class Token(BaseModel):
    access_token: str
    token_type: str
    user_info: Optional[User] = None

class TokenData(BaseModel):
    username: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class EkycInfoDB(Base):
    __tablename__ = "ekyc_info"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    id_number = Column(String(20), nullable=True)
    full_name = Column(String(100), nullable=True)
    date_of_birth = Column(String(20), nullable=True)
    gender = Column(String(10), nullable=True)
    nationality = Column(String(50), nullable=True)
    place_of_origin = Column(String(255), nullable=True)
    place_of_residence = Column(String(255), nullable=True)
    expiry_date = Column(String(20), nullable=True)
    selfie_image_url = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class EkycInfoBase(BaseModel):
    id_number: Optional[str] = None
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    place_of_origin: Optional[str] = None
    place_of_residence: Optional[str] = None
    expiry_date: Optional[str] = None
    selfie_image_url: Optional[str] = None

class EkycInfoCreate(EkycInfoBase):
    user_id: int

class EkycInfo(EkycInfoBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }

class EkycPage(BaseModel):
    items: list[EkycInfo]
    total: int
    page: int
    limit: int
    pages: int

class EkycRecord(Base):
    __tablename__ = "ekyc_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, index=True)  # pending, completed, failed
    face_match_score = Column(Float, nullable=True)
    extracted_info = Column(JSON, nullable=True)  # Store OCR extracted info
    document_image_id = Column(String, nullable=True)  # ID from storage service
    selfie_image_id = Column(String, nullable=True)  # ID from storage service

    user = relationship("User", back_populates="ekyc_records")

class EkycRecordPage(BaseModel):
    items: List[EkycRecord]
    total: int
    page: int
    size: int