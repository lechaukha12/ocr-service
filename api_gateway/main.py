from fastapi import FastAPI, Request, HTTPException, status, Response, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
import asyncio
import json
from typing import List, Optional
import logging # Thêm logging
import jwt

from config import settings

# Thiết lập logging cơ bản
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

    logger.info(f"Forwarding {method} to {target_url} with params {params}, json_data_present: {json_data is not None}, form_data_present: {form_data is not None}, files_data_present: {files_data is not None}")
    logger.debug(f"Outgoing headers for httpx: {client_headers}")

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
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
                logger.error(f"Method not allowed by gateway: {method}")
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

    except httpx.ConnectTimeout as exc_ct:
        logger.error(f"Service at {target_url} timed out (connect): {exc_ct}")
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=f"Service at {target_url} timed out (connect).")
    except httpx.ReadTimeout as exc_rt:
        logger.error(f"Service at {target_url} timed out (read): {exc_rt}")
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=f"Service at {target_url} timed out (read).")
    except httpx.RequestError as exc_req:
        logger.error(f"Error connecting to service at {target_url}: {exc_req}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Error connecting to service at {target_url}: {exc_req}")
    except Exception as e_fwd: 
        logger.error(f"Unhandled exception in forward_request to {target_url}: {type(e_fwd).__name__} - {e_fwd}", exc_info=True)
        if not isinstance(e_fwd, HTTPException):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gateway error forwarding to {target_url}: {type(e_fwd).__name__}")
        else:
            raise e_fwd


@app.post("/auth/users/", tags=["User Service"])
async def register_user(request: Request):
    try:
        json_data = await request.json()
    except json.JSONDecodeError as json_err:
        logger.error(f"Invalid JSON received for /auth/users/: {json_err}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid JSON format: {json_err}")
    except Exception as e:
        logger.error(f"Error reading request body for /auth/users/: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error reading request body.")
        
    target_url = f"{settings.USER_SERVICE_URL}/users/"
    return await forward_request(request, target_url, "POST", json_data=json_data)

@app.post("/auth/token", tags=["User Service"])
async def login_for_token(request: Request):
    try:
        form_data = await request.form()
    except Exception as e:
        logger.error(f"Error reading form data for /auth/token: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error reading form data.")

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
    # Note: Reading body directly for generic forwarding.
    # Consider specific parsing if only multipart is allowed for this route.
    try:
        body_bytes = await request.body()
    except Exception as e:
        logger.error(f"Error reading body for /storage/upload/file/: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error reading request body for file upload.")

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

@app.get("/files/{filename}", tags=["Storage Service"])
async def proxy_get_file_direct(filename: str, request: Request):
    """
    Route để xử lý yêu cầu tải ảnh trực tiếp từ /files/{filename}
    Portal sẽ gọi endpoint này để hiển thị ảnh CCCD và selfie
    """
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

@app.post("/admin/users/{user_id}/activate", tags=["Admin Portal"])
async def proxy_activate_user(request: Request, user_id: int):
    target_url = f"{settings.ADMIN_PORTAL_BACKEND_SERVICE_URL}/admin/users/{user_id}/activate"
    auth_header = request.headers.get("Authorization")
    headers_to_fwd = {}
    if auth_header:
        headers_to_fwd["Authorization"] = auth_header
    return await forward_request(request, target_url, "POST", headers_to_forward=headers_to_fwd)

@app.post("/admin/users/{user_id}/deactivate", tags=["Admin Portal"])
async def proxy_deactivate_user(request: Request, user_id: int):
    target_url = f"{settings.ADMIN_PORTAL_BACKEND_SERVICE_URL}/admin/users/{user_id}/deactivate"
    auth_header = request.headers.get("Authorization")
    headers_to_fwd = {}
    if auth_header:
        headers_to_fwd["Authorization"] = auth_header
    return await forward_request(request, target_url, "POST", headers_to_forward=headers_to_fwd)

