#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script đơn giản để kiểm tra PaddleOCR
"""

import sys
import os

# Test import
try:
    from paddleocr import PaddleOCR
    print("✅ PaddleOCR import thành công")
except ImportError as e:
    print(f"❌ Lỗi import PaddleOCR: {e}")
    sys.exit(1)

try:
    import cv2
    print("✅ OpenCV import thành công")
except ImportError as e:
    print(f"❌ Lỗi import OpenCV: {e}")
    sys.exit(1)

try:
    from PIL import Image
    print("✅ PIL import thành công")
except ImportError as e:
    print(f"❌ Lỗi import PIL: {e}")
    sys.exit(1)

# Test khởi tạo PaddleOCR
print("\n🔧 Đang khởi tạo PaddleOCR...")
try:
    ocr = PaddleOCR(use_angle_cls=True, lang='vi', use_gpu=False, show_log=False)
    print("✅ PaddleOCR khởi tạo thành công")
except Exception as e:
    print(f"❌ Lỗi khởi tạo PaddleOCR: {e}")
    sys.exit(1)

# Test OCR với file ảnh
image_path = "/Users/lechaukha12/Desktop/ocr-service/IMG_4620.png"
if not os.path.exists(image_path):
    print(f"❌ File ảnh không tồn tại: {image_path}")
    sys.exit(1)

print(f"\n📸 Đang xử lý ảnh: {os.path.basename(image_path)}")
try:
    result = ocr.ocr(image_path, cls=True)
    print("✅ OCR hoàn thành")
    
    # Hiển thị kết quả
    if result and len(result) > 0 and result[0]:
        print(f"\n📄 Tìm thấy {len(result[0])} text segments:")
        all_text = ""
        for i, line in enumerate(result[0]):
            if line and len(line) >= 2:
                text_info = line[1]
                if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                    text = text_info[0]
                    confidence = text_info[1]
                    print(f"  {i+1}. {text} (confidence: {confidence:.2f})")
                    all_text += text + " "
        
        print(f"\n📝 FULL TEXT:")
        print(f"'{all_text.strip()}'")
        
        # Đếm ký tự tiếng Việt
        vietnamese_chars = "áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ"
        vietnamese_chars += vietnamese_chars.upper()
        viet_count = sum(1 for char in all_text if char in vietnamese_chars)
        print(f"\n🇻🇳 Vietnamese characters: {viet_count}/{len(all_text)} ({viet_count/len(all_text)*100:.1f}%)")
        
    else:
        print("❌ Không nhận diện được text nào")
        
except Exception as e:
    print(f"❌ Lỗi trong quá trình OCR: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ Test hoàn thành")
