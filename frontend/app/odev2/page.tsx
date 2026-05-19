"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Button } from "@heroui/react";

const API_BASE = process.env.NODE_ENV === "development" ? "http://localhost:8000/api" : "/api";
const MODEL_NAME = "car_damage";

export default function Odev2Page() {
  const [activeTab, setActiveTab] = useState<"upload" | "camera">("upload");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState("");
  const [resultImage, setResultImage] = useState("");
  const [detections, setDetections] = useState<Array<{ class: string; confidence: number }>>([]);
  const [loading, setLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  // Camera real-time stream
  const [streaming, setStreaming] = useState(false);
  const [streamLoading, setStreamLoading] = useState(false);
  const [facingMode, setFacingMode] = useState<"environment" | "user">("environment");
  const [detectionCount, setDetectionCount] = useState(0);
  const [streamResultImage, setStreamResultImage] = useState<string | null>(null);
  const [fps, setFps] = useState(0);

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const processingRef = useRef(false);

  const wsRef = useRef<WebSocket | null>(null);
  const rafRef = useRef<number>(0);
  const lastFpsTimeRef = useRef<number>(0);
  const frameCountRef = useRef<number>(0);
  const lastDetectionCountRef = useRef<number>(0);
  const pendingRef = useRef(false);
  const reqIdRef = useRef<number>(0);

  const WS_URL = process.env.NODE_ENV === "development" ? "ws://localhost:8000/ws/detect/" : `wss://${typeof window !== 'undefined' ? window.location.host : ''}/ws/detect/`;

  // Auto-stop on unmount
  useEffect(() => {
    return () => stopStream();
  }, []);

  const handleImageSelect = (file: File) => {
    setImageFile(file);
    const reader = new FileReader();
    reader.onload = (e) => setImagePreview(e.target?.result as string);
    reader.readAsDataURL(file);
    setResultImage("");
    setDetections([]);
  };

  const runDetection = async () => {
    if (!imageFile) return;
    setLoading(true);
    const formData = new FormData();
    formData.append("model_name", MODEL_NAME);
    formData.append("image", imageFile);
    formData.append("task", "segment");
    try {
      const res = await fetch(`${API_BASE}/detect/`, { method: "POST", body: formData });
      const data = await res.json();
      if (data.success) {
        setResultImage(data.image);
        setDetections(data.detections);
      }
    } catch (e) {
      console.error("Segmentation failed:", e);
    } finally {
      setLoading(false);
    }
  };

  const startStream = async (mode = facingMode) => {
    setStreamLoading(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: mode, width: { ideal: 640 }, height: { ideal: 480 } },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setStreaming(true);
        setStreamLoading(false);
        processingRef.current = true;
        pendingRef.current = false;
        lastFpsTimeRef.current = performance.now();
        frameCountRef.current = 0;
        reqIdRef.current = 0;
        rafRef.current = requestAnimationFrame(loop);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.success) {
          setStreamResultImage(data.image);
          const cnt = data.count || 0;
          if (cnt !== lastDetectionCountRef.current) {
            setDetectionCount(cnt);
            lastDetectionCountRef.current = cnt;
          }
        }
        pendingRef.current = false;
      };

      ws.onerror = () => {
        console.error("WebSocket error");
        stopStream();
      };

      ws.onclose = () => {
        pendingRef.current = false;
      };

    } catch (e) {
      console.error("Camera access failed:", e);
      alert("Kamera başlatılamadı. Lütfen kamera izinlerinizi kontrol edin.");
      setStreamLoading(false);
    }
  };

  const loop = useCallback(() => {
    if (!processingRef.current) return;

    const now = performance.now();
    const elapsed = now - lastFpsTimeRef.current;
    if (elapsed >= 1000) {
      setFps(Math.round((frameCountRef.current * 1000) / elapsed));
      frameCountRef.current = 0;
      lastFpsTimeRef.current = now;
    }

    if (!videoRef.current || !canvasRef.current || !wsRef.current) {
      rafRef.current = requestAnimationFrame(loop);
      return;
    }
    if (wsRef.current.readyState !== WebSocket.OPEN) {
      rafRef.current = requestAnimationFrame(loop);
      return;
    }
    if (pendingRef.current) {
      rafRef.current = requestAnimationFrame(loop);
      return;
    }

    const video = videoRef.current;
    if (video.readyState < 2) {
      rafRef.current = requestAnimationFrame(loop);
      return;
    }

    const canvas = canvasRef.current;
    const outW = 320;
    const outH = 240;
    if (canvas.width !== outW || canvas.height !== outH) {
      canvas.width = outW;
      canvas.height = outH;
    }

    const ctx = canvas.getContext("2d");
    if (!ctx) {
      rafRef.current = requestAnimationFrame(loop);
      return;
    }

    ctx.drawImage(video, 0, 0, outW, outH);

    const dataUrl = canvas.toDataURL("image/jpeg", 0.7);
    const base64Only = dataUrl.includes(",") ? dataUrl.split(",")[1] : dataUrl;
    reqIdRef.current += 1;

    pendingRef.current = true;
    wsRef.current.send(JSON.stringify({
      model_name: MODEL_NAME,
      task: "segment",
      image_b64: base64Only,
      req_id: reqIdRef.current,
    }));

    frameCountRef.current += 1;
    rafRef.current = requestAnimationFrame(loop);
  }, []);

  const stopStream = () => {
    processingRef.current = false;
    pendingRef.current = false;
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = 0;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) videoRef.current.srcObject = null;
    setStreaming(false);
    setStreamResultImage(null);
    setDetectionCount(0);
    setFps(0);
  };

  const toggleCamera = () => {
    const newMode = facingMode === "environment" ? "user" : "environment";
    setFacingMode(newMode);
    if (streaming) {
      stopStream();
      setTimeout(() => startStream(newMode), 300);
    }
  };

  return (
    <div className="page-enter max-w-6xl mx-auto px-4 md:px-6 py-8 md:py-12">
      {/* Hidden video/canvas for camera capture — must be outside conditionals */}
      <video ref={videoRef} playsInline muted className="hidden" />
      <canvas ref={canvasRef} className="hidden" />

      {/* Header */}
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#00d2ff] to-[#3a7bd5] flex items-center justify-center text-xl">
            🚗
          </div>
          <span className="text-xs font-semibold text-[#00d2ff] bg-[#00d2ff]/10 px-3 py-1 rounded-full">
            2. Ödev
          </span>
        </div>
        <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">
          Instance Segmentation — <span className="gradient-text">Car Damage</span>
        </h1>
        <p className="text-[#a0a0b5]">
          Araç hasar tespiti. <strong className="text-white">YOLO11l</strong> ve{" "}
          <strong className="text-white">RF-DETR</strong> modelleri denendi.
        </p>

        {/* Model comparison + active model */}
        <div className="mt-4 flex gap-4 flex-wrap">
          <div className="glass-card p-4 flex items-start gap-3 flex-1">
            <span className="text-2xl">📊</span>
            <div>
              <p className="text-sm text-white font-medium mb-1">Denenen Modeller</p>
              <div className="flex gap-2">
                <span className="text-xs bg-[#6c63ff]/15 text-[#6c63ff] px-3 py-1 rounded-full font-medium">YOLO11l</span>
                <span className="text-xs bg-[#00d2ff]/15 text-[#00d2ff] px-3 py-1 rounded-full font-medium">RF-DETR</span>
              </div>
            </div>
          </div>
          <div className="glass-card p-4 flex items-center gap-3 flex-1">
            <span className="text-2xl">🧠</span>
            <div>
              <p className="text-sm text-white font-medium">Aktif Model</p>
              <span className="text-xs bg-[#00d2ff]/15 text-[#00d2ff] px-3 py-1 rounded-full font-medium">
                CarModel.pt — Otomatik Yüklü ✓
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column */}
        <div className="space-y-6">
          {/* PDF Rapor */}
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">📄 PDF Rapor</h2>
            <Button
              className="w-full bg-[#00d2ff] text-black font-semibold"
              onPress={() => window.open("/pdfs/odev2.pdf", "_blank")}
            >
              📄 Raporu Görüntüle
            </Button>
          </div>
        </div>

        {/* Right Column — Test */}
        <div className="space-y-6">
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold text-white mb-4">🔍 Test Et</h2>

            {/* Tabs */}
            <div className="flex gap-2 mb-4">
              <button
                onClick={() => { setActiveTab("upload"); if (streaming) stopStream(); }}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === "upload" ? "bg-[#00d2ff] text-black" : "bg-white/5 text-[#a0a0b5] hover:text-white"
                  }`}
              >
                📷 Resim Yükle
              </button>
              <button
                onClick={() => { setActiveTab("camera"); if (!streaming) startStream(); }}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === "camera" ? "bg-[#00d2ff] text-black" : "bg-white/5 text-[#a0a0b5] hover:text-white"
                  }`}
              >
                📹 Canlı Kamera
              </button>
            </div>

            {activeTab === "upload" ? (
              <>
                <div
                  className={`upload-zone ${dragOver ? "drag-over" : ""}`}
                  onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={(e) => {
                    e.preventDefault();
                    setDragOver(false);
                    const f = e.dataTransfer.files[0];
                    if (f?.type.startsWith("image/")) handleImageSelect(f);
                  }}
                  onClick={() => document.getElementById("image-input-2")?.click()}
                >
                  <input
                    id="image-input-2"
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => e.target.files?.[0] && handleImageSelect(e.target.files[0])}
                  />
                  {imagePreview ? (
                    <img src={imagePreview} alt="preview" className="max-h-64 mx-auto rounded-lg" />
                  ) : (
                    <>
                      <div className="text-4xl mb-2">🖼️</div>
                      <p className="text-[#a0a0b5] text-sm">Hasarlı araç görselini sürükleyin veya tıklayın</p>
                    </>
                  )}
                </div>

                {imageFile && (
                  <Button
                    className="mt-4 w-full bg-gradient-to-r from-[#00d2ff] to-[#3a7bd5] text-white font-bold text-lg py-6"
                    onPress={runDetection}
                    isDisabled={loading}
                  >
                    {loading ? "Segmentasyon Çalışıyor..." : "🚀 Segmentasyonu Çalıştır"}
                  </Button>
                )}
              </>
            ) : (
              /* Camera Real-time Mode */
              <div>
                {!streaming ? (
                  <Button
                    className="w-full bg-gradient-to-r from-[#00d2ff] to-[#00ffc8] text-black font-semibold py-6 text-lg"
                    onPress={() => startStream()}
                    isDisabled={streamLoading}
                  >
                    {streamLoading ? "Başlatılıyor..." : "📹 Canlı Tespiti Başlat"}
                  </Button>
                ) : (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-green-400 live-pulse" />
                        <span className="text-green-400 font-semibold text-sm">CANLI</span>
                      </div>
                      <div className="flex gap-4">
                        <span className="text-[#00d2ff] font-mono text-sm">{fps} FPS</span>
                        <span className="text-[#00d2ff] font-mono text-sm">{detectionCount} hasar</span>
                      </div>
                    </div>

                    {/* Stream Display */}
                    <div className="stream-container relative overflow-hidden bg-black aspect-video flex items-center justify-center rounded-xl">
                      {streamResultImage ? (
                        <img
                          src={streamResultImage}
                          alt="Car Damage Real-time Segmentation"
                          className="w-full h-full object-contain"
                        />
                      ) : (
                        <video
                          ref={(el) => { if (el && videoRef.current) { el.srcObject = videoRef.current.srcObject; el.play().catch(() => {}); } }}
                          playsInline muted autoPlay
                          className="w-full h-full object-contain"
                        />
                      )}
                    </div>

                    <div className="flex flex-col gap-2">
                      <Button
                        className="w-full bg-red-500/20 text-red-400 font-semibold border border-red-500/30"
                        onPress={stopStream}
                      >
                        ⏹ Durdur
                      </Button>
                      <Button
                        className="w-full bg-[#2c2c3e] border border-white/10 text-white font-semibold"
                        onPress={toggleCamera}
                      >
                        🔄 {facingMode === "environment" ? "Ön Kameraya Geç" : "Arka Kameraya Geç"}
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Results (image mode only) */}
          {resultImage && (
            <div className="glass-card p-6">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                📊 Segmentasyon Sonuçları
                <span className="detection-badge">{detections.length} tespit</span>
              </h2>
              <img src={resultImage} alt="result" className="result-image w-full mb-4" />
              {detections.length > 0 && (
                <div className="space-y-2">
                  {detections.map((d, i) => (
                    <div key={i} className="flex items-center justify-between bg-white/5 rounded-lg px-4 py-2">
                      <span className="text-white text-sm font-medium">{d.class}</span>
                      <span className="text-[#00d2ff] text-sm font-mono">{(d.confidence * 100).toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              )}
              <Button
                className="mt-4 w-full bg-white/10 text-white font-semibold"
                onPress={() => {
                  setImageFile(null);
                  setImagePreview("");
                  setResultImage("");
                  setDetections([]);
                }}
              >
                🔄 Yeni Test Yap
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}