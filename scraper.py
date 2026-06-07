from seleniumbase import SB
from bs4 import BeautifulSoup
import sqlite3
import time
import random
import os

# --- AYARLAR VE KLASÖR TANIMLAMALARI ---
# Projenin ana klasör yolunu alıyoruz (hangi klasörden çalıştırırsak çalıştıralım yollar bozulmasın diye).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Ekran görüntülerinin (screenshot) kaydedileceği alt klasörü tanımlıyoruz.
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")

# Eğer screenshots klasörü bilgisayarda henüz yoksa otomatik olarak oluşturuyoruz.
if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR)

# --- YARDIMCI OTOMASYON FONKSİYONLARI ---
def random_sleep(min_s, max_s):
    # Bot koruma sistemlerinin (Cloudflare vb.) bizi yapay zeka olarak algılamaması için,
    # iki işlem arasında insan davranışı gibi değişken/rastgele saniyelerle beklememizi sağlar.
    time.sleep(random.uniform(min_s, max_s))

def veritabanina_ekle(data):
    db_yolu = os.path.join(BASE_DIR, "emlak.db")
    # Eğer veritabanı dosyası yoksa, database.py modülünü çağırarak tabloları oluşturuyoruz.
    if not os.path.exists(db_yolu):
        import database
        database.init_db()

    conn = sqlite3.connect(db_yolu)
    cursor = conn.cursor()
    durum = False
    
    try:
        # SQL Injection yememek için parametrik sorgu (?) kullanıyoruz.
        # Böylece dışarıdan gelen veriler doğrudan kod gibi çalıştırılamaz, sadece veri olarak kaydedilir.
        cursor.execute("""
            INSERT INTO ilanlar (
                ilan_no, baslik, fiyat, link, resim_yolu, aciklama, lokasyon,
                ilan_tarihi, emlak_tipi, m2_brut, m2_net, oda_sayisi, bina_yasi,
                bulundugu_kat, kat_sayisi, isitma, banyo_sayisi, mutfak, balkon,
                asansor, otopark, esyali, kullanim_durumu, site_icerisinde, site_adi,
                aidat, krediye_uygun, tapu_durumu, kimden, takas
            ) 
            VALUES (
                ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?
            )
        """, (
            data["ilan_no"], data["baslik"], data["fiyat"], data["link"], data["resim_yolu"], data["aciklama"], data["lokasyon"],
            data["ilan_tarihi"],
            data["emlak_tipi"], data["m2_brut"], data["m2_net"], data["oda_sayisi"], data["bina_yasi"],
            data["bulundugu_kat"], data["kat_sayisi"], data["isitma"], data["banyo_sayisi"], data["mutfak"], data["balkon"],
            data["asansor"], data["otopark"], data["esyali"], data["kullanim_durumu"], data["site_icerisinde"], data["site_adi"],
            data["aidat"], data["krediye_uygun"], data["tapu_durumu"], data["kimden"], data["takas"]
        ))
        conn.commit() # Verileri dosyaya yazıp kaydediyoruz.
        print(f"💾 DB Kayıt Başarılı: {data['ilan_no']}")
        durum = True
    except sqlite3.IntegrityError:
        # Veritabanında ilan_no UNIQUE (benzersiz) olduğu için, aynı ilanı tekrar eklemeye çalıştığımızda
        # SQLite hata verir. Bu hatayı yakalayıp "zaten kayıtlı" diyerek programın çökmesini engelliyoruz.
        print(f"⏭️ Pas geçiliyor (Zaten var): {data['ilan_no']}")
        durum = False
    except Exception as e:
        print(f"❌ DB Yazma Hatası: {e}")
        durum = False
    finally:
        conn.close() # Her durumda veritabanı bağlantısını güvenle kapatıyoruz.
    
    return durum

