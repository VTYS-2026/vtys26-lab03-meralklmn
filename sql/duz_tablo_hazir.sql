-- =====================================================
-- Föy 03 — Düz (kirli) tablonun kurulumu — HAZIR DOSYA
-- Bu dosyayı DEĞİŞTİRMEYİN; olduğu gibi çalıştırın:
--   docker exec -i vtys-postgres psql -U vtys -d vtysdb < sql/duz_tablo_hazir.sql
-- =====================================================
DROP TABLE IF EXISTS duz_kayitlar;

CREATE TABLE duz_kayitlar (
    uye_id          INTEGER,
    uye_ad          VARCHAR(100),
    uye_telefonlar  VARCHAR(200),
    ders_id         INTEGER,
    ders_ad         VARCHAR(100),
    ucret           INTEGER,
    egitmen_ad      VARCHAR(100),
    egitmen_brans   VARCHAR(50),
    salon_ad        VARCHAR(50),
    salon_kapasite  SMALLINT,
    tarih           DATE
);

COPY duz_kayitlar FROM '/veri/duzensiz_kayitlar.csv'
  WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
