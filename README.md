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
        * **Sự cố hiện tại**: Service bị crash (ngắt kết nối không phản hồi khi API Gateway gọi tới) khi xử lý yêu cầu OCR ảnh (cụ thể là tại bước `predictor.predict()` bên trong VietOCR), ngay cả khi ảnh đã được resize. Nguyên nhân nghi ngờ nhất là do hết bộ nhớ (Out of Memory) hoặc lỗi ở tầng C/C++ của thư viện nền khi xử lý ảnh lớn/phức tạp, mặc dù RAM cho Docker đã được người dùng tăng lên 12GB.
        * Cần tiếp tục gỡ lỗi bằng cách thử nghiệm với ảnh nhỏ hơn, đơn giản hơn, theo dõi chặt chẽ tài nguyên container và các log chi tiết đã thêm vào.

5.  **eKYC Information Extraction Service (`ekyc_information_extraction_service`)**
    * **Mô tả**: Trích xuất thông tin có cấu trúc (Họ tên, Ngày sinh, Số CMND/CCCD, Địa chỉ, v.v.) từ kết quả OCR của giấy tờ tùy thân. Sử dụng phương pháp hybrid: ban đầu dùng regex, sau đó có thể fallback hoặc cải thiện bằng Google Gemini LLM nếu cần và được cấu hình.
    * **Công nghệ**: FastAPI, Python (cho regex), Google Generative AI SDK.
    * **Port**: `8005`
    * **Tình trạng**: **Đang phát triển - Phiên bản hybrid ban đầu đã tích hợp.** Hiệu quả hiện tại bị giới hạn nghiêm trọng bởi chất lượng và tính ổn định của đầu vào từ `generic-ocr-service`. Cần tinh chỉnh regex và prompt Gemini khi có kết quả OCR tốt và ổn định hơn.

6.  **Admin Portal Frontend (`admin_portal_frontend`)**
    * **Mô tả**: Giao diện web cho quản trị viên để xem danh sách người dùng và có thể là các thông tin quản trị khác.
    * **Công nghệ**: FastAPI (với Jinja2 templates), HTML, CSS.
    * **Port**: `8080`
    * **Tình trạng**: **Hoàn thiện cơ bản.** Đã có giao diện login (xác thực với User Service qua API Gateway) và hiển thị danh sách người dùng với phân trang chi tiết (lấy từ Admin Portal Backend Service qua API Gateway).

7.  **Admin Portal Backend Service (`admin_portal_backend_service`)**
    * **Mô tả**: Service backend cung cấp API cho Admin Portal Frontend, bao gồm xác thực admin và lấy dữ liệu từ User Service.
    * **Công nghệ**: FastAPI.
    * **Port**: `8002`
    * **Tình trạng**: **Hoàn thiện cơ bản.** Đã có API lấy danh sách user (yêu cầu xác thực admin) với thông tin phân trang đầy đủ.

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
    6.  Thực hiện OCR ảnh (Generic OCR Service - hiện đang sử dụng VietOCR).
    7.  Gửi kết quả OCR đến dịch vụ trích xuất thông tin eKYC (eKYC Information Extraction Service) và nhận lại thông tin đã trích xuất (có thể sử dụng Gemini fallback).
* **Lưu ý**: Bước OCR (số 6) hiện đang gặp sự cố. `generic-ocr-service` (sử dụng VietOCR) khởi động và load model thành công nhưng bị crash khi xử lý yêu cầu OCR ảnh thực tế, ngay cả khi ảnh đã được resize. Điều này khiến API Gateway trả về lỗi 503 cho client.

## Tình trạng Dự án Hiện tại (Tính đến 25/05/2025)

* **Hoàn thành cơ bản và Tích hợp**:
    * User Service (bao gồm xác thực JWT, phân trang).
    * Storage Service.
    * API Gateway.
    * Admin Portal Frontend & Backend Service (hiển thị danh sách người dùng với phân trang).
    * Container hóa toàn bộ các service trên bằng Docker và Docker Compose.
    * Kịch bản test tự động cho luồng tích hợp (ngoại trừ bước OCR đang lỗi).
    * `ekyc_information_extraction_service`: Phiên bản Hybrid ban đầu (Regex + tùy chọn Gemini fallback).
