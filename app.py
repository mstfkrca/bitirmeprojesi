# Gerekli kutuphaneleri projeye dahil ediyoruz
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify, flash
from werkzeug.utils import secure_filename
import sqlite3
import os
import threading
<<<<<<< HEAD
import shutil # Dosya ve klasor silme islemleri icin eklendi
from scraper import botu_calistir
import database

# Projenin calistigi ana dizini belirliyoruz
=======
import shutil # Klasörleri ve içindekileri tamamen silmek için kullanılan kütüphane
from scraper import botu_calistir
import database

# Projenin ana çalışma dizinini ve alt yollarını tanımlıyoruz.
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Veritabaninin kaydedilecegi tam yolu ayarladik
DB_PATH = os.path.join(BASE_DIR, "emlak.db")
<<<<<<< HEAD
# Botun cektigi ekran goruntulerini saklayacagimiz klasorun yolunu belirttik
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")

# Veritabani dosyasi yoksa bastan olusturuyoruz
=======
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")

# Uygulama her başladığında veritabanı dosyasının ve tablolarının varlığını kontrol edip yoksa oluşturuyor.
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
database.init_db()

# Flask web uygulamamizi baslatiyoruz
app = Flask(__name__)
<<<<<<< HEAD
# Kullaniciya gosterilecek bildirim mesajlari icin gizli bir anahtar belirledik
app.secret_key = "gizli_anahtar_emlak_avcisi_premium" 

# Botun arka planda calisip calismadigini ve anlik durumunu bu sozluk uzerinden takip ediyoruz
=======
# Flask üzerinde flash mesajlarını (bildirim pencerelerini) kullanabilmek için şifreleme anahtarı (secret key) tanımlıyoruz.
app.secret_key = "gizli_anahtar_emlak_avcisi_premium" 

# Arka planda çalışan Selenium botunun durumunu ve mesajını tutan küresel (global) sözlük.
# Arayüzdeki JavaScript (AJAX) burayı sorgulayarak ekranda anlık yüklenme durumunu gösterir.
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
bot_durumu = {"mesaj": "", "calisiyor": False}

# Arayuz donmasin diye botu ayri bir is parcaciginda arka planda calistiran fonksiyonumuz
def botu_arka_planda_calistir(link, limit):
<<<<<<< HEAD
    # Botun calismaya basladigini sisteme bildiriyoruz
=======
    # Botun çalışmaya başladığını işaretliyoruz.
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
    bot_durumu["calisiyor"] = True
    bot_durumu["mesaj"] = "Yapay zeka botu islemlere basliyor lutfen bekleyin"
    try:
<<<<<<< HEAD
        # Scraper dosyasindaki gercek bot fonksiyonunu cagiriyoruz
=======
        # scraper.py içindeki ana tarama fonksiyonunu çağırıyoruz.
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
        sonuc = botu_calistir(link, limit=limit)
        # Islem bitince botun dondugu mesaji duruma yaziyoruz
        bot_durumu["mesaj"] = sonuc
    except Exception as e:
        # Eger bir hata cikarsa bunu kaydediyoruz
        bot_durumu["mesaj"] = f"Bir hata olustu: {str(e)}"
        print(f"Arka plan isleminde hata: {e}")
    finally:
<<<<<<< HEAD
        # Islem basarili da olsa hatali da olsa botun calismasini durduruyoruz
        bot_durumu["calisiyor"] = False

# Kaydedilen ekran goruntulerine web arayuzunden erisebilmek icin bir yol tanimladik
@app.route('/screenshots/<path:filename>')
def resim_goster(filename):
    # Dosyalari guvenli bir sekilde disari sunuyoruz
    return send_from_directory(SCREENSHOTS_DIR, filename)

# Botun ne durumda oldugunu tarayiciya bildiren adres
@app.route('/status')
def durum_kontrol():
    # Anlik durumu JSON formatinda donduruyoruz ki on yuz guncellenebilsin
    return jsonify(bot_durumu)

# Uygulamamizin ana sayfasi hem form gonderme hem de sayfa goruntuleme islerini yapiyor
=======
        # Hata alınsa da tarama başarıyla bitse de çalışıyor durumunu kapatıyoruz.
        bot_durumu["calisiyor"] = False

