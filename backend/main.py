import io
import os
import time
import json
import uuid
import base64
import logging
import tempfile
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional

import cv2
from fastapi import FastAPI, Request, UploadFile, File, Query, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from ultralytics import YOLO

# 1. Cấu hình Structured Logger chuẩn Python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [yolo-api] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("yolo-api")

model_state: Dict[str, Any] = {}

def get_env_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default

MAX_IMAGE_SIZE_MB = get_env_int("MAX_UPLOAD_SIZE_MB", 10)
MAX_VIDEO_SIZE_MB = get_env_int("MAX_VIDEO_SIZE_MB", 5)
MAX_VIDEO_FRAMES = 150  # ~5 giây ở 30fps

def cleanup_files(*file_paths: str):
    """Hàm dọn dẹp file tạm chạy ngầm"""
    for path in file_paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    model_name = os.getenv("MODEL_NAME", "yolov8n.pt")
    logger.info(f"KHỞI ĐỘNG HỆ THỐNG: Đang nạp mô hình '{model_name}' vào CPU...")
    model_state["model"] = YOLO(model_name)
    model_state["model_name"] = model_name
    logger.info(f"KHỞI ĐỘNG HOÀN TẤT: Mô hình '{model_name}' đã sẵn sàng nhận diện.")
    yield
    model_state.clear()
    logger.info("DỪNG HỆ THỐNG: Đã giải phóng bộ nhớ mô hình.")

app = FastAPI(
    title="YOLO Object Detection API",
    description="Backend API phục vụ nhận diện vật thể ảnh/video cho Lab Train DevOps",
    version="0.4.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Summary-Counts", "X-Inference-Time-Ms", "X-Request-ID"]
)

# 2. Middleware cấp phát Request ID và ghi Structured Log cho từng lượt gọi
@app.middleware("http")
async def structured_logging_middleware(request: Request, call_next):
    # Lấy Request-ID từ client gửi lên hoặc tự sinh mã duy nhất (Correlation ID)
    request_id = request.headers.get("X-Request-ID") or f"req-{uuid.uuid4().hex[:8]}"
    request.state.request_id = request_id

    start_time = time.time()
    response = await call_next(request)
    latency_ms = round((time.time() - start_time) * 1000, 2)

    # Đính kèm X-Request-ID vào response header để client đối chiếu khi có lỗi
    response.headers["X-Request-ID"] = request_id

    # Đóng gói log dạng cấu trúc (Structured JSON Payload)
    log_data = {
        "request_id": request_id,
        "method": request.method,
        "route": request.url.path,
        "status": response.status_code,
        "latency_ms": latency_ms,
        "client_ip": request.client.host if request.client else "unknown"
    }

    if response.status_code < 400:
        logger.info(f"REQUEST_SUCCESS: {json.dumps(log_data)}")
    elif response.status_code < 500:
        logger.warning(f"REQUEST_CLIENT_ERROR: {json.dumps(log_data)}")
    else:
        logger.error(f"REQUEST_SERVER_ERROR: {json.dumps(log_data)}")

    return response

# 3. Exception Handler tùy biến: trả mã lỗi đính kèm request_id mà không làm gãy test
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(f"HTTP_EXCEPTION [{request_id}] - Status {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "request_id": request_id
        },
        headers={"X-Request-ID": request_id}
    )

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check(request: Request):
    """Health check cơ bản cho Container và Render"""
    return {
        "status": "healthy",
        "service": "yolo-backend",
        "model_loaded": "model" in model_state,
        "version": "0.4.0",
        "request_id": getattr(request.state, "request_id", "unknown"),
        "limits": {
            "max_image_mb": MAX_IMAGE_SIZE_MB,
            "max_video_mb": MAX_VIDEO_SIZE_MB,
            "max_video_frames": MAX_VIDEO_FRAMES
        }
    }

@app.get("/ready", status_code=status.HTTP_200_OK)
def readiness_check():
    """Readiness probe theo đề cương Week 6: Kiểm tra model đã nạp xong chưa"""
    if "model" not in model_state:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hệ thống chưa sẵn sàng: Mô hình YOLO đang được nạp."
        )
    return {"status": "ready", "model": model_state.get("model_name")}

