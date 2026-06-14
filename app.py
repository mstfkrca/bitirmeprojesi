# Gerekli kutuphaneleri projeye dahil ediyoruz
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify, flash
from werkzeug.utils import secure_filename
import sqlite3
import os
import threading
import shutil # Dosya ve klasor silme islemleri icin eklendi
from scraper import botu_calistir
import database

# Projenin calistigi ana dizini belirliyoruz
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Veritabaninin kaydedilecegi tam yolu ayarladik
DB_PATH = os.path.join(BASE_DIR, "emlak.db")
# Botun cektigi ekran goruntulerini saklayacagimiz klasorun yolunu belirttik
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")

# Veritabani dosyasi yoksa bastan olusturuyoruz
database.init_db()

# Flask web uygulamamizi baslatiyoruz
app = Flask(__name__)
# Kullaniciya gosterilecek bildirim mesajlari icin gizli bir anahtar belirledik
app.secret_key = "gizli_anahtar_emlak_avcisi_premium" 

# Botun arka planda calisip calismadigini ve anlik durumunu bu sozluk uzerinden takip ediyoruz
bot_durumu = {"mesaj": "", "calisiyor": False}

# Arayuz donmasin diye botu ayri bir is parcaciginda arka planda calistiran fonksiyonumuz
def botu_arka_planda_calistir(link, limit):
    # Botun calismaya basladigini sisteme bildiriyoruz
    bot_durumu["calisiyor"] = True
    bot_durumu["mesaj"] = "Yapay zeka botu islemlere basliyor lutfen bekleyin"
    try:
        # Scraper dosyasindaki gercek bot fonksiyonunu cagiriyoruz
        sonuc = botu_calistir(link, limit=limit)
        # Islem bitince botun dondugu mesaji duruma yaziyoruz
        bot_durumu["mesaj"] = sonuc
    except Exception as e:
        # Eger bir hata cikarsa bunu kaydediyoruz
        bot_durumu["mesaj"] = f"Bir hata olustu: {str(e)}"
        print(f"Arka plan isleminde hata: {e}")
    finally:
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
@app.route('/', methods=['GET', 'POST'])
def ana_sayfa():
    # Eger kullanici arayuzden bir butona basmissa bu kisim calisir
    if request.method == 'POST':
        
        # Kullanici botu baslatma butonuna basmissa
        if 'baslat' in request.form:
            # Formdan gelen linki ve limiti aliyoruz
            link = request.form.get('ilan_linki')
            limit = request.form.get('limit', '200')
            # Limit eger sayi degilse varsayilan olarak iki yuz yapiyoruz
            limit = int(limit) if limit.isdigit() else 200
            
            # Eger gecerli bir link varsa ve bot su an baska bir islem yapmiyorsa
            if link and not bot_durumu["calisiyor"]:
                # Botu arka planda baslatiyoruz boylece web sitemiz donmuyor
                t = threading.Thread(target=botu_arka_planda_calistir, args=(link, limit))
                t.daemon = True
                t.start()
                # Kullaniciya isin basladigina dair bilgi veriyoruz
                flash("Bot islemleri basladi lutfen sonuclanmasini bekleyin", "success")
        
        # Kullanici arsivi tamamen temizle butonuna basmissa
        elif 'temizle' in request.form:
            # Eger bot arka planda islem yapmiyorsa verileri siliyoruz
            if not bot_durumu["calisiyor"]:
                try:
                    # Veritabanina baglanip tum ilanlari siliyoruz
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM ilanlar")
                    conn.commit()
                    conn.close()
                    
                    # Indirilmis olan tum ekran goruntusu klasorlerini komple silip yeniden bos bir klasor aciyoruz
                    if os.path.exists(SCREENSHOTS_DIR):
                        shutil.rmtree(SCREENSHOTS_DIR)
                        os.makedirs(SCREENSHOTS_DIR)
                    
                    # Sisteme her seyin temizlendigi bilgisini geciyoruz
                    bot_durumu["mesaj"] = "Tum veriler ve resimler temizlendi"
                    flash("Sistemdeki tum veriler ve resimler basariyla temizlendi", "success")
                except Exception as e:
                    # Silme isleminde bir terslik olursa ekrana hata donduruyoruz
                    flash(f"Arsivi silerken bir problem yasandi: {str(e)}", "danger")

        # Kullanici sadece tek bir ilani silmek isterse
        elif 'tek_sil' in request.form:
            # Bot calismiyorken silme islemine izin veriyoruz
            if not bot_durumu["calisiyor"]:
                ilan_id_to_delete = request.form.get('sil_ilan_id')
                if ilan_id_to_delete and ilan_id_to_delete.strip() != "":
                    # Gelen id bilgisini guvenli hale getiriyoruz ki sistem klasorlerine sizilamasin
                    guvenli_id = secure_filename(ilan_id_to_delete)
                    if guvenli_id:
                        try:
                            # Veritabanindan o ilana ait olan satiri kaldiriyoruz
                            conn = sqlite3.connect(DB_PATH)
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM ilanlar WHERE ilan_no = ?", (ilan_id_to_delete,))
                            conn.commit()
                            conn.close()
                            
                            # O ilana ait olan resim klasorunu bularak siliyoruz
                            folder_path = os.path.join(SCREENSHOTS_DIR, guvenli_id)
                            if os.path.exists(folder_path):
                                shutil.rmtree(folder_path)
                            
                            flash(f"Ilan sistemden basariyla kaldirildi", "success")
                        except Exception as e:
                            print(f"Ilan silinirken bir hata olustu: {e}")
                            flash(f"Silme isleminde hata yasandi: {str(e)}", "danger")

        # Islemler bittikten sonra sayfayi yeniliyoruz ki kullanici sayfayi yenileyince tekrar form gondermesin
        return redirect(url_for('ana_sayfa'))

    # Buradan sonrasi sayfa normal bir sekilde acildiginda veya arama yapildiginda calisir
    # URL uzerinden gelen arama ve filtreleme parametrelerini aliyoruz
    search_q = request.args.get('q', '').strip()
    il_filtre = request.args.get('il', '').strip()
    ilce_filtre = request.args.get('ilce', '').strip()
    mahalle_filtre = request.args.get('mahalle', '').strip()
    oda_filtre = request.args.get('oda', '').strip()
    fiyat_araligi = request.args.get('fiyat_araligi', '').strip()
    siralama = request.args.get('siralama', 'tarih_yeni').strip()
    
    # Sayfalama islemi icin gecerli sayfa numarasini aliyoruz varsayilan olarak birinci sayfa
    page = request.args.get('page', 1, type=int)
    # Her sayfada on bes ilan gosterilmesini sagliyoruz
    per_page = 15

    # Veritabanina okuma islemleri icin baglanti aciyoruz
    conn = sqlite3.connect(DB_PATH)
    # Satirlari sozluk gibi cekebilmek icin bu ayari yapiyoruz
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Menulerde gostermek uzere kayitli ilanlarin bulundugu sehir ve ilceleri cekiyoruz
    cursor.execute("SELECT DISTINCT lokasyon FROM ilanlar WHERE lokasyon IS NOT NULL AND lokasyon != '' AND lokasyon != '-'")
    ham_lokasyonlar = [row[0] for row in cursor.fetchall() if row[0]]
    
    # Il ilce ve mahalleleri birbiri icinde hiyerarsik olarak tutacagimiz bir sozluge atiyoruz
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
                
    # HTML tarafinda rahat listeleme yapabilmek icin kumeleri normal listeye ceviriyoruz
    iller = sorted(list(lokasyon_agaci.keys()))
    for il in lokasyon_agaci:
        for ilce in lokasyon_agaci[il]:
            lokasyon_agaci[il][ilce] = sorted(list(lokasyon_agaci[il][ilce]))
    
    # Ayni islemi oda sayisi secenekleri icin de yapiyoruz farkli oda tiplerini listeliyoruz
    cursor.execute("SELECT DISTINCT oda_sayisi FROM ilanlar WHERE oda_sayisi IS NOT NULL AND oda_sayisi != '' AND oda_sayisi != '-'")
    odalar = [row[0] for row in cursor.fetchall() if row[0]]

    # Kullanicinin sectigi filtrelere gore veritabaninda arama yapacak sorguyu hazirliyoruz
    query_conditions = "1=1"
    params = []

    # Arama kutusuna bir sey yazildiysa hem baslikta hem aciklamada ariyoruz
    if search_q:
        query_conditions += " AND (baslik LIKE ? OR aciklama LIKE ?)"
        params.extend([f"%{search_q}%", f"%{search_q}%"])

    # Eger bolge secildiyse sirasiyla sehir ilce veya mahalleye gore sorguyu daraltiyoruz
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
        
    # Eger oda sayisi secildiyse sadece o oda sayisina sahip ilanlari istiyoruz
    if oda_filtre:
        query_conditions += " AND oda_sayisi = ?"
        params.append(oda_filtre)

    # Kullanici fiyat araligi secmisse fiyati sayiya cevirip araliga gore filtreliyoruz
    if fiyat_araligi:
        if fiyat_araligi == "0-2M":
            query_conditions += " AND CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER) <= 2000000"
        elif fiyat_araligi == "2M-5M":
            query_conditions += " AND CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER) BETWEEN 2000000 AND 5000000"
        elif fiyat_araligi == "5M-10M":
            query_conditions += " AND CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER) BETWEEN 5000000 AND 10000000"
        elif fiyat_araligi == "10M+":
            query_conditions += " AND CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER) >= 10000000"

    # Filtrelere uyan toplam kac tane ilan oldugunu sayiyoruz ki asagiya sayfa numaralarini dizebilelim
    cursor.execute(f"SELECT COUNT(*) FROM ilanlar WHERE {query_conditions}", params)
    total_ilan = cursor.fetchone()[0]
    
    # Toplam sayfa sayisini hesapliyoruz
    total_pages = (total_ilan + per_page - 1) // per_page
    if page < 1: page = 1
    if page > total_pages and total_pages > 0: page = total_pages

    # Istenen siralama yonune gore sonuclari duzenliyoruz
    order_clause = "tarih DESC"
    if siralama == "tarih_eski":
        order_clause = "tarih ASC"
    elif siralama == "fiyat_artan":
        order_clause = "CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER) ASC"
    elif siralama == "fiyat_azalan":
        order_clause = "CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER) DESC"

    # Filtrelerimize uygun olan ilanlari veritabanindan limitli olarak cekiyoruz
    query = f"SELECT * FROM ilanlar WHERE {query_conditions} ORDER BY {order_clause} LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])
    
    cursor.execute(query, params)
    ilanlar = cursor.fetchall()
    
    # Secilen bolgeye ait ortalama bir fiyat bilgisi sunmak icin hesaplama yapiyoruz
    ortalama_fiyat = None
    bolge_adi = None
    if il_filtre:
        bolge_adi = f"{il_filtre} Ili"
        if ilce_filtre:
            bolge_adi = f"{ilce_filtre}"
            if mahalle_filtre:
                bolge_adi = f"{mahalle_filtre}"
            
        # Filtrelere uyan kayitlarin fiyat ortalamasini aliyoruz
        avg_query = f"SELECT AVG(CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER)) FROM ilanlar WHERE {query_conditions} AND fiyat IS NOT NULL AND fiyat != 'Fiyat Yok' AND fiyat != ''"
        avg_params = params[:-2] 
        cursor.execute(avg_query, avg_params)
        avg_result = cursor.fetchone()[0]
        if avg_result:
            # Cikan ortalamayi okunabilir bir formata ceviriyoruz
            ortalama_fiyat = f"{int(avg_result):,} TL".replace(',', '.')
            
    conn.close()

    # Toplanan tum verileri html sablonuna gondererek web sayfamizin basilmasini sagliyoruz
    return render_template('index.html', ilanlar=ilanlar, 
                           iller=iller, lokasyon_agaci=lokasyon_agaci, odalar=odalar,
                           search_q=search_q, il_filtre=il_filtre, ilce_filtre=ilce_filtre, mahalle_filtre=mahalle_filtre,
                           oda_filtre=oda_filtre, fiyat_araligi=fiyat_araligi,
                           siralama=siralama, page=page, total_pages=total_pages, 
                           total_ilan=total_ilan, ortalama_fiyat=ortalama_fiyat, bolge_adi=bolge_adi)

# Projemiz dogrudan calistirilirsa flask sunucusunu ayaga kaldiriyoruz
if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False)