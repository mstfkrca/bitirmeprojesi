from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify, flash
from werkzeug.utils import secure_filename
import sqlite3
import os
import threading
import shutil # Klasör silme işlemi için
from scraper import botu_calistir
import database

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "emlak.db")
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")

# Veritabanını başlat
database.init_db()

app = Flask(__name__)
app.secret_key = "gizli_anahtar_emlak_avcisi_premium" # Flash mesajlar için gerekli

# Botun anlık durumunu tutan sözlük
bot_durumu = {"mesaj": "", "calisiyor": False}

def botu_arka_planda_calistir(link, limit):
    bot_durumu["calisiyor"] = True
    bot_durumu["mesaj"] = "⏳ Yapay Zeka botu engelleri aşıp ilanları analiz ediyor..."
    try:
        sonuc = botu_calistir(link, limit=limit)
        bot_durumu["mesaj"] = sonuc
    except Exception as e:
        bot_durumu["mesaj"] = f"❌ Hata: {str(e)}"
        print(f"🔥 Thread hatası: {e}")
    finally:
        bot_durumu["calisiyor"] = False

@app.route('/screenshots/<path:filename>')
def resim_goster(filename):
    # send_from_directory Flask kütüphanesi Path Traversal'ı kendi önler
    return send_from_directory(SCREENSHOTS_DIR, filename)

@app.route('/status')
def durum_kontrol():
    # AJAX üzerinden frontende anlık bilgi vermek için
    return jsonify(bot_durumu)

