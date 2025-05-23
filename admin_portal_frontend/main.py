# admin_portal_frontend/main.py
from fastapi import FastAPI, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles # For serving static files if needed
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import httpx # For making API calls to backend
from typing import Optional, List, Dict, Any

# Import settings from config.py
from config import settings

# --- App Initialization ---
app = FastAPI(title=settings.APP_TITLE)

# --- Templates ---
templates = Jinja2Templates(directory="templates")
# If you have static files (CSS, JS, images) in a 'static' folder:
# app.mount("/static", StaticFiles(directory="static"), name="static")


# --- Security and Authentication (Simplified for example) ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Mock user database (In a real app, this would come from your user service/database)
# Store hashed passwords
FAKE_USERS_DB = {
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "email": "admin@example.com",
        "hashed_password": pwd_context.hash("adminpass"), # Password is "adminpass"
        "disabled": False,
        "roles": ["admin"]
    },
    "user1": {
        "username": "user1",
        "full_name": "Regular User",
        "email": "user1@example.com",
        "hashed_password": pwd_context.hash("user1pass"), # Password is "user1pass"
        "disabled": False,
        "roles": ["user"]
    }
}

# --- Helper Functions for Auth (Simplified) ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user(username: str) -> Optional[Dict[str, Any]]:
    if username in FAKE_USERS_DB:
        user_dict = FAKE_USERS_DB[username]
        return user_dict
    return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user_from_cookie(request: Request) -> Optional[Dict[str, Any]]:
    token = request.cookies.get("access_token")
    if not token:
        print("No access_token cookie found")
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            print("Token payload does not contain username (sub)")
            return None
        user = get_user(username) # Fetch user details from your DB/source
        if user is None:
            print(f"User {username} not found in FAKE_USERS_DB")
            return None
        # You can add more checks here, e.g., token expiry from payload if not handled by jwt.decode
        return user
    except JWTError as e:
        print(f"JWTError decoding token: {e}")
        return None

async def get_current_active_user(
    request: Request, # Add request here to get cookies
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_from_cookie)
) -> Dict[str, Any]:
    if not current_user:
        # If no current_user, redirect to login
        response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        # Clear any potentially invalid cookie
        response.delete_cookie("access_token")
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Not authenticated",
            headers={"Location": "/login"}, # Ensure browser redirects
        )
    if current_user.get("disabled"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


# --- Mock Backend API Calls ---
async def fetch_users_from_backend(token_unused: str, skip: int = 0, limit: int = 10) -> Dict[str, Any]:
    # In a real app, you'd use the 'token_unused' (which would be the actual token)
    # to authenticate with the backend.
    print(f"MOCKING: Fetching users from backend. Skip: {skip}, Limit: {limit}")

    # Simulating a list of users that might come from a database or another service
    all_mock_users_list = [
        {"id": "user1-backend", "username": "john.doe", "email": "john@example.com", "full_name": "John Doe (Backend)", "is_active": True, "created_at": "2024-01-01T10:00:00Z"},
        {"id": "user2-backend", "username": "jane.smith", "email": "jane@example.com", "full_name": "Jane Smith (Backend)", "is_active": False, "created_at": "2024-01-02T11:00:00Z"},
        {"id": "user3-backend", "username": "alice.wonder", "email": "alice@example.com", "full_name": "Alice Wonder (Backend)", "is_active": True, "created_at": "2024-01-03T12:00:00Z"},
        {"id": "user4-backend", "username": "bob.builder", "email": "bob@example.com", "full_name": "Bob Builder (Backend)", "is_active": True, "created_at": "2024-01-04T13:00:00Z"},
    ]
    
    total_mock_users = len(all_mock_users_list)
    paginated_users = all_mock_users_list[skip : skip + limit]
    
    total_pages = (total_mock_users + limit - 1) // limit if limit > 0 else 1
    current_page = skip // limit + 1 if limit > 0 else 1

    return {
        "users": paginated_users,
        "total_users": total_mock_users,
        "page": current_page,
        "limit": limit,
        "total_pages": total_pages
    }

# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def root(request: Request, current_user: Optional[Dict[str, Any]] = Depends(get_current_user_from_cookie)):
    if current_user:
        return RedirectResponse(url="/dashboard/users", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/login", response_class=HTMLResponse)
async def login_page_get(request: Request, error: Optional[str] = None):
    print(f"GET /login - Serving login page. Error: {error}")
    return templates.TemplateResponse("login.html", {"request": request, "settings": settings, "error": error})

@app.post("/login", response_class=HTMLResponse)
async def login_page_post(request: Request, username: str = Form(...), password: str = Form(...)):
    print(f"POST /login - Attempting login for user: {username}")
    user = get_user(username)
    if not user or not verify_password(password, user["hashed_password"]) or user.get("disabled"):
        print(f"Login failed for user: {username}")
        # It's better to redirect to GET /login with an error query parameter
        # to avoid form resubmission issues and to keep the URL clean.
        return RedirectResponse(url="/login?error=Invalid username or password", status_code=status.HTTP_303_SEE_OTHER)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "roles": user.get("roles", [])}, expires_delta=access_token_expires
    )
    
    response = RedirectResponse(url="/dashboard/users", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=int(access_token_expires.total_seconds()), samesite="Lax")
    print(f"Login successful for user: {username}. Redirecting to dashboard.")
    return response

@app.post("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    print("User logged out. Redirecting to login.")
    return response

@app.get("/dashboard/users", response_class=HTMLResponse)
async def dashboard_users_page(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_active_user), # Ensures user is logged in
    skip: int = 0,
    limit: int = 10 # Default items per page
):
    print(f"GET /dashboard/users - User: {current_user['username']}, Skip: {skip}, Limit: {limit}")
    # The token for backend calls would typically be the one stored in the cookie,
    # or a new one generated for service-to-service communication.
    # For this example, we'll pass the username as a placeholder for 'token'.
    token_for_backend = current_user['username'] # Placeholder
    
    users_data = await fetch_users_from_backend(token_for_backend, skip=skip, limit=limit)
    
    print(f"Fetched users data: {users_data['total_users']} total users.")
    return templates.TemplateResponse(
        "user_list.html",
        {
            "request": request,
            "settings": settings,
            "current_user": current_user,
            "users": users_data.get("users", []),
            "total_users": users_data.get("total_users", 0),
            "current_page": users_data.get("page", 1),
            "limit": users_data.get("limit", 10),
            "total_pages": users_data.get("total_pages", 1)
        }
    )

# Example of a protected route that requires admin role
@app.get("/admin/only", response_class=HTMLResponse)
async def admin_only_route(request: Request, current_user: Dict[str, Any] = Depends(get_current_active_user)):
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return HTMLResponse(f"<h1>Welcome Admin {current_user['username']}!</h1><p>This is an admin-only area.</p><a href='/dashboard/users'>Back to Users</a>")


if __name__ == "__main__":
    import uvicorn
    # This is for local development running this file directly.
    # In production, you'd use a command like: uvicorn main:app --host 0.0.0.0 --port 8080
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
