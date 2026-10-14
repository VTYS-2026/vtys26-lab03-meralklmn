#!/usr/bin/env python3
"""Kişiye özel veri üreteci — Föy 03 (FıratFit'in eski sistemi)

Kullanım:
    python3 veri/uret.py <ogrenci_no>

Tek CSV üretir: duzensiz_kayitlar.csv — eski sistemden devralınmış,
BİLEREK kirli bir "Excel tablosu":
  * uye_telefonlar sütununda ';' ile ayrılmış birden çok numara (1NF ihlali)
  * eğitmen ve salon bilgisi her satırda tekrar (3NF ihlali)
  * bazı derslerin ücreti satırdan satıra tutarsız (güncelleme anomalisinin izi)

Aynı öğrenci numarası her çalıştırmada AYNI veri setini üretir.
"""
import csv
import random
import sys
from pathlib import Path

ADLAR = ["Ahmet", "Ayşe", "Mehmet", "Elif", "Mustafa", "Zeynep", "Ali",
         "Fatma", "Hasan", "Emine", "Murat", "Hülya", "Kemal", "Nazlı",
         "Selim", "Leyla", "Orhan", "Sevgi", "Yakup", "Melek", "Deniz",
         "Ece", "Burak", "Ceren", "Tolga", "İpek", "Serkan", "Gül"]

SOYADLAR = ["Yılmaz", "Kaya", "Demir", "Çelik", "Şahin", "Yıldız", "Aydın",
            "Arslan", "Doğan", "Kılıç", "Aslan", "Çetin", "Koç", "Kurt",
            "Özdemir", "Erdoğan", "Polat", "Güneş", "Taş", "Bulut"]

BRANSLAR = ["Fitness", "Yoga", "Pilates", "Yüzme", "Boks", "Crossfit"]

DERS_TEMEL = ["Sabah Yogası", "Fonksiyonel Antrenman", "Yüzme Teknikleri",
              "Pilates Matwork", "Boks Temelleri", "Crossfit WOD",
              "Core Güçlendirme", "Esneklik ve Denge", "Kardiyo Dayanıklılık",
              "Kuvvet Antrenmanı", "Hamile Yogası", "Kıdemli Fitness",
              "Gençlik Yüzme", "İleri Pilates", "Kickboks"]

SEVIYELER = ["Başlangıç", "Orta", "İleri"]

SALON_ADLARI = ["Ana Salon", "Stüdyo A", "Stüdyo B", "Havuz",
                "Dövüş Salonu", "Açık Alan", "Spinning Odası"]

UCRETLER = [300, 400, 450, 500, 600]


