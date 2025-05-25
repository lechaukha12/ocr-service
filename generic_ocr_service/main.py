from fastapi import FastAPI, File, UploadFile, HTTPException, status, Form
from fastapi.responses import JSONResponse
from PIL import Image 
import io
import os
from typing import Optional
# import cv2 # Chỉ cần nếu dùng deskew_image (hiện không dùng trong luồng chính)
# import numpy as np # Chỉ cần nếu dùng cv2 (hiện không dùng trong luồng chính)
from contextlib import asynccontextmanager
import logging 
import traceback # Để in traceback chi tiết

from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ocr_predictor_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global ocr_predictor_instance
    logger.info("Lifespan: Attempting to load VietOCR model...")
    print("[DEBUG] Lifespan: Attempting to load VietOCR model...", flush=True)
    try:
        # Sử dụng lại model 'vgg_transformer' vì 'resnet_transformer' gây lỗi config
        config = Cfg.load_config_from_name('vgg_transformer') 
        logger.info("Lifespan: VietOCR Cfg 'vgg_transformer' loaded.")
        print("[DEBUG] Lifespan: VietOCR Cfg 'vgg_transformer' loaded.", flush=True)
    except Exception as e:
        logger.error(f"Lifespan: Fatal - Error loading VietOCR config 'vgg_transformer': {e}", exc_info=True)
        print(f"[DEBUG] Lifespan: Fatal - Error loading VietOCR config: {e}", flush=True)
        traceback.print_exc()
        ocr_predictor_instance = None 
        yield 
        return

    config['device'] = 'cpu'
    logger.info(f"Lifespan: VietOCR config device set to: {config['device']}")
    print(f"[DEBUG] Lifespan: VietOCR config device set to: {config['device']}", flush=True)

    try:
        ocr_predictor_instance = Predictor(config)
        logger.info("Lifespan: VietOCR Predictor instance created successfully on CPU.")
        print("[DEBUG] Lifespan: VietOCR Predictor instance created successfully on CPU.", flush=True)
    except Exception as e:
        logger.error(f"Lifespan: Fatal - Error initializing VietOCR Predictor: {e}", exc_info=True)
        print(f"[DEBUG] Lifespan: Fatal - Error initializing VietOCR Predictor: {e}", flush=True)
        traceback.print_exc()
        ocr_predictor_instance = None 

    yield

    logger.info("Lifespan: Generic OCR Service (VietOCR) shutting down.")
    print("[DEBUG] Lifespan: Generic OCR Service (VietOCR) shutting down.", flush=True)
    ocr_predictor_instance = None

app = FastAPI(title="Generic OCR Service (VietOCR)", lifespan=lifespan)

@app.post("/ocr/image/", tags=["OCR"])
async def ocr_image(
    file: UploadFile = File(...)
):
    global ocr_predictor_instance
    if ocr_predictor_instance is None:
        logger.error("OCR endpoint: VietOCR model is not available (ocr_predictor_instance is None).")
        print("[DEBUG] OCR endpoint: VietOCR model is not available.", flush=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="VietOCR model is not available or failed to load. Check service logs."
        )

    if not file.content_type or not file.content_type.startswith("image/"):
        logger.warning(f"OCR endpoint: Unsupported media type: {file.content_type} for file: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File provided is not an image or content type is missing. Received: {file.content_type}"
        )

    filename_for_log = file.filename if file else "unknown_file"
    logger.info(f"OCR endpoint: Processing OCR request for file: {filename_for_log}")
    print(f"[DEBUG] OCR endpoint: Processing OCR request for file: {filename_for_log}", flush=True)

    try:
        image_bytes = await file.read()
        if not image_bytes:
            logger.warning(f"OCR endpoint: Received empty file: {filename_for_log}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Received an empty file.")

        logger.info(f"OCR endpoint: Read {len(image_bytes)} bytes from file: {filename_for_log}")
        print(f"[DEBUG] OCR endpoint: Read {len(image_bytes)} bytes from file: {filename_for_log}", flush=True)

        img_pil = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        logger.info(f"OCR endpoint: Image {filename_for_log} loaded into PIL, mode: {img_pil.mode}, size: {img_pil.size}")
        print(f"[DEBUG] OCR endpoint: Image {filename_for_log} loaded into PIL, mode: {img_pil.mode}, size: {img_pil.size}", flush=True)

        MAX_DIMENSION = 1024 
        if img_pil.width > MAX_DIMENSION or img_pil.height > MAX_DIMENSION:
            logger.info(f"OCR endpoint: Image {filename_for_log} is large ({img_pil.size}), resizing to max dimension {MAX_DIMENSION} while maintaining aspect ratio...")
            print(f"[DEBUG] OCR endpoint: Image {filename_for_log} is large ({img_pil.size}), resizing to max dimension {MAX_DIMENSION}", flush=True)
            img_pil.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)
            logger.info(f"OCR endpoint: Image {filename_for_log} resized to: {img_pil.size}")
            print(f"[DEBUG] OCR endpoint: Image {filename_for_log} resized to: {img_pil.size}", flush=True)

        text_result = "Error during prediction or prediction did not run." 
        print(f"[DEBUG] OCR endpoint: >>> PREPARING TO CALL VietOCR.predict() for {filename_for_log} (size: {img_pil.size})", flush=True)
        logger.info(f"OCR endpoint: Attempting VietOCR.predict() for {filename_for_log} (size after potential resize: {img_pil.size})...")

        try:
            text_result = ocr_predictor_instance.predict(img_pil)
            print(f"[DEBUG] OCR endpoint: <<< VietOCR.predict() CALL COMPLETED for {filename_for_log}. Result type: {type(text_result)}", flush=True)
            logger.info(f"OCR endpoint: VietOCR.predict() call completed for {filename_for_log}. Text length: {len(text_result if text_result else '')}")
        except Exception as predict_err:
            print(f"[DEBUG] OCR endpoint: !!!! EXCEPTION during VietOCR.predict(): {predict_err}", flush=True)
            logger.error(f"OCR endpoint: EXCEPTION during VietOCR.predict() for file {filename_for_log}", exc_info=True)
            traceback.print_exc() 
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error during VietOCR prediction: {type(predict_err).__name__}"
            )

        return JSONResponse(content={"filename": filename_for_log, "text": text_result.strip() if text_result else ""})

    except HTTPException as e: 
        logger.error(f"OCR endpoint: HTTPException occurred for file {filename_for_log}: {e.detail}", exc_info=True)
        raise e
    except Exception as e: 
        logger.error(f"OCR endpoint: Critical error during VietOCR processing for file {filename_for_log}", exc_info=True)
        traceback.print_exc() 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during VietOCR processing: {type(e).__name__}"
        )
    finally:
        if file and hasattr(file, 'file') and hasattr(file.file, 'closed') and not file.file.closed:
             try:
                 await file.close()
             except Exception as e_close:
                 logger.warning(f"OCR endpoint: Error closing file {filename_for_log}: {e_close}")


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    global ocr_predictor_instance
    if ocr_predictor_instance:
        logger.info("Health check: VietOCR model instance exists.")
        return {"status": "healthy", "message": "Generic OCR Service (VietOCR) is running and model instance exists!"}
    else:
        logger.error("Health check: VietOCR model instance is None.")
        return {"status": "unhealthy", "message": "Generic OCR Service (VietOCR) is running BUT VietOCR model failed to load or not initialized."}