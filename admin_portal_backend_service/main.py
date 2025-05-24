from fastapi import FastAPI, HTTPException, status, Depends, Request
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
import httpx
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, EmailStr 
from datetime import datetime
import math 

from config import settings as backend_settings

app = FastAPI(title="Admin Portal Backend Service")

DEFAULT_TIMEOUT = 10.0

class User(BaseModel):
    id: int
    email: EmailStr
    username: str
    is_active: bool
    created_at: Optional[datetime] = None
    full_name: Optional[str] = None

    class Config:
        from_attributes = True

class UserPage(BaseModel):
    items: List[User]
    total: int
    page: int
    limit: int
    pages: int


async def get_current_admin_user(request: Request) -> Dict[str, Any]:
    token = request.headers.get("Authorization")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials for admin",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        raise credentials_exception
    
    if token.startswith("Bearer "):
        token = token.split("Bearer ")[1]
    else:
        raise credentials_exception

    try:
        payload = jwt.decode(token, backend_settings.USER_SERVICE_JWT_SECRET_KEY, algorithms=[backend_settings.USER_SERVICE_ALGORITHM])
        username: str | None = payload.get("sub")
        roles: List[str] = payload.get("roles", [])
        
        if username is None:
            raise credentials_exception
        if "admin" not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have admin privileges"
            )
        
        user_data = {"username": username, "roles": roles, "full_name": payload.get("full_name")}
        return user_data
        
    except JWTError:
        raise credentials_exception


@app.get("/admin/users/", response_model=UserPage, tags=["Admin - Users"])
async def get_all_users_from_user_service(
    request: Request,
    page: int = 1,
    limit: int = 10,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    if page < 1: page = 1
    if limit < 1: limit =1
    skip = (page - 1) * limit
    
    target_url = f"{backend_settings.USER_SERVICE_URL}/users/"
    
    params = {"skip": skip, "limit": limit} 
    
    client_headers = {
        "Authorization": request.headers.get("Authorization")
    }

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            response = await client.get(target_url, params=params, headers=client_headers)
            response.raise_for_status()
            
            user_page_data_from_user_service = response.json()
            
            validated_user_page = UserPage.model_validate(user_page_data_from_user_service)
            return validated_user_page

        except httpx.HTTPStatusError as exc:
            error_detail = "Error from user service"
            try:
                error_detail = exc.response.json().get("detail", error_detail)
            except Exception:
                pass
            raise HTTPException(
                status_code=exc.response.status_code, 
                detail=f"Error fetching users from User Service: {error_detail}"
            )
        except httpx.ConnectTimeout:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT, 
                detail=f"User Service at {target_url} timed out (connect)."
            )
        except httpx.ReadTimeout:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT, 
                detail=f"User Service at {target_url} timed out (read)."
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail=f"Error connecting to User Service at {target_url}: {exc}"
            )
        except Exception as e: 
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred in Admin Portal or data validation failed: {str(e)}"
            )