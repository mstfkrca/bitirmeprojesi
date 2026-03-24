from seleniumbase import SB
from bs4 import BeautifulSoup
import sqlite3
import time
import random
import os

# --- AYARLAR ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")

if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR)

# --- YARDIMCI FONKSİYONLAR ---
def random_sleep(min_s, max_s):
    time.sleep(random.uniform(min_s, max_s))

def veritabanina_ekle(data):
    db_yolu = os.path.join(BASE_DIR, "emlak.db")
    # Veritabanı yoksa oluştur (database.py'yi çağırır)
    if not os.path.exists(db_yolu):
        import database
        database.init_db()

    conn = sqlite3.connect(db_yolu)
    cursor = conn.cursor()
    durum = False
    
    try:
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
            
            # --- YENİ VERİ: İlan Tarihi ---
            data["ilan_tarihi"],
            # -------------------------------
            
            data["emlak_tipi"], data["m2_brut"], data["m2_net"], data["oda_sayisi"], data["bina_yasi"],
            data["bulundugu_kat"], data["kat_sayisi"], data["isitma"], data["banyo_sayisi"], data["mutfak"], data["balkon"],
            data["asansor"], data["otopark"], data["esyali"], data["kullanim_durumu"], data["site_icerisinde"], data["site_adi"],
            data["aidat"], data["krediye_uygun"], data["tapu_durumu"], data["kimden"], data["takas"]
        ))
        conn.commit()
        print(f"💾 DB Kayıt Başarılı: {data['ilan_no']}")
        durum = True
    except sqlite3.IntegrityError:
        print(f"⏭️ Pas geçiliyor (Zaten var): {data['ilan_no']}")
        durum = False
    except Exception as e:
        print(f"❌ DB Yazma Hatası: {e}")
        durum = False
    finally:
        conn.close()
    
    return durum

