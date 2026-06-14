# Bot ve web kazima islemleri icin gerekli kutuphaneleri projeye dahil ediyoruz
from seleniumbase import SB
from bs4 import BeautifulSoup
import sqlite3
import time
import random
import os

# Projenin calistigi ana dizini belirliyoruz
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Cekilecek ekran goruntulerinin kaydedilecegi klasoru ayarladik
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")

# Eger resimlerin kaydedilecegi klasor henuz yoksa yeni bir tane olusturuyoruz
if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR)

# Botun anlasilmamasi icin bekleme surelerini rastgele yapan fonksiyon
def random_sleep(min_s, max_s):
    time.sleep(random.uniform(min_s, max_s))

# Web sayfasindan aldigimiz verileri alip veritabanina kaydeden fonksiyonumuz
def veritabanina_ekle(data):
    db_yolu = os.path.join(BASE_DIR, "emlak.db")
    # Eger veritabani dosyasi henuz yoksa database modulunu cagirarak bastan olusturuyoruz
    if not os.path.exists(db_yolu):
        import database
        database.init_db()

    # Veritabanina islem yapabilmek icin baglanti sagliyoruz
    conn = sqlite3.connect(db_yolu)
    cursor = conn.cursor()
    durum = False
    
    try:
        # Cektigimiz emlak bilgilerini ilgili sutunlara gelecek sekilde veritabanina yaziyoruz
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
            
            # Ilandan cekilen guncel tarih bilgisini ekliyoruz
            data["ilan_tarihi"],
            
            # Diger detayli teknik ozellikleri veritabanina tek tek yerlestiriyoruz
            data["emlak_tipi"], data["m2_brut"], data["m2_net"], data["oda_sayisi"], data["bina_yasi"],
            data["bulundugu_kat"], data["kat_sayisi"], data["isitma"], data["banyo_sayisi"], data["mutfak"], data["balkon"],
            data["asansor"], data["otopark"], data["esyali"], data["kullanim_durumu"], data["site_icerisinde"], data["site_adi"],
            data["aidat"], data["krediye_uygun"], data["tapu_durumu"], data["kimden"], data["takas"]
        ))
        # Yaptigimiz degisiklikleri veritabanina temelli kaydediyoruz
        conn.commit()
        print(f"Basariyla veritabanina eklendi: {data['ilan_no']}")
        durum = True
    except sqlite3.IntegrityError:
        # Eger ilan zaten kayitliysa ayni ilani tekrar eklememek icin pas geciyoruz
        print(f"Ilan zaten sistemde mevcut: {data['ilan_no']}")
        durum = False
    except Exception as e:
        # Farkli bir hata olusursa bunu ekrana basiyoruz
        print(f"Veritabani yazma isleminde bir problem oldu: {e}")
        durum = False
    finally:
        # Islem bitince veritabani baglantisini mecburi kapatiyoruz
        conn.close()
    
    return durum

