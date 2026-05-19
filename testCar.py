import cv2
from ultralytics import YOLO

# Eğittiğin segmentasyon modelini yükle
model = YOLO("best.pt")

# Test resmi yolu
resim_yolu = "test.jpeg"
# 2. Tahmini yap (kutusuz)
results = model.predict(source=resim_yolu, conf=0.5, retina_masks=True)
cizimli_resim = results[0].plot(boxes=False)

# 3. Resmin boyutlarını al (Fontu orantılı yapmak için)
h, w, _ = cizimli_resim.shape
font_scale = max(w / 1200.0, 0.5)  # Resim ne kadar küçükse font da o kadar küçülecek (min 0.5)
kalinlik = max(1, int(font_scale * 2))

# 4. Profesyonel etiketi çiz
for sonuc in results[0].boxes:
    skor = float(sonuc.conf[0])
    sinif_id = int(sonuc.cls[0])
    sinif_adi = model.names[sinif_id]
    yazi = f"{sinif_adi} {skor:.2f}"
    
    x1, y1, x2, y2 = map(int, sonuc.xyxy[0])
    
    # Yazının tam kaplayacağı alanı (genişlik, yükseklik) hesapla
    (yazi_genislik, yazi_yukseklik), baseline = cv2.getTextSize(yazi, cv2.FONT_HERSHEY_SIMPLEX, font_scale, kalinlik)
    
    # Yazı ekranın üstünden taşmasın diye ufak bir güvenlik ayarı
    y_yazi = max(y1, yazi_yukseklik + 10)
    
    # Önce yazının arkasına estetik lacivert bir kutu çiz (Sadece yazı boyutu kadar!)
    cv2.rectangle(cizimli_resim, 
                  (x1, y_yazi - yazi_yukseklik - 8), 
                  (x1 + yazi_genislik, y_yazi + baseline - 3), 
                  (255, 50, 50), -1) # Renk: OpenCV'de (B,G,R) formatındadır
    
    # Şimdi o lacivert kutunun üstüne beyaz pürüzsüz yazıyı bas
    cv2.putText(cizimli_resim, yazi, (x1, y_yazi - 5), 
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), kalinlik)

# 5. Sonucu kaydet
kayit_yolu = "jilet_gibi_maske.jpg"
cv2.imwrite(kayit_yolu, cizimli_resim)

print(f"✅ İşlem tamam! Tabelacı fontu kovuldu, yerine dinamik etiket geldi: {kayit_yolu}")