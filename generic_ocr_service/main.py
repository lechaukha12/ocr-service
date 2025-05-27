from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
from PIL import Image, ImageDraw
import io
import numpy as np
from contextlib import asynccontextmanager
import logging
import traceback
import os
import cv2

from paddleocr import PaddleOCR
from vietocr.tool.predictor import Predictor as VietOCRPredictor
from vietocr.tool.config import Cfg as VietOCRConfig

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

paddle_ocr_instance = None
viet_ocr_predictor_instance = None

VIETOCR_MODEL_PATH = "/app/model/seq2seqocr.pth"

def warp_and_prepare_for_vietocr(original_pil_image: Image.Image, box_coords) -> Image.Image | None:
    try:
        frame_cv = np.array(original_pil_image.convert('RGB')) 
        
        if not (isinstance(box_coords, list) and len(box_coords) == 4 and \
                all(isinstance(pt, (list, np.ndarray, tuple)) and len(pt) == 2 for pt in box_coords)):
            logger.warning(f"Invalid box_coords structure for warping: {box_coords}")
            return None

        pt_A = (float(box_coords[0][0]), float(box_coords[0][1]))
        pt_D = (float(box_coords[1][0]), float(box_coords[1][1]))
        pt_C = (float(box_coords[2][0]), float(box_coords[2][1]))
        pt_B = (float(box_coords[3][0]), float(box_coords[3][1]))

        width_AD = np.sqrt(((pt_A[0] - pt_D[0]) ** 2) + ((pt_A[1] - pt_D[1]) ** 2))
        width_BC = np.sqrt(((pt_B[0] - pt_C[0]) ** 2) + ((pt_B[1] - pt_C[1]) ** 2))
        maxWidth = max(int(width_AD), int(width_BC))

        height_AB = np.sqrt(((pt_A[0] - pt_B[0]) ** 2) + ((pt_A[1] - pt_B[1]) ** 2))
        height_CD = np.sqrt(((pt_C[0] - pt_D[0]) ** 2) + ((pt_C[1] - pt_D[1]) ** 2))
        maxHeight = max(int(height_AB), int(height_CD))

        if maxWidth <= 0 or maxHeight <= 0:
            logger.warning(f"Invalid maxWidth or maxHeight for warping: {maxWidth}, {maxHeight} from box {box_coords}")
            return None

        input_pts = np.float32([pt_A, pt_B, pt_C, pt_D])
        output_pts = np.float32([[0, 0],
                                [0, maxHeight - 1],
                                [maxWidth - 1, maxHeight - 1],
                                [maxWidth - 1, 0]])

        M = cv2.getPerspectiveTransform(input_pts, output_pts)
        matWarped_cv = cv2.warpPerspective(frame_cv, M, (maxWidth, maxHeight), flags=cv2.INTER_LINEAR)
        
        img_warped_pil = Image.fromarray(cv2.cvtColor(matWarped_cv, cv2.COLOR_BGR2RGB))
        return img_warped_pil

    except Exception as e:
        logger.error(f"Error during warping image for VietOCR: {e}", exc_info=True)
        return None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global paddle_ocr_instance, viet_ocr_predictor_instance
    
    logger.info("Lifespan: Initializing PaddleOCR...")
    try:
        paddle_ocr_instance = PaddleOCR(use_angle_cls=False, lang='vi')
        logger.info("Lifespan: PaddleOCR instance created successfully.")
    except Exception as e:
        logger.error(f"Lifespan: Fatal - Error initializing PaddleOCR: {e}", exc_info=True)
        paddle_ocr_instance = None

    logger.info("Lifespan: Attempting to load VietOCR model (vgg_seq2seq)...")
    try:
        logger.info(f"Checking for VietOCR model at: {VIETOCR_MODEL_PATH}")
        if not os.path.exists(VIETOCR_MODEL_PATH):
            logger.error(f"VietOCR weights file NOT FOUND at {VIETOCR_MODEL_PATH}! VietOCR will not be initialized.")
            viet_ocr_predictor_instance = None
        else:
            logger.info(f"VietOCR weights file found at {VIETOCR_MODEL_PATH}.")
            config = VietOCRConfig.load_config_from_name('vgg_seq2seq')
            logger.info("VietOCR config 'vgg_seq2seq' loaded.")
            config['weights'] = VIETOCR_MODEL_PATH
            config['cnn']['pretrained'] = False
            config['device'] = 'cpu' 
            config['predictor']['beamsearch'] = False
            logger.info("VietOCR config prepared. Initializing VietOCR predictor...")
            viet_ocr_predictor_instance = VietOCRPredictor(config)
            logger.info("Lifespan: VietOCR instance (vgg_seq2seq) created successfully.")
    except Exception as e:
        logger.error(f"Lifespan: Fatal - Error initializing VietOCR: {e}", exc_info=True)
        viet_ocr_predictor_instance = None
        
    yield
    
    logger.info("Lifespan: Generic OCR Service (Hybrid) shutting down.")
    paddle_ocr_instance = None
    viet_ocr_predictor_instance = None

