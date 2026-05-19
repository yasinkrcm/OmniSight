"""
WebSocket Consumer for Real-time YOLO Detection
=================================================
Async consumer — non-blocking inference per connection.
"""

import json
import base64
import asyncio
import time
import cv2
import numpy as np
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from ultralytics import YOLO

# Reuse the global model cache from views
from api.views import _LOADED_MODELS


def _run_inference(model, image, model_name):
    """Run YOLO inference synchronously — called in thread pool."""
    t0 = time.perf_counter()
    detections = []
    annotated = None

    h, w = image.shape[:2]

    if model_name == 'ppe':
        try:
            results = model.predict(source=image, conf=0.5, classes=[0,1,2,3,4,5,7], imgsz=320, half=False, verbose=False)
        except Exception:
            results = model.predict(source=image, conf=0.5, classes=[0,1,2,3,4,5,7], imgsz=320, verbose=False)
        annotated = results[0].plot(font_size=0, line_width=1)

        h, w = annotated.shape[:2]
        font_scale = max(min(w, h) / 400.0, 0.35)
        thickness = max(1, int(font_scale * 0.5))

        class_colors = {
            'helmet': (0, 200, 255),
            'head': (0, 165, 255),
            'person': (0, 255, 120),
            'vest': (180, 100, 0),
            'boot': (80, 60, 40),
            'glove': (100, 150, 200),
            'safety glasses': (200, 200, 100),
            'mask': (150, 100, 200),
            'shield': (50, 200, 150),
        }
        default_color = (0, 255, 120)

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

    elif model_name == 'car_damage':
        try:
            results = model.predict(source=image, conf=0.5, imgsz=320, half=False, verbose=False)
        except Exception:
            results = model.predict(source=image, conf=0.5, imgsz=320, verbose=False)

        # Use YOLO's built-in plot with masks
        annotated = results[0].plot(boxes=False, font_size=0, line_width=1)
        h, w = annotated.shape[:2]
        font_scale = max(min(w, h) / 400.0, 0.35)
        thickness = max(1, int(font_scale * 0.5))

        if results[0].boxes:
            for box in results[0].boxes:
                conf = float(box.conf[0]) if box.conf is not None else 0.0
                cls_id = int(box.cls[0])
                cls_name = model.names[cls_id]
                label = f"{cls_name} {conf:.0%}"
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                color = (0, 255, 120)
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
                bg_y1 = max(y1 - th - 4, 0)
                cv2.rectangle(annotated, (x1, bg_y1), (x1 + tw + 4, y1), (30, 30, 30), -1)
                cv2.putText(annotated, label, (x1 + 2, y1 - 2),
                            cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA)
                detections.append({'class': cls_name, 'confidence': round(conf, 3)})

    elif model_name == 'peoplecounter':
        try:
            results = model(image, conf=0.45, imgsz=320, half=False, verbose=False)
        except Exception:
            results = model(image, conf=0.45, imgsz=320, verbose=False)

        annotated = image.copy()
        count = 0
        h_img, w_img = image.shape[:2]
        fs = max(min(w_img, h_img) / 600.0, 0.35)
        th_box = max(1, int(fs * 0.5))
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                if int(box.cls[0]) != 0:
                    continue
                count += 1
                conf = float(box.conf[0]) if box.conf is not None else 0.0
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 120), 1)
                label = f"Person {count}"
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, fs, th_box)
                bg_y1 = max(y1 - th - 4, 0)
                cv2.rectangle(annotated, (x1, bg_y1), (x1 + tw + 4, y1), (30, 30, 30), -1)
                cv2.putText(annotated, label, (x1 + 2, y1 - 2),
                            cv2.FONT_HERSHEY_SIMPLEX, fs, (0, 255, 200), th_box, cv2.LINE_AA)

        detections = [{'class': 'person'} for _ in range(count)]

    else:
        return None, [], None

    elapsed = (time.perf_counter() - t0) * 1000

    if annotated is not None:
        out_h, out_w = annotated.shape[:2]
        if out_w > 640:
            scale = 640 / out_w
            annotated = cv2.resize(annotated, (640, int(out_h * scale)), interpolation=cv2.INTER_LINEAR)
        ret, buffer = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 65])
        img_b64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
    else:
        img_b64 = None

    return img_b64, detections, len(detections)


class DetectConsumer(AsyncWebsocketConsumer):
    """Async WebSocket consumer for YOLO inference."""

    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        model_name = data.get('model_name', '')
        image_b64 = data.get('image_b64', '')
        req_id = data.get('req_id', 0)

        if not model_name or not image_b64:
            return

        # Decode image in thread
        def decode_image():
            try:
                if ',' in image_b64:
                    b64 = image_b64.split(',')[1]
                else:
                    b64 = image_b64
                file_bytes = np.frombuffer(base64.b64decode(b64), np.uint8)
                return cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            except Exception:
                return None

        image = await asyncio.to_thread(decode_image)
        if image is None:
            return

        # Get or create model
        model_path = settings.MODEL_PATHS.get(model_name)
        if not model_path:
            return

        model = _LOADED_MODELS.get(model_path)
        if not model:
            model = YOLO(model_path)
            _LOADED_MODELS[model_path] = model

        # Run inference in thread pool (never blocks event loop)
        img_b64, detections, count = await asyncio.to_thread(
            _run_inference, model, image, model_name
        )

        if img_b64 is None:
            return

        await self.send(text_data=json.dumps({
            'success': True,
            'image': f'data:image/jpeg;base64,{img_b64}',
            'detections': detections,
            'count': count,
            'req_id': req_id,
        }))