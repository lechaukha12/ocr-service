FROM python:3.10-slim

WORKDIR /app

# Cài đặt các dependencies hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    build-essential \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-vie \
    tesseract-ocr-osd \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libtiff-dev \
    libgl1-mesa-glx \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Kiểm tra Tesseract và các ngôn ngữ đã cài đặt từ command line (trong quá trình build)
RUN echo "--- Tesseract Version (from command line during build) ---" && \
    tesseract --version

RUN echo "--- Tesseract List Available Languages (from command line during build) ---" && \
    tesseract --list-langs

RUN echo "--- Listing contents of /usr/share/tesseract-ocr/4.00/tessdata/ (old path attempt) ---" && \
    (ls -l /usr/share/tesseract-ocr/4.00/tessdata/ || echo "Path /usr/share/tesseract-ocr/4.00/tessdata not found or empty")

RUN echo "--- Listing contents of /usr/share/tessdata/ (previous path attempt) ---" && \
    (ls -l /usr/share/tessdata/ || echo "Path /usr/share/tessdata not found or empty")

RUN echo "--- Listing contents of /usr/share/tesseract-ocr/5/tessdata/ (confirmed path) ---" && \
    (ls -l /usr/share/tesseract-ocr/5/tessdata/ || echo "Path /usr/share/tesseract-ocr/5/tessdata not found or empty")


# Thiết lập biến môi trường TESSDATA_PREFIX dựa trên output của tesseract --list-langs
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata

# Sao chép file requirements.txt
COPY requirements.txt /app/requirements.txt

# Cài đặt các thư viện Python
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r /app/requirements.txt

# Sao chép toàn bộ nội dung của thư mục context
COPY . /app/

# Port mà ứng dụng FastAPI sẽ chạy bên trong container
EXPOSE 8004

# Lệnh để chạy ứng dụng khi container khởi động
# Bây giờ check_tesseract.py sẽ sử dụng TESSDATA_PREFIX đúng
CMD python /app/check_tesseract.py && \
    echo "--- Attempting to run main.py directly (full version) ---" && \
    python /app/main.py && \
    echo "--- Attempting to start Uvicorn with trace log level (full main.py) ---" && \
    uvicorn main:app --host 0.0.0.0 --port 8004 --log-level trace
