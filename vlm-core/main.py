"""
vlm-core service - Dịch vụ sử dụng Gemma 3 để OCR và eKYC
"""
import os
import io
import time
import logging
import base64
import asyncio
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import httpx

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import các module ocr và llm
from ocr_processor import OCRProcessor
from llm_processor import LLMProcessor
from text_utils import extract_info_from_text, postprocess_vietnamese_text

# Khởi tạo FastAPI app
app = FastAPI(
    title="VLM Core OCR Service with Gemma 3",
    description="OCR và Extract Information từ hình ảnh sử dụng Gemma 3",
    version="1.0.0",
)

# Thêm CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo processors
try:
    # Sử dụng biến môi trường để cấu hình
    use_ollama = os.environ.get("USE_OLLAMA", "false").lower() == "true"
    use_local_model = os.environ.get("USE_LOCAL_MODEL", "true").lower() == "true"
    model_name = os.environ.get("MODEL_NAME", "distilgpt2")
    logger.info(f"Initializing LLM processor with model={model_name}, use_ollama={use_ollama}, use_local_model={use_local_model}")
    
    ocr_processor = OCRProcessor()
    llm_processor = LLMProcessor(model=model_name, use_ollama=use_ollama)
    logger.info("OCR and LLM processors initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize processors: {e}")
    ocr_processor = None
    llm_processor = None

# Schemas
class OCRRequest(BaseModel):
    image_url: Optional[str] = None
    language: str = "vie"

class OCRResult(BaseModel):
    text: str
    confidence: float = 0.0
    language: str
    processing_time: float

class ExtractedInfo(BaseModel):
    id_number: Optional[str] = None
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    place_of_origin: Optional[str] = None
    place_of_residence: Optional[str] = None
    expiry_date: Optional[str] = None
    document_type: Optional[str] = None
    raw_text: str
    confidence: float = 0.0

class HealthCheckResponse(BaseModel):
    status: str
    ocr_processor: str
    llm_processor: str
    version: str = "1.0.0"
    model: str = "distilgpt2"
    deployment_type: str = "container"

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Kiểm tra trạng thái hoạt động của service
    """
    ocr_status = "active" if ocr_processor is not None else "inactive" 
    llm_status = "active" if llm_processor is not None else "inactive"
    overall = "ok" if ocr_processor is not None and llm_processor is not None else "error"
    
    model_name = os.environ.get("MODEL_NAME", "google/gemma-3b")
    deployment_type = "container" if os.environ.get("USE_LOCAL_MODEL", "true").lower() == "true" else "ollama"
    
    return HealthCheckResponse(
        status=overall,
        ocr_processor=ocr_status,
        llm_processor=llm_status,
        model=model_name,
        deployment_type=deployment_type
    )

@app.post("/ocr", response_model=OCRResult)
async def perform_ocr(
    image: UploadFile = File(...),
    language: str = Form("vie"),
):
    """
    Thực hiện OCR trên hình ảnh được tải lên
    """
    start_time = time.time()
    
    if ocr_processor is None or llm_processor is None:
        raise HTTPException(status_code=503, detail="OCR service not initialized")
    
    try:
        content = await image.read()
        img = Image.open(io.BytesIO(content))
        
        # Thực hiện OCR qua processor
        logger.info(f"Processing image {image.filename} with OCR processor")
        ocr_text = ocr_processor.process_image(img)
        
        # Xử lý văn bản với LLM
        logger.info("Processing OCR text with LLM")
        enhanced_text = llm_processor.enhance_text(ocr_text, language)
        
        # Áp dụng hậu xử lý tiếng Việt
        if language.lower() in ["vi", "vie", "vietnamese"]:
            enhanced_text = postprocess_vietnamese_text(enhanced_text)
        
        processing_time = time.time() - start_time
        confidence = 0.9 if len(enhanced_text) > 10 else 0.5
        
        logger.info(f"OCR completed in {processing_time:.2f}s")
        
        return OCRResult(
            text=enhanced_text,
            confidence=confidence,
            language=language,
            processing_time=processing_time
        )
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract_info", response_model=ExtractedInfo)
async def extract_info(
    image: UploadFile = File(...),
    language: str = Form("vie"),
):
    """
    Thực hiện OCR và trích xuất thông tin từ CCCD/CMND
    """
    start_time = time.time()
    
    if ocr_processor is None or llm_processor is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        content = await image.read()
        img = Image.open(io.BytesIO(content))
        
        # Thực hiện OCR
        ocr_text = ocr_processor.process_image(img)
        
        # Xử lý văn bản với LLM
        enhanced_text = llm_processor.enhance_text(ocr_text, language)
        
        # Trích xuất thông tin từ văn bản
        extracted_info = llm_processor.extract_info(enhanced_text, language)
        extracted_info["raw_text"] = enhanced_text
        
        # Tính độ tin cậy
        confidence = 0.9 if len(enhanced_text) > 20 else 0.5
        extracted_info["confidence"] = confidence
        
        logger.info(f"Info extraction completed in {time.time() - start_time:.2f}s")
        
        return ExtractedInfo(**extracted_info)
    except Exception as e:
        logger.error(f"Error extracting info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/languages")
async def get_languages():
    """
    Trả về danh sách các ngôn ngữ được hỗ trợ
    """
    return {
        "languages": ["vie", "eng"],
        "default": "vie",
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8010))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
