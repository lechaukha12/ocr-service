from fastapi import FastAPI, Request, HTTPException, status, Response
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
import asyncio # Cần thiết cho timeout

# Đảm bảo rằng bạn import settings từ local config của api_gateway
from .config import settings

app = FastAPI(title="API Gateway")

# Thời gian timeout mặc định cho các request đến microservices
DEFAULT_TIMEOUT = 10.0 # Tăng lên 10 giây

async def forward_request(
    request: Request,
    target_url: str,
    method: str,
    params: dict = None,
    json_data: dict = None,
    form_data: dict = None,
    data_bytes: bytes = None, # Thêm data_bytes để forward raw body
    headers_to_forward: dict = None,
):
    """
    Hàm chung để chuyển tiếp request đến một service khác.
    """
    client_headers = {
        key: value for key, value in request.headers.items()
        if key.lower() not in ["host", "connection", "content-length", "transfer-encoding", "expect", "user-agent"]
    }
    # Giữ lại User-Agent nếu muốn, hoặc bỏ đi để service backend không biết chi tiết client gốc
    # client_headers["user-agent"] = request.headers.get("user-agent", "API-Gateway-Forwarder")


    if headers_to_forward:
        client_headers.update(headers_to_forward)

    # In ra để debug
    # print(f"Forwarding {method} to {target_url}")
    # print(f"  Params: {params}")
    # print(f"  JSON Data: {json_data}")
    # print(f"  Form Data: {form_data}")
    # print(f"  Byte Data Length: {len(data_bytes) if data_bytes else 0}")
    # print(f"  Headers: {client_headers}")


    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            if method.upper() == "GET":
                response = await client.get(target_url, params=params, headers=client_headers)
            elif method.upper() == "POST":
                if json_data:
                    response = await client.post(target_url, json=json_data, params=params, headers=client_headers)
                elif form_data: # FastAPI request.form() trả về một đối tượng FormData, cần chuyển thành dict
                    response = await client.post(target_url, data=form_data, params=params, headers=client_headers)
                elif data_bytes: # Dùng cho forward raw body như file uploads
                    response = await client.post(target_url, content=data_bytes, params=params, headers=client_headers)
                else: # Nếu không có body, ví dụ POST không có body
                    response = await client.post(target_url, params=params, headers=client_headers)
            elif method.upper() == "PUT": # Giả sử PUT dùng JSON
                response = await client.put(target_url, json=json_data, params=params, headers=client_headers)
            elif method.upper() == "DELETE":
                response = await client.delete(target_url, params=params, headers=client_headers)
            else:
                raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Method not allowed by gateway")

            # Xử lý response từ microservice
            response_content = response.content # Đọc content trước khi response đóng
            response_status_code = response.status_code
            response_headers = dict(response.headers)
            
            # Loại bỏ các header không nên chuyển tiếp lại cho client (tùy chỉnh nếu cần)
            headers_to_exclude = ["content-encoding", "transfer-encoding", "connection", "server", "date"]
            for h in headers_to_exclude:
                if h in response_headers:
                    del response_headers[h]
            
            # print(f"Response from service: Status {response_status_code}")
            # print(f"Response headers from service: {response_headers}")

            # Trả về Response object của FastAPI/Starlette để giữ nguyên headers và content
            return Response(
                content=response_content,
                status_code=response_status_code,
                headers=response_headers
            )

        except httpx.ConnectTimeout:
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=f"Service at {target_url} timed out (connect).")
        except httpx.ReadTimeout:
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=f"Service at {target_url} timed out (read).")
        except httpx.RequestError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Error connecting to service at {target_url}: {exc}")


# --- User Service Routes ---

@app.post("/auth/users/", tags=["User Service"])
async def register_user(request: Request):
    json_data = await request.json()
    target_url = f"{settings.USER_SERVICE_URL}/users/" #
    return await forward_request(request, target_url, "POST", json_data=json_data)

@app.post("/auth/token", tags=["User Service"])
async def login_for_token(request: Request):
    form_data = await request.form()
    target_url = f"{settings.USER_SERVICE_URL}/token" #
    # Chuyển đổi form_data (Starlette FormData) thành dict để httpx có thể gửi
    form_data_dict = {key: value for key, value in form_data.items()}
    return await forward_request(request, target_url, "POST", form_data=form_data_dict)

@app.get("/users/me/", tags=["User Service"])
async def get_current_user_details(request: Request):
    target_url = f"{settings.USER_SERVICE_URL}/users/me/" #
    auth_header = request.headers.get("Authorization")
    headers_to_fwd = {}
    if auth_header:
        headers_to_fwd["Authorization"] = auth_header
    return await forward_request(request, target_url, "GET", headers_to_forward=headers_to_fwd)

# --- Storage Service Routes ---
# Bạn cần đảm bảo STORAGE_SERVICE_URL được định nghĩa trong api_gateway/config.py

@app.post("/storage/upload/file/", tags=["Storage Service"])
async def proxy_upload_file_storage(request: Request):
    content_type = request.headers.get("content-type")
    # Không kiểm tra content_type ở đây, để storage service tự quyết định
    # if not content_type or "multipart/form-data" not in content_type:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File upload must be multipart/form-data")

    body_bytes = await request.body()
    
    # Giữ lại content-type gốc từ client request
    headers_to_fwd = {"content-type": content_type} if content_type else {}

    target_url = f"{settings.STORAGE_SERVICE_URL}/upload/file/" #
    return await forward_request(
        request,
        target_url,
        "POST",
        data_bytes=body_bytes,
        headers_to_forward=headers_to_fwd
    )

@app.get("/storage/files/{filename}", tags=["Storage Service"])
async def proxy_get_file_storage(filename: str, request: Request):
    target_url = f"{settings.STORAGE_SERVICE_URL}/files/{filename}" #
    # forward_request sẽ xử lý việc trả về file response
    # Cần đảm bảo forward_request trả về Response object để giữ đúng media_type, headers
    return await forward_request(request, target_url, "GET")


# --- Admin Portal Backend Service Routes ---
# Bạn cần đảm bảo ADMIN_PORTAL_BACKEND_SERVICE_URL được định nghĩa trong api_gateway/config.py

@app.get("/admin/users/", tags=["Admin Portal Backend Service"])
async def proxy_admin_get_users(request: Request, skip: int = 0, limit: int = 100):
    # Endpoint này của Admin Portal Backend Service là /admin/users/
    target_url = f"{settings.ADMIN_PORTAL_BACKEND_SERVICE_URL}/admin/users/"
    params = {"skip": skip, "limit": limit}
    
    # Giả sử endpoint này cần xác thực admin, bạn cần cơ chế để gateway lấy/forward token admin
    # Ví dụ: lấy từ một header đặc biệt hoặc một cookie mà admin portal frontend đặt
    auth_header = request.headers.get("Authorization") # Hoặc một header/cookie khác dành cho admin
    headers_to_fwd = {}
    if auth_header:
        headers_to_fwd["Authorization"] = auth_header
        
    return await forward_request(request, target_url, "GET", params=params, headers_to_forward=headers_to_fwd)

# Thêm các route khác cho các service khác ở đây khi chúng được phát triển

# if __name__ == "__main__":
#     import uvicorn
#     # Chạy trực tiếp file này chỉ dùng cho mục đích debug local, không phải cách chạy trong Docker
#     # Trong Docker, bạn sẽ dùng lệnh như: uvicorn api_gateway.main:app --host 0.0.0.0 --port 8000
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)