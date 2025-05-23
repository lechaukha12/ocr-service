# Project eKYC Microservices

Hệ thống eKYC bao gồm nhiều microservices để thực hiện các tác vụ xác minh danh tính điện tử.

## Mục tiêu Dự án

Xây dựng một hệ thống eKYC module hóa, dễ dàng mở rộng, bao gồm các chức năng chính như quản lý người dùng, lưu trữ file, OCR, trích xuất thông tin từ giấy tờ tùy thân, và nhận dạng khuôn mặt.

## Tổng quan Kiến trúc

Hệ thống sử dụng kiến trúc microservices, với mỗi service đảm nhiệm một chức năng cụ thể. API Gateway đóng vai trò là điểm vào duy nhất cho các request từ client, điều phối đến các service tương ứng. Tất cả các service được đóng gói bằng Docker và quản lý bởi Docker Compose.

## Các Services

1.  **User Service (`user_service`)**
    * **Mô tả**: Quản lý thông tin người dùng, bao gồm đăng ký, đăng nhập, xác thực token JWT.
    * **Công nghệ**: FastAPI, PostgreSQL, SQLAlchemy.
    * **Port**: `8001`
    * **Tình trạng**: **Hoàn thành và Đã tích hợp** (Đã kiểm thử thành công qua API Gateway).

2.  **API Gateway (`api_gateway`)**
    * **Mô tả**: Điểm vào duy nhất cho client, điều hướng request đến các microservices phù hợp, xử lý CORS, và có thể thực hiện xác thực ở tầng gateway.
    * **Công nghệ**: FastAPI, HTTPX.
    * **Port**: `8000`
    * **Tình trạng**: **Hoàn thành và Đã tích hợp** (Đã kiểm thử điều phối request thành công đến User Service, Storage Service, và Generic OCR Service).

3.  **Storage Service (`storage_service`)**
    * **Mô tả**: Lưu trữ và quản lý các file được upload (ví dụ: ảnh giấy tờ tùy thân, ảnh chân dung).
    * **Công nghệ**: FastAPI.
    * **Port**: `8003` (Lưu ý: file `docker-compose.yml` đang map tới `8003` cho service này)
    * **Tình trạng**: **Hoàn thành và Đã tích hợp** (Đã kiểm thử upload và download file thành công qua API Gateway).

4.  **Generic OCR Service (`generic_ocr_service`)**
    * **Mô tả**: Thực hiện nhận dạng ký tự quang học (OCR) trên ảnh được cung cấp.
    * **Công nghệ**: FastAPI, Pytesseract, OpenCV (headless).
    * **Port**: `8004`
    * **Tình trạng**: **Hoàn thành và Đã tích hợp**
        * Sử dụng Tesseract OCR Engine (phiên bản 5.3.0).
        * Hỗ trợ các ngôn ngữ (ví dụ: tiếng Việt - `vie`, tiếng Anh - `eng`).
        * Đã kiểm thử thành công việc lấy danh sách ngôn ngữ và OCR ảnh qua API Gateway.

5.  **Admin Portal Frontend (`admin_portal_frontend`)**
    * **Mô tả**: Giao diện web cho quản trị viên để xem danh sách người dùng và có thể là các thông tin quản trị khác.
    * **Công nghệ**: FastAPI (với Jinja2 templates), HTML, CSS.
    * **Port**: `8080`
    * **Tình trạng**: **Đang phát triển / Cơ bản** (Đã có giao diện login và hiển thị danh sách user cơ bản, cần hoàn thiện).

6.  **Admin Portal Backend Service (`admin_portal_backend_service`)**
    * **Mô tả**: Service backend cung cấp API cho Admin Portal Frontend.
    * **Công nghệ**: FastAPI.
    * **Port**: `8002`
    * **Tình trạng**: **Đang phát triển / Cơ bản** (Đã có API lấy danh sách user, cần hoàn thiện).

