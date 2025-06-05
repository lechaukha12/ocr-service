from fastapi import FastAPI, Depends, HTTPException, status, Body, Path
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import List, Annotated, Optional
from sqlalchemy.orm import Session
import math

import crud
import utils
import database
from config import settings
from schemas import (
    UserBase, UserCreate, User, UserPage, Token, TokenData, UserLogin,
    EkycInfoBase, EkycInfoCreate, EkycInfo, EkycPage,
    EkycRecordSchema, EkycRecordPage, EkycRecordCreate
)

database.create_db_tables()

app = FastAPI(title="User Service")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

from models import UserDB
def create_access_token(user: UserDB, expires_delta: timedelta | None = None):
    to_encode = {"sub": user.username}
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    roles = []
    if user.username == settings.ADMIN_USERNAME_FOR_TESTING:
        roles.append("admin")
    
    to_encode.update({"roles": roles})
    if user.full_name:
        to_encode.update({"full_name": user.full_name})
    to_encode.update({"user_id": user.id}) 
        
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user_db(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: Annotated[UserDB, Depends(get_current_user_db)]
):
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return User.model_validate(current_user)


async def get_current_active_admin_user(
    current_user: Annotated[UserDB, Depends(get_current_user_db)]
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User does not have admin privileges"
    )
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    
    try:
        if current_user.username != settings.ADMIN_USERNAME_FOR_TESTING:
            raise credentials_exception
    except Exception: 
        raise credentials_exception
    
    return User.model_validate(current_user)


@app.post("/users/", response_model=User, status_code=status.HTTP_201_CREATED, tags=["Users"])
def create_new_user(user: UserCreate, db: Session = Depends(database.get_db)):
    db_user_by_email = crud.get_user_by_email(db, email=user.email)
    if db_user_by_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    db_user_by_username = crud.get_user_by_username(db, username=user.username)
    if db_user_by_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
        
    created_user_db = crud.create_user(db=db, user=user)
    return User.model_validate(created_user_db)


@app.post("/token", response_model=Token, tags=["Authentication"])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(database.get_db)
):
    user_db_obj = crud.get_user_by_username(db, username=form_data.username)
    if not user_db_obj or not utils.verify_password(form_data.password, user_db_obj.hashed_password):
        user_by_email = crud.get_user_by_email(db, email=form_data.username)
        if not user_by_email or not utils.verify_password(form_data.password, user_by_email.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_db_obj = user_by_email

    if not user_db_obj.is_active:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        user=user_db_obj, expires_delta=access_token_expires
    )
    user_info_for_response = User.model_validate(user_db_obj)
    return {"access_token": access_token, "token_type": "bearer", "user_info": user_info_for_response}

@app.get("/users/me/", response_model=User, tags=["Users"])
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user

@app.get("/users/", response_model=UserPage, tags=["Admin"])
def read_all_users(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(database.get_db),
    current_admin: Annotated[User, Depends(get_current_active_admin_user)] = None 
):
    if limit <= 0:
        limit = 10
    if skip < 0:
        skip = 0

    users_db_list, total_users = crud.get_users(db, skip=skip, limit=limit)
    
    current_page = (skip // limit) + 1
    total_pages = math.ceil(total_users / limit) if limit > 0 else 0
    if total_pages == 0 and total_users > 0: 
        total_pages = 1


    return UserPage(
        items=[User.model_validate(user_db) for user_db in users_db_list],
        total=total_users,
        page=current_page,
        limit=limit,
        pages=total_pages
    )


@app.post("/ekyc/", response_model=EkycInfo, tags=["eKYC"])
def create_ekyc_info(
    ekyc_info: EkycInfoCreate = Body(...),
    db: Session = Depends(database.get_db),
    current_user: Annotated[User, Depends(get_current_active_user)] = None
):
    if ekyc_info.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="User ID mismatch.")
    db_ekyc = crud.create_ekyc_info(db, ekyc_info)
    return EkycInfo.model_validate(db_ekyc)

