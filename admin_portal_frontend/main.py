from fastapi import FastAPI, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone # Đảm bảo datetime được import
import httpx
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr # Thêm EmailStr
import math
import logging # Thêm logging

from config import settings

# Thiết lập logging cơ bản
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_datetime_string(date_str: Optional[str]) -> Optional[datetime]:
    """Parse datetime string from API response to datetime object"""
    if not date_str:
        return None
    try:
        # Try parsing with microseconds first
        if '.' in date_str:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            # If no microseconds, parse without them
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        try:
            # Fallback: try parsing with strptime
            return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%f')
        except ValueError:
            logger.warning(f"Could not parse datetime string: {date_str}")
            return None

def process_ekyc_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process eKYC records to convert datetime strings to datetime objects"""
    processed_records = []
    for record in records:
        processed_record = record.copy()
        
        # Convert datetime fields
        datetime_fields = ['created_at', 'updated_at', 'verified_at']
        for field in datetime_fields:
            if field in processed_record:
                processed_record[field] = parse_datetime_string(processed_record[field])
        
        # Process user datetime fields if user exists
        if 'user' in processed_record and processed_record['user']:
            user = processed_record['user'].copy()
            user['created_at'] = parse_datetime_string(user.get('created_at'))
            processed_record['user'] = user
            
        # Process verifier datetime fields if verifier exists
        if 'verifier' in processed_record and processed_record['verifier']:
            verifier = processed_record['verifier'].copy()
            verifier['created_at'] = parse_datetime_string(verifier.get('created_at'))
            processed_record['verifier'] = verifier
            
        processed_records.append(processed_record)
    
    return processed_records

app = FastAPI(title=settings.APP_TITLE)

templates = Jinja2Templates(directory=settings.TEMPLATES_DIR_CONFIG)
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR_CONFIG), name="static")

class UserForFrontend(BaseModel): 
    id: Optional[int] = None
    username: str
    full_name: Optional[str] = None
    roles: List[str] = []

class UserDetailForTemplate(BaseModel): # Model mới cho dữ liệu người dùng trong template
    id: int
    email: EmailStr 
    username: str
    is_active: bool
    created_at: Optional[datetime] = None
    full_name: Optional[str] = None

    class Config: 
        from_attributes = True


async def get_current_user_from_cookie(request: Request) -> Optional[UserForFrontend]:
    token = request.cookies.get("access_token_admin_portal")
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            return None
        
        return UserForFrontend(
            id=payload.get("user_id"),
            username=username,
            full_name=payload.get("full_name", username),
            roles=payload.get("roles", [])
        )
    except JWTError:
        return None

async def get_current_active_user(
    request: Request, 
    current_user: Optional[UserForFrontend] = Depends(get_current_user_from_cookie)
) -> UserForFrontend:
    if not current_user:
        response = RedirectResponse(url="/login?error=Session expired or invalid", status_code=status.HTTP_303_SEE_OTHER)
        response.delete_cookie("access_token_admin_portal") 
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Not authenticated",
            headers={"Location": "/login"}, 
        )
    return current_user


async def fetch_users_from_backend_via_gateway(
    admin_token: str,
    page: int = 1,
    limit: int = 10
) -> Dict[str, Any]:
    gateway_admin_users_url = f"{settings.API_GATEWAY_URL}/admin/users/"
    headers = {"Authorization": f"Bearer {admin_token}"}
    params = {"page": page, "limit": limit}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(gateway_admin_users_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Chuyển đổi danh sách users thô (list of dicts) thành list of Pydantic models
            users_list_raw = data.get("items", [])
            parsed_users_list: List[UserDetailForTemplate] = []
            if isinstance(users_list_raw, list):
                for user_dict in users_list_raw:
                    try:
                        parsed_users_list.append(UserDetailForTemplate.model_validate(user_dict))
                    except Exception as val_err:
                        logger.error(f"Validation error for user data: {user_dict}, error: {val_err}")
                        # Bỏ qua user này hoặc xử lý lỗi phù hợp

            return {
                "users": parsed_users_list, # Trả về danh sách đã được parse
                "total_users": data.get("total", 0),
                "current_page": data.get("page", 1),
                "limit": data.get("limit", limit),
                "total_pages": data.get("pages", 1),
                "error": None
            }
        except httpx.HTTPStatusError as exc:
            error_detail = "Error from backend service"
            try:
                error_detail = exc.response.json().get("detail", error_detail)
            except Exception:
                pass
            logger.error(f"HTTPStatusError from backend: {error_detail}")
            return {"users": [], "error": error_detail, "total_users": 0, "current_page": page, "limit": limit, "total_pages": 0}
        except Exception as e:
            logger.error(f"Generic error fetching users: {str(e)}")
            return {"users": [], "error": str(e), "total_users": 0, "current_page": page, "limit": limit, "total_pages": 0}


@app.get("/", response_class=HTMLResponse)
async def root(request: Request, current_user: Optional[UserForFrontend] = Depends(get_current_user_from_cookie)):
    if current_user:
        return RedirectResponse(url="/dashboard/users", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/login", response_class=HTMLResponse)
async def login_page_get(request: Request, error: Optional[str] = None):
    return templates.TemplateResponse("login.html", {"request": request, "settings": settings, "error": error})

@app.post("/login", response_class=HTMLResponse)
async def login_page_post(request: Request, username: str = Form(...), password: str = Form(...)):
    login_data = {"username": username, "password": password}
    gateway_token_url = f"{settings.API_GATEWAY_URL}/auth/token"
    
    async with httpx.AsyncClient() as client:
        try:
            api_response = await client.post(gateway_token_url, data=login_data)
            if api_response.status_code == 200:
                token_data = api_response.json()
                access_token = token_data.get("access_token")
                
                if not access_token: # Kiểm tra access_token có tồn tại không
                    logger.error("Access token missing in response from /auth/token")
                    return RedirectResponse(url="/login?error=Authentication failed, no token received.", status_code=status.HTTP_303_SEE_OTHER)

                temp_payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                roles_in_token = temp_payload.get("roles", [])

                if "admin" not in roles_in_token:
                     logger.warning(f"User '{username}' logged in but does not have admin role.")
                     return RedirectResponse(url="/login?error=User is not an admin.", status_code=status.HTTP_303_SEE_OTHER)

                response = RedirectResponse(url="/dashboard/users", status_code=status.HTTP_303_SEE_OTHER)
                expires = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
                response.set_cookie(
                    key="access_token_admin_portal", 
                    value=access_token, 
                    httponly=True, 
                    samesite="Lax",
                    expires=expires
                )
                return response
            else:
                error_detail = "Invalid username or password"
                try:
                    error_detail = api_response.json().get("detail", error_detail)
                except Exception:
                    pass
                logger.warning(f"Login failed for '{username}': {error_detail} (Status: {api_response.status_code})")
                return RedirectResponse(url=f"/login?error={error_detail}", status_code=status.HTTP_303_SEE_OTHER)

        except httpx.RequestError as req_err:
            logger.error(f"Connection error to authentication service: {req_err}")
            return RedirectResponse(url="/login?error=Could not connect to authentication service", status_code=status.HTTP_303_SEE_OTHER)
        except JWTError as jwt_err: 
            logger.error(f"JWT decoding error after login: {jwt_err}")
            return RedirectResponse(url="/login?error=Invalid token structure after login", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token_admin_portal")
    return response

@app.get("/dashboard/users", response_class=HTMLResponse)
async def dashboard_users_page(
    request: Request,
    current_user: UserForFrontend = Depends(get_current_active_user),
    page: int = 1,
    limit: int = 10 
):
    admin_token = request.cookies.get("access_token_admin_portal")
    if not admin_token: # Should be caught by get_current_active_user, but good to double check
         return RedirectResponse(url="/login?error=Session expired", status_code=status.HTTP_303_SEE_OTHER)

    if page < 1: page = 1
    if limit < 1: limit = 10 

    users_data_from_backend = await fetch_users_from_backend_via_gateway(admin_token, page=page, limit=limit)
    
    # users_data_from_backend["users"] giờ đây là một list các đối tượng UserDetailForTemplate
    # Pydantic đã parse chuỗi "created_at" thành đối tượng datetime.
    
    return templates.TemplateResponse(
        "user_list.html",
        {
            "request": request,
            "settings": settings,
            "current_user": current_user,
            "users": users_data_from_backend.get("users", []), 
            "error_message": users_data_from_backend.get("error"),
            "current_page": users_data_from_backend.get("current_page", page),
            "limit": users_data_from_backend.get("limit", limit),
            "total_users": users_data_from_backend.get("total_users", 0),
            "total_pages": users_data_from_backend.get("total_pages", 0)
        }
    )

@app.get("/admin/only", response_class=HTMLResponse) 
async def admin_only_route(request: Request, current_user: UserForFrontend = Depends(get_current_active_user)):
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions (checked on frontend)")
    
    gateway_admin_test_url = f"{settings.API_GATEWAY_URL}/admin/users/?limit=1" 
    admin_token = request.cookies.get("access_token_admin_portal")
    headers = {"Authorization": f"Bearer {admin_token}"}
    backend_message = "Could not verify backend admin access."

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(gateway_admin_test_url, headers=headers)
            if response.status_code == 200:
                backend_message = f"Successfully accessed admin backend. (Status: {response.status_code})"
            else:
                backend_message = f"Backend denied access or error. (Status: {response.status_code}, Detail: {response.text[:100]})"
        except Exception as e:
            backend_message = f"Error connecting to backend: {str(e)}"

    return HTMLResponse(f"""
        <h1>Welcome Admin {current_user.full_name or current_user.username}!</h1>
        <p>This is an admin-only area (frontend check passed).</p>
        <p>Backend access check: {backend_message}</p>
        <a href='/dashboard/users'>Back to Users</a> <br/>
        <form action="/logout" method="post"><button type="submit">Logout</button></form>
    """)

@app.post("/dashboard/users/activate/{user_id}")
async def activate_user(request: Request, user_id: int, current_user: UserForFrontend = Depends(get_current_active_user)):
    admin_token = request.cookies.get("access_token_admin_portal")
    if not admin_token:
        return RedirectResponse(url="/login?error=Session expired", status_code=status.HTTP_303_SEE_OTHER)
    gateway_url = f"{settings.API_GATEWAY_URL}/admin/users/{user_id}/activate"
    headers = {"Authorization": f"Bearer {admin_token}"}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(gateway_url, headers=headers)
            if resp.status_code == 200:
                return RedirectResponse(url="/dashboard/users?msg=activated", status_code=status.HTTP_303_SEE_OTHER)
            else:
                return RedirectResponse(url=f"/dashboard/users?error=Không thể kích hoạt user: {resp.text}", status_code=status.HTTP_303_SEE_OTHER)
        except Exception as e:
            return RedirectResponse(url=f"/dashboard/users?error=Lỗi backend: {str(e)}", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/dashboard/users/deactivate/{user_id}")
async def deactivate_user(request: Request, user_id: int, current_user: UserForFrontend = Depends(get_current_active_user)):
    admin_token = request.cookies.get("access_token_admin_portal")
    if not admin_token:
        return RedirectResponse(url="/login?error=Session expired", status_code=status.HTTP_303_SEE_OTHER)
    gateway_url = f"{settings.API_GATEWAY_URL}/admin/users/{user_id}/deactivate"
    headers = {"Authorization": f"Bearer {admin_token}"}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(gateway_url, headers=headers)
            if resp.status_code == 200:
                return RedirectResponse(url="/dashboard/users?msg=deactivated", status_code=status.HTTP_303_SEE_OTHER)
            else:
                return RedirectResponse(url=f"/dashboard/users?error=Không thể vô hiệu hóa user: {resp.text}", status_code=status.HTTP_303_SEE_OTHER)
        except Exception as e:
            return RedirectResponse(url=f"/dashboard/users?error=Lỗi backend: {str(e)}", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/dashboard/ekyc", response_class=HTMLResponse)
async def dashboard_ekyc_page(
    request: Request,
    current_user: UserForFrontend = Depends(get_current_active_user),
    page: int = 1,
    limit: int = 10,
    status: Optional[str] = None,
    date: Optional[str] = None
):
    admin_token = request.cookies.get("access_token_admin_portal")
    if not admin_token:
        return RedirectResponse(url="/login?error=Session expired", status_code=status.HTTP_303_SEE_OTHER)

    params = {
        "page": page,
        "limit": limit
    }
    if status:
        params["status"] = status
    if date:
        params["date"] = date

    gateway_ekyc_url = f"{settings.API_GATEWAY_URL}/admin/ekyc"
    headers = {"Authorization": f"Bearer {admin_token}"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(gateway_ekyc_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            # Process the records to convert datetime strings to datetime objects
            processed_records = process_ekyc_records(data.get("items", []))

            return templates.TemplateResponse(
                "ekyc_list.html",
                {
                    "request": request,
                    "settings": settings,
                    "current_user": current_user,
                    "records": processed_records,
                    "total_records": data.get("total", 0),
                    "current_page": data.get("page", page),
                    "limit": data.get("limit", limit),
                    "total_pages": data.get("pages", 1),
                    "error_message": None
                }
            )
        except Exception as e:
            logger.error(f"Error fetching eKYC records: {str(e)}")
            return templates.TemplateResponse(
                "ekyc_list.html",
                {
                    "request": request,
                    "settings": settings,
                    "current_user": current_user,
                    "records": [],
                    "total_records": 0,
                    "current_page": 1,
                    "limit": limit,
                    "total_pages": 0,
                    "error_message": f"Không thể tải danh sách eKYC: {str(e)}"
                }
            )

@app.get("/dashboard/ekyc/{record_id}", response_class=HTMLResponse)
async def dashboard_ekyc_detail_page(
    record_id: int,
    request: Request,
    current_user: UserForFrontend = Depends(get_current_active_user)
):
    admin_token = request.cookies.get("access_token_admin_portal")
    if not admin_token:
        return RedirectResponse(url="/login?error=Session expired", status_code=status.HTTP_303_SEE_OTHER)

    gateway_ekyc_detail_url = f"{settings.API_GATEWAY_URL}/admin/ekyc/{record_id}"
    headers = {"Authorization": f"Bearer {admin_token}"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(gateway_ekyc_detail_url, headers=headers)
            response.raise_for_status()
            record = response.json()

            # Process the single record to convert datetime strings to datetime objects
            processed_records = process_ekyc_records([record])
            processed_record = processed_records[0] if processed_records else record

            return templates.TemplateResponse(
                "ekyc_detail.html",
                {
                    "request": request,
                    "settings": settings,
                    "current_user": current_user,
                    "record": processed_record,
                    "error_message": None
                }
            )
        except Exception as e:
            logger.error(f"Error fetching eKYC record detail: {str(e)}")
            return templates.TemplateResponse(
                "ekyc_detail.html",
                {
                    "request": request,
                    "settings": settings,
                    "current_user": current_user,
                    "record": None,
                    "error_message": f"Không thể tải thông tin eKYC: {str(e)}"
                }
            )

@app.get("/dashboard/statistics", response_class=HTMLResponse)
async def dashboard_statistics_page(request: Request, current_user: UserForFrontend = Depends(get_current_active_user)):
    admin_token = request.cookies.get("access_token_admin_portal")
    if not admin_token:
        return RedirectResponse(url="/login?error=Session expired", status_code=status.HTTP_303_SEE_OTHER)
    gateway_stats_url = f"{settings.API_GATEWAY_URL}/admin/statistics"
    headers = {"Authorization": f"Bearer {admin_token}"}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(gateway_stats_url, headers=headers)
            resp.raise_for_status()
            stats = resp.json()
            return templates.TemplateResponse("statistics.html", {"request": request, "settings": settings, "current_user": current_user, "stats": stats})
        except Exception as e:
            logger.error(f"Error fetching statistics: {str(e)}")
            return templates.TemplateResponse("statistics.html", {"request": request, "settings": settings, "current_user": current_user, "stats": {"total_users": 0, "total_ekyc": 0, "face_match_rate": 0, "chart_labels": [], "chart_data": []}})

@app.get("/dashboard/notifications", response_class=HTMLResponse)
async def dashboard_notifications_page(request: Request, current_user: UserForFrontend = Depends(get_current_active_user)):
    admin_token = request.cookies.get("access_token_admin_portal")
    if not admin_token:
        return RedirectResponse(url="/login?error=Session expired", status_code=status.HTTP_303_SEE_OTHER)
    gateway_notify_url = f"{settings.API_GATEWAY_URL}/admin/notifications"
    headers = {"Authorization": f"Bearer {admin_token}"}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(gateway_notify_url, headers=headers)
            resp.raise_for_status()
            notifications = resp.json().get("items", [])
            return templates.TemplateResponse("notifications.html", {"request": request, "settings": settings, "current_user": current_user, "notifications": notifications})
        except Exception as e:
            logger.error(f"Error fetching notifications: {str(e)}")
            return templates.TemplateResponse("notifications.html", {"request": request, "settings": settings, "current_user": current_user, "notifications": []})

@app.get("/dashboard/docs", response_class=HTMLResponse)
async def dashboard_docs_page(request: Request, current_user: UserForFrontend = Depends(get_current_active_user)):
    return templates.TemplateResponse("docs.html", {"request": request, "settings": settings, "current_user": current_user})

@app.post("/dashboard/ekyc/{record_id}/verify", response_class=RedirectResponse)
async def verify_ekyc_record(
    record_id: int,
    request: Request,
    verification_status: str = Form(...),
    verification_note: Optional[str] = Form(None),
    current_user: UserForFrontend = Depends(get_current_active_user)
):
    admin_token = request.cookies.get("access_token_admin_portal")
    if not admin_token:
        return RedirectResponse(url="/login?error=Session expired", status_code=status.HTTP_303_SEE_OTHER)

    gateway_verify_url = f"{settings.API_GATEWAY_URL}/admin/ekyc/{record_id}/verify"
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            verify_data = {
                "verification_status": verification_status,
                "verification_note": verification_note
            }
            response = await client.post(gateway_verify_url, json=verify_data, headers=headers)
            response.raise_for_status()
            
            # Redirect back to the eKYC detail page with a success message
            return RedirectResponse(
                url=f"/dashboard/ekyc/{record_id}?message=Verification successful", 
                status_code=status.HTTP_303_SEE_OTHER
            )
        except Exception as e:
            logger.error(f"Error verifying eKYC record: {str(e)}")
            # Redirect back to the eKYC detail page with an error message
            return RedirectResponse(
                url=f"/dashboard/ekyc/{record_id}?error=Verification failed: {str(e)}", 
                status_code=status.HTTP_303_SEE_OTHER
            )