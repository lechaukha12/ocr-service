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
    * **Tình trạng**: **Hoạt động**. Đã kiểm thử thành công qua API Gateway. Có một cảnh báo nhỏ không nghiêm trọng liên quan đến `bcrypt` khi `passlib` cố gắng đọc thông tin phiên bản (lỗi `AttributeError: module 'bcrypt' has no attribute '__about__'`), tuy nhiên chức năng hash và xác minh mật khẩu vẫn hoạt động. Cần xem xét lại `requirements.txt` để `passlib` tự quản lý phiên bản `bcrypt`.

2.  **API Gateway (`api_gateway`)**
    * **Mô tả**: Điểm vào duy nhất cho client, điều hướng request đến các microservices phù hợp.
    * **Công nghệ**: FastAPI, HTTPX.
    * **Port**: `8000`
    * **Tình trạng**: **Hoạt động**. Đã kiểm thử điều phối request thành công đến các dịch vụ User, Storage, Generic OCR, và eKYC Information Extraction.

3.  **Storage Service (`storage_service`)**
    * **Mô tả**: Lưu trữ và quản lý các file được upload.
    * **Công nghệ**: FastAPI, AIOFiles.
    * **Port**: `8003`
    * **Tình trạng**: **Hoạt động**. Đã kiểm thử upload và download file thành công qua API Gateway.

4.  **Generic OCR Service (`generic_ocr_service`)**
    * **Mô tả**: Thực hiện nhận dạng ký tự quang học (OCR) trên ảnh được cung cấp.
    * **Công nghệ hiện tại**: FastAPI, **PaddleOCR** (sử dụng `lang='vi'` với các model mặc định như `PP-OCRv5_mobile_det` và `PP-OCRv5_mobile_rec`). Đã có nỗ lực tích hợp VietOCR (model `vgg_seq2seq` với file weights `seq2seqocr.pth`) theo "Lựa chọn C" - một hướng tiếp cận hybrid.
    * **Port**: `8004`
    * **Tình trạng**:
        * **PaddleOCR hoạt động và trả về kết quả OCR**: Service khởi động thành công với PaddleOCR. Khi nhận ảnh, service trả về `Status Code: 200 OK` và một chuỗi văn bản đã được OCR. Kết quả này đã có nội dung chữ, không còn là chuỗi rỗng.
        * **Chất lượng dấu tiếng Việt (PaddleOCR)**: Kết quả OCR từ model PaddleOCR mobile mặc định cho thấy nhiều từ tiếng Việt (đặc biệt là chữ IN HOA) bị mất dấu hoặc nhận dạng dấu chưa chính xác, mặc dù một số từ có dấu vẫn được giữ lại.
        * **VietOCR và "Lựa chọn C" (Hybrid OCR - Tích hợp chưa hoàn tất)**:
            * **Mô tả "Lựa chọn C"**: Đây là một hướng tiếp cận hybrid được đề xuất với mục tiêu cải thiện chất lượng nhận dạng dấu tiếng Việt. Quy trình dự kiến bao gồm:
                1. PaddleOCR (`lang='vi'`) thực hiện OCR toàn bộ ảnh để lấy văn bản và tọa độ các vùng chữ (bounding box).
                2. Các vùng chữ quan trọng (Regions of Interest - ROI), đặc biệt là những vùng cần độ chính xác cao về dấu tiếng Việt (ví dụ: tên riêng, địa danh), sẽ được xác định từ kết quả của PaddleOCR.
                3. Các ROI này sau đó sẽ được "warp" (cắt và chỉnh sửa phối cảnh dựa trên tọa độ box) và đưa qua VietOCR (sử dụng model `vgg_seq2seq` với file weights `seq2seqocr.pth` do người dùng cung cấp) để nhận dạng lại.
                4. Kết quả từ VietOCR sẽ được dùng để thay thế hoặc bổ sung cho kết quả của PaddleOCR tại các ROI tương ứng, với kỳ vọng VietOCR sẽ cho kết quả dấu tốt hơn cho các vùng này.
            * **Hiện trạng tích hợp VietOCR**: Mặc dù mã nguồn `main.py` đã bao gồm logic để khởi tạo cả PaddleOCR và VietOCR, và file model `seq2seqocr.pth` đã được copy vào Docker image, log khởi động của service **không cho thấy bất kỳ dấu hiệu nào của việc VietOCR được khởi tạo thành công** (không có log "Lifespan: Attempting to load VietOCR model..." hay các log liên quan khác được ghi nhận trong các lần kiểm tra gần nhất). Do đó, phần xử lý hybrid sử dụng VietOCR trong endpoint `/ocr/image/` chưa được kích hoạt và thử nghiệm đầy đủ. Một lỗi `ValueError: The truth value of an array with more than one element is ambiguous...` cũng đã xuất hiện trong phần code chuẩn bị cho việc xử lý ROI bằng VietOCR (cụ thể là dòng `if should_refine_with_vietocr and box_coordinates:`), cho thấy logic kiểm tra `box_coordinates` cần được sửa nếu tiếp tục hướng này.
        * **Tạm dừng phát triển hướng Hybrid OCR (PaddleOCR + VietOCR)**: Do gặp khó khăn trong việc xác nhận VietOCR khởi tạo thành công và các lỗi phát sinh, hướng tiếp cận này tạm thời được dừng lại. Service hiện tại hoạt động dựa trên PaddleOCR.

