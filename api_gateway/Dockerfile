FROM python:3.10-slim

WORKDIR /app

# Sao chép file requirements.txt từ thư mục context (./api_gateway)
COPY requirements.txt /app/requirements.txt

# Cài đặt các thư viện Python
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r /app/requirements.txt

# Sao chép toàn bộ nội dung của thư mục context (./api_gateway)
COPY . /app/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
