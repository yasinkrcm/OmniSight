"""
API Views — ML Website Backend
================================
Handles file uploads, YOLO inference, and MJPEG video streaming.
"""

import os
import base64
import threading
from datetime import datetime, timezone
import cv2
import numpy as np
from pymongo import MongoClient
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from ultralytics import YOLO
import requests as http_requests

# MongoDB connection
mongo_client = MongoClient(settings.MONGO_URI)
db = mongo_client[settings.MONGO_DB_NAME]


# ═══════════════════════════════════════════════════════════════════════════
# Roboflow Serverless API Helper
# ═══════════════════════════════════════════════════════════════════════════


def roboflow_detect(frame, confidence=0.15):
    """Call Roboflow serverless API with a cv2 frame. Returns list of predictions."""
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    img_b64 = base64.b64encode(buffer.tobytes()).decode('utf-8')

    resp = http_requests.post(
        settings.ROBOFLOW_PPE_URL,
        params={'api_key': settings.ROBOFLOW_API_KEY, 'confidence': confidence},
        data=img_b64,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        timeout=10,
    )
    if resp.status_code == 200:
        data = resp.json()
        return data.get('predictions', [])
    return []





# ═══════════════════════════════════════════════════════════════════════════
# File Upload Views
# ═══════════════════════════════════════════════════════════════════════════

# Global model cache to avoid reloading models on every frame
_LOADED_MODELS = {}

def _preload_models():
    """Preload all YOLO models at startup for instant first-frame inference."""
    for name, path in settings.MODEL_PATHS.items():
        if os.path.exists(path) and path not in _LOADED_MODELS:
            print(f"[PRELOAD] Loading {name} model: {path}")
            _LOADED_MODELS[path] = YOLO(path)
            print(f"[PRELOAD] {name} model ready ✓")

_preload_models()

def _save_uploaded_file(uploaded_file, sub_dir):
    """Save an uploaded file and return its path."""
    upload_dir = os.path.join(settings.MEDIA_ROOT, sub_dir)
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, uploaded_file.name)
    with open(file_path, 'wb+') as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)
    return file_path


@csrf_exempt
def upload_pdf(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)
    pdf = request.FILES.get('pdf')
    odev = request.POST.get('odev', 'unknown')
    if not pdf:
        return JsonResponse({'error': 'No PDF file provided'}, status=400)
    path = _save_uploaded_file(pdf, 'pdfs')
    url = f'{settings.MEDIA_URL}pdfs/{pdf.name}'
    db.uploads.insert_one({
        'type': 'pdf', 'filename': pdf.name, 'odev': odev,
        'path': path, 'url': url, 'uploaded_at': datetime.now(timezone.utc),
    })
    return JsonResponse({'success': True, 'filename': pdf.name, 'url': url})


@csrf_exempt
def upload_model(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)
    model_file = request.FILES.get('model')
    odev = request.POST.get('odev', 'unknown')
    if not model_file:
        return JsonResponse({'error': 'No model file provided'}, status=400)
    path = _save_uploaded_file(model_file, 'models')
    db.uploads.insert_one({
        'type': 'model', 'filename': model_file.name, 'odev': odev,
        'path': path, 'uploaded_at': datetime.now(timezone.utc),
    })
    return JsonResponse({'success': True, 'filename': model_file.name, 'path': path})


# ═══════════════════════════════════════════════════════════════════════════
# Detection / Segmentation View (Fotoğraf yükleme modu)
# ═══════════════════════════════════════════════════════════════════════════

