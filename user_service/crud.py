from sqlalchemy.orm import Session
import models
import utils

def get_user_by_email(db: Session, email: str) -> models.UserDB | None:
    return db.query(models.UserDB).filter(models.UserDB.email == email).first()

def get_user_by_username(db: Session, username: str) -> models.UserDB | None:
    return db.query(models.UserDB).filter(models.UserDB.username == username).first()

def get_user_by_id(db: Session, user_id: int) -> models.UserDB | None:
    return db.query(models.UserDB).filter(models.UserDB.id == user_id).first()

def create_user(db: Session, user: models.UserCreate) -> models.UserDB:
    hashed_password = utils.get_password_hash(user.password)
    db_user = models.UserDB(
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

def get_users(db: Session, skip: int = 0, limit: int = 100) -> tuple[list[models.UserDB], int]:
    total_users = db.query(models.UserDB).count()
    users = db.query(models.UserDB).order_by(models.UserDB.id).offset(skip).limit(limit).all()
    return users, total_users

def create_ekyc_info(db: Session, ekyc_info: models.EkycInfoCreate) -> models.EkycInfoDB:
    db_ekyc = models.EkycInfoDB(**ekyc_info.dict())
    db.add(db_ekyc)
    db.commit()
    db.refresh(db_ekyc)
    return db_ekyc

def get_ekyc_info_by_user_id(db: Session, user_id: int) -> list[models.EkycInfoDB]:
    return db.query(models.EkycInfoDB).filter(models.EkycInfoDB.user_id == user_id).order_by(models.EkycInfoDB.created_at.desc()).all()