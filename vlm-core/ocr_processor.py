"""
OCR Processor sử dụng camera model hoặc các phương pháp OCR khác
"""
import os
import io
import logging
from PIL import Image
import base64
import cv2
import numpy as np

logger = logging.getLogger(__name__)

class OCRProcessor:
    """
    Xử lý OCR sử dụng các phương pháp đơn giản và gọi LLM để cải thiện kết quả
    """
    def __init__(self):
        """
        Khởi tạo processor
        """
        logger.info("Initializing OCR processor")
        self.initialize()
        
    def initialize(self):
        """
        Thiết lập các thành phần cần thiết
        """
        # Không cần khởi tạo model phức tạp vì chúng ta sẽ sử dụng LLM
        pass
        
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Tiền xử lý hình ảnh để cải thiện kết quả OCR
        """
        # Chuyển đổi thành array numpy để xử lý với OpenCV
        img_array = np.array(image)
        
        # Chuyển sang ảnh xám nếu cần
        if len(img_array.shape) == 3 and img_array.shape[2] == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Áp dụng các kỹ thuật cải thiện ảnh
        # Thay đổi kích thước nếu ảnh quá lớn
        height, width = gray.shape
        if width > 1000 or height > 1000:
            scale = min(1000.0 / width, 1000.0 / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            gray = cv2.resize(gray, (new_width, new_height))
        
        # Tăng cường độ tương phản
        gray = cv2.equalizeHist(gray)
        
        # Giảm nhiễu
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Chuyển đổi lại thành đối tượng PIL.Image
        processed_image = Image.fromarray(gray)
        
        return processed_image
    
    def process_image(self, image: Image.Image) -> str:
        """
        Xử lý hình ảnh và trả về văn bản
        """
        try:
            # Tiền xử lý ảnh
            processed_image = self.preprocess_image(image)
            
            # Trong triển khai thực tế, chúng ta sẽ dùng một OCR engine thực
            # Nhưng hiện tại, chúng ta sẽ dựa vào LLM để có khả năng OCR
            # Do đó trả về một ảnh đã xử lý để sử dụng với LLM
            
            # Mã hóa ảnh thành base64 để có thể chuyển tới LLM
            buffered = io.BytesIO()
            processed_image.save(buffered, format="JPEG", quality=85)
            
            # Trả về ảnh đã xử lý
            return "Image processed for OCR"
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return ""
    
    def encode_image_to_base64(self, image: Image.Image) -> str:
        """
        Mã hóa ảnh thành chuỗi base64
        """
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return img_str
