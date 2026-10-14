#!/usr/bin/env python3
"""Föy 03 — Otomatik Değerlendirici

GitHub Actions içinde çalışır. Düz (kirli) tabloyu öğrencinin numarasından
yeniden üretip yükler; öğrencinin anomali sorgularını, 3NF şemasını ve veri
taşıma komutlarını bu KİŞİYE ÖZEL veriye karşı kontrol eder. Beklenen
değerler veri üretecinden Python ile hesaplanır; hazır SQL cevabı yoktur.
"""
import os
import re
import sys
from collections import Counter
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "veri"))
from uret import uret  # noqa: E402

try:
    import psycopg
except ImportError:
    print("HATA: psycopg kurulu değil (pip install 'psycopg[binary]').")
    sys.exit(2)

SONUCLAR = []


def kaydet(gorev, alinan, tam, mesaj):
    SONUCLAR.append((gorev, alinan, tam, mesaj))
    durum = "✓" if alinan == tam else ("~" if alinan > 0 else "✗")
    print(f"[{durum}] {gorev}: {alinan}/{tam} — {mesaj}")


def oku(yol):
    p = KOK / yol
    # is_file(): ogrenci bazen dosya yerine AYNI ADLA KLASOR olusturuyor
    # (ornegin "sonuc/g1.txt/g1.txt"). exists() bunu dosya sanip read_bytes()
    # ile cokuyor ve TUM degerlendirme sifirlaniyordu.
    if not p.is_file():
        return None
    try:
        ham = p.read_bytes()
    except OSError:
        return None
    # Windows'ta PowerShell'in ">" yonlendirmesi UTF-16 yazar; Not Defteri de
    # UTF-8'e BOM ekler. Bunlari cozmezsek ogrencinin dogru cikti dosyasi
    # taninmaz ve haksiz puan kaybi olur.
    if ham[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return ham.decode("utf-16", errors="replace")
    return ham.decode("utf-8-sig", errors="replace")

def sql_kodu(metin):
    """SQL metninden yorumlari atar.

    Sablon dosyalarinin KENDI yorumlarinda "CREATE TABLE komutunuzu yazin"
    gibi ifadeler gectigi icin, ham metinde anahtar kelime aramak bos teslimi
    gecerli sayiyordu. Denetimler bu fonksiyonun ciktisi uzerinde yapilir.
    """
    metin = re.sub(r"/\*.*?\*/", " ", metin or "", flags=re.S)
    return re.sub("--.*", " ", metin)


def baglanti():
    return psycopg.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=os.environ.get("PGPORT", "5432"),
        user=os.environ.get("PGUSER", "vtys"),
        password=os.environ.get("PGPASSWORD", "vtys2026"),
        dbname=os.environ.get("PGDATABASE", "vtysdb"),
        autocommit=True,
    )


def ogrno_al():
    icerik = oku("ogrno.txt")
    if icerik is None:
        return None
    icerik = icerik.strip()
    return icerik if icerik.isdigit() else None


def sorgulari_ayir(metin, on_ek):
    parcalar = re.split(rf"--\s*Soru\s*{on_ek}\.(\d)[^\n]*", metin or "")
    sorgular = {}
    for i in range(1, len(parcalar) - 1, 2):
        sorgular[int(parcalar[i])] = parcalar[i + 1].strip().rstrip(";")
    return sorgular


# ------------------------------------------------------------- düz tablo kurulumu
def duz_yukle(con, satirlar):
    con.execute("DROP TABLE IF EXISTS duz_kayitlar CASCADE")
    con.execute("""CREATE TABLE duz_kayitlar (
        uye_id INTEGER, uye_ad VARCHAR(100), uye_telefonlar VARCHAR(200),
        ders_id INTEGER, ders_ad VARCHAR(100), ucret INTEGER,
        egitmen_ad VARCHAR(100), egitmen_brans VARCHAR(50),
        salon_ad VARCHAR(50), salon_kapasite SMALLINT, tarih DATE)""")
    kolonlar = ["uye_id", "uye_ad", "uye_telefonlar", "ders_id", "ders_ad",
                "ucret", "egitmen_ad", "egitmen_brans", "salon_ad",
                "salon_kapasite", "tarih"]
    with con.cursor() as cur:
        with cur.copy(f"COPY duz_kayitlar ({', '.join(kolonlar)}) FROM STDIN") as cp:
            for s in satirlar:
                cp.write_row(tuple(s[k] for k in kolonlar))


