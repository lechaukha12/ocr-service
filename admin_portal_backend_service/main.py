from fastapi import FastAPI, HTTPException, status, Depends, Request, Path
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
import httpx
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, EmailStr 
from datetime import datetime, date
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

class EkycRecord(BaseModel):
    id: int
    user_id: int
    id_number: Optional[str] = None
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    place_of_origin: Optional[str] = None
    place_of_residence: Optional[str] = None
    expiry_date: Optional[str] = None
    selfie_image_url: Optional[str] = None
    id_card_image_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user: User

class EkycRecordPage(BaseModel):
    items: List[EkycRecord]
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

@app.post("/admin/users/{user_id}/activate", tags=["Admin - Users"])
async def activate_user(
    request: Request,
    user_id: int,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    target_url = f"{backend_settings.USER_SERVICE_URL}/users/{user_id}/activate"
    client_headers = {
        "Authorization": request.headers.get("Authorization")
    }
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            response = await client.post(target_url, headers=client_headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Error activating user: {exc.response.text}"
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Error connecting to User Service: {exc}"
            )

@app.post("/admin/users/{user_id}/deactivate", tags=["Admin - Users"])
async def deactivate_user(
    request: Request,
    user_id: int,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    target_url = f"{backend_settings.USER_SERVICE_URL}/users/{user_id}/deactivate"
    client_headers = {
        "Authorization": request.headers.get("Authorization")
    }
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            response = await client.post(target_url, headers=client_headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Error deactivating user: {exc.response.text}"
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Error connecting to User Service: {exc}"
            )

@app.get("/admin/ekyc", response_model=EkycRecordPage, tags=["Admin - eKYC"])
async def get_ekyc_records(
    request: Request,
    page: int = 1,
    limit: int = 10,
    status: Optional[str] = None,
    date: Optional[date] = None,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    if page < 1: page = 1
    if limit < 1: limit = 1
    skip = (page - 1) * limit
    
    target_url = f"{backend_settings.USER_SERVICE_URL}/ekyc/all"
    params = {"skip": skip, "limit": limit}
    if status:
        params["status"] = status
    if date:
        params["date"] = date.isoformat()

    client_headers = {
        "Authorization": request.headers.get("Authorization")
    }

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            response = await client.get(target_url, params=params, headers=client_headers)
            response.raise_for_status()
            ekyc_page_data = response.json()
            validated_page = EkycRecordPage.model_validate(ekyc_page_data)
            return validated_page
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Error fetching eKYC records: {exc.response.text}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error: {str(e)}"
            )

@app.get("/admin/ekyc/{record_id}", response_model=EkycRecord, tags=["Admin - eKYC"])
async def get_ekyc_record_detail(
    request: Request,
    record_id: int,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    target_url = f"{backend_settings.USER_SERVICE_URL}/ekyc/{record_id}"
    client_headers = {
        "Authorization": request.headers.get("Authorization")
    }

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            response = await client.get(target_url, headers=client_headers)
            response.raise_for_status()
            record_data = response.json()
            validated_record = EkycRecord.model_validate(record_data)
            return validated_record
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Error fetching eKYC record: {exc.response.text}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error: {str(e)}"
            )

from datetime import datetime

@app.get("/admin/statistics", tags=["Admin - Statistics"])
async def admin_statistics(current_admin: Dict[str, Any] = Depends(get_current_admin_user)):
    # Demo: Lấy tổng số user, tổng số eKYC, tỉ lệ match khuôn mặt (giả lập)
    # Thực tế sẽ query DB hoặc gọi service
    return {
        "total_users": 123,
        "total_ekyc": 456,
        "face_match_rate": 87,
        "chart_labels": ["01/06", "02/06", "03/06", "04/06"],
        "chart_data": [10, 20, 30, 40]
    }

@app.get("/admin/notifications", tags=["Admin - Notifications"])
async def admin_notifications(current_admin: Dict[str, Any] = Depends(get_current_admin_user)):
    # Demo: Trả về danh sách thông báo mẫu
    return {
        "items": [
            {"title": "Hệ thống cập nhật", "content": "Đã cập nhật tính năng thống kê.", "created_at": datetime.now()},
            {"title": "Thông báo bảo trì", "content": "Hệ thống sẽ bảo trì lúc 23:00 hôm nay.", "created_at": datetime.now()}
        ]
    }