7.  **eKYC Information Extraction Service (`ekyc_information_extraction_service`)**
    * **Mô tả**: Trích xuất thông tin có cấu trúc (Họ tên, Ngày sinh, Số CMND/CCCD, Địa chỉ, v.v.) từ kết quả OCR của giấy tờ tùy thân.
    * **Công nghệ**: FastAPI, các thư viện xử lý ngôn ngữ tự nhiên (NLP) và regex.
    * **Port**: (Chưa xác định)
    * **Tình trạng**: **Kế hoạch / Tiếp theo**

8.  **Face Recognition Service (`face_recognition_service`)**
    * **Mô tả**: So sánh ảnh chân dung với ảnh trên giấy tờ tùy thân để xác minh danh tính.
    * **Công nghệ**: FastAPI, các thư viện nhận dạng khuôn mặt (ví dụ: face_recognition, OpenCV).
    * **Port**: (Chưa xác định)
    * **Tình trạng**: **Kế hoạch**

## Thiết lập và Chạy Dự án

1.  **Yêu cầu**:
    * Docker
    * Docker Compose

2.  **Các bước chạy**:
    * Clone repository (nếu có).
    * Đặt các file của từng service vào đúng cấu trúc thư mục như đã thiết kế.
    * Từ thư mục gốc của dự án (chứa file `docker-compose.yml`), chạy lệnh:
        ```bash
        docker-compose up -d --build
        ```
    * Các service sẽ được khởi chạy. Truy cập API Gateway tại `http://localhost:8000`.

## Kịch bản Kiểm thử Toàn bộ Luồng

* Một script `test_full_flow.py` đã được tạo và sử dụng để kiểm thử tự động các luồng chính của hệ thống:
    1.  Đăng ký người dùng mới (User Service).
    2.  Đăng nhập để lấy token (User Service).
    3.  Lấy thông tin người dùng hiện tại (User Service).
    4.  Upload file (Storage Service).
    5.  Tải file về (Storage Service).
    6.  Lấy danh sách ngôn ngữ OCR (Generic OCR Service).
    7.  Thực hiện OCR ảnh (Generic OCR Service).
* Tất cả các bước kiểm thử này đều được thực hiện thông qua API Gateway và đã xác nhận hoạt động thành công.

## Tình trạng Dự án Hiện tại (Tính đến 23/05/2025)

* **Hoàn thành**:
    * User Service (bao gồm xác thực JWT).
    * Storage Service (upload/download file).
    * Generic OCR Service (sử dụng Tesseract, hỗ trợ đa ngôn ngữ).
    * API Gateway (điều phối request đến các service trên).
    * Container hóa toàn bộ các service trên bằng Docker và Docker Compose.
    * Kịch bản test tự động cho luồng tích hợp các service đã hoàn thành.
* **Đang phát triển**:
    * Admin Portal Frontend (giao diện cơ bản).
    * Admin Portal Backend Service (API cơ bản).
* **Ưu tiên tiếp theo**:
    * Hoàn thiện Admin Portal (Frontend và Backend).
    * Phát triển **eKYC Information Extraction Service** để trích xuất thông tin từ kết quả OCR.

## Các Bước Phát triển Tiếp theo (Dự kiến)

1.  **Hoàn thiện Admin Portal**:
    * Frontend: Thêm các chức năng quản lý, tìm kiếm, phân trang cho danh sách người dùng.
    * Backend: Mở rộng API để hỗ trợ các chức năng quản trị mới.
2.  **Phát triển eKYC Information Extraction Service**:
    * Xây dựng logic để phân tích text từ OCR và trích xuất các trường thông tin quan trọng.
    * Tích hợp service này vào luồng eKYC chung qua API Gateway.
3.  **Phát triển Face Recognition Service**:
    * Xây dựng logic so khớp khuôn mặt.
    * Tích hợp service.
4.  **Hoàn thiện Luồng eKYC End-to-End**: Kết hợp tất cả các service để tạo thành một quy trình eKYC hoàn chỉnh.
5.  **Tài liệu hóa API**: Sử dụng Swagger/OpenAPI UI được cung cấp bởi FastAPI cho từng service và cho API Gateway.
6.  **Tối ưu và Bảo mật**: Rà soát, tối ưu hiệu năng và tăng cường các biện pháp bảo mật cho toàn hệ thống.