
# Hướng Dẫn Gỡ Lỗi & Cây Quyết Định (Troubleshooting Guide & Decision Tree)

Tài liệu này định hình quy trình chuẩn đoán, cô lập và xử lý sự cố trong hệ thống YOLOv8 Vision Detection Platform, tuân thủ mô hình vận hành DevOps.

---

## 1. Quy Trình Gỡ Lỗi Chuẩn 6 Bước (Standard 6-Step Workflow)

Khi phát hiện bất kỳ sự cố nào từ giao diện hoặc hệ thống giám sát, kỹ sư thực hiện theo chu trình sau:

```text
[1. Reproduce] -> [2. Collect Evidence] -> [3. Isolate Layer] -> [4. Fix] -> [5. Test] -> [6. Document]
```

1. **Reproduce (Tái hiện lỗi):**
   * Xác định chính xác các bước thao tác dẫn tới lỗi: định dạng file tải lên, dung lượng file, ngưỡng confidence, thiết bị/trình duyệt sử dụng.
   * Đảm bảo lỗi có tính lặp lại (reproducible).

2. **Collect Evidence (Thu thập bằng chứng):**
   * **Client-side:** Mở Chrome DevTools (F12) $\rightarrow$ Tab **Console** (ghi nhận exception) $\rightarrow$ Tab **Network** (Status Code, Request/Response Headers, Response Payload).
   * **Server-side (Render / Docker):** Lọc log theo `request_id`, kiểm tra các dòng log mức độ `[WARNING]` hoặc `[ERROR]`, độ trễ `latency_ms` và mức sử dụng tài nguyên (RAM/CPU).

3. **Isolate Layer (Cô lập tầng lỗi):**
   * Phân loại lỗi thuộc tầng nào:
     * *Client/Network:* DNS, CORS policy, Mixed content HTTPS/HTTP.
     * *Ingress/Gateway:* 502 Bad Gateway (Server đang khởi động lại hoặc Crash), 504 Gateway Timeout.
     * *Application Validation:* 400 Bad Request (Sai định dạng file), 413 Payload Too Large (Vượt quá giới hạn dung lượng).
     * *Inference/Runtime:* 500 Internal Server Error (OOM do thiếu RAM, lỗi nạp trọng số YOLO, lỗi OpenCV video writer).

4. **Fix (Thực hiện bản vá):**
   * Sửa chữa trên nhánh tính năng riêng biệt (`fix/...`).
   * Không sửa trực tiếp trên production hoặc nhánh `main`.

5. **Test (Kiểm thử):**
   * Chạy lại test suite cục bộ (`pytest tests/`).
   * Kiểm thử tích hợp từ giao diện người dùng cả trường hợp thành công (happy path) và trường hợp lỗi ngoại lệ (edge cases).

6. **Document (Tài liệu hóa):**
   * Ghi nhận lại nguyên nhân và cách khắc phục vào Incident Report để phục vụ việc chia sẻ kinh nghiệm và cải tiến hệ thống.

---

## 2. Cây Quyết Định Gỡ Lỗi (Troubleshooting Decision Tree)

Sử dụng bảng tra cứu nhanh dưới đây để phản ứng nhanh với các triệu chứng thường gặp:

| Triệu chứng quan sát | Tầng nghi vấn | Điểm kiểm tra (Evidence Checklist) | Hành động khắc phục |
| :--- | :--- | :--- | :--- |
| **Giao diện báo `Mã yêu cầu: N/A` & Console báo CORS error** | Network / CORS | 1. Header `Access-Control-Allow-Origin` có trong Response không?<br>2. Endpoint gây lỗi có trả về qua custom exception handler không? | Đính kèm header CORS tường minh vào `HTTPException` handler của FastAPI. Kiểm tra logic bóc tách `res.json()` tại frontend. |
| **Console báo `502 Bad Gateway`** | Gateway / Cold Start | 1. Service trên Render có đang trong trạng thái khởi động lại (Rebooting) không?<br>2. Endpoint `/ready` đã trả về 200 OK chưa? | Đợi container khởi động xong (thường mất 30-60s với Render Free tier). Cấu hình probe kiểm tra `/ready` trước khi gửi request nặng. |
| **Server trả mã `400 Bad Request`** | Validation | 1. Định dạng file có thuộc danh sách hỗ trợ không (JPG, JPEG, PNG, MP4)?<br>2. File header (magic bytes) có hợp lệ không? | Người dùng cần tải đúng định dạng file. Frontend cần rào trước định dạng file qua thuộc tính `accept` ở thẻ `<input>`. |
| **Server trả mã `413 Payload Too Large`** | Validation / Cloud Limit | Dung lượng file tải lên có vượt ngưỡng cho phép (10MB cho ảnh, 5MB cho video) không? | Nén file hoặc giảm độ phân giải video trước khi gửi lên API. |
| **Container bị restart đột ngột (Exit code 137)** | OS / Memory | Kiểm tra log Render xem có thông báo `Out of Memory (OOM)` hay không. | Giảm batch size, giảm độ phân giải xử lý frame, hoặc chuyển sang model gọn nhẹ hơn (`yolov8n.pt`). |

---

## 3. Vai Trò Của Mã `request_id` Correlation

Hệ thống triển khai cơ chế sinh mã `request_id` (định dạng `req-xxxxxxxx`) duy nhất cho mỗi vòng đời request:
1. Middleware backend tự động tạo hoặc đọc từ header `X-Request-ID`.
2. Mọi dòng log phát sinh trong quá trình xử lý request đều mang con dấu `[req-xxxxxxxx]`.
3. Khi xảy ra lỗi, `request_id` được trả về cả ở Header lẫn JSON Body để Frontend hiển thị lên banner thông báo cho người dùng.
4. Kỹ sư vận hành chỉ cần copy mã này từ màn hình người dùng và tìm kiếm trực tiếp trên Render Logs để định vị chính xác dòng code bị sự cố trong vài giây.