app = FastAPI(title="Generic OCR Service (Hybrid - PaddleOCR + VietOCR)", lifespan=lifespan)

@app.post("/ocr/image/", tags=["OCR"])
async def ocr_image(
    file: UploadFile = File(...)
):
    global paddle_ocr_instance, viet_ocr_predictor_instance

    if paddle_ocr_instance is None:
        logger.error("OCR endpoint: PaddleOCR model is not available.")
        if viet_ocr_predictor_instance is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="CRITICAL: Both PaddleOCR and VietOCR models are not available."
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PaddleOCR model not available, cannot proceed with primary OCR."
        )

    if not file.content_type or not file.content_type.startswith("image/"):
        logger.warning(f"OCR endpoint: Unsupported media type: {file.content_type} for file: {file.filename}")
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported media type.")

    filename_for_log = file.filename if file.filename else "unknown_file"
    
    try:
        image_bytes = await file.read()
        if not image_bytes:
            logger.warning(f"OCR endpoint: Received empty file: {filename_for_log}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file.")

        img_pil_original = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        
        MAX_DIMENSION = 2048
        img_pil_for_paddle = img_pil_original.copy()
        if img_pil_for_paddle.width > MAX_DIMENSION or img_pil_for_paddle.height > MAX_DIMENSION:
            img_pil_for_paddle.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)
            logger.info(f"OCR endpoint: Image for PaddleOCR resized to: {img_pil_for_paddle.size}")

        image_np_rgb = np.array(img_pil_for_paddle)
        image_np_bgr = image_np_rgb[:, :, ::-1] 

        paddle_ocr_lines_data = []
        
        logger.info(f"OCR endpoint: Processing with PaddleOCR for file: {filename_for_log}")
        try:
            paddle_raw_result = paddle_ocr_instance.ocr(image_np_bgr)
            logger.info(f"PADDLEOCR RAW RESULT for {filename_for_log}: {str(paddle_raw_result)[:1500]}...")

            if paddle_raw_result and len(paddle_raw_result) > 0 and paddle_raw_result[0] is not None:
                ocr_output_data = paddle_raw_result[0]

                if isinstance(ocr_output_data, dict):
                    logger.info(f"PaddleOCR output is a dictionary. Keys: {list(ocr_output_data.keys())}")
                    if 'rec_texts' in ocr_output_data and isinstance(ocr_output_data['rec_texts'], list) and \
                       'dt_polys' in ocr_output_data and isinstance(ocr_output_data['dt_polys'], list):
                        
                        texts = ocr_output_data['rec_texts']
                        boxes = ocr_output_data['dt_polys']
                        scores = ocr_output_data.get('rec_scores', [None] * len(texts)) 

                        if len(texts) == len(boxes):
                            for i, text_line in enumerate(texts):
                                if isinstance(text_line, str):
                                    paddle_ocr_lines_data.append({
                                        "box": boxes[i], 
                                        "text_paddle": text_line,
                                        "text_final": text_line, 
                                        "score_paddle": scores[i] if i < len(scores) else None
                                    })
                            logger.info(f"Processed {len(paddle_ocr_lines_data)} lines from PaddleOCR (dict output 'rec_texts' & 'dt_polys').")
                        else:
                            logger.warning("Mismatch in lengths of 'rec_texts' and 'dt_polys' from PaddleOCR dict.")
                    else:
                        logger.warning("PaddleOCR output is a dict but 'rec_texts' or 'dt_polys' key is missing, not a list, or structure is unexpected.")
                
                elif isinstance(ocr_output_data, list): 
                    logger.info("PaddleOCR output is a list of lines. Processing standard format.")
                    for line_info in ocr_output_data: 
                        if isinstance(line_info, list) and len(line_info) == 2 and \
                           isinstance(line_info[0], list) and \
                           isinstance(line_info[1], tuple) and len(line_info[1]) >= 1 and \
                           isinstance(line_info[1][0], str):
                            box_coords = line_info[0] 
                            text = line_info[1][0]
                            score = line_info[1][1] if len(line_info[1]) > 1 else None
                            paddle_ocr_lines_data.append({
                                "box": box_coords,
                                "text_paddle": text,
                                "text_final": text, 
                                "score_paddle": score
                            })
                        else:
                            logger.warning(f"Unexpected line_info structure in PaddleOCR list output: {str(line_info)[:100]}")
                else:
                    logger.warning(f"PaddleOCR output (result[0]) is neither a dict nor a list. Type: {type(ocr_output_data)}")
            
            if not paddle_ocr_lines_data:
                 logger.warning(f"No text lines extracted by PaddleOCR for {filename_for_log}. Check RAW RESULT log.")

        except Exception as predict_err:
            logger.error(f"OCR endpoint: EXCEPTION during PaddleOCR for file {filename_for_log}", exc_info=True)
            pass 

        if viet_ocr_predictor_instance and paddle_ocr_lines_data:
            logger.info(f"Attempting to refine {len(paddle_ocr_lines_data)} lines with VietOCR...")
            for i, line_data in enumerate(paddle_ocr_lines_data):
                box_coordinates = line_data.get("box")
                paddle_text = line_data.get("text_paddle", "")
                
                should_refine_with_vietocr = True 

                # SỬA LỖI ValueError:
                if should_refine_with_vietocr and box_coordinates is not None and len(box_coordinates) > 0:
                    img_roi_pil_warped = warp_and_prepare_for_vietocr(img_pil_original, box_coordinates)
                    
                    if img_roi_pil_warped:
                        try:
                            vietocr_text_roi = viet_ocr_predictor_instance.predict(img_roi_pil_warped)
                            logger.info(f"Line {i}, Paddle: '{paddle_text}', VietOCR_ROI: '{vietocr_text_roi}'")
                            if vietocr_text_roi and isinstance(vietocr_text_roi, str) and len(vietocr_text_roi.strip()) > 0:
                                paddle_ocr_lines_data[i]["text_final"] = vietocr_text_roi.strip() 
                                paddle_ocr_lines_data[i]["refined_by_vietocr"] = True
                        except Exception as e_vietocr:
                            logger.error(f"Error during VietOCR predict for ROI {i}: {e_vietocr}", exc_info=False) 
                    else:
                        logger.warning(f"Failed to warp ROI {i} for VietOCR.")
        elif not viet_ocr_predictor_instance:
            logger.warning("VietOCR instance not available, skipping refinement step.")
        elif not paddle_ocr_lines_data:
            logger.warning("No lines from PaddleOCR to refine with VietOCR.")


        final_text_list = [line.get("text_final", "") for line in paddle_ocr_lines_data]
        final_text_combined = "\n".join(final_text_list).strip()
        
        logger.info(f"Hybrid OCR processing complete. Final text length: {len(final_text_combined)}")

        return JSONResponse(content={
            "filename": filename_for_log, 
            "text": final_text_combined,
            })

    except HTTPException as e:
        logger.error(f"OCR endpoint: HTTPException occurred for file {filename_for_log}: {e.detail}", exc_info=True)
        raise e
    except Exception as e:
        logger.error(f"OCR endpoint: Critical error during processing for file {filename_for_log}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {type(e).__name__} - {str(e)}"
        )
    finally:
        if file and hasattr(file, 'close'):
             try:
                 await file.close()
             except Exception as e_close:
                 logger.warning(f"OCR endpoint: Error closing file {filename_for_log}: {e_close}")


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    global paddle_ocr_instance, viet_ocr_predictor_instance
    status_paddle = "OK" if paddle_ocr_instance else "Not loaded"
    status_vietocr = "OK" if viet_ocr_predictor_instance else "Not loaded"
    
    if paddle_ocr_instance and viet_ocr_predictor_instance:
        return {"status": "healthy", "message": f"Hybrid OCR Service: PaddleOCR ({status_paddle}), VietOCR ({status_vietocr}). Both ready."}
    elif paddle_ocr_instance:
        return {"status": "partially_healthy", "message": f"Hybrid OCR Service: PaddleOCR ({status_paddle}), VietOCR ({status_vietocr}). VietOCR failed to load."}
    elif viet_ocr_predictor_instance:
        return {"status": "partially_healthy", "message": f"Hybrid OCR Service: PaddleOCR ({status_paddle}), VietOCR ({status_vietocr}). PaddleOCR failed to load."}
    else:
        return {"status": "unhealthy", "message": "Hybrid OCR Service: Both PaddleOCR and VietOCR failed to load."}