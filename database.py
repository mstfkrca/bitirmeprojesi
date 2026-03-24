import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def init_db():
    conn = sqlite3.connect(os.path.join(BASE_DIR, "emlak.db"))
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ilanlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ilan_no TEXT UNIQUE,
            baslik TEXT,
            fiyat TEXT,
            link TEXT,
            resim_yolu TEXT,
            aciklama TEXT,
            lokasyon TEXT,
            ilan_tarihi TEXT,
            emlak_tipi TEXT,
            m2_brut TEXT,
            m2_net TEXT,
            oda_sayisi TEXT,
            bina_yasi TEXT,
            bulundugu_kat TEXT,
            kat_sayisi TEXT,
            isitma TEXT,
            banyo_sayisi TEXT,
            mutfak TEXT,
            balkon TEXT,
            asansor TEXT,
            otopark TEXT,
            esyali TEXT,
            kullanim_durumu TEXT,
            site_icerisinde TEXT,
            site_adi TEXT,
            aidat TEXT,
            krediye_uygun TEXT,
            tapu_durumu TEXT,
            kimden TEXT,
            takas TEXT,
            tarih DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("✅ Veritabanı (emlak.db) en güncel ilan tarihi yapısıyla hazırlandı.")

if __name__ == "__main__":
    db_yolu = os.path.join(BASE_DIR, "emlak.db")
    if os.path.exists(db_yolu):
        os.remove(db_yolu)
        print("Eski emlak.db silindi.")
    init_db()