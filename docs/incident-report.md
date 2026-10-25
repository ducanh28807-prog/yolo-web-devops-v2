
# Báo Cáo Bài Tập Xử Lý Sự Cố (Incident Exercise Report)

* **Mã sự cố (Incident ID):** INC-20261025-CORS-REQID
* **Thời gian xảy ra:** 25/10/2026
* **Hệ thống ảnh hưởng:** Backend API (FastAPI) & Frontend UI (React + Vite)
* **Mức độ nghiêm trọng:** Medium (Chức năng cốt lõi vẫn chạy, nhưng trải nghiệm báo lỗi bị gián đoạn và mất khả năng truy vết log từ phía người dùng).
* **Người thực hiện:** Đội ngũ phát triển DevOps

---

## 1. Triệu Chứng (Symptoms)

* Người dùng tải lên một tệp tin hình ảnh có định dạng không được hỗ trợ (`.webp`) để thử nghiệm cơ chế kiểm tra tính hợp lệ (validation).
* **Hiện tượng tại giao diện:** Màn hình hiển thị banner cảnh báo chung chung:
  `Upload Error: Đã xảy ra lỗi khi kết nối máy chủ. (Mã yêu cầu: N/A)`
* Giá trị định danh truy vết (`request_id`) bị hiển thị thành `N/A`, khiến người dùng không thể cung cấp mã hỗ trợ và kỹ sư không thể tra cứu log tương ứng trên hệ thống giám sát.

---

## 2. Bằng Chứng Thu Thập (Evidence Collected)

1. **Tab Console (Trình duyệt):**
   * Xuất hiện thông báo chặn bảo mật từ trình duyệt:  
     `Access to fetch at 'https://yolo-backend-cupu.onrender.com/api/detect/image' from origin 'https://yolo-frontend-ulf0.onrender.com' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`
   * Kèm theo lỗi mạng: `POST ... net::ERR_FAILED 502 (Bad Gateway)` (trong pha khởi động lại) và `POST ... 400 (Bad Request)`.

2. **Server Logs (Render Dashboard):**
   * Backend vẫn nhận được request và xử lý logic bắt lỗi nghiệp vụ rất chính xác:
     ```text
     2026-10-25 15:24:52 [WARNING] [yolo-api] HTTP_EXCEPTION [req-b4b714b1] - Status 400: Tệp tải lên bị hỏng hoặc định dạng 'image/webp' không được hỗ trợ. Chỉ chấp nhận JPG, JPEG, PNG.
     2026-10-25 15:24:52 [WARNING] [yolo-api] REQUEST_CLIENT_ERROR: {"request_id": "req-b4b714b1", "method": "POST", "route": "/api/detect/image", "status": 400, "latency_ms": 10.02}
     ```
   * Như vậy, backend **thực sự đã sinh mã `req-b4b714b1`**, nhưng thông tin này không tới được người dùng.

3. **Tab Network (Chrome DevTools):**
   * Gói tin phản hồi `400 Bad Request` ban đầu bị thiếu header `Access-Control-Allow-Origin`. Do đó, trình duyệt từ chối cho phép JavaScript đọc nội dung JSON phản hồi.

---

## 3. Phân Tích Nguyên Nhân Gốc Rễ (Root Cause Analysis - RCA)

Sự cố bắt nguồn từ **lỗi kép** ở cả hai tầng Backend và Frontend:

1. **Nguyên nhân tại Backend (CORS on Exception):**
   * FastAPI sử dụng `CORSMiddleware` cho các phản hồi thông thường. Tuy nhiên, khi một ngoại lệ `HTTPException` được kích hoạt, hàm xử lý ngoại lệ tùy biến (`custom_http_exception_handler`) ban đầu chỉ trả về `JSONResponse` chứa header `X-Request-ID` mà **không đính kèm các header CORS**.
   * Hệ quả: Khi trả về mã lỗi 400, trình duyệt coi đây là vi phạm chính sách cùng nguồn gốc (Same-Origin Policy) và chặn hoàn toàn không cho mã client đọc body.

2. **Nguyên nhân tại Frontend (Sai lệch cấu trúc đối tượng lỗi):**
   * Frontend sử dụng hàm `fetch()` của Web API tiêu chuẩn.
   * Khi kiểm tra `!res.ok`, code bóc tách `errData = await res.json()`, nhưng sau đó lại ném ngoại lệ `throw new Error(...)`.
   * Tại khối `catch (err)`, mã nguồn lại cố gắng truy cập `err.response?.data?.request_id` (vốn là cú pháp dành riêng cho thư viện Axios).
   * Vì `err.response` là `undefined`, toán tử fallback `||` đã kích hoạt và gán giá trị `"N/A"`.

---

## 4. Giải Pháp Khắc Phục (Resolution & Fix)

### Bước 1: Vá lỗi Backend (`backend/app/main.py`)
Cập nhật `custom_http_exception_handler` để luôn đính kèm đầy đủ các header CORS cho mọi phản hồi lỗi:
```python
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    request_id = getattr(request.state, "request_id", "req-unknown")
    headers = {
        "X-Request-ID": request_id,
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Expose-Headers": "X-Request-ID",
    }
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "request_id": request_id},
        headers=headers,
    )
```

### Bước 2: Vá lỗi Frontend (`frontend/src/App.jsx`)

Sửa đổi logic xử lý phản hồi lỗi trực tiếp từ đối tượng `res` của `fetch()`:

```javascript
if (!res.ok) {
  let errDetail = `Lỗi ${res.status}: Xử lý thất bại.`;
  let reqId = res.headers.get('X-Request-ID') || "N/A";

  try {
    const errData = await res.json();
    if (errData && errData.detail) errDetail = errData.detail;
    if (errData && errData.request_id) reqId = errData.request_id;
  } catch (_) {
    // Phản hồi không phải JSON
  }

  setError(`${errDetail} (Mã yêu cầu: ${reqId})`);
  return;
}
```

---

## 5. Kiểm Thử & Nghiệm Thu (Verification)

1. Tải lên tệp `c (2).webp` trên môi trường triển khai thực tế.
2. Kiểm tra tab Network:
* Response Headers xuất hiện: `access-control-allow-origin: https://yolo-frontend-ulf0.onrender.com` và `access-control-expose-headers: ..., X-Request-ID`.
* Response Body trả về: `{"detail": "Tệp tải lên bị hỏng hoặc định dạng 'image/webp' không được hỗ trợ...", "request_id": "req-d32f74bd"}`.

3. Giao diện người dùng hiển thị chính xác:
`Upload Error: Tệp tải lên bị hỏng hoặc định dạng 'image/webp' không được hỗ trợ. Chỉ chấp nhận JPG, JPEG, PNG. (Mã yêu cầu: req-d32f74bd)`.
4. Tìm kiếm chuỗi `req-d32f74bd` trong log backend của Render: Dòng log tương ứng được định vị tức thì.

---

## 6. Biện Pháp Phòng Ngừa (Prevention & Lessons Learned)

* **Tự động hóa kiểm thử (CI Test):** Bổ sung test case trong `pytest` để kiểm tra rằng mọi phản hồi lỗi (400, 404, 413, 500) đều phải chứa header `Access-Control-Allow-Origin` và `X-Request-ID`.
* **Nhất quán thư viện HTTP:** Thống nhất việc sử dụng API Client (chọn thuần `fetch` hoặc chuẩn hóa bằng `axios`) trong toàn bộ mã nguồn Frontend để tránh giả định sai về cấu trúc đối tượng lỗi.
