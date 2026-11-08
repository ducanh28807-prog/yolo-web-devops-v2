# Báo Cáo Đóng Góp Cá Nhân & Bài Học Kinh Nghiệm (Individual Reflection)

- **Họ và tên:** Nguyễn Đức Anh
- **Dự án:** YOLOv8 Object Detection Web Platform (DevOps Workflow)
- **Vai trò:** Kỹ sư DevOps & Full-stack Developer

---

## 1. Đóng góp kỹ thuật chính (Key Technical Contributions)

Trong suốt 7 tuần triển khai dự án, tôi đã trực tiếp đảm nhận và hoàn thành các hạng mục kỹ thuật cốt lõi:

1. **Containerization & Mạng nội bộ (Week 3):**
   * Đóng gói Backend FastAPI và Frontend React bằng Dockerfile tối ưu hóa kích thước: sử dụng multi-stage build cho Frontend với base image Nginx Alpine nhẹ, và chạy user non-root `appuser` cho Backend trên `python:3.11-slim`[cite: 1, 4].
   * Thiết lập file `compose.yaml` cho phép khởi chạy toàn bộ cụm dịch vụ chỉ với một lệnh duy nhất (`docker compose up -d --build`) trên mạng nội bộ độc lập `yolo-net`[cite: 1, 4, 5].
   * **Cấu hình Nginx Reverse Proxy ở Local:** Trong môi trường Docker Compose, cấu hình Nginx đóng vai trò Reverse Proxy nhận request từ trình duyệt và điều hướng nội bộ sang container backend thông qua **service name** (`http://backend:8000`), giúp bảo mật cổng nội bộ và độc lập với địa chỉ IP của máy host[cite: 1, 4, 5].

2. **CI/CD Pipeline Tự động hóa (Week 4):**
   * Xây dựng workflow GitHub Actions `.github/workflows/ci.yml` tự động kích hoạt khi có Push hoặc Pull Request vào nhánh `main`[cite: 1, 5].
   * Tự động hóa bộ kiểm thử đơn vị với PyTest, kiểm tra lỗi cú pháp và đóng gói Frontend (`npm run build`), kiểm tra tính toàn vẹn của cấu trúc Docker Compose[cite: 1, 5].
   * Tối ưu hóa thời gian build bằng cơ chế GitHub Actions Cache (`type=gha`) và tự động xuất bản container images lên GitHub Container Registry (GHCR)[cite: 1, 5].

3. **Triển khai Cloud & Chuyển dịch Kiến trúc Mạng (Week 5):**
   * Triển khai hệ thống lên hạ tầng đám mây Render Web Services (Docker runtime), quản lý bảo mật thông tin qua biến môi trường (Environment Variables)[cite: 1, 6].
   * **Chuyển đổi từ Local Proxy sang Cloud Static/Public API:** Khi đưa lên Cloud công cộng, không còn mạng nội bộ Docker chung giữa hai service[cite: 1, 4, 6]. Đã chuyển dịch kiến trúc: Frontend được build thành Static bundle độc lập, gọi trực tiếp ra **Public HTTPS URL** của Backend thông qua biến môi trường `VITE_API_BASE_URL`, đồng thời thiết lập chính sách CORS liên domain để trình duyệt cho phép giao tiếp an toàn[cite: 1, 4, 6].
   * Tối ưu hóa suy luận: Giới hạn kích thước tensor đầu vào (`imgsz=320`), giới hạn video ngắn (tối đa 30 khung hình) để hệ thống vận hành bền bỉ trên môi trường CPU-only giới hạn khắt khe 512MB RAM[cite: 1, 6].

