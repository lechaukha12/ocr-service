FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Các thư viện hệ thống như libgl1-mesa-glx, libglib2.0-0 có thể không cần thiết nữa
# nếu không có các thư viện Python nặng về xử lý ảnh/GUI như OpenCV đầy đủ.
# Pillow thường không yêu cầu chúng.
# RUN apt-get update && apt-get install -y --no-install-recommends \
#  && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 8004

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
