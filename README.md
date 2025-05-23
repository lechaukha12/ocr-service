# README - Dự án eKYC Microservices

## 1. Tổng quan Dự án

Dự án này nhằm mục đích xây dựng một hệ thống Định danh Khách hàng Điện tử (eKYC) toàn diện, được thiết kế theo kiến trúc microservices. Hệ thống cho phép người dùng cuối đăng ký tài khoản thông qua ứng dụng di động, bao gồm các bước xác minh danh tính bằng cách chụp ảnh giấy tờ tùy thân (CCCD, Hộ chiếu) và ảnh chân dung. Thông tin từ giấy tờ sẽ được bóc tách tự động (OCR), và khuôn mặt sẽ được so sánh để xác thực.

Ngoài ra, dự án bao gồm một cổng thông tin web (Admin Portal Frontend) được xây dựng bằng Python (FastAPI với Jinja2 templates) dành cho đội ngũ nội bộ để rà soát, phân tích các trường hợp eKYC đã được hệ thống xử lý tự động, từ đó đưa ra các điều chỉnh và tinh chỉnh tham số hệ thống nhằm cải thiện độ chính xác theo thời gian.

Mục tiêu chính là sử dụng các công cụ mã nguồn mở và miễn phí, với khả năng tích hợp API Gemini (gói miễn phí) cho các tác vụ nâng cao nếu cần.

## 2. Kiến trúc Microservices và Chức năng

Dưới đây là danh sách các microservice và chức năng chính của chúng:

* **user-service (Service Quản lý Người dùng)**
    * **Chức năng**:
        * Xử lý đăng ký tài khoản người dùng mới (username, email, mật khẩu).
        * Xác thực đăng nhập và tạo token truy cập (JWT).
        * Lưu trữ thông tin cơ bản của người dùng và trạng thái tài khoản.
        * Lưu trữ thông tin PII đã được xác minh từ CCCD/Hộ chiếu.
    * **Trạng thái**: Đã build (Giai đoạn 1 - cơ bản, sử dụng SQLite, Dockerized).

* **api-gateway (Cổng API)**
    * **Chức năng**:
        * Là điểm vào duy nhất cho tất cả các request từ client.
        * Điều hướng các request đến các microservice nội bộ.
    * **Trạng thái**: Đã build (Giai đoạn 1 - cơ bản, định tuyến cho user-service, Dockerized).

* **admin-portal-backend-service (Backend cho Cổng Admin Rà soát)**
    * **Chức năng**:
        * Cung cấp API cho Admin Portal Frontend.
        * Xác thực nhân viên truy cập portal (sẽ triển khai).
        * API để truy vấn và hiển thị chi tiết các trường hợp eKYC, thông tin người dùng từ user-service.
    * **Trạng thái**: Đã build (Giai đoạn 1 - cơ bản, lấy danh sách người dùng, Dockerized).

* **storage-service (Service Lưu trữ Tệp)**
    * **Chức năng**:
        * Quản lý việc lưu trữ an toàn và truy xuất tất cả các tệp hình ảnh/video của quy trình eKYC.
        * Cung cấp API cho các service khác để tải lên hoặc lấy tệp.
    * **Trạng thái**: Đã build (Giai đoạn 1 - cơ bản, lưu file cục bộ, Dockerized).

* **admin_portal_frontend (Frontend cho Cổng Admin Rà soát)**
    * **Chức năng**: Giao diện web cho phép đội ngũ nội bộ đăng nhập, xem danh sách người dùng, rà soát và phân tích các trường hợp eKYC.
    * **Trạng thái**: Đã build và hoạt động (Sử dụng Python FastAPI với Jinja2 templates, Dockerized).

* **generic-ocr-service (Service OCR Chung)**
    * **Chức năng**:
        * Service OCR độc lập, có khả năng tái sử dụng cho nhiều loại tài liệu.
        * Nhận ảnh, thực hiện tiền xử lý và OCR, trả về văn bản thô.
    * **Trạng thái**: Chưa build.

* **ekyc-information-extraction-service (Service Trích xuất Thông tin eKYC)**
    * **Chức năng**:
        * Nhận văn bản thô từ `generic-ocr-service`, trích xuất các trường thông tin cụ thể cho eKYC.
    * **Trạng thái**: Chưa build.

