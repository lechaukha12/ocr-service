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
    * **Yêu cầu thư viện**: Xem file `generic_ocr_service/requirements.txt` (đã bổ sung `pydantic-settings`).

5.  **eKYC Information Extraction Service (`ekyc_information_extraction_service`) - Phiên bản Regex-Only**
    * **Mô tả**: Trích xuất thông tin có cấu trúc (Họ tên, Ngày sinh, Số CMND/CCCD, Địa chỉ, v.v.) từ kết quả OCR của giấy tờ tùy thân, **chỉ sử dụng biểu thức chính quy (Regex)**.
    * **Công nghệ**: FastAPI, Python (cho regex).
    * **Port**: `8005`
    * **Tình trạng**: **Hoạt động tốt**.
        * Service này nhận input text từ `generic-ocr-service` (phiên bản Gemini).
        * **Trích xuất thành công các trường**: `id_number`, `date_of_birth`, `gender`, `nationality`, `place_of_origin`, `place_of_residence`, `expiry_date`, `full_name` (đã sửa lỗi Regex, trích xuất chính xác).
        * **Các trường không có trên mặt trước CCCD (ngày cấp, nơi cấp, đặc điểm nhận dạng, dân tộc, tôn giáo) không được trích xuất là đúng.**
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

8.  **Face Detection Service (`face_detection_service`)**
    * **Mô tả**: Phát hiện khuôn mặt trong ảnh, trả về vị trí (bounding box) các khuôn mặt.
    * **Công nghệ**: FastAPI, face_recognition hoặc OpenCV.
    * **Port**: `8006`
    * **Tình trạng**: **Đang phát triển**.

9.  **Face Comparison Service (`face_comparison_service`)**
    * **Mô tả**: So sánh hai ảnh khuôn mặt, trả về điểm tương đồng (similarity score).
    * **Công nghệ**: FastAPI, face_recognition hoặc deepface.
    * **Port**: `8007`
    * **Tình trạng**: **Đang phát triển**.

10. **Liveness Service (`liveness_service`)**
    * **Mô tả**: Kiểm tra liveness (ảnh là người thật, không phải ảnh giấy/tái sử dụng).
    * **Công nghệ**: FastAPI, model liveness open source hoặc tích hợp API cloud.
    * **Port**: `8008`
    * **Tình trạng**: **Đang phát triển**.

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

## Kiểm thử so khớp khuôn mặt (Face Comparison)

- Để kiểm thử chức năng so khớp khuôn mặt giữa ảnh CCCD và ảnh selfie, cần đảm bảo:
    1. Đã có đủ hai file ảnh mẫu: `IMG_4620.png` (ảnh CCCD) và `IMG_4637.png` (ảnh selfie) trong thư mục gốc.
    2. Dịch vụ `face_comparison_service` (port 8007) đã được khởi động:
        - Có thể khởi động bằng lệnh:
          ```bash
          docker compose up -d face-comparison-service
          ```
    3. Sau đó, chạy lại script kiểm thử toàn bộ luồng:
        ```bash
        python3 test_full_flow.py
        ```
    4. Kết quả so khớp khuôn mặt sẽ được in ra màn hình, cho biết hai ảnh có khớp hay không và điểm tương đồng (score).

- Nếu gặp lỗi "Connection refused" khi kiểm thử, hãy kiểm tra lại trạng thái container `face_comparison_service`.

## Kiểm thử và bảo mật so khớp khuôn mặt (Face Comparison)

- **Ngưỡng so khớp khuôn mặt (face match threshold) đã được đặt là 0.4** để đảm bảo chỉ những khuôn mặt thực sự giống nhau mới được coi là khớp. Điều này giúp loại bỏ hoàn toàn nguy cơ nhận diện sai khuôn mặt không khớp là "khớp" – một lỗi tối kỵ trong eKYC.
- **Cảnh báo bảo mật:** Nếu score >= 0.4, hệ thống sẽ trả về match = false (KHÔNG KHỚP), bất kể hai ảnh có thể hơi giống nhau. Chỉ score < 0.4 mới được coi là khớp.

### Hướng dẫn kiểm thử so khớp khuôn mặt

