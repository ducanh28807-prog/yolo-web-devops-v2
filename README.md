
# YOLOv8 Object Detection Web Platform (DevOps Workflow)

Nền tảng Full-stack AI nhận diện đối tượng theo thời gian thực (ảnh & video ngắn) sử dụng mô hình YOLOv8n trên CPU, được đóng gói container hóa và tự động hóa quy trình CI/CD theo chuẩn công nghiệp.

---

## 1. Kiến trúc Hệ thống (Architecture)

```text
               [ Trình duyệt Client ]
                 /                \
      (Port 8080) /                  \ (Port 8000)
                 v                    v
    +------------------------+   +-------------------------+
    | Container: Frontend    |   | Container: Backend      |
    | (Nginx Alpine)         |   | (FastAPI + Uvicorn)     |
    | Phục vụ React SPA tĩnh |   | Chạy YOLOv8n Inference  |
    +------------------------+   +-------------------------+
                 \                    /
                  +--------+---------+
                           |
                     Mạng Docker
                     [ yolo-net ]

```

## 2. Công nghệ sử dụng (Tech Stack)

- **Backend:** Python 3.11, FastAPI, Ultralytics YOLOv8n, OpenCV Headless, PyTest, HTTPX.
- **Frontend:** React 18, Vite, Tailwind CSS, Axios, Lucide React.
- **DevOps & Containerization:** Docker (Multi-stage build), Nginx Alpine, Docker Compose (Rootless runtime).
- **CI/CD:** GitHub Actions (Automated PyTest, React Build Verification, Docker Compose Validation).

## 3. Hướng dẫn Khởi chạy nhanh (Quick Start)

### Yêu cầu hệ thống:

- Đã cài đặt Docker và Docker Compose (hoặc Podman).

### Khởi chạy toàn bộ hệ thống bằng 1 lệnh duy nhất:

```bash
docker compose up -d --build
```

### Truy cập dịch vụ:

- **Giao diện Web:** `http://<IP-MÁY-CỦA-BẠN>:8080` (hoặc `http://localhost:8080`)
- **API Documentation (Swagger UI):** `http://<IP-MÁY-CỦA-BẠN>:8000/docs`

## 4. Chạy Kiểm thử Cục bộ (Local Testing)

```bash
# Kiểm thử Backend API với PyTest
cd backend
source venv/bin/activate
pytest -v

# Kiểm thử build Frontend
cd ../frontend
npm run build
```

## 5. Quy trình CI/CD (GitHub Actions)

Mỗi commit hoặc Pull Request vào nhánh `main` sẽ tự động kích hoạt pipeline kiểm tra:

1. **Backend Unit Tests:** Kiểm tra tính toàn vẹn của API endpoints (`/health`, `/api/detect/image`).
2. **Frontend Build Check:** Xác thực cú pháp React, kiểm tra đóng gói bundle.
3. **Docker Validation:** Kiểm tra cú pháp và cấu trúc mạng của file `docker-compose.yml`.
