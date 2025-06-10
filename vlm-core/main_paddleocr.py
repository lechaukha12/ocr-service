import os
import io
import logging
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
import numpy as np
from paddleocr import PaddleOCR

# Thiết lập logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Khởi tạo PaddleOCR với hỗ trợ tiếng Việt
# use_angle_cls=True để xử lý văn bản nghiêng
# lang='vi' để hỗ trợ tiếng Việt
try:
    ocr = PaddleOCR(use_angle_cls=True, lang='vi', use_gpu=False, show_log=False)
    logger.info("PaddleOCR initialized successfully with Vietnamese support")
except Exception as e:
    logger.error(f"Failed to initialize PaddleOCR: {e}")
    ocr = None

app = FastAPI(
    title="Vietnamese OCR Service with PaddleOCR",
    description="OCR service optimized for Vietnamese text using PaddleOCR",
    version="2.0.0"
)

# Thêm CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class OcrResponse(BaseModel):
    text: str
    model: str
    success: bool
    error: Optional[str] = None
    confidence: Optional[float] = None

class HealthResponse(BaseModel):
    status: str
    model: str
    ocr_status: str

# Helper functions
def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """Tiền xử lý hình ảnh để cải thiện độ chính xác OCR"""
    try:
        # Chuyển bytes thành PIL Image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Chuyển sang RGB nếu cần
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Chuyển sang numpy array
        img_array = np.array(image)
        
        return img_array
    except Exception as e:
        logger.error(f"Error preprocessing image: {e}")
        raise e

def extract_text_from_results(results):
    """Trích xuất văn bản từ kết quả PaddleOCR"""
    if not results or len(results) == 0:
        return "", 0.0
    
    text_lines = []
    confidences = []
    
    for line in results:
        if len(line) >= 2:
            # line[0] là coordinates, line[1] là (text, confidence)
            text_info = line[1]
            if len(text_info) >= 2:
                text = text_info[0]
                confidence = text_info[1]
                text_lines.append(text)
                confidences.append(confidence)
    
    # Kết hợp các dòng văn bản
    full_text = '\n'.join(text_lines)
    
    # Tính confidence trung bình
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    
    return full_text, avg_confidence

# Routes
@app.get("/health", response_model=HealthResponse)
async def health_check():
    ocr_status = "ok" if ocr is not None else "failed"
    status = "ok" if ocr_status == "ok" else "error"
    
    return HealthResponse(
        status=status,
        model="PaddleOCR-Vietnamese",
        ocr_status=ocr_status
    )

@app.post("/ocr", response_model=OcrResponse)
async def perform_ocr(image: UploadFile = File(...)):
    """
    Trích xuất text từ hình ảnh sử dụng PaddleOCR với hỗ trợ tiếng Việt
    """
    logger.info(f"OCR request received for file: {image.filename}")
    
    # Kiểm tra xem OCR đã được khởi tạo chưa
    if ocr is None:
        return OcrResponse(
            text="", 
            model="PaddleOCR-Vietnamese", 
            success=False, 
            error="OCR engine not initialized"
        )
    
    try:
        # Đọc image bytes
        image_bytes = await image.read()
        logger.info(f"Image size: {len(image_bytes)} bytes")
        
        # Tiền xử lý hình ảnh
        img_array = preprocess_image(image_bytes)
        logger.info(f"Image shape: {img_array.shape}")
        
        # Thực hiện OCR
        logger.info("Starting OCR processing...")
        results = ocr.ocr(img_array, cls=True)
        
        # Trích xuất văn bản từ kết quả
        extracted_text, confidence = extract_text_from_results(results[0] if results else [])
        
        if not extracted_text.strip():
            extracted_text = "Không phát hiện văn bản rõ ràng trong hình ảnh"
            confidence = 0.0
        
        logger.info(f"OCR completed. Text length: {len(extracted_text)}, Confidence: {confidence:.2f}")
        
        return OcrResponse(
            text=extracted_text,
            model="PaddleOCR-Vietnamese",
            success=True,
            error=None,
            confidence=confidence
        )
        
    except Exception as e:
        error_msg = f"Error during OCR processing: {str(e)}"
        logger.error(error_msg)
        return OcrResponse(
            text="", 
            model="PaddleOCR-Vietnamese", 
            success=False, 
            error=error_msg
        )

@app.get("/")
async def root():
    return {"message": "Vietnamese OCR Service with PaddleOCR", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)
