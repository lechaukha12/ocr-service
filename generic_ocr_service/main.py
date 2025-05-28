import asyncio
from fastapi import FastAPI, File, UploadFile, HTTPException, status, Form
from fastapi.responses import JSONResponse
from PIL import Image
import io
import base64
import logging
import httpx 
from typing import Optional, List, Dict, Any

# Import settings từ config.py mới
from config import settings as service_settings

# === Cấu hình Logging ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Generic OCR Service (Gemini Edition)")

@app.on_event("startup")
async def startup_event():
    logger.info("Generic OCR Service (Gemini Edition) is starting up.")
    if not service_settings.OCR_GEMINI_API_KEY or service_settings.OCR_GEMINI_API_KEY == "YOUR_OCR_GEMINI_API_KEY_HERE":
        logger.warning("OCR_GEMINI_API_KEY is not configured or using placeholder value. Calls to Gemini API may fail.")
    else:
        logger.info("OCR_GEMINI_API_KEY is configured.")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Generic OCR Service (Gemini Edition) is shutting down.")

async def count_gemini_tokens_http(parts: List[Dict[str, Any]], model_name: str = "gemini-2.0-flash") -> Optional[int]:
    """
    Đếm số token cho một nội dung nhất định bằng cách gọi API countTokens của Gemini.
    """
    if not service_settings.OCR_GEMINI_API_KEY or service_settings.OCR_GEMINI_API_KEY == "YOUR_OCR_GEMINI_API_KEY_HERE":
        logger.error("Cannot count tokens: OCR_GEMINI_API_KEY is not configured correctly.")
        return None

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:countTokens?key={service_settings.OCR_GEMINI_API_KEY}"
    payload = {"contents": [{"parts": parts}]}
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(api_url, json=payload, headers={'Content-Type': 'application/json'})
            response.raise_for_status()
            result = response.json()
            total_tokens = result.get("totalTokens")
            if total_tokens is not None:
                logger.info(f"Token count for model {model_name} with {len(parts)} part(s): {total_tokens} tokens.")
                return total_tokens
            else:
                logger.error(f"Could not get totalTokens from Gemini countTokens API response: {result}")
                return None
    except httpx.HTTPStatusError as e:
        error_body = "N/A"
        try: 
            error_body = e.response.json()
        except: 
            pass # Giữ error_body là "N/A" nếu không parse được JSON
        logger.error(f"HTTP error calling Gemini countTokens API: {e.response.status_code} - {error_body}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error in count_gemini_tokens_http: {e}", exc_info=True)
        return None

