README - Dự án eKYC Microservices
1. Tổng quan Dự án
Dự án này nhằm mục đích xây dựng một hệ thống Định danh Khách hàng Điện tử (eKYC) hoàn chỉnh, được thiết kế theo kiến trúc microservices. Hệ thống cho phép người dùng cuối đăng ký tài khoản thông qua ứng dụng di động, bao gồm các bước xác minh danh tính bằng cách chụp ảnh giấy tờ tùy thân (CCCD, Hộ chiếu) và ảnh chân dung. Thông tin từ giấy tờ sẽ được bóc tách tự động (OCR), và khuôn mặt sẽ được so sánh để xác thực.

Ngoài ra, dự án bao gồm một cổng thông tin web (web portal) dành cho đội ngũ nội bộ để rà soát, phân tích các trường hợp eKYC đã được hệ thống xử lý tự động, từ đó đưa ra các điều chỉnh và tinh chỉnh tham số hệ thống nhằm cải thiện độ chính xác theo thời gian.

Mục tiêu chính là sử dụng các công cụ mã nguồn mở và miễn phí, với khả năng tích hợp API Gemini (gói miễn phí) cho các tác vụ nâng cao nếu cần.

2. Kiến trúc Microservices và Chức năng
Dưới đây là danh sách các microservice dự kiến và chức năng chính của chúng:

user-service (Service Quản lý Người dùng)

Chức năng:

Xử lý đăng ký tài khoản người dùng mới (username, email, mật khẩu).

Xác thực đăng nhập và tạo token truy cập (JWT).

Lưu trữ thông tin cơ bản của người dùng và trạng thái tài khoản (ví dụ: chờ xác minh eKYC, đã xác minh, bị từ chối).

Lưu trữ thông tin PII (Personally Identifiable Information) đã được xác minh từ CCCD/Hộ chiếu sau quá trình eKYC.

Trạng thái: Đã build (Giai đoạn 1 - cơ bản).

api-gateway (Cổng API)

Chức năng:

Là điểm vào (entry point) duy nhất cho tất cả các request từ client (mobile app, web portal).

Điều hướng (route) các request đến các microservice nội bộ tương ứng.

Có thể thực hiện các tác vụ chung như xác thực request cơ bản, rate limiting (trong tương lai).

Trạng thái: Đã build (Giai đoạn 1 - cơ bản, định tuyến cho user-service).

storage-service (Service Lưu trữ Tệp)

Chức năng:

Quản lý việc lưu trữ an toàn và truy xuất tất cả các tệp hình ảnh/video của quy trình eKYC (ảnh giấy tờ, ảnh selfie, video/ảnh liveness).

Cung cấp API cho các service khác để tải lên hoặc lấy tệp.

Trạng thái: Chưa build.

generic-ocr-service (Service OCR Chung)

Chức năng:

Là một service OCR độc lập, có khả năng tái sử dụng cho nhiều loại tài liệu khác nhau.

Nhận đầu vào là ảnh (hoặc đường dẫn ảnh) và tùy chọn loại tài liệu.

Thực hiện tiền xử lý ảnh và áp dụng công cụ OCR để trích xuất toàn bộ văn bản thô.

Trả về văn bản thô đã OCR.

Trạng thái: Chưa build.

ekyc-information-extraction-service (Service Trích xuất Thông tin eKYC)

Chức năng:

Nhận văn bản thô từ generic-ocr-service.

Dựa trên loại giấy tờ (CCCD/Hộ chiếu), áp dụng các quy tắc, regex, hoặc AI/ML để trích xuất các trường thông tin cụ thể cần thiết cho eKYC.

Xác định và hỗ trợ trích xuất ảnh khuôn mặt từ ảnh giấy tờ.

Trạng thái: Chưa build.

face-detection-service (Service Phát hiện Khuôn mặt)

Chức năng:

Phát hiện và trích xuất (crop) vùng chứa khuôn mặt từ ảnh giấy tờ và ảnh selfie.

