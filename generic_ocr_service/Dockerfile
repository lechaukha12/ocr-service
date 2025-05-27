FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxext6 \
    libsm6 \
    libfontconfig1 \
    libxrender1 \
    fonts-arphic-ukai \
    fonts-arphic-uming \
    fonts-wqy-zenhei \
    libgomp1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN python -c "from paddleocr import PaddleOCR; print('Attempting to download PaddleOCR models for vi...'); ocr = PaddleOCR(use_angle_cls=False, lang='vi'); print('PaddleOCR model download process triggered or models already present.')"

COPY . /app/

ENV PORT=8004

EXPOSE ${PORT}

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]