# İndirilen ilan ekran görüntülerini web arayüzünde güvenle göstermek için kullanılan endpoint.
@app.route('/screenshots/<path:filename>')
def resim_goster(filename):
    # send_from_directory fonksiyonu, dosya yollarının manipüle edilmesini (Path Traversal - üst dizinlere sızma) otomatik önler.
    return send_from_directory(SCREENSHOT_DIR, filename)

# Arayüzün sayfayı yenilemeden botun durumunu sorgulayabilmesi için JSON yanıt dönen endpoint.
@app.route('/status')
def durum_kontrol():
    # AJAX (fetch API) üzerinden frontend'e anlık bilgi vermek için sözlüğü JSON formatında dönüyoruz.
    return jsonify(bot_durumu)

# Ana sayfa ve tüm filtreleme/tetikleme işlemlerinin yapıldığı ana rota.
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
@app.route('/', methods=['GET', 'POST'])
def ana_sayfa():
    # Eger kullanici arayuzden bir butona basmissa bu kisim calisir
    if request.method == 'POST':
<<<<<<< HEAD
        
        # Kullanici botu baslatma butonuna basmissa
=======
        # --- BOTU BAŞLATMA İŞLEMİ ---
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
        if 'baslat' in request.form:
            # Formdan gelen linki ve limiti aliyoruz
            link = request.form.get('ilan_linki')
            limit = request.form.get('limit', '200')
            # Limit eger sayi degilse varsayilan olarak iki yuz yapiyoruz
            limit = int(limit) if limit.isdigit() else 200
            
<<<<<<< HEAD
            # Eger gecerli bir link varsa ve bot su an baska bir islem yapmiyorsa
=======
            # Bot zaten çalışmıyorsa yeni bir iş parçacığı (Thread) oluşturup başlatıyoruz.
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
            if link and not bot_durumu["calisiyor"]:
                # Botu arka planda baslatiyoruz boylece web sitemiz donmuyor
                t = threading.Thread(target=botu_arka_planda_calistir, args=(link, limit))
                # daemon=True: Ana Flask uygulaması kapatıldığında bu thread'in de arka planda çalışmaya devam edip
                # işletim sisteminde "zombi süreç" oluşturmasını önler, otomatik sonlandırır.
                t.daemon = True
                t.start()
                # Kullaniciya isin basladigina dair bilgi veriyoruz
                flash("Bot islemleri basladi lutfen sonuclanmasini bekleyin", "success")
        
<<<<<<< HEAD
        # Kullanici arsivi tamamen temizle butonuna basmissa
=======
        # --- VERİTABANI VE ARŞİVİ SIFIRLAMA İŞLEMİ ---
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
        elif 'temizle' in request.form:
            # Eger bot arka planda islem yapmiyorsa verileri siliyoruz
            if not bot_durumu["calisiyor"]:
                try:
<<<<<<< HEAD
                    # Veritabanina baglanip tum ilanlari siliyoruz
=======
                    # SQLite veritabanındaki tüm ilanları siliyoruz.
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM ilanlar")
                    conn.commit()
                    conn.close()
                    
<<<<<<< HEAD
                    # Indirilmis olan tum ekran goruntusu klasorlerini komple silip yeniden bos bir klasor aciyoruz
                    if os.path.exists(SCREENSHOTS_DIR):
                        shutil.rmtree(SCREENSHOTS_DIR)
                        os.makedirs(SCREENSHOTS_DIR)
=======
                    # Disk üzerindeki screenshots klasörünü komple silip sıfırdan boş oluşturuyoruz.
                    if os.path.exists(SCREENSHOT_DIR):
                        shutil.rmtree(SCREENSHOT_DIR)
                        os.makedirs(SCREENSHOT_DIR)
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
                    
                    # Sisteme her seyin temizlendigi bilgisini geciyoruz
                    bot_durumu["mesaj"] = "Tum veriler ve resimler temizlendi"
                    flash("Sistemdeki tum veriler ve resimler basariyla temizlendi", "success")
                except Exception as e:
                    # Silme isleminde bir terslik olursa ekrana hata donduruyoruz
                    flash(f"Arsivi silerken bir problem yasandi: {str(e)}", "danger")

