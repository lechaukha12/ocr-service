from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func 
from database import Base
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

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

    class Config:
        from_attributes = True

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
    user_id = Column(Integer, index=True, nullable=False)
    id_number = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    date_of_birth = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    nationality = Column(String, nullable=True)
    place_of_origin = Column(String, nullable=True)
    place_of_residence = Column(String, nullable=True)
    expiry_date = Column(String, nullable=True)
    selfie_image_url = Column(String, nullable=True)
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

    class Config:
        from_attributes = True

class EkycPage(BaseModel):
    items: list[EkycInfo]
    total: int
    page: int
    limit: int
    pages: int