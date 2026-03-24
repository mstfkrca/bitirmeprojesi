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

    # --- GET İsteği (Arama ve Filtreleme İşlemleri) ---
    search_q = request.args.get('q', '').strip()
    lokasyon_filtre = request.args.get('lokasyon', '').strip()
    oda_filtre = request.args.get('oda', '').strip()
    fiyat_araligi = request.args.get('fiyat_araligi', '').strip()
    
    page = request.args.get('page', 1, type=int)
    per_page = 15

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Dinamik Dropdown Seçeneklerini DB'den Çek (Benzersiz Lokasyon ve Oda)
    cursor.execute("SELECT DISTINCT lokasyon FROM ilanlar WHERE lokasyon IS NOT NULL AND lokasyon != '' AND lokasyon != '-'")
    lokasyonlar = [row[0] for row in cursor.fetchall() if row[0]]
    
    cursor.execute("SELECT DISTINCT oda_sayisi FROM ilanlar WHERE oda_sayisi IS NOT NULL AND oda_sayisi != '' AND oda_sayisi != '-'")
    odalar = [row[0] for row in cursor.fetchall() if row[0]]

    # Dinamik Filtreleme Sorgusu Oluştur
    query_conditions = "1=1"
    params = []

    if search_q:
        query_conditions += " AND (baslik LIKE ? OR aciklama LIKE ?)"
        params.extend([f"%{search_q}%", f"%{search_q}%"])

    if lokasyon_filtre:
        query_conditions += " AND lokasyon = ?"
        params.append(lokasyon_filtre)
        
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
    query = f"SELECT * FROM ilanlar WHERE {query_conditions} ORDER BY tarih DESC LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])
    
    cursor.execute(query, params)
    ilanlar = cursor.fetchall()
    conn.close()

    return render_template('index.html', ilanlar=ilanlar, 
                           lokasyonlar=lokasyonlar, odalar=odalar,
                           search_q=search_q, lokasyon_filtre=lokasyon_filtre, 
                           oda_filtre=oda_filtre, fiyat_araligi=fiyat_araligi,
                           page=page, total_pages=total_pages, total_ilan=total_ilan)

if __name__ == '__main__':
    app.run(debug=True, port=8080, use_reloader=False)