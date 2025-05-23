from fastapi import FastAPI, File, UploadFile, HTTPException, status, Form
from fastapi.responses import JSONResponse
import pytesseract
from PIL import Image
import io
import os
from typing import Optional

app = FastAPI(title="Generic OCR Service")

# Chỉ định đường dẫn đến Tesseract executable.
# Điều này quan trọng để pytesseract tìm thấy Tesseract trong môi trường container.
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

@app.post("/ocr/image/", tags=["OCR"])
async def ocr_image(file: UploadFile = File(...), lang: Optional[str] = Form("vie")): # Mặc định tiếng Việt (vie)
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File provided is not an image or content type is missing."
        )

    try:
        image_bytes = await file.read()
        img = Image.open(io.BytesIO(image_bytes))
        
        # Cấu hình Tesseract:
        # -l {lang}: chọn ngôn ngữ.
        # --oem 3: Chế độ OCR Engine mặc định (LSTM).
        # --psm 6: Chế độ Page Segmentation Mode - Assume a single uniform block of text.
        # Bạn có thể thử các giá trị psm khác tùy theo loại ảnh (ví dụ psm 3, 4, 11, 13).
        custom_config = f'-l {lang} --oem 3 --psm 6' 
        text = pytesseract.image_to_string(img, config=custom_config)
        
        return JSONResponse(content={"filename": file.filename, "language": lang, "text": text.strip()})

    except HTTPException as e: # Re-raise HTTPException để FastAPI xử lý đúng status code
        raise e
    except pytesseract.TesseractNotFoundError:
        # print("Tesseract is not installed or not in your PATH, or tesseract_cmd is incorrect.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tesseract OCR engine not found or tesseract_cmd is incorrect. Please check server configuration."
        )
    except Exception as e:
        # print(f"Error during OCR processing: {type(e).__name__} - {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during OCR processing: {str(e)}"
        )
    finally:
        if file and not file.file.closed: # Đảm bảo file được đóng
             await file.close()

@app.get("/ocr/languages/", tags=["OCR"])
async def get_available_languages():
    try:
        # Thử lấy danh sách ngôn ngữ. Nếu TESSDATA_PREFIX đúng, nó sẽ hoạt động.
        languages = pytesseract.get_languages(config='')
        return JSONResponse(content={"available_languages": languages})
    except pytesseract.TesseractNotFoundError:
        # print("Tesseract is not installed or not in your PATH, or tesseract_cmd is incorrect.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tesseract OCR engine not found or tesseract_cmd is incorrect. Please check server configuration."
        )
    except Exception as e:
        # print(f"Could not fetch Tesseract languages: {type(e).__name__} - {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not fetch Tesseract languages: {str(e)}"
        )

@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    return {"status": "healthy", "message": "Generic OCR Service is running!"}

print("Full main.py for Generic OCR Service loaded by Python interpreter.")