# Emlak arama sayfasina gidip ilanlari taramaya baslayan ana bot fonksiyonumuz
def botu_calistir(hedef_link, limit=10):
    print(f"Tarama motoru baslatildi lutfen bekleyin hedef baglanti: {hedef_link}")
    
    # Hizi artirmak icin onceden eklenen ilan numaralarini sistem hafizasina aliyoruz
    db_yolu = os.path.join(BASE_DIR, "emlak.db")
    mevcut_ilanlar = set()
    try:
        # Veritabanindaki sadece ilan numaralarini cekip bir kume icinde topluyoruz
        if os.path.exists(db_yolu):
            conn = sqlite3.connect(db_yolu)
            cursor = conn.cursor()
            cursor.execute("SELECT ilan_no FROM ilanlar")
            for sat in cursor.fetchall():
                mevcut_ilanlar.add(sat[0])
            conn.close()
    except Exception as e:
        print("Veritabani kontrol edilirken sorun yasandi:", e)

    toplam_yeni_ilan = 0
    # Birden fazla sayfayi gezebilmek icin sayfa numarasini birden baslatiyoruz
    su_anki_sayfa = 1
    # Yuz ilan taranacaksa her sayfada yirmi ilan oldugu icin yaklasik bes alti sayfa gezmesini sagliyoruz
    MAX_SAYFA_LIMITI = (limit // 20) + 1 
    # Bot korumasi devreye girerse sistemi durdurmak icin ard arda alinan hata sayisini sayiyoruz
    ardisik_hata_sayisi = 0

    # Tarayicinin bilgisayarda nerede yuklu oldugunu gosteren dosya yolu
    BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"

    try:
        # Gizli modda ve reklamlari engelleyerek tarayiciyi baslatiyoruz
        with SB(uc=True, test=True, ad_block_on=True, binary_location=BRAVE_PATH) as sb:
            try: sb.maximize_window()
            except: pass

            # Belirledigimiz sayfa limitine ulasana kadar donguyu donduruyoruz
            while su_anki_sayfa <= MAX_SAYFA_LIMITI:
                
                # Ikinci sayfaya gecerken sahibinden sitesinin istedigi sayfa baslangic degerini ekliyoruz
                offset = (su_anki_sayfa - 1) * 20
                guncel_link = hedef_link
                if offset > 0:
                    if "?" in hedef_link:
                        guncel_link = f"{hedef_link}&pagingOffset={offset}"
                    else:
                        guncel_link = f"{hedef_link}?pagingOffset={offset}"

                print(f"Su an sayfa {su_anki_sayfa} uzerinde arama yapiliyor")
                
                # Olusturdugumuz linki tarayicida aciyoruz
                sb.open(guncel_link)
                random_sleep(5, 7)

                # Sayfanin kodlarini cekip okunabilir hale getiriyoruz
                soup = BeautifulSoup(sb.get_page_source(), "html.parser")
                # Ilanlarin listelendigi ana tabloyu sayfa icinde buluyoruz
                main_table = soup.find("table", {"id": "searchResultsTable"})
                
                if not main_table:
                     # Tablo olarak bulamazsak farkli bir sablon olabilir diye kutu bazli ariyoruz
                     satirlar = soup.find_all("div", {"class": "searchResultsItem"})
                     if not satirlar: 
                         print("Sayfada liste bulunamadi muhtemelen engellendik veya ilanlar bitti")
                         break
                else:
                     # Eger ana tablo bulunduysa tablonun icindeki satirlari tek tek cekiyoruz
                     satirlar = main_table.find("tbody").find_all("tr")

                # Eger satirlar bos geldiyse donguden cikip islemi bitiriyoruz
                if len(satirlar) == 0: break

                # Buldugumuz tum satirlari sirayla donmeye basliyoruz
                for index, satir in enumerate(satirlar):
                    # Istenilen ilan sayisina ulastiysak botu komple durduruyoruz
                    if toplam_yeni_ilan >= limit:
                        print(f"Belirtilen ilan islem sinirina basariyla ulasildi")
                        return f"Tarama sonlandirildi toplam {toplam_yeni_ilan} ilan eklendi"

                    # Satir eger reklam veya sponsorlu ilansa o satiri atliyoruz
                    if "nativeAd" in satir.get("class", []) or "searchResultsPromoSuper" in satir.get("class", []):
                        continue
                    
                    try:
                        # Ilanin numarasini satirdan almaya calisiyoruz
                        ilan_id = satir.get("data-id")
                        link_elem = satir.find("a", class_="classifiedTitle")
                        
                        # Eger numarayi bulamazsak baglanti linki uzerinden cekmeyi deniyoruz
                        if not ilan_id:
                             if link_elem and "-" in link_elem.get("href"):
                                 ilan_id = link_elem.get("href").split("-")[-1].replace("/detay", "")
                        
                        # Iki bilgi de eksikse hatali satirdir diyerek es geciyoruz
                        if not ilan_id or not link_elem: continue

                        # Ilan numarasini onceki ilanlarimiz icinde ariyip var ise tekrar acmadan atliyoruz
                        if ilan_id in mevcut_ilanlar:
                            print(f"Ilan kayitlarda var pas geciliyor: {ilan_id}")
                            continue

                        # Belirli araliklarla tarayici cerezlerini siliyoruz ki bot oldugumuzu anlamasinlar
                        if index > 0 and index % 5 == 0:
                            sb.delete_all_cookies()
                            random_sleep(1, 2)

                        # Ilanin linkini duzenleyerek ilanin kendi tam sayfasina gidiyoruz
                        raw_link = link_elem.get("href")
                        full_link = "https://www.sahibinden.com" + raw_link if raw_link.startswith("/") else raw_link
                        baslik = link_elem.text.strip()
                        
                        print(f"Detayli bilgi toplanan ilan: {baslik}")
                        sb.open(full_link)
                        # Sayfanin tamamen yuklenmesi ve bot sanilmamasi icin bir sure bekliyoruz
                        random_sleep(4, 6) 

                        # Resimleri kaydetmek icin sadece bu ilana ozel bir klasor aciyoruz
                        ilan_klasoru = os.path.join(SCREENSHOT_DIR, ilan_id)
                        if not os.path.exists(ilan_klasoru): os.makedirs(ilan_klasoru)
                        
                        # Sayfaya girer girmez gordugumuz ilk ekranin fotografini cekip kaydediyoruz
                        sb.save_screenshot(os.path.join(ilan_klasoru, "1_giris.png"))
                        
                        # Ilan detay sayfasinin butun kaynak kodlarini okuyoruz
                        detay_soup = BeautifulSoup(sb.get_page_source(), "html.parser")

                        # Siteden fiyati bulup aliyoruz ardindan gereksiz yazilari temizliyoruz
                        fiyat = "Fiyat Yok"
                        ham_fiyat = ""
                        fiyat_kutu = detay_soup.find("div", class_="classifiedInfo")
                        fiyat_container = detay_soup.find("div", class_="classified-price-container")
                        if fiyat_kutu and fiyat_kutu.find("h3"): ham_fiyat = fiyat_kutu.find("h3").text.strip()
                        elif fiyat_container: ham_fiyat = fiyat_container.text.strip()
                        if ham_fiyat:
                            temiz_fiyat = ham_fiyat.split("Fiyat Tarihcesi")[0].split("\n")[0]
                            fiyat = temiz_fiyat.strip()

                        # Satici tarafindan eklenen detayli ilan aciklama metnini bularak cekiyoruz
                        aciklama_div = detay_soup.find("div", {"id": "classifiedDescription"})
                        aciklama_metni = aciklama_div.text.strip() if aciklama_div else "Bu ilanda aciklama yer almiyor"
                        formatli_aciklama = f"Aciklama: {aciklama_metni}"
                        
                        # Ilanin bulundugu sehir ilce ve mahalle bilgilerini duzenleyerek aliyoruz
                        lokasyon = "Belirtilmemis"
                        lokasyon_h2 = detay_soup.find("div", class_="classifiedInfo").find("h2")
                        if lokasyon_h2: lokasyon = lokasyon_h2.text.strip().replace("\n", "").replace("  ", "")

                        # Sitedeki sag tarafta bulunan ozellikler kismini db sutunlariyla eslestiriyoruz
                        ozellik_haritasi = {
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
                        
                        # Eksik bilgiler bos kalmasin diye once tum verileri tire isaretiyle dolduruyoruz
                        veri_paketi = {column: "-" for column in ozellik_haritasi.values()}
                        
                        # Kendi buldugumuz temel verileri ustune yaziyoruz
                        veri_paketi["ilan_no"] = ilan_id
                        veri_paketi["baslik"] = baslik
                        veri_paketi["fiyat"] = fiyat
                        veri_paketi["link"] = full_link
                        veri_paketi["resim_yolu"] = f"{ilan_id}/1_giris.png"
                        veri_paketi["aciklama"] = formatli_aciklama
                        veri_paketi["lokasyon"] = lokasyon

                        # Sitedeki sag tarafta bulunan madde madde teknik ozellikleri buluyoruz
                        info_ul = detay_soup.find("ul", class_="classifiedInfoList")
                        if info_ul:
                            li_items = info_ul.find_all("li")
                            for li in li_items:
                                etiket = li.find("strong")
                                deger = li.find("span")
                                if etiket and deger:
                                    # Ozellik basligindaki gereksiz bosluklari siliyoruz
                                    etiket_adi = etiket.text.strip()
                                    
                                    # Eger siteden aldigimiz bu ozellik bizim kayit listemizde varsa degerini isliyoruz
                                    if etiket_adi in ozellik_haritasi:
                                        sutun_adi = ozellik_haritasi[etiket_adi]
                                        veri_paketi[sutun_adi] = deger.text.strip()

                        # Toparlanan tum bu verileri veritabanina gondermek uzere diger fonksiyona iletiyoruz
                        basarili = veritabanina_ekle(veri_paketi)
                        if basarili: toplam_yeni_ilan += 1
                        
                        # Sorunsuz sekilde sayfayi okuduysak bot korumasina yakalanmamisiz demektir hatayi sifirliyoruz
                        ardisik_hata_sayisi = 0 
                        random_sleep(2, 4)

                    except Exception as e:
                        # Sayfa yapisi farkliysa veya bot korumasi yuzunden ogeler gorunmuyorsa hata aliriz
                        print(f"Satir islenirken beklenmeyen bir durum yasandi: {e}")
                        # Hatayi bir artirip ust uste bes kez olup olmadigina bakiyoruz
                        ardisik_hata_sayisi += 1
                        if ardisik_hata_sayisi >= 5:
                            # Ust uste cok hata verdiysen sistemden ban yemis olabiliriz o yuzden islemi sonlandiriyoruz
                            hata_mesaji = f"Sistem ust uste bes kez verileri okuyamadi guvenlik onlemi olarak islem sonlandiriliyor eklenen ilan: {toplam_yeni_ilan}"
                            print(hata_mesaji)
                            return hata_mesaji
                        continue
                
                # Bu sayfadaki ilanlar bitince diger sayfaya geciyoruz
                su_anki_sayfa += 1
                # Sayfa degistirirken cerezleri siliyoruz ki izimizi kaybettirelim
                sb.delete_all_cookies() 
                random_sleep(3, 5)
            
            # Belirtilen sayfa limitine ulasildiysa basari mesajini ve kac ilan eklendigini donuyoruz
            return f"Bot tarama gorevini basariyla bitirdi toplam {toplam_yeni_ilan} yeni kayit olusturuldu"

    except Exception as genel_hata:
        # Sistemin baslatilmasini engelleyen buyuk bir sorun olursa bunu yakaliyoruz
        print(f"Tarayici baslatilamadi veya buyuk bir hata olustu: {genel_hata}")
        return f"Beklenmeyen bir hata yuzunden islem durdu: {str(genel_hata)}"