@app.get("/ekyc/me", response_model=List[EkycInfo], tags=["eKYC"])
def get_my_ekyc_info(
    db: Session = Depends(database.get_db),
    current_user: Annotated[User, Depends(get_current_active_user)] = None
):
    records = crud.get_ekyc_info_by_user_id(db, current_user.id)
    return [EkycInfo.model_validate(r) for r in records]


@app.get("/ekyc/all", response_model=EkycRecordPage, tags=["Admin"])
def get_all_ekyc_records(
    skip: int = 0,
    limit: int = 10,
    status: Optional[str] = None,
    date: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_admin: Annotated[User, Depends(get_current_active_admin_user)] = None
):
    if limit <= 0:
        limit = 10
    if skip < 0:
        skip = 0

    records, total = crud.get_ekyc_records(
        db, 
        skip=skip, 
        limit=limit, 
        status=status, 
        date=date
    )

    current_page = (skip // limit) + 1
    total_pages = math.ceil(total / limit) if limit > 0 else 0
    if total_pages == 0 and total > 0:
        total_pages = 1

    return EkycRecordPage(
        items=[EkycRecordSchema.model_validate(record) for record in records],
        total=total,
        page=current_page,
        limit=limit,
        size=limit
    )

@app.get("/ekyc/{record_id}", response_model=EkycInfo, tags=["Admin"])
def get_ekyc_record(
    record_id: int,
    db: Session = Depends(database.get_db),
    current_admin: Annotated[User, Depends(get_current_active_admin_user)] = None
):
    record = crud.get_ekyc_info_by_id(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="eKYC record not found")
    return EkycInfo.model_validate(record)

@app.post("/users/{user_id}/activate", tags=["Admin"])
def activate_user(
    user_id: int = Path(...), 
    db: Session = Depends(database.get_db), 
    current_admin: Annotated[User, Depends(get_current_active_admin_user)] = None
):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = True
    db.commit()
    return {"msg": "User activated"}

@app.post("/users/{user_id}/deactivate", tags=["Admin"])
def deactivate_user(
    user_id: int = Path(...), 
    db: Session = Depends(database.get_db), 
    current_admin: Annotated[User, Depends(get_current_active_admin_user)] = None
):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    return {"msg": "User deactivated"}

@app.post("/ekyc/record/", response_model=EkycRecordSchema, tags=["eKYC"])
def create_ekyc_record(
    record: EkycRecordCreate = Body(...),
    db: Session = Depends(database.get_db)
):
    print("[DEBUG] Payload nhận được:", record.dict())
    try:
        db_record = crud.create_ekyc_record(db, record)
        print("[DEBUG] Đã lưu record:", db_record)
        return EkycRecordSchema.model_validate(db_record)
    except Exception as e:
        import traceback
        print("[ERROR] create_ekyc_record exception:", e)
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to create eKYC record: {e}")

from fastapi import APIRouter, Depends, Body, HTTPException, Path, status
from sqlalchemy.orm import Session
from typing import Annotated, List, Optional
import math
from database import get_db
from crud import get_all_ekyc_records
from models import UserDB as User
from schemas import EkycRecordPage, EkycRecordSchema

router = APIRouter()

@router.get("/ekyc/records/all", response_model=EkycRecordPage, tags=["Admin"])
def get_ekyc_records_all(
    skip: int = 0,
    limit: int = 10,
    status: Optional[str] = None,
    date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: Annotated[User, Depends(get_current_active_admin_user)] = None
):
    if limit <= 0:
        limit = 10
    if skip < 0:
        skip = 0

    records, total = crud.get_ekyc_records(
        db, 
        skip=skip, 
        limit=limit, 
        status=status, 
        date=date
    )

    current_page = (skip // limit) + 1
    total_pages = math.ceil(total / limit) if limit > 0 else 0
    if total_pages == 0 and total > 0:
        total_pages = 1

    return EkycRecordPage(
        items=[EkycRecordSchema.model_validate(record) for record in records],
        total=total,
        page=current_page,
        limit=limit,
        size=limit
    )

# Đảm bảo router được include vào app
app.include_router(router)