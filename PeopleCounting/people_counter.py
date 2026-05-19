"""
People Counting with YOLO (Ultralytics)
========================================
Webcam (source 0) üzerinden gerçek zamanlı insan sayımı yapar.
YOLO modelini kullanarak kişileri tespit eder ve ekranda sayısını gösterir.

Kullanım:
    python people_counter.py

Çıkış: 'q' tuşuna basın.
"""

import cv2
import numpy as np
from ultralytics import YOLO


# ── Ayarlar ──────────────────────────────────────────────────────────────
MODEL_PATH = "yolo26n.pt"          # Ultralytics otomatik indirir (YOLO26)
CONFIDENCE_THRESHOLD = 0.45        # Minimum güven eşiği
PERSON_CLASS_ID = 0                # COCO veri setinde "person" sınıfı = 0
SOURCE = 0                         # Webcam

# Renk paleti
BOX_COLOR = (0, 255, 120)          # Yeşil kutu
TEXT_BG_COLOR = (30, 30, 30)       # Koyu arka plan
TEXT_COLOR = (0, 255, 200)         # Açık yeşil yazı
HEADER_COLOR = (50, 50, 50)       # Üst bant rengi


def draw_fancy_box(frame, x1, y1, x2, y2, conf, person_id):
    """Şık bounding box ve etiket çizer."""
    # Ana kutu
    cv2.rectangle(frame, (x1, y1), (x2, y2), BOX_COLOR, 2)

    # Köşe süslemeleri (corner accents)
    corner_len = 20
    thickness = 3
    # Sol üst
    cv2.line(frame, (x1, y1), (x1 + corner_len, y1), BOX_COLOR, thickness)
    cv2.line(frame, (x1, y1), (x1, y1 + corner_len), BOX_COLOR, thickness)
    # Sağ üst
    cv2.line(frame, (x2, y1), (x2 - corner_len, y1), BOX_COLOR, thickness)
    cv2.line(frame, (x2, y1), (x2, y1 + corner_len), BOX_COLOR, thickness)
    # Sol alt
    cv2.line(frame, (x1, y2), (x1 + corner_len, y2), BOX_COLOR, thickness)
    cv2.line(frame, (x1, y2), (x1, y2 - corner_len), BOX_COLOR, thickness)
    # Sağ alt
    cv2.line(frame, (x2, y2), (x2 - corner_len, y2), BOX_COLOR, thickness)
    cv2.line(frame, (x2, y2), (x2, y2 - corner_len), BOX_COLOR, thickness)

    # Etiket
    label = f"Kisi #{person_id}  {conf:.0%}"
    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    cv2.rectangle(frame, (x1, y1 - th - 10), (x1 + tw + 10, y1), TEXT_BG_COLOR, -1)
    cv2.putText(frame, label, (x1 + 5, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, TEXT_COLOR, 1, cv2.LINE_AA)


def draw_header(frame, count, fps):
    """Üst bilgi bandını çizer."""
    h, w = frame.shape[:2]
    header_h = 60

    # Yarı saydam üst bant
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, header_h), HEADER_COLOR, -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    # Başlık metni
    title = "PEOPLE COUNTER"
    cv2.putText(frame, title, (15, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

    # Sayaç
    count_text = f"Tespit Edilen Kisi: {count}"
    cv2.putText(frame, count_text, (15, 48),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, TEXT_COLOR, 2, cv2.LINE_AA)

    # FPS
    fps_text = f"FPS: {fps:.1f}"
    (fw, _), _ = cv2.getTextSize(fps_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    cv2.putText(frame, fps_text, (w - fw - 15, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)

    # Çıkış bilgisi
    quit_text = "Cikis: 'q'"
    (qw, _), _ = cv2.getTextSize(quit_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
    cv2.putText(frame, quit_text, (w - qw - 15, 48),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 150, 150), 1, cv2.LINE_AA)


def main():
    # ── Model yükle ──────────────────────────────────────────────────────
    print("[INFO] YOLO modeli yukleniyor...")
    model = YOLO(MODEL_PATH)
    print(f"[INFO] Model yuklendi: {MODEL_PATH}")

    # ── Kamera aç ────────────────────────────────────────────────────────
    print(f"[INFO] Kamera aciliyor (source={SOURCE})...")
    cap = cv2.VideoCapture(SOURCE)

    if not cap.isOpened():
        print("[HATA] Kamera acilamadi! Lutfen kamera baglantinizi kontrol edin.")
        return

    # Kamera çözünürlüğü
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("[INFO] Kamera hazir. Goruntu isleniyor...")
    print("[INFO] Cikmak icin 'q' tusuna basin.\n")

    # FPS hesaplama
    prev_time = cv2.getTickCount()
    fps = 0.0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[HATA] Kameradan goruntu alinamadi!")
            break

        # ── YOLO ile tespit ──────────────────────────────────────────────
        results = model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)

        # ── Sadece "person" sınıfını filtrele ────────────────────────────
        person_count = 0

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue

            for i, box in enumerate(boxes):
                cls_id = int(box.cls[0])
                if cls_id != PERSON_CLASS_ID:
                    continue

                person_count += 1
                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                draw_fancy_box(frame, x1, y1, x2, y2, conf, person_count)

        # ── FPS hesapla ──────────────────────────────────────────────────
        curr_time = cv2.getTickCount()
        time_diff = (curr_time - prev_time) / cv2.getTickFrequency()
        if time_diff > 0:
            fps = 1.0 / time_diff
        prev_time = curr_time

        # ── Üst bilgi bandı ──────────────────────────────────────────────
        draw_header(frame, person_count, fps)

        # ── Göster ───────────────────────────────────────────────────────
        cv2.imshow("People Counter - YOLO", frame)

        # Çıkış
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("\n[INFO] Cikis yapiliyor...")
            break

    # ── Temizlik ─────────────────────────────────────────────────────────
    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Program sonlandirildi.")


if __name__ == "__main__":
    main()