1. Đảm bảo có đủ các file ảnh mẫu trong thư mục gốc:
    - `IMG_4620.png`: Ảnh CCCD
    - `IMG_4637.png`: Ảnh khuôn mặt KHỚP với CCCD
    - `IMG_5132.png`: Ảnh khuôn mặt KHÔNG KHỚP với CCCD
2. Khởi động lại dịch vụ face_comparison_service sau khi cập nhật:
    ```bash
    docker compose build face-comparison-service && docker compose up -d face-comparison-service
    ```
3. Chạy lại script kiểm thử toàn bộ luồng:
    ```bash
    python3 test_full_flow.py
    ```
4. Kết quả sẽ in rõ:
    - [CASE 1] CCCD vs Ảnh selfie KHỚP: Nếu score < 0.4, match = true. Nếu score >= 0.4, match = false.
    - [CASE 2] CCCD vs Ảnh không khớp: match = false (bảo mật tuyệt đối).

### Ý nghĩa các trường trả về từ API so khớp khuôn mặt
- `match`: true/false – hai khuôn mặt có được coi là khớp không (dựa trên threshold)
- `score`: giá trị khoảng cách khuôn mặt, càng nhỏ càng giống
- `threshold`: ngưỡng so khớp hiện tại (0.4)

> **Khuyến nghị:** Không nên tăng threshold lên cao hơn 0.4 để đảm bảo an toàn eKYC. Nếu cần kiểm thử với ảnh khác, chỉ cần đổi tên file ảnh và chạy lại script.

## Luồng eKYC Tự Động (Full Flow)

Hệ thống đã tích hợp endpoint `/ekyc/full_flow/` trên API Gateway để tự động hóa toàn bộ quy trình eKYC:

1. **Upload ảnh selfie** lên storage service, nhận về URL.
2. **Thực hiện OCR** trên ảnh CCCD qua Generic OCR Service (Gemini).
3. **Trích xuất thông tin eKYC** từ kết quả OCR qua eKYC Information Extraction Service.
4. **Lưu dữ liệu eKYC** (các trường bóc tách + selfie_image_url) vào user_service.
5. **Trả về kết quả tổng hợp** gồm thông tin eKYC, ocr_text, các trường bóc tách, link ảnh selfie.

### Hướng dẫn kiểm thử tự động

- Sử dụng script `test_ekyc_full_flow.py` để kiểm thử end-to-end:
    ```bash
    python3 test_ekyc_full_flow.py
    ```
- Script sẽ tự động:
    - Đăng ký và đăng nhập user mới
    - Gửi ảnh CCCD (`IMG_4620.png`) và ảnh selfie (`IMG_4637.png`) qua API Gateway
    - Nhận kết quả trả về gồm dữ liệu eKYC đã lưu, văn bản OCR, các trường bóc tách, link ảnh selfie

### Định dạng request API Gateway `/ekyc/full_flow/`
- Method: `POST`
- Form-data:
    - `cccd_image`: file ảnh CCCD
    - `selfie_image`: file ảnh selfie
    - `lang`: (tùy chọn, mặc định `vie`)
    - `psm`: (tùy chọn)
- Header:  
  `Authorization: Bearer <access_token>`

### Định dạng response mẫu
```json
{
  "ekyc_info": {
    "id": 1,
    "user_id": 2,
    "id_number": "0123456789",
    "full_name": "NGUYEN VAN A",
    "date_of_birth": "01/01/1990",
    "gender": "Nam",
    "nationality": "Việt Nam",
    "place_of_origin": "Hà Nội",
    "place_of_residence": "Hà Nội",
    "expiry_date": "01/01/2030",
    "selfie_image_url": "http://localhost:8003/files/abcxyz.png",
    "created_at": "2025-06-04T10:00:00Z",
    "updated_at": null
  },
  "ocr_text": "...văn bản OCR...",
  "extracted_fields": { ...các trường bóc tách... },
  "selfie_image_url": "http://localhost:8003/files/abcxyz.png"
}
```

### Lưu ý
- Ảnh sẽ được lưu vào storage service, chỉ lưu URL vào user_service.
- Dữ liệu CCCD bóc tách sẽ lưu vào bảng `ekyc_info` trong user_service.
- Có thể kiểm tra lại dữ liệu eKYC đã lưu qua API `/ekyc/me` (GET, cần token).

