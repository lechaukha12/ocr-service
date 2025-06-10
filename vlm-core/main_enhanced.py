import os
import io
import logging
import httpx
import time
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
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

# Enhanced Models
class TextBbox(BaseModel):
    text: str
    confidence: float
    bbox: List[List[float]]  # Coordinates of the bounding box

class OcrResponse(BaseModel):
    text: str
    model: str
    success: bool
    error: Optional[str] = None
    confidence: Optional[float] = None

class DetailedOcrResponse(BaseModel):
    text: str
    model: str
    success: bool
    error: Optional[str] = None
    confidence: Optional[float] = None
    text_blocks: Optional[List[TextBbox]] = None
    processing_time: Optional[float] = None

class HealthResponse(BaseModel):
    status: str
    model: str
    ocr_status: str
    
class UrlOcrRequest(BaseModel):
    url: HttpUrl
    format: Optional[str] = "text"  # "text" or "json"

# Enhanced utility functions
def preprocess_image(image_bytes):
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
        return "", 0.0, []
    
    text_lines = []
    confidences = []
    text_blocks = []
    
    for line in results:
        if len(line) >= 2:
            # line[0] là coordinates, line[1] là (text, confidence)
            bbox = line[0]
            text_info = line[1]
            if len(text_info) >= 2:
                text = text_info[0]
                confidence = text_info[1]
                text_lines.append(text)
                confidences.append(confidence)
                
                # Create text block for detailed response
                text_blocks.append(TextBbox(
                    text=text,
                    confidence=confidence,
                    bbox=bbox
                ))
    
    # Kết hợp các dòng văn bản
    full_text = '\n'.join(text_lines)
    
    # Tính confidence trung bình
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    
    return full_text, avg_confidence, text_blocks

async def download_image_from_url(url: str) -> bytes:
    """Download image from URL"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="URL does not point to an image")
            
            return response.content
    except httpx.HTTPError as e:
        logger.error(f"Error downloading image from URL {url}: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to download image: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error downloading image from URL {url}: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

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

@app.post("/ocr", response_model=DetailedOcrResponse)
async def perform_ocr(
    image: UploadFile = File(...),
    format: str = Form("text")  # "text" or "json"
):
    """
    Trích xuất text từ hình ảnh sử dụng PaddleOCR với hỗ trợ tiếng Việt
    """
    start_time = time.time()
    
    logger.info(f"OCR request received for file: {image.filename}, format: {format}")
    
    # Kiểm tra xem OCR đã được khởi tạo chưa
    if ocr is None:
        return DetailedOcrResponse(
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
        extracted_text, confidence, text_blocks = extract_text_from_results(results[0] if results else [])
        
        if not extracted_text.strip():
            extracted_text = "Không phát hiện văn bản rõ ràng trong hình ảnh"
            confidence = 0.0
            text_blocks = []
        
        processing_time = time.time() - start_time
        logger.info(f"OCR completed. Text length: {len(extracted_text)}, Confidence: {confidence:.2f}, Time: {processing_time:.2f}s")
        
        return DetailedOcrResponse(
            text=extracted_text,
            model="PaddleOCR-Vietnamese",
            success=True,
            error=None,
            confidence=confidence,
            text_blocks=text_blocks if format == "json" else None,
            processing_time=processing_time
        )
        
    except Exception as e:
        error_msg = f"Error during OCR processing: {str(e)}"
        logger.error(error_msg)
        return DetailedOcrResponse(
            text="", 
            model="PaddleOCR-Vietnamese", 
            success=False, 
            error=error_msg
        )

@app.post("/ocr/url", response_model=DetailedOcrResponse)
async def ocr_from_url(request: UrlOcrRequest):
    """
    Nhận diện văn bản từ URL hình ảnh
    """
    start_time = time.time()
    
    logger.info(f"OCR URL request received for: {request.url}")
    
    # Kiểm tra xem OCR đã được khởi tạo chưa
    if ocr is None:
        return DetailedOcrResponse(
            text="", 
            model="PaddleOCR-Vietnamese", 
            success=False, 
            error="OCR engine not initialized"
        )
    
    try:
        # Tải hình ảnh từ URL
        image_bytes = await download_image_from_url(str(request.url))
        logger.info(f"Image size from URL: {len(image_bytes)} bytes")
        
        # Tiền xử lý hình ảnh
        img_array = preprocess_image(image_bytes)
        logger.info(f"Image shape from URL: {img_array.shape}")
        
        # Thực hiện OCR
        logger.info("Starting OCR processing for URL image...")
        results = ocr.ocr(img_array, cls=True)
        
        # Trích xuất văn bản từ kết quả
        extracted_text, confidence, text_blocks = extract_text_from_results(results[0] if results else [])
        
        if not extracted_text.strip():
            extracted_text = "Không phát hiện văn bản rõ ràng trong hình ảnh"
            confidence = 0.0
            text_blocks = []
        
        processing_time = time.time() - start_time
        logger.info(f"OCR URL completed. Text length: {len(extracted_text)}, Confidence: {confidence:.2f}, Time: {processing_time:.2f}s")
        
        return DetailedOcrResponse(
            text=extracted_text,
            model="PaddleOCR-Vietnamese",
            success=True,
            error=None,
            confidence=confidence,
            text_blocks=text_blocks if request.format == "json" else None,
            processing_time=processing_time
        )
        
    except Exception as e:
        error_msg = f"Error during OCR processing from URL: {str(e)}"
        logger.error(error_msg)
        return DetailedOcrResponse(
            text="", 
            model="PaddleOCR-Vietnamese", 
            success=False, 
            error=error_msg
        )

@app.get("/languages")
async def get_supported_languages():
    """
    Trả về danh sách ngôn ngữ được hỗ trợ
    """
    return {
        "languages": ["vi", "en"], 
        "message": "PaddleOCR supports Vietnamese and English text recognition",
        "primary": "vi"
    }

@app.get("/")
async def root():
    return {
        "message": "Vietnamese OCR Service with PaddleOCR", 
        "version": "2.0.0",
        "endpoints": {
            "/ocr": "POST - Upload image for OCR processing",
            "/ocr/url": "POST - Process image from URL",
            "/health": "GET - Health check",
            "/languages": "GET - Supported languages"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
