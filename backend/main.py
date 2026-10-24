import io
import os
import time
import json
import base64
import tempfile
from contextlib import asynccontextmanager
from typing import List, Dict, Any

import cv2
from fastapi import FastAPI, UploadFile, File, Query, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError
from ultralytics import YOLO

model_state: Dict[str, Any] = {}

# Giới hạn xử lý an toàn cho môi trường CPU
MAX_VIDEO_SIZE_MB = 10
MAX_VIDEO_FRAMES = 150  # Khoảng 5 giây ở tốc độ 30fps

def cleanup_files(*file_paths: str):
    """Hàm chạy nền để xóa tệp tạm sau khi gửi response hoàn tất"""
    for path in file_paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    model_name = "yolov8n.pt"
    print(f"[*] Đang nạp mô hình {model_name} vào bộ nhớ CPU...")
    model_state["model"] = YOLO(model_name)
    print("[*] Nạp mô hình hoàn tất.")
    yield
    model_state.clear()

app = FastAPI(
    title="YOLO Object Detection API",
    description="Backend API phục vụ nhận diện vật thể ảnh/video cho Lab Train DevOps",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Summary-Counts", "X-Inference-Time-Ms"]
)

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {
        "status": "healthy",
        "service": "yolo-backend",
        "model_loaded": "model" in model_state,
        "version": "0.3.0"
    }

@app.post("/api/detect/image")
async def detect_image(
    file: UploadFile = File(...),
    conf_threshold: float = Query(default=0.25, ge=0.05, le=1.0)
):
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Định dạng tệp không được hỗ trợ ({file.content_type}). Chỉ chấp nhận JPG, JPEG, PNG."
        )

    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        image.verify()
        image = Image.open(io.BytesIO(image_bytes))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tệp tải lên bị hỏng hoặc không phải là hình ảnh hợp lệ."
        )

    model = model_state.get("model")
    if model is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model chưa sẵn sàng.")

    start_time = time.time()
    results = model.predict(source=image, conf=conf_threshold, device="cpu")
    inference_time_ms = round((time.time() - start_time) * 1000, 2)

    result = results[0]
    detections: List[Dict[str, Any]] = []

    for box in result.boxes:
        cls_id = int(box.cls[0].item())
        detections.append({
            "class_name": result.names[cls_id],
            "confidence": round(float(box.conf[0].item()), 4),
            "bbox": [round(float(coord), 2) for coord in box.xyxy[0].tolist()]
        })

    annotated_bgr = result.plot()
    annotated_rgb = annotated_bgr[..., ::-1]
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

@app.post("/api/detect/video")
async def detect_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    conf_threshold: float = Query(default=0.25, ge=0.05, le=1.0)
):
    # 1. Kiểm tra định dạng MP4
    if file.content_type != "video/mp4" and not (file.filename and file.filename.lower().endswith(".mp4")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Định dạng video không được hỗ trợ ({file.content_type}). Chỉ chấp nhận video MP4."
        )

    # 2. Đọc và kiểm tra kích thước file
    contents = await file.read()
    file_size_mb = len(contents) / (1024 * 1024)
    if file_size_mb > MAX_VIDEO_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dung lượng video vượt quá giới hạn cho phép ({file_size_mb:.2f}MB > {MAX_VIDEO_SIZE_MB}MB)."
        )

    # 3. Tạo các file tạm trên đĩa để OpenCV xử lý
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as in_temp:
        in_temp.write(contents)
        input_path = in_temp.name

    out_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    output_path = out_temp.name
    out_temp.close()

    model = model_state.get("model")
    if model is None:
        cleanup_files(input_path, output_path)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model chưa sẵn sàng.")

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        cleanup_files(input_path, output_path)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể mở hoặc giải mã tệp video.")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    summary_counts: Dict[str, int] = {}
    frame_count = 0
    start_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame_count >= MAX_VIDEO_FRAMES:
                break

            # Dự đoán trên frame hiện tại
            results = model.predict(source=frame, conf=conf_threshold, device="cpu", verbose=False)
            res = results[0]

            for box in res.boxes:
                cls_name = res.names[int(box.cls[0].item())]
                summary_counts[cls_name] = summary_counts.get(cls_name, 0) + 1

            annotated_frame = res.plot()
            out.write(annotated_frame)
            frame_count += 1
    except Exception as exc:
        cleanup_files(input_path, output_path)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi khi xử lý video: {str(exc)}")
    finally:
        cap.release()
        out.release()

    total_time_ms = round((time.time() - start_time) * 1000, 2)

    # Đăng ký tác vụ nền: Xóa cả 2 tệp tạm sau khi gửi file xong
    background_tasks.add_task(cleanup_files, input_path, output_path)

    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename="detected_output.mp4",
        headers={
            "X-Summary-Counts": json.dumps(summary_counts),
            "X-Inference-Time-Ms": str(total_time_ms)
        }
    )