@app.route('/', methods=['GET', 'POST'])
def ana_sayfa():
    if request.method == 'POST':
        # BAŞLAT BUTONU
        if 'baslat' in request.form:
            link = request.form.get('ilan_linki')
            limit = request.form.get('limit', '200')
            limit = int(limit) if limit.isdigit() else 200
            if link and not bot_durumu["calisiyor"]:
                t = threading.Thread(target=botu_arka_planda_calistir, args=(link, limit))
                t.daemon = True
                t.start()
                flash("🚀 Bot başarıyla sahaya indi! Lütfen bekleyin.", "success")
        
        # SIFIRLA BUTONU (Tüm Arşivi Sil)
        elif 'temizle' in request.form:
            if not bot_durumu["calisiyor"]:
                try:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM ilanlar")
                    conn.commit()
                    conn.close()
                    
                    if os.path.exists(SCREENSHOTS_DIR):
                        shutil.rmtree(SCREENSHOTS_DIR)
                        os.makedirs(SCREENSHOTS_DIR)
                    
                    bot_durumu["mesaj"] = "✅ Tüm arşiv temizlendi."
                    flash("🗑️ Tüm arşiv, veritabanı ve resimler başarıyla sıfırlandı!", "success")
                except Exception as e:
                    flash(f"❌ Arşiv Silme Hatası: {str(e)}", "danger")

        # TEK BİR İLANI SİL
        elif 'tek_sil' in request.form:
            if not bot_durumu["calisiyor"]:
                ilan_id_to_delete = request.form.get('sil_ilan_id')
                if ilan_id_to_delete and ilan_id_to_delete.strip() != "":
                    # GÜVENLİK YAMASI: Sadece güvenilir path alınarak Traversal önlenir
                    guvenli_id = secure_filename(ilan_id_to_delete)
                    if guvenli_id:
                        try:
                            # 1. Veritabanından sil
                            conn = sqlite3.connect(DB_PATH)
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM ilanlar WHERE ilan_no = ?", (ilan_id_to_delete,))
                            conn.commit()
                            conn.close()
                            
                            # 2. Resim klasörünü sil (Mutlak Yol)
                            folder_path = os.path.join(SCREENSHOTS_DIR, guvenli_id)
                            if os.path.exists(folder_path):
                                shutil.rmtree(folder_path)
                            
                            flash(f"🗑️ İlan Numarası {guvenli_id} başarıyla silindi.", "success")
                        except Exception as e:
                            print(f"❌ Tekli Silme Hatası: {e}")
                            flash(f"❌ Kısmi Hata: {str(e)}", "danger")

        # Post sonrası yönlendirme yap ki F5 atınca tekrar Post atmasın
        return redirect(url_for('ana_sayfa'))

    search_q = request.args.get('q', '').strip()
    il_filtre = request.args.get('il', '').strip()
    ilce_filtre = request.args.get('ilce', '').strip()
    mahalle_filtre = request.args.get('mahalle', '').strip()
    oda_filtre = request.args.get('oda', '').strip()
    fiyat_araligi = request.args.get('fiyat_araligi', '').strip()
    siralama = request.args.get('siralama', 'tarih_yeni').strip()
    
    page = request.args.get('page', 1, type=int)
    per_page = 15

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Dinamik Dropdown Seçeneklerini DB'den Çek
    cursor.execute("SELECT DISTINCT lokasyon FROM ilanlar WHERE lokasyon IS NOT NULL AND lokasyon != '' AND lokasyon != '-'")
    ham_lokasyonlar = [row[0] for row in cursor.fetchall() if row[0]]
    
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
                
    # Set'leri listeye çevirelim ki HTML'de rahat dönelim
    iller = sorted(list(lokasyon_agaci.keys()))
    for il in lokasyon_agaci:
        for ilce in lokasyon_agaci[il]:
            lokasyon_agaci[il][ilce] = sorted(list(lokasyon_agaci[il][ilce]))
    
    cursor.execute("SELECT DISTINCT oda_sayisi FROM ilanlar WHERE oda_sayisi IS NOT NULL AND oda_sayisi != '' AND oda_sayisi != '-'")
    odalar = [row[0] for row in cursor.fetchall() if row[0]]

    # Dinamik Filtreleme Sorgusu Oluştur
    query_conditions = "1=1"
    params = []

    if search_q:
        query_conditions += " AND (baslik LIKE ? OR aciklama LIKE ?)"
        params.extend([f"%{search_q}%", f"%{search_q}%"])

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
        
    if oda_filtre:
        query_conditions += " AND oda_sayisi = ?"
        params.append(oda_filtre)

    if fiyat_araligi:
        if fiyat_araligi == "0-2M":
            query_conditions += " AND CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER) <= 2000000"
        elif fiyat_araligi == "2M-5M":
            query_conditions += " AND CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER) BETWEEN 2000000 AND 5000000"
        elif fiyat_araligi == "5M-10M":
            query_conditions += " AND CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER) BETWEEN 5000000 AND 10000000"
        elif fiyat_araligi == "10M+":
            query_conditions += " AND CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER) >= 10000000"

    # Toplam sonuç sayısını bul (Sayfalama için)
    cursor.execute(f"SELECT COUNT(*) FROM ilanlar WHERE {query_conditions}", params)
    total_ilan = cursor.fetchone()[0]
    total_pages = (total_ilan + per_page - 1) // per_page
    if page < 1: page = 1
    if page > total_pages and total_pages > 0: page = total_pages

    # 15 İlanı Limitle ve Getir
    order_clause = "tarih DESC"
    if siralama == "tarih_eski":
        order_clause = "tarih ASC"
    elif siralama == "fiyat_artan":
        order_clause = "CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER) ASC"
    elif siralama == "fiyat_azalan":
        order_clause = "CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER) DESC"

    query = f"SELECT * FROM ilanlar WHERE {query_conditions} ORDER BY {order_clause} LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])
    
    cursor.execute(query, params)
    ilanlar = cursor.fetchall()
    
    # Ortalama Fiyat Hesaplama
    ortalama_fiyat = None
    bolge_adi = None
    if il_filtre:
        bolge_adi = f"{il_filtre} İli"
        if ilce_filtre:
            bolge_adi = f"{ilce_filtre}"
            if mahalle_filtre:
                bolge_adi = f"{mahalle_filtre}"
            
        avg_query = f"SELECT AVG(CAST(REPLACE(REPLACE(fiyat, '.', ''), ' TL', '') AS INTEGER)) FROM ilanlar WHERE {query_conditions} AND fiyat IS NOT NULL AND fiyat != 'Fiyat Yok' AND fiyat != ''"
        # We need to use params without the limit/offset for the average
        avg_params = params[:-2] 
        cursor.execute(avg_query, avg_params)
        avg_result = cursor.fetchone()[0]
        if avg_result:
            ortalama_fiyat = f"{int(avg_result):,} TL".replace(',', '.')
            
    conn.close()

    return render_template('index.html', ilanlar=ilanlar, 
                           iller=iller, lokasyon_agaci=lokasyon_agaci, odalar=odalar,
                           search_q=search_q, il_filtre=il_filtre, ilce_filtre=ilce_filtre, mahalle_filtre=mahalle_filtre,
                           oda_filtre=oda_filtre, fiyat_araligi=fiyat_araligi,
                           siralama=siralama, page=page, total_pages=total_pages, 
                           total_ilan=total_ilan, ortalama_fiyat=ortalama_fiyat, bolge_adi=bolge_adi)

if __name__ == '__main__':
    app.run(debug=True, port=8080, use_reloader=False)