import React, { useState, useEffect } from 'react';
import { 
  Activity, ShieldCheck, Upload, Video, Image as ImageIcon, 
  Sliders, Loader2, Clock, CheckCircle2, AlertCircle, FileText 
} from 'lucide-react';
import axios from 'axios';

// Tự động nhận diện host (localhost hoặc IP máy ảo) để trỏ về cổng backend 8000
const API_BASE = "";

function App() {
  const [activeTab, setActiveTab] = useState('image'); // 'image' hoặc 'video'
  const [backendStatus, setBackendStatus] = useState('Đang kiểm tra...');
  const [isHealthy, setIsHealthy] = useState(false);
  const [confThreshold, setConfThreshold] = useState(0.25);

  // State cho ảnh
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [imageResult, setImageResult] = useState(null);
  const [isImageLoading, setIsImageLoading] = useState(false);

  // State cho video
  const [videoFile, setVideoFile] = useState(null);
  const [videoPreview, setVideoPreview] = useState(null);
  const [videoResultUrl, setVideoResultUrl] = useState(null);
  const [videoSummary, setVideoSummary] = useState(null);
  const [isVideoLoading, setIsVideoLoading] = useState(false);

  const [errorMessage, setErrorMessage] = useState('');

  // Kiểm tra sức khỏe Backend
  useEffect(() => {
    axios.get(`${API_BASE}/health`)
      .then(res => {
        if (res.data.status === 'healthy') {
          setBackendStatus('Kết nối thành công (Model sẵn sàng)');
          setIsHealthy(true);
        }
      })
      .catch(() => {
        setBackendStatus(`Không thể kết nối Backend (${API_BASE})`);
        setIsHealthy(false);
      });
  }, []);

  // Xử lý chọn ảnh
  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImageFile(file);
      setImagePreview(URL.createObjectURL(file));
      setImageResult(null);
      setErrorMessage('');
    }
  };

  // Gửi ảnh lên backend
  const handleDetectImage = async () => {
    if (!imageFile) return;
    setIsImageLoading(true);
    setErrorMessage('');

    const formData = new FormData();
    formData.append('file', imageFile);

    try {
      const response = await axios.post(
        `${API_BASE}/api/detect/image?conf_threshold=${confThreshold}`, 
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      setImageResult(response.data);
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Lỗi khi gửi ảnh lên máy chủ.');
    } finally {
      setIsImageLoading(false);
    }
  };

  // Xử lý chọn video
  const handleVideoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 10 * 1024 * 1024) {
        setErrorMessage('File video vượt quá giới hạn 10MB!');
        return;
      }
      setVideoFile(file);
      setVideoPreview(URL.createObjectURL(file));
      setVideoResultUrl(null);
      setVideoSummary(null);
      setErrorMessage('');
    }
  };

  // Gửi video lên backend
  const handleDetectVideo = async () => {
    if (!videoFile) return;
    setIsVideoLoading(true);
    setErrorMessage('');

    const formData = new FormData();
    formData.append('file', videoFile);

    try {
      const response = await axios.post(
        `${API_BASE}/api/detect/video?conf_threshold=${confThreshold}`,
        formData,
        { 
          headers: { 'Content-Type': 'multipart/form-data' },
          responseType: 'blob' 
        }
      );

      // Lấy metadata từ header
      const summaryHeader = response.headers['x-summary-counts'];
      const inferenceTime = response.headers['x-inference-time-ms'];
      
      let summaryCounts = {};
      if (summaryHeader) {
        try { summaryCounts = JSON.parse(summaryHeader); } catch (_) {}
      }

      setVideoSummary({
        timeMs: inferenceTime || 'N/A',
        counts: summaryCounts
      });

      // Tạo Blob URL để phát video trả về
      const videoBlob = new Blob([response.data], { type: 'video/mp4' });
      setVideoResultUrl(URL.createObjectURL(videoBlob));
    } catch (err) {
      setErrorMessage('Lỗi khi xử lý video. Hãy đảm bảo video dưới 10MB và đúng định dạng MP4.');
    } finally {
      setIsVideoLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 flex flex-col items-center">
      {/* Tiêu đề */}
      <header className="max-w-5xl w-full text-center py-4 border-b border-slate-800">
        <h1 className="text-3xl font-extrabold tracking-tight text-white mb-1">
          YOLOv8 Detection Workspace
        </h1>
        <p className="text-slate-400 text-sm">
          Giao diện kiểm thử hệ thống nhận diện đối tượng theo chuẩn luồng DevOps
        </p>
      </header>

      {/* Thanh trạng thái Server */}
      <div className="max-w-5xl w-full mt-4 flex items-center justify-between px-4 py-2 bg-slate-900 rounded-lg border border-slate-800 text-xs">
        <div className="flex items-center space-x-2">
          <Activity className={`w-4 h-4 ${isHealthy ? 'text-emerald-400 animate-pulse' : 'text-amber-400'}`} />
          <span className="text-slate-300">Backend:</span>
          <span className={`font-semibold ${isHealthy ? 'text-emerald-400' : 'text-amber-400'}`}>{backendStatus}</span>
        </div>
        <div className="flex items-center space-x-1 text-slate-400">
          <ShieldCheck className="w-4 h-4 text-indigo-400" />
          <span>YOLOv8n CPU Engine</span>
        </div>
      </div>

      {/* Điều khiển chung & Chuyển Tab */}
      <div className="max-w-5xl w-full mt-6 flex flex-col md:flex-row items-center justify-between gap-4 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
        <div className="flex space-x-2">
          <button
            onClick={() => { setActiveTab('image'); setErrorMessage(''); }}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
              activeTab === 'image' 
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20' 
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            <ImageIcon className="w-4 h-4" />
            <span>Nhận diện Ảnh</span>
          </button>

          <button
            onClick={() => { setActiveTab('video'); setErrorMessage(''); }}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
              activeTab === 'video' 
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20' 
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            <Video className="w-4 h-4" />
            <span>Nhận diện Video</span>
          </button>
        </div>

        {/* Thanh trượt Confidence Threshold */}
        <div className="flex items-center space-x-3 w-full md:w-auto px-2">
          <Sliders className="w-4 h-4 text-indigo-400" />
          <span className="text-xs text-slate-300 whitespace-nowrap">Độ tin cậy:</span>
          <input 
            type="range" 
            min="0.1" 
            max="0.9" 
            step="0.05"
            value={confThreshold}
            onChange={(e) => setConfThreshold(parseFloat(e.target.value))}
            className="w-32 h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
          />
          <span className="text-xs font-mono text-indigo-300 w-8">{confThreshold.toFixed(2)}</span>
        </div>
      </div>

      {/* Thông báo lỗi nếu có */}
      {errorMessage && (
        <div className="max-w-5xl w-full mt-4 p-3 bg-rose-950/60 border border-rose-800 rounded-lg flex items-center space-x-2 text-rose-300 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Nội dung Tab: IMAGE */}
      {activeTab === 'image' && (
        <main className="max-w-5xl w-full mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Cột trái: Tải ảnh */}
          <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800 flex flex-col justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-200 mb-3 flex items-center space-x-2">
                <Upload className="w-4 h-4 text-indigo-400" />
                <span>Tải ảnh đầu vào</span>
              </h2>

              <label className="flex flex-col items-center justify-center border-2 border-dashed border-slate-700 hover:border-indigo-500 rounded-xl p-6 cursor-pointer bg-slate-950/50 transition">
                {imagePreview ? (
                  <img src={imagePreview} alt="Preview" className="max-h-64 object-contain rounded-lg" />
                ) : (
                  <div className="text-center">
                    <ImageIcon className="w-10 h-10 text-slate-500 mx-auto mb-2" />
                    <p className="text-xs text-slate-300">Nhấn để chọn hoặc kéo thả ảnh (JPG, PNG)</p>
                  </div>
                )}
                <input type="file" accept="image/*" onChange={handleImageChange} className="hidden" />
              </label>
            </div>

            <button
              onClick={handleDetectImage}
              disabled={!imageFile || isImageLoading}
              className={`w-full mt-5 py-2.5 rounded-lg text-sm font-medium flex items-center justify-center space-x-2 transition ${
                !imageFile || isImageLoading
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                  : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/30'
              }`}
            >
              {isImageLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Đang phân tích ảnh...</span>
                </>
              ) : (
                <span>Bắt đầu nhận diện</span>
              )}
            </button>
          </div>

          {/* Cột phải: Kết quả ảnh */}
          <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800 flex flex-col">
            <h2 className="text-sm font-semibold text-slate-200 mb-3 flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Kết quả nhận diện</span>
            </h2>

            {imageResult ? (
              <div className="flex-1 flex flex-col">
                <div className="flex items-center space-x-4 mb-3 text-xs">
                  <span className="flex items-center text-slate-300">
                    <Clock className="w-3.5 h-3.5 mr-1 text-indigo-400" />
                    {imageResult.inference_time_ms} ms
                  </span>
                  <span className="px-2 py-0.5 bg-indigo-950 text-indigo-300 border border-indigo-800 rounded-md font-mono">
                    {imageResult.total_objects} vật thể
                  </span>
                </div>

                <div className="bg-slate-950 rounded-xl p-2 flex items-center justify-center mb-4">
                  <img src={imageResult.image_base64} alt="Detected" className="max-h-64 object-contain rounded-lg" />
                </div>

                {/* Bảng chi tiết detections */}
                <div className="flex-1 overflow-y-auto max-h-40 border border-slate-800 rounded-lg p-2 bg-slate-950/40">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="text-slate-400 border-b border-slate-800">
                        <th className="pb-1">Vật thể</th>
                        <th className="pb-1">Độ tin cậy</th>
                      </tr>
                    </thead>
                    <tbody>
                      {imageResult.detections.map((d, idx) => (
                        <tr key={idx} className="border-b border-slate-800/40 text-slate-300">
                          <td className="py-1 font-medium">{d.class_name}</td>
                          <td className="py-1 text-emerald-400 font-mono">{(d.confidence * 100).toFixed(1)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-500 border border-dashed border-slate-800 rounded-xl p-8">
                <FileText className="w-8 h-8 mb-2 stroke-[1.5]" />
                <p className="text-xs">Chưa có kết quả. Hãy tải ảnh và nhấn nút phân tích.</p>
              </div>
            )}
          </div>
        </main>
      )}

      {/* Nội dung Tab: VIDEO */}
      {activeTab === 'video' && (
        <main className="max-w-5xl w-full mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Cột trái: Tải video */}
          <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800 flex flex-col justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-200 mb-3 flex items-center space-x-2">
                <Upload className="w-4 h-4 text-violet-400" />
                <span>Tải video ngắn (&le; 10MB)</span>
              </h2>

              <label className="flex flex-col items-center justify-center border-2 border-dashed border-slate-700 hover:border-violet-500 rounded-xl p-6 cursor-pointer bg-slate-950/50 transition">
                {videoPreview ? (
                  <video src={videoPreview} controls className="max-h-60 rounded-lg" />
                ) : (
                  <div className="text-center">
                    <Video className="w-10 h-10 text-slate-500 mx-auto mb-2" />
                    <p className="text-xs text-slate-300">Nhấn để chọn file MP4 (Tối đa 5-10 giây)</p>
                  </div>
                )}
                <input type="file" accept="video/mp4" onChange={handleVideoChange} className="hidden" />
              </label>
            </div>

            <button
              onClick={handleDetectVideo}
              disabled={!videoFile || isVideoLoading}
              className={`w-full mt-5 py-2.5 rounded-lg text-sm font-medium flex items-center justify-center space-x-2 transition ${
                !videoFile || isVideoLoading
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                  : 'bg-violet-600 hover:bg-violet-500 text-white shadow-lg shadow-violet-600/30'
              }`}
            >
              {isVideoLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Đang xử lý video từng frame...</span>
                </>
              ) : (
                <span>Bắt đầu xử lý Video</span>
              )}
            </button>
          </div>

          {/* Cột phải: Kết quả video */}
          <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800 flex flex-col">
            <h2 className="text-sm font-semibold text-slate-200 mb-3 flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Video đã nhận diện</span>
            </h2>

            {videoResultUrl ? (
              <div className="flex-1 flex flex-col">
                <div className="flex items-center space-x-3 mb-3 text-xs">
                  <span className="flex items-center text-slate-300">
                    <Clock className="w-3.5 h-3.5 mr-1 text-violet-400" />
                    Thời gian: {videoSummary?.timeMs} ms
                  </span>
                </div>

                <div className="bg-slate-950 rounded-xl p-2 mb-4">
                  <video src={videoResultUrl} controls autoPlay loop className="max-h-60 w-full rounded-lg" />
                </div>

                {/* Bảng tổng hợp số lượng vật thể */}
                <div className="border border-slate-800 rounded-lg p-3 bg-slate-950/40">
                  <p className="text-xs text-slate-400 mb-2 font-medium">Tổng số đối tượng xuất hiện:</p>
                  <div className="flex flex-wrap gap-2">
                    {videoSummary && Object.entries(videoSummary.counts).length > 0 ? (
                      Object.entries(videoSummary.counts).map(([name, count]) => (
                        <span key={name} className="px-2.5 py-1 bg-violet-950/80 text-violet-300 border border-violet-800 rounded-md text-xs">
                          {name}: <strong className="text-white">{count}</strong>
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-500">Không có đối tượng nào vượt ngưỡng tin cậy.</span>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-500 border border-dashed border-slate-800 rounded-xl p-8">
                <Video className="w-8 h-8 mb-2 stroke-[1.5]" />
                <p className="text-xs">Chưa có kết quả. Xử lý video trên CPU sẽ mất khoảng 5–15 giây.</p>
              </div>
            )}
          </div>
        </main>
      )}
    </div>
  );
}

export default App;
