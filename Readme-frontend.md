# Admin Portal Frontend - Dịch vụ OCR

Dịch vụ này chịu trách nhiệm cho giao diện người dùng quản trị của hệ thống OCR. Nó được xây dựng bằng FastAPI và Jinja2 templates.

## Cài đặt và Chạy với Docker

Để build và chạy dịch vụ này bằng Docker, bạn cần có Docker và Docker Compose (khuyến nghị) đã được cài đặt.

**Cấu trúc thư mục dự kiến cho `admin-portal-frontend`:**


admin-portal-frontend/
├── Dockerfile
├── main.py
├── config.py
├── requirements.txt
└── templates/
├── login.html
├── dashboard_layout.html
└── user_list.html
└── ... (các template khác)


**Dockerfile:**

Dockerfile để build image cho dịch vụ này có thể tham khảo trong Canvas (hiện tại là artifact `dockerfile_frontend_v2`).

**Build và Chạy:**

1.  **Build image:**
    Mở terminal, di chuyển đến thư mục gốc của dự án OCR (nơi chứa `docker-compose.yml`) và chạy:
    ```bash
    docker-compose build admin-portal-frontend
    ```
    Hoặc nếu build thủ công từ thư mục `admin-portal-frontend` (nơi chứa Dockerfile này):
    ```bash
    docker build -t ocr-service-admin-portal-frontend .
    ```

2.  **Chạy container:**
    Sử dụng Docker Compose:
    ```bash
    docker-compose up -d admin-portal-frontend
    ```
    Hoặc chạy thủ công (đảm bảo các service phụ thuộc như backend đã chạy và network được cấu hình đúng):
    ```bash
    docker run -d -p 8080:8080 --name admin-portal-frontend-container ocr-service-admin-portal-frontend
    ```

Ứng dụng frontend sẽ có thể truy cập tại `http://localhost:8080` (nếu cổng 8080 được map từ `docker-compose.yml` hoặc lệnh `docker run`).

## Lỗi Hiện Tại và Gỡ Lỗi (Troubleshooting)

**Lỗi đang gặp phải (dựa trên log gần nhất):**


Traceback (most recent call last):
File "/app/admin_portal_frontend/main.py", line 13, in 
from config import settings
ModuleNotFoundError: No module named 'config'


**Nguyên nhân có thể:**

Lỗi này xảy ra khi ứng dụng Python (cụ thể là file `main.py` trong service `admin-portal-frontend`) cố gắng import module `config` (từ dòng `from config import settings`) nhưng không tìm thấy file `config.py`. Điều này thường là do:

1.  **File `config.py` không được sao chép vào Docker image:**
    Kiểm tra lại Dockerfile (tham khảo artifact `dockerfile_frontend_v2` trong Canvas). Dòng `COPY ./admin_portal_frontend/ /app/admin_portal_frontend/` (hoặc một lệnh `COPY` tương tự) phải đảm bảo file `config.py` (nằm trong thư mục `admin_portal_frontend` trên máy local của bạn) được sao chép vào thư mục `/app/admin_portal_frontend/` bên trong image.
2.  **File `config.py` bị thiếu trong thư mục nguồn:**
    Đảm bảo rằng file `config.py` thực sự tồn tại trong thư mục `admin_portal_frontend` trên máy của bạn trước khi build Docker image.
3.  **Đường dẫn import hoặc `WORKDIR` không chính xác:**
    Nếu `WORKDIR` trong Dockerfile là `/app` và bạn copy toàn bộ thư mục `admin_portal_frontend` vào `/app` (tức là cấu trúc bên trong image sẽ là `/app/admin_portal_frontend/main.py` và `/app/admin_portal_frontend/config.py`), thì câu lệnh `CMD` trong Dockerfile phải trỏ đúng đến module main, ví dụ: `CMD ["uvicorn", "admin_portal_frontend.main:app", ...]`. Và dòng import `from config import settings` trong `main.py` sẽ đúng nếu `config.py` nằm cùng cấp với `main.py` *bên trong thư mục package `admin_portal_frontend` đó*.

**Cách kiểm tra:**

* Xem lại nội dung Dockerfile.
* Kiểm tra cấu trúc file trong thư mục `admin_portal_frontend` trên máy local.
* Sau khi build image, bạn có thể chạy một container tạm thời từ image đó để kiểm tra cấu trúc file bên trong:
    ```bash
    docker run --rm -it ocr-service-admin-portal-frontend ls -l /app/admin_portal_frontend/
    ```
    Lệnh này sẽ liệt kê các file trong thư mục `/app/admin_portal_frontend/` bên trong container, giúp bạn xác nhận `config.py` có ở đó không.

Sau khi sửa lỗi, hãy build lại image và khởi động lại container.