<<<<<<< HEAD
        # Kullanici sadece tek bir ilani silmek isterse
=======
        # --- TEK BİR İLANI SİLME İŞLEMİ ---
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
        elif 'tek_sil' in request.form:
            # Bot calismiyorken silme islemine izin veriyoruz
            if not bot_durumu["calisiyor"]:
                ilan_id_to_delete = request.form.get('sil_ilan_id')
                if ilan_id_to_delete and ilan_id_to_delete.strip() != "":
<<<<<<< HEAD
                    # Gelen id bilgisini guvenli hale getiriyoruz ki sistem klasorlerine sizilamasin
                    guvenli_id = secure_filename(ilan_id_to_delete)
                    if guvenli_id:
                        try:
                            # Veritabanindan o ilana ait olan satiri kaldiriyoruz
=======
                    # GÜVENLİK YAMASI: secure_filename fonksiyonu dosya adındaki tehlikeli karakterleri (örneğin "../")
                    # temizleyerek Path Traversal (başka sistem klasörlerini silme) saldırılarını engeller.
                    guvenli_id = secure_filename(ilan_id_to_delete)
                    if guvenli_id:
                        try:
                            # 1. Veritabanından ilgili ilanı siliyoruz (parametrik sorgu ile SQL injection korumalı).
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
                            conn = sqlite3.connect(DB_PATH)
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM ilanlar WHERE ilan_no = ?", (ilan_id_to_delete,))
                            conn.commit()
                            conn.close()
                            
<<<<<<< HEAD
                            # O ilana ait olan resim klasorunu bularak siliyoruz
                            folder_path = os.path.join(SCREENSHOTS_DIR, guvenli_id)
=======
                            # 2. İlana ait ekran görüntüsü klasörünü diskten siliyoruz.
                            folder_path = os.path.join(SCREENSHOT_DIR, guvenli_id)
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
                            if os.path.exists(folder_path):
                                shutil.rmtree(folder_path)
                            
                            flash(f"Ilan sistemden basariyla kaldirildi", "success")
                        except Exception as e:
                            print(f"Ilan silinirken bir hata olustu: {e}")
                            flash(f"Silme isleminde hata yasandi: {str(e)}", "danger")

<<<<<<< HEAD
        # Islemler bittikten sonra sayfayi yeniliyoruz ki kullanici sayfayi yenileyince tekrar form gondermesin
        return redirect(url_for('ana_sayfa'))

    # Buradan sonrasi sayfa normal bir sekilde acildiginda veya arama yapildiginda calisir
    # URL uzerinden gelen arama ve filtreleme parametrelerini aliyoruz
=======
        # POST-REDIRECT-GET (PRG) DESENİ:
        # POST işlemi bittikten sonra sayfayı ana sayfaya yönlendiriyoruz (Redirect).
        # Böylece kullanıcı arayüzde F5 (sayfa yenileme) yaptığında tarayıcı aynı POST isteğini tekrar gönderip
        # yanlışlıkla botu yeniden başlatmaz veya silme işlemini tekrarlamaz.
        return redirect(url_for('ana_sayfa'))

    # --- GET İSTEĞİ (ARAMA, FİLTRELEME VE SAYFALAMA) ---
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
    search_q = request.args.get('q', '').strip()
    il_filtre = request.args.get('il', '').strip()
    ilce_filtre = request.args.get('ilce', '').strip()
    mahalle_filtre = request.args.get('mahalle', '').strip()
    oda_filtre = request.args.get('oda', '').strip()
    fiyat_araligi = request.args.get('fiyat_araligi', '').strip()
    siralama = request.args.get('siralama', 'tarih_yeni').strip()
    
    # Sayfalama islemi icin gecerli sayfa numarasini aliyoruz varsayilan olarak birinci sayfa
    page = request.args.get('page', 1, type=int)
<<<<<<< HEAD
    # Her sayfada on bes ilan gosterilmesini sagliyoruz
    per_page = 15
=======
    per_page = 15 # Sayfa başına gösterilecek ilan sayısı
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4

    # Veritabanina okuma islemleri icin baglanti aciyoruz
    conn = sqlite3.connect(DB_PATH)
