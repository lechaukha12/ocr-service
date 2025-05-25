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
        print(f"Response Text: {response.text[:1000]}...") 
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

def test_04_upload_single_file_via_gateway(access_token: str, filename: str = "test_gateway_upload.txt", content: str = "Hello Gateway Storage!") -> Optional[Dict[str, Any]]:
    print_section_header("API Gateway -> Storage Service: Upload Single File")
    if not access_token:
        print("No access token provided for upload_single_file_via_gateway.")
        return None

    storage_upload_url = f"{API_GATEWAY_URL}/storage/upload/file/"
    
    files_payload = {'file': (filename, content.encode('utf-8'), 'text/plain')} 

    headers = {"Authorization": f"Bearer {access_token}"} 

    try:
        response = requests.post(storage_upload_url, files=files_payload, headers=headers)
        print_response_details(response, f"Uploading file to {storage_upload_url}...")
        if response.status_code == 200: 
            return response.json()
    except requests.exceptions.ConnectionError as e:
        print(f"Could not connect to {storage_upload_url}. Ensure API Gateway is running and the route is configured.")
        print(e)
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
        if response.status_code == 200:
            print(f"Content-Type: {response.headers.get('content-type')}")
            print(f"Content length: {len(response.content)}")
            if "text" in response.headers.get('content-type', ""):
                 print(f"File content (first 100 chars if text): {response.text[:100]}")
            else:
                print("File content is binary or not text.")
        else:
            print_response_details(response) 
    except requests.exceptions.ConnectionError as e:
        print(f"Could not connect to {storage_get_file_url}. Ensure API Gateway is running and the route is configured.")
        print(e)
    print("-" * 40)

# test_06_ocr_get_languages_via_gateway đã bị xóa

def test_07_ocr_image_via_gateway(access_token: str, image_path: str) -> Optional[Dict[str, Any]]: 
    print_section_header(f"API Gateway -> OCR Service (VietOCR): OCR Image '{os.path.basename(image_path)}'")
    if not access_token: 
        print("No access token provided for ocr_image_via_gateway.")
        return None 
    
    if not os.path.exists(image_path):
        print(f"Test image file not found: {image_path}")
        return None

    ocr_image_url = f"{API_GATEWAY_URL}/ocr/image/"
    
    # VietOCR endpoint không còn nhận `lang` và `psm`
    files_payload = {'file': (os.path.basename(image_path), open(image_path, 'rb'), 'image/jpeg')} 
    # data_payload không còn cần thiết cho lang và psm
    headers = {"Authorization": f"Bearer {access_token}"} 

    try:
        # Gửi request không có data_payload cho lang và psm
        response = requests.post(ocr_image_url, files=files_payload, headers=headers)
        print_response_details(response, f"Sending image to VietOCR at {ocr_image_url}...")
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.ConnectionError as e:
        print(f"Could not connect to {ocr_image_url}. Ensure API Gateway is running and the OCR route is configured.")
        print(e)
    finally:
        if 'file' in files_payload and hasattr(files_payload['file'][1], 'close'):
            files_payload['file'][1].close()
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
        "language": lang, # Giữ lại lang ở đây vì eKYC service có thể vẫn dùng nó cho logic Gemini
        "use_gemini_fallback": use_gemini
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


def test_09_admin_get_users(admin_token: str):
    print_section_header("API Gateway -> Admin Portal Backend: Get Users")
    if not admin_token:
        print("No admin token provided for get_users.")
        return None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    params = {"page": 1, "limit": 5}
    response = requests.get(f"{API_GATEWAY_URL}/admin/users/", headers=headers, params=params)
    print_response_details(response, "Fetching users via admin route...")
    if response.status_code == 200:
        return response.json()
    return None


