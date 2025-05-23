FROM python:3.10-slim

WORKDIR /app

# Sao chép file requirements.txt từ thư mục context (./admin_portal_frontend)
COPY requirements.txt /app/requirements.txt

# Cài đặt các thư viện Python
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r /app/requirements.txt

# Sao chép toàn bộ nội dung của thư mục context (./admin_portal_frontend)
# Điều này bao gồm main.py, config.py, thư mục templates, static (nếu có)
COPY . /app/

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
