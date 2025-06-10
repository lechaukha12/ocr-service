#!/usr/bin/env python3
"""
Script test trực tiếp với API Ollama sử dụng model llava
"""

import requests
import base64
import json

def test_ollama_llava_direct():
    """Test OCR trực tiếp với API Ollama model llava"""
    print("========== Testing Ollama LLaVA Direct ==========")
    
    image_path = "IMG_4620.png"
    
    try:
        # Đọc và encode hình ảnh
        with open(image_path, 'rb') as image_file:
            image_bytes = image_file.read()
            encoded_image = base64.b64encode(image_bytes).decode('utf-8')
        
        # Payload cho API Ollama
        payload = {
            "model": "llava",
            "prompt": """Cẩn thận đọc và trích xuất TẤT CẢ văn bản hiển thị trong hình ảnh này. 
- Các câu hoàn chỉnh - giữ nguyên cấu trúc các đoạn văn
- Chính xác từng ký tự, số, dấu câu
- Giữ nguyên thứ tự văn bản từ trái sang phải, trên xuống dưới
- Khi văn bản đa ngôn ngữ - ưu tiên văn bản tiếng Việt và phiên âm đúng
- Đọc rõ cả chữ in, chữ viết tay, logo, dấu ấn
- Luôn GIỮA NGUYÊN định dạng gốc và KHÔNG thêm bất kỳ chú thích hoặc diễn giải nào
- KHÔNG ĐƯỢC sáng tạo ra nội dung không có trong ảnh
- Chỉ trả về văn bản, không thêm giải thích

Nếu không thấy văn bản, trả về "Không phát hiện văn bản rõ ràng trong hình ảnh".""",
            "stream": False,
            "images": [encoded_image]
        }
        
        # Gọi API Ollama trực tiếp
        response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=180)
        response.raise_for_status()
        
        result = response.json()
        ocr_text = result.get("response", "")
        
        print(f"Status Code: {response.status_code}")
        print(f"Model: llava")
        print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        print(f"\n--- Extracted Text ---")
        print(ocr_text)
        print("----------------------")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("Bắt đầu test trực tiếp với API Ollama model LLaVA...")
    test_ollama_llava_direct()
    print("\nTest hoàn tất.")

if __name__ == "__main__":
    main()
