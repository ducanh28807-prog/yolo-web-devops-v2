import io
import time
import base64
from contextlib import asynccontextmanager
from typing import List, Dict, Any

from fastapi import FastAPI, UploadFile, File, Query, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError
from ultralytics import YOLO

# Biến toàn cục lưu trữ instance của mô hình
model_state: Dict[str, Any] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Nạp model duy nhất 1 lần khi server khởi động
    model_name = "yolov8n.pt"
    print(f"[*] Đang nạp mô hình {model_name} vào bộ nhớ CPU...")
    model_state["model"] = YOLO(model_name)
    print("[*] Nạp mô hình hoàn tất.")
    yield
    # Dọn dẹp tài nguyên khi tắt server
    model_state.clear()

app = FastAPI(
    title="YOLO Object Detection API",
    description="Backend API phục vụ nhận diện vật thể ảnh/video cho Lab Train DevOps",
    version="0.2.0",
    lifespan=lifespan,
)

# Cấu hình CORS cho phép frontend kết nối
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {
        "status": "healthy",
        "service": "yolo-backend",
        "model_loaded": "model" in model_state,
        "version": "0.2.0"
    }

@app.post("/api/detect/image")
async def detect_image(
    file: UploadFile = File(...),
    conf_threshold: float = Query(default=0.25, ge=0.05, le=1.0, description="Ngưỡng tin cậy (0.05 - 1.0)")
):
    # 1. Kiểm tra định dạng Content-Type
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Định dạng tệp không được hỗ trợ ({file.content_type}). Chỉ chấp nhận JPG, JPEG, PNG."
        )

    # 2. Đọc dữ liệu file và xác thực tính toàn vẹn của ảnh
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        image.verify()  # Kiểm tra file có thực sự là ảnh hợp lệ hay không
        image = Image.open(io.BytesIO(image_bytes))  # Mở lại để xử lý sau khi verify
    except (UnidentifiedImageError, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tệp tải lên bị hỏng hoặc không phải là hình ảnh hợp lệ."
        )

    model = model_state.get("model")
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mô hình YOLO chưa sẵn sàng."
        )

    # 3. Thực hiện suy luận (Inference) và đo lường thời gian
    start_time = time.time()
    results = model.predict(source=image, conf=conf_threshold, device="cpu")
    inference_time_ms = round((time.time() - start_time) * 1000, 2)

    result = results[0]
    detections: List[Dict[str, Any]] = []

    # 4. Trích xuất metadata có cấu trúc
    for box in result.boxes:
        cls_id = int(box.cls[0].item())
        class_name = result.names[cls_id]
        confidence = round(float(box.conf[0].item()), 4)
        xyxy = [round(float(coord), 2) for coord in box.xyxy[0].tolist()]

        detections.append({
            "class_name": class_name,
            "confidence": confidence,
            "bbox": xyxy  # [x_min, y_min, x_max, y_max]
        })

    # 5. Vẽ nhãn và bounding box lên ảnh kết quả rồi mã hóa Base64
    annotated_bgr = result.plot()
    annotated_rgb = annotated_bgr[..., ::-1]  # Chuyển BGR sang RGB
    annotated_img = Image.fromarray(annotated_rgb)

    buffered = io.BytesIO()
    annotated_img.save(buffered, format="JPEG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return {
        "inference_time_ms": inference_time_ms,
        "total_objects": len(detections),
        "detections": detections,
        "image_base64": f"data:image/jpeg;base64,{img_base64}"
    }
