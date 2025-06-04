import requests
import os

def find_real_image(basename: str):
    for ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".JPG", ".JPEG", ".PNG"]:
        filename = f"{basename}{ext}"
        if os.path.exists(filename):
            return filename
    return None

API_GATEWAY_URL = "http://localhost:8000"

def test_ekyc_full_flow():
    # 1. Đăng ký và đăng nhập user
    user_data = {
        "email": f"ekycuser_{os.getpid()}@example.com",
        "username": f"ekycuser_{os.getpid()}",
        "password": "TestPassword123",
        "full_name": "Test Ekyc User"
    }
    r = requests.post(f"{API_GATEWAY_URL}/auth/users/", json=user_data)
    print("Register:", r.status_code, r.text)
    r = requests.post(f"{API_GATEWAY_URL}/auth/token", data={"username": user_data["username"], "password": user_data["password"]})
    print("Login:", r.status_code, r.text)
    assert r.status_code == 200
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Chuẩn bị file ảnh
    cccd_path = find_real_image("IMG_4620")
    selfie_path = find_real_image("IMG_4637")
    assert cccd_path and selfie_path, "Thiếu ảnh test"

    # 3. Gọi API full_flow
    files = {
        "cccd_image": (os.path.basename(cccd_path), open(cccd_path, "rb"), "image/jpeg"),
        "selfie_image": (os.path.basename(selfie_path), open(selfie_path, "rb"), "image/jpeg")
    }
    data = {"lang": "vie"}
    r = requests.post(f"{API_GATEWAY_URL}/ekyc/full_flow/", files=files, data=data, headers=headers)
    print("\n===== eKYC Full Flow Response =====")
    print("Status:", r.status_code)
    try:
        print(r.json())
    except Exception:
        print(r.text)
    for f in files.values():
        if hasattr(f[1], 'close'):
            f[1].close()

if __name__ == "__main__":
    test_ekyc_full_flow()
