# Vision Language Model OCR Service (VLM-Core)

Service này cung cấp API nhận dạng văn bản từ hình ảnh (OCR) bằng các mô hình Vision-Language models (VLM) mã nguồn mở thông qua [Ollama](https://ollama.com/).

## Tính năng

- **OCR trên cơ sở hạ tầng của bạn**: Không cần gửi dữ liệu đến dịch vụ bên ngoài
- **Không giới hạn lượt gọi API**: Tiết kiệm chi phí cho các API thương mại
- **Tùy chỉnh mô hình**: Hỗ trợ nhiều VLM khác nhau từ Ollama (moondream, llava, bakllava, ...)
- **Dễ dàng tích hợp**: Cung cấp API RESTful đơn giản, được triển khai bằng FastAPI
- **Độc lập**: Được đóng gói trong Docker container riêng biệt

## Cấu trúc

```
vlm-core/
├── Dockerfile        # Cấu hình Docker, bao gồm cả Ollama
├── main.py           # FastAPI server cung cấp các API endpoints
└── requirements.txt  # Các thư viện Python cần thiết
```

## API Endpoints

### 1. OCR từ hình ảnh

**Endpoint**: `/ocr`  
**Method**: `POST`  
**Content-Type**: `multipart/form-data`  
**Parameters**:
- `image`: File hình ảnh cần nhận dạng văn bản

**Phản hồi**:
```json
{
  "text": "Nội dung đã nhận dạng từ hình ảnh...",
  "model": "moondream",
  "success": true,
  "error": null
}
```

### 2. Kiểm tra trạng thái

**Endpoint**: `/health`  
**Method**: `GET`  

**Phản hồi**:
```json
{
  "status": "ok",
  "model": "moondream",
  "ollama_status": "ok"
}
```

## Cài đặt & Chạy

### Thông qua Docker Compose

1. Đảm bảo Docker và Docker Compose đã được cài đặt
2. Service được đưa vào cấu hình trong `docker-compose.override.yml`
3. Chạy lệnh:
```bash
docker-compose up -d vlm-core
```

### Truy cập thông qua API Gateway

Các endpoints của VLM-Core được đưa vào API Gateway:

- OCR endpoint: `http://localhost:8000/vlm/ocr/`
- Health check: `http://localhost:8000/vlm/health/`

## Cấu hình

Service sử dụng các biến môi trường sau:

- `OLLAMA_API_URL`: URL của Ollama API, mặc định là `http://localhost:11434/api/generate`
- `MODEL_NAME`: Tên model VLM trong Ollama, mặc định là `moondream`
- `TIMEOUT_SECONDS`: Thời gian timeout cho mỗi yêu cầu OCR, mặc định 120 giây

## Kiểm thử

Một script kiểm thử đã được cung cấp để thử nghiệm service:

```bash
# Kiểm tra sức khỏe của service
python test_vlm_ocr.py --health

# Kiểm tra nhận dạng hình ảnh (kết nối trực tiếp)
python test_vlm_ocr.py --image path/to/image.png

# Kiểm tra thông qua API Gateway
python test_vlm_ocr.py --image path/to/image.png --gateway
```

## Yêu cầu hệ thống

- Docker + Docker Compose
- Ít nhất 2GB RAM (khuyến nghị 4GB) cho Ollama và mô hình
- Khoảng 1GB dung lượng đĩa để lưu trữ mô hình

## Khắc phục sự cố

- Nếu OCR không hoạt động, kiểm tra xem mô hình đã được tải hoặc không bằng endpoint `/health`
- Đối với hình ảnh phức tạp, thời gian xử lý có thể kéo dài, cân nhắc tăng `TIMEOUT_SECONDS`
- Nếu Ollama gặp lỗi Out of memory, tăng giới hạn memory cho container trong docker-compose.override.yml
