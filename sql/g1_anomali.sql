-- =====================================================
-- Föy 03 / Görev 1 — Anomalileri sorguyla kanıtlayın
-- Her sorguyu ilgili "-- Soru 1.x" başlığının ALTINA yazın.
-- Başlık satırlarını silmeyin ve değiştirmeyin.
-- Kısa yorumunuzu sonuc/g1.txt dosyasına yazın.
-- =====================================================

-- ==========================================
-- GÖREV 1: Anomali Kanıtları ve Analizi
-- ==========================================

-- 1.1 Her eğitmen adının düz tabloda kaç satırda tekrar ettiğini listeleyin (Çoktan aza sıralı)
-- (Eğitmen sütununun adının 'egitmen_adi' veya 'egitmen' olduğunu varsayıyoruz)
SELECT egitmen_adi, COUNT(*) AS tekrar_sayisi
FROM ders_tablosu -- Tablo adınızı kendi veritabanınıza göre güncelleyebilirsiniz
GROUP BY egitmen_adi
ORDER BY tekrar_sayisi DESC;


-- 1.2 Birden fazla farklı ücreti görünen derslerin ders_id'lerini bulun
SELECT ders_id
FROM ders_tablosu
GROUP BY ders_id
HAVING COUNT(DISTINCT ucret) > 1;