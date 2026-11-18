-- =====================================================
-- Föy 03 / Görev 3 — Düz tablodan temiz şemaya veri taşıma
-- INSERT INTO ... SELECT (DISTINCT) ile doldurun.
-- Tutarsız ücretlerde kural: her ders için EN DÜŞÜK ücret esas alınır.
-- Telefonlar için string_to_array + unnest kullanın (bkz. föy).
-- =====================================================


-- 1. Ana Tabloların Doldurulması
INSERT INTO uyeler (uye_id, ad)
SELECT DISTINCT uye_id, uye_ad FROM duz_kayitlar;

INSERT INTO egitmenler (ad, brans)
SELECT DISTINCT egitmen_ad, egitmen_brans FROM duz_kayitlar;

INSERT INTO salonlar (ad, kapasite)
SELECT DISTINCT salon_ad, salon_kapasite FROM duz_kayitlar;

-- 2. Bağımlı Tabloların Doldurulması
INSERT INTO telefonlar (uye_id, numara)
SELECT DISTINCT u.uye_id, t.numara
FROM (SELECT DISTINCT uye_id, uye_telefonlar FROM duz_kayitlar) dt
JOIN uyeler u ON dt.uye_id = u.uye_id
CROSS LATERAL unnest(string_to_array(dt.uye_telefonlar, ';')) AS t(numara);

INSERT INTO dersler (ders_id, ad, egitmen_id, salon_id, ucret)
SELECT 
    dt.ders_id,
    MAX(dt.ders_ad) AS ad,
    e.egitmen_id,
    s.salon_id,
    MIN(dt.ucret) AS ucret
FROM duz_kayitlar dt
JOIN egitmenler e ON dt.egitmen_ad = e.ad
JOIN salonlar s ON dt.salon_ad = s.ad
GROUP BY dt.ders_id, e.egitmen_id, s.salon_id;

INSERT INTO kayitlar (uye_id, ders_id, tarih)
SELECT DISTINCT uye_id, ders_id, kayit_tarih FROM duz_kayitlar;