* **Đang phát triển và cần hoàn thiện/gỡ lỗi**:
    * **`generic_ocr_service`**: Đã chuyển sang sử dụng VietOCR. Service khởi động và load model (`vgg_transformer`) thành công. Tuy nhiên, đang gặp sự cố **crash khi gọi hàm `predict()`** trên ảnh (ngay cả khi ảnh đã được resize xuống 1024px). Nghi ngờ chính là do hết bộ nhớ (Out of Memory) hoặc lỗi ở tầng C/C++ của thư viện nền khi xử lý ảnh đầu vào (đặc biệt là ảnh lớn/phức tạp ban đầu như `IMG_4620.png`). Mặc dù RAM Docker đã được tăng lên 12GB, sự cố vẫn xảy ra. **Cần ưu tiên gỡ lỗi và ổn định service này.**
    * **`ekyc_information_extraction_service`**: Hiệu quả trích xuất phụ thuộc lớn vào kết quả OCR. Sẽ tiếp tục cải thiện khi `generic-ocr-service` ổn định và cung cấp OCR tốt hơn.
* **Ưu tiên tiếp theo**:
    1.  **Gỡ lỗi và Ổn định `generic-ocr-service` (VietOCR)**:
        * **Xác định và giải quyết nguyên nhân crash khi gọi hàm `predict()`**. Thử nghiệm với các ảnh có kích thước/độ phức tạp khác nhau (bắt đầu với ảnh rất nhỏ, đơn giản).
        * Theo dõi sát sao tài nguyên (CPU, RAM) của container `generic-ocr-service` trong quá trình xử lý ảnh bằng `docker stats`.
        * Nếu OOM là nguyên nhân, xem xét tối ưu hóa việc sử dụng bộ nhớ hoặc chọn model VietOCR nhẹ hơn nếu có.
    2.  **Nâng cao chất lượng Trích xuất thông tin**: Sau khi có OCR tốt, tập trung cải thiện `ekyc_information_extraction_service`.
    3.  Hoàn thiện các chức năng còn lại của Admin Portal.
    4.  Bắt đầu phát triển các dịch vụ liên quan đến Nhận dạng Khuôn mặt.

## Các Bước Phát triển Tiếp theo (Dự kiến)

1.  **Ổn định và Tối ưu `generic_ocr_service` (VietOCR)**: Đây là ưu tiên hàng đầu.
2.  **Nâng cao `ekyc_information_extraction_service`**:
    * Phát triển bộ regex toàn diện hơn. Tinh chỉnh prompt và logic xử lý kết quả từ Gemini để đạt độ chính xác cao nhất. Xây dựng bộ dữ liệu kiểm thử đa dạng.
3.  **Hoàn thiện Admin Portal**:
    * Frontend: Thêm các chức năng quản lý, tìm kiếm, phân trang chi tiết cho danh sách người dùng. Giao diện xem chi tiết một eKYC request.
    * Backend: Mở rộng API để hỗ trợ các chức năng quản trị mới.
4.  **Phát triển các Dịch vụ Nhận dạng Khuôn mặt**:
    * `Face Detection Service`: Phát hiện khuôn mặt trong ảnh.
    * `Face Comparison Service`: So sánh độ tương đồng giữa hai khuôn mặt.
    * `Liveness Service`: Chống giả mạo.
5.  **Hoàn thiện Luồng eKYC End-to-End**: Kết hợp tất cả các service để tạo thành một quy trình eKYC hoàn chỉnh từ lúc người dùng upload ảnh đến khi có kết quả xác minh.
6.  **Tài liệu hóa API**: Sử dụng Swagger/OpenAPI UI được cung cấp bởi FastAPI cho từng service và cho API Gateway.
7.  **Tối ưu và Bảo mật**: Rà soát, tối ưu hiệu năng và tăng cường các biện pháp bảo mật cho toàn hệ thống.