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
    """Cố gắng làm thẳng ảnh dựa trên các đường văn bản."""
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    
    # Thử làm mờ nhẹ để giảm nhiễu trước khi tìm góc
    # blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Nhị phân hóa ảnh để tìm các thành phần text
    # _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    # Sử dụng adaptive threshold có thể tốt hơn cho ảnh không đồng đều
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 11, 2)

    # Tìm các đường bao của các vùng text
    contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return image_cv # Không có contour, không làm gì cả

    angles = []
    for contour in contours:
        # Chỉ xử lý các contour có diện tích đủ lớn để tránh nhiễu
        if cv2.contourArea(contour) < 100: # Ngưỡng diện tích có thể cần điều chỉnh
            continue
        rect = cv2.minAreaRect(contour)
        angle = rect[-1]
        # Chuẩn hóa góc về khoảng (-45, 45]
        if angle < -45:
            angle = 90 + angle
        # Chỉ xem xét các góc nhỏ, tránh xoay quá mạnh do các thành phần không phải text
        if abs(angle) < 30 and abs(angle) > 0.5 : # Ngưỡng góc có thể cần điều chỉnh
             angles.append(angle)

    if not angles:
        return image_cv # Không có góc phù hợp để xoay

    # Lấy góc trung vị để giảm ảnh hưởng của các giá trị ngoại lai
    median_angle = np.median(angles)
    
    # print(f"Deskew: Detected median angle: {median_angle:.2f} degrees")

    if abs(median_angle) < 0.5: # Nếu góc quá nhỏ, không cần xoay
        return image_cv

    (h, w) = image_cv.shape[:2]
    center = (w // 2, h // 2)
    # Lưu ý: cv2.getRotationMatrix2D nhận góc dương cho xoay ngược chiều kim đồng hồ
    # Góc từ minAreaRect có thể cần điều chỉnh dấu tùy theo cách nó được tính toán
    # Nếu median_angle là góc nghiêng của text, chúng ta muốn xoay ngược lại
    rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    
    # Tính toán kích thước bao mới để chứa toàn bộ ảnh sau khi xoay
    abs_cos = abs(rotation_matrix[0,0]) 
    abs_sin = abs(rotation_matrix[0,1])
    new_w = int(h * abs_sin + w * abs_cos)
    new_h = int(h * abs_cos + w * abs_sin)

    # Điều chỉnh ma trận xoay để tính đến việc thay đổi kích thước và dịch chuyển
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
            # print("Không thể decode ảnh bằng OpenCV.")
            return Image.open(io.BytesIO(image_bytes)) # Fallback

        # 0. (Tùy chọn) Deskew - Làm thẳng ảnh
        # img_cv = deskew_image(img_cv) # Có thể tốn thời gian và không phải lúc nào cũng hiệu quả

        # 1. Resize ảnh để có chiều rộng tối ưu cho OCR, giữ tỷ lệ khung hình
        if target_width:
            (h, w) = img_cv.shape[:2]
            if w != target_width:
                r = target_width / float(w)
                dim = (target_width, int(h * r))
                img_cv = cv2.resize(img_cv, dim, interpolation=cv2.INTER_LANCZOS4) # Lanczos cho chất lượng tốt hơn khi resize

        # 2. Chuyển sang ảnh xám
        gray_img = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

        # 3. Khử nhiễu
        # Tùy chọn A: Median Blur (tốt cho nhiễu salt-and-pepper)
        # denoised_img = cv2.medianBlur(gray_img, 3) 
        # Tùy chọn B: Gaussian Blur (làm mờ nhiễu Gauss)
        # denoised_img = cv2.GaussianBlur(gray_img, (3, 3), 0)
        # Tùy chọn C: FastNlMeansDenoising (mạnh hơn nhưng chậm hơn)
        denoised_img = cv2.fastNlMeansDenoising(gray_img, None, h=10, templateWindowSize=7, searchWindowSize=21)
        
        current_img_to_process = denoised_img

        # 4. Tăng cường độ tương phản (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        contrast_enhanced_img = clahe.apply(current_img_to_process)
        current_img_to_process = contrast_enhanced_img
        
        # 5. (Tùy chọn) Làm nét ảnh sau khi khử nhiễu và tăng tương phản
        # kernel_sharpening = np.array([[-1,-1,-1], 
        #                               [-1, 9,-1],
        #                               [-1,-1,-1]])
        # sharpened_img = cv2.filter2D(current_img_to_process, -1, kernel_sharpening)
        # current_img_to_process = sharpened_img


        # 6. Nhị phân hóa ảnh
        # Adaptive Thresholding thường tốt cho điều kiện ánh sáng không đồng đều
        binary_img = cv2.adaptiveThreshold(
            current_img_to_process, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, # Chữ trắng trên nền đen
            blockSize=15, # Nên là số lẻ, thử nghiệm các giá trị khác nhau (ví dụ 11, 13, 15, 17)
            C=9           # Hằng số trừ đi, thử nghiệm (ví dụ 5, 7, 9)
        )
        
        # 7. (Tùy chọn) Dọn dẹp ảnh nhị phân bằng phép toán hình thái
        # kernel_size = 1 # Kernel rất nhỏ để không làm mất chữ
        # kernel = np.ones((kernel_size,kernel_size),np.uint8)
        # opened_img = cv2.morphologyEx(binary_img, cv2.MORPH_OPEN, kernel, iterations=1) # Loại bỏ nhiễu nhỏ
        # closed_img = cv2.morphologyEx(opened_img, cv2.MORPH_CLOSE, kernel, iterations=1) # Nối các phần chữ bị đứt
        # final_img_to_ocr = closed_img
        
        final_img_to_ocr = binary_img # Sử dụng ảnh đã nhị phân hóa trực tiếp

        # Lưu ảnh đã xử lý để kiểm tra (chỉ dùng khi debug)
        # cv2.imwrite("processed_ocr_image.png", final_img_to_ocr)

        processed_pil_img = Image.fromarray(final_img_to_ocr)
        return processed_pil_img
        
    except Exception as e:
        # print(f"Lỗi nghiêm trọng trong quá trình tiền xử lý ảnh: {type(e).__name__} - {e}")
        # Trong trường hợp lỗi, trả về ảnh gốc để Tesseract vẫn có thể thử
        try:
            return Image.open(io.BytesIO(image_bytes))
        except Exception: # Nếu ngay cả việc mở ảnh gốc cũng lỗi
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể xử lý file ảnh đầu vào.")


@app.post("/ocr/image/", tags=["OCR"])
async def ocr_image(
    file: UploadFile = File(...), 
    lang: Optional[str] = Form("vie"),
    psm: Optional[str] = Form("3") # Mặc định PSM 3 có thể tốt hơn cho layout tự động
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File provided is not an image or content type is missing."
        )

    try:
        image_bytes = await file.read()
        
        processed_img_pil = preprocess_image_for_ocr(image_bytes)
        
        # Cấu hình Tesseract
        # --oem 3: LSTM OCR engine.
        # --dpi 300: Gợi ý DPI cho Tesseract (mặc dù ảnh đã được resize)
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