<<<<<<< HEAD
    # Satirlari sozluk gibi cekebilmek icin bu ayari yapiyoruz
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Menulerde gostermek uzere kayitli ilanlarin bulundugu sehir ve ilceleri cekiyoruz
    cursor.execute("SELECT DISTINCT lokasyon FROM ilanlar WHERE lokasyon IS NOT NULL AND lokasyon != '' AND lokasyon != '-'")
    ham_lokasyonlar = [row[0] for row in cursor.fetchall() if row[0]]
    
    # Il ilce ve mahalleleri birbiri icinde hiyerarsik olarak tutacagimiz bir sozluge atiyoruz
=======
    conn.row_factory = sqlite3.Row # Veritabanından gelen satırları sözlük (key-value) şeklinde okuyabilmek için Row yapısını aktif ediyoruz.
    cursor = conn.cursor()
    
    # --- DİNAMİK LOKASYON AĞACI OLUŞTURMA (JS DROPDOWN'LAR İÇİN) ---
    # Veritabanında kayıtlı olan benzersiz lokasyonları (örn: "İstanbul/Kadıköy/Caferağa") çekiyoruz.
    cursor.execute("SELECT DISTINCT lokasyon FROM ilanlar WHERE lokasyon IS NOT NULL AND lokasyon != '' AND lokasyon != '-'")
    ham_lokasyonlar = [row[0] for row in cursor.fetchall() if row[0]]
    
    # JavaScript tarafında dinamik il->ilçe->mahalle ilişkisini kurabilmek için lokasyonları ağaç yapısına (Sözlük) dönüştürüyoruz.
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
    lokasyon_agaci = {}
    
    # Veritabanindan cektigimiz slash isaretli lokasyon bilgisini parcaliyoruz
    for lok in ham_lokasyonlar:
        parts = lok.split('/')
        if len(parts) >= 1:
            il = parts[0].strip()
            # Eger il sozlugumuzde yoksa yeni bir il aciyoruz
            if il not in lokasyon_agaci:
                lokasyon_agaci[il] = {}
                
            if len(parts) >= 2:
                ilce = parts[1].strip()
                # Ilcenin altina mahalleleri ekleyecegimiz icin kume kullaniyoruz
                if ilce not in lokasyon_agaci[il]:
                    lokasyon_agaci[il][ilce] = set()
                    
                if len(parts) >= 3:
                    mahalle = parts[2].strip()
                    # Ayni mahalleden birden fazla varsa kume sayesinde tek bir kere kaydediliyor
                    lokasyon_agaci[il][ilce].add(mahalle)
                
<<<<<<< HEAD
    # HTML tarafinda rahat listeleme yapabilmek icin kumeleri normal listeye ceviriyoruz
=======
    # JavaScript'in okuması kolay olsun diye Set'leri sıralı listeye dönüştürüyoruz.
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
    iller = sorted(list(lokasyon_agaci.keys()))
    for il in lokasyon_agaci:
        for ilce in lokasyon_agaci[il]:
            lokasyon_agaci[il][ilce] = sorted(list(lokasyon_agaci[il][ilce]))
    
<<<<<<< HEAD
    # Ayni islemi oda sayisi secenekleri icin de yapiyoruz farkli oda tiplerini listeliyoruz
    cursor.execute("SELECT DISTINCT oda_sayisi FROM ilanlar WHERE oda_sayisi IS NOT NULL AND oda_sayisi != '' AND oda_sayisi != '-'")
    odalar = [row[0] for row in cursor.fetchall() if row[0]]

    # Kullanicinin sectigi filtrelere gore veritabaninda arama yapacak sorguyu hazirliyoruz
    query_conditions = "1=1"
    params = []

    # Arama kutusuna bir sey yazildiysa hem baslikta hem aciklamada ariyoruz