5.  **eKYC Information Extraction Service (`ekyc_information_extraction_service`)**
    * **Mô tả**: Trích xuất thông tin có cấu trúc (Họ tên, Ngày sinh, Số CMND/CCCD, Địa chỉ, v.v.) từ kết quả OCR của giấy tờ tùy thân. Sử dụng phương pháp hybrid: ban đầu dùng regex, sau đó có thể fallback hoặc cải thiện bằng Google Gemini LLM nếu cần và được cấu hình.
    * **Công nghệ**: FastAPI, Python (cho regex), Google Generative AI SDK.
    * **Port**: `8005`
    * **Tình trạng**:
        * **Hoạt động dựa trên output của PaddleOCR**: Service nhận text từ `generic-ocr-service` và đã có thể trích xuất được nhiều trường thông tin cơ bản (Số ID, Họ tên, Ngày sinh, Giới tính, Ngày hết hạn) mà không còn báo lỗi `errors` nghiêm trọng.
        * **Cần tinh chỉnh Regex**: Các trường như Quốc tịch (`nationality`), Quê quán (`place_of_origin`), Nơi thường trú (`place_of_residence`) vẫn còn bị trích xuất lộn xộn và chứa thông tin thừa. Cần cải thiện các biểu thức chính quy (regex) để phù hợp hơn với định dạng output hiện tại của PaddleOCR.
        * **Chất lượng trích xuất phụ thuộc OCR**: Độ chính xác của việc trích xuất vẫn bị ảnh hưởng bởi chất lượng dấu tiếng Việt từ đầu vào OCR.

6.  **Admin Portal Frontend (`admin_portal_frontend`)**
    * **Mô tả**: Giao diện web cho quản trị viên để xem danh sách người dùng.
    * **Công nghệ**: FastAPI (với Jinja2 templates), HTML, CSS.
    * **Port**: `8080`
    * **Tình trạng**: **Hoàn thiện cơ bản**. Đã có giao diện login và hiển thị danh sách người dùng với phân trang.

7.  **Admin Portal Backend Service (`admin_portal_backend_service`)**
    * **Mô tả**: Service backend cung cấp API cho Admin Portal Frontend.
    * **Công nghệ**: FastAPI.
    * **Port**: `8002`
    * **Tình trạng**: **Hoàn thiện cơ bản**. Đã có API lấy danh sách user.

8.  **Face Detection Service (`face_detection_service`)**: Kế hoạch.
9.  **Face Comparison Service (`face_comparison_service`)**: Kế hoạch.
10. **Liveness Service (`liveness_service`)**: Kế hoạch.

## Thiết lập và Chạy Dự án

1.  **Yêu cầu**:
    * Docker
    * Docker Compose
    * (Tùy chọn, nếu sử dụng Gemini fallback trong `ekyc_information_extraction_service`) API Key từ Google AI Studio, được cấu hình trong tệp `.env` ở thư mục gốc dự án:
        ```
        GEMINI_API_KEY=your_actual_google_ai_studio_api_key
        ```

