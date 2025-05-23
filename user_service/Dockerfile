FROM python:3.10-slim

WORKDIR /app

# Sao chép file requirements.txt từ thư mục context (./user_service) vào /app/
COPY requirements.txt /app/requirements.txt

# Cài đặt các thư viện Python
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r /app/requirements.txt

# Sao chép toàn bộ nội dung của thư mục context (./user_service) vào /app/
COPY . /app/

# Port mà ứng dụng FastAPI sẽ chạy bên trong container
EXPOSE 8001

# Lệnh để chạy ứng dụng khi container khởi động
# Giả sử file main.py của bạn nằm ở thư mục gốc của service (trong /app/)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