# ------------------------------------------------------------- Görev 1: anomali
def kontrol_g1(con, veri):
    satirlar = veri["satirlar"]
    sorgular = sorgulari_ayir(oku("sql/g1_anomali.sql"), 1)
    puan = 0
    mesajlar = []

    beklenen11 = Counter(s["egitmen_ad"] for s in satirlar)
    q = sorgular.get(1)
    if not q:
        mesajlar.append("1.1: sorgu yok.")
    else:
        try:
            rows = con.execute(q).fetchall()
            sayilar = [r[-1] for r in rows]
            if (Counter({str(r[0]): r[-1] for r in rows}) == beklenen11
                    and sayilar == sorted(sayilar, reverse=True)):
                puan += 6
                mesajlar.append("1.1: doğru.")
            else:
                mesajlar.append("1.1: sonuç beklenenden farklı.")
        except Exception as e:
            mesajlar.append(f"1.1: sorgu hatası ({str(e).splitlines()[0]}).")

    ucretler = {}
    for s in satirlar:
        ucretler.setdefault(s["ders_id"], set()).add(s["ucret"])
    beklenen12 = Counter(d for d, u in ucretler.items() if len(u) > 1)
    q = sorgular.get(2)
    if not q:
        mesajlar.append("1.2: sorgu yok.")
    else:
        try:
            rows = con.execute(q).fetchall()
            if Counter(r[0] for r in rows) == beklenen12:
                puan += 6
                mesajlar.append("1.2: doğru — tutarsız dersleri buldunuz.")
            else:
                mesajlar.append("1.2: sonuç beklenenden farklı.")
        except Exception as e:
            mesajlar.append(f"1.2: sorgu hatası ({str(e).splitlines()[0]}).")

    yorum = oku("sonuc/g1.txt")
    if yorum and len(yorum.strip()) >= 150:
        puan += 3
        mesajlar.append("Yorum teslim edildi.")
    else:
        mesajlar.append("sonuc/g1.txt'deki yorum eksik ya da çok kısa.")

    kaydet("Görev 1 (Anomali)", puan, 15, " ".join(mesajlar))


# ------------------------------------------------------------- Görev 2: DDL
def kontrol_g2(con):
    sql = oku("sql/g2_ddl.sql")
    if not sql or "CREATE" not in sql_kodu(sql).upper():
        kaydet("Görev 2 (3NF DDL)", 0, 25, "sql/g2_ddl.sql bulunamadı veya CREATE içermiyor.")
        return False
    try:
        for t in ("kayitlar", "telefonlar", "dersler", "salonlar",
                  "egitmenler", "uyeler"):
            con.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
        con.execute(sql)
    except Exception as e:
        kaydet("Görev 2 (3NF DDL)", 0, 25, f"DDL çalıştırılamadı: {e}")
        return False

    puan = 0
    mesajlar = []
    tablolar = {r[0] for r in con.execute(
        """SELECT table_name FROM information_schema.tables
           WHERE table_schema='public' AND table_name <> 'duz_kayitlar'""")}
    gerekli = {"uyeler", "telefonlar", "egitmenler", "salonlar",
               "dersler", "kayitlar"}
    eksik = gerekli - tablolar
    if eksik:
        kaydet("Görev 2 (3NF DDL)", 4, 25,
               f"Eksik tablo(lar): {', '.join(sorted(eksik))}.")
        return False
    puan += 10

    pk_tablolari = {r[0] for r in con.execute(
        """SELECT table_name FROM information_schema.table_constraints
           WHERE constraint_type='PRIMARY KEY' AND table_schema='public'""")}
    if gerekli <= pk_tablolari:
        puan += 5
    else:
        mesajlar.append("Birincil anahtarı olmayan tablo(lar): "
                        f"{', '.join(sorted(gerekli - pk_tablolari))}.")

    fkler = {(r[0], r[1]) for r in con.execute(
        """SELECT tc.table_name, ccu.table_name
           FROM information_schema.table_constraints tc
           JOIN information_schema.constraint_column_usage ccu
             ON tc.constraint_name = ccu.constraint_name
           WHERE tc.constraint_type='FOREIGN KEY'""")}
    beklenen_fk = {("telefonlar", "uyeler"), ("dersler", "egitmenler"),
                   ("dersler", "salonlar"), ("kayitlar", "uyeler"),
                   ("kayitlar", "dersler")}
    dogru = beklenen_fk & fkler
    puan += len(dogru) * 2
    if len(dogru) < 5:
        eksik_fk = beklenen_fk - fkler
        mesajlar.append("Eksik yabancı anahtar(lar): " +
                        ", ".join(f"{a}→{b}" for a, b in sorted(eksik_fk)) + ".")
    else:
        mesajlar.append("Beş yabancı anahtar da doğru.")

    kaydet("Görev 2 (3NF DDL)", min(puan, 25), 25, " ".join(mesajlar))
    return True


