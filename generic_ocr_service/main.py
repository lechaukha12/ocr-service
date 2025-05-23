from fastapi import FastAPI, File, UploadFile, HTTPException, status, Form
from fastapi.responses import JSONResponse
import pytesseract
from PIL import Image
import io
import os
from typing import Optional
import cv2 # Thư viện OpenCV
import numpy as np

app = FastAPI(title="Generic OCR Service")

pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

def preprocess_image_for_ocr(image_bytes: bytes) -> Image.Image:
    try:
        # Đọc ảnh bằng OpenCV
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # 1. Chuyển sang ảnh xám
        gray_img = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

        # 2. Áp dụng Gaussian Blur để giảm nhiễu nhẹ (tùy chọn, có thể điều chỉnh kernel size)
        # blurred_img = cv2.GaussianBlur(gray_img, (3, 3), 0)

        # 3. Nhị phân hóa ảnh sử dụng Otsu's Binarization
        # Điều này hiệu quả với ảnh có độ tương phản tốt giữa nền và chữ
        _, binary_img = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # (Tùy chọn nâng cao hơn: Adaptive Thresholding nếu ảnh có điều kiện ánh sáng không đồng đều)
        # adaptive_thresh_img = cv2.adaptiveThreshold(gray_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        # cv2.THRESH_BINARY, 11, 2)


        # (Tùy chọn: Giảm nhiễu sau khi nhị phân hóa bằng morphological operations)
        # kernel = np.ones((1,1),np.uint8)
        # opening = cv2.morphologyEx(binary_img, cv2.MORPH_OPEN, kernel, iterations = 1)
        # closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel, iterations = 1)


        # Chuyển đổi ảnh OpenCV (NumPy array) đã xử lý trở lại đối tượng Image của Pillow
        # Sử dụng ảnh đã nhị phân hóa:
        processed_pil_img = Image.fromarray(binary_img)
        # Hoặc nếu bạn thử các bước khác:
        # processed_pil_img = Image.fromarray(gray_img) # Nếu chỉ muốn ảnh xám
        # processed_pil_img = Image.fromarray(adaptive_thresh_img) # Nếu dùng adaptive threshold

        return processed_pil_img
    except Exception as e:
        # print(f"Lỗi trong quá trình tiền xử lý ảnh: {e}")
        # Nếu lỗi, trả về ảnh gốc chưa xử lý
        return Image.open(io.BytesIO(image_bytes))


@app.post("/ocr/image/", tags=["OCR"])
async def ocr_image(
    file: UploadFile = File(...), 
    lang: Optional[str] = Form("vie"),
    psm: Optional[str] = Form("6") # Thêm tham số PSM, mặc định là 6
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File provided is not an image or content type is missing."
        )

    try:
        image_bytes = await file.read()
        
        # Tiền xử lý ảnh
        processed_img_pil = preprocess_image_for_ocr(image_bytes)
        
        # Cấu hình Tesseract với PSM tùy chỉnh
        # --oem 3: Chế độ OCR Engine mặc định (LSTM).
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
