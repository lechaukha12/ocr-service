#!/usr/bin/env python
# filepath: /Users/lechaukha12/Desktop/ocr-service/test_vlm_ocr.py
"""
Script kiểm tra dịch vụ OCR sử dụng Vision Language Model
"""

import requests
import argparse
import sys
import json
import os

def test_vlm_ocr(image_path, use_api_gateway=False):
    """
    Test OCR service bằng VLM
    """
    if not os.path.exists(image_path):
        print(f"Lỗi: File hình ảnh không tồn tại: {image_path}")
        sys.exit(1)
    
    # Xác định endpoint
    if use_api_gateway:
        url = "http://localhost:8000/vlm/ocr/"
    else:
        url = "http://localhost:8009/ocr"
    
    print(f"Gửi yêu cầu OCR tới: {url}")
    
    # Chuẩn bị file hình ảnh
    with open(image_path, "rb") as f:
        files = {"image" if not use_api_gateway else "file": (os.path.basename(image_path), f, "image/png")}
        
        # Gửi yêu cầu
        try:
            response = requests.post(url, files=files)
            response.raise_for_status()
            
            # In kết quả
            result = response.json()
            print("\n===== KẾT QUẢ OCR =====")
            if use_api_gateway:
                print(f"Model: {result.get('model', 'Không xác định')}")
                print(f"Thành công: {result.get('success', False)}")
                if result.get('error'):
                    print(f"Lỗi: {result['error']}")
                print("\nNỘI DUNG:")
                print(result.get('text', ''))
            else:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            
            return True
            
        except requests.RequestException as e:
            print(f"Lỗi khi gửi yêu cầu: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try:
                    print(f"Chi tiết: {e.response.json()}")
                except:
                    print(f"Nội dung phản hồi: {e.response.text[:500]}...")
            return False

def test_vlm_health(use_api_gateway=False):
    """
    Kiểm tra trạng thái hoạt động của VLM OCR service
    """
    if use_api_gateway:
        url = "http://localhost:8000/vlm/health/"
    else:
        url = "http://localhost:8009/health"
    
    print(f"Kiểm tra sức khỏe VLM OCR service tại: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        print("\n===== TRẠNG THÁI VLM OCR SERVICE =====")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return True
    except requests.RequestException as e:
        print(f"Lỗi khi kiểm tra sức khỏe: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status code: {e.response.status_code}")
            try:
                print(f"Chi tiết: {e.response.json()}")
            except:
                print(f"Nội dung phản hồi: {e.response.text[:500]}...")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test VLM OCR Service")
    parser.add_argument("--image", "-i", help="Đường dẫn tới file hình ảnh")
    parser.add_argument("--gateway", "-g", action="store_true", help="Sử dụng API Gateway")
    parser.add_argument("--health", action="store_true", help="Chỉ kiểm tra trạng thái dịch vụ")
    
    args = parser.parse_args()
    
    if args.health:
        test_vlm_health(use_api_gateway=args.gateway)
    elif args.image:
        test_vlm_ocr(args.image, use_api_gateway=args.gateway)
    else:
        print("Vui lòng cung cấp đường dẫn tới file hình ảnh (--image) hoặc kiểm tra sức khỏe (--health)")
        parser.print_help()