* **face-detection-service (Service Phát hiện Khuôn mặt)**
    * **Chức năng**: Phát hiện và trích xuất vùng chứa khuôn mặt từ ảnh.
    * **Trạng thái**: Chưa build.

* **face-comparison-service (Service So sánh Khuôn mặt)**
    * **Chức năng**: So sánh ảnh khuôn mặt từ giấy tờ với ảnh selfie, trả về điểm tương đồng.
    * **Trạng thái**: Chưa build.

* **liveness-service (Service Kiểm tra Người thật)**
    * **Chức năng**: Phân tích ảnh/video cử chỉ để xác định người dùng là thật.
    * **Trạng thái**: Chưa build.

* **Logic Điều phối (Orchestration Logic)**
    * **Chức năng**: Điều phối toàn bộ luồng nghiệp vụ eKYC.
    * **Trạng thái**: Chưa build (một phần cơ bản nằm trong api-gateway).

## 3. Trạng thái Phát triển Hiện tại

Chúng ta đã hoàn thành Giai đoạn 1 với việc xây dựng các service backend nền tảng, Admin Portal Frontend và một số chức năng cơ bản.

**Các service đã được build (đã Dockerize và chạy được qua Docker Compose):**

* `user-service`: Chức năng đăng ký, đăng nhập, lấy thông tin người dùng (sử dụng SQLite).
* `api-gateway`: Định tuyến các request cơ bản đến user-service.
* `admin-portal-backend-service`: API để lấy danh sách người dùng.
* `storage-service`: API để upload và tải file cơ bản (lưu trữ cục bộ).
* `admin_portal_frontend`: Giao diện web quản trị cơ bản (FastAPI + Jinja2).

**Các service/chức năng CHƯA build hoặc đang trong kế hoạch (theo thứ tự ưu tiên dự kiến):**

* `generic-ocr-service`
* `ekyc-information-extraction-service`
* `face-detection-service`
* `face-comparison-service`
* `liveness-service`
* Hoàn thiện logic điều phối eKYC.
* Tích hợp PostgreSQL cho `user_service` (Tạm hoãn).
* Frontend cho Mobile App.

## 4. Công nghệ Chính (Dự kiến và Hiện tại)

* **Backend**: Python (FastAPI)
* **Admin Portal Frontend**: Python (FastAPI + Jinja2 templates)
* **Cơ sở dữ liệu**: SQLite (cho `user_service` hiện tại). PostgreSQL (dự kiến tích hợp, hiện tại tạm hoãn).
* **Xử lý ảnh/Video**: OpenCV-Python
* **OCR**: Tesseract OCR (thông qua pytesseract) - *Dự kiến cho `generic-ocr-service`*
* **Phát hiện & So sánh Khuôn mặt**: OpenCV, thư viện `face_recognition` (dlib) - *Dự kiến*
* **Liveness Detection (Cơ bản)**: OpenCV, có thể thử nghiệm API Gemini Vision (free tier) - *Dự kiến*
* **Lưu trữ tệp**: Hệ thống tệp cục bộ (cho `storage-service` hiện tại).
* **Containerization**: Docker, Docker Compose.
* **API Gateway**: FastAPI (hiện tại).

## 5. Hướng Phát triển Tiếp theo

1.  **Bắt đầu phát triển `generic-ocr-service`**:
    * Tập trung vào việc nhận diện văn bản từ ảnh giấy tờ tùy thân.
2.  **Phát triển `ekyc-information-extraction-service`**:
    * Xử lý output từ `generic-ocr-service` để trích xuất thông tin có cấu trúc.
3.  **Tiếp tục với các service xử lý ảnh**:
    * `face-detection-service`
    * `face-comparison-service`
    * `liveness-service`
4.  **Hoàn thiện Logic Điều phối eKYC**: Xây dựng hoặc mở rộng logic để kết nối các service OCR và xử lý ảnh thành một quy trình eKYC hoàn chỉnh.
5.  **Xem xét Frontend cho Mobile App**: Lên kế hoạch và phát triển nếu cần thiết.
6.  **(Tạm hoãn) Tích hợp PostgreSQL vào `user_service`**: Sẽ thực hiện khi có nhu cầu về hiệu năng và mở rộng cao hơn.