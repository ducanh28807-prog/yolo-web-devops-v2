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
- **Hướng dẫn Gỡ lỗi (Troubleshooting Guide):** [docs/troubleshooting.md](./docs/troubleshooting.md)
- **Bài thu hoạch Cá nhân (Week 7 Reflection):** [docs/REFLECTION.md](./docs/REFLECTION.md)

---

## 1. Kiến trúc Hệ thống (System Architecture)

Hệ thống được thiết kế theo mô hình Microservices tách biệt giữa giao diện tĩnh (Frontend SPA) và dịch vụ xử lý AI tính toán nặng (Backend API), kết nối qua mạng nội bộ Docker ở môi trường Local và giao tiếp qua Public HTTPS API trên Cloud.

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

---

## 2. Công nghệ Sử dụng (Tech Stack)

| Tầng hệ thống | Công nghệ sử dụng | Vai trò & Đặc điểm kỹ thuật |
|---|---|---|
| **Backend API** | Python 3.11, FastAPI, Uvicorn | Xây dựng RESTful API hiệu năng cao, non-blocking Threadpool |
| **Trí tuệ nhân tạo (AI)** | Ultralytics YOLOv8n, OpenCV, PIL | Mô hình Nano tối ưu hóa suy luận CPU, xử lý tensor ảnh/video |
| **Frontend UI** | React 18, Vite, Tailwind CSS, Lucide | Ứng dụng Single Page hiển thị bounding box, xuất báo cáo CSV |
| **Đóng gói (Docker)** | Dockerfile (Multi-stage), Compose | Non-root runtime (`appuser`), tận dụng Docker layer cache |
| **CI/CD Pipeline** | GitHub Actions | Tự động hóa kiểm thử đơn vị, kiểm tra đóng gói và xuất bản image |
| **Cloud Hosting** | Render Web Services (Docker-based) | Triển khai hạ tầng đám mây kèm cơ chế tự động Health Check |

---

## 3. Tính năng Nổi bật (Features)

- **Nhận diện ảnh đa định dạng:** Hỗ trợ JPG, JPEG, PNG; tự động tiền xử lý kích thước bảo vệ tài nguyên (tối đa 640px), trả về danh sách đối tượng, độ tin cậy và ảnh Base64 có vẽ bounding box.
- **Xử lý video ngắn tối ưu:** Tiếp nhận video MP4, tự động co khung hình về 320p để CPU xử lý siêu tốc trong ~5–7s, khống chế an toàn 30 frames (~1.0s), hỗ trợ tải trực tiếp file kết quả về máy.
- **Điều chỉnh ngưỡng tin cậy (Confidence Control):** Thanh trượt trực quan cho phép lọc vật thể theo độ tin cậy từ 0.05 đến 1.0.
- **Bộ lọc lớp & Xuất báo cáo (Summary & CSV Export):** Hiển thị tổng số lượng từng loại đối tượng phát hiện được và hỗ trợ xuất báo cáo định dạng CSV đầy đủ qua `expose_headers`.
- **Cơ chế gỡ lỗi phân tán (Traceability):** Tự động tạo và đính kèm `X-Request-ID` xuyên suốt từ Frontend qua Middleware đến Logger của Backend.

---

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
```bash
# Chạy Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Chạy Frontend (Mở terminal khác)
cd frontend
npm install
npm run dev
```

---

## 5. Đặc tả Giao diện Lập trình (API Contract)

### Các Endpoints chính

| Phương thức | Đường dẫn | Chức năng | Phản hồi chính |
|:---:|---|---|---|
| `GET` | `/health` | Kiểm tra trạng thái sống của dịch vụ và giới hạn tải | `200 OK` + JSON status |
| `GET` | `/ready` | Readiness probe kiểm tra mô hình YOLO đã nạp xong | `200 OK` (Sẵn sàng) / `503` |
| `POST` | `/api/detect/image` | Tải ảnh lên và nhận diện đối tượng | `200 OK` + Bounding Box JSON |
| `POST` | `/api/detect/video` | Tải video MP4 ngắn lên để xử lý | `200 OK` + File video annotated |

### Cấu trúc dữ liệu phản hồi mẫu (`POST /api/detect/image`)
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

---

## 6. Quy trình CI/CD & Tự động hóa (GitHub Actions)

Mỗi lần gửi Pull Request hoặc gộp mã nguồn vào nhánh `main`, pipeline `.github/workflows/ci.yml` sẽ tự động thực thi chuỗi kiểm định nghiêm ngặt:

1. **Backend Automated Testing:** Khởi tạo môi trường Python 3.11, thực thi bộ kiểm thử `pytest -v` (kiểm tra `/health`, xử lý ảnh hợp lệ và bắt lỗi tệp sai định dạng).
2. **Frontend Build Verification:** Khởi tạo Node.js LTS, kiểm tra cú pháp và chạy lệnh đóng gói `npm run build` để phát hiện sớm các lỗi build-time.
3. **Container Build & Registry Publishing:** Đóng gói Docker images sử dụng bộ đệm lớp GitHub Actions Cache (`type=gha`), tự động xuất bản lên GitHub Packages (GHCR).

