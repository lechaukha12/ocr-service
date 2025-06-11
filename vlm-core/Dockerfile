FROM python:3.10-slim

WORKDIR /app

# Install required packages
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port
EXPOSE 8010

# Set environment variables
ENV USE_OLLAMA=false
ENV USE_LOCAL_MODEL=true
ENV MODEL_NAME=google/gemma-2-2b
ENV TRANSFORMERS_OFFLINE=0
ENV HF_HUB_DISABLE_PROGRESS_BARS=1

# Command to start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]