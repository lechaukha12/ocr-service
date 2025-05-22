from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import List, Annotated

from . import crud, models, utils, database
from .config import settings

app = FastAPI(title="User Service")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15) # Mặc định 15 phút
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
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
    
    user = crud.get_user_by_username(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: Annotated[models.UserInDBBase, Depends(get_current_user)]
):
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

@app.post("/users/", response_model=models.User, status_code=status.HTTP_201_CREATED, tags=["Users"])
def create_new_user(user: models.UserCreate):
    db_user_by_email = crud.get_user_by_email(email=user.email)
    if db_user_by_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    db_user_by_username = crud.get_user_by_username(username=user.username)
    if db_user_by_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
        
    created_user = crud.create_user(user=user)
    
    return models.User(
        id=created_user.id,
        username=created_user.username,
        email=created_user.email,
        is_active=created_user.is_active
    )

@app.post("/token", response_model=models.Token, tags=["Authentication"])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = crud.get_user_by_username(username=form_data.username)
    if not user or not utils.verify_password(form_data.password, user.hashed_password):
        # Thử đăng nhập bằng email nếu username không khớp
        user_by_email = crud.get_user_by_email(email=form_data.username)
        if not user_by_email or not utils.verify_password(form_data.password, user_by_email.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = user_by_email

    if not user.is_active: # Kiểm tra sau khi đã xác định được user
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=models.User, tags=["Users"])
async def read_users_me(
    current_user: Annotated[models.UserInDBBase, Depends(get_current_active_user)]
):
    return models.User(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active
    )

# Endpoint này chỉ mang tính minh họa, cần bảo mật đúng cách nếu dùng cho admin
# @app.get("/users/", response_model=List[models.User], tags=["Admin"])
# def read_all_users(skip: int = 0, limit: int = 100, 
#                    # current_admin: Annotated[models.UserInDBBase, Depends(get_current_active_admin_user)] # Cần hàm xác thực admin
#                   ):
#     users_in_db = list(database.fake_users_db.values())[skip : skip + limit]
#     users_response = []
#     for user_data in users_in_db:
#         users_response.append(models.User(
#             id=user_data["id"],
#             username=user_data["username"],
#             email=user_data["email"],
#             is_active=user_data["is_active"]
#         ))
#     return users_response

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)