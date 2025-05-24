import requests
import json
import time
import os
from typing import Dict, Any, Optional, List

API_GATEWAY_URL = "http://localhost:8000"
REAL_IMAGE_BASENAME = "IMG_4620" # Đảm bảo tên tệp ảnh của bạn ở đây (không bao gồm phần mở rộng)

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
        print(f"Response Text: {response.text[:1000]}...") # Tăng giới hạn text để xem lỗi rõ hơn nếu có
    print("-" * 40)

def generate_unique_user_data() -> Dict[str, str]:
    timestamp = int(time.time() * 1000)
    return {
        "email": f"testuser{timestamp}@example.com",
        "username": f"testuser{timestamp}",
        "password": "SecurePassword123"
    }

def find_real_image(basename: str) -> Optional[str]:
    supported_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".JPG", ".JPEG", ".PNG"] # Thêm phần mở rộng viết hoa
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
        return response.json().get("access_token")
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

def test_04_upload_single_file_via_gateway(access_token: str, filename: str = "test_gateway_upload.txt", content: str = "Hello Gateway Storage!") -> Optional[Dict[str, Any]]:
    print_section_header("API Gateway -> Storage Service: Upload Single File")
    if not access_token:
        print("No access token provided for upload_single_file_via_gateway.")
        return None

    storage_upload_url = f"{API_GATEWAY_URL}/storage/upload/file/"
    with open(filename, "w") as f:
        f.write(content)

    files_payload = {'file': (filename, open(filename, 'rb'), 'text/plain')}
    headers = {"Authorization": f"Bearer {access_token}"} 

    try:
        response = requests.post(storage_upload_url, files=files_payload, headers=headers)
        print_response_details(response, f"Uploading file to {storage_upload_url}...")
        if response.status_code == 200: 
            return response.json()
    except requests.exceptions.ConnectionError as e:
        print(f"Could not connect to {storage_upload_url}. Ensure API Gateway is running and the route is configured.")
        print(e)
    finally:
        if os.path.exists(filename):
            os.remove(filename) 
    return None

def test_05_get_file_via_gateway(access_token: str, uploaded_filename_on_storage: str):
    print_section_header("API Gateway -> Storage Service: Get File")
    if not access_token:
        print("No access token provided for get_file_via_gateway.")
        return
    if not uploaded_filename_on_storage:
        print("No uploaded_filename_on_storage provided.")
        return

    storage_get_file_url = f"{API_GATEWAY_URL}/storage/files/{uploaded_filename_on_storage}"
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(storage_get_file_url, headers=headers)
        # print(f"URL: {response.url}") # Đã có trong print_response_details
        # print(f"Status Code: {response.status_code}") # Đã có trong print_response_details
        if response.status_code == 200:
            print(f"Content-Type: {response.headers.get('content-type')}")
            print(f"Content length: {len(response.content)}")
            print_response_details(response, "File content (first 100 chars if text):") # In lại để thấy response JSON nếu có
            # print(f"File content (first 100 chars if text): {response.text[:100]}")
        else:
            print_response_details(response) 
    except requests.exceptions.ConnectionError as e:
        print(f"Could not connect to {storage_get_file_url}. Ensure API Gateway is running and the route is configured.")
        print(e)
    print("-" * 40)

def test_06_ocr_get_languages_via_gateway(access_token: str):
    print_section_header("API Gateway -> OCR Service: Get Available Languages")
    if not access_token: 
        print("No access token provided for ocr_get_languages_via_gateway (if required by gateway).")

    ocr_languages_url = f"{API_GATEWAY_URL}/ocr/languages/"
    headers = {"Authorization": f"Bearer {access_token}"} 

    try:
        response = requests.get(ocr_languages_url, headers=headers)
        print_response_details(response, f"Fetching OCR languages from {ocr_languages_url}...")
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.ConnectionError as e:
        print(f"Could not connect to {ocr_languages_url}. Ensure API Gateway is running and the OCR route is configured.")
        print(e)
    return None

def test_07_ocr_image_via_gateway(access_token: str, image_path: str, lang: str = "vie", psm_value: str = "3"): 
    print_section_header(f"API Gateway -> OCR Service: OCR Image '{os.path.basename(image_path)}' with lang '{lang}' psm '{psm_value}'")
    if not access_token: 
        print("No access token provided for ocr_image_via_gateway (if required by gateway).")
    
    if not os.path.exists(image_path):
        print(f"Test image file not found: {image_path}")
        return None

    ocr_image_url = f"{API_GATEWAY_URL}/ocr/image/"
    
    files_payload = {'file': (os.path.basename(image_path), open(image_path, 'rb'))}
    data_payload = {'lang': lang, 'psm': psm_value} 
    headers = {"Authorization": f"Bearer {access_token}"} 

    try:
        response = requests.post(ocr_image_url, files=files_payload, data=data_payload, headers=headers)
        print_response_details(response, f"Sending image to OCR at {ocr_image_url}...")
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.ConnectionError as e:
        print(f"Could not connect to {ocr_image_url}. Ensure API Gateway is running and the OCR route is configured.")
        print(e)
    return None

