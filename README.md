# Project eKYC Microservices

Hệ thống eKYC bao gồm nhiều microservices để thực hiện các tác vụ xác minh danh tính điện tử.

## Mục tiêu Dự án

Xây dựng một hệ thống eKYC module hóa, dễ dàng mở rộng, bao gồm các chức năng chính như quản lý người dùng, lưu trữ file, OCR, trích xuất thông tin từ giấy tờ tùy thân, và nhận dạng khuôn mặt.

## Tổng quan Kiến trúc

Hệ thống sử dụng kiến trúc microservices, với mỗi service đảm nhiệm một chức năng cụ thể. API Gateway đóng vai trò là điểm vào duy nhất cho các request từ client, điều phối đến các service tương ứng. Tất cả các service được đóng gói bằng Docker và quản lý bởi Docker Compose.

## Các Services

1.  **User Service (`user_service`)**
    * **Mô tả**: Quản lý thông tin người dùng, bao gồm đăng ký, đăng nhập, xác thực token JWT.
    * **Công nghệ**: FastAPI, SQLAlchemy (SQLite), Passlib (bcrypt).
    * **Port**: `8001`
    * **Tình trạng**: **Hoạt động tốt**. Lỗi "attempt to write a readonly database" đã được khắc phục bằng cách sử dụng named volume cho SQLite database. Cảnh báo nhỏ liên quan đến `bcrypt` khi `passlib` đọc phiên bản vẫn còn, nhưng không ảnh hưởng chức năng.

2.  **API Gateway (`api_gateway`)**
    * **Mô tả**: Điểm vào duy nhất cho client, điều hướng request đến các microservices phù hợp.
    * **Công nghệ**: FastAPI, HTTPX.
    * **Port**: `8000`
    * **Tình trạng**: **Hoạt động**. Đã kiểm thử điều phối request thành công đến các dịch vụ User, Storage, Generic OCR (phiên bản Gemini), và eKYC Information Extraction.

3.  **Storage Service (`storage_service`)**
    * **Mô tả**: Lưu trữ và quản lý các file được upload.
    * **Công nghệ**: FastAPI, AIOFiles.
    * **Port**: `8003`
    * **Tình trạng**: **Hoạt động**. Đã kiểm thử upload và download file thành công qua API Gateway.

4.  **Generic OCR Service (`generic_ocr_service`) - Phiên bản Gemini**
    * **Mô tả**: Thực hiện nhận dạng ký tự quang học (OCR) trên ảnh được cung cấp bằng cách sử dụng Google Gemini API.
    * **Công nghệ hiện tại**: FastAPI, HTTPX (để gọi Gemini API), Pillow. Sử dụng model `gemini-2.0-flash` để xử lý ảnh và trích xuất văn bản.
    * **Logic hoạt động**: Nhận file ảnh, chuyển đổi sang base64, gửi đến Gemini API cùng với prompt yêu cầu OCR, nhận về văn bản và trả cho client. Có tích hợp chức năng đếm token (input/output) cho mỗi request Gemini và ghi log.
    * **Port**: `8004`
    * **Tình trạng**: **Hoạt động tốt**. Đã kiểm thử thành công với ảnh CCCD mẫu, Gemini trả về kết quả OCR chính xác và đầy đủ. Service yêu cầu cấu hình `OCR_GEMINI_API_KEY`.

5.  **eKYC Information Extraction Service (`ekyc_information_extraction_service`) - Phiên bản Regex-Only**
    * **Mô tả**: Trích xuất thông tin có cấu trúc (Họ tên, Ngày sinh, Số CMND/CCCD, Địa chỉ, v.v.) từ kết quả OCR của giấy tờ tùy thân, **chỉ sử dụng biểu thức chính quy (Regex)**.
    * **Công nghệ**: FastAPI, Python (cho regex).
    * **Port**: `8005`
    * **Tình trạng**: **Hoạt động một phần**.
        * Service này nhận input text từ `generic-ocr-service` (phiên bản Gemini).
        * **Trích xuất thành công các trường**: `id_number`, `date_of_birth`, `gender`, `nationality`, `place_of_origin`, `place_of_residence`, `expiry_date` với độ chính xác khá tốt sau các lần tinh chỉnh Regex.
        * **Vấn đề còn tồn tại**:
            * Trường `full_name` vẫn chưa trích xuất được (`null`). Log gần nhất cho thấy vẫn còn lỗi "Regex compilation/matching error" ("bad character range") liên quan đến pattern của `full_name`, dù đã có nhiều nỗ lực sửa đổi. Cần tiếp tục xem xét kỹ lưỡng định nghĩa các biến ký tự cho phép và cách chúng được sử dụng trong pattern Regex của `full_name`.
            * Các trường `date_of_issue`, `place_of_issue`, `personal_identification_features`, `ethnicity`, `religion` không được trích xuất. Điều này là **đúng và mong đợi** vì các thông tin này không có trên mặt trước của Căn cước công dân gắn chip đang được sử dụng để test.
        * **Không còn sử dụng Gemini fallback**: Service đã được cập nhật để chỉ dựa vào Regex.

