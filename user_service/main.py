from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import List, Annotated
from sqlalchemy.orm import Session
import math

import crud
import models
import utils
import database
from config import settings

database.create_db_tables()

app = FastAPI(title="User Service")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(user: models.UserDB, expires_delta: timedelta | None = None):
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
        token_data = models.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: Annotated[models.UserDB, Depends(get_current_user_db)]
):
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return models.User.model_validate(current_user)


async def get_current_active_admin_user(
    current_user: Annotated[models.UserDB, Depends(get_current_user_db)]
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
    
    return models.User.model_validate(current_user)


@app.post("/users/", response_model=models.User, status_code=status.HTTP_201_CREATED, tags=["Users"])
def create_new_user(user: models.UserCreate, db: Session = Depends(database.get_db)):
    db_user_by_email = crud.get_user_by_email(db, email=user.email)
    if db_user_by_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    db_user_by_username = crud.get_user_by_username(db, username=user.username)
    if db_user_by_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
        
    created_user_db = crud.create_user(db=db, user=user)
    return models.User.model_validate(created_user_db)


@app.post("/token", response_model=models.Token, tags=["Authentication"])
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
    user_info_for_response = models.User.model_validate(user_db_obj)
    return {"access_token": access_token, "token_type": "bearer", "user_info": user_info_for_response}

@app.get("/users/me/", response_model=models.User, tags=["Users"])
async def read_users_me(
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    return current_user

@app.get("/users/", response_model=models.UserPage, tags=["Admin"])
def read_all_users(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(database.get_db),
    current_admin: Annotated[models.User, Depends(get_current_active_admin_user)] = None 
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


    return models.UserPage(
        items=[models.User.model_validate(user_db) for user_db in users_db_list],
        total=total_users,
        page=current_page,
        limit=limit,
        pages=total_pages
    )