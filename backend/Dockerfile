FROM python:3.11-slim

# Thiết lập biến môi trường tránh sinh file .pyc và buffer log
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Cài đặt các gói hệ thống cần thiết cho xử lý video và opencv-headless
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Tận dụng Docker layer cache bằng cách copy và cài requirements trước
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Nạp trước model yolov8n.pt vào cache của container lúc build
RUN python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# Sao chép toàn bộ mã nguồn backend vào image
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
