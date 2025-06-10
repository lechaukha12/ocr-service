FROM python:3.9-slim

WORKDIR /app

# Cài đặt system dependencies cho OpenCV và PaddleOCR
RUN apt-get update && \
    apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgtk2.0-dev \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements và cài đặt Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Khởi động FastAPI với PaddleOCR
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]