def test_08_ekyc_extract_info_via_gateway(access_token: str, ocr_text_sample: str, lang: str = "vie", use_gemini: bool = True) -> Optional[Dict[str, Any]]:
    print_section_header(f"API Gateway -> eKYC Info Extraction: Extract Info (use_gemini={use_gemini})")
    if not access_token:
        print("No access token provided for ekyc_extract_info_via_gateway.")
        return None
    
    if not ocr_text_sample:
        print("No OCR text provided for extraction.")
        return None

    extraction_url = f"{API_GATEWAY_URL}/ekyc/extract_info/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json" 
    }
    payload = {
        "ocr_text": ocr_text_sample,
        "language": lang,
        "use_gemini_fallback": use_gemini # Thêm tham số này
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
        exit()

    if user_token:
        current_user_info = test_03_get_current_user_me(user_token)
        if current_user_info:
            print(f"Successfully fetched 'me': {current_user_info.get('username')}")
    else:
        print("Login failed, cannot proceed with authenticated tests.")
        exit()

    print("\n--- Storage Service Tests (via API Gateway) ---")
    uploaded_file_details = test_04_upload_single_file_via_gateway(user_token)
    if uploaded_file_details and "filename" in uploaded_file_details:
        filename_on_storage = uploaded_file_details["filename"]
        print(f"File uploaded to storage, unique name: {filename_on_storage}")
        time.sleep(0.5) 
        test_05_get_file_via_gateway(user_token, filename_on_storage)
    else:
        print("File upload via gateway to Storage Service failed or was skipped.")
    
    print("\n--- Generic OCR Service Tests (via API Gateway) ---")
    ocr_result_text_for_extraction = None 
    
    real_image_path = find_real_image(REAL_IMAGE_BASENAME)

    if not real_image_path:
        print(f"Không thể tìm thấy ảnh '{REAL_IMAGE_BASENAME}' để kiểm thử OCR. Vui lòng đặt ảnh vào cùng thư mục với script.")
        ocr_result_text_for_extraction = "Lỗi: Không tìm thấy ảnh để OCR. Họ và tên: Nguyễn Văn A. Số: 123456789."
    else:
        if user_token: 
            ocr_languages = test_06_ocr_get_languages_via_gateway(user_token)
            if ocr_languages:
                print(f"Available OCR languages: {ocr_languages.get('available_languages')}")

            print(f"\nSử dụng ảnh '{real_image_path}' cho OCR...")
            
            psm_to_test = "3" # Bạn có thể thay đổi giá trị này (ví dụ: "3", "6", "11", "13")

            ocr_result_real_image_vie = test_07_ocr_image_via_gateway(user_token, real_image_path, lang="vie", psm_value=psm_to_test)
            
            if ocr_result_real_image_vie and ocr_result_real_image_vie.get("text"):
                print(f"OCR Result (vie, psm={psm_to_test}) for '{os.path.basename(real_image_path)}':\n---\n{ocr_result_real_image_vie.get('text')}\n---")
                ocr_result_text_for_extraction = ocr_result_real_image_vie.get("text") 
            else:
                print(f"Không nhận được kết quả văn bản từ OCR cho ảnh '{os.path.basename(real_image_path)}' (lang: vie, psm={psm_to_test}).")
                ocr_result_text_for_extraction = f"Lỗi OCR hoặc không có văn bản (vie, psm={psm_to_test})."
        else:
            print("Không có token người dùng, bỏ qua kiểm thử OCR với ảnh thật.")
            ocr_result_text_for_extraction = "Lỗi: Không có token người dùng để OCR."


    print("\n--- eKYC Information Extraction Service Tests (via API Gateway) ---")
    if user_token and ocr_result_text_for_extraction:
        # Chạy thử với Gemini fallback được bật
        extracted_info_with_gemini = test_08_ekyc_extract_info_via_gateway(user_token, ocr_result_text_for_extraction, lang="vie", use_gemini=True)
        if extracted_info_with_gemini:
            print(f"Extracted Information (Gemini Fallback Enabled):") # {json.dumps(extracted_info_with_gemini, indent=2, ensure_ascii=False)}")
            # print_response_details đã in rồi

        # (Tùy chọn) Chạy thử với Gemini fallback bị tắt để so sánh
        # print("\n--- Testing eKYC Extraction with Gemini Fallback DISABLED ---")
        # extracted_info_no_gemini = test_08_ekyc_extract_info_via_gateway(user_token, ocr_result_text_for_extraction, lang="vie", use_gemini=False)
        # if extracted_info_no_gemini:
        #     print(f"Extracted Information (Gemini Fallback Disabled):") # {json.dumps(extracted_info_no_gemini, indent=2, ensure_ascii=False)}")

    elif not user_token:
        print("No user token, skipping eKYC Information Extraction test.")
    else: 
        print(f"No OCR text available for extraction (value: {ocr_result_text_for_extraction}). Skipping eKYC Information Extraction test.")


    print("\nFull API Flow Tests Completed.")
    print("Ensure API Gateway is correctly configured for all service routes.")

