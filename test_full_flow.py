import requests
import json
import time
import os
from typing import Dict, Any, Optional, List

API_GATEWAY_URL = "http://localhost:8000"
REAL_IMAGE_BASENAME = "IMG_4620" 

def print_section_header(title: str):
    print("\n" + "=" * 10 + f" {title} " + "=" * 10)

def print_response_details(response: requests.Response, message: str = ""):
    if message:
        print(message)
    print(f"URL: {response.url}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response JSON: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except json.JSONDecodeError:
        print(f"Response Text (first 1000 chars): {response.text[:1000]}...") 
    print("-" * 40)

def generate_unique_user_data() -> Dict[str, str]:
    timestamp = int(time.time() * 1000)
    return {
        "email": f"testuser{timestamp}@example.com",
        "username": f"testuser{timestamp}",
        "password": "SecurePassword123",
        "full_name": f"Test User {timestamp}"
    }

def find_real_image(basename: str) -> Optional[str]:
    supported_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".JPG", ".JPEG", ".PNG"] 
    for ext in supported_extensions:
        filename = f"{basename}{ext}"
        if os.path.exists(filename):
            print(f"Tìm thấy ảnh thực tế: {filename}")
            return filename
    print(f"Không tìm thấy ảnh '{basename}' với các phần mở rộng được hỗ trợ tại '{os.getcwd()}': {supported_extensions}")
    return None

def test_01_register_user(user_data: Dict[str, str]) -> Optional[Dict[str, Any]]:
    print_section_header("API Gateway: Register User")
    response = requests.post(f"{API_GATEWAY_URL}/auth/users/", json=user_data)
    print_response_details(response, "Registering new user...")
    if response.status_code == 201:
        return response.json()
    return None

def test_02_login_for_token(username: str, password: str) -> Optional[str]:
    print_section_header(f"API Gateway: Login User - {username}")
    login_data = {"username": username, "password": password}
    response = requests.post(f"{API_GATEWAY_URL}/auth/token", data=login_data)
    print_response_details(response, "Logging in...")
    if response.status_code == 200:
        token_info = response.json()
        if "user_info" in token_info:
            print(f"User Info from login: {token_info['user_info']}")
        return token_info.get("access_token")
    return None

def test_03_get_current_user_me(access_token: str) -> Optional[Dict[str, Any]]:
    print_section_header("API Gateway: Get Current User (me)")
    if not access_token:
        print("No access token provided for get_current_user_me.")
        return None
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{API_GATEWAY_URL}/users/me/", headers=headers)
    print_response_details(response, "Fetching current user details...")
    if response.status_code == 200:
        return response.json()
    return None

def test_07_ocr_image_via_gateway(access_token: str, image_path: str) -> Optional[Dict[str, Any]]: 
    print_section_header(f"API Gateway -> Generic OCR Service (Gemini): OCR Image '{os.path.basename(image_path)}'")
    if not access_token: 
        print("No access token provided for ocr_image_via_gateway.")
        return None 
    
    if not os.path.exists(image_path):
        print(f"Test image file not found: {image_path}")
        return None

    ocr_image_url = f"{API_GATEWAY_URL}/ocr/image/"
    
    form_data_payload = {'lang': 'vie', 'psm': '6'} 
    files_payload = {'file': (os.path.basename(image_path), open(image_path, 'rb'), 'image/jpeg')} 
    headers = {"Authorization": f"Bearer {access_token}"} 

    try:
        response = requests.post(ocr_image_url, files=files_payload, data=form_data_payload, headers=headers)
        # In chi tiết response JSON trước để debug
        print("Raw Response Details from Generic OCR Service:")
        print_response_details(response) # In toàn bộ response

        if response.status_code == 200:
            return response.json()
    except requests.exceptions.ConnectionError as e:
        print(f"Could not connect to {ocr_image_url}. Ensure API Gateway and Generic OCR service are running.")
        print(e)
    finally:
        if 'file' in files_payload and hasattr(files_payload['file'][1], 'close'):
            files_payload['file'][1].close()
    return None

