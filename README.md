# Project eKYC Microservices

Hệ thống eKYC bao gồm nhiều microservices để thực hiện các tác vụ xác minh danh tính điện tử.

## Mục tiêu Dự án

Xây dựng một hệ thống eKYC module hóa, dễ dàng mở rộng, bao gồm các chức năng chính như quản lý người dùng, lưu trữ file, OCR, trích xuất thông tin từ giấy tờ tùy thân, và nhận dạng khuôn mặt.

## Tổng quan Kiến trúc

Hệ thống sử dụng kiến trúc microservices, với mỗi service đảm nhiệm một chức năng cụ thể. API Gateway đóng vai trò là điểm vào duy nhất cho các request từ client, điều phối đến các service tương ứng. Tất cả các service được đóng gói bằng Docker và quản lý bởi Docker Compose.

## Các Services

1.  **User Service (`user_service`)**
    * **Mô tả**: Quản lý thông tin người dùng, bao gồm đăng ký, đăng nhập, xác thực token JWT.
    * **Công nghệ**: FastAPI, SQLAlchemy (hiện tại dùng SQLite, có kế hoạch cho PostgreSQL).
    * **Port**: `8001`
    * **Tình trạng**: **Hoàn thành và Đã tích hợp** (Đã kiểm thử thành công qua API Gateway).

2.  **API Gateway (`api_gateway`)**
    * **Mô tả**: Điểm vào duy nhất cho client, điều hướng request đến các microservices phù hợp, xử lý CORS, và có thể thực hiện xác thực ở tầng gateway.
    * **Công nghệ**: FastAPI, HTTPX.
    * **Port**: `8000`
    * **Tình trạng**: **Hoàn thành và Đã tích hợp** (Đã kiểm thử điều phối request thành công đến các dịch vụ User, Storage, Generic OCR, và eKYC Information Extraction).

3.  **Storage Service (`storage_service`)**
    * **Mô tả**: Lưu trữ và quản lý các file được upload (ví dụ: ảnh giấy tờ tùy thân, ảnh chân dung).
    * **Công nghệ**: FastAPI.
    * **Port**: `8003`
    * **Tình trạng**: **Hoàn thành và Đã tích hợp** (Đã kiểm thử upload và download file thành công qua API Gateway).

4.  **Generic OCR Service (`generic_ocr_service`)**
    * **Mô tả**: Thực hiện nhận dạng ký tự quang học (OCR) trên ảnh được cung cấp. Bao gồm các bước tiền xử lý ảnh (resize, grayscale, denoising, binarization, deskewing tùy chọn) và cho phép tùy chỉnh Page Segmentation Mode (PSM) của Tesseract.
    * **Công nghệ**: FastAPI, Pytesseract, OpenCV (headless).
    * **Port**: `8004`
    * **Tình trạng**: **Hoàn thành và Đã tích hợp**
        * Sử dụng Tesseract OCR Engine (phiên bản 5.3.0).
        * Hỗ trợ các ngôn ngữ (ví dụ: tiếng Việt - `vie`, tiếng Anh - `eng`).
        * Đã kiểm thử thành công việc lấy danh sách ngôn ngữ và OCR ảnh (với các tùy chọn tiền xử lý và PSM) qua API Gateway.

5.  **eKYC Information Extraction Service (`ekyc_information_extraction_service`)**
    * **Mô tả**: Trích xuất thông tin có cấu trúc (Họ tên, Ngày sinh, Số CMND/CCCD, Địa chỉ, v.v.) từ kết quả OCR của giấy tờ tùy thân. Sử dụng phương pháp hybrid: ban đầu dùng regex, sau đó có thể fallback hoặc cải thiện bằng Google Gemini LLM nếu cần và được cấu hình.
    * **Công nghệ**: FastAPI, Python (cho regex), Google Generative AI SDK.
    * **Port**: `8005`
    * **Tình trạng**: **Đang phát triển - Phiên bản hybrid (Regex + Gemini fallback) ban đầu đã được tích hợp và kiểm thử với luồng cơ bản qua API Gateway.** Cần tiếp tục tinh chỉnh regex, prompt Gemini và cải thiện chất lượng OCR đầu vào.

