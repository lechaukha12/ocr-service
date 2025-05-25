# Project eKYC Microservices

Hệ thống eKYC bao gồm nhiều microservices để thực hiện các tác vụ xác minh danh tính điện tử.

## Mục tiêu Dự án

Xây dựng một hệ thống eKYC module hóa, dễ dàng mở rộng, bao gồm các chức năng chính như quản lý người dùng, lưu trữ file, OCR, trích xuất thông tin từ giấy tờ tùy thân, và nhận dạng khuôn mặt.

## Tổng quan Kiến trúc

Hệ thống sử dụng kiến trúc microservices, với mỗi service đảm nhiệm một chức năng cụ thể. API Gateway đóng vai trò là điểm vào duy nhất cho các request từ client, điều phối đến các service tương ứng. Tất cả các service được đóng gói bằng Docker và quản lý bởi Docker Compose.

## Các Services

1.  **User Service (`user_service`)**
    * **Mô tả**: Quản lý thông tin người dùng, bao gồm đăng ký, đăng nhập, xác thực token JWT.
    * **Công nghệ**: FastAPI, SQLAlchemy (SQLite).
    * **Port**: `8001`
    * **Tình trạng**: **Hoàn thành và Đã tích hợp**. Đã kiểm thử thành công qua API Gateway, bao gồm đăng ký, đăng nhập, lấy thông tin user, và hỗ trợ phân trang cho Admin Portal.

2.  **API Gateway (`api_gateway`)**
    * **Mô tả**: Điểm vào duy nhất cho client, điều hướng request đến các microservices phù hợp.
    * **Công nghệ**: FastAPI, HTTPX.
    * **Port**: `8000`
    * **Tình trạng**: **Hoàn thành và Đã tích hợp**. Đã kiểm thử điều phối request thành công đến các dịch vụ User, Storage, Generic OCR, và eKYC Information Extraction.

3.  **Storage Service (`storage_service`)**
    * **Mô tả**: Lưu trữ và quản lý các file được upload.
    * **Công nghệ**: FastAPI.
    * **Port**: `8003`
    * **Tình trạng**: **Hoàn thành và Đã tích hợp**. Đã kiểm thử upload và download file thành công qua API Gateway.

4.  **Generic OCR Service (`generic_ocr_service`)**
    * **Mô tả**: Thực hiện nhận dạng ký tự quang học (OCR) trên ảnh được cung cấp.
    * **Công nghệ**: FastAPI, **VietOCR (sử dụng PyTorch, OpenCV)**.
    * **Port**: `8004`
    * **Tình trạng**: **Đang gặp sự cố và cần gỡ lỗi.**
        * Đã chuyển từ Tesseract sang VietOCR để cải thiện chất lượng nhận dạng tiếng Việt.
        * Service khởi động và load model VietOCR (`vgg_transformer` trên CPU) thành công.
        * **Sự cố hiện tại**: Service bị crash (ngắt kết nối không phản hồi) khi xử lý yêu cầu OCR ảnh (cụ thể là tại bước `predictor.predict()`), ngay cả với ảnh đã được resize. Nguyên nhân nghi ngờ nhất là do hết bộ nhớ (Out of Memory) hoặc lỗi ở tầng C/C++ của thư viện nền khi xử lý ảnh lớn/phức tạp, mặc dù RAM cho Docker đã được tăng lên 12GB.
        * Cần tiếp tục gỡ lỗi bằng cách thử nghiệm với ảnh nhỏ hơn, đơn giản hơn và theo dõi chặt chẽ tài nguyên container.

5.  **eKYC Information Extraction Service (`ekyc_information_extraction_service`)**
    * **Mô tả**: Trích xuất thông tin có cấu trúc từ kết quả OCR. Sử dụng phương pháp hybrid: regex và Google Gemini fallback.
    * **Công nghệ**: FastAPI, Python (regex), Google Generative AI SDK.
    * **Port**: `8005`
    * **Tình trạng**: **Đang phát triển - Phiên bản hybrid ban đầu đã tích hợp.** Hiệu quả hiện tại bị giới hạn nghiêm trọng bởi chất lượng đầu vào từ `generic-ocr-service`. Cần tinh chỉnh regex và prompt Gemini khi có kết quả OCR tốt hơn.

6.  **Admin Portal Frontend (`admin_portal_frontend`)**
    * **Mô tả**: Giao diện web cho quản trị viên.
    * **Công nghệ**: FastAPI (Jinja2 templates), HTML, CSS.
    * **Port**: `8080`
    * **Tình trạng**: **Hoàn thiện cơ bản.** Đã có giao diện login (xác thực với User Service qua API Gateway) và hiển thị danh sách người dùng với phân trang chi tiết (lấy từ Admin Portal Backend Service).