@app.post("/ocr/image/", tags=["OCR Service"])
async def proxy_ocr_image(
    request: Request, # Added request here
    file: UploadFile = File(...), # Kept File(...) for multipart detection by FastAPI
    lang: Optional[str] = Form(None),
    psm: Optional[str] = Form(None)
):
    target_url = f"{settings.GENERIC_OCR_SERVICE_URL}/ocr/image/"
    
    # Prepare form data and files for httpx
    # This requires careful handling as request.form() consumes the body if called directly
    # and we need to reconstruct it for httpx if it's multipart.
    # The most robust way for multipart is to let httpx build it from files and data dicts.

    file_content = await file.read()
    files_for_httpx = [("file", (file.filename, file_content, file.content_type))]
    
    data_for_httpx = {}
    if lang:
        data_for_httpx["lang"] = lang
    if psm:
        data_for_httpx["psm"] = psm
    
    auth_header = request.headers.get("Authorization")
    headers_to_fwd = {} # Do not forward original content-type for multipart, httpx will set it.
    if auth_header:
        headers_to_fwd["Authorization"] = auth_header

    # When sending files with httpx, do not set content-type in headers,
    # httpx will generate the correct multipart/form-data header.
    return await forward_request(
        request, # Pass original request for other headers if needed
        target_url,
        "POST",
        form_data=data_for_httpx, # httpx handles form data
        files_data=files_for_httpx, # httpx handles files
        headers_to_forward=headers_to_fwd
    )


@app.post("/ekyc/extract_info/", tags=["eKYC Information Extraction Service"])
async def proxy_ekyc_extract_info(request: Request):
    target_url = f"{settings.EKYC_INFO_EXTRACTION_SERVICE_URL}/extract_info/"

    auth_header = request.headers.get("Authorization")
    headers_to_fwd = {}
    if auth_header:
        headers_to_fwd["Authorization"] = auth_header
    
    try:
        json_data = await request.json()
    except json.JSONDecodeError as json_err:
        logger.error(f"Invalid JSON received for /ekyc/extract_info/: {json_err}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid JSON format: {json_err}")
    except Exception as e:
        logger.error(f"Error reading request body for /ekyc/extract_info/: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error reading request body.")


    return await forward_request(
        request,
        target_url,
        "POST",
        json_data=json_data,
        headers_to_forward=headers_to_fwd
    )