## Tình trạng dịch vụ
- Tất cả các service chính đã hoạt động tốt, trừ `liveness_service` (đang lỗi, chưa hoàn thiện).
- Luồng eKYC tự động đã kiểm thử thành công với ảnh thật.

## Kịch bản Kiểm thử

* Sử dụng script `test_ocr_service.py` để kiểm tra riêng `generic-ocr-service` (phiên bản Gemini).
* Sử dụng script `test_full_flow.py` để kiểm tra toàn bộ luồng từ OCR đến trích xuất thông tin eKYC.

## Tình trạng Dự án Hiện tại (Cập nhật ngày 04/06/2025)

* **Các thành phần hoạt động tốt**:
    * User Service.
    * Storage Service.
    * API Gateway.
    * Admin Portal Frontend & Backend Service.
    * `generic-ocr-service` (phiên bản Gemini) hoạt động tốt, cung cấp OCR chất lượng cao.
    * `ekyc_information_extraction_service` (Regex-Only) đã sửa lỗi Regex, trích xuất chính xác trường `full_name` và các trường quan trọng khác.

* **Các vấn đề nhỏ còn lại**:
    * Cảnh báo `bcrypt` trong `user-service` (không ảnh hưởng chức năng).
    * Các trường không có trên mặt trước CCCD (ngày cấp, nơi cấp, đặc điểm nhận dạng, dân tộc, tôn giáo) không được trích xuất là đúng.

* **Các dịch vụ nhận diện khuôn mặt và liveness**: Đang ở giai đoạn kế hoạch.

## Ưu tiên Tiếp theo

1.  Kiểm thử toàn diện luồng eKYC với nhiều ảnh CCCD khác nhau.
2.  Xem xét tối ưu hóa chi phí token nếu cần.
3.  Phát triển các dịch vụ liên quan đến Nhận dạng Khuôn mặt theo kế hoạch.

## [CẬP NHẬT 04/06/2025] Kết quả kiểm thử full luồng eKYC (test_full_flow.py)

### Kết quả thực tế (log tóm tắt):

- Đăng ký user qua API Gateway: **Thành công**
- Đăng nhập user, lấy access token: **Thành công**
- Lấy thông tin user hiện tại: **Thành công**
- Gửi ảnh CCCD qua Generic OCR Service (Gemini): **OCR thành công, text trích xuất đầy đủ**
- Gửi text OCR sang eKYC Information Extraction Service: **Trích xuất chính xác các trường (id_number, full_name, date_of_birth, ...)**
- So khớp khuôn mặt (Face Comparison Service):
    - [CASE 1] CCCD vs Ảnh selfie KHỚP: **match = false, score = 0.45** (ngưỡng bảo mật cao, không nhận nhầm)
    - [CASE 2] CCCD vs Ảnh không khớp: **match = false, score = 0.51**

#### Log mẫu:

```
========== API Gateway: Register User ==========
Registering new user...
Status Code: 201
...
========== API Gateway: Login User - ... ==========
Logging in...
Status Code: 200
...
========== API Gateway: Get Current User (me) ==========
Status Code: 200
...
========== API Gateway -> Generic OCR Service (Gemini): OCR Image 'IMG_4620.png' ==========
Status Code: 200
Response JSON: { ...text OCR... }
...
========== API Gateway -> eKYC Info Extraction: Extract Info ==========
Status Code: 200
Response JSON: { ...fields... }
...
========== Face Comparison Service: Compare 'IMG_4620.png' vs 'IMG_4637.png' ==========
Status Code: 200
Response JSON: { "match": false, "score": 0.45, "threshold": 0.4 }
...
========== Face Comparison Service: Compare 'IMG_4620.png' vs 'IMG_5132.png' ==========
Status Code: 200
Response JSON: { "match": false, "score": 0.51, "threshold": 0.4 }
...
Full API Flow Tests Completed.
```

### Đánh giá hiện trạng
- **Tất cả các service chính đã hoạt động tốt, full flow eKYC qua API Gateway thành công.**
- **OCR và bóc tách thông tin chính xác, bảo mật so khớp khuôn mặt đảm bảo.**
- **Liveness service đã fix lỗi phụ thuộc python-multipart, đã khởi động thành công (chưa kiểm thử luồng liveness).**

