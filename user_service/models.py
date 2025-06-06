from __future__ import annotations
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Float, ForeignKey, JSON
from sqlalchemy.sql import func 
from sqlalchemy.orm import relationship, Mapped
from database import Base
from typing import List
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
    ekyc_records: Mapped[List["EkycRecord"]] = relationship("EkycRecord", back_populates="user")

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

class EkycRecord(Base):
    __tablename__ = "ekyc_records"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    status = Column(String, index=True)  # PENDING, MATCHED, NOT_MATCHED, ERROR
    face_match_score = Column(Float, nullable=True)
    extracted_info = Column(JSON, nullable=True)  # All extracted fields from eKYC
    document_image_id = Column(String, nullable=True)  # URL to CCCD image
    selfie_image_id = Column(String, nullable=True)  # URL to selfie image
    ocr_text = Column(String, nullable=True)  # Raw OCR text
    verification_note = Column(String, nullable=True)  # Admin verification notes
    verification_status = Column(String, nullable=True)  # APPROVED, REJECTED
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    user: Mapped["UserDB"] = relationship("UserDB", back_populates="ekyc_records", foreign_keys=[user_id])
    verifier: Mapped["UserDB"] = relationship("UserDB", foreign_keys=[verified_by])