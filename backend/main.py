from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="YOLO Object Detection API",
    description="Backend API phục vụ nhận diện vật thể ảnh/video cho Lab Train DevOps",
    version="0.1.0",
)

# Cấu hình CORS cơ bản cho phép frontend giao tiếp
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "yolo-backend",
        "version": "0.1.0"
    }
