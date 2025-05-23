import requests
import json
import time
import os
from typing import Dict, Any, Optional, List

API_GATEWAY_URL = "http://localhost:8000"
ADMIN_PORTAL_FRONTEND_URL = "http://localhost:8080"

def print_section_header(title: str):
    print("\n" + "=" * 10 + f" {title} " + "=" * 10)

def print_response_details(response: requests.Response, message: str = ""):
    if message:
        print(message)
    print(f"URL: {response.url}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response JSON: {response.json()}")
    except json.JSONDecodeError:
        print(f"Response Text: {response.text[:500]}...")
    print("-" * 40)

def generate_unique_user_data() -> Dict[str, str]:
    timestamp = int(time.time() * 1000)
    return {
        "email": f"testuser{timestamp}@example.com",
        "username": f"testuser{timestamp}",
        "password": "SecurePassword123"
    }

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

def test_03_get_current_user_me(access_token: str):
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
    print(f"NOTE: This test assumes '{storage_upload_url}' is configured on API Gateway to forward to Storage Service.")

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
    print(f"NOTE: This test assumes '{storage_get_file_url}' is configured on API Gateway to forward to Storage Service.")

    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(storage_get_file_url, headers=headers)
        print(f"URL: {response.url}")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"Content-Type: {response.headers.get('content-type')}")
            print(f"Content length: {len(response.content)}")
        else:
            print_response_details(response)
    except requests.exceptions.ConnectionError as e:
        print(f"Could not connect to {storage_get_file_url}. Ensure API Gateway is running and the route is configured.")
        print(e)
    print("-" * 40)

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

    print("\n--- Storage Service Tests (Running) ---")
    
    uploaded_file_details = test_04_upload_single_file_via_gateway(user_token)
    if uploaded_file_details and "filename" in uploaded_file_details:
        filename_on_storage = uploaded_file_details["filename"]
        print(f"File uploaded to storage, unique name: {filename_on_storage}")
        time.sleep(1)
        test_05_get_file_via_gateway(user_token, filename_on_storage)
    else:
        print("File upload via gateway failed or test not run due to missing gateway config / error during upload.")
    
    print("\nFull API Flow Tests Completed.")
    print("Ensure API Gateway is correctly configured for all service routes.")