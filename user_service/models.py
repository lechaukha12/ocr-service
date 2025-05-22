from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str = Field(min_length=8)

class User(UserBase):
    id: int
    is_active: bool = True
    # Chúng ta sẽ thêm các trường từ CCCD sau này
    # full_name: Optional[str] = None
    # id_number: Optional[str] = None
    # date_of_birth: Optional[str] = None 
    # gender: Optional[str] = None
    # nationality: Optional[str] = "Việt Nam"
    # place_of_origin: Optional[str] = None
    # place_of_residence: Optional[str] = None
    # date_of_issue: Optional[str] = None 
    # ekyc_status: str = "pending" 

    class Config:
        from_attributes = True # Đã thay đổi từ orm_mode


class UserInDBBase(UserBase):
    id: int
    hashed_password: str
    is_active: bool = True
    # Thêm các trường khác từ User model nếu cần, với giá trị mặc định
    # full_name: Optional[str] = None
    # id_number: Optional[str] = None
    # date_of_birth: Optional[str] = None
    # gender: Optional[str] = None
    # nationality: Optional[str] = "Việt Nam"
    # place_of_origin: Optional[str] = None
    # place_of_residence: Optional[str] = None
    # date_of_issue: Optional[str] = None
    # ekyc_status: str = "pending"

    class Config:
        from_attributes = True # Đã thay đổi từ orm_mode

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserLogin(BaseModel):
    username: str 
    password: str