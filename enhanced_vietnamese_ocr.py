#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script cải thiện độ chính xác nhận diện dấu tiếng Việt cho PaddleOCR
Bao gồm preprocessing, post-processing và fine-tuning parameters
"""

import os
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from paddleocr import PaddleOCR
import unicodedata
import re
import logging
from typing import Dict, List, Any, Tuple
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VietnameseOCREnhancer:
    def __init__(self):
        """Khởi tạo OCR với cấu hình tối ưu cho tiếng Việt"""
        self.ocr_configs = {
            # Cấu hình chính
            'primary': PaddleOCR(
                use_angle_cls=True, 
                lang='vi', 
                use_gpu=False, 
                show_log=False,
                det_limit_side_len=960,
                det_limit_type='max',
                rec_batch_num=6
            ),
            # Cấu hình cao cấp hơn
            'enhanced': PaddleOCR(
                use_angle_cls=True, 
                lang='vi', 
                use_gpu=False, 
                show_log=False,
                det_limit_side_len=1280,
                det_limit_type='max',
                rec_batch_num=1,
                det_db_thresh=0.3,
                det_db_box_thresh=0.5
            )
        }
        
        # Dictionary ánh xạ các ký tự bị nhận diện sai
        self.vietnamese_char_mapping = {
            # Các lỗi thường gặp với PaddleOCR
            'Döc': 'Độc',
            'Tudo': 'Tự do', 
            'Hanh phüc': 'Hạnh phúc',
            'phuc': 'phúc',
            'döc': 'độc',
            'tudo': 'tự do',
            'hanh': 'hạnh',
            'phüc': 'phúc',
            'lap': 'lập',
            # Thêm các mapping khác
            'a': 'á',  # context-dependent
            'e': 'ể',  # context-dependent  
            'o': 'ồ',  # context-dependent
            'u': 'ư',  # context-dependent
            'i': 'ị',  # context-dependent
            # Mapping với diacritics
            'ö': 'ồ',
            'ü': 'ư',
            'ä': 'ă',
            'ê': 'ề',
        }
        
        # Từ điển tiếng Việt phổ biến
        self.vietnamese_words = {
            'độc lập', 'tự do', 'hạnh phúc', 'việt nam', 'hồ chí minh',
            'thành phố', 'quận', 'phường', 'đường', 'số nhà',
            'điện thoại', 'email', 'website', 'công ty', 'doanh nghiệp'
        }

    def preprocess_image(self, image_path: str, method: str = 'enhanced') -> str:
        """Tiền xử lý ảnh để cải thiện OCR"""
        try:
            # Đọc ảnh
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Không thể đọc ảnh: {image_path}")
            
            # Convert to PIL
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            if method == 'enhanced':
                # Cải thiện độ tương phản
                enhancer = ImageEnhance.Contrast(pil_image)
                pil_image = enhancer.enhance(1.5)
                
                # Cải thiện độ sắc nét
                enhancer = ImageEnhance.Sharpness(pil_image)
                pil_image = enhancer.enhance(1.2)
                
                # Resize nếu ảnh quá nhỏ
                width, height = pil_image.size
                if width < 800 or height < 600:
                    scale = max(800/width, 600/height)
                    new_size = (int(width * scale), int(height * scale))
                    pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
            
            elif method == 'grayscale_enhanced':
                # Convert to grayscale
                pil_image = pil_image.convert('L')
                
                # Convert back to numpy
                np_image = np.array(pil_image)
                
                # Apply adaptive threshold
                np_image = cv2.adaptiveThreshold(
                    np_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY, 11, 2
                )
                
                # Convert back to PIL
                pil_image = Image.fromarray(np_image)
            
            # Lưu ảnh đã xử lý
            temp_path = image_path.replace('.', '_processed.')
            pil_image.save(temp_path)
            return temp_path
            
        except Exception as e:
            logger.error(f"Lỗi preprocessing: {e}")
            return image_path

    def postprocess_text(self, text: str) -> str:
        """Hậu xử lý văn bản để sửa lỗi dấu tiếng Việt"""
        if not text:
            return text
        
        # Áp dụng character mapping
        processed_text = text
        for wrong, correct in self.vietnamese_char_mapping.items():
            processed_text = processed_text.replace(wrong, correct)
        
        # Regex patterns để sửa một số lỗi phổ biến
        patterns = [
            (r'Döc\s+lap', 'Độc lập'),
            (r'Tudo', 'Tự do'),
            (r'Hanh\s+phüc', 'Hạnh phúc'),
            (r'phüc', 'phúc'),
            (r'döc', 'độc'),
            (r'tudo', 'tự do'),
            (r'hanh', 'hạnh'),
        ]
        
        for pattern, replacement in patterns:
            processed_text = re.sub(pattern, replacement, processed_text, flags=re.IGNORECASE)
        
        return processed_text

    def enhanced_ocr(self, image_path: str, config: str = 'primary') -> Dict[str, Any]:
        """OCR với các cải tiến cho tiếng Việt"""
        try:
            start_time = time.time()
            
            # Preprocessing
            processed_image_path = self.preprocess_image(image_path, 'enhanced')
            
            # OCR với config được chọn
            ocr_engine = self.ocr_configs[config]
            result = ocr_engine.ocr(processed_image_path, cls=True)
            
            # Xử lý kết quả
            texts = []
            confidences = []
            bboxes = []
            all_text = ""
            
            if result and len(result) > 0 and result[0]:
                for line in result[0]:
                    if line and len(line) >= 2:
                        bbox = line[0]
                        text_info = line[1]
                        if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                            raw_text = text_info[0]
                            confidence = text_info[1]
                            
                            # Post-process text
                            processed_text = self.postprocess_text(raw_text)
                            
                            texts.append(processed_text)
                            confidences.append(confidence)
                            bboxes.append(bbox)
                            all_text += processed_text + " "
            
            # Cleanup temp file
            if processed_image_path != image_path and os.path.exists(processed_image_path):
                os.remove(processed_image_path)
            
            processing_time = time.time() - start_time
            
            return {
                "engine": f"Enhanced PaddleOCR ({config})",
                "text": all_text.strip(),
                "texts": texts,
                "confidences": confidences,
                "avg_confidence": sum(confidences) / len(confidences) if confidences else 0,
                "bboxes": bboxes,
                "processing_time": processing_time,
                "total_segments": len(texts)
            }
            
        except Exception as e:
            logger.error(f"Lỗi enhanced OCR: {e}")
            return {"error": str(e)}

    def test_multiple_configs(self, image_path: str) -> Dict[str, Any]:
        """Test với nhiều cấu hình khác nhau"""
        results = {}
        
        for config_name in self.ocr_configs.keys():
            logger.info(f"Testing với config: {config_name}")
            result = self.enhanced_ocr(image_path, config_name)
            results[config_name] = result
        
        # So sánh kết quả
        best_config = self.find_best_config(results)
        
        return {
            "results": results,
            "best_config": best_config,
            "comparison": self.compare_configs(results)
        }

    def find_best_config(self, results: Dict[str, Any]) -> str:
        """Tìm config tốt nhất dựa trên confidence và số ký tự tiếng Việt"""
        best_score = 0
        best_config = "primary"
        
        vietnamese_chars = "áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ"
        vietnamese_chars += vietnamese_chars.upper()
        
        for config, result in results.items():
            if "error" not in result:
                confidence = result.get("avg_confidence", 0)
                text = result.get("text", "")
                vietnamese_count = sum(1 for char in text if char in vietnamese_chars)
                
                # Score = confidence * 0.7 + vietnamese_ratio * 0.3
                vietnamese_ratio = vietnamese_count / len(text) if text else 0
                score = confidence * 0.7 + vietnamese_ratio * 0.3
                
                if score > best_score:
                    best_score = score
                    best_config = config
        
        return best_config

    def compare_configs(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """So sánh các config"""
        comparison = {}
        
        vietnamese_chars = "áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ"
        vietnamese_chars += vietnamese_chars.upper()
        
        for config, result in results.items():
            if "error" not in result:
                text = result.get("text", "")
                comparison[config] = {
                    "confidence": result.get("avg_confidence", 0),
                    "processing_time": result.get("processing_time", 0),
                    "text_length": len(text),
                    "vietnamese_chars": sum(1 for char in text if char in vietnamese_chars),
                    "segments": result.get("total_segments", 0)
                }
        
        return comparison

def main():
    """Test script"""
    print("🚀 Testing Enhanced Vietnamese OCR...")
    
    enhancer = VietnameseOCREnhancer()
    
    # Test image
    test_image = "/Users/lechaukha12/Desktop/ocr-service/IMG_4620.png"
    
    if not os.path.exists(test_image):
        print(f"❌ File không tồn tại: {test_image}")
        return
    
    # Test với multiple configs
    results = enhancer.test_multiple_configs(test_image)
    
    # In kết quả
    print("\n📊 KẾT QUẢ TEST:")
    print(f"Best config: {results['best_config']}")
    
    for config, result in results['results'].items():
        if "error" not in result:
            print(f"\n🔧 Config: {config}")
            print(f"  Text: {result['text'][:100]}...")
            print(f"  Confidence: {result['avg_confidence']:.2f}")
            print(f"  Processing time: {result['processing_time']:.2f}s")
            print(f"  Segments: {result['total_segments']}")
    
    print(f"\n📈 COMPARISON:")
    for config, stats in results['comparison'].items():
        print(f"  {config}:")
        print(f"    Vietnamese chars: {stats['vietnamese_chars']}")
        print(f"    Confidence: {stats['confidence']:.2f}")
        print(f"    Processing time: {stats['processing_time']:.2f}s")

if __name__ == "__main__":
    main()
