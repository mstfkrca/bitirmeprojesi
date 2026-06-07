from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify, flash
from werkzeug.utils import secure_filename
import sqlite3
import os
import threading
import shutil # Klasörleri ve içindekileri tamamen silmek için kullanılan kütüphane
from scraper import botu_calistir
import database

# Projenin ana çalışma dizinini ve alt yollarını tanımlıyoruz.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "emlak.db")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")

# Uygulama her başladığında veritabanı dosyasının ve tablolarının varlığını kontrol edip yoksa oluşturuyor.
database.init_db()

app = Flask(__name__)
# Flask üzerinde flash mesajlarını (bildirim pencerelerini) kullanabilmek için şifreleme anahtarı (secret key) tanımlıyoruz.
app.secret_key = "gizli_anahtar_emlak_avcisi_premium" 

# Arka planda çalışan Selenium botunun durumunu ve mesajını tutan küresel (global) sözlük.
# Arayüzdeki JavaScript (AJAX) burayı sorgulayarak ekranda anlık yüklenme durumunu gösterir.
bot_durumu = {"mesaj": "", "calisiyor": False}

def botu_arka_planda_calistir(link, limit):
    # Botun çalışmaya başladığını işaretliyoruz.
    bot_durumu["calisiyor"] = True
    bot_durumu["mesaj"] = "⏳ Yapay Zeka botu engelleri aşıp ilanları analiz ediyor..."
    try:
        # scraper.py içindeki ana tarama fonksiyonunu çağırıyoruz.
        sonuc = botu_calistir(link, limit=limit)
        bot_durumu["mesaj"] = sonuc
    except Exception as e:
        bot_durumu["mesaj"] = f"❌ Hata: {str(e)}"
        print(f"🔥 Thread hatası: {e}")
    finally:
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
@app.route('/', methods=['GET', 'POST'])
def ana_sayfa():
    if request.method == 'POST':
        # --- BOTU BAŞLATMA İŞLEMİ ---
        if 'baslat' in request.form:
            link = request.form.get('ilan_linki')
            limit = request.form.get('limit', '200')
            limit = int(limit) if limit.isdigit() else 200
            
            # Bot zaten çalışmıyorsa yeni bir iş parçacığı (Thread) oluşturup başlatıyoruz.
            if link and not bot_durumu["calisiyor"]:
                t = threading.Thread(target=botu_arka_planda_calistir, args=(link, limit))
                # daemon=True: Ana Flask uygulaması kapatıldığında bu thread'in de arka planda çalışmaya devam edip
                # işletim sisteminde "zombi süreç" oluşturmasını önler, otomatik sonlandırır.
                t.daemon = True
                t.start()
                flash("🚀 Bot başarıyla sahaya indi! Lütfen bekleyin.", "success")
        
        # --- VERİTABANI VE ARŞİVİ SIFIRLAMA İŞLEMİ ---
        elif 'temizle' in request.form:
            if not bot_durumu["calisiyor"]:
                try:
                    # SQLite veritabanındaki tüm ilanları siliyoruz.
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM ilanlar")
                    conn.commit()
                    conn.close()
                    
                    # Disk üzerindeki screenshots klasörünü komple silip sıfırdan boş oluşturuyoruz.
                    if os.path.exists(SCREENSHOT_DIR):
                        shutil.rmtree(SCREENSHOT_DIR)
                        os.makedirs(SCREENSHOT_DIR)
                    
                    bot_durumu["mesaj"] = "✅ Tüm arşiv temizlendi."
                    flash("🗑️ Tüm arşiv, veritabanı ve resimler başarıyla sıfırlandı!", "success")
                except Exception as e:
                    flash(f"❌ Arşiv Silme Hatası: {str(e)}", "danger")

        # --- TEK BİR İLANI SİLME İŞLEMİ ---
        elif 'tek_sil' in request.form:
            if not bot_durumu["calisiyor"]:
                ilan_id_to_delete = request.form.get('sil_ilan_id')
                if ilan_id_to_delete and ilan_id_to_delete.strip() != "":
                    # GÜVENLİK YAMASI: secure_filename fonksiyonu dosya adındaki tehlikeli karakterleri (örneğin "../")
                    # temizleyerek Path Traversal (başka sistem klasörlerini silme) saldırılarını engeller.
                    guvenli_id = secure_filename(ilan_id_to_delete)
                    if guvenli_id:
                        try:
                            # 1. Veritabanından ilgili ilanı siliyoruz (parametrik sorgu ile SQL injection korumalı).
                            conn = sqlite3.connect(DB_PATH)
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM ilanlar WHERE ilan_no = ?", (ilan_id_to_delete,))
                            conn.commit()
                            conn.close()
                            
                            # 2. İlana ait ekran görüntüsü klasörünü diskten siliyoruz.
                            folder_path = os.path.join(SCREENSHOT_DIR, guvenli_id)
                            if os.path.exists(folder_path):
                                shutil.rmtree(folder_path)
                            
                            flash(f"🗑️ İlan Numarası {guvenli_id} başarıyla silindi.", "success")
                        except Exception as e:
                            print(f"❌ Tekli Silme Hatası: {e}")
                            flash(f"❌ Kısmi Hata: {str(e)}", "danger")

        # POST-REDIRECT-GET (PRG) DESENİ:
        # POST işlemi bittikten sonra sayfayı ana sayfaya yönlendiriyoruz (Redirect).
        # Böylece kullanıcı arayüzde F5 (sayfa yenileme) yaptığında tarayıcı aynı POST isteğini tekrar gönderip
        # yanlışlıkla botu yeniden başlatmaz veya silme işlemini tekrarlamaz.
        return redirect(url_for('ana_sayfa'))

    # --- GET İSTEĞİ (ARAMA, FİLTRELEME VE SAYFALAMA) ---
    search_q = request.args.get('q', '').strip()
    il_filtre = request.args.get('il', '').strip()
    ilce_filtre = request.args.get('ilce', '').strip()
    mahalle_filtre = request.args.get('mahalle', '').strip()
    oda_filtre = request.args.get('oda', '').strip()
    fiyat_araligi = request.args.get('fiyat_araligi', '').strip()
    siralama = request.args.get('siralama', 'tarih_yeni').strip()
    
    page = request.args.get('page', 1, type=int)
    per_page = 15 # Sayfa başına gösterilecek ilan sayısı

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Veritabanından gelen satırları sözlük (key-value) şeklinde okuyabilmek için Row yapısını aktif ediyoruz.
    cursor = conn.cursor()
    
    # --- DİNAMİK LOKASYON AĞACI OLUŞTURMA (JS DROPDOWN'LAR İÇİN) ---
    # Veritabanında kayıtlı olan benzersiz lokasyonları (örn: "İstanbul/Kadıköy/Caferağa") çekiyoruz.
    cursor.execute("SELECT DISTINCT lokasyon FROM ilanlar WHERE lokasyon IS NOT NULL AND lokasyon != '' AND lokasyon != '-'")
    ham_lokasyonlar = [row[0] for row in cursor.fetchall() if row[0]]
    
    # JavaScript tarafında dinamik il->ilçe->mahalle ilişkisini kurabilmek için lokasyonları ağaç yapısına (Sözlük) dönüştürüyoruz.
    lokasyon_agaci = {}
    
    for lok in ham_lokasyonlar:
        parts = lok.split('/')
        if len(parts) >= 1:
            il = parts[0].strip()
            if il not in lokasyon_agaci:
                lokasyon_agaci[il] = {}
                
            if len(parts) >= 2:
                ilce = parts[1].strip()
                if ilce not in lokasyon_agaci[il]:
                    lokasyon_agaci[il][ilce] = set()
                    
                if len(parts) >= 3:
                    mahalle = parts[2].strip()
                    lokasyon_agaci[il][ilce].add(mahalle)
                
    # JavaScript'in okuması kolay olsun diye Set'leri sıralı listeye dönüştürüyoruz.
    iller = sorted(list(lokasyon_agaci.keys()))
    for il in lokasyon_agaci:
        for ilce in lokasyon_agaci[il]:
            lokasyon_agaci[il][ilce] = sorted(list(lokasyon_agaci[il][ilce]))
    
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
    if search_q:
        query_conditions += " AND (baslik LIKE ? OR aciklama LIKE ?)"
        params.extend([f"%{search_q}%", f"%{search_q}%"])

    # Lokasyon (İl, İlçe, Mahalle) hiyerarşik filtresi
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
        
    # Oda sayısı filtresi
    if oda_filtre:
        query_conditions += " AND oda_sayisi = ?"
        params.append(oda_filtre)

    # --- METİNSEL FİYATI SAYISALA ÇEVİRİP FİLTRELEME (CAST/REPLACE) ---
    # Fiyat veritabanında "2.500.000 TL" şeklinde metindir. Matematiksel karşılaştırma yapabilmek için:
    # 1. REPLACE ile nokta ('.') ve ' TL' kısımlarını temizliyoruz.
    # 2. CAST(... AS INTEGER) ile sayıyı tamsayıya dönüştürüp aralık kontrolü yapıyoruz.
    if fiyat_araligi:
        if fiyat_araligi == "0-2M":
            query_conditions += " AND CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER) <= 2000000"
        elif fiyat_araligi == "2M-5M":
            query_conditions += " AND CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER) BETWEEN 2000000 AND 5000000"
        elif fiyat_araligi == "5M-10M":
            query_conditions += " AND CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER) BETWEEN 5000000 AND 10000000"
        elif fiyat_araligi == "10M+":
            query_conditions += " AND CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER) >= 10000000"

    # --- SAYFALAMA (PAGINATION) HESAPLAMA ---
    # Seçilen kriterlere uyan toplam ilan sayısını buluyoruz.
    cursor.execute(f"SELECT COUNT(*) FROM ilanlar WHERE {query_conditions}", params)
    total_ilan = cursor.fetchone()[0]
    total_pages = (total_ilan + per_page - 1) // per_page
    
    # Sayfa sınırlarının dışına çıkılmasını önlüyoruz.
    if page < 1: 
        page = 1
    if page > total_pages and total_pages > 0: 
        page = total_pages

    # --- SIRALAMA (ORDER BY) İŞLEMLERİ ---
    order_clause = "tarih DESC" # Varsayılan olarak en son eklenen ilan en üstte görünür.
    if siralama == "tarih_eski":
        order_clause = "tarih ASC"
    elif siralama == "fiyat_artan":
        order_clause = "CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER) ASC"
    elif siralama == "fiyat_azalan":
        order_clause = "CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER) DESC"

    # --- SAYFALAMA LİMİTLEME SORGUSU (LIMIT & OFFSET) ---
    # LIMIT: Sadece sayfa başına gösterilecek adet kadar veri çeker.
    # OFFSET: Önceki sayfaların verilerini atlayarak hedef sayfa verisinin başlamasını sağlar.
    query = f"SELECT * FROM ilanlar WHERE {query_conditions} ORDER BY {order_clause} LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])
    
    cursor.execute(query, params)
    ilanlar = cursor.fetchall()
    
    # --- ORTALAMA BÖLGESEL FİYAT HESAPLAMA ---
    # Kullanıcı bir il filtrelediğinde, o bölgedeki ortalama ev fiyatını hesaplayıp ekranda istatistik olarak gösteriyoruz.
    ortalama_fiyat = None
    bolge_adi = None
    if il_filtre:
        bolge_adi = f"{il_filtre} İli"
        if ilce_filtre:
            bolge_adi = f"{ilce_filtre}"
            if mahalle_filtre:
                bolge_adi = f"{mahalle_filtre}"
            
        # Ortalama almak için SQL'in AVG() fonksiyonunu kullanıyoruz. Fiyatı temizleyerek sayıya çeviriyoruz.
        avg_query = f"SELECT AVG(CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER)) FROM ilanlar WHERE {query_conditions} AND fiyat IS NOT NULL AND fiyat != 'Fiyat Yok' AND fiyat != ''"
        # LIMIT ve OFFSET parametrelerini bu sorguda kullanmayacağımız için params listesinden çıkarıyoruz.
        avg_params = params[:-2] 
        cursor.execute(avg_query, avg_params)
        avg_result = cursor.fetchone()[0]
        if avg_result:
            # Çıkan sonucu binlik ayraca göre formatlayıp (örn: 2.340.000 TL) arayüze gönderiyoruz.
            ortalama_fiyat = f"{int(avg_result):,} TL".replace(',', '.')
            
    conn.close()

    # Değişkenleri HTML şablonuna (Jinja2) gönderiyoruz.
    return render_template('index.html', ilanlar=ilanlar, 
                           iller=iller, lokasyon_agaci=lokasyon_agaci, odalar=odalar,
                           search_q=search_q, il_filtre=il_filtre, ilce_filtre=ilce_filtre, mahalle_filtre=mahalle_filtre,
                           oda_filtre=oda_filtre, fiyat_araligi=fiyat_araligi,
                           siralama=siralama, page=page, total_pages=total_pages, 
                           total_ilan=total_ilan, ortalama_fiyat=ortalama_fiyat, bolge_adi=bolge_adi)

if __name__ == '__main__':
    # use_reloader=False: Flask'ın arka plan thread'iyle bot çalıştırırken çakışma/çift tetiklenme yapmasını engeller.
    # port=8080: Uygulamayı localhost:8080 portunda ayağa kaldırır.
    app.run(debug=True, port=8080, use_reloader=False)