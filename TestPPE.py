import cv2
from ultralytics import YOLO

# 1. Modeli yükle
model = YOLO("best (2).pt")
image_path = "ppe.jpg"

# 2. FİLTRE YOK! Modeli kendi haline bırakıyoruz.
# Normal bir PPE tespiti için conf=0.15 idealdir.
results = model.predict(
    source=image_path,
    conf=0.15,      # Barajı normale çektik
    imgsz=640,
    save=False      # Çizim işlemini biz kendimiz yapacağız
)

print("\n" + "="*50)
print("🎯 GERÇEK PPE TESPİTLERİ (Arka plan gürültüsü olmadan):")
print("="*50)

# Orijinal resmi OpenCV ile yükle (üzerine çizmek için)
img = cv2.imread(image_path)
hic_ppe_bulundu_mu = False

for result in results:
    for box in result.boxes:
        cls_id = int(box.cls[0])
        cls_name = model.names[cls_id]
        conf = float(box.conf[0])

        # 3. HAYAT KURTARAN DOKUNUŞ: Eğer model Person bulduysa, bunu YOKSAY ve çizme!
        if cls_name == "Person":
            continue

        # 4. Geriye kalanlar (Baret, Yelek, Bot) gerçekten PPE'dir.
        hic_ppe_bulundu_mu = True
        print(f"✅ [{cls_name}] bulundu! Güven: %{conf*100:.1f}")

        # PPE'nin etrafına Yeşil kutu çiz
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Etiketi ve skoru yaz
        label = f"{cls_name} {conf:.2f}"
        cv2.putText(img, label, (x1, max(15, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

if not hic_ppe_bulundu_mu:
    print("❌ Model %15 barajını geçen gerçek bir PPE bulamadı.")
    print("   Not: Bu fotoğraftaki yelek veya baret eğitim setindekilerden farklı olabilir.")

# Sonucu kaydet
kayit_yolu = "gercek_temiz_sonuc.jpg"
cv2.imwrite(kayit_yolu, img)
print("="*50)
print(f"📂 İşlem tamam! Temiz resim '{kayit_yolu}' olarak kaydedildi.")