2.  **Các bước chạy**:
    * Clone repository (nếu có).
    * Đặt các file của từng service vào đúng cấu trúc thư mục.
    * (Nếu đã từng cấu hình cho VietOCR) Đảm bảo file model `seq2seqocr.pth` được đặt tại `ocr-service/generic_ocr_service/model/seq2seqocr.pth` (mặc dù hiện tại VietOCR chưa được kích hoạt).
    * Từ thư mục gốc của dự án (chứa file `docker-compose.yml`), chạy lệnh:
        ```bash
        docker-compose up -d --build
        ```
    * Các service sẽ được khởi chạy. Truy cập API Gateway tại `http://localhost:8000`.

## Kịch bản Kiểm thử Toàn bộ Luồng

* Một script `test_full_flow.py` được sử dụng để kiểm thử tự động các luồng chính của hệ thống.
* Hiện tại, script này cho thấy `generic-ocr-service` (sử dụng PaddleOCR) trả về kết quả text, và `ekyc_information_extraction_service` có thể trích xuất một phần thông tin từ đó.

## Tình trạng Dự án Hiện tại (Tính đến 27/05/2025)

* **Các thành phần hoạt động tốt**:
    * User Service (với cảnh báo nhỏ về bcrypt).
    * Storage Service.
    * API Gateway.
    * Admin Portal Frontend & Backend Service.
    * `generic-ocr-service` sử dụng **PaddleOCR** đã có thể xử lý ảnh và trả về văn bản OCR.
    * `ekyc_information_extraction_service` đã có thể trích xuất các trường cơ bản từ kết quả của PaddleOCR.

* **Các vấn đề cần giải quyết và cải thiện**:
    1.  **Chất lượng dấu tiếng Việt của `generic-ocr-service` (PaddleOCR)**: Model PaddleOCR mobile mặc định (`PP-OCRv5_mobile_rec`) cho kết quả nhận dạng dấu tiếng Việt chưa cao, đặc biệt với chữ IN HOA.
    2.  **Độ chính xác trích xuất thông tin của `ekyc_information_extraction_service`**: Cần tinh chỉnh lại các biểu thức chính quy (regex) để phù hợp hơn với output thực tế từ PaddleOCR, đặc biệt cho các trường phức tạp như địa chỉ, quốc tịch.
    3.  **VietOCR trong `generic-ocr-service`**: Việc khởi tạo VietOCR chưa thành công (không có log xác nhận trong các lần kiểm tra gần nhất). Hướng hybrid (PaddleOCR + VietOCR, hay "Lựa chọn C") tạm dừng để tập trung vào các giải pháp khác hoặc gỡ lỗi VietOCR một cách triệt để hơn.
    4.  **Cảnh báo `bcrypt` trong `user-service`**: Cần xem xét lại `requirements.txt` của `user-service`.

* **Hướng tham khảo (đã tạm dừng)**:
    * Đã xem xét project `Vietnamese-CitizenID-Recognition` trên GitHub (do người dùng cung cấp file `Extractor.py` và `requirements.txt`). Project này sử dụng kết hợp PaddleOCR (`lang='en'` cho detection) và VietOCR (model `vgg_seq2seq` với file weights `seq2seqocr.pth` cho recognition tiếng Việt).

## Ưu tiên Tiếp theo

1.  **Cải thiện chất lượng nhận dạng dấu tiếng Việt của `generic-ocr-service`**:
    * **Ưu tiên**: xem xét lại các engine OCR khác (ví dụ: Tesseract) nếu có đánh giá tốt về chất lượng dấu tiếng Việt cho loại ảnh CCCD và dễ tích hợp hơn.
2.  **Tinh chỉnh Regex trong `ekyc_information_extraction_service`**: Dựa trên output ổn định nhất có thể đạt được từ `generic-ocr-service`, tối ưu hóa lại các biểu thức chính quy.
3.  **(Tùy chọn, nếu quyết định quay lại)** **Gỡ lỗi khởi tạo VietOCR**: Nếu vẫn muốn theo đuổi giải pháp hybrid "Lựa chọn C", cần tìm ra nguyên nhân VietOCR không hiển thị log khởi tạo trong `generic-ocr-service` và giải quyết các lỗi phát sinh (như `ValueError` đã thấy).
4.  **Giải quyết cảnh báo `bcrypt`** trong `user-service`.
5.  **Phát triển các dịch vụ liên quan đến Nhận dạng Khuôn mặt** theo kế hoạch.