@app.post("/ekyc/full_flow/", tags=["eKYC Full Flow"])
async def ekyc_full_flow(
    request: Request,
    cccd_image: UploadFile = File(...),
    selfie_image: UploadFile = File(...),
    lang: Optional[str] = Form("vie"),
    psm: Optional[str] = Form(None)
):
    """
    1. Upload selfie image lên storage_service, lấy URL.
    2. Gửi ảnh CCCD qua OCR service lấy text.
    3. Gửi text qua eKYC extraction lấy dữ liệu bóc tách.
    4. Lưu dữ liệu eKYC (các trường + selfie_image_url) vào user_service.
    5. Trả về kết quả tổng hợp.
    """
    # 1. Upload selfie image
    storage_url = f"{settings.STORAGE_SERVICE_URL}/upload/file/"
    selfie_bytes = await selfie_image.read()
    files = {"file": (selfie_image.filename, selfie_bytes, selfie_image.content_type)}
    
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        storage_resp = await client.post(storage_url, files=files)
        if storage_resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Upload selfie image failed")
        selfie_result = storage_resp.json()
        selfie_image_url = selfie_result.get("url") or selfie_result.get("file_url") or selfie_result.get("file_id")
        if not selfie_image_url:
            raise HTTPException(status_code=502, detail="Storage service did not return file url")

    # Đọc file CCCD chỉ 1 lần
    cccd_bytes = await cccd_image.read()

    # 2. OCR CCCD image
    ocr_url = f"{settings.GENERIC_OCR_SERVICE_URL}/ocr/image/"
    files = {"file": (cccd_image.filename, cccd_bytes, cccd_image.content_type)}
    data = {"lang": lang}
    if psm:
        data["psm"] = psm
    # Tăng timeout lên 120 giây cho OCR service vì xử lý ảnh có thể mất nhiều thời gian
    ocr_text = None
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                ocr_resp = await client.post(ocr_url, files=files, data=data)
                if ocr_resp.status_code == 200:
                    ocr_json = ocr_resp.json()
                    ocr_text = ocr_json.get("text")
                    if not ocr_text:
                        logger.warning("OCR service returned empty text")
                else:
                    logger.error(f"OCR service failed with status {ocr_resp.status_code}")
            except httpx.ReadTimeout:
                logger.warning(f"OCR service timeout for file {cccd_image.filename}, continuing without OCR text")
    except Exception as e:
        logger.error(f"Unexpected error during OCR: {e}")
        
    # Nếu OCR không thành công, vẫn tiếp tục với extracted_info rỗng

    # 3. eKYC extraction
    ekyc_data = {}
    if ocr_text:
        ekyc_url = f"{settings.EKYC_INFO_EXTRACTION_SERVICE_URL}/extract_info/"
        payload = {"ocr_text": ocr_text, "language": lang}
        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                ekyc_resp = await client.post(ekyc_url, json=payload)
                if ekyc_resp.status_code == 200:
                    ekyc_data = ekyc_resp.json()
                else:
                    logger.error(f"eKYC extraction failed with status {ekyc_resp.status_code}")
        except Exception as e:
            logger.error(f"Unexpected error during eKYC extraction: {e}")

    # 4. Lưu dữ liệu eKYC vào user_service
    # Lấy user_id từ token
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = auth_header.split(" ")[-1]
    try:
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = decoded.get("user_id")
    except Exception as e:
        logger.error(f"[ERROR] Failed to decode token: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token missing user_id")

    user_service_url = f"{settings.USER_SERVICE_URL}/ekyc/"
    ekyc_payload = {k: ekyc_data.get(k) for k in [
        "id_number", "full_name", "date_of_birth", "gender", "nationality", "place_of_origin", "place_of_residence", "expiry_date"
    ]}
    ekyc_payload["user_id"] = user_id
    ekyc_payload["selfie_image_url"] = selfie_image_url
    logger.info(f"[DEBUG] user_service_url: {user_service_url}")
    logger.info(f"[DEBUG] ekyc_payload: {ekyc_payload}")
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        save_resp = await client.post(user_service_url, json=ekyc_payload, headers={"Authorization": auth_header})
        logger.info(f"[DEBUG] save_resp status: {save_resp.status_code}")
        logger.info(f"[DEBUG] save_resp text: {save_resp.text}")
        if save_resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Save eKYC info failed: {save_resp.text}")
        saved_ekyc = save_resp.json()

    # Upload CCCD image to storage for admin review (dùng lại cccd_bytes)
    cccd_image_url = None
    try:
        storage_url = f"{settings.STORAGE_SERVICE_URL}/upload/file/"
        files = {"file": (cccd_image.filename, cccd_bytes, cccd_image.content_type)}
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            cccd_storage_resp = await client.post(storage_url, files=files)
            if cccd_storage_resp.status_code == 200:
                cccd_result = cccd_storage_resp.json()
                cccd_image_url = cccd_result.get("url") or cccd_result.get("file_url") or cccd_result.get("file_id")
                if not cccd_image_url:
                    logger.error("Storage service did not return file url for CCCD")
            else:
                logger.error(f"Upload CCCD image failed with status {cccd_storage_resp.status_code}")
    except Exception as e:
        logger.error(f"Exception during CCCD image upload: {e}")

    # Face matching (dùng lại selfie_bytes và cccd_bytes)
    face_match_score = None
    face_match_status = "PENDING"
    try:
        face_matching_url = f"{settings.FACE_COMPARISON_SERVICE_URL}/compare_faces/"
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            files = {
                "file1": (selfie_image.filename, selfie_bytes, selfie_image.content_type),
                "file2": (cccd_image.filename, cccd_bytes, cccd_image.content_type)
            }
            face_matching_resp = await client.post(face_matching_url, files=files)
            if face_matching_resp.status_code == 200:
                face_match_result = face_matching_resp.json()
                # Lower score is better in face_recognition (it's a distance)
                # Convert to a similarity score where higher is better
                face_match_score = 1.0 - face_match_result.get("score", 0.0) if face_match_result.get("score") is not None else None
                # A score above 0.6 (60%) is considered a match
                face_match_status = "MATCHED" if face_match_score and face_match_score > 0.6 else "NOT_MATCHED"
            else:
                logger.error(f"Face matching failed with status {face_matching_resp.status_code}: {face_matching_resp.text}")
                face_match_status = "ERROR"
    except Exception as e:
        logger.error(f"Exception during face matching: {e}")
        face_match_status = "ERROR"

    # Save to /ekyc/record/ for admin/audit with automatic verification
    # Auto-approve if face_match_score is high enough, otherwise auto-reject
    verification_status = None
    verification_note = None
    
    # We're using a threshold of 0.6 (60%) for a good match
    if face_match_status == "MATCHED" and face_match_score and face_match_score > 0.6:
        verification_status = "APPROVED"
        verification_note = f"Tự động xác minh bởi hệ thống - Điểm đối chiếu khuôn mặt {face_match_score:.2%} đạt ngưỡng"
    elif face_match_status == "NOT_MATCHED" or (face_match_score is not None and face_match_score <= 0.6):
        verification_status = "REJECTED"
        verification_note = f"Tự động từ chối bởi hệ thống - Điểm đối chiếu khuôn mặt {face_match_score:.2%} không đạt ngưỡng"
    elif face_match_status == "ERROR":
        verification_status = "REJECTED"
        verification_note = "Tự động từ chối bởi hệ thống - Lỗi xử lý khuôn mặt"
    
    record_payload = {
        "user_id": user_id,
        "status": face_match_status,
        "extracted_info": ekyc_data if isinstance(ekyc_data, dict) else {},
        "document_image_id": cccd_image_url,
        "selfie_image_id": selfie_image_url,
        "face_match_score": face_match_score,
        "verification_status": verification_status,
        "verification_note": verification_note,
        "verified_at": None,  # Will be set by the server
        "verified_by": None   # Auto-verification by system
    }
    logger.info(f"[DEBUG] Gửi record_payload tới user_service: {record_payload}")
    record_url = f"{settings.USER_SERVICE_URL}/ekyc/record/"
    logger.info(f"[DEBUG] record_url: {record_url}")
    
    saved_record = None
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            record_resp = await client.post(record_url, json=record_payload, headers={"Authorization": auth_header})
            logger.info(f"[DEBUG] record_resp status: {record_resp.status_code}")
            logger.info(f"[DEBUG] record_resp text: {record_resp.text}")
            if record_resp.status_code == 200:
                logger.info("eKYC record saved successfully")
                saved_record = record_resp.json()
            else:
                logger.error(f"Failed to save eKYC record: {record_resp.text}")
    except Exception as e:
        logger.error(f"[ERROR] Exception when saving eKYC record: {e}")

    # 5. Trả về kết quả tổng hợp
    return {
        "ekyc_info": saved_ekyc or {},
        "ocr_text": ocr_text or "",
        "extracted_fields": ekyc_data or {},
        "selfie_image_url": selfie_image_url or "",
        "document_image_id": cccd_image_url or "",
        "face_match_status": face_match_status or "PENDING",
        "face_match_score": face_match_score,
        "ekyc_record": saved_record
    }

