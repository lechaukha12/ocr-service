import requests
import json
import time
import os
from typing import Dict, Any, Optional

# Địa chỉ của API Gateway
API_GATEWAY_URL = "http://localhost:8000"
# Tên file ảnh test (không có phần mở rộng, script sẽ tự tìm)
# Hãy đảm bảo bạn có file ảnh này (ví dụ: IMG_4620.jpg) trong cùng thư mục với script
REAL_IMAGE_BASENAME = "IMG_4620" 

def print_section_header(title: str):
    """In tiêu đề cho một phần test."""
    print("\n" + "=" * 10 + f" {title} " + "=" * 10)

def print_response_details(response: requests.Response, message: str = ""):
    """In chi tiết của một HTTP response."""
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
    """Tạo dữ liệu người dùng duy nhất để đăng ký."""
    timestamp = int(time.time() * 1000)
    return {
        "email": f"ocr_test_user{timestamp}@example.com",
        "username": f"ocr_test_user{timestamp}",
        "password": "SecurePassword123",
        "full_name": f"OCR Test User {timestamp}"
    }

def find_real_image(basename: str) -> Optional[str]:
    """Tìm file ảnh thực tế dựa trên tên gốc và các phần mở rộng phổ biến."""
    supported_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".JPG", ".JPEG", ".PNG"]
    for ext in supported_extensions:
        filename = f"{basename}{ext}"
        if os.path.exists(filename):
            print(f"Tìm thấy ảnh thực tế: {filename}")
            return filename
    print(f"Không tìm thấy ảnh '{basename}' với các phần mở rộng được hỗ trợ tại '{os.getcwd()}': {supported_extensions}")
    return None

def register_and_login_test_user() -> Optional[str]:
    """Đăng ký và đăng nhập người dùng thử nghiệm, trả về access token."""
    user_data = generate_unique_user_data()
    
    print_section_header("Register Test User for OCR")
    register_url = f"{API_GATEWAY_URL}/auth/users/"
    try:
        response_register = requests.post(register_url, json=user_data)
        if response_register.status_code == 201:
            print(f"Người dùng '{user_data['username']}' đã được đăng ký thành công.")
        elif response_register.status_code == 400 and "already registered" in response_register.text.lower():
            print(f"Người dùng '{user_data['username']}' đã tồn tại, tiến hành đăng nhập.")
        else:
            print(f"Đăng ký người dùng '{user_data['username']}' thất bại. Status: {response_register.status_code}")
            print_response_details(response_register)
            return None
    except requests.exceptions.ConnectionError as e:
        print(f"Lỗi kết nối khi đăng ký người dùng: {e}")
        return None

    print_section_header(f"Login Test User: {user_data['username']}")
    login_url = f"{API_GATEWAY_URL}/auth/token"
    login_payload = {"username": user_data["username"], "password": user_data["password"]}
    try:
        response_login = requests.post(login_url, data=login_payload)
        if response_login.status_code == 200:
            token_info = response_login.json()
            access_token = token_info.get("access_token")
            print(f"Đăng nhập thành công. Access token nhận được.")
            return access_token
        else:
            print(f"Đăng nhập thất bại cho người dùng '{user_data['username']}'.")
            print_response_details(response_login)
            return None
    except requests.exceptions.ConnectionError as e:
        print(f"Lỗi kết nối khi đăng nhập: {e}")
        return None

def test_ocr_service_endpoint(access_token: str, image_path: str):
    """Gọi endpoint OCR của generic-ocr-service."""
    print_section_header(f"Testing Generic OCR Service v2 (Gemini) with image: '{os.path.basename(image_path)}'")
    
    if not access_token:
        print("Lỗi: Không có access token để gọi API OCR.")
        return
    
    if not os.path.exists(image_path):
        print(f"Lỗi: File ảnh test không tồn tại tại đường dẫn: {image_path}")
        return

    ocr_url = f"{API_GATEWAY_URL}/ocr/image/"
    form_data_payload = {'lang': 'vie', 'psm': '6'} 
    
    files_payload = None
    try:
        with open(image_path, 'rb') as f_image:
            files_payload = {'file': (os.path.basename(image_path), f_image, 'image/jpeg')} 
            headers = {"Authorization": f"Bearer {access_token}"}
            
            print(f"Đang gửi yêu cầu POST đến: {ocr_url}")
            response = requests.post(ocr_url, files=files_payload, data=form_data_payload, headers=headers)
            
            # In chi tiết response JSON trước để debug
            print("Raw Response Details from OCR Service:")
            print_response_details(response) # In toàn bộ response

            if response.status_code == 200:
                try:
                    ocr_data = response.json()
                    if "text" in ocr_data: # Kiểm tra key "text"
                        print("\n--- OCR Text (from Gemini API) ---")
                        print(ocr_data["text"])
                        print("------------------------------------")
                    else:
                        print("Output JSON từ OCR service không chứa key 'text' như mong đợi.")
                except json.JSONDecodeError:
                    print("Lỗi: Không thể parse JSON từ phản hồi của OCR service.")
            # Không cần else ở đây vì print_response_details đã xử lý các status code khác 200
            
    except requests.exceptions.ConnectionError as e:
        print(f"Lỗi kết nối đến OCR service: {e}")
    except FileNotFoundError:
        print(f"Lỗi: Không thể mở file ảnh: {image_path}")
    except Exception as e:
        print(f"Lỗi không xác định xảy ra: {e}")

if __name__ == "__main__":
    print("Bắt đầu kịch bản test dành riêng cho Generic OCR Service v2 (Gemini Edition)...")
    token = register_and_login_test_user()

    if token:
        image_file_to_test = find_real_image(REAL_IMAGE_BASENAME)
        if image_file_to_test:
            test_ocr_service_endpoint(token, image_file_to_test)
        else:
            print(f"Không tìm thấy ảnh '{REAL_IMAGE_BASENAME}' để thực hiện test OCR.")
    else:
        print("Không thể lấy access token, bỏ qua việc test OCR service.")

    print("\nKịch bản test OCR service đã hoàn tất.")