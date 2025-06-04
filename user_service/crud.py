from sqlalchemy.orm import Session
from models import UserDB, EkycInfoDB, EkycRecord
from schemas import (
    UserBase, UserCreate, User, UserPage, Token, TokenData, UserLogin,
    EkycInfoBase, EkycInfoCreate, EkycInfo, EkycPage,
    EkycRecordSchema, EkycRecordPage
)
import utils

def get_user_by_email(db: Session, email: str) -> UserDB | None:
    return db.query(UserDB).filter(UserDB.email == email).first()

def get_user_by_username(db: Session, username: str) -> UserDB | None:
    return db.query(UserDB).filter(UserDB.username == username).first()

def get_user_by_id(db: Session, user_id: int) -> UserDB | None:
    return db.query(UserDB).filter(UserDB.id == user_id).first()

def create_user(db: Session, user: UserCreate) -> UserDB:
    hashed_password = utils.get_password_hash(user.password)
    db_user = UserDB(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db: Session, skip: int = 0, limit: int = 100) -> tuple[list[UserDB], int]:
    total_users = db.query(UserDB).count()
    users = db.query(UserDB).order_by(UserDB.id).offset(skip).limit(limit).all()
    return users, total_users

def create_ekyc_info(db: Session, ekyc_info: EkycInfoCreate) -> EkycInfoDB:
    db_ekyc = EkycInfoDB(**ekyc_info.dict())
    db.add(db_ekyc)
    db.commit()
    db.refresh(db_ekyc)
    return db_ekyc

def get_ekyc_info_by_user_id(db: Session, user_id: int) -> list[EkycInfoDB]:
    return db.query(EkycInfoDB).filter(EkycInfoDB.user_id == user_id).order_by(EkycInfoDB.created_at.desc()).all()

def get_ekyc_records(db: Session, skip: int = 0, limit: int = 10, status: str = None, date: str = None):
    query = db.query(EkycInfoDB)
    if status:
        query = query.filter(EkycInfoDB.status == status)
    if date:
        query = query.filter(EkycInfoDB.created_at.cast(String).like(f"{date}%"))
    total = query.count()
    records = query.order_by(EkycInfoDB.id.desc()).offset(skip).limit(limit).all()
    return records, total

def create_ekyc_record(db: Session, record_data):
    from models import EkycRecord
    db_record = EkycRecord(**record_data.dict())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def get_all_ekyc_records(db: Session, skip: int = 0, limit: int = 10, status: str = None, date: str = None):
    query = db.query(EkycRecord)
    if status:
        query = query.filter(EkycRecord.status == status)
    if date:
        query = query.filter(EkycRecord.created_at.cast(String).like(f"{date}%"))
    total = query.count()
    records = query.order_by(EkycRecord.id.desc()).offset(skip).limit(limit).all()
    return records, total