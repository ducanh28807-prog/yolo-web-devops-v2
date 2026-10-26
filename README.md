# YOLOv8 Object Detection Web Platform (DevOps Workflow)

[![CI/CD Pipeline](https://github.com/ducanh28807-prog/yolo-web-devops-v2/actions/workflows/ci.yml/badge.svg)](https://github.com/ducanh28807-prog/yolo-web-devops-v2/actions)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue?logo=docker)
![Render](https://img.shields.io/badge/Deployed-Render-46E3B7?logo=render)
![Python](https://img.shields.io/badge/Python-3.11-yellow?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)

Nền tảng Full-stack AI nhận diện đối tượng theo thời gian thực (hỗ trợ cả ảnh và video ngắn) sử dụng mô hình pre-trained **YOLOv8n** tối ưu trên CPU, được đóng gói container hóa độc lập và tự động hóa quy trình CI/CD từ kiểm thử đến triển khai trên nền tảng Cloud.

---

## 🌐 Đường dẫn Dịch vụ & Tài liệu Bài nộp (Live Services & Docs)

- **Live Frontend Web App:** [https://yolo-frontend-ulf0.onrender.com](https://yolo-frontend-ulf0.onrender.com)
- **Live Backend API Health:** [https://yolo-backend-cupu.onrender.com/health](https://yolo-backend-cupu.onrender.com/health)
- **API Documentation (Swagger UI):** [https://yolo-backend-cupu.onrender.com/docs](https://yolo-backend-cupu.onrender.com/docs)
- **Báo cáo Sự cố (Week 6 Incident Report):** [docs/incident-report.md](./docs/incident-report.md)
- **Bài thu hoạch Cá nhân (Week 7 Reflection):** [docs/REFLECTION.md](./docs/REFLECTION.md)

---

## 1. Kiến trúc Hệ thống (System Architecture)

Hệ thống được thiết kế theo mô hình Microservices tách biệt giữa giao diện tĩnh (Frontend SPA) và dịch vụ xử lý AI tính toán nặng (Backend API), kết nối qua mạng nội bộ Docker và tự động hóa qua GitHub Actions.

```text
              +-------------------------------------------------+
              |              TRÌNH DUYỆT CLIENT                 |
              +-------------------------------------------------+
                        /                             \
    Tải giao diện SPA  /                               \ Gửi Multipart Media
          (Port 8080) /                                 \ (Port 8000)
                     v                                   v
      +-----------------------------+     +-------------------------------+
      | Container: Frontend         |     | Container: Backend            |
      | • Base: Nginx Alpine        |     | • Base: Python 3.11-slim      |
      | • Multi-stage React + Vite  |     | • FastAPI + Uvicorn Worker    |
      | • Reverse proxy tĩnh        |     | • Ultralytics YOLOv8n (CPU)   |
      +-----------------------------+     +-------------------------------+
                     \                                   /
                      \====== [ Docker Network ] ======/
                                (yolo-net)

===============================================================================
                          LUỒNG TỰ ĐỘNG HÓA CI/CD
===============================================================================

[ Git Push / PR ] ──> [ GitHub Actions CI ] ──> [ GHCR Image Registry ] ──> [ Render Cloud ]
                      • PyTest API               • ghcr.io/.../backend       • Auto-deploy
                      • ESLint & React Build     • ghcr.io/.../frontend      • Health probe
                      • Docker Build Check
```

## 2. Công nghệ Sử dụng (Tech Stack)

| Tầng hệ thống | Công nghệ sử dụng | Vai trò & Đặc điểm kỹ thuật |
|---|---|---|
| Backend API | Python 3.11, FastAPI, Uvicorn | Xây dựng RESTful API hiệu năng cao, cơ chế non-blocking |
| Trí tuệ nhân tạo (AI) | Ultralytics YOLOv8n, OpenCV, PIL | Mô hình Nano tối ưu hóa suy luận CPU, xử lý tensor ảnh/video |
| Frontend UI | React 18, Vite, Tailwind CSS, Lucide | Ứng dụng Single Page hiển thị bounding box, hỗ trợ xuất CSV |
| Đóng gói (Docker) | Dockerfile (Multi-stage), Compose | Non-root runtime (`appuser`), tận dụng Docker layer cache |
| CI/CD Pipeline | GitHub Actions | Tự động hóa kiểm thử đơn vị, kiểm tra đóng gói và xuất bản image |
| Cloud Hosting | Render Web Services (Docker-based) | Triển khai hạ tầng đám mây kèm cơ chế tự động Health Check |

## 3. Tính năng Nổi bật (Features)

- **Nhận diện ảnh đa định dạng:** Hỗ trợ JPG, JPEG, PNG; tự động chuẩn hóa hệ màu RGB, trả về danh sách đối tượng, độ tin cậy và ảnh Base64 có vẽ bounding box.
- **Xử lý video ngắn:** Tiếp nhận video MP4, xử lý từng khung hình và trả về file video đã gán nhãn kèm metadata trong Header phản hồi.
- **Điều chỉnh ngưỡng tin cậy (Confidence Control):** Thanh trượt trực quan cho phép lọc vật thể theo độ tin cậy từ 0.05 đến 1.0.
- **Bộ lọc lớp & Thống kê (Summary & Export):** Hiển thị tổng số lượng từng loại đối tượng phát hiện được và hỗ trợ xuất báo cáo định dạng CSV.
- **Cơ chế gỡ lỗi phân tán (Traceability):** Tự động tạo và đính kèm `X-Request-ID` xuyên suốt từ Frontend qua Middleware đến Logger của Backend.

## 4. Hướng dẫn Cài đặt & Khởi chạy (Local Setup)

### Yêu cầu tiên quyết

- Đã cài đặt Docker Engine và Docker Compose (hoặc Podman).
- Đã cấu hình Git trên môi trường Linux/macOS/WSL2.

### A. Khởi chạy bằng Docker Compose (Khuyên dùng - 1 lệnh duy nhất)

```bash
# 1. Clone mã nguồn dự án
git clone https://github.com/ducanh28807-prog/yolo-web-devops-v2.git
cd yolo-web-devops-v2

# 2. Thiết lập biến môi trường
cp .env.example .env

# 3. Khởi động toàn bộ cụm container
docker compose up -d --build
```

**Kiểm tra dịch vụ cục bộ:**

- Ứng dụng Web: http://localhost:8080
- Tài liệu Swagger UI: http://localhost:8000/docs
- Kiểm tra trạng thái container: `docker compose ps`
- Xem nhật ký hoạt động: `docker compose logs -f`

### B. Khởi chạy môi trường phát triển (Development Mode)

**Chạy Backend**

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Chạy Frontend (Mở terminal khác)**

```bash
cd frontend
npm install
npm run dev
```

## 5. Đặc tả Giao diện Lập trình (API Contract)

### Các Endpoints chính

| Phương thức | Đường dẫn | Chức năng | Phản hồi chính |
|---|---|---|---|
| GET | `/health` | Kiểm tra trạng thái sống của dịch vụ và giới hạn tải | `200 OK` + JSON status |
| GET | `/ready` | Readiness probe kiểm tra mô hình YOLO đã nạp xong | `200 OK` (Sẵn sàng) / `503` |
| POST | `/api/detect/image` | Tải ảnh lên và nhận diện đối tượng | `200 OK` + Bounding Box JSON |
| POST | `/api/detect/video` | Tải video MP4 ngắn lên để xử lý | `200 OK` + File video annotated |

### Cấu trúc dữ liệu phản hồi mẫu (POST `/api/detect/image`)

```json
{
  "filename": "sample.jpg",
  "inference_time_ms": 913.96,
  "total_objects": 2,
  "detections": [
    {
      "class": "person",
      "class_name": "person",
      "confidence": 0.9416,
      "bbox": [12.79, 41.12, 155.86, 399.7]
    }
  ],
  "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "request_id": "req-c185bc1d"
}
```

## 6. Quy trình CI/CD & Tự động hóa (GitHub Actions)

Mỗi lần gửi Pull Request hoặc gộp mã nguồn vào nhánh `main`, pipeline `.github/workflows/ci.yml` sẽ tự động thực thi chuỗi kiểm định nghiêm ngặt.

### Backend Automated Testing

- Cài đặt môi trường Python 3.11 với cache pip.
- Chạy bộ kiểm thử tự động với `pytest -v` (bao gồm: kiểm tra `/health`, xử lý ảnh hợp lệ, và bắt lỗi tệp sai định dạng).

### Frontend Build Verification

- Cài đặt Node.js LTS.
- Kiểm tra tính toàn vẹn gói phụ thuộc và chạy lệnh đóng gói `npm run build` để phát hiện sớm các lỗi cú pháp React/JSX.

### Container Build & Registry Publishing

- Đóng gói Docker images cho cả hai service có sử dụng bộ đệm lớp GitHub Actions Cache (`type=gha`).
- Xuất bản phiên bản container image lên GitHub Packages (GHCR).

## 7. Giám sát, Nhật ký & Khắc phục Sự cố (Observability & Debugging)

### Cơ chế Giám sát & Nhật ký có cấu trúc (Structured Logging)

Backend API ghi nhận nhật ký nghiệp vụ dưới định dạng chuẩn hóa, không rò rỉ dữ liệu nhạy cảm hoặc nội dung file của người dùng:

```text
2026-10-26 18:54:23 [INFO] [yolo-api] INFERENCE_IMAGE [req-5074c9aa] - Tệp: sample.jpg, Dung lượng: 0.03MB, Mô hình: yolov8n.pt, Số vật thể: 2, Inference: 918.84ms

2026-10-26 18:54:37 [WARNING] [yolo-api] HTTP_EXCEPTION [req-e06c4eb1] - Status 400: Tệp tải lên bị hỏng hoặc định dạng 'image/webp' không được hỗ trợ.
```

### Cây quyết định gỡ lỗi (Troubleshooting Guide)

```text
[Lỗi phát sinh trên Web]
   │
   ├── Giao diện báo lỗi "N/A Request ID" hoặc vi phạm CORS?
   │    └── Kiểm tra phản hồi từ Exception Handler: Đảm bảo backend luôn trả về
   │        các header Access-Control-Allow-Origin ngay cả khi gặp lỗi HTTP 4xx/5xx.
   │
   ├── Server văng lỗi "502 Bad Gateway" khi gửi ảnh/video?
   │    └── Kiểm tra Event Loop của FastAPI: Hàm suy luận CPU-bound phải dùng `def`
   │        thường để chạy trên Threadpool, tránh làm nghẽn luồng xử lý ping /ready.
   │
   └── Container bị dừng đột ngột (Exit Code 137 / Killed)?
        └── Kiểm tra tài nguyên: Tệp tải lên vượt quá ngưỡng RAM 512MB trên Render.
            Giảm kích thước ảnh đầu vào (`imgsz=320`) hoặc giới hạn số khung hình video.
```

## 8. Giới hạn Nền tảng & Định hướng Phát triển (Limitations & Future Work)

### Giới hạn kỹ thuật hiện tại

- **Hạ tầng miễn phí (Render Free Tier):** Vận hành trên môi trường chia sẻ CPU, không có GPU chuyên dụng; bộ nhớ RAM bị giới hạn ở mức 512 MB và không có bộ nhớ Swap.
- **Thời gian khởi động lạnh (Cold Start):** Dịch vụ sẽ tự động tạm dừng sau 15 phút không có lượt truy cập, mất khoảng 30–50 giây để tái khởi động ở lần truy cập kế tiếp.
- **Giới hạn tệp tin:** Hình ảnh tối đa 10 MB; video tối đa 5 MB và giới hạn xử lý 150 khung hình (~5 giây) để tránh quá thời gian chờ (request timeout).

### Định hướng mở rộng trong tương lai

- [ ] Tích hợp hàng đợi tác vụ bất đồng bộ (Celery + Redis) để xử lý video dung lượng dài mà không chặn HTTP response.
- [ ] Hỗ trợ mô hình phát hiện chuyên biệt hóa (Custom trained model: đếm phương tiện giao thông, bảo hộ lao động).
- [ ] Mở rộng cơ chế giám sát với Prometheus và Grafana Dashboard để trực quan hóa độ trễ và tỷ lệ lỗi thời gian thực.
