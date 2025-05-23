from fastapi import FastAPI, File, UploadFile, HTTPException, status, Form
from fastapi.responses import JSONResponse
import pytesseract
from PIL import Image
import io
import os
from typing import Optional
import cv2
import numpy as np

app = FastAPI(title="Generic OCR Service")

pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

def preprocess_image_for_ocr(image_bytes: bytes) -> Image.Image:
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # 1. Chuyển sang ảnh xám
        gray_img = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

        # 2. Khử nhiễu bằng Median Blur (thử nghiệm)
        # Kích thước kernel phải là số lẻ, ví dụ: 3 hoặc 5
        # Nếu ảnh quá mờ sau bước này, có thể giảm kernel size hoặc bỏ qua
        median_blurred_img = cv2.medianBlur(gray_img, 3)
        
        current_img_to_process = median_blurred_img
        # current_img_to_process = gray_img # Nếu không muốn dùng Median Blur

        # 3. (Tùy chọn) Áp dụng CLAHE để cải thiện độ tương phản cục bộ
        # clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        # clahe_img = clahe.apply(current_img_to_process)
        # current_img_to_process = clahe_img # Sử dụng ảnh đã qua CLAHE nếu muốn

        # 4. Nhị phân hóa ảnh
        # Tùy chọn A: Adaptive Thresholding
        # Thử các giá trị blockSize và C khác nhau.
        # blockSize lớn hơn có thể phù hợp với các vùng chữ lớn hơn.
        # C dương làm cho ít pixel được coi là foreground hơn.
        binary_img = cv2.adaptiveThreshold(
            current_img_to_process, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, # THỬ THRESH_BINARY_INV (chữ trắng trên nền đen cho Tesseract thường tốt hơn)
            blockSize=15, # Thử tăng blockSize
            C=9           # Thử điều chỉnh C
        )

        # Tùy chọn B: Otsu's Binarization
        # _, binary_img = cv2.threshold(current_img_to_process, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 5. (Tùy chọn) Khử nhiễu thêm sau nhị phân hóa bằng phép toán hình thái
        # kernel_size = 2
        # kernel = np.ones((kernel_size, kernel_size), np.uint8)
        # opened_img = cv2.morphologyEx(binary_img, cv2.MORPH_OPEN, kernel, iterations=1)
        # final_img_to_ocr = cv2.morphologyEx(opened_img, cv2.MORPH_CLOSE, kernel, iterations=1)
        
        final_img_to_ocr = binary_img # Sử dụng ảnh đã nhị phân hóa trực tiếp

        # Lưu ảnh đã xử lý để kiểm tra (chỉ dùng khi debug)
        # cv2.imwrite("processed_image_for_ocr.png", final_img_to_ocr)

        processed_pil_img = Image.fromarray(final_img_to_ocr)
        return processed_pil_img
        
    except Exception as e:
        # print(f"Lỗi trong quá trình tiền xử lý ảnh: {e}")
        return Image.open(io.BytesIO(image_bytes))


@app.post("/ocr/image/", tags=["OCR"])
async def ocr_image(
    file: UploadFile = File(...), 
    lang: Optional[str] = Form("vie"),
    psm: Optional[str] = Form("6") 
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File provided is not an image or content type is missing."
        )

    try:
        image_bytes = await file.read()
        
        processed_img_pil = preprocess_image_for_ocr(image_bytes)
        
        custom_config = f'-l {lang} --oem 3 --psm {psm}' 
        text = pytesseract.image_to_string(processed_img_pil, config=custom_config)
        
        return JSONResponse(content={"filename": file.filename, "language": lang, "psm_used": psm, "text": text.strip()})

    except HTTPException as e:
        raise e
    except pytesseract.TesseractNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tesseract OCR engine not found or tesseract_cmd is incorrect. Please check server configuration."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during OCR processing: {str(e)}"
        )
    finally:
        if file and hasattr(file, 'file') and not file.file.closed:
             await file.close()

@app.get("/ocr/languages/", tags=["OCR"])
async def get_available_languages():
    try:
        languages = pytesseract.get_languages(config='')
        return JSONResponse(content={"available_languages": languages})
    except pytesseract.TesseractNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tesseract OCR engine not found or tesseract_cmd is incorrect. Please check server configuration."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not fetch Tesseract languages: {str(e)}"
        )

@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    return {"status": "healthy", "message": "Generic OCR Service is running!"}
