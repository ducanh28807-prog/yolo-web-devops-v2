# YOLO Web App & DevOps Pipeline

Dự án xây dựng ứng dụng web nhận diện vật thể bằng mô hình YOLO (FastAPI + React) kết hợp triển khai tự động hóa CI/CD và Containerization theo lộ trình Lab Train DevOps 2026.

## 1. Mục Tiêu Dự Án
- Xây dựng API phát hiện vật thể qua ảnh và video ngắn với FastAPI và Ultralytics YOLO.
- Phát triển giao diện tương tác người dùng trực quan bằng React + Vite.
- Đóng gói ứng dụng chuẩn hóa với Docker và quản lý đa dịch vụ bằng Docker Compose.
- Tự động hóa kiểm thử, build và xuất bản container image lên GitHub Container Registry qua GitHub Actions.
- Triển khai ứng dụng lên nền tảng cloud (Render) kèm hệ thống logging, monitoring và tài liệu xử lý sự cố.

## 2. Thành Viên Thực Hiện
- Nguyễn Đức Anh (Sinh viên K70 - ĐH Bách khoa Hà Nội)

## 3. Điều Kiện Tiên Quyết (Prerequisites)
- Hệ điều hành: Linux (Ubuntu x86_64)
- Git >= 2.40
- Python 3.10+
- Container Runtime: Docker Engine hoặc Podman (với `podman.socket` đang hoạt động)

## 4. Cấu Trúc Nhánh & Quy Trình Phát Triển
Chi tiết về quy chuẩn làm việc nhóm và đóng góp mã nguồn được ghi rõ tại [CONTRIBUTING.md](./CONTRIBUTING.md).