def botu_calistir(hedef_link, limit=10):
    print(f"\n🚀 Bot başlatılıyor... Hedef: {hedef_link} (Limit: {limit})")
    
    # Hızlandırma: Veritabanındaki tüm ilan ID'leri RAM'e (Set) alınıyor.
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
    # Sayfalama desteği (Senin attığın scrapper.py'den URL tabanlı sayfalama eklendi)
    su_anki_sayfa = 1
    MAX_SAYFA_LIMITI = (limit // 20) + 1 # 100 ilan varsa 5-6 sayfa gezer

    BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"

    try:
        # Sende sadece Brave olduğu için Brave dizinini geri tanımladık.
        with SB(uc=True, test=True, ad_block_on=True, binary_location=BRAVE_PATH) as sb:
            try: sb.maximize_window()
            except: pass

            while su_anki_sayfa <= MAX_SAYFA_LIMITI:
                
                # URL'ye pagingOffset ekleme (1. sayfa hariç)
                offset = (su_anki_sayfa - 1) * 20
                guncel_link = hedef_link
                if offset > 0:
                    if "?" in hedef_link:
                        guncel_link = f"{hedef_link}&pagingOffset={offset}"
                    else:
                        guncel_link = f"{hedef_link}?pagingOffset={offset}"

                print(f"\n📄 --- SAYFA {su_anki_sayfa} TARANIYOR --- (Offset: {offset})")
                
                sb.open(guncel_link)
                random_sleep(5, 7)

                soup = BeautifulSoup(sb.get_page_source(), "html.parser")
                main_table = soup.find("table", {"id": "searchResultsTable"})
                
                if not main_table:
                     satirlar = soup.find_all("div", {"class": "searchResultsItem"})
                     if not satirlar: 
                         print("❌ İlan listesi bulunamadı. (Bitti veya ban yendi)")
                         break
                else:
                     satirlar = main_table.find("tbody").find_all("tr")

                if len(satirlar) == 0: break

                for index, satir in enumerate(satirlar):
                    # Toplam limit kontrolü
                    if toplam_yeni_ilan >= limit:
                        print(f"🛑 İstenen ilan limitine ({limit}) ulaşıldı.")
                        return f"✅ Tarama Bitti. {toplam_yeni_ilan} ilan kaydedildi."

                    if "nativeAd" in satir.get("class", []) or "searchResultsPromoSuper" in satir.get("class", []):
                        continue
                    
                    try:
                        ilan_id = satir.get("data-id")
                        link_elem = satir.find("a", class_="classifiedTitle")
                        
                        if not ilan_id:
                             if link_elem and "-" in link_elem.get("href"):
                                 ilan_id = link_elem.get("href").split("-")[-1].replace("/detay", "")
                        
                        if not ilan_id or not link_elem: continue

                        # DB Kontrolü (Hız için - Set üzerinden kontrol)
                        if ilan_id in mevcut_ilanlar:
                            print(f"⏭️ Pas geçiliyor (Zaten var): {ilan_id}")
                            continue

                        # --- LOGİN DUVARI ÖNLEMİ (Senin koda eklendi) ---
                        if index > 0 and index % 5 == 0:
                            sb.delete_all_cookies()
                            random_sleep(1, 2)

                        # --- İLANA GİRİŞ ---
                        raw_link = link_elem.get("href")
                        full_link = "https://www.sahibinden.com" + raw_link if raw_link.startswith("/") else raw_link
                        baslik = link_elem.text.strip()
                        
                        print(f"✨ İnceleniyor: {baslik}")
                        sb.open(full_link)
                        random_sleep(4, 6) # Sayfa yüklenmesi için bekle

                        # Klasör Oluştur
                        ilan_klasoru = os.path.join(SCREENSHOT_DIR, ilan_id)
                        if not os.path.exists(ilan_klasoru): os.makedirs(ilan_klasoru)
                        
                        # 1. İLK AÇILIŞ SS (İstenen Revize)
                        sb.save_screenshot(os.path.join(ilan_klasoru, "1_giris.png"))
                        
                        detay_soup = BeautifulSoup(sb.get_page_source(), "html.parser")

                        # Fiyat Temizliği
                        fiyat = "Fiyat Yok"
                        ham_fiyat = ""
                        fiyat_kutu = detay_soup.find("div", class_="classifiedInfo")
                        fiyat_container = detay_soup.find("div", class_="classified-price-container")
                        if fiyat_kutu and fiyat_kutu.find("h3"): ham_fiyat = fiyat_kutu.find("h3").text.strip()
                        elif fiyat_container: ham_fiyat = fiyat_container.text.strip()
                        if ham_fiyat:
                            temiz_fiyat = ham_fiyat.split("Fiyat Tarihçesi")[0].split("\n")[0]
                            fiyat = temiz_fiyat.strip()

                        # Açıklama (İstenen Revize: Açıklama : ... formatı)
                        aciklama_div = detay_soup.find("div", {"id": "classifiedDescription"})
                        aciklama_metni = aciklama_div.text.strip() if aciklama_div else "Açıklama bulunamadı."
                        formatli_aciklama = f"Açıklama: {aciklama_metni}"
                        
                        # Lokasyon (Trabzon / Ortahisar vb.)
                        lokasyon = "Belirtilmemiş"
                        lokasyon_h2 = detay_soup.find("div", class_="classifiedInfo").find("h2")
                        if lokasyon_h2: lokasyon = lokasyon_h2.text.strip().replace("\n", "").replace("  ", "")

                        # --- DETAYLI TEKNİK ÖZELLİKLERİ ÇEKME (Yeni Revize) ---
                        # Bu sözlük, sitedeki etiketleri veritabanındaki sütun adlarıyla eşleştirir
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
                        
                        # Veri paketini varsayılan değerlerle ("-") hazırla
                        veri_paketi = {column: "-" for column in özellik_haritası.values()}
                        
                        # Temel bilgileri ekle
                        veri_paketi["ilan_no"] = ilan_id
                        veri_paketi["baslik"] = baslik
                        veri_paketi["fiyat"] = fiyat
                        veri_paketi["link"] = full_link
                        veri_paketi["resim_yolu"] = f"{ilan_id}/1_giris.png"
                        veri_paketi["aciklama"] = formatli_aciklama
                        veri_paketi["lokasyon"] = lokasyon

                        # Sitedeki teknik özellik listesini (ul class="classifiedInfoList") tara
                        info_ul = detay_soup.find("ul", class_="classifiedInfoList")
                        if info_ul:
                            li_items = info_ul.find_all("li")
                            for li in li_items:
                                etiket = li.find("strong")
                                deger = li.find("span")
                                if etiket and deger:
                                    # Sitedeki etiket adını temizle (örn: " Oda Sayısı " -> "Oda Sayısı")
                                    etiket_adi = etiket.text.strip()
                                    
                                    # Eğer bu etiket bizim haritamızda varsa, değerini kaydet
                                    if etiket_adi in özellik_haritası:
                                        sütun_adi = özellik_haritası[etiket_adi]
                                        veri_paketi[sütun_adi] = deger.text.strip()

                        basarili = veritabanina_ekle(veri_paketi)
                        if basarili: toplam_yeni_ilan += 1
                        
                        random_sleep(2, 4)

                    except Exception as e:
                        print(f"❌ Satır hatası: {e}")
                        continue
                
                # Sayfa bitince sonrakine geç
                su_anki_sayfa += 1
                sb.delete_all_cookies() # Ban koruması
                random_sleep(3, 5)
            
            return f"✅ Tarama Tamamlandı. Toplam {toplam_yeni_ilan} yeni ilan kaydedildi."

    except Exception as genel_hata:
        print(f"🔥 KRİTİK HATA: {genel_hata}")
        return f"❌ Hata oluştu: {str(genel_hata)}"