Trạng thái: Chưa build.

face-comparison-service (Service So sánh Khuôn mặt)

Chức năng:

So sánh ảnh khuôn mặt trích xuất từ giấy tờ với ảnh khuôn mặt từ selfie.

Tính toán và trả về điểm số tương đồng.

Trạng thái: Chưa build.

liveness-service (Service Kiểm tra Người thật)

Chức năng:

Phân tích các ảnh/video cử chỉ (chớp mắt, quay đầu, mỉm cười) để xác định người dùng là thật và đang tương tác trực tiếp, chống giả mạo.

Trạng thái: Chưa build.

admin-portal-backend-service (Backend cho Web Portal Rà soát)

Chức năng:

Cung cấp API cho Web Portal của đội ngũ rà soát.

Xác thực nhân viên truy cập portal.

API để truy vấn và hiển thị chi tiết các trường hợp eKYC đã được hệ thống tự động xử lý (bao gồm tất cả hình ảnh, dữ liệu OCR, điểm số, quyết định tự động, và các tham số hệ thống đã sử dụng).

(Tùy chọn) API để nhân viên thêm ghi chú, tag vào các trường hợp.

Trạng thái: Chưa build.

Logic Điều phối (Orchestration Logic)

Chức năng: Điều phối toàn bộ luồng nghiệp vụ eKYC, gọi tuần tự các service liên quan, tổng hợp kết quả và đưa ra quyết định tự động cuối cùng. Logic này có thể nằm trong api-gateway hoặc một service điều phối chuyên biệt.

Trạng thái: Chưa build (một phần cơ bản nằm trong api-gateway để gọi user-service).

3. Trạng thái Phát triển Hiện tại
Chúng ta đang ở Giai đoạn 1 của kế hoạch phát triển, tập trung vào việc xây dựng nền tảng cơ bản cho hệ thống.

Các service đã được build (cơ bản, đã Dockerize và chạy được qua Docker Compose):

user-service:

Chức năng: Đăng ký người dùng (email, username, password), đăng nhập (tạo JWT), lấy thông tin người dùng (/users/me/).

Database: Hiện đang sử dụng "fake database" trong bộ nhớ.

api-gateway:

Chức năng: Định tuyến các request /auth/users/, /auth/token, /users/me/ đến user-service.

Các service/chức năng CHƯA build hoặc đang trong kế hoạch:

Tích hợp PostgreSQL cho user-service.

storage-service

generic-ocr-service

ekyc-information-extraction-service

face-detection-service

face-comparison-service

liveness-service

admin-portal-backend-service

Frontend cho Mobile App.

Frontend cho Web Portal Rà soát.

Hoàn thiện logic điều phối eKYC.

4. Công nghệ Chính (Dự kiến)
Backend: Python (FastAPI)

Cơ sở dữ liệu: PostgreSQL (hiện tại: fake DB trong user-service)

Xử lý ảnh/Video: OpenCV-Python

OCR: Tesseract OCR (thông qua pytesseract)

Phát hiện & So sánh Khuôn mặt: OpenCV, thư viện face_recognition (dlib)

Liveness Detection (Cơ bản): OpenCV, có thể thử nghiệm API Gemini Vision (free tier)

Lưu trữ tệp: Ban đầu là hệ thống tệp cục bộ trên server, sau này có thể là giải pháp cloud storage.

Frontend Web Portal: HTML, CSS, JavaScript.

Containerization: Docker, Docker Compose.

API Gateway: FastAPI (hiện tại).

5. Hướng Phát triển Tiếp theo
Hoàn thiện admin_portal_backend_service (Giai đoạn 1) để có thể xem danh sách người dùng đã đăng ký.

Tích hợp PostgreSQL vào user_service.

Bắt đầu phát triển storage-service.

Tiếp tục với các service liên quan đến xử lý ảnh và OCR (generic-ocr-service, ekyc-information-extraction-service, face-detection-service).