#!/usr/bin/env python3
"""
Script test trực tiếp với VLM-Core service
"""

import requests
import os

def test_vlm_core_health():
    """Test health check của VLM-Core service"""
    print("========== Testing VLM-Core Health Check ==========")
    try:
        response = requests.get("http://localhost:8009/health")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"Health Response: {health_data}")
            return True
        else:
            print(f"Health check failed with status: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"Error connecting to VLM-Core service: {e}")
        return False

def test_vlm_core_ocr(image_path):
    """Test OCR với VLM-Core service"""
    print(f"\n========== Testing VLM-Core OCR with image: {image_path} ==========")
    
    if not os.path.exists(image_path):
        print(f"Image file not found: {image_path}")
        return False
    
    try:
        # Gửi yêu cầu OCR trực tiếp đến VLM-Core
        with open(image_path, 'rb') as image_file:
            files = {'image': image_file}
            response = requests.post("http://localhost:8009/ocr", files=files)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            ocr_result = response.json()
            print(f"OCR Result: {ocr_result}")
            print(f"\n--- Extracted Text ---")
            print(ocr_result.get('text', 'No text found'))
            print("----------------------")
            return True
        else:
            print(f"OCR request failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"Error calling VLM-Core OCR: {e}")
        return False

def main():
    print("Bắt đầu test trực tiếp với VLM-Core service...")
    
    # Test health check trước
    if not test_vlm_core_health():
        print("Health check failed. Exiting...")
        return
    
    # Test OCR với hình ảnh IMG_4620.png
    image_path = "IMG_4620.png"
    if os.path.exists(image_path):
        test_vlm_core_ocr(image_path)
    else:
        print(f"Image {image_path} not found in current directory")
    
    print("\nTest VLM-Core service hoàn tất.")

if __name__ == "__main__":
    main()
