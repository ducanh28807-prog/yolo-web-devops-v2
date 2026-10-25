import os
import shutil
import tempfile
import cv2
from fastapi import FastAPI, File, UploadFile, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from ultralytics import YOLO

app = FastAPI(title="YOLO Object Detection API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_NAME = os.getenv("MODEL_NAME", "yolov8n.pt")
model = YOLO(MODEL_NAME)

MAX_IMAGE_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
MAX_VIDEO_SIZE_MB = int(os.getenv("MAX_VIDEO_SIZE_MB", "5"))
MAX_VIDEO_DURATION_SEC = float(os.getenv("MAX_VIDEO_DURATION_SEC", "10.0"))

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "model": MODEL_NAME,
        "limits": {
            "max_image_mb": MAX_IMAGE_SIZE_MB,
            "max_video_mb": MAX_VIDEO_SIZE_MB,
            "max_video_duration_sec": MAX_VIDEO_DURATION_SEC
        }
    }

@app.post("/api/detect/image")
async def detect_image(
    file: UploadFile = File(...),
    confidence: float = Query(0.25, ge=0.0, le=1.0)
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Only accept JPG, JPEG, and PNG images."
        )

    contents = await file.read()
    file_size_mb = len(contents) / (1024 * 1024)
    if file_size_mb > MAX_IMAGE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Exceeding limit: Image size is {file_size_mb:.2f}MB, maximum allowed is {MAX_IMAGE_SIZE_MB}MB. Only accept files <= {MAX_IMAGE_SIZE_MB}MB."
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    out_path = None
    try:
        results = model.predict(source=tmp_path, conf=confidence)
        res = results[0]

        detections = []
        for box in res.boxes:
            cls_id = int(box.cls[0].item())
            cls_name = res.names[cls_id]
            conf = float(box.conf[0].item())
            xyxy = [float(x) for x in box.xyxy[0].tolist()]
            detections.append({
                "class": cls_name,
                "confidence": round(conf, 4),
                "bbox": [round(x, 1) for x in xyxy]
            })

        fd, out_path = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)
        res.save(filename=out_path)

        with open(out_path, "rb") as f:
            annotated_bytes = f.read()

        import base64
        base64_img = base64.b64encode(annotated_bytes).decode("utf-8")

        return {
            "filename": file.filename,
            "count": len(detections),
            "detections": detections,
            "image_base64": f"data:image/jpeg;base64,{base64_img}",
            "speed": res.speed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        if out_path and os.path.exists(out_path):
            os.remove(out_path)

@app.post("/api/detect/video")
async def detect_video(
    file: UploadFile = File(...),
    confidence: float = Query(0.25, ge=0.0, le=1.0)
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext != ".mp4":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '{ext}'. Only accept MP4 video files."
        )

    contents = await file.read()
    file_size_mb = len(contents) / (1024 * 1024)
    if file_size_mb > MAX_VIDEO_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Exceeding limit: Video size is {file_size_mb:.2f}MB, maximum allowed is {MAX_VIDEO_SIZE_MB}MB. Only accept clips <= {MAX_VIDEO_SIZE_MB}MB."
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_in:
        tmp_in.write(contents)
        tmp_in_path = tmp_in.name

    cap = cv2.VideoCapture(tmp_in_path)
    if not cap.isOpened():
        if os.path.exists(tmp_in_path):
            os.remove(tmp_in_path)
        raise HTTPException(status_code=400, detail="Cannot read video file.")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps

    if duration > MAX_VIDEO_DURATION_SEC:
        cap.release()
        if os.path.exists(tmp_in_path):
            os.remove(tmp_in_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Exceeding limit: Video duration is {duration:.1f}s, maximum allowed is {MAX_VIDEO_DURATION_SEC}s on Cloud. Please upload a shorter clip."
        )

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fd, tmp_out_path = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)
    out = cv2.VideoWriter(tmp_out_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

    detected_classes = set()
    total_detections = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            results = model.predict(source=frame, conf=confidence, verbose=False)
            res = results[0]
            annotated_frame = res.plot()
            out.write(annotated_frame)
            total_detections += len(res.boxes)
            for box in res.boxes:
                detected_classes.add(res.names[int(box.cls[0].item())])
    finally:
        cap.release()
        out.release()
        if os.path.exists(tmp_in_path):
            os.remove(tmp_in_path)

    return FileResponse(
        tmp_out_path,
        media_type="video/mp4",
        filename=f"detected_{file.filename}",
        headers={
            "X-Total-Detections": str(total_detections),
            "X-Detected-Classes": ", ".join(list(detected_classes)),
            "X-Duration-Seconds": f"{duration:.1f}"
        }
    )
