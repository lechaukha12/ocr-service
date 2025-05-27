from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
from PIL import Image
import io
import numpy as np
from contextlib import asynccontextmanager
import logging
import traceback
from paddleocr import PaddleOCR

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ocr_predictor_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global ocr_predictor_instance
    logger.info("Lifespan: Attempting to load PaddleOCR model...")
    try:
        ocr_predictor_instance = PaddleOCR(use_angle_cls=False, lang='vi')
        logger.info("Lifespan: PaddleOCR instance created successfully.")
    except Exception as e:
        logger.error(f"Lifespan: Fatal - Error initializing PaddleOCR Predictor: {e}", exc_info=True)
        ocr_predictor_instance = None
    yield
    logger.info("Lifespan: Generic OCR Service (PaddleOCR) shutting down.")
    ocr_predictor_instance = None

app = FastAPI(title="Generic OCR Service (PaddleOCR)", lifespan=lifespan)

@app.post("/ocr/image/", tags=["OCR"])
async def ocr_image(
    file: UploadFile = File(...)
):
    global ocr_predictor_instance
    if ocr_predictor_instance is None:
        logger.error("OCR endpoint: PaddleOCR model is not available (ocr_predictor_instance is None).")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PaddleOCR model is not available or failed to load. Check service logs."
        )

    if not file.content_type or not file.content_type.startswith("image/"):
        logger.warning(f"OCR endpoint: Unsupported media type: {file.content_type} for file: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File provided is not an image or content type is missing. Received: {file.content_type}"
        )

    filename_for_log = file.filename if file.filename else "unknown_file"
    logger.info(f"OCR endpoint: Processing OCR request for file: {filename_for_log}")

    try:
        image_bytes = await file.read()
        if not image_bytes:
            logger.warning(f"OCR endpoint: Received empty file: {filename_for_log}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Received an empty file.")

        img_pil = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        
        MAX_DIMENSION = 2048
        if img_pil.width > MAX_DIMENSION or img_pil.height > MAX_DIMENSION:
            img_pil.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)
            logger.info(f"OCR endpoint: Image {filename_for_log} resized to: {img_pil.size}")

        image_np_rgb = np.array(img_pil)
        image_np_bgr = image_np_rgb[:, :, ::-1] 

        full_text_list = []
        try:
            result = ocr_predictor_instance.ocr(image_np_bgr)
            logger.info(f"PADDLEOCR RAW RESULT for {filename_for_log}: {result}")

            if result and len(result) > 0 and result[0] is not None:
                ocr_data_for_image = result[0] 

                if isinstance(ocr_data_for_image, dict):
                    if 'rec_texts' in ocr_data_for_image and isinstance(ocr_data_for_image['rec_texts'], list):
                        raw_texts = ocr_data_for_image['rec_texts']
                        if all(isinstance(item, str) for item in raw_texts): # Nếu là list của string
                             full_text_list.extend(raw_texts)
                        # Nếu 'rec_texts' chứa list của list (trường hợp box, text, score trong một sublist)
                        elif all(isinstance(item, list) and len(item) >= 2 and isinstance(item[1], tuple) and len(item[1]) >0 and isinstance(item[1][0], str) for item in raw_texts):
                            for item_line in raw_texts:
                                full_text_list.append(item_line[1][0])
                        else: # Cấu trúc khác không rõ trong 'rec_texts'
                            logger.warning(f"Content of 'rec_texts' is not a simple list of strings or expected line structures. Content: {raw_texts[:5]}")
                        logger.info(f"Extracted text from dict key 'rec_texts'. Lines found: {len(full_text_list)}")
                    
                    # Thử kiểm tra cấu trúc thường thấy hơn: list của [box, (text, score)]
                    # Điều này có thể nằm trong một key khác, hoặc ocr_data_for_image có thể chính là list đó
                    # (nhưng logic ở trên đã kiểm tra ocr_data_for_image là dict)
                    # Phổ biến hơn là kết quả nhận dạng nằm trong một list các tuple (text, score)
                    # hoặc list các list [box, (text,score)]
                    # Ví dụ, nếu key 'structure_result' chứa các dòng text có cấu trúc:
                    elif 'structure_result' in ocr_data_for_image and isinstance(ocr_data_for_image['structure_result'], list):
                        for line_info in ocr_data_for_image['structure_result']:
                            if isinstance(line_info, list) and len(line_info) == 2 and \
                               isinstance(line_info[1], tuple) and len(line_info[1]) >= 1 and \
                               isinstance(line_info[1][0], str):
                                full_text_list.append(line_info[1][0])
                        logger.info(f"Extracted text from dict key 'structure_result'. Lines: {len(full_text_list)}")
                    else:
                        logger.warning(f"result[0] is a dict, but expected text keys ('rec_texts', 'structure_result', etc.) not found or in wrong format. Keys: {list(ocr_data_for_image.keys())}")
                
                elif isinstance(ocr_data_for_image, list): # Nếu result[0] là một list các dòng
                    logger.info("result[0] is a list, processing as list of lines (standard OCR output).")
                    for line_info in ocr_data_for_image:
                        if isinstance(line_info, list) and len(line_info) >= 1 : # Toàn bộ line_info
                            # line_info[0] là box, line_info[1] là (text, score)
                            if len(line_info) >=2 and isinstance(line_info[1], tuple) and len(line_info[1]) >= 1 and isinstance(line_info[1][0], str) :
                                full_text_list.append(line_info[1][0])
                            # Đôi khi một số phiên bản/model chỉ trả về text và score dưới dạng tuple trực tiếp trong list
                            elif isinstance(line_info, tuple) and len(line_info) >=1 and isinstance(line_info[0], str):
                                 full_text_list.append(line_info[0])
                            else:
                                logger.warning(f"Unexpected line_info structure in list: {line_info}")
                        # Nếu line_info là một tuple (text, score)
                        elif isinstance(line_info, tuple) and len(line_info) >= 1 and isinstance(line_info[0], str):
                            full_text_list.append(line_info[0])
                        else:
                             logger.warning(f"Unexpected item type in result[0] list: {type(line_info)}, item: {str(line_info)[:100]}")

                else:
                    logger.warning(f"result[0] is neither a dict nor a list. Type: {type(ocr_data_for_image)}. Value: {str(ocr_data_for_image)[:200]}")

            if not full_text_list: # Nếu không trích xuất được gì
                 logger.warning(f"full_text_list is empty after processing PaddleOCR result for {filename_for_log}. Check RAW RESULT log.")


            logger.info(f"OCR endpoint: PaddleOCR.ocr() call completed for {filename_for_log}. Lines extracted to full_text_list: {len(full_text_list)}")
        except Exception as predict_err:
            logger.error(f"OCR endpoint: EXCEPTION during PaddleOCR.ocr() for file {filename_for_log}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error during PaddleOCR prediction (ocr method): {type(predict_err).__name__} - {str(predict_err)}"
            )
        
        final_text = "\n".join(full_text_list).strip()
        return JSONResponse(content={"filename": filename_for_log, "text": final_text})

    except HTTPException as e:
        logger.error(f"OCR endpoint: HTTPException occurred for file {filename_for_log}: {e.detail}", exc_info=True)
        raise e
    except Exception as e:
        logger.error(f"OCR endpoint: Critical error during PaddleOCR processing for file {filename_for_log}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during image processing before OCR: {type(e).__name__} - {str(e)}"
        )
    finally:
        if file and hasattr(file, 'close'):
             try:
                 await file.close()
             except Exception as e_close:
                 logger.warning(f"OCR endpoint: Error closing file {filename_for_log}: {e_close}")


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    global ocr_predictor_instance
    if ocr_predictor_instance:
        logger.info("Health check: PaddleOCR model instance exists.")
        return {"status": "healthy", "message": "Generic OCR Service (PaddleOCR) is running and model instance exists!"}
    else:
        logger.error("Health check: PaddleOCR model instance is None.")
        return {"status": "unhealthy", "message": "Generic OCR Service (PaddleOCR) is running BUT PaddleOCR model failed to load or not initialized."}