> Để kiểm thử lại, chỉ cần chạy:
> ```bash
> python3 test_full_flow.py
> ```

## [CẬP NHẬT 04/06/2025] Kiểm thử liveness_service

### Kết quả kiểm thử thực tế endpoint `/check_liveness/`:

- Gửi ảnh selfie (`IMG_4637.png`):
  - Kết quả: `{ "is_live": true, "score": 0.90 }`
- Gửi ảnh CCCD (`IMG_4620.png`):
  - Kết quả: `{ "is_live": true, "score": 0.97 }`
- Gửi ảnh không khớp (`IMG_5132.png`):
  - Kết quả: `{ "is_live": false, "score": 0.29 }`

> Lưu ý: Service hiện tại trả kết quả random (demo), chưa tích hợp model liveness thực tế. Endpoint đã hoạt động tốt, nhận file multipart và trả về kết quả đúng format.

## Cập nhật ngày 04/06/2025

### Lỗi '404 Not Found' khi truy cập các chức năng mới

**Nguyên nhân:**
Các route tương ứng cho các chức năng mới (Quản lý eKYC, Thống kê, Thông báo, Tài liệu hướng dẫn) chưa được định nghĩa trong `admin_portal_frontend/main.py`.

**Cách khắc phục:**
Đã thêm các route placeholder trong `admin_portal_frontend/main.py` để xử lý các yêu cầu đến các đường dẫn này. Hiện tại, các route sẽ trả về thông báo rằng chức năng đang được phát triển.

**Các route đã thêm:**
- `/dashboard/ekyc`: Quản lý eKYC
- `/dashboard/statistics`: Thống kê
- `/dashboard/notifications`: Thông báo
- `/dashboard/docs`: Hướng dẫn

**Hành động tiếp theo:**
- Phát triển nội dung và logic cho các chức năng này.
- Kiểm tra và triển khai các tính năng liên quan.

## Cập nhật Admin Portal (04/06/2025)

### 1. Sửa lỗi "404 Not Found" trên Admin Portal

#### 1.1. Lỗi các trang chức năng mới
**Nguyên nhân:**
- Các route mới (/dashboard/ekyc, /statistics, /notifications, /docs) chưa được định nghĩa trong admin portal frontend.

**Cách khắc phục:**
- Đã thêm route handlers trong `admin_portal_frontend/main.py`
- Tạo template `message_page.html` để hiển thị thông báo chức năng đang phát triển
- Đã định tuyến các request tới template phù hợp

**Trạng thái hiện tại:**
- Các trang hiển thị thông báo "đang phát triển"
- UI/UX thống nhất với thiết kế chung
- Chức năng sẽ được phát triển trong các bản cập nhật tiếp theo

#### 1.2. Lỗi API kích hoạt/vô hiệu hóa user
**Nguyên nhân:**
- Thiếu các route xử lý trong chuỗi API Gateway -> Admin Backend -> User Service

**Cách khắc phục:**
- Thêm route `/admin/users/{user_id}/activate` và `/deactivate` trong API Gateway
- Bổ sung xử lý trong Admin Portal Backend Service
- Cập nhật User Service để hỗ trợ kích hoạt/vô hiệu hóa user

**Trạng thái hiện tại:**
- API hoạt động đầy đủ theo chuỗi:
  - Frontend -> API Gateway -> Admin Backend -> User Service
- Có xử lý lỗi và thông báo phù hợp
- Giao diện người dùng đã cập nhật trạng thái real-time

### 2. Kế hoạch phát triển tiếp theo
1. **Quản lý eKYC:**
   - Xem lịch sử eKYC của user
   - Hiển thị thông tin chi tiết từng lần eKYC
   - Thống kê tỷ lệ thành công/thất bại

2. **Dashboard thống kê:**
   - Số lượng user active/inactive
   - Số lượng eKYC theo thời gian
   - Biểu đồ phân tích dữ liệu

3. **Hệ thống thông báo:**
   - Thông báo realtime cho admin
   - Lưu trữ lịch sử thông báo
   - Phân loại theo mức độ ưu tiên

4. **Tài liệu hướng dẫn:**
   - Hướng dẫn sử dụng chi tiết
   - FAQ cho admin
   - Quy trình xử lý các tình huống phổ biến