4. **Giám sát, Bóc tách log & Xử lý sự cố (Week 6 & Week 7):**
   * Triển khai chuẩn Structured Logging với con dấu truy vết `X-Request-ID` xuyên suốt từ Client qua Middleware đến Server[cite: 1, 7].
   * Bổ sung cơ chế thăm dò trạng thái nâng cao (`/health` cho liveness và `/ready` cho readiness probe)[cite: 1, 7].
   * Trực tiếp phân tích, cách ly và xử lý thành công 2 sự cố phức tạp nối tiếp nhau:
     * *Sự cố 1 (CORS & N/A Request ID):* Sửa lỗi rớt header CORS tại `http_exception_handler` và chuẩn hóa cơ chế bóc tách lỗi tại Frontend từ đối tượng Response của `fetch()`[cite: 1, 10, 11].
     * *Sự cố 2 (502 Bad Gateway / Container Restart):* Phát hiện lỗi nghẽn Event Loop do hàm bất đồng bộ `async def` gánh tác vụ nặng CPU-bound khiến Render ping `/ready` bị timeout[cite: 1, 7]. Đã khắc phục triệt để bằng cách chuyển sang `def` đồng bộ để đưa việc suy luận vào Threadpool riêng biệt và bọc `global_exception_handler`[cite: 1, 7].
   * Hoàn thiện tài liệu kiến trúc hệ thống, đặc tả API contract trong `README.md` và biên soạn báo cáo xử lý sự cố chuẩn mực `incident-report.md`[cite: 1, 7, 8].

---

## 2. Bài học kinh nghiệm & Tư duy DevOps rút ra (Lessons Learned)

- **Sự khác biệt giữa Local Networking và Cloud Networking:** Hiểu sâu bản chất định tuyến: Ở môi trường Docker Compose local, các container nói chuyện bằng DNS nội bộ qua service name[cite: 1, 5]; nhưng khi lên môi trường Cloud (Render), Frontend chạy trên trình duyệt người dùng phải gọi qua Public Internet vào Backend[cite: 1, 4, 6]. Điều này đòi hỏi kỹ sư phải nắm vững cách cấu hình CORS, cơ chế HTTPS và phân định rõ biến môi trường lúc build-time (Vite) so với run-time (FastAPI)[cite: 1, 4, 6].
- **Tư duy Parity Testing (Đồng nhất môi trường):** Sự chênh lệch giữa máy trạm phát triển và môi trường Cloud thực tế (sức mạnh CPU, dung lượng RAM, cơ chế Swap và chính sách kill process của platform) có thể khiến code chạy hoàn hảo ở local nhưng sập ngay lập tức trên Cloud[cite: 1, 6, 8]. Việc sử dụng `podman run -m 512m` để mô phỏng chính xác ngưỡng giới hạn tài nguyên của Render là một bài học thực tế đắt giá[cite: 1, 4, 8].
- **Hiểu sâu cơ chế bất đồng bộ (Async vs Sync trong Python/FastAPI):** Không lạm dụng từ khóa `async def` cho các tác vụ tính toán nặng (CPU-bound) như Machine Learning inference (YOLO, PyTorch) hay xử lý media (OpenCV)[cite: 1, 4]. Việc đẩy tác vụ CPU-bound sang Threadpool bằng hàm `def` thường là nguyên tắc sống còn để giữ Event Loop chính luôn thông suốt cho các luồng kiểm tra sức khỏe hệ thống (Health Check)[cite: 1, 4, 7].
- **Khả năng quan sát (Observability) là chìa khóa vận hành:** Một hệ thống không có log chi tiết và mã định danh tương quan (`request_id`) thì khi có lỗi xảy ra trên production sẽ hoàn toàn rơi vào trạng thái phỏng đoán[cite: 1, 7]. Việc thiết lập log có cấu trúc và đính kèm `request_id` đa tầng giúp rút ngắn thời gian khoanh vùng nguyên nhân gốc rễ từ hàng giờ xuống chỉ còn vài phút[cite: 1, 7].
- **Thiết kế phòng vệ trước giới hạn tài nguyên (Graceful Degradation):** Nhận diện rõ các đặc tính của hạ tầng miễn phí (thời gian khởi động lạnh - cold start, không có GPU, RAM thấp) để chủ động đặt ra các giới hạn bảo vệ: kích thước file, số lượng frame xử lý và cơ chế dọn dẹp file tạm tự động nhằm đảm bảo hệ thống không bao giờ bị rơi vào trạng thái từ chối dịch vụ[cite: 1, 6, 8].
