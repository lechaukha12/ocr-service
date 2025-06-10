#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script so sánh kết quả OCR giữa PaddleOCR và Google Gemini
Đặc biệt tập trung vào độ chính xác nhận diện dấu tiếng Việt
"""

import os
import sys
import time
import json
import logging
from typing import Dict, List, Any, Optional
from PIL import Image
import base64
import io
import requests
from pathlib import Path

# Import PaddleOCR
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    print("❌ PaddleOCR không khả dụng")

# Import Google Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("❌ Google Gemini không khả dụng")

# Thiết lập logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OCRComparison:
    def __init__(self):
        """Khởi tạo các OCR engines"""
        self.paddle_ocr = None
        self.gemini_model = None
        
        # Khởi tạo PaddleOCR
        if PADDLEOCR_AVAILABLE:
            try:
                self.paddle_ocr = PaddleOCR(use_angle_cls=True, lang='vi', use_gpu=False, show_log=False)
                logger.info("✅ PaddleOCR đã sẵn sàng với hỗ trợ tiếng Việt")
            except Exception as e:
                logger.error(f"❌ Lỗi khởi tạo PaddleOCR: {e}")
        
        # Khởi tạo Gemini
        if GEMINI_AVAILABLE:
            api_key = os.getenv('GOOGLE_API_KEY')
            if api_key:
                try:
                    genai.configure(api_key=api_key)
                    self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                    logger.info("✅ Google Gemini đã sẵn sàng")
                except Exception as e:
                    logger.error(f"❌ Lỗi khởi tạo Gemini: {e}")
            else:
                logger.warning("⚠️ Thiếu GOOGLE_API_KEY environment variable")

    def ocr_with_paddleocr(self, image_path: str) -> Dict[str, Any]:
        """Thực hiện OCR với PaddleOCR"""
        if not self.paddle_ocr:
            return {"error": "PaddleOCR không khả dụng"}
        
        try:
            start_time = time.time()
            result = self.paddle_ocr.ocr(image_path, cls=True)
            processing_time = time.time() - start_time
            
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
                            text = text_info[0]
                            confidence = text_info[1]
                            
                            texts.append(text)
                            confidences.append(confidence)
                            bboxes.append(bbox)
                            all_text += text + " "
            
            return {
                "engine": "PaddleOCR",
                "text": all_text.strip(),
                "texts": texts,
                "confidences": confidences,
                "avg_confidence": sum(confidences) / len(confidences) if confidences else 0,
                "bboxes": bboxes,
                "processing_time": processing_time,
                "total_segments": len(texts)
            }
            
        except Exception as e:
            logger.error(f"Lỗi PaddleOCR: {e}")
            return {"error": str(e)}

    def ocr_with_gemini(self, image_path: str) -> Dict[str, Any]:
        """Thực hiện OCR với Google Gemini"""
        if not self.gemini_model:
            return {"error": "Google Gemini không khả dụng"}
        
        try:
            start_time = time.time()
            
            # Đọc và xử lý ảnh
            image = Image.open(image_path)
            
            # Prompt tiếng Việt cho Gemini
            prompt = """
            Hãy nhận diện và trích xuất toàn bộ văn bản trong ảnh này.
            Đặc biệt chú ý đến các dấu tiếng Việt (á, à, ả, ã, ạ, ă, ắ, ằ, ẳ, ẵ, ặ, â, ấ, ầ, ẩ, ẫ, ậ, v.v.).
            Trả về kết quả dưới dạng JSON với format:
            {
                "text": "toàn bộ văn bản được nhận diện",
                "segments": ["từng đoạn văn bản riêng biệt"]
            }
            
            Chỉ trả về JSON, không thêm bất kỳ text nào khác.
            """
            
            response = self.gemini_model.generate_content([prompt, image])
            processing_time = time.time() - start_time
            
            # Xử lý response
            if response and response.text:
                try:
                    # Thử parse JSON
                    result_json = json.loads(response.text.strip())
                    return {
                        "engine": "Google Gemini",
                        "text": result_json.get("text", ""),
                        "segments": result_json.get("segments", []),
                        "processing_time": processing_time,
                        "total_segments": len(result_json.get("segments", [])),
                        "raw_response": response.text
                    }
                except json.JSONDecodeError:
                    # Nếu không parse được JSON, trả về text thô
                    return {
                        "engine": "Google Gemini",
                        "text": response.text.strip(),
                        "segments": [response.text.strip()],
                        "processing_time": processing_time,
                        "total_segments": 1,
                        "raw_response": response.text
                    }
            else:
                return {"error": "Gemini không trả về kết quả"}
                
        except Exception as e:
            logger.error(f"Lỗi Gemini: {e}")
            return {"error": str(e)}

    def compare_ocr_results(self, image_path: str) -> Dict[str, Any]:
        """So sánh kết quả OCR từ cả hai engine"""
        if not os.path.exists(image_path):
            return {"error": f"File không tồn tại: {image_path}"}
        
        logger.info(f"🔍 Bắt đầu so sánh OCR cho ảnh: {image_path}")
        
        # Chạy OCR với cả hai engine
        paddle_result = self.ocr_with_paddleocr(image_path)
        gemini_result = self.ocr_with_gemini(image_path)
        
        # Phân tích kết quả
        comparison = {
            "image_path": image_path,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "paddle_ocr": paddle_result,
            "gemini": gemini_result,
            "analysis": {}
        }
        
        # So sánh chi tiết
        if "error" not in paddle_result and "error" not in gemini_result:
            paddle_text = paddle_result.get("text", "")
            gemini_text = gemini_result.get("text", "")
            
            # Đếm dấu tiếng Việt
            vietnamese_chars = "áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ"
            vietnamese_chars += vietnamese_chars.upper()
            
            paddle_vietnamese_count = sum(1 for char in paddle_text if char in vietnamese_chars)
            gemini_vietnamese_count = sum(1 for char in gemini_text if char in vietnamese_chars)
            
            comparison["analysis"] = {
                "paddle_text_length": len(paddle_text),
                "gemini_text_length": len(gemini_text),
                "paddle_vietnamese_chars": paddle_vietnamese_count,
                "gemini_vietnamese_chars": gemini_vietnamese_count,
                "paddle_processing_time": paddle_result.get("processing_time", 0),
                "gemini_processing_time": gemini_result.get("processing_time", 0),
                "text_similarity": self.calculate_text_similarity(paddle_text, gemini_text)
            }
        
        return comparison

    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Tính độ tương đồng giữa hai văn bản (đơn giản)"""
        if not text1 or not text2:
            return 0.0
        
        # Chuẩn hóa text
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()
        
        if text1 == text2:
            return 1.0
        
        # Tính Jaccard similarity với từ
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        intersection = words1 & words2
        union = words1 | words2
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)

    def run_comparison_test(self, test_images: List[str]) -> Dict[str, Any]:
        """Chạy test so sánh trên nhiều ảnh"""
        results = []
        
        for image_path in test_images:
            if os.path.exists(image_path):
                logger.info(f"📸 Đang test ảnh: {os.path.basename(image_path)}")
                result = self.compare_ocr_results(image_path)
                results.append(result)
            else:
                logger.warning(f"⚠️ File không tồn tại: {image_path}")
        
        # Tổng hợp kết quả
        summary = {
            "total_images": len(results),
            "successful_tests": len([r for r in results if "error" not in r.get("paddle_ocr", {}) and "error" not in r.get("gemini", {})]),
            "results": results,
            "summary_stats": self.calculate_summary_stats(results)
        }
        
        return summary

    def calculate_summary_stats(self, results: List[Dict]) -> Dict[str, Any]:
        """Tính toán thống kê tổng hợp"""
        valid_results = [r for r in results if r.get("analysis")]
        
        if not valid_results:
            return {"error": "Không có kết quả hợp lệ"}
        
        analyses = [r["analysis"] for r in valid_results]
        
        return {
            "avg_paddle_processing_time": sum(a.get("paddle_processing_time", 0) for a in analyses) / len(analyses),
            "avg_gemini_processing_time": sum(a.get("gemini_processing_time", 0) for a in analyses) / len(analyses),
            "avg_text_similarity": sum(a.get("text_similarity", 0) for a in analyses) / len(analyses),
            "paddle_total_vietnamese_chars": sum(a.get("paddle_vietnamese_chars", 0) for a in analyses),
            "gemini_total_vietnamese_chars": sum(a.get("gemini_vietnamese_chars", 0) for a in analyses)
        }

