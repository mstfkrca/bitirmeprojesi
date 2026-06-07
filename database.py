import sqlite3
import os

# Projenin çalıştığı klasörün tam yolunu alıyoruz. 
# Böylece dosyaları kaydederken veya okurken işletim sisteminden bağımsız olarak hep doğru klasörü (proje kök dizinini) hedeflemiş oluyoruz.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Veritabanını ve gerekli tabloları sıfırdan oluşturan fonksiyon
def init_db():
    # emlak.db adında bir SQLite veritabanı dosyası oluşturuyor ve bağlanıyor.
    # Dosya zaten varsa sadece bağlantı kurar, yoksa sıfırdan oluşturur.
    conn = sqlite3.connect(os.path.join(BASE_DIR, "emlak.db"))
    cursor = conn.cursor() # Veritabanı üzerinde SQL komutları çalıştırabilmek için imleç (cursor) oluşturuyoruz.
    
    # 'ilanlar' adında bir tablo yoksa oluşturuyoruz. (IF NOT EXISTS hata almayı önler)
    # Burada ilanların detaylı tüm teknik özellikleri sütun olarak tanımlanmıştır.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ilanlar (
            # Her kayda otomatik artan benzersiz bir sayısal kimlik veriyoruz.
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            # Sahibinden üzerindeki ilan numarasını tutar. 
            # UNIQUE (benzersiz) yaptık; böylece aynı ilan veritabanına ikinci kez kaydedilmeye çalışıldığında hata verir ve duplikasyonu engeller.
            ilan_no TEXT UNIQUE,
            
            # İlanın başlığı, fiyat bilgisi ve orijinal web adresi
            baslik TEXT,
            fiyat TEXT,
            link TEXT,
            
            # İndirilen ekran görüntüsünün yerel diskteki klasör yolu
            resim_yolu TEXT,
            
            # İlanın uzun açıklama metni ve konumu (İl/İlçe/Mahalle formatında)
            aciklama TEXT,
            lokasyon TEXT,
            
            # İlanın sitedeki yayınlanma tarihi ve konut/iş yeri gibi tipi
            ilan_tarihi TEXT,
            emlak_tipi TEXT,
            
            # Metrekare cinsinden alan bilgileri
            m2_brut TEXT,
            m2_net TEXT,
            
            # Oda sayısı (örn: 3+1) ve binanın yapımından geçen yıl
            oda_sayisi TEXT,
            bina_yasi TEXT,
            
            # Dairenin kaçıncı katta olduğu ve binanın toplam kat sayısı
            bulundugu_kat TEXT,
            kat_sayisi TEXT,
            
            # Isınma tipi (doğalgaz vb.) ve banyo sayısı
            isitma TEXT,
            banyo_sayisi TEXT,
            
            # Diğer fiziksel nitelikler
            mutfak TEXT,
            balkon TEXT,
            asansor TEXT,
            otopark TEXT,
            esyali TEXT,
            kullanim_durumu TEXT,
            
            # Siteye dair bilgiler
            site_icerisinde TEXT,
            site_adi TEXT,
            
            # Finansal ve hukuki detaylar
            aidat TEXT,
            krediye_uygun TEXT,
            tapu_durumu TEXT,
            
            # İlanı koyan kişi (sahibinden, emlak ofisinden vb.) ve takas durumu
            kimden TEXT,
            takas TEXT,
            
            # İlanın bizim sistemimiz tarafından veritabanına kaydedildiği tarih ve saat.
            # DEFAULT CURRENT_TIMESTAMP sayesinde herhangi bir tarih göndermesek bile SQL o anki zamanı otomatik yazar.
            tarih DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit() # Değişiklikleri veritabanına kalıcı olarak işliyoruz.
    conn.close()  # Veritabanı bağlantısını kapatarak kaynakları serbest bırakıyoruz.
    print("✅ Veritabanı (emlak.db) en güncel ilan tarihi yapısıyla hazırlandı.")

# database.py dosyası doğrudan çalıştırıldığında (import edilmeden) eski veritabanını silip temiz bir başlangıç yapar.
if __name__ == "__main__":
    db_yolu = os.path.join(BASE_DIR, "emlak.db")
    if os.path.exists(db_yolu):
        os.remove(db_yolu) # Eğer eski bir veritabanı dosyası varsa siliyoruz.
        print("Eski emlak.db silindi.")
    init_db() # Veritabanını sıfırdan oluşturuyoruz.