@csrf_exempt
def detect(request):
    """Run YOLO inference on uploaded image. Uses pre-configured model."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    model_name = request.POST.get('model_name')  # 'ppe', 'car_damage', or 'peoplecounter'
    image_file = request.FILES.get('image')
    image_b64 = request.POST.get('image_b64')
    task = request.POST.get('task', 'detect')

    if not model_name or (not image_file and not image_b64):
        return JsonResponse({'error': 'model_name and image are required'}, status=400)

    # Decode image
    if image_b64:
        if ',' in image_b64:
            image_b64 = image_b64.split(',')[1]
        file_bytes = np.frombuffer(base64.b64decode(image_b64), np.uint8)
    else:
        file_bytes = np.frombuffer(image_file.read(), np.uint8)

    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if image is None:
        return JsonResponse({'error': 'Invalid image file'}, status=400)

    detections = []
    has_masks = False

    if model_name == 'ppe':
        # ── Local YOLO PPE Model ──
        model_path = settings.MODEL_PATHS.get('ppe')
        if not model_path or not os.path.exists(model_path):
            return JsonResponse({'error': 'PPE model (ppe.pt) not found'}, status=404)

        if model_path not in _LOADED_MODELS:
            _LOADED_MODELS[model_path] = YOLO(model_path)
        model = _LOADED_MODELS[model_path]

        try:
            results = model.predict(source=image, conf=0.5, classes=[0,1,2,3,4,5,7], imgsz=320, half=False, verbose=False)
        except Exception:
            results = model.predict(source=image, conf=0.5, classes=[0,1,2,3,4,5,7], imgsz=320, verbose=False)
        annotated = results[0].plot(font_size=0, line_width=1)

        h, w = annotated.shape[:2]
        font_scale = max(min(w, h) / 400.0, 0.35)
        thickness = max(1, int(font_scale * 0.5))

        # Per-class color palette (BGR)
        class_colors = {
            'helmet': (0, 200, 255),    # sarı
            'head': (0, 165, 255),      # turuncu
            'person': (0, 255, 120),    # yeşil
            'vest': (180, 100, 0),      # mor
            'boot': (80, 60, 40),       # kahve
            'glove': (100, 150, 200),   # gri-mavi
            'safety glasses': (200, 200, 100), # hardal
            'mask': (150, 100, 200),   # pembe-mor
            'shield': (50, 200, 150),   # turkuaz
        }
        default_color = (0, 255, 120)  # yeşil

        if results[0].boxes:
            for box in results[0].boxes:
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                cls_name = model.names[cls_id]
                label = f"{cls_name} {conf:.0%}"
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                color = class_colors.get(cls_name.lower(), default_color)
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
                bg_y1 = max(y1 - th - 6, 0)
                cv2.rectangle(annotated, (x1, bg_y1), (x1 + tw + 6, y1), (30, 30, 30), -1)
                cv2.rectangle(annotated, (x1, bg_y1), (x1 + tw + 6, y1), color, 1)
                cv2.putText(annotated, label, (x1 + 3, y1 - 3),
                            cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA)
                detections.append({'class': cls_name, 'confidence': round(conf, 3)})

    elif task == 'segment':
        # ── Segmentation: car_damage ──
        model_path = settings.MODEL_PATHS.get(model_name)
        if not model_path or not os.path.exists(model_path):
            return JsonResponse({'error': f'Model "{model_name}" not found'}, status=404)

        if model_path not in _LOADED_MODELS:
            _LOADED_MODELS[model_path] = YOLO(model_path)
        model = _LOADED_MODELS[model_path]
        try:
            results = model.predict(source=image, conf=0.5, imgsz=320, half=False, verbose=False)
        except Exception:
            results = model.predict(source=image, conf=0.5, imgsz=320, verbose=False)

        annotated = results[0].plot(boxes=False, font_size=0, line_width=1)
        h, w = annotated.shape[:2]
        font_scale = max(min(w, h) / 400.0, 0.35)
        thickness = max(1, int(font_scale * 0.5))

        if results[0].boxes:
            for sonuc in results[0].boxes:
                skor = float(sonuc.conf[0]) if sonuc.conf is not None else 0.0
                sinif_id = int(sonuc.cls[0])
                sinif_adi = model.names[sinif_id]
                yazi = f"{sinif_adi} {skor:.0%}"
                x1, y1, x2, y2 = map(int, sonuc.xyxy[0])
                color = (0, 255, 120)
                (yazi_genislik, yazi_yukseklik), baseline = cv2.getTextSize(yazi, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
                y_yazi = max(y1, yazi_yukseklik + 6)
                cv2.rectangle(annotated,
                              (x1, y_yazi - yazi_yukseklik - 4),
                              (x1 + yazi_genislik, y_yazi + baseline - 2),
                              (30, 30, 30), -1)
                cv2.putText(annotated, yazi, (x1, y_yazi - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA)
                detections.append({'class': sinif_adi, 'confidence': round(skor, 3), 'has_mask': True})

        has_masks = results[0].masks is not None

    elif model_name == 'peoplecounter':
        # ── People Counter (YOLO26) ──
        model_path = settings.MODEL_PATHS.get('peoplecounter')
        if not model_path or not os.path.exists(model_path):
            return JsonResponse({'error': 'People counter model (yolo26n.pt) not found'}, status=404)
        if model_path not in _LOADED_MODELS:
            _LOADED_MODELS[model_path] = YOLO(model_path)
        model = _LOADED_MODELS[model_path]
        
        try:
            results = model(image, conf=0.45, imgsz=320, half=False, verbose=False)
        except Exception:
            results = model(image, conf=0.45, imgsz=320, verbose=False)
            
        annotated = image.copy()
        count = 0
        max_y = 0

        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                if int(box.cls[0]) != 0:
                    continue
                count += 1
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                max_y = max(max_y, y2)

                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 120), 1)

                label = f"Person {count}"
                h_img, w_img = annotated.shape[:2]
                fs = max(min(w_img, h_img) / 600.0, 0.35)
                th = max(1, int(fs * 0.5))
                (tw, th_box), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, fs, th)
                cv2.rectangle(annotated, (x1, y1 - th_box - 4), (x1 + tw + 4, y1), (30, 30, 30), -1)
                cv2.putText(annotated, label, (x1 + 2, y1 - 2),
                            cv2.FONT_HERSHEY_SIMPLEX, fs, (0, 255, 200), th, cv2.LINE_AA)

        # Toplam kişi sayısı - below the last detected person
        if count > 0:
            h, w = annotated.shape[:2]
            y_pos = min(max_y + 20, h - 10)
            label2 = f"Toplam: {count}"
            fs2 = max(min(w, h) / 500.0, 0.4)
            th2 = max(1, int(fs2 * 0.5))
            (tw2, th2_box), _ = cv2.getTextSize(label2, cv2.FONT_HERSHEY_SIMPLEX, fs2, th2)
            x_pos = w - tw2 - 10
            cv2.rectangle(annotated, (x_pos - 4, y_pos - th2_box - 2), (x_pos + tw2 + 4, y_pos + 2), (30, 30, 30), -1)
            cv2.putText(annotated, label2, (x_pos, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, fs2, (0, 255, 120), th2, cv2.LINE_AA)
        
        detections = [{'class': 'person'} for _ in range(count)]

    else:
        return JsonResponse({'error': 'Invalid model_name or task'}, status=400)

    # Encode result
    # Resize annotated image for faster transfer
    h, w = annotated.shape[:2]
    if w > 640:
        scale = 640 / w
        annotated = cv2.resize(annotated, (640, int(h * scale)), interpolation=cv2.INTER_LINEAR)
    ret, buffer = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 65])
    img_b64 = base64.b64encode(buffer.tobytes()).decode('utf-8')

    return JsonResponse({
        'success': True,
        'image': f'data:image/jpeg;base64,{img_b64}',
        'detections': detections,
        'count': len(detections),
        'task': task,
        'has_masks': has_masks,
    })



