from fastapi import FastAPI, HTTPException, status, Depends, Request
from fastapi.responses import JSONResponse
import httpx
from typing import List, Optional, Any
from pydantic import BaseModel

from .config import settings

app = FastAPI(title="Admin Portal Backend Service")

DEFAULT_TIMEOUT = 10.0

class User(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool

    class Config:
        from_attributes = True


async def get_admin_user(request: Request):
    pass


@app.get("/admin/users/", response_model=List[User], tags=["Admin - Users"])
async def get_all_users_from_user_service(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    admin_user: Any = Depends(get_admin_user)
):
    target_url = f"{settings.USER_SERVICE_URL}/users/"
    params = {"skip": skip, "limit": limit}
    
    client_headers = {
        key: value for key, value in request.headers.items()
        if key.lower() not in ["host", "connection", "content-length", "transfer-encoding", "user-agent", "accept", "accept-encoding"]
    }

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            response = await client.get(target_url, params=params, headers=client_headers)
            response.raise_for_status()
            
            users_data = response.json()
            
            return users_data

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
                detail=f"An unexpected error occurred in Admin Portal: {str(e)}"
            )