6.  **Admin Portal Frontend (`admin_portal_frontend`)**
    * **Mô tả**: Giao diện web cho quản trị viên để xem danh sách người dùng.
    * **Công nghệ**: FastAPI (với Jinja2 templates), HTML, CSS.
    * **Port**: `8080`
    * **Tình trạng**: **Hoàn thiện cơ bản**.

7.  **Admin Portal Backend Service (`admin_portal_backend_service`)**
    * **Mô tả**: Service backend cung cấp API cho Admin Portal Frontend.
    * **Công nghệ**: FastAPI.
    * **Port**: `8002`
    * **Tình trạng**: **Hoàn thiện cơ bản**.

8.  **Face Detection Service (`face_detection_service`)**: Kế hoạch.
9.  **Face Comparison Service (`face_comparison_service`)**: Kế hoạch.
10. **Liveness Service (`liveness_service`)**: Kế hoạch.

## Thiết lập và Chạy Dự án

1.  **Yêu cầu**:
    * Docker
    * Docker Compose
    * API Key từ Google AI Studio (hoặc Google Cloud Vertex AI) cho Gemini. Hiện tại chỉ cần cho `generic-ocr-service`:
        * Một key cho `generic-ocr-service` (sẽ được cấu hình qua biến môi trường `OCR_GEMINI_API_KEY`).
    * Key này cần được khai báo trong file `.env` ở thư mục gốc của dự án (cùng cấp với `docker-compose.yml`):
        ```env
        # Ví dụ nội dung file .env
        OCR_GEMINI_API_KEY=your_actual_ocr_gemini_api_key
        # GEMINI_API_KEY=your_actual_ekyc_gemini_api_key # Không còn cần thiết cho ekyc_information_extraction_service
        ```

2.  **Các bước chạy**:
    * Clone repository (nếu có).
    * Đặt các file của từng service vào đúng cấu trúc thư mục.
    * Tạo file `.env` ở thư mục gốc dự án và điền API key như hướng dẫn ở trên.
    * Từ thư mục gốc của dự án (chứa file `docker-compose.yml`), chạy lệnh:
        ```bash
        docker-compose up -d --build
        ```
    * Các service sẽ được khởi chạy. Truy cập API Gateway tại `http://localhost:8000`.

## Kịch bản Kiểm thử

* Sử dụng script `test_ocr_service.py` để kiểm tra riêng `generic-ocr-service` (phiên bản Gemini).
* Sử dụng script `test_full_flow.py` để kiểm tra toàn bộ luồng từ OCR đến trích xuất thông tin eKYC.

## Tình trạng Dự án Hiện tại (Tính đến 28/05/2025)

* **Các thành phần hoạt động tốt**:
    * User Service.
    * Storage Service.
    * API Gateway.
    * Admin Portal Frontend & Backend Service.
    * `generic-ocr-service` (phiên bản Gemini) hoạt động tốt, cung cấp OCR chất lượng cao.

* **`ekyc_information_extraction_service` (Regex-Only)**:
    * Hoạt động, nhận input từ `generic-ocr-service`.
    * Trích xuất thành công nhiều trường quan trọng.
    * **Vấn đề chính**: Trường `full_name` vẫn chưa trích xuất được do lỗi Regex ("bad character range"). Cần tiếp tục tinh chỉnh Regex cho trường này.
    * Các trường không có trên mặt trước CCCD (ngày cấp, nơi cấp, đặc điểm nhận dạng, dân tộc, tôn giáo) không được trích xuất là đúng.

* **Các vấn đề cần giải quyết và cải thiện**:
    1.  **Tinh chỉnh Regex cho `full_name` trong `ekyc_information_extraction_service`**: Đây là ưu tiên hàng đầu để hoàn thiện chức năng trích xuất.
    2.  **Chi phí Token Gemini cho `generic-ocr-service`**: Theo dõi và cân nhắc nếu cần tối ưu.
    3.  **Cảnh báo `bcrypt` trong `user-service`**: Vấn đề nhỏ, có thể xem xét sau.

## Ưu tiên Tiếp theo

1.  **Sửa lỗi Regex và hoàn thiện trích xuất `full_name`** trong `ekyc_information_extraction_service`.
2.  Kiểm thử toàn diện luồng eKYC với nhiều ảnh CCCD khác nhau sau khi `full_name` được sửa.
3.  Xem xét tối ưu hóa chi phí token nếu cần.
4.  Phát triển các dịch vụ liên quan đến Nhận dạng Khuôn mặt theo kế hoạch.