def uret(ogrno: str):
    """Öğrenci numarasından deterministik düz (kirli) tablo üretir.

    Dönen sözlük:
      satirlar    : duzensiz_kayitlar.csv satırları
      tutarsizlar : ücreti bilerek bozulan ders_id kümesi
      gercek_ucret: ders_id -> doğru (en düşük) ücret
    """
    tohum = int(ogrno)
    rnd = random.Random(tohum)

    # --- salonlar (5–7) ---
    salon_sayisi = 5 + tohum % 3
    salonlar = []
    for ad in SALON_ADLARI[:salon_sayisi]:
        salonlar.append({"ad": ad, "kapasite": rnd.choice([15, 20, 25, 30, 40])})

    # --- eğitmenler (8–12) ---
    egitmen_sayisi = 8 + tohum % 5
    egitmen_adlari = set()
    egitmenler = []
    for _ in range(egitmen_sayisi):
        while True:
            ad = f"{rnd.choice(ADLAR)} {rnd.choice(SOYADLAR)}"
            if ad not in egitmen_adlari:
                egitmen_adlari.add(ad)
                break
        egitmenler.append({"ad": ad, "brans": rnd.choice(BRANSLAR)})

    # --- dersler (24–32); her ders: eğitmen, salon, ücret ---
    ders_sayisi = 24 + tohum % 9
    ders_adlari = set()
    dersler = []
    for did in range(1, ders_sayisi + 1):
        while True:
            ad = f"{rnd.choice(DERS_TEMEL)} — {rnd.choice(SEVIYELER)}"
            if ad not in ders_adlari:
                ders_adlari.add(ad)
                break
        dersler.append({
            "ders_id": did,
            "ad": ad,
            "egitmen": rnd.choice(egitmenler),
            "salon": rnd.choice(salonlar),
            "ucret": rnd.choice(UCRETLER),
        })

    # --- üyeler (150–200); her üyenin 1–3 telefonu ---
    uye_sayisi = 150 + tohum % 51
    uyeler = []
    for uid in range(1, uye_sayisi + 1):
        tel_sayisi = rnd.randint(1, 3)
        teller = []
        for _ in range(tel_sayisi):
            teller.append(f"05{rnd.randint(30, 55)}-{rnd.randint(100, 999)}-"
                          f"{rnd.randint(1000, 9999)}")
        uyeler.append({
            "uye_id": uid,
            "ad": f"{rnd.choice(ADLAR)} {rnd.choice(SOYADLAR)}",
            "telefonlar": ";".join(teller),
        })

    # --- kayıtlar: önce her derse 1 kayıt (hiçbir ders boş kalmasın),
    #     sonra 300–400'e tamamla ---
    kayit_hedefi = 300 + tohum % 101
    ikili_kume = set()
    kayit_listesi = []
    for d in dersler:
        uye = rnd.randint(1, uye_sayisi)
        ikili_kume.add((uye, d["ders_id"]))
        kayit_listesi.append((uye, d["ders_id"]))
    while len(kayit_listesi) < kayit_hedefi:
        uye = rnd.randint(1, uye_sayisi)
        ders = rnd.randint(1, ders_sayisi)
        if (uye, ders) in ikili_kume:
            continue
        ikili_kume.add((uye, ders))
        kayit_listesi.append((uye, ders))

    # --- tutarsız ücret enjeksiyonu: 3–6 ders, bazı satırlarda ucret+50 ---
    tutarsiz_sayisi = 3 + tohum % 4
    tutarsizlar = set(rnd.sample(range(1, ders_sayisi + 1), tutarsiz_sayisi))

    ders_map = {d["ders_id"]: d for d in dersler}
    uye_map = {u["uye_id"]: u for u in uyeler}
    bozuk_sayaci = {d: 0 for d in tutarsizlar}

    satirlar = []
    for uye_id, ders_id in kayit_listesi:
        d = ders_map[ders_id]
        u = uye_map[uye_id]
        ucret = d["ucret"]
        if ders_id in tutarsizlar and rnd.random() < 0.4:
            ucret = d["ucret"] + 50
            bozuk_sayaci[ders_id] += 1
        ay, gun = rnd.randint(1, 12), rnd.randint(1, 28)
        satirlar.append({
            "uye_id": uye_id,
            "uye_ad": u["ad"],
            "uye_telefonlar": u["telefonlar"],
            "ders_id": ders_id,
            "ders_ad": d["ad"],
            "ucret": ucret,
            "egitmen_ad": d["egitmen"]["ad"],
            "egitmen_brans": d["egitmen"]["brans"],
            "salon_ad": d["salon"]["ad"],
            "salon_kapasite": d["salon"]["kapasite"],
            "tarih": f"2026-{ay:02d}-{gun:02d}",
        })

    # Enjeksiyon şansa bağlı hiç satır bozmadıysa bir satırı elle boz.
    for ders_id, adet in bozuk_sayaci.items():
        if adet == 0:
            for s in satirlar:
                if s["ders_id"] == ders_id:
                    s["ucret"] = ders_map[ders_id]["ucret"] + 50
                    break

    return {
        "satirlar": satirlar,
        "tutarsizlar": tutarsizlar,
        "gercek_ucret": {d["ders_id"]: d["ucret"] for d in dersler},
    }


def main():
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        print("Kullanım: python3 veri/uret.py <ogrenci_no>")
        print("Örnek   : python3 veri/uret.py 230541001")
        sys.exit(1)

    ogrno = sys.argv[1]
    hedef = Path(__file__).resolve().parent / "duzensiz_kayitlar.csv"
    sonuc = uret(ogrno)
    satirlar = sonuc["satirlar"]

    with open(hedef, "w", newline="", encoding="utf-8") as f:
        yazici = csv.DictWriter(f, fieldnames=list(satirlar[0].keys()))
        yazici.writeheader()
        yazici.writerows(satirlar)

    print(f"Üretildi: {hedef.name} ({len(satirlar)} satır)")
    print("Bu 'Excel artığı' tablo bilerek kirlidir: tekrarlar, çok değerli")
    print("telefon sütunu ve tutarsız ücretler içerir. Temizlemek sizin işiniz.")


if __name__ == "__main__":
    main()
