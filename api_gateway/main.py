from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
import asyncio # Cần thiết cho timeout

from .config import settings

app = FastAPI(title="API Gateway")

# Thời gian timeout mặc định cho các request đến microservices
DEFAULT_TIMEOUT = 5.0 # 5 giây

async def forward_request(
    request: Request,
    target_url: str,
    method: str,
    params: dict = None,
    json_data: dict = None,
    form_data: dict = None,
    headers_to_forward: dict = None,
):
    """
    Hàm chung để chuyển tiếp request đến một service khác.
    """
    client_headers = {
        key: value for key, value in request.headers.items()
        if key.lower() not in ["host", "connection", "content-length", "transfer-encoding"]
    }
    if headers_to_forward:
        client_headers.update(headers_to_forward)

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            if method.upper() == "GET":
                response = await client.get(target_url, params=params, headers=client_headers)
            elif method.upper() == "POST":
                if json_data:
                    response = await client.post(target_url, json=json_data, params=params, headers=client_headers)
                elif form_data:
                    response = await client.post(target_url, data=form_data, params=params, headers=client_headers)
                else: # Nếu không có body, ví dụ POST không có body
                    response = await client.post(target_url, params=params, headers=client_headers)
            elif method.upper() == "PUT":
                response = await client.put(target_url, json=json_data, params=params, headers=client_headers)
            elif method.upper() == "DELETE":
                response = await client.delete(target_url, params=params, headers=client_headers)
            else:
                raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Method not allowed by gateway")

            # Xử lý response từ microservice
            response_content = response.content
            response_status_code = response.status_code
            response_headers = dict(response.headers)
            
            # Loại bỏ các header không nên chuyển tiếp lại cho client
            headers_to_exclude = ["content-encoding", "transfer-encoding", "connection"]
            for h in headers_to_exclude:
                if h in response_headers:
                    del response_headers[h]

            if "application/json" in response.headers.get("content-type", ""):
                return JSONResponse(
                    content=response.json(),
                    status_code=response_status_code,
                    headers=response_headers
                )
            else:
                # Đối với các loại content khác, stream response
                return StreamingResponse(
                    content=response.iter_bytes(),
                    status_code=response_status_code,
                    media_type=response.headers.get("content-type"),
                    headers=response_headers
                )

        except httpx.ConnectTimeout:
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=f"Service at {target_url} timed out (connect).")
        except httpx.ReadTimeout:
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=f"Service at {target_url} timed out (read).")
        except httpx.RequestError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Error connecting to service at {target_url}: {exc}")


# --- User Service Routes ---

@app.post("/auth/users/", tags=["Authentication & Users"])
async def register_user(request: Request):
    json_data = await request.json()
    target_url = f"{settings.USER_SERVICE_URL}/users/"
    return await forward_request(request, target_url, "POST", json_data=json_data)

@app.post("/auth/token", tags=["Authentication & Users"])
async def login_for_token(request: Request):
    # Endpoint /token của user_service mong đợi form data (OAuth2PasswordRequestForm)
    form_data = await request.form()
    target_url = f"{settings.USER_SERVICE_URL}/token"
    # Chuyển đổi form_data thành dict để httpx có thể gửi
    form_data_dict = {key: value for key, value in form_data.items()}
    return await forward_request(request, target_url, "POST", form_data=form_data_dict)

@app.get("/users/me/", tags=["Authentication & Users"])
async def get_current_user_details(request: Request):
    target_url = f"{settings.USER_SERVICE_URL}/users/me/"
    # Cần lấy token từ header "Authorization" của request gốc và chuyển tiếp nó
    auth_header = request.headers.get("Authorization")
    headers_to_fwd = {}
    if auth_header:
        headers_to_fwd["Authorization"] = auth_header
    return await forward_request(request, target_url, "GET", headers_to_forward=headers_to_fwd)

# Thêm các route khác cho các service khác ở đây khi chúng được phát triển

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)