@app.get("/admin/ekyc", tags=["Admin Portal"])
async def proxy_get_ekyc_records(request: Request):
    target_url = f"{settings.ADMIN_PORTAL_BACKEND_SERVICE_URL}/admin/ekyc"
    auth_header = request.headers.get("Authorization")
    headers_to_fwd = {}
    if auth_header:
        headers_to_fwd["Authorization"] = auth_header
    return await forward_request(request, target_url, "GET", headers_to_forward=headers_to_fwd)

@app.get("/admin/ekyc/{record_id}", tags=["Admin Portal"])
async def proxy_get_ekyc_detail(request: Request, record_id: int):
    target_url = f"{settings.ADMIN_PORTAL_BACKEND_SERVICE_URL}/admin/ekyc/{record_id}"
    auth_header = request.headers.get("Authorization")
    headers_to_fwd = {}
    if auth_header:
        headers_to_fwd["Authorization"] = auth_header
    return await forward_request(request, target_url, "GET", headers_to_forward=headers_to_fwd)

@app.get("/admin/statistics", tags=["Admin Portal"])
async def proxy_admin_statistics(request: Request):
    target_url = f"{settings.ADMIN_PORTAL_BACKEND_SERVICE_URL}/admin/statistics"
    auth_header = request.headers.get("Authorization")
    headers_to_fwd = {}
    if auth_header:
        headers_to_fwd["Authorization"] = auth_header
    return await forward_request(request, target_url, "GET", headers_to_forward=headers_to_fwd)

