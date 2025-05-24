from fastapi import FastAPI, Request, HTTPException, status, Response, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
import asyncio 
from typing import List, Optional

from config import settings

app = FastAPI(title="API Gateway")

DEFAULT_TIMEOUT = 60.0

async def forward_request(
    request: Request,
    target_url: str,
    method: str,
    params: dict = None,
    json_data: dict = None,
    form_data: dict = None,
    data_bytes: bytes = None,
    files_data: Optional[List[tuple]] = None, 
    headers_to_forward: dict = None,
):
    client_headers = {
        key: value for key, value in request.headers.items()
        if key.lower() not in ["host", "connection", "content-length", "transfer-encoding", "expect", "user-agent", "content-type"]
    }

    if headers_to_forward:
        client_headers.update(headers_to_forward)

    if not files_data and request.headers.get("content-type") and not form_data: 
        client_headers["content-type"] = request.headers.get("content-type")
    elif form_data and not files_data : 
        pass
    elif json_data:
         client_headers["content-type"] = "application/json"


    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            if method.upper() == "GET":
                response = await client.get(target_url, params=params, headers=client_headers)
            elif method.upper() == "POST":
                if files_data: 
                    response = await client.post(target_url, files=files_data, data=form_data, params=params, headers=client_headers)
                elif json_data:
                    response = await client.post(target_url, json=json_data, params=params, headers=client_headers)
                elif form_data: 
                    response = await client.post(target_url, data=form_data, params=params, headers=client_headers)
                elif data_bytes:
                    response = await client.post(target_url, content=data_bytes, params=params, headers=client_headers)
                else:
                    content_body = await request.body() 
                    response = await client.post(target_url, content=content_body, params=params, headers=client_headers)
            elif method.upper() == "PUT":
                if json_data: 
                    response = await client.put(target_url, json=json_data, params=params, headers=client_headers)
                elif data_bytes: 
                     response = await client.put(target_url, content=data_bytes, params=params, headers=client_headers)
                else:
                    content_body = await request.body()
                    response = await client.put(target_url, content=content_body, params=params, headers=client_headers)
            elif method.upper() == "DELETE":
                response = await client.delete(target_url, params=params, headers=client_headers)
            else:
                raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Method not allowed by gateway")

            response_content = response.content
            response_status_code = response.status_code
            response_headers = dict(response.headers)
            
            headers_to_exclude = ["content-encoding", "transfer-encoding", "connection", "server", "date"]
            for h in headers_to_exclude:
                if h in response_headers:
                    del response_headers[h]
            
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

@app.post("/auth/users/", tags=["User Service"])
async def register_user(request: Request):
    json_data = await request.json()
    target_url = f"{settings.USER_SERVICE_URL}/users/"
    return await forward_request(request, target_url, "POST", json_data=json_data)

@app.post("/auth/token", tags=["User Service"])
async def login_for_token(request: Request):
    form_data = await request.form()
    target_url = f"{settings.USER_SERVICE_URL}/token"
    form_data_dict = {key: value for key, value in form_data.items()}
    return await forward_request(request, target_url, "POST", form_data=form_data_dict)

@app.get("/users/me/", tags=["User Service"])
async def get_current_user_details(request: Request):
    target_url = f"{settings.USER_SERVICE_URL}/users/me/"
    auth_header = request.headers.get("Authorization")
    headers_to_fwd = {}
    if auth_header:
        headers_to_fwd["Authorization"] = auth_header
    return await forward_request(request, target_url, "GET", headers_to_forward=headers_to_fwd)

@app.post("/storage/upload/file/", tags=["Storage Service"])
async def proxy_upload_file_storage(request: Request):
    body_bytes = await request.body()
    content_type = request.headers.get("content-type") 
    headers_to_fwd = {"content-type": content_type} if content_type else {}
    auth_header = request.headers.get("Authorization")
    if auth_header:
        headers_to_fwd["Authorization"] = auth_header

    target_url = f"{settings.STORAGE_SERVICE_URL}/upload/file/"
    return await forward_request(
        request,
        target_url,
        "POST",
        data_bytes=body_bytes,
        headers_to_forward=headers_to_fwd
    )

@app.get("/storage/files/{filename}", tags=["Storage Service"])
async def proxy_get_file_storage(filename: str, request: Request):
    target_url = f"{settings.STORAGE_SERVICE_URL}/files/{filename}"
    auth_header = request.headers.get("Authorization")
    headers_to_fwd = {}
    if auth_header:
        headers_to_fwd["Authorization"] = auth_header
    return await forward_request(request, target_url, "GET", headers_to_forward=headers_to_fwd)


@app.get("/admin/users/", tags=["Admin Portal Backend Service"])
async def proxy_admin_get_users(request: Request, page: int = 1, limit: int = 10):
    target_url = f"{settings.ADMIN_PORTAL_BACKEND_SERVICE_URL}/admin/users/"
    params = {"page": page, "limit": limit}
    
    auth_header = request.headers.get("Authorization") 
    headers_to_fwd = {}
    if auth_header:
        headers_to_fwd["Authorization"] = auth_header
        
    return await forward_request(request, target_url, "GET", params=params, headers_to_forward=headers_to_fwd)

@app.post("/ocr/image/", tags=["OCR Service"])
async def proxy_ocr_image(
    request: Request,
    file: UploadFile = File(...),
    lang: Optional[str] = Form(None),
    psm: Optional[str] = Form(None) 
):
    target_url = f"{settings.GENERIC_OCR_SERVICE_URL}/ocr/image/"
    file_content = await file.read()
    files_for_httpx = [("file", (file.filename, file_content, file.content_type))]
    
    data_for_httpx = {}
    if lang:
        data_for_httpx["lang"] = lang
    if psm: 
        data_for_httpx["psm"] = psm
    
    auth_header = request.headers.get("Authorization")
    headers_to_fwd = {}
    if auth_header:
        headers_to_fwd["Authorization"] = auth_header

    return await forward_request(
        request,
        target_url,
        "POST",
        form_data=data_for_httpx, 
        files_data=files_for_httpx, 
        headers_to_forward=headers_to_fwd
    )

@app.get("/ocr/languages/", tags=["OCR Service"])
async def proxy_ocr_languages(request: Request):
    target_url = f"{settings.GENERIC_OCR_SERVICE_URL}/ocr/languages/"
    auth_header = request.headers.get("Authorization")
    headers_to_fwd = {}
    if auth_header:
        headers_to_fwd["Authorization"] = auth_header
    return await forward_request(request, target_url, "GET", headers_to_forward=headers_to_fwd)

@app.post("/ekyc/extract_info/", tags=["eKYC Information Extraction Service"])
async def proxy_ekyc_extract_info(request: Request):
    target_url = f"{settings.EKYC_INFO_EXTRACTION_SERVICE_URL}/extract_info/"
    
    auth_header = request.headers.get("Authorization") 
    headers_to_fwd = {}
    if auth_header:
        headers_to_fwd["Authorization"] = auth_header

    json_data = await request.json()
    
    return await forward_request(
        request,
        target_url,
        "POST",
        json_data=json_data,
        headers_to_forward=headers_to_fwd
    )