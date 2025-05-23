import requests
import json
import time
import os
from typing import Dict, Any, Optional, List

USER_SERVICE_URL = "http://localhost:8001"
ADMIN_PORTAL_BACKEND_URL = "http://localhost:8002"
STORAGE_SERVICE_URL = "http://localhost:8003"
API_GATEWAY_URL = "http://localhost:8000"


def print_section_header(title: str):
    print("\n" + "=" * 10 + f" {title} " + "=" * 10)

def print_response_details(response: requests.Response):
    print(f"URL: {response.url}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response JSON: {response.json()}")
    except json.JSONDecodeError:
        print(f"Response Text: {response.text}")
    print("-" * 40)

def generate_unique_user_data() -> Dict[str, str]:
    timestamp = int(time.time() * 1000) # milliseconds for more uniqueness
    return {
        "email": f"testuser{timestamp}@example.com",
        "username": f"testuser{timestamp}",
        "password": "SecurePassword123"
    }

# --- User Service Tests ---
def test_user_service_create_user(user_data: Dict[str, str]) -> Optional[Dict[str, Any]]:
    print_section_header("User Service: Create User")
    response = requests.post(f"{USER_SERVICE_URL}/users/", json=user_data)
    print_response_details(response)
    if response.status_code == 201:
        return response.json()
    return None

def test_user_service_login(username, password) -> Optional[str]:
    print_section_header(f"User Service: Login User - {username}")
    login_data = {"username": username, "password": password}
    response = requests.post(f"{USER_SERVICE_URL}/token", data=login_data)
    print_response_details(response)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def test_user_service_get_me(access_token: str):
    print_section_header("User Service: Get Current User (me)")
    if not access_token:
        print("No access token provided.")
        return
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{USER_SERVICE_URL}/users/me/", headers=headers)
    print_response_details(response)

def test_user_service_get_all_users():
    print_section_header("User Service: Get All Users")
    response = requests.get(f"{USER_SERVICE_URL}/users/")
    print_response_details(response)

# --- Admin Portal Backend Service Tests ---
def test_admin_portal_get_all_users():
    print_section_header("Admin Portal Backend: Get All Users")
    response = requests.get(f"{ADMIN_PORTAL_BACKEND_URL}/admin/users/")
    print_response_details(response)

# --- Storage Service Tests ---
def test_storage_service_upload_single_file(filename: str = "test_upload.txt", content: str = "Hello Storage!") -> Optional[Dict[str, Any]]:
    print_section_header("Storage Service: Upload Single File")
    # Create a dummy file
    with open(filename, "w") as f:
        f.write(content)
    
    files_payload = {'file': (filename, open(filename, 'rb'))}
    response = requests.post(f"{STORAGE_SERVICE_URL}/upload/file/", files=files_payload)
    
    # Clean up dummy file
    if os.path.exists(filename):
        os.remove(filename)
        
    print_response_details(response)
    if response.status_code == 200: # Assuming 200 OK for successful upload based on your main.py
        return response.json()
    return None

def test_storage_service_upload_multiple_files():
    print_section_header("Storage Service: Upload Multiple Files")
    file1_name = "multi_test1.txt"
    file2_name = "multi_test2.log"
    
    with open(file1_name, "w") as f1:
        f1.write("Content for file 1")
    with open(file2_name, "w") as f2:
        f2.write("Content for file 2 - log data")
        
    files_payload = [
        ('files', (file1_name, open(file1_name, 'rb'), 'text/plain')),
        ('files', (file2_name, open(file2_name, 'rb'), 'text/plain')) # FastAPI/Starlette might infer content type
    ]
    
    response = requests.post(f"{STORAGE_SERVICE_URL}/upload/files/", files=files_payload)
    
    if os.path.exists(file1_name):
        os.remove(file1_name)
    if os.path.exists(file2_name):
        os.remove(file2_name)
        
    print_response_details(response)

def test_storage_service_get_file(uploaded_filename: str):
    print_section_header(f"Storage Service: Get File - {uploaded_filename}")
    if not uploaded_filename:
        print("No filename provided for get_file test.")
        return

    response = requests.get(f"{STORAGE_SERVICE_URL}/files/{uploaded_filename}")
    print(f"URL: {response.url}")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Content (first 100 chars): {response.text[:100]}...")
    else:
        try:
            print(f"Response JSON: {response.json()}")
        except json.JSONDecodeError:
            print(f"Response Text: {response.text}")
    print("-" * 40)


if __name__ == "__main__":
    print("Starting Individual Service Tests...")

    # --- Test User Service ---
    new_user = generate_unique_user_data()
    created_user_response = test_user_service_create_user(new_user)
    user_token = None
    if created_user_response:
        user_token = test_user_service_login(new_user["username"], new_user["password"])
    if user_token:
        test_user_service_get_me(user_token)
    test_user_service_get_all_users()

    # --- Test Admin Portal Backend Service ---
    # This service currently calls user_service, so having users helps.
    test_admin_portal_get_all_users()

    # --- Test Storage Service ---
    uploaded_file_info = test_storage_service_upload_single_file()
    if uploaded_file_info and "filename" in uploaded_file_info:
        test_storage_service_get_file(uploaded_file_info["filename"])
    
    test_storage_service_upload_multiple_files()
    # To test get_file for multiple uploads, you'd need to parse the response from upload_multiple_files

    print("\nIndividual Service Tests Completed.")
