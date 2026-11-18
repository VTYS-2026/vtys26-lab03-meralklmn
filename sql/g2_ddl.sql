-- =====================================================
-- Föy 03 / Görev 2 — 3NF şema (altı tablo)
-- uyeler, telefonlar, egitmenler, salonlar, dersler, kayitlar
-- Birincil ve yabancı anahtarları föydeki tabloya göre tanımlayın.
-- Oluşturma sırasına dikkat!
-- =====================================================


-- 1. Bağımlı tablosu olmayan ana (parent) tablolar öncelikli olarak oluşturulur.

CREATE TABLE uyeler (
    uye_id INT PRIMARY KEY,
    ad VARCHAR(100)
);

CREATE TABLE egitmenler (
    egitmen_id SERIAL PRIMARY KEY,
    ad VARCHAR(100),
    brans VARCHAR(100)
);

CREATE TABLE salonlar (
    salon_id SERIAL PRIMARY KEY,
    ad VARCHAR(100),
    kapasite INT
);


-- 2. Yabancı anahtar (FK) içeren bağımlı (child) tablolar sırasıyla oluşturulur.

CREATE TABLE telefonlar (
    telefon_id SERIAL PRIMARY KEY,
    uye_id INT,
    numara VARCHAR(20),
    FOREIGN KEY (uye_id) REFERENCES uyeler(uye_id)
);

CREATE TABLE dersler (
    ders_id INT PRIMARY KEY,
    ad VARCHAR(100),
    egitmen_id INT,
    salon_id INT,
    ucret DECIMAL(10, 2),
    FOREIGN KEY (egitmen_id) REFERENCES egitmenler(egitmen_id),
    FOREIGN KEY (salon_id) REFERENCES salonlar(salon_id)
);

CREATE TABLE kayitlar (
    kayit_id SERIAL PRIMARY KEY,
    uye_id INT,
    ders_id INT,
    tarih DATE,
    FOREIGN KEY (uye_id) REFERENCES uyeler(uye_id),
    FOREIGN KEY (ders_id) REFERENCES dersler(ders_id)
);