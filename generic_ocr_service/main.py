from fastapi import FastAPI, File, UploadFile, HTTPException, status, Form
from fastapi.responses import JSONResponse
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import io
import os
from typing import Optional
import cv2
import numpy as np
import math

app = FastAPI(title="Generic OCR Service (Advanced Preprocessing)")

pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

def deskew_image(image_cv: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 11, 2)
    contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return image_cv

    angles = []
    for contour in contours:
        if cv2.contourArea(contour) < 100:
            continue
        rect = cv2.minAreaRect(contour)
        angle = rect[-1]
        if angle < -45:
            angle = 90 + angle
        if abs(angle) < 30 and abs(angle) > 0.5 :
             angles.append(angle)

    if not angles:
        return image_cv

    median_angle = np.median(angles)
    if abs(median_angle) < 0.5:
        return image_cv

    (h, w) = image_cv.shape[:2]
    center = (w // 2, h // 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    abs_cos = abs(rotation_matrix[0,0])
    abs_sin = abs(rotation_matrix[0,1])
    new_w = int(h * abs_sin + w * abs_cos)
    new_h = int(h * abs_cos + w * abs_sin)
    rotation_matrix[0,2] += (new_w/2) - center[0]
    rotation_matrix[1,2] += (new_h/2) - center[1]
    rotated_image = cv2.warpAffine(image_cv, rotation_matrix, (new_w, new_h),
                                   flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated_image


def preprocess_image_for_ocr(image_bytes: bytes, target_width: Optional[int] = 1200) -> Image.Image:
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img_cv is None:
            return Image.open(io.BytesIO(image_bytes))

        img_cv = deskew_image(img_cv)

        if target_width:
            (h, w) = img_cv.shape[:2]
            if w != target_width:
                r = target_width / float(w)
                dim = (target_width, int(h * r))
                img_cv = cv2.resize(img_cv, dim, interpolation=cv2.INTER_LANCZOS4)

        gray_img = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        denoised_img = cv2.fastNlMeansDenoising(gray_img, None, h=10, templateWindowSize=7, searchWindowSize=21)
        current_img_to_process = denoised_img
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        contrast_enhanced_img = clahe.apply(current_img_to_process)
        current_img_to_process = contrast_enhanced_img
        binary_img = cv2.adaptiveThreshold(
            current_img_to_process, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            blockSize=15,
            C=9
        )
        kernel_size = 1
        kernel = np.ones((kernel_size,kernel_size),np.uint8)
        opened_img = cv2.morphologyEx(binary_img, cv2.MORPH_OPEN, kernel, iterations=1)
        closed_img = cv2.morphologyEx(opened_img, cv2.MORPH_CLOSE, kernel, iterations=1)
        final_img_to_ocr = closed_img
        processed_pil_img = Image.fromarray(final_img_to_ocr)
        return processed_pil_img
    except Exception as e:
        try:
            return Image.open(io.BytesIO(image_bytes))
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể xử lý file ảnh đầu vào.")


@app.post("/ocr/image/", tags=["OCR"])
async def ocr_image(
    file: UploadFile = File(...),
    lang: Optional[str] = Form("vie"),
    psm: Optional[str] = Form("3")
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File provided is not an image or content type is missing."
        )

    try:
        image_bytes = await file.read()
        processed_img_pil = preprocess_image_for_ocr(image_bytes)
        custom_config = f'-l {lang} --oem 3 --psm {psm} --dpi 300'
        text = pytesseract.image_to_string(processed_img_pil, config=custom_config)
        return JSONResponse(content={"filename": file.filename, "language": lang, "psm_used": psm, "text": text.strip()})

    except HTTPException as e:
        raise e
    except pytesseract.TesseractNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tesseract OCR engine not found or tesseract_cmd is incorrect."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during OCR processing: {type(e).__name__} - {str(e)}"
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Tesseract OCR engine not found.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not fetch Tesseract languages: {str(e)}")

@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    return {"status": "healthy", "message": "Generic OCR Service (Advanced Preprocessing) is running!"}