def test_08_ekyc_extract_info_via_gateway(access_token: str, ocr_text_sample: str, lang: str = "vie", use_gemini_fallback_for_ekyc: bool = True) -> Optional[Dict[str, Any]]:
    print_section_header(f"API Gateway -> eKYC Info Extraction: Extract Info (use_gemini_fallback_for_ekyc={use_gemini_fallback_for_ekyc})")
    if not access_token:
        print("No access token provided for ekyc_extract_info_via_gateway.")
        return None
    
    if not ocr_text_sample:
        print("No OCR text provided for extraction.")
        ocr_text_sample = "Lỗi OCR hoặc không có văn bản từ Generic OCR Service." 
        
    extraction_url = f"{API_GATEWAY_URL}/ekyc/extract_info/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json" 
    }
    payload = {
        "ocr_text": ocr_text_sample,
        "language": lang,
        "use_gemini_fallback": use_gemini_fallback_for_ekyc # Sử dụng tham số mới này
    }

    try:
        response = requests.post(extraction_url, json=payload, headers=headers)
        print_response_details(response, f"Sending OCR text for extraction to {extraction_url}...")
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.ConnectionError as e:
        print(f"Could not connect to {extraction_url}. Ensure API Gateway and eKYC Info Extraction service are running.")
        print(e)
    return None


if __name__ == "__main__":
    print("Starting Full API Flow Tests through API Gateway...")

    new_user_data = generate_unique_user_data()
    created_user = test_01_register_user(new_user_data)
    
    user_token = None
    if created_user:
        user_token = test_02_login_for_token(new_user_data["username"], new_user_data["password"])
    else:
        print("User registration failed, cannot proceed with login and other tests.")

    if not user_token:
        print("Login failed, cannot proceed with authenticated tests (OCR, eKYC).")
    else:
        current_user_info = test_03_get_current_user_me(user_token)
        if current_user_info:
            print(f"Successfully fetched 'me' for {current_user_info.get('username')}")
        
        print("\n--- Generic OCR Service (Gemini Edition) Test ---")
        ocr_result_text_for_extraction = None 
        
        real_image_path = find_real_image(REAL_IMAGE_BASENAME) # Sử dụng ảnh thật

        if not real_image_path:
            print(f"Không thể tìm thấy ảnh '{REAL_IMAGE_BASENAME}' để kiểm thử OCR. Vui lòng đặt ảnh vào cùng thư mục với script.")
            ocr_result_text_for_extraction = f"Lỗi: Không tìm thấy ảnh {REAL_IMAGE_BASENAME} để OCR." 
        else:
            print(f"\nSử dụng ảnh '{real_image_path}' cho Generic OCR Service...")
            ocr_response_data = test_07_ocr_image_via_gateway(user_token, real_image_path)
            
            if ocr_response_data and "text" in ocr_response_data:
                ocr_result_text_for_extraction = ocr_response_data.get("text")
                print(f"Generic OCR Service (Gemini) Result for '{os.path.basename(real_image_path)}':\n---\n{ocr_result_text_for_extraction}\n---")
            else:
                print(f"Không nhận được kết quả văn bản có key 'text' từ Generic OCR Service cho ảnh '{os.path.basename(real_image_path)}'.")
                ocr_result_text_for_extraction = "Lỗi: Cấu trúc output OCR không đúng hoặc không có text từ Generic OCR Service."
        
        print("\n--- eKYC Information Extraction Service Test ---")
        # Quyết định có dùng Gemini fallback cho eKYC service hay không
        # True: eKYC service sẽ dùng Regex trước, nếu không ổn sẽ gọi Gemini của nó.
        # False: eKYC service sẽ chỉ dùng Regex.
        should_ekyc_use_gemini_fallback = True 
        
        extracted_info = test_08_ekyc_extract_info_via_gateway(
            user_token, 
            ocr_result_text_for_extraction, 
            lang="vie", 
            use_gemini_fallback_for_ekyc=should_ekyc_use_gemini_fallback
        )
        
        if extracted_info:
             # print_response_details đã in rồi, có thể in thêm tóm tắt nếu muốn
             print(f"eKYC Service extraction method used: {extracted_info.get('extraction_method')}")
             if extracted_info.get("errors"):
                 print(f"eKYC Service extraction errors: {extracted_info.get('errors')}")
        else: 
            print(f"Không có thông tin được trích xuất bởi eKYC service hoặc gọi service eKYC thất bại.")

    print("\nFull API Flow Tests Completed.")