=======
    # Arayüzdeki oda filtresi dropdown'ını doldurmak için DB'deki benzersiz oda sayılarını (örn: 2+1, 3+1) çekiyoruz.
    cursor.execute("SELECT DISTINCT oda_sayisi FROM ilanlar WHERE oda_sayisi IS NOT NULL AND oda_sayisi != '' AND oda_sayisi != '-'")
    odalar = [row[0] for row in cursor.fetchall() if row[0]]

    # --- DİNAMİK SQL QUERY BUILDER (SORGU OLUŞTURUCU) ---
    # "1=1" koşulu her zaman doğru (True) kabul edilir. 
    # Bu teknik sayesinde ilk filtre eklenirken "WHERE mi AND mi yazmalıyım?" derdi olmadan, 
    # sonraki tüm koşulları doğrudan "AND" ile dinamik olarak bağlayabiliyoruz.
    query_conditions = "1=1"
    params = []

    # Kelime arama filtresi (Başlık veya Açıklama içinde arar)
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
    if search_q:
        query_conditions += " AND (baslik LIKE ? OR aciklama LIKE ?)"
        params.extend([f"%{search_q}%", f"%{search_q}%"])

<<<<<<< HEAD
    # Eger bolge secildiyse sirasiyla sehir ilce veya mahalleye gore sorguyu daraltiyoruz
=======
    # Lokasyon (İl, İlçe, Mahalle) hiyerarşik filtresi
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
    if il_filtre:
        if mahalle_filtre:
            query_conditions += " AND lokasyon LIKE ?"
            params.append(f"{il_filtre}/{ilce_filtre}/{mahalle_filtre}%")
        elif ilce_filtre:
            query_conditions += " AND lokasyon LIKE ?"
            params.append(f"{il_filtre}/{ilce_filtre}%")
        else:
            query_conditions += " AND lokasyon LIKE ?"
            params.append(f"{il_filtre}/%")
        
<<<<<<< HEAD
    # Eger oda sayisi secildiyse sadece o oda sayisina sahip ilanlari istiyoruz
=======
    # Oda sayısı filtresi
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
    if oda_filtre:
        query_conditions += " AND oda_sayisi = ?"
        params.append(oda_filtre)

<<<<<<< HEAD
    # Kullanici fiyat araligi secmisse fiyati sayiya cevirip araliga gore filtreliyoruz
=======
    # --- METİNSEL FİYATI SAYISALA ÇEVİRİP FİLTRELEME (CAST/REPLACE) ---
    # Fiyat veritabanında "2.500.000 TL" şeklinde metindir. Matematiksel karşılaştırma yapabilmek için:
    # 1. REPLACE ile nokta ('.') ve ' TL' kısımlarını temizliyoruz.
    # 2. CAST(... AS INTEGER) ile sayıyı tamsayıya dönüştürüp aralık kontrolü yapıyoruz.
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
    if fiyat_araligi:
        if fiyat_araligi == "0-2M":
            query_conditions += " AND CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER) <= 2000000"
        elif fiyat_araligi == "2M-5M":
            query_conditions += " AND CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER) BETWEEN 2000000 AND 5000000"
        elif fiyat_araligi == "5M-10M":
            query_conditions += " AND CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER) BETWEEN 5000000 AND 10000000"
        elif fiyat_araligi == "10M+":
            query_conditions += " AND CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER) >= 10000000"

<<<<<<< HEAD
    # Filtrelere uyan toplam kac tane ilan oldugunu sayiyoruz ki asagiya sayfa numaralarini dizebilelim
=======
    # --- SAYFALAMA (PAGINATION) HESAPLAMA ---
    # Seçilen kriterlere uyan toplam ilan sayısını buluyoruz.
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
    cursor.execute(f"SELECT COUNT(*) FROM ilanlar WHERE {query_conditions}", params)
    total_ilan = cursor.fetchone()[0]
    
    # Toplam sayfa sayisini hesapliyoruz
    total_pages = (total_ilan + per_page - 1) // per_page
    
    # Sayfa sınırlarının dışına çıkılmasını önlüyoruz.
    if page < 1: 
        page = 1
    if page > total_pages and total_pages > 0: 
        page = total_pages

<<<<<<< HEAD
    # Istenen siralama yonune gore sonuclari duzenliyoruz
    order_clause = "tarih DESC"
=======
    # --- SIRALAMA (ORDER BY) İŞLEMLERİ ---
    order_clause = "tarih DESC" # Varsayılan olarak en son eklenen ilan en üstte görünür.
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
    if siralama == "tarih_eski":
        order_clause = "tarih ASC"
    elif siralama == "fiyat_artan":
        order_clause = "CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER) ASC"
    elif siralama == "fiyat_azalan":
        order_clause = "CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER) DESC"