6.  **Admin Portal Frontend (`admin_portal_frontend`)**
    * **Mô tả**: Giao diện web cho quản trị viên để xem danh sách người dùng và có thể là các thông tin quản trị khác.
    * **Công nghệ**: FastAPI (với Jinja2 templates), HTML, CSS.
    * **Port**: `8080`
    * **Tình trạng**: **Đang tích hợp và hoàn thiện.** Đã có giao diện login (xác thực với User Service qua API Gateway) và hiển thị danh sách user (lấy từ Admin Portal Backend Service qua API Gateway). Cần hoàn thiện các chức năng quản lý và UI.

7.  **Admin Portal Backend Service (`admin_portal_backend_service`)**
    * **Mô tả**: Service backend cung cấp API cho Admin Portal Frontend, bao gồm xác thực admin và lấy dữ liệu từ User Service.
    * **Công nghệ**: FastAPI.
    * **Port**: `8002`
    * **Tình trạng**: **Đang tích hợp và hoàn thiện.** Đã có API lấy danh sách user (yêu cầu xác thực admin qua JWT) và đang được Admin Portal Frontend sử dụng.

8.  **Face Detection Service (`face_detection_service`)**
    * **Mô tả**: Phát hiện khuôn mặt trong ảnh (ví dụ: ảnh chân dung, ảnh trên giấy tờ tùy thân).
    * **Công nghệ**: FastAPI, các thư viện nhận dạng khuôn mặt (ví dụ: OpenCV, MTCNN).
    * **Port**: (Chưa xác định)
    * **Tình trạng**: **Kế hoạch**

9.  **Face Comparison Service (`face_comparison_service`)** (Hoặc là một phần của Face Recognition Service)
    * **Mô tả**: So sánh hai khuôn mặt để xác định mức độ tương đồng (ví dụ: so sánh ảnh chân dung với ảnh trên giấy tờ tùy thân).
    * **Công nghệ**: FastAPI, các thư viện nhận dạng khuôn mặt (ví dụ: face_recognition, DeepFace, ArcFace).
    * **Port**: (Chưa xác định)
    * **Tình trạng**: **Kế hoạch**

10. **Liveness Service (`liveness_service`)**
    * **Mô tả**: Xác định xem ảnh/video chân dung đầu vào có phải là từ một người thật, đang hiện diện hay không, nhằm chống giả mạo (ví dụ: dùng ảnh in, video phát lại).
    * **Công nghệ**: FastAPI, các kỹ thuật AI/ML cho liveness detection.
    * **Port**: (Chưa xác định)
    * **Tình trạng**: **Kế hoạch**

## Thiết lập và Chạy Dự án

1.  **Yêu cầu**:
    * Docker
    * Docker Compose
    * (Tùy chọn, nếu sử dụng Gemini) API Key từ Google AI Studio, được cấu hình trong tệp `.env`.

2.  **Các bước chạy**:
    * Clone repository (nếu có).
    * Đặt các file của từng service vào đúng cấu trúc thư mục như đã thiết kế.
    * Tạo tệp `.env` ở thư mục gốc của dự án (cùng cấp với `docker-compose.yml`) nếu muốn sử dụng Gemini, và thêm vào đó:
        ```
        GEMINI_API_KEY=your_actual_google_ai_studio_api_key
        ```
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
    7.  Thực hiện OCR ảnh với các tùy chọn PSM và tiền xử lý ảnh (Generic OCR Service).
    8.  Gửi kết quả OCR đến dịch vụ trích xuất thông tin eKYC (eKYC Information Extraction Service) và nhận lại thông tin đã trích xuất (có thể sử dụng Gemini fallback).
* Tất cả các bước kiểm thử này đều được thực hiện thông qua API Gateway và đã xác nhận hoạt động thành công ở mức độ tích hợp cơ bản.

## Tình trạng Dự án Hiện tại (Tính đến 24/05/2025)

