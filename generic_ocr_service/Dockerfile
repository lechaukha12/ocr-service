# Sử dụng một base image Python chính thức, ví dụ python:3.10-slim
FROM python:3.10-slim

# Thiết lập các biến môi trường để tối ưu hóa Python trong Docker
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Tạo thư mục làm việc bên trong container
WORKDIR /app

# Cài đặt các thư viện hệ thống cần thiết cho OpenCV và các thư viện đồ họa khác
# libgl1-mesa-glx cung cấp libGL.so.1
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Cài đặt PyTorch, Torchvision, và Torchaudio (phiên bản CPU) một cách tường minh
# Luôn kiểm tra trang chủ PyTorch (pytorch.org/get-started/locally/) để có lệnh pip mới nhất cho CPU.
# Sử dụng phiên bản không có "+cpu" trong tên version, --index-url sẽ lo việc chọn bản CPU.
RUN pip install --no-cache-dir torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cpu

# Sao chép tệp requirements.txt vào trước để tận dụng Docker cache
COPY ./requirements.txt /app/requirements.txt

# Cài đặt các phụ thuộc Python từ requirements.txt
# (Lưu ý: torch, torchvision, torchaudio đã được cài ở bước trên,
#  vietocr trong requirements.txt sẽ nhận diện chúng đã được cài đặt)
RUN pip install --no-cache-dir -r /app/requirements.txt

# Sao chép toàn bộ mã nguồn của ứng dụng vào thư mục làm việc
COPY . /app/

# Port mà ứng dụng FastAPI sẽ chạy bên trong container
EXPOSE 8004

# Lệnh để chạy ứng dụng khi container khởi động
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004", "--workers", "1"]