def main():
    """Hàm main để chạy test"""
    print("🚀 Bắt đầu so sánh OCR engines...")
    
    # Khởi tạo comparison
    comparator = OCRComparison()
    
    # Danh sách ảnh test
    test_images = [
        "/Users/lechaukha12/Desktop/ocr-service/IMG_4620.png"
    ]
    
    # Thêm ảnh test khác nếu có
    test_dir = "/Users/lechaukha12/Desktop/ocr-service/"
    for ext in ["*.png", "*.jpg", "*.jpeg"]:
        from glob import glob
        test_images.extend(glob(os.path.join(test_dir, ext)))
    
    # Loại bỏ duplicate
    test_images = list(set(test_images))
    
    print(f"📋 Tìm thấy {len(test_images)} ảnh để test:")
    for img in test_images:
        print(f"  - {os.path.basename(img)}")
    
    # Chạy comparison test
    results = comparator.run_comparison_test(test_images)
    
    # Lưu kết quả
    output_file = "/Users/lechaukha12/Desktop/ocr-service/OCR_COMPARISON_RESULTS.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Kết quả đã được lưu vào: {output_file}")
    
    # In tóm tắt
    print("\n📊 TÓM TẮT KẾT QUẢ:")
    print(f"  • Tổng số ảnh test: {results['total_images']}")
    print(f"  • Test thành công: {results['successful_tests']}")
    
    if results.get("summary_stats"):
        stats = results["summary_stats"]
        print(f"  • Thời gian xử lý trung bình:")
        print(f"    - PaddleOCR: {stats.get('avg_paddle_processing_time', 0):.2f}s")
        print(f"    - Gemini: {stats.get('avg_gemini_processing_time', 0):.2f}s")
        print(f"  • Độ tương đồng văn bản: {stats.get('avg_text_similarity', 0):.2f}")
        print(f"  • Tổng ký tự tiếng Việt:")
        print(f"    - PaddleOCR: {stats.get('paddle_total_vietnamese_chars', 0)}")
        print(f"    - Gemini: {stats.get('gemini_total_vietnamese_chars', 0)}")

if __name__ == "__main__":
    main()