7.  **Admin Portal Backend Service (`admin_portal_backend_service`)**
    * **Mô tả**: Service backend cung cấp API cho Admin Portal Frontend.
    * **Công nghệ**: FastAPI.
    * **Port**: `8002`
    * **Tình trạng**: **Hoàn thiện cơ bản.** Đã có API lấy danh sách user (yêu cầu xác thực admin) với thông tin phân trang đầy đủ.

8.  **Face Detection Service (`face_detection_service`)**
    * **Mô tả**: Phát hiện khuôn mặt trong ảnh.
    * **Công nghệ**: FastAPI, OpenCV, MTCNN (dự kiến).
    * **Port**: (Chưa xác định)
    * **Tình trạng**: **Kế hoạch**

9.  **Face Comparison Service (`face_comparison_service`)**
    * **Mô tả**: So sánh hai khuôn mặt.
    * **Công nghệ**: FastAPI, face_recognition, DeepFace (dự kiến).
    * **Port**: (Chưa xác định)
    * **Tình trạng**: **Kế hoạch**

10. **Liveness Service (`liveness_service`)**
    * **Mô tả**: Xác định người thật, chống giả mạo.
    * **Công nghệ**: FastAPI, AI/ML.
    * **Port**: (Chưa xác định)
    * **Tình trạng**: **Kế hoạch**

## Thiết lập và Chạy Dự án

(Giữ nguyên phần này)

## Kịch bản Kiểm thử Toàn bộ Luồng

* Một script `test_full_flow.py` đã được sử dụng để kiểm thử tự động các luồng chính:
    1.  Đăng ký người dùng mới (User Service).
    2.  Đăng nhập để lấy token (User Service).
    3.  Lấy thông tin người dùng hiện tại (User Service).
    4.  Upload file (Storage Service).
    5.  Tải file về (Storage Service).
    6.  Thực hiện OCR ảnh (Generic OCR Service - hiện đang sử dụng VietOCR).
    7.  Gửi kết quả OCR đến dịch vụ trích xuất thông tin eKYC (eKYC Information Extraction Service).
* **Lưu ý**: Bước OCR hiện đang gặp sự cố (service bị crash khi xử lý ảnh).

## Tình trạng Dự án Hiện tại (Tính đến 25/05/2025)

* **Hoàn thành cơ bản và Tích hợp**:
    * User Service (bao gồm xác thực JWT, phân trang).
    * Storage Service.
    * API Gateway.
    * Admin Portal Frontend & Backend Service (hiển thị danh sách người dùng với phân trang).
    * Container hóa toàn bộ các service bằng Docker và Docker Compose.
    * Kịch bản test tự động cho luồng tích hợp.
    * `ekyc_information_extraction_service`: Phiên bản Hybrid ban đầu (Regex + tùy chọn Gemini fallback).
* **Đang phát triển và cần hoàn thiện/gỡ lỗi**:
    * **`generic_ocr_service`**: Đã chuyển sang sử dụng VietOCR. Service khởi động và load model thành công, tuy nhiên đang gặp sự cố crash khi thực hiện `predict` trên ảnh (ngay cả khi ảnh đã được resize). Nghi ngờ chính là do hết bộ nhớ (OOM) hoặc lỗi ở tầng sâu của thư viện xử lý ảnh/model với ảnh đầu vào cụ thể. **Cần ưu tiên gỡ lỗi và ổn định service này.**
    * **`ekyc_information_extraction_service`**: Hiệu quả trích xuất phụ thuộc lớn vào kết quả OCR. Sẽ tiếp tục cải thiện khi `generic-ocr-service` ổn định và cung cấp OCR tốt hơn.
* **Ưu tiên tiếp theo**:
    1.  **Gỡ lỗi và Ổn định `generic-ocr-service` (VietOCR)**:
        * Xác định và giải quyết nguyên nhân crash khi gọi hàm `predict()`. Thử nghiệm với các kích thước ảnh khác nhau, ảnh đơn giản hơn. Theo dõi sát sao tài nguyên container.
        * Đánh giá chất lượng OCR của VietOCR với ảnh giấy tờ tùy thân thực tế sau khi service ổn định.
    2.  **Nâng cao chất lượng Trích xuất thông tin**: Sau khi có OCR tốt, tập trung cải thiện `ekyc_information_extraction_service`.
    3.  Hoàn thiện các chức năng còn lại của Admin Portal.
    4.  Bắt đầu phát triển các dịch vụ liên quan đến Nhận dạng Khuôn mặt.

## Các Bước Phát triển Tiếp theo (Dự kiến)

(Giữ nguyên phần này, nhưng lưu ý rằng việc ổn định OCR là điều kiện tiên quyết)