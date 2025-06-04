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

# Install netcat for database connection checking
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Add the startup script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh && \
    # Make sure the script has Unix line endings
    sed -i 's/\r$//' /app/start.sh

# Run the startup script
CMD ["/bin/bash", "/app/start.sh"]
