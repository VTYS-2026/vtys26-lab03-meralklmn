# Föy 03 — Normalizasyon: Dağınık Veriden Güvenilir Şemaya

Modern Veritabanı Yönetim Sistemleri — Laboratuvar teslim deposu.
Görevlerin tam açıklaması **Föy 03 PDF**'indedir; bu dosya kısa bir hatırlatmadır.

## Senaryo

FıratFit'in eski üyelik sistemi tek bir Excel tablosuydu. Bu tabloyu
(`duzensiz_kayitlar`) devraldınız: telefonlar tek hücrede `;` ile ayrılmış,
eğitmen/salon bilgisi her satırda tekrarlanmış ve bazı derslerin ücreti
satırdan satıra tutarsız. Göreviniz: anomalileri sorgularla **kanıtlamak**,
sonra tabloyu **3NF'e ayrıştırıp** veriyi temiz şemaya taşımak.

## Hızlı başlangıç

```bash
echo "230541001" > ogrno.txt                  # kendi numaranız
docker compose up -d
python3 veri/uret.py 230541001                # kendi numaranız → kirli CSV
docker exec -i vtys-postgres psql -U vtys -d vtysdb < sql/duz_tablo_hazir.sql
docker exec -it vtys-postgres psql -U vtys -d vtysdb
```

## Depo yapısı

| Yol | Ne |
|---|---|
| `ogrno.txt` | Öğrenci numaranız (ilk iş: doldurun) |
| `sql/duz_tablo_hazir.sql` | Kirli tablonun kurulumu — HAZIR, değiştirmeyin |
| `sql/g1_anomali.sql` | Görev 1 — anomali kanıt sorguları |
| `sql/g2_ddl.sql` | Görev 2 — 3NF şema |
| `sql/g3_dolum.sql` | Görev 3 — veri taşıma |
| `sql/g4_kanit.sql` | Görev 4 — temiz şemanın kanıtı |
| `sonuc/` | Çıktılarınız ve AI köşesi teslimi |


## Push etmeden önce kendinizi kontrol edin

Değerlendiriciyi kendi bilgisayarınızda çalıştırabilirsiniz — GitHub'daki ile
**aynı dosya, aynı puan**:

```bash
docker compose run --rm kontrol
```

Ekrana görev görev puanınız ve eksikleriniz düşer. İlk çalıştırma birkaç
saniye sürer, sonrakiler ~2 saniye. Ayrıca bir şey kurmanız gerekmez; Docker
zaten kurulu.

**Önce burada tam puan alın, sonra push edin.** Her push GitHub'da sınıfın
ortak Actions kotasından dakika harcar; deneme-yanılmayı buraya taşırsanız
kota dönem sonuna kadar yeter.

## Teslim

```bash
git add ogrno.txt sql/ sonuc/
git commit -m "Foy 03 teslimi"
git push
```

Push sonrası **Actions** sekmesinden sonucu görün. Düzeltmeleri önce
`docker compose run --rm kontrol` ile yerelde doğrulayın, sonra push edin.