async def ocr_with_gemini(image_bytes: bytes, filename: str) -> str:
    try:
        base64_image_data = base64.b64encode(image_bytes).decode('utf-8')
        
        mime_type = "image/jpeg" 
        if filename:
            ext = filename.split('.')[-1].lower()
            if ext == "png": mime_type = "image/png"
            elif ext in ["jpg", "jpeg"]: mime_type = "image/jpeg"

        logger.info(f"Preparing to call Gemini for image: {filename}, mime_type: {mime_type}")

        prompt_text = "Trích xuất toàn bộ văn bản từ hình ảnh này. Chỉ trả về phần văn bản thuần túy, không có giải thích hay định dạng markdown."

        input_parts_for_gemini = [
            {"text": prompt_text},
            {
                "inline_data": {
                    "mime_type": mime_type,
                    "data": base64_image_data
                }
            }
        ]

        input_tokens = await count_gemini_tokens_http(input_parts_for_gemini, model_name="gemini-2.0-flash")
        if input_tokens is not None:
            logger.info(f"Estimated INPUT tokens for Gemini OCR (gemini-2.0-flash): {input_tokens}")

        payload = {
            "contents": [{"parts": input_parts_for_gemini}],
            "generationConfig": { "temperature": 0.2 }
        }
        
        if not service_settings.OCR_GEMINI_API_KEY or service_settings.OCR_GEMINI_API_KEY == "YOUR_OCR_GEMINI_API_KEY_HERE":
            logger.error("OCR_GEMINI_API_KEY is not configured correctly. Cannot call Gemini API.")
            return "Lỗi: OCR_GEMINI_API_KEY chưa được cấu hình trong service."

        api_url_generate = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={service_settings.OCR_GEMINI_API_KEY}"

        async with httpx.AsyncClient(timeout=60.0) as client: 
            logger.info(f"Calling Gemini generateContent API...")
            response = await client.post(api_url_generate, json=payload, headers={'Content-Type': 'application/json'})
            response.raise_for_status() 
            
            result = response.json()
            logger.debug(f"Gemini API raw response: {result}")

            if (result.get("candidates") and 
                result["candidates"][0].get("content") and
                result["candidates"][0]["content"].get("parts") and
                len(result["candidates"][0]["content"]["parts"]) > 0 and
                result["candidates"][0]["content"]["parts"][0].get("text")):
                
                extracted_text = result["candidates"][0]["content"]["parts"][0]["text"]
                logger.info(f"Text extracted successfully by Gemini for {filename}. Length: {len(extracted_text)}")

                output_parts_for_gemini = [{"text": extracted_text}]
                output_tokens = await count_gemini_tokens_http(output_parts_for_gemini, model_name="gemini-2.0-flash")
                if output_tokens is not None:
                    logger.info(f"Estimated OUTPUT tokens for Gemini OCR (gemini-2.0-flash): {output_tokens}")
                if input_tokens is not None and output_tokens is not None:
                    logger.info(f"Estimated TOTAL tokens for this OCR request: {input_tokens + output_tokens}")

                return extracted_text.strip()
            else:
                logger.error(f"Gemini API response structure unexpected or content missing for {filename}. Response: {result}")
                error_reason = result.get("promptFeedback", {}).get("blockReason", {}).get("reason", "Unknown error from Gemini")
                if not result.get("candidates"): error_reason = "No candidates in response."
                return f"Lỗi: Gemini không trả về văn bản. Lý do: {error_reason}"

    except httpx.HTTPStatusError as e:
        error_body = "N/A"
        try: 
            error_body = e.response.json()
        except: 
            pass # Sửa lỗi cú pháp ở đây
        logger.error(f"HTTP error calling Gemini API for {filename}: {e.response.status_code} - {error_body}", exc_info=True)
        return f"Lỗi: Gọi Gemini API thất bại. Status: {e.response.status_code}. Chi tiết: {error_body}"
    except Exception as e:
        logger.error(f"Unexpected error during OCR with Gemini for {filename}: {e}", exc_info=True)
        return f"Lỗi không xác định khi thực hiện OCR với Gemini: {str(e)}"

@app.post("/ocr/image/", tags=["OCR"])
async def ocr_image_endpoint(
    file: UploadFile = File(...),
    lang: Optional[str] = Form(None), 
    psm: Optional[str] = Form(None)   
):
    logger.info(f"Received OCR request for file: {file.filename}. Lang (ignored): {lang}, PSM (ignored): {psm}")
    
    if not file.content_type or not file.content_type.startswith("image/"):
        logger.warning(f"Unsupported media type: {file.content_type} for file: {file.filename}")
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported media type.")

    try:
        image_bytes = await file.read()
        if not image_bytes:
            logger.warning(f"Received empty file: {file.filename}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file.")
        try:
            img_pil = Image.open(io.BytesIO(image_bytes))
            img_pil.verify() 
        except Exception as img_err:
            logger.error(f"Invalid image file provided: {file.filename}, error: {img_err}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid image file: {img_err}")

        ocr_text_result = await ocr_with_gemini(image_bytes, file.filename)

        return JSONResponse(content={
            "filename": file.filename,
            "text": ocr_text_result 
        })

    except HTTPException as e: 
        raise e
    except Exception as e:
        logger.error(f"Error processing OCR request for file {file.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")
    finally:
        if file:
            await file.close()

@app.get("/ocr/languages/", tags=["OCR Info"])
async def get_supported_languages():
    return {"languages": ["auto"], "message": "Gemini API auto-detects language or can be guided by prompt."} 

@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    api_key_configured = service_settings.OCR_GEMINI_API_KEY and service_settings.OCR_GEMINI_API_KEY != "YOUR_OCR_GEMINI_API_KEY_HERE"
    if api_key_configured:
        return {"status": "healthy", "message": "Generic OCR Service (Gemini Edition) is running and API key is configured."}
    else:
        return {"status": "unhealthy", "message": "Generic OCR Service (Gemini Edition) is running BUT OCR_GEMINI_API_KEY is NOT configured."}