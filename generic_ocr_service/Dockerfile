FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    tar \
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
    libjpeg-dev \
    libpng-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --timeout=600 -r requirements.txt

RUN mkdir -p /app/model
COPY ./model/seq2seqocr.pth /app/model/seq2seqocr.pth

RUN python -c "from paddleocr import PaddleOCR; print('Attempting to download default PaddleOCR models for vi...'); PaddleOCR(use_angle_cls=False, lang='vi'); print('Default PaddleOCR model download process complete.')"

COPY . /app/

ENV PORT=8004
EXPOSE ${PORT}

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]