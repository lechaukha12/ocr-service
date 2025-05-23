from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship # Sẽ dùng sau nếu có quan hệ

from .database import Base # Import Base từ database.py

# --- SQLAlchemy Model ---
class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    # Các trường thông tin eKYC sẽ được thêm vào đây sau này
    # full_name = Column(String, index=True, nullable=True)
    # id_number = Column(String, unique=True, index=True, nullable=True) # Số CCCD
    # date_of_birth = Column(String, nullable=True) # Cân nhắc kiểu Date
    # gender = Column(String, nullable=True)
    # nationality = Column(String, default="Việt Nam", nullable=True)
    # place_of_origin = Column(String, nullable=True)
    # place_of_residence = Column(String, nullable=True)
    # date_of_issue = Column(String, nullable=True) # Cân nhắc kiểu Date
    # ekyc_status = Column(String, default="pending", nullable=True) # ví dụ: pending, verified, rejected


# --- Pydantic Models (giữ nguyên hoặc điều chỉnh nếu cần) ---
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
    # Các trường eKYC sẽ được thêm vào đây để response cho client
    # full_name: Optional[str] = None
    # id_number: Optional[str] = None
    # date_of_birth: Optional[str] = None
    # gender: Optional[str] = None
    # nationality: Optional[str] = "Việt Nam"
    # place_of_origin: Optional[str] = None
    # place_of_residence: Optional[str] = None
    # date_of_issue: Optional[str] = None
    # ekyc_status: Optional[str] = "pending"

    class Config:
        from_attributes = True


# UserInDBBase không còn cần thiết vì chúng ta sẽ dùng UserDB cho DB
# và User (Pydantic) để trả về cho client.
# Tuy nhiên, nếu bạn muốn một Pydantic model đại diện cho đối tượng từ DB
# để validate trước khi trả về, bạn có thể giữ lại hoặc tạo mới.
# class UserInDB(User): # Ví dụ, kế thừa từ User và thêm các trường DB nếu cần
#     hashed_password: str # Không nên trả về trường này cho client
#     pass


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str