---

## 7. Giám sát, Nhật ký & Quy trình Gỡ lỗi Tuần tự (Observability & Debugging)

### Cơ chế Giám sát & Nhật ký có cấu trúc (Structured Logging)
Backend API ghi nhận nhật ký nghiệp vụ dưới định dạng chuẩn hóa, không rò rỉ dữ liệu nhạy cảm hoặc nội dung file của người dùng:
```text
2026-10-26 18:54:23 [INFO] [yolo-api] INFERENCE_IMAGE [req-5074c9aa] - Tệp: sample.jpg, Dung lượng: 0.03MB, Mô hình: yolov8n.pt, Số vật thể: 2, Inference: 918.84ms
2026-10-26 18:54:37 [WARNING] [yolo-api] HTTP_EXCEPTION [req-e06c4eb1] - Status 400: Tệp tải lên bị hỏng hoặc định dạng 'image/webp' không được hỗ trợ.
```

### Cây quyết định gỡ lỗi theo chuỗi nhân quả (Sequential Troubleshooting Tree)

```text
[Phát hiện Sự Cố Hệ Thống]
   │
   ├── [Nấc 1]: Giao diện báo lỗi "N/A Request ID" hoặc vi phạm CORS?
   │    └── Nguyên nhân: Exception Handler của FastAPI chưa đính kèm CORS headers khi trả lỗi 4xx.
   │    └── Xử lý: Ép trả CORS header trực tiếp trong custom http_exception_handler.
   │
   ├── [Nấc 2]: Sửa xong Nấc 1, gửi ảnh bị "502 Bad Gateway" / Container Restart?
   │    └── Nguyên nhân: Hàm inference dùng `async def` làm nghẽn Event Loop khiến Render ping /ready bị timeout.
   │    └── Xử lý: Chuyển hàm sang `def` đồng bộ để FastAPI đưa tác vụ nặng vào Threadpool riêng.
   │
   ├── [Nấc 3]: Sửa xong Nấc 2, ảnh nhỏ chạy mượt nhưng ảnh > 500KB văng 502 / Máy chủ không phản hồi?
   │    └── Nguyên nhân: Bung mảng pixel thô từ ảnh độ phân giải cao làm chạm trần RAM 512MB hoặc CPU tính toán quá lâu.
   │    └── Xử lý: Áp dụng cơ chế tiền xử lý co kích thước ảnh về tối đa 640px trước khi suy luận.
   │
   └── [Nấc 4]: Video xử lý mất 11.5 phút / chạm trần timeout 49s, video đen màn hình, CSV rỗng?
        └── Nguyên nhân: Video 1080p quá nặng cho vCPU; codec mp4v không chạy trên web; CORS thiếu expose_headers.
        └── Xử lý: Resize video về tối đa 320px (kích thước chẵn), chuyển FourCC sang avc1, giới hạn 30 frames và mở toàn bộ expose_headers.
```

---

## 8. Giới hạn Nền tảng & Định hướng Phát triển (Limitations & Future Work)

### Giới hạn kỹ thuật hiện tại
- **Hạ tầng đám mây (Render Free Tier):** Vận hành trên CPU chia sẻ, không có GPU chuyên dụng; bộ nhớ RAM bị giới hạn khắt khe ở mức 512 MB và không có bộ nhớ Swap.
- **Cơ chế tiền xử lý bảo vệ tài nguyên (Auto Pre-resizing):** Ảnh tải lên tự động được tối ưu cạnh lớn nhất về 640px bằng thuật toán LANCZOS trước khi suy luận, giúp giải phóng mảng tensor khổng lồ và triệt tiêu nguy cơ quá tải bộ nhớ.
- **Thời gian khởi động lạnh (Cold Start):** Dịch vụ tự động tạm dừng sau 15 phút không có lượt truy cập, mất khoảng 30–50 giây để tái khởi động ở lần truy cập kế tiếp.
- **Giới hạn tệp tin:** Hình ảnh tối đa 10 MB; video tối đa 5 MB, tự động co về 320p và giới hạn xử lý 30 khung hình (~1.0 giây) để tránh quá thời gian chờ (request timeout).

### Định hướng mở rộng trong tương lai
- [ ] Tích hợp hàng đợi tác vụ bất đồng bộ (Celery + Redis) để xử lý video dung lượng dài mà không chặn HTTP response.
- [ ] Hỗ trợ mô hình phát hiện chuyên biệt hóa (Custom trained model: đếm phương tiện giao thông, bảo hộ lao động).
- [ ] Mở rộng cơ chế giám sát với Prometheus và Grafana Dashboard để trực quan hóa độ trễ và tỷ lệ lỗi thời gian thực.
