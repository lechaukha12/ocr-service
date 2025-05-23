FROM python:3.10-slim

WORKDIR /app

# Sao chép file requirements.txt từ thư mục context (./storage_service)
COPY requirements.txt /app/requirements.txt

# Cài đặt các thư viện Python
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r /app/requirements.txt

# Sao chép toàn bộ nội dung của thư mục context (./storage_service)
COPY . /app/

# Tạo thư mục uploads nếu nó được quản lý bởi code trong service
# Nếu UPLOAD_DIR trong config.py của storage_service là tương đối (ví dụ "uploads")
# thì nó sẽ được tạo trong /app/uploads
# RUN mkdir -p /app/uploads 
# Tuy nhiên, config.py của storage_service đã có logic tạo thư mục này rồi.

EXPOSE 8003

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