@app.post("/api/detect/image")
async def detect_image(
    request: Request,
    file: UploadFile = File(...),
    conf_threshold: float = Query(default=0.25, ge=0.05, le=1.0),
    confidence: Optional[float] = Query(default=None, ge=0.05, le=1.0)
):
    req_id = getattr(request.state, "request_id", "unknown")
    threshold = confidence if confidence is not None else conf_threshold

    # 1. Kiểm tra định dạng
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    ext = os.path.splitext(file.filename or "")[1].lower()
    if file.content_type not in allowed_types and ext not in [".jpg", ".jpeg", ".png"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tệp tải lên bị hỏng hoặc định dạng '{file.content_type}' không được hỗ trợ. Chỉ chấp nhận JPG, JPEG, PNG."
        )

    image_bytes = await file.read()
    file_size_mb = round(len(image_bytes) / (1024 * 1024), 2)

    # 2. Kiểm tra dung lượng
    if file_size_mb > MAX_IMAGE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dung lượng ảnh ({file_size_mb}MB) vượt quá giới hạn cho phép (tối đa {MAX_IMAGE_SIZE_MB}MB). Vui lòng chọn ảnh nhẹ hơn."
        )

    # 3. Xác thực cấu trúc ảnh
    try:
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
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Mô hình YOLO chưa sẵn sàng.")

    start_infer = time.time()
    results = model.predict(source=image, conf=threshold, device="cpu", verbose=False)
    inference_time_ms = round((time.time() - start_infer) * 1000, 2)

    result = results[0]
    detections: List[Dict[str, Any]] = []

    for box in result.boxes:
        cls_id = int(box.cls[0].item())
        detections.append({
            "class": result.names[cls_id],
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

    # Structured business log cho luồng ảnh
    logger.info(
        f"INFERENCE_IMAGE [{req_id}] - Tệp: {file.filename}, Dung lượng: {file_size_mb}MB, "
        f"Mô hình: {model_state.get('model_name')}, Số vật thể: {len(detections)}, Inference: {inference_time_ms}ms"
    )

    return {
        "filename": file.filename,
        "inference_time_ms": inference_time_ms,
        "total_objects": len(detections),
        "detections": detections,
        "image_base64": f"data:image/jpeg;base64,{img_base64}",
        "request_id": req_id
    }

@app.post("/api/detect/video")
async def detect_video(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    conf_threshold: float = Query(default=0.25, ge=0.05, le=1.0),
    confidence: Optional[float] = Query(default=None, ge=0.05, le=1.0)
):
    req_id = getattr(request.state, "request_id", "unknown")
    threshold = confidence if confidence is not None else conf_threshold

    # 1. Kiểm tra định dạng MP4
    if file.content_type != "video/mp4" and not (file.filename and file.filename.lower().endswith(".mp4")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tệp tải lên bị hỏng hoặc định dạng '{file.content_type}' không được hỗ trợ. Chỉ chấp nhận video MP4."
        )

    # 2. Kiểm tra dung lượng video
    contents = await file.read()
    file_size_mb = round(len(contents) / (1024 * 1024), 2)
    if file_size_mb > MAX_VIDEO_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dung lượng video ({file_size_mb}MB) vượt quá giới hạn cho phép (tối đa {MAX_VIDEO_SIZE_MB}MB). Vui lòng chọn clip nhẹ hơn."
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as in_temp:
        in_temp.write(contents)
        input_path = in_temp.name

    out_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    output_path = out_temp.name
    out_temp.close()

    model = model_state.get("model")
    if model is None:
        cleanup_files(input_path, output_path)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Mô hình YOLO chưa sẵn sàng.")

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        cleanup_files(input_path, output_path)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tệp tải lên bị hỏng: Không thể mở tệp video.")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    summary_counts: Dict[str, int] = {}
    detected_classes = set()
    frame_count = 0
    start_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame_count >= MAX_VIDEO_FRAMES:
                break

            results = model.predict(source=frame, conf=threshold, device="cpu", verbose=False)
            res = results[0]

            for box in res.boxes:
                cls_name = res.names[int(box.cls[0].item())]
                summary_counts[cls_name] = summary_counts.get(cls_name, 0) + 1
                detected_classes.add(cls_name)

            annotated_frame = res.plot()
            out.write(annotated_frame)
            frame_count += 1
    except Exception as exc:
        cleanup_files(input_path, output_path)
        logger.error(f"XỬ LÝ VIDEO THẤT BẠI [{req_id}]: {str(exc)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi khi xử lý video: {str(exc)}")
    finally:
        cap.release()
        out.release()

    total_time_ms = round((time.time() - start_time) * 1000, 2)
    duration_sec = round(frame_count / fps, 1)

    # Structured business log cho luồng video
    logger.info(
        f"INFERENCE_VIDEO [{req_id}] - Tệp: {file.filename}, Số khung hình: {frame_count}, "
        f"Thời lượng: {duration_sec}s, Tổng phát hiện: {sum(summary_counts.values())}, Tổng thời gian: {total_time_ms}ms"
    )

    background_tasks.add_task(cleanup_files, input_path, output_path)

    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"detected_{file.filename or 'output.mp4'}",
        headers={
            "X-Summary-Counts": json.dumps(summary_counts),
            "X-Total-Detections": str(sum(summary_counts.values())),
            "X-Detected-Classes": ", ".join(list(detected_classes)),
            "X-Duration-Seconds": str(duration_sec),
            "X-Inference-Time-Ms": str(total_time_ms),
            "X-Request-ID": req_id
        }
    )
