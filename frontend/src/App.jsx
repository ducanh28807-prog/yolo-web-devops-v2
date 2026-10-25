import React, { useState, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

export default function App() {
  const [activeTab, setActiveTab] = useState('image');
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [confidence, setConfidence] = useState(0.25);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [backendStatus, setBackendStatus] = useState('checking');

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then(res => res.json())
      .then(data => {
        if (data.status === 'healthy') setBackendStatus('online');
        else setBackendStatus('error');
      })
      .catch(() => setBackendStatus('offline'));
  }, []);

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      setFile(selected);
      setPreviewUrl(URL.createObjectURL(selected));
      setResult(null);
      setError(null);
    }
  };

  const handleDetect = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    const endpoint = activeTab === 'image'
      ? `${API_BASE}/api/detect/image?confidence=${confidence}`
      : `${API_BASE}/api/detect/video?confidence=${confidence}`;

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        let errMessage = `Error ${res.status}: Failed to process request.`;
        try {
          const errData = await res.json();
          if (errData && errData.detail) {
            errMessage = errData.detail;
          }
        } catch (_) {}
        throw new Error(errMessage);
      }

      if (activeTab === 'image') {
        const data = await res.json();
        setResult(data);
      } else {
        const blob = await res.blob();
        const videoUrl = URL.createObjectURL(blob);
        setResult({
          videoUrl,
          total: res.headers.get('X-Total-Detections') || 'N/A',
          classes: res.headers.get('X-Detected-Classes') || 'None',
          duration: res.headers.get('X-Duration-Seconds') || 'N/A'
        });
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col items-center p-6">
      <header className="w-full max-w-4xl flex items-center justify-between pb-6 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            🚀 YOLOv8 Vision Detection
          </h1>
          <p className="text-xs text-slate-400 mt-1">DevOps Pipeline & Cloud Deployment Platform</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Backend:</span>
          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
            backendStatus === 'online' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
            backendStatus === 'checking' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
            'bg-rose-500/20 text-rose-400 border border-rose-500/30'
          }`}>
            {backendStatus.toUpperCase()}
          </span>
        </div>
      </header>

      <main className="w-full max-w-4xl mt-6 space-y-6">
        {/* Tab Selection */}
        <div className="flex bg-slate-800/80 p-1 rounded-xl border border-slate-700/60 max-w-xs">
          <button
            onClick={() => { setActiveTab('image'); setFile(null); setPreviewUrl(null); setResult(null); setError(null); }}
            className={`flex-1 py-1.5 text-sm font-medium rounded-lg transition-all ${
              activeTab === 'image' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            Image
          </button>
          <button
            onClick={() => { setActiveTab('video'); setFile(null); setPreviewUrl(null); setResult(null); setError(null); }}
            className={`flex-1 py-1.5 text-sm font-medium rounded-lg transition-all ${
              activeTab === 'video' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            Video
          </button>
        </div>

        {/* Upload Card */}
        <div className="bg-slate-800/50 border border-slate-700/60 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex flex-col items-center justify-center border-2 border-dashed border-slate-600 hover:border-indigo-500/60 rounded-xl p-8 bg-slate-900/40 transition-colors">
            <input
              type="file"
              accept={activeTab === 'image' ? "image/png, image/jpeg, image/jpg" : "video/mp4"}
              onChange={handleFileChange}
              className="text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer"
            />

            {/* Rào trước quy định file upload */}
            <div className="mt-4 text-center text-xs text-slate-400 bg-slate-800/80 px-4 py-2 rounded-lg border border-slate-700/80">
              <span className="font-semibold text-slate-300">Giới hạn định dạng & dung lượng:</span>
              {activeTab === 'image' ? (
                <p className="mt-0.5 text-slate-400">
                  Chỉ chấp nhận <span className="text-indigo-300 font-medium">JPG, JPEG, PNG</span> • Dung lượng tối đa <span className="text-indigo-300 font-medium">10 MB</span>
                </p>
              ) : (
                <p className="mt-0.5 text-slate-400">
                  Chỉ chấp nhận <span className="text-indigo-300 font-medium">MP4</span> • Dung lượng tối đa <span className="text-indigo-300 font-medium">5 MB</span> • Độ dài khuyến nghị <span className="text-indigo-300 font-medium">&le; 10 giây</span>
                </p>
              )}
            </div>
          </div>

          {/* Confidence Slider */}
          <div className="flex items-center justify-between pt-2">
            <label className="text-sm font-medium text-slate-300 flex items-center gap-2">
              Confidence Threshold:
              <span className="text-indigo-400 font-bold">{Math.round(confidence * 100)}%</span>
            </label>
            <input
              type="range"
              min="0.05"
              max="0.95"
              step="0.05"
              value={confidence}
              onChange={(e) => setConfidence(parseFloat(e.target.value))}
              className="w-48 accent-indigo-500 cursor-pointer"
            />
          </div>

          <button
            onClick={handleDetect}
            disabled={!file || loading}
            className={`w-full py-2.5 rounded-xl font-semibold text-sm transition-all shadow-lg ${
              !file || loading
                ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/30'
            }`}
          >
            {loading ? "Processing Inference..." : `Detect Objects in ${activeTab === 'image' ? 'Image' : 'Video'}`}
          </button>
        </div>

        {/* User-facing Error State Banner */}
        {error && (
          <div className="bg-rose-500/10 border border-rose-500/40 rounded-xl p-4 flex items-start gap-3 text-rose-300">
            <span className="text-lg">⚠️</span>
            <div className="text-xs leading-relaxed">
              <span className="font-semibold block text-rose-200 mb-0.5">Upload Error:</span>
              {error}
            </div>
          </div>
        )}

        {/* Result Viewer */}
        {result && (
          <div className="bg-slate-800/50 border border-slate-700/60 rounded-2xl p-6 shadow-xl space-y-4">
            <h2 className="text-lg font-bold text-white flex items-center justify-between">
              <span>Detection Results</span>
              {activeTab === 'image' && (
                <span className="text-xs bg-indigo-500/20 text-indigo-300 px-2.5 py-1 rounded-full border border-indigo-500/30 font-medium">
                  {result.count} object(s) found
                </span>
              )}
            </h2>

            {activeTab === 'image' ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <p className="text-xs font-semibold text-slate-400">Original</p>
                  <img src={previewUrl} alt="Original" className="w-full rounded-xl border border-slate-700 object-contain max-h-80" />
                </div>
                <div className="space-y-2">
                  <p className="text-xs font-semibold text-slate-400">Annotated (YOLOv8)</p>
                  <img src={result.image_base64} alt="Annotated" className="w-full rounded-xl border border-slate-700 object-contain max-h-80" />
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <video src={result.videoUrl} controls className="w-full rounded-xl border border-slate-700 max-h-96" />
                <div className="grid grid-cols-3 gap-2 text-center text-xs bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                  <div>
                    <span className="text-slate-500 block">Detections</span>
                    <span className="text-indigo-400 font-bold">{result.total}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Duration</span>
                    <span className="text-indigo-400 font-bold">{result.duration}s</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Detected Classes</span>
                    <span className="text-indigo-400 font-bold truncate block">{result.classes}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