# ------------------------------------------------------------- Görev 3: dolum
def kontrol_g3(con, veri):
    sql = oku("sql/g3_dolum.sql")
    if not sql or "INSERT" not in sql_kodu(sql).upper():
        kaydet("Görev 3 (Dolum)", 0, 30, "sql/g3_dolum.sql bulunamadı veya INSERT içermiyor.")
        return
    try:
        con.execute(sql)
    except Exception as e:
        kaydet("Görev 3 (Dolum)", 0, 30, f"Dolum çalıştırılamadı: {e}")
        return

    satirlar = veri["satirlar"]
    puan = 0
    mesajlar = []

    # beklenen içerikler (Python'dan)
    uyeler = {s["uye_id"]: s for s in satirlar}
    b_uye = len(uyeler)
    b_egitmen = len({s["egitmen_ad"] for s in satirlar})
    b_salon = len({s["salon_ad"] for s in satirlar})
    b_ders = len({s["ders_id"] for s in satirlar})
    b_kayit = len(satirlar)
    b_tel_dagilimi = Counter(len(u["uye_telefonlar"].split(";"))
                             for u in uyeler.values())

    sayimlar = {
        "uyeler": b_uye, "egitmenler": b_egitmen, "salonlar": b_salon,
        "dersler": b_ders, "kayitlar": b_kayit,
        "telefonlar": sum(k * v for k, v in b_tel_dagilimi.items()),
    }
    for tablo, beklenen in sayimlar.items():
        try:
            n = con.execute(f"SELECT COUNT(*) FROM {tablo}").fetchone()[0]
        except Exception:
            n = -1
        if n == beklenen:
            puan += 2
        else:
            mesajlar.append(f"{tablo}: satır sayısı beklenenden farklı.")

    # ders → eğitmen ve ders → salon eşleşmeleri
    b_ders_egitmen = Counter((s["ders_ad"], s["egitmen_ad"]) for s in
                             {x["ders_id"]: x for x in satirlar}.values())
    b_ders_salon = Counter((s["ders_ad"], s["salon_ad"]) for s in
                           {x["ders_id"]: x for x in satirlar}.values())
    try:
        rows = con.execute(
            """SELECT d.ad, e.ad FROM dersler d
               JOIN egitmenler e ON d.egitmen_id = e.egitmen_id""").fetchall()
        if Counter((str(a), str(b)) for a, b in rows) == b_ders_egitmen:
            puan += 3
        else:
            mesajlar.append("Ders–eğitmen eşleşmeleri beklenenden farklı.")
    except Exception:
        mesajlar.append("Ders–eğitmen eşleşmesi kontrol edilemedi (sütun adları?).")
    try:
        rows = con.execute(
            """SELECT d.ad, s.ad FROM dersler d
               JOIN salonlar s ON d.salon_id = s.salon_id""").fetchall()
        if Counter((str(a), str(b)) for a, b in rows) == b_ders_salon:
            puan += 3
        else:
            mesajlar.append("Ders–salon eşleşmeleri beklenenden farklı.")
    except Exception:
        mesajlar.append("Ders–salon eşleşmesi kontrol edilemedi (sütun adları?).")

    # ücret kuralı: her ders için en düşük ücret
    b_ucret = Counter((s["ders_ad"], veri["gercek_ucret"][s["ders_id"]])
                      for s in {x["ders_id"]: x for x in satirlar}.values())
    try:
        rows = con.execute("SELECT ad, ucret FROM dersler").fetchall()
        if Counter((str(a), int(b)) for a, b in rows) == b_ucret:
            puan += 6
            mesajlar.append("Ücret kuralı (en düşük) doğru uygulanmış.")
        else:
            mesajlar.append("dersler.ucret değerleri en-düşük-ücret kuralıyla uyuşmuyor.")
    except Exception:
        mesajlar.append("Ücret kontrol edilemedi.")

    # telefon dağılımı: üye başına numara sayıları
    try:
        rows = con.execute(
            "SELECT uye_id, COUNT(*) FROM telefonlar GROUP BY uye_id").fetchall()
        if Counter(r[1] for r in rows) == b_tel_dagilimi:
            puan += 6
            mesajlar.append("Telefonlar 1NF'e doğru ayrıştırılmış.")
        else:
            mesajlar.append("telefonlar tablosundaki numara dağılımı beklenenden farklı.")
    except Exception:
        mesajlar.append("Telefon dağılımı kontrol edilemedi.")

    kaydet("Görev 3 (Dolum)", min(puan, 30), 30, " ".join(mesajlar))


