from fastapi import FastAPI, HTTPException, status, Depends, Request
from fastapi.responses import JSONResponse
import httpx
from typing import List, Optional, Any
from pydantic import BaseModel

# Sửa import tương đối thành tuyệt đối
from config import settings # Thay vì from .config import settings

app = FastAPI(title="Admin Portal Backend Service")

DEFAULT_TIMEOUT = 10.0

class User(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool

    class Config:
        from_attributes = True # Đổi orm_mode thành from_attributes cho Pydantic v2


async def get_admin_user(request: Request):
    # TODO: Implement proper admin user authentication/authorization
    # For now, this is a placeholder and allows any request to proceed.
    # In a real application, you would verify an admin token or session.
    print("Placeholder get_admin_user called. Implement actual admin auth.")
    pass # Returns None, effectively not blocking


@app.get("/admin/users/", response_model=List[User], tags=["Admin - Users"])
async def get_all_users_from_user_service(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    admin_user: Any = Depends(get_admin_user) # This dependency currently does not restrict access
):
    target_url = f"{settings.USER_SERVICE_URL}/users/"
    params = {"skip": skip, "limit": limit}
    
    # Forward only necessary headers, or specific admin auth headers if implemented
    client_headers = {
        key: value for key, value in request.headers.items()
        if key.lower() in ["authorization", "x-admin-token"] # Example: forward auth or custom admin token
    }
    # If no specific admin auth is implemented yet, you might not need to forward any special headers
    # or User Service's /users/ endpoint might need its own protection.

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            # User Service's /users/ endpoint might be protected, ensure it allows access
            # or this service (admin-portal-backend) needs a privileged way to call it.
            response = await client.get(target_url, params=params, headers=client_headers)
            response.raise_for_status() # Raise an exception for 4XX/5XX responses
            
            users_data = response.json()
            
            # Ensure the data matches the User Pydantic model
            # This list comprehension will try to parse each item
            # Pydantic will raise validation errors if the data doesn't match
            return [User.model_validate(user_item) for user_item in users_data]


        except httpx.HTTPStatusError as exc:
            error_detail = "Error from user service"
            try:
                # Try to parse error detail from the upstream service
                error_detail = exc.response.json().get("detail", error_detail)
            except Exception:
                pass # Keep default error_detail if parsing fails
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
        except Exception as e: # Catch any other unexpected errors
            # Log the full error for debugging
            # print(f"Unexpected error in Admin Portal Backend: {type(e).__name__} - {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred in Admin Portal: {str(e)}"
            )