<<<<<<< HEAD
    # Filtrelerimize uygun olan ilanlari veritabanindan limitli olarak cekiyoruz
=======
    # --- SAYFALAMA LİMİTLEME SORGUSU (LIMIT & OFFSET) ---
    # LIMIT: Sadece sayfa başına gösterilecek adet kadar veri çeker.
    # OFFSET: Önceki sayfaların verilerini atlayarak hedef sayfa verisinin başlamasını sağlar.
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
    query = f"SELECT * FROM ilanlar WHERE {query_conditions} ORDER BY {order_clause} LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])
    
    cursor.execute(query, params)
    ilanlar = cursor.fetchall()
    
<<<<<<< HEAD
    # Secilen bolgeye ait ortalama bir fiyat bilgisi sunmak icin hesaplama yapiyoruz
=======
    # --- ORTALAMA BÖLGESEL FİYAT HESAPLAMA ---
    # Kullanıcı bir il filtrelediğinde, o bölgedeki ortalama ev fiyatını hesaplayıp ekranda istatistik olarak gösteriyoruz.
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
    ortalama_fiyat = None
    bolge_adi = None
    if il_filtre:
        bolge_adi = f"{il_filtre} Ili"
        if ilce_filtre:
            bolge_adi = f"{ilce_filtre}"
            if mahalle_filtre:
                bolge_adi = f"{mahalle_filtre}"
            
<<<<<<< HEAD
        # Filtrelere uyan kayitlarin fiyat ortalamasini aliyoruz
        avg_query = f"SELECT AVG(CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER)) FROM ilanlar WHERE {query_conditions} AND fiyat IS NOT NULL AND fiyat != 'Fiyat Yok' AND fiyat != ''"
=======
        # Ortalama almak için SQL'in AVG() fonksiyonunu kullanıyoruz. Fiyatı temizleyerek sayıya çeviriyoruz.
        avg_query = f"SELECT AVG(CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER)) FROM ilanlar WHERE {query_conditions} AND fiyat IS NOT NULL AND fiyat != 'Fiyat Yok' AND fiyat != ''"
        # LIMIT ve OFFSET parametrelerini bu sorguda kullanmayacağımız için params listesinden çıkarıyoruz.
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
        avg_params = params[:-2] 
        cursor.execute(avg_query, avg_params)
        avg_result = cursor.fetchone()[0]
        if avg_result:
<<<<<<< HEAD
            # Cikan ortalamayi okunabilir bir formata ceviriyoruz
=======
            # Çıkan sonucu binlik ayraca göre formatlayıp (örn: 2.340.000 TL) arayüze gönderiyoruz.
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
            ortalama_fiyat = f"{int(avg_result):,} TL".replace(',', '.')
            
    conn.close()

<<<<<<< HEAD
    # Toplanan tum verileri html sablonuna gondererek web sayfamizin basilmasini sagliyoruz
=======
    # Değişkenleri HTML şablonuna (Jinja2) gönderiyoruz.
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
    return render_template('index.html', ilanlar=ilanlar, 
                           iller=iller, lokasyon_agaci=lokasyon_agaci, odalar=odalar,
                           search_q=search_q, il_filtre=il_filtre, ilce_filtre=ilce_filtre, mahalle_filtre=mahalle_filtre,
                           oda_filtre=oda_filtre, fiyat_araligi=fiyat_araligi,
                           siralama=siralama, page=page, total_pages=total_pages, 
                           total_ilan=total_ilan, ortalama_fiyat=ortalama_fiyat, bolge_adi=bolge_adi)

# Projemiz dogrudan calistirilirsa flask sunucusunu ayaga kaldiriyoruz
if __name__ == '__main__':
<<<<<<< HEAD
    app.run(debug=True, port=5000, use_reloader=False)
=======
    # use_reloader=False: Flask'ın arka plan thread'iyle bot çalıştırırken çakışma/çift tetiklenme yapmasını engeller.
    # port=8080: Uygulamayı localhost:8080 portunda ayağa kaldırır.
    app.run(debug=True, port=8080, use_reloader=False)
>>>>>>> 901686982563c35bf74ba89b256a2ad221d48dc4