* **Hoàn thành cơ bản và Tích hợp**:
    * User Service (bao gồm xác thực JWT).
    * Storage Service (upload/download file).
    * Generic OCR Service (sử dụng Tesseract, hỗ trợ đa ngôn ngữ, tiền xử lý ảnh nâng cao, tùy chỉnh PSM).
    * API Gateway (điều phối request đến các service trên).
    * Container hóa toàn bộ các service trên bằng Docker và Docker Compose.
    * Kịch bản test tự động cho luồng tích hợp các service đã hoàn thành (bao gồm cả bước gọi eKYC Information Extraction Service).
    * `ekyc_information_extraction_service`: Phiên bản Hybrid ban đầu (Regex + tùy chọn Gemini fallback) đã được tích hợp và kiểm thử.
    * `Admin Portal Frontend` và `Admin Portal Backend Service`: Đã tích hợp xác thực cơ bản và luồng lấy danh sách người dùng.
* **Đang phát triển và cần hoàn thiện**:
    * **`ekyc_information_extraction_service`**: Tinh chỉnh và mở rộng đáng kể các biểu thức chính quy, cải thiện prompt cho Gemini, thử nghiệm các mô hình Gemini khác nhau, và xử lý các trường hợp lỗi OCR phức tạp hơn.
    * **`generic_ocr_service`**: Tiếp tục thử nghiệm và tối ưu các bước tiền xử lý ảnh để cải thiện chất lượng OCR đầu vào cho ảnh CCCD/CMND thực tế.
    * **`Admin Portal Frontend` & `Admin Portal Backend Service`**: Hoàn thiện các chức năng quản trị, cải thiện UI/UX.
* **Ưu tiên tiếp theo**:
    1.  **Nâng cao chất lượng OCR và Trích xuất thông tin**:
        * Tập trung cải thiện `generic_ocr_service` (tiền xử lý ảnh, thử nghiệm Tesseract parameters).
        * Hoàn thiện và làm phức tạp hơn nữa logic trong `ekyc_information_extraction_service` (cả regex và prompt/logic Gemini).
    2.  Hoàn thiện Admin Portal (Frontend và Backend).
    3.  Bắt đầu phát triển các dịch vụ liên quan đến Nhận dạng Khuôn mặt.

## Các Bước Phát triển Tiếp theo (Dự kiến)

1.  **Nâng cao `generic_ocr_service` và `ekyc_information_extraction_service`**:
    * **OCR**: Nghiên cứu và áp dụng các kỹ thuật tiền xử lý ảnh tiên tiến hơn (ví dụ: deskewing, binarization nâng cao, phát hiện và loại bỏ vùng nhiễu, tự động crop vùng chứa thông tin). Xem xét các OCR engine khác nếu Tesseract không đáp ứng được yêu cầu về độ chính xác với ảnh chất lượng thấp.
    * **Extraction**: Phát triển bộ regex toàn diện hơn. Tinh chỉnh prompt và logic xử lý kết quả từ Gemini để đạt độ chính xác cao nhất. Xây dựng bộ dữ liệu kiểm thử đa dạng.
2.  **Hoàn thiện Admin Portal**:
    * Frontend: Thêm các chức năng quản lý, tìm kiếm, phân trang chi tiết cho danh sách người dùng. Giao diện xem chi tiết một eKYC request.
    * Backend: Mở rộng API để hỗ trợ các chức năng quản trị mới.
3.  **Phát triển các Dịch vụ Nhận dạng Khuôn mặt**:
    * `Face Detection Service`: Phát hiện khuôn mặt trong ảnh.
    * `Face Comparison Service`: So sánh độ tương đồng giữa hai khuôn mặt.
    * `Liveness Service`: Chống giả mạo.
4.  **Hoàn thiện Luồng eKYC End-to-End**: Kết hợp tất cả các service để tạo thành một quy trình eKYC hoàn chỉnh từ lúc người dùng upload ảnh đến khi có kết quả xác minh.
5.  **Tài liệu hóa API**: Sử dụng Swagger/OpenAPI UI được cung cấp bởi FastAPI cho từng service và cho API Gateway.
6.  **Tối ưu và Bảo mật**: Rà soát, tối ưu hiệu năng và tăng cường các biện pháp bảo mật cho toàn hệ thống.

