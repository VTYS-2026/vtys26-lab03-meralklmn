-- =====================================================
-- Föy 03 / Görev 4 — Temiz şemanın kanıtı
-- Soru 4.1'i buraya yazın; 4.2'nin UPDATE çıktılarının
-- tamamını sonuc/g4.txt dosyasına yapıştırın.
-- =====================================================



-- 4.1 Tek sorguda düz tablo ve kayıtlar tablosunun satır sayılarını döndürme (Veri kaybı kontrolü)
SELECT 
    (SELECT COUNT(*) FROM duz_kayitlar) AS duz_tablo_satir_sayisi,
    (SELECT COUNT(*) FROM kayitlar) AS temiz_kayitlar_satir_sayisi;


-- 4.2 Güncelleme anomalisinin ve normalizasyon kazancının kanıtı
-- (Önce Görev 1.1'de en çok tekrar eden örnek bir eğitmen adını seçip güncelleme yapıyoruz)

-- 1. Aşama: Düz tabloda güncelleme (Yüzlerce satırı etkiler / Güncelleme anomalisi riski)
UPDATE duz_kayitlar 
SET egitmen_ad = 'Ahmet Hoca (Güncellendi)' 
WHERE egitmen_ad = 'Önceki Eğitmen Adı'; -- Kendi tablonuzdaki en çok geçen eğitmen adını buraya yazabilirsiniz

-- 2. Aşama: Temiz şemadaki egitmenler tablosunda güncelleme (Yalnızca tek bir satırı etkiler)
UPDATE egitmenler 
SET ad = 'Ahmet Hoca (Güncellendi)' 
WHERE ad = 'Önceki Eğitmen Adı';