if __name__ == "__main__":
    print("Starting Full API Flow Tests through API Gateway...")

    new_user_data = generate_unique_user_data()
    created_user = test_01_register_user(new_user_data)
    
    user_token = None
    if created_user:
        user_token = test_02_login_for_token(new_user_data["username"], new_user_data["password"])
    else:
        print("User registration failed, cannot proceed with login and other tests for user 1.")

    if user_token:
        current_user_info = test_03_get_current_user_me(user_token)
        if current_user_info:
            print(f"Successfully fetched 'me' for {current_user_info.get('username')}")
    else:
        print("Login failed for user 1, cannot proceed with authenticated tests for user 1.")

    admin_username_from_config = "admin_ekyc" 
    admin_password = "AdminPassword123" 
    
    admin_user_data = {
        "email": "admin_ekyc@example.com", 
        "username": admin_username_from_config,
        "password": admin_password,
        "full_name": "EKYC Administrator"
    }
    
    print(f"\nAttempting to ensure admin user '{admin_username_from_config}' exists or register...")
    test_01_register_user(admin_user_data) 

    admin_token = test_02_login_for_token(admin_username_from_config, admin_password)

    if admin_token:
        print(f"Admin user '{admin_username_from_config}' logged in successfully.")
        current_admin_info = test_03_get_current_user_me(admin_token)
        if current_admin_info:
            print(f"Successfully fetched 'me' for admin: {current_admin_info.get('username')}")
        
        admin_user_list_page = test_09_admin_get_users(admin_token)
        if admin_user_list_page:
            print(f"Admin successfully fetched user list. Total users: {admin_user_list_page.get('total')}, Page: {admin_user_list_page.get('page')}")
    else:
        print(f"Admin user '{admin_username_from_config}' login failed. Admin tests will be skipped.")
        print("Ensure the admin user is registered in User Service or User Service allows this registration.")


    if not user_token:
        print("\nRegular user login failed. Skipping user-specific Storage and OCR tests.")
    else:
        print("\n--- Storage Service Tests (via API Gateway with User Token) ---")
        uploaded_file_details = test_04_upload_single_file_via_gateway(user_token, content="Hello from user_token test!")
        if uploaded_file_details and "filename" in uploaded_file_details:
            filename_on_storage = uploaded_file_details["filename"]
            print(f"File uploaded to storage by user, unique name: {filename_on_storage}")
            time.sleep(0.5) 
            test_05_get_file_via_gateway(user_token, filename_on_storage)
        else:
            print("File upload via gateway to Storage Service failed or was skipped for user.")
        
        print("\n--- Generic OCR Service Tests (VietOCR) (via API Gateway with User Token) ---")
        ocr_result_text_for_extraction = None 
        
        real_image_path = find_real_image(REAL_IMAGE_BASENAME)

        if not real_image_path:
            print(f"Không thể tìm thấy ảnh '{REAL_IMAGE_BASENAME}' để kiểm thử OCR. Vui lòng đặt ảnh vào cùng thư mục với script.")
            ocr_result_text_for_extraction = "Lỗi: Không tìm thấy ảnh để OCR. Họ và tên: Nguyễn Văn A. Số: 123456789."
        else:
            # test_06_ocr_get_languages_via_gateway is removed
            print(f"\nSử dụng ảnh '{real_image_path}' cho VietOCR...")
            ocr_result_real_image_vie = test_07_ocr_image_via_gateway(user_token, real_image_path) # lang và psm đã bị xóa
            
            if ocr_result_real_image_vie and ocr_result_real_image_vie.get("text"):
                print(f"VietOCR Result for '{os.path.basename(real_image_path)}':\n---\n{ocr_result_real_image_vie.get('text')}\n---")
                ocr_result_text_for_extraction = ocr_result_real_image_vie.get("text") 
            else:
                print(f"Không nhận được kết quả văn bản từ VietOCR cho ảnh '{os.path.basename(real_image_path)}'.")
                ocr_result_text_for_extraction = f"Lỗi VietOCR hoặc không có văn bản."
        
        print("\n--- eKYC Information Extraction Service Tests (via API Gateway with User Token) ---")
        if ocr_result_text_for_extraction:
            # Tham số `lang="vie"` vẫn được giữ lại cho ekyc service vì nó có thể dùng cho Gemini
            extracted_info_with_gemini = test_08_ekyc_extract_info_via_gateway(user_token, ocr_result_text_for_extraction, lang="vie", use_gemini=True)
            if extracted_info_with_gemini:
                 print(f"Extracted Information (Gemini Fallback Enabled for user token run):")
        else: 
            print(f"No OCR text available for extraction. Skipping eKYC Information Extraction test for user.")


    print("\nFull API Flow Tests Completed.")
    print("Ensure API Gateway is correctly configured for all service routes.")
    print("Ensure all services (User, Storage, Generic OCR with VietOCR, eKYC Info Extraction, Admin Portal Backend) are running.")