@app.get("/admin/notifications", tags=["Admin Portal"])
async def proxy_admin_notifications(request: Request):
    target_url = f"{settings.ADMIN_PORTAL_BACKEND_SERVICE_URL}/admin/notifications"
    auth_header = request.headers.get("Authorization")
    headers_to_fwd = {}
    if auth_header:
        headers_to_fwd["Authorization"] = auth_header
    return await forward_request(request, target_url, "GET", headers_to_forward=headers_to_fwd)

@app.post("/admin/ekyc/{record_id}/verify", tags=["Admin Portal"])
async def proxy_verify_ekyc_record(request: Request, record_id: int):
    target_url = f"{settings.ADMIN_PORTAL_BACKEND_SERVICE_URL}/admin/ekyc/{record_id}/verify"
    auth_header = request.headers.get("Authorization")
    headers_to_fwd = {}
    if auth_header:
        headers_to_fwd["Authorization"] = auth_header
    return await forward_request(request, target_url, "POST", headers_to_forward=headers_to_fwd)

@app.post("/vlm/ocr/", tags=["VLM Core Service"])
async def proxy_vlm_ocr_image(
    request: Request,
    image: UploadFile = File(...),
    language: str = Form("vie"),
):
    """
    OCR sử dụng VLM Core service (Gemma 3)
    """
    target_url = f"{settings.VLM_CORE_SERVICE_URL}/ocr"
    files_data = [("image", (image.filename, await image.read(), image.content_type))]
    form_data = {"language": language}
    
    return await forward_request(
        request, 
        target_url, 
        "POST", 
        form_data=form_data, 
        files_data=files_data
    )

@app.post("/vlm/extract_info/", tags=["VLM Core Service"])
async def proxy_vlm_extract_info(
    request: Request,
    image: UploadFile = File(...),
    language: str = Form("vie"),
):
    """
    Trích xuất thông tin từ ảnh CCCD/CMND sử dụng VLM Core service (Gemma 3)
    """
    target_url = f"{settings.VLM_CORE_SERVICE_URL}/extract_info"
    files_data = [("image", (image.filename, await image.read(), image.content_type))]
    form_data = {"language": language}
    
    return await forward_request(
        request, 
        target_url, 
        "POST", 
        form_data=form_data, 
        files_data=files_data
    )

@app.get("/vlm/languages/", tags=["VLM Core Service"])
async def proxy_vlm_languages(request: Request):
    """
    Lấy danh sách ngôn ngữ được VLM Core hỗ trợ
    """
    target_url = f"{settings.VLM_CORE_SERVICE_URL}/languages"
    return await forward_request(request, target_url, "GET")

@app.get("/vlm/health/", tags=["VLM Core Service"])
async def proxy_vlm_health(request: Request):
    """
    Kiểm tra trạng thái hoạt động của VLM Core service
    """
    target_url = f"{settings.VLM_CORE_SERVICE_URL}/health"
    return await forward_request(request, target_url, "GET")