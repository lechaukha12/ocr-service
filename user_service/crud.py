from sqlalchemy.orm import Session
# Sửa các import tương đối thành tuyệt đối
import models  # Thay vì from . import models
import utils   # Thay vì from . import utils

def get_user_by_email(db: Session, email: str) -> models.UserDB | None: # Đảm bảo models.UserDB được gọi đúng
    return db.query(models.UserDB).filter(models.UserDB.email == email).first()

def get_user_by_username(db: Session, username: str) -> models.UserDB | None: # Đảm bảo models.UserDB được gọi đúng
    return db.query(models.UserDB).filter(models.UserDB.username == username).first()

def get_user_by_id(db: Session, user_id: int) -> models.UserDB | None: # Đảm bảo models.UserDB được gọi đúng
    return db.query(models.UserDB).filter(models.UserDB.id == user_id).first()

def create_user(db: Session, user: models.UserCreate) -> models.UserDB: # Đảm bảo models.UserCreate và models.UserDB được gọi đúng
    hashed_password = utils.get_password_hash(user.password) # Đảm bảo utils.get_password_hash được gọi đúng
    db_user = models.UserDB(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[models.UserDB]: # Đảm bảo models.UserDB được gọi đúng
    return db.query(models.UserDB).offset(skip).limit(limit).all()