# ------------------------------------------------------------- Görev 4: kanıt
def kontrol_g4(con, veri):
    satirlar = veri["satirlar"]
    puan = 0
    mesajlar = []

    sorgular = sorgulari_ayir(oku("sql/g4_kanit.sql"), 4)
    q = sorgular.get(1)
    if not q:
        mesajlar.append("4.1: sorgu yok.")
    else:
        try:
            r = con.execute(q).fetchone()
            if r and len(r) >= 2 and int(r[0]) == int(r[1]) == len(satirlar):
                puan += 7
                mesajlar.append("4.1: doğru — veri kaybı yok.")
            else:
                mesajlar.append("4.1: iki sayı eşit ve sizin veri setinizle uyumlu değil.")
        except Exception as e:
            mesajlar.append(f"4.1: sorgu hatası ({str(e).splitlines()[0]}).")

    en_cok = Counter(s["egitmen_ad"] for s in satirlar).most_common(1)[0][1]
    icerik = oku("sonuc/g4.txt") or ""
    bozuk_var = re.search(rf"UPDATE {en_cok}\b", icerik)
    temiz_var = re.search(r"UPDATE 1\b", icerik)
    if bozuk_var and temiz_var:
        puan += 8
        mesajlar.append(f"4.2: doğru — düz tabloda {en_cok} satır, temiz şemada 1 satır.")
    elif icerik:
        mesajlar.append("4.2: sonuc/g4.txt'de beklenen iki 'UPDATE n' çıktısı bulunamadı "
                        "(en çok satırda geçen eğitmeni seçtiğinizden emin olun).")
    else:
        mesajlar.append("4.2: sonuc/g4.txt bulunamadı.")

    kaydet("Görev 4 (Kanıt)", puan, 15, " ".join(mesajlar))


def ogrenci_metni(markdown):
    """Markdown'dan kod bloklarini atip ogrencinin KENDI yazdigi metni birakir.

    Yapay zekanin urettigi SQL'i yapistirip tek satir elestiri yazmayan
    teslimler yalnizca uzunluga bakildiginda esigi gecip tam puan aliyordu
    (gercek teslimlerde tespit edildi). Puan artik duz metne gore verilir.
    """
    m = markdown or ""
    m = re.sub(r"```.*?```", " ", m, flags=re.S)
    m = re.sub(r"```.*", " ", m, flags=re.S)
    m = re.sub(r"^\s{4,}\S.*$", " ", m, flags=re.M)
    m = re.sub(r"`[^`]*`", " ", m)
    return re.sub(r"\s+", " ", m).strip()


def kontrol_ai():
    icerik = oku("sonuc/ai_elestiri.md")
    if not icerik or len(ogrenci_metni(icerik)) < 300:
        kaydet("AI Köşesi", 0, 10,
               "sonuc/ai_elestiri.md yok ya da eleştiri metniniz 300 karakterden kısa "
               "(yapıştırdığınız kod blokları sayılmaz). Föyde istenen iki "
               "somut eleştiriyi yazdığınızda bu uzunluk zaten aşılır "
               "(içerik ayrıca asistan tarafından okunur).")
    else:
        kaydet("AI Köşesi", 10, 10,
               "Dosya teslim edildi (isabet puanı asistan değerlendirmesiyle kesinleşir).")


# ------------------------------------------------------------- ana akış
def main():
    print("=" * 64)
    print("Föy 03 — Otomatik Değerlendirme")
    print("=" * 64)

    ogrno = ogrno_al()
    if not ogrno:
        print("HATA: ogrno.txt bulunamadı ya da geçerli bir numara içermiyor.")
        sys.exit(1)
    print(f"Öğrenci no: {ogrno} (veri seti bu numaradan yeniden üretiliyor)\n")

    veri = uret(ogrno)

    with baglanti() as con:
        duz_yukle(con, veri["satirlar"])
        kontrol_g1(con, veri)
        hazir = kontrol_g2(con)
        if hazir:
            kontrol_g3(con, veri)
            kontrol_g4(con, veri)
        else:
            kaydet("Görev 3 (Dolum)", 0, 30, "Şema hazır olmadığı için kontrol edilemedi.")
            kaydet("Görev 4 (Kanıt)", 0, 15, "Şema hazır olmadığı için kontrol edilemedi.")
    kontrol_ai()

    alinan = sum(s[1] for s in SONUCLAR)
    tam = sum(s[2] for s in SONUCLAR)
    print("\n" + "=" * 64)
    print(f"TOPLAM (otomatik kontrol edilen kısım): {alinan}/{tam}")
    print("Ön quiz (5p) bu rapora dahil değildir; AI köşesi asistan")
    print("tarafından ayrıca değerlendirilir.")
    print("=" * 64)

    ozet = os.environ.get("GITHUB_STEP_SUMMARY")
    if ozet:
        with open(ozet, "a", encoding="utf-8") as f:
            f.write("## Föy 03 — Otomatik Değerlendirme\n\n")
            f.write("| Bileşen | Puan | Açıklama |\n|---|---|---|\n")
            for gorev, a, tp, m in SONUCLAR:
                f.write(f"| {gorev} | {a}/{tp} | {m} |\n")
            f.write(f"| **Toplam** | **{alinan}/{tam}** | |\n")

    sys.exit(0 if alinan == tam else 1)


if __name__ == "__main__":
    main()
