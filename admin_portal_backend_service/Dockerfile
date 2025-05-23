FROM python:3.10-slim

WORKDIR /app

# Sao chép file requirements.txt từ thư mục context (./admin_portal_backend_service)
COPY requirements.txt /app/requirements.txt

# Cài đặt các thư viện Python
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r /app/requirements.txt

# Sao chép toàn bộ nội dung của thư mục context (./admin_portal_backend_service)
COPY . /app/

EXPOSE 8002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
