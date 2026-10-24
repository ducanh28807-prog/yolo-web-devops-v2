import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from main import app

@pytest.fixture(scope="module")
def client():
    # Khối 'with' bắt buộc để kích hoạt sự kiện lifespan (nạp model vào CPU)
    with TestClient(app) as test_client:
        yield test_client

def test_health_check(client):
    """Test 1: Kiểm tra endpoint /health trả về 200 và model đã nạp"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "yolo-backend"
    assert data["model_loaded"] is True

def test_detect_image_invalid_file(client):
    """Test 2: Kiểm tra validation khi gửi file hỏng (kỳ vọng 400)"""
    fake_file_content = b"Day la file van ban gia mao anh"
    files = {"file": ("fake_image.png", fake_file_content, "image/png")}
    response = client.post("/api/detect/image", files=files)
    
    assert response.status_code == 400
    assert "Tệp tải lên bị hỏng" in response.json()["detail"]

def test_detect_image_valid_synthetic_image(client):
    """Test 3: Kiểm tra nhận diện ảnh hợp lệ (kỳ vọng 200 và có metadata)"""
    # Tạo ảnh đỏ 100x100 trong RAM để gửi test
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_bytes = img_byte_arr.getvalue()

    files = {"file": ("test.jpg", img_bytes, "image/jpeg")}
    response = client.post("/api/detect/image?conf_threshold=0.25", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "inference_time_ms" in data
    assert "total_objects" in data
    assert "detections" in data
    assert "image_base64" in data
    assert data["image_base64"].startswith("data:image/jpeg;base64,")
