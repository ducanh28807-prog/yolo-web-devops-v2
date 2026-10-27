# Hướng Dẫn Chẩn Đoán & Khắc Phục Sự Cố Tuần Tự (Sequential Troubleshooting Guide)

Tài liệu này chuẩn hóa quy trình điều tra và xử lý sự cố trên nền tảng YOLO Web Platform theo mô hình leo thang 4 bước tuần tự (**Sequential Triage Flow**). Các lỗi được sắp xếp đúng theo thứ tự nhân quả: từ tầng giao tiếp mạng, tầng xử lý luồng, tầng tài nguyên phần cứng cho đến trạng thái nền tảng.

---

## 1. Sơ Đồ Cây Chẩn Đoán Leo Thang (Sequential Triage Tree)

```text
[BẮT ĐẦU: Phát hiện lỗi khi người dùng thao tác trên Web]
   │
   ▼
[BƯỚC 1: Kiểm tra tầng Giao tiếp & Header CORS]
   │── Triệu chứng: Console báo đỏ CORS, UI hiện "Mã yêu cầu: N/A".
   │── Nguyên nhân: Exception Handler trả về thiếu header Access-Control-Allow-Origin.
   │── Biện pháp: Đính kèm CORS headers và X-Request-ID trực tiếp trong http_exception_handler.
   │── Đã đạt yêu cầu? ──► [CHUYỂN TIẾP SANG BƯỚC 2]
   │
   ▼
[BƯỚC 2: Kiểm tra tầng Quản lý Luồng & Event Loop]
   │── Triệu chứng: CORS đã chuẩn, nhưng khi gửi ảnh hợp lệ thì văng 502, Render restart container.
   │── Nguyên nhân: Hàm inference dùng `async def` làm nghẽn Event Loop khiến Render ping /ready bị timeout.
   │── Biện pháp: Đổi sang `def` đồng bộ để FastAPI tự động điều phối tác vụ sang Threadpool riêng.
   │── Đã đạt yêu cầu? ──► [CHUYỂN TIẾP SANG BƯỚC 3]
   │
   ▼
[BƯỚC 3: Kiểm tra tầng Bộ nhớ RAM & Độ phân giải Tệp tin]
   │── Triệu chứng: Ảnh nhỏ (<100KB) chạy tốt, nhưng ảnh lớn (>500KB / ảnh 4K) bị treo hoặc văng 502.
   │── Nguyên nhân: Bung mảng pixel thô từ ảnh lớn làm vọt quá ngưỡng RAM 512MB (OOM) hoặc quá tải CPU.
   │── Biện pháp: Thêm bộ tiền xử lý `image.thumbnail((640, 640))` thu nhỏ ảnh trước khi đưa vào YOLO.
   │── Đã đạt yêu cầu? ──► [CHUYỂN TIẾP SANG BƯỚC 4]
   │
   ▼
[BƯỚC 4: Kiểm tra tầng Vòng đời Dịch vụ & Khởi động lạnh (Cold Start)]
   │── Triệu chứng: Giao diện báo "Backend: OFFLINE" ngay khi vừa mở trang web.
   │── Nguyên nhân: Gói Render Free Tier tự động tạm dừng (spin down) container sau 15 phút không có traffic.
   └── Biện pháp: Chờ 30–50 giây để container thức dậy, hoặc truy cập trực tiếp /health để đánh thức dịch vụ.
```

---

## 2. Chi Tiết Các Kịch Bản Khắc Phục Theo Thứ Tự Leo Thang

### Nấc 1: Sự cố gãy liên kết mã định danh (CORS & Missing Request-ID)
* **Hiện tượng:** Khi tải file không hợp lệ (ví dụ `.webp`), Console ghi nhận mã `400 Bad Request` từ backend nhưng giao diện người dùng lại báo `Upload Error: Đã xảy ra lỗi khi kết nối máy chủ. (Mã yêu cầu: N/A)`.
* **Cách xác định:** Mở DevTools $\rightarrow$ tab Network $\rightarrow$ bấm vào request bị đỏ $\rightarrow$ kiểm tra mục Response Headers xem có dòng `Access-Control-Allow-Origin` hay không.
* **Khắc phục:** Bổ sung dictionary headers đầy đủ vào `http_exception_handler` và cập nhật logic bóc tách `res.json()` tại React.

### Nấc 2: Sự cố nghẽn luồng xử lý chính (Event Loop Blocking & 502 Bad Gateway)
* **Hiện tượng:** Khắc phục xong Nấc 1, tải tệp ảnh hợp lệ thì trình duyệt chờ rất lâu rồi nhận mã `502 Bad Gateway`. Kiểm tra log Render thấy xuất hiện dòng `Starting server process [1]` (container bị khởi động lại).
* **Cách xác định:** Kiểm tra khai báo endpoint: nếu là `async def detect_image(...)` mà bên trong chứa lệnh tính toán nặng `model.predict(...)` thì chính là nguyên nhân làm đứng Event Loop.
* **Khắc phục:** Đổi định nghĩa hàm thành `def detect_image(...)` để kích hoạt cơ chế multi-threading ngầm của Starlette.

### Nấc 3: Sự cố quá tải bộ nhớ do ảnh độ phân giải cao (Memory Spike & High-Res OOM)
* **Hiện tượng:** Khắc phục xong Nấc 2, ảnh chụp nhẹ thử nghiệm chạy thành công trong 900ms, nhưng khi người dùng tải ảnh chụp từ camera điện thoại (dung lượng trên 500KB, kích thước 4000x3000) thì server lại bị đơ hoặc ngắt kết nối.
* **Cách xác định:** Chạy thử nghiệm cục bộ với lệnh `podman run -m 512m` và kiểm tra dung lượng RAM khi chuyển đổi sang mảng RGB.
* **Khắc phục:** Áp dụng phương thức `image.thumbnail((640, 640), Image.Resampling.LANCZOS)` ngay sau khi mở ảnh để khống chế kích thước ma trận pixel đầu vào.

### Nấc 4: Xử lý trạng thái ngủ đông của hạ tầng Cloud (Platform Cold Start)
* **Hiện tượng:** Giao diện vừa mở lên hiển thị ngay thanh thông báo đỏ `Backend: OFFLINE`.
* **Cách xác định:** Mở trực tiếp đường link `[https://yolo-backend-cupu.onrender.com/health](https://yolo-backend-cupu.onrender.com/health)` trên tab mới. Nếu trình duyệt xoay vòng khoảng 30 giây rồi mới hiện `{"status": "healthy"}`, đó là hiện tượng Cold Start bình thường của Render Free Tier.
* **Khắc phục:** Chờ container khởi động hoàn tất, giao diện React có cơ chế polling định kỳ sẽ tự động chuyển sang trạng thái xanh `Backend: ONLINE`.