def botu_calistir(hedef_link, limit=10):
    print(f"\n🚀 Bot başlatılıyor... Hedef: {hedef_link} (Limit: {limit})")
    
    # --- RAM BELLEK (CACHE) OPTİMİZASYONU ---
    # Tarama hızını artırmak için: Her ilan için veritabanına sorgu atmak yerine,
    # mevcut tüm ilan numaralarını başlangıçta RAM'e (Set yapısına) yüklüyoruz.
    # Python Set aramaları O(1) karmaşıklığında olduğundan, mükerrer ilan kontrolünü 100 kat hızlandırır.
    db_yolu = os.path.join(BASE_DIR, "emlak.db")
    mevcut_ilanlar = set()
    try:
        if os.path.exists(db_yolu):
            conn = sqlite3.connect(db_yolu)
            cursor = conn.cursor()
            cursor.execute("SELECT ilan_no FROM ilanlar")
            for sat in cursor.fetchall():
                mevcut_ilanlar.add(sat[0])
            conn.close()
    except Exception as e:
        print("DB okuma hatası:", e)

    toplam_yeni_ilan = 0
    su_anki_sayfa = 1
    # Sahibinden her sayfada 20 ilan listeler. Toplam limitimize ulaşmak için kaç sayfa gezmemiz gerektiğini hesaplıyoruz.
    MAX_SAYFA_LIMITI = (limit // 20) + 1 

    # Bot tespiti yememek için bilgisayarda yüklü olan orijinal Brave tarayıcısını kullanıyoruz.
    BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"

    try:
        # SeleniumBase (SB) kütüphanesini başlatıyoruz.
        # uc=True: Undetected ChromeDriver modunu açar (Cloudflare bot korumasını aşar).
        # test=True: Otomasyon izlerini gizleyen ek ayarları yükler.
        # ad_block_on=True: Reklamları engelleyerek sayfaların çok daha hızlı yüklenmesini sağlar.
        with SB(uc=True, test=True, ad_block_on=True, binary_location=BRAVE_PATH) as sb:
            try: 
                sb.maximize_window() # Tarayıcı penceresini tam ekran yapıyoruz.
            except: 
                pass

            while su_anki_sayfa <= MAX_SAYFA_LIMITI:
                
                # --- SAYFALAMA (PAGINATION) HESAPLAMA ---
                # 1. sayfadan sonraki sayfalara geçebilmek için Sahibinden'in kullandığı pagingOffset parametresini ekliyoruz.
                offset = (su_anki_sayfa - 1) * 20
                guncel_link = hedef_link
                if offset > 0:
                    # Linkin içinde halihazırda "?" parametre işareti varsa "&", yoksa "?" ile ekleme yapıyoruz.
                    if "?" in hedef_link:
                        guncel_link = f"{hedef_link}&pagingOffset={offset}"
                    else:
                        guncel_link = f"{hedef_link}?pagingOffset={offset}"

                print(f"\n📄 --- SAYFA {su_anki_sayfa} TARANIYOR --- (Offset: {offset})")
                
                sb.open(guncel_link) # Hedef arama sayfasını tarayıcıda açıyoruz.
                random_sleep(5, 7) # Sayfa içeriğinin tam yüklenmesi ve bot koruması için 5-7 saniye bekliyoruz.

                # Sayfanın kaynak kodunu (HTML) alıp BeautifulSoup ile analiz edilebilir hale getiriyoruz.
                soup = BeautifulSoup(sb.get_page_source(), "html.parser")
                main_table = soup.find("table", {"id": "searchResultsTable"})
                
                # Sitenin iki farklı arayüz şablonu (tablo veya div listesi) olabilir, ikisini de destekliyoruz:
                if not main_table:
                     satirlar = soup.find_all("div", {"class": "searchResultsItem"})
                     if not satirlar: 
                          print("❌ İlan listesi bulunamadı. (Bitti veya ban yendi)")
                          break
                else:
                     satirlar = main_table.find("tbody").find_all("tr")

                if len(satirlar) == 0: 
                    break

                for index, satir in enumerate(satirlar):
                    # Kullanıcının belirlediği maksimum ilan sayısına ulaştıysak döngüyü bitiriyoruz.
                    if toplam_yeni_ilan >= limit:
                        print(f"🛑 İstenen ilan limitine ({limit}) ulaşıldı.")
                        return f"✅ Tarama Bitti. {toplam_yeni_ilan} ilan kaydedildi."

                    # Araya giren reklam satırlarını pas geçiyoruz.
                    if "nativeAd" in satir.get("class", []) or "searchResultsPromoSuper" in satir.get("class", []):
                        continue
                    
                    try:
                        ilan_id = satir.get("data-id")
                        link_elem = satir.find("a", class_="classifiedTitle")
                        
                        # Eğer ilan ID'si doğrudan satırda yoksa, linkin içinden (klasik URL formatından) ayıklıyoruz.
                        if not ilan_id:
                             if link_elem and "-" in link_elem.get("href"):
                                 ilan_id = link_elem.get("href").split("-")[-1].replace("/detay", "")
                        
                        if not ilan_id or not link_elem: 
                            continue

                        # --- MÜKERRER KONTROLÜ (RAM BELLEK ÜZERİNDEN) ---
                        # İlan numarası set içinde varsa veritabanına sormadan doğrudan atlıyoruz (büyük performans kazancı).
                        if ilan_id in mevcut_ilanlar:
                            print(f"⏭️ Pas geçiliyor (Zaten var): {ilan_id}")
                            continue

                        # --- LİMİT / LOGIN DUVARI ÖNLEMİ ---
                        # Sahibinden, giriş yapmamış kullanıcılara arka arkaya çok istek atınca giriş zorunluluğu getirir.
                        # Bunu aşmak için her 5 ilanda bir tarayıcının tüm çerezlerini (cookies) temizliyoruz.
                        if index > 0 and index % 5 == 0:
                            sb.delete_all_cookies()
                            random_sleep(1, 2)

                        # --- İLAN DETAYINA GİRİŞ ---
                        raw_link = link_elem.get("href")
                        # Link göreceli yol ise başına alan adını ekliyoruz.
                        full_link = "https://www.sahibinden.com" + raw_link if raw_link.startswith("/") else raw_link
                        baslik = link_elem.text.strip()
                        
                        print(f"✨ İnceleniyor: {baslik}")
                        sb.open(full_link) # İlanın detay sayfasını yeni sekme/sayfa gibi açıyoruz.
                        random_sleep(4, 6) # Detay verilerinin ve resimlerin yüklenmesini bekliyoruz.

                        # Ekran görüntüsü klasörünü oluşturuyoruz (ilan ID'sine göre klasörleme).
                        ilan_klasoru = os.path.join(SCREENSHOT_DIR, ilan_id)
                        if not os.path.exists(ilan_klasoru): 
                            os.makedirs(ilan_klasoru)
                        
                        # 1. Ekran Görüntüsü: İlana ilk girildiği andaki kanıt görseli olarak kaydediyoruz.
                        sb.save_screenshot(os.path.join(ilan_klasoru, "1_giris.png"))
                        
                        detay_soup = BeautifulSoup(sb.get_page_source(), "html.parser")

                        # --- FİYAT VERİSİ TEMİZLEME ---
                        # Fiyat kısmındaki gereksiz boşlukları ve "Fiyat Tarihçesi" buton metnini temizliyoruz.
                        fiyat = "Fiyat Yok"
                        ham_fiyat = ""
                        fiyat_kutu = detay_soup.find("div", class_="classifiedInfo")
                        fiyat_container = detay_soup.find("div", class_="classified-price-container")
                        if fiyat_kutu and fiyat_kutu.find("h3"): 
                            ham_fiyat = fiyat_kutu.find("h3").text.strip()
                        elif fiyat_container: 
                            ham_fiyat = fiyat_container.text.strip()
                        if ham_fiyat:
                            temiz_fiyat = ham_fiyat.split("Fiyat Tarihçesi")[0].split("\n")[0]
                            fiyat = temiz_fiyat.strip()

                        # Açıklama metnini çekiyoruz ve formatlıyoruz.
                        aciklama_div = detay_soup.find("div", {"id": "classifiedDescription"})
                        aciklama_metni = aciklama_div.text.strip() if aciklama_div else "Açıklama bulunamadı."
                        formatli_aciklama = f"Açıklama: {aciklama_metni}"
                        
                        # Lokasyon bilgisini çekiyoruz (örn: "İstanbul / Kadıköy / Caferağa").
                        lokasyon = "Belirtilmemiş"
                        lokasyon_h2 = detay_soup.find("div", class_="classifiedInfo").find("h2")
                        if lokasyon_h2: 
                            lokasyon = lokasyon_h2.text.strip().replace("\n", "").replace("  ", "")

                        # --- DICTIONARY MAPPING (SÖZLÜK EŞLEŞTİRME) DESENİ ---
                        # Sitedeki Türkçe başlık etiketlerini veritabanı sütunlarıyla eşleştiriyoruz.
                        # Bu desen sayesinde if-else blokları kullanmadan O(1) sürede veri eşlemesi yapabiliyoruz.
                        özellik_haritası = {
                            "İlan No": "ilan_no",
                            "İlan Tarihi": "ilan_tarihi",
                            "Emlak Tipi": "emlak_tipi",
                            "m² (Brüt)": "m2_brut",
                            "m² (Net)": "m2_net",
                            "Oda Sayısı": "oda_sayisi",
                            "Bina Yaşı": "bina_yasi",
                            "Bulunduğu Kat": "bulundugu_kat",
                            "Kat Sayısı": "kat_sayisi",
                            "Isıtma": "isitma",
                            "Banyo Sayısı": "banyo_sayisi",
                            "Mutfak": "mutfak",
                            "Balkon": "balkon",
                            "Asansör": "asansor",
                            "Otopark": "otopark",
                            "Eşyalı": "esyali",
                            "Kullanım Durumu": "kullanim_durumu",
                            "Site İçerisinde": "site_icerisinde",
                            "Site Adı": "site_adi",
                            "Aidat (TL)": "aidat",
                            "Krediye Uygun": "krediye_uygun",
                            "Tapu Durumu": "tapu_durumu",
                            "Kimden": "kimden",
                            "Takas": "takas"
                        }
                        
                        # Veri paketini varsayılan değerlerle ("-") hazırla. 
                        # Eksik gelen veriler veritabanı kaydının çökmesine neden olmasın diye bu önlemi alıyoruz.
                        veri_paketi = {column: "-" for column in özellik_haritası.values()}
                        
                        # Temel bilgileri pakete ekliyoruz
                        veri_paketi["ilan_no"] = ilan_id
                        veri_paketi["baslik"] = baslik
                        veri_paketi["fiyat"] = fiyat
                        veri_paketi["link"] = full_link
                        veri_paketi["resim_yolu"] = f"{ilan_id}/1_giris.png"
                        veri_paketi["aciklama"] = formatli_aciklama
                        veri_paketi["lokasyon"] = lokasyon

                        # Sitedeki teknik özellik tablosunu (ul) bulup li etiketlerini dönüyoruz.
                        info_ul = detay_soup.find("ul", class_="classifiedInfoList")
                        if info_ul:
                            li_items = info_ul.find_all("li")
                            for li in li_items:
                                etiket = li.find("strong")
                                deger = li.find("span")
                                if etiket and deger:
                                    # Başlığın başındaki ve sonundaki boşlukları atıyoruz.
                                    etiket_adi = etiket.text.strip()
                                    
                                    # Eşleştirme sözlüğümüzde varsa, değerini ilgili veritabanı sütununa yazıyoruz.
                                    if etiket_adi in özellik_haritası:
                                        sütun_adi = özellik_haritası[etiket_adi]
                                        veri_paketi[sütun_adi] = deger.text.strip()

                        # Hazırladığımız veriyi veritabanına kaydediyoruz.
                        basarili = veritabanina_ekle(veri_paketi)
                        if basarili: 
                            toplam_yeni_ilan += 1
                            # RAM'deki mevcut ilanlar set'ini güncelliyoruz ki aynı taramada tekrar karşımıza çıkarsa atlayabilelim.
                            mevcut_ilanlar.add(ilan_id)
                        
                        random_sleep(2, 4) # Bir sonraki ilana geçmeden önce bot koruması için 2-4 saniye bekliyoruz.

                    except Exception as e:
                        print(f"❌ Satır hatası: {e}")
                        continue
                
                # Mevcut arama sayfasındaki tüm ilanlar bitince sonraki sayfaya geçiyoruz.
                su_anki_sayfa += 1
                sb.delete_all_cookies() # Sayfa geçişlerinde çerezleri temizleyerek ban riskini düşürüyoruz.
                random_sleep(3, 5)
            
            return f"✅ Tarama Tamamlandı. Toplam {toplam_yeni_ilan} yeni ilan kaydedildi."

    except Exception as genel_hata:
        print(f"🔥 KRİTİK HATA: {genel_hata}")
        return f"❌ Hata oluştu: {str(genel_hata)}"