from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# User schemas
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
        arbitrary_types_allowed = True

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

# EkycInfo schemas
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
        arbitrary_types_allowed = True

class EkycPage(BaseModel):
    items: List[EkycInfo]
    total: int
    page: int
    limit: int
    pages: int

# EkycRecord schemas
class EkycRecordSchema(BaseModel):
    id: int
    user_id: Optional[int] = None
    created_at: Optional[datetime] = None
    status: Optional[str] = None
    face_match_score: Optional[float] = None
    extracted_info: Optional[dict] = None
    document_image_id: Optional[str] = None
    selfie_image_id: Optional[str] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

class EkycRecordPage(BaseModel):
    items: List[EkycRecordSchema]
    total: int
    page: int
    size: int

class EkycRecordCreate(BaseModel):
    user_id: Optional[int] = None
    status: Optional[str] = None
    face_match_score: Optional[float] = None
    extracted_info: Optional[dict] = None
    document_image_id: Optional[str] = None
    selfie_image_id: Optional[str] = None
