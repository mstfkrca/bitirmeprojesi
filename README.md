# 🏡 Emlak Avcısı Pro (Premium Web Arayüzlü Sürüm)

**Emlak Avcısı Pro**, emlak sitelerindeki (sahibinden.com) satılık/kiralık ilanlarını belirlediğiniz arama filtrelerine göre otomatik tarayan, veri madenciliği yapan, ilan detaylarını ve görsellerini indirerek modern ve ultra-hızlı bir web panelinde sunan otomasyon aracıdır. Gelişmiş "Glassmorphism" tasarımı ve yepyeni özellikleri ile veritabanınızı saniyeler içinde süzebilirsiniz.

![Python](https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Frontend-Flask-black?style=for-the-badge&logo=flask)
![SeleniumBase](https://img.shields.io/badge/Bot-SeleniumBase-green?style=for-the-badge&logo=selenium)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey?style=for-the-badge&logo=sqlite)

---

## ✨ Öne Çıkan Özellikler

* **Otonom Veri Madenciliği:** İlan bağlantısını (URL) ve limiti girin, arkanıza yaslanın. SeleniumBase (Undetected ChromeDriver) kalkanı sayesinde Cloudflare geçilerek; İlan No, M², Fiyat, Oda Sayısı, Bina Yaşı, Otopark, Isıtma vb. veriler indirilir.
* **Premium ve Stabil Arayüz (UI):** Apple tarzı şık "Glassmorphism" tasarım kullanılmıştır. Site donmadan AJAX ile anlık yapay zeka analiz ve bot durumunu sağ köşeden takip edebilirsiniz.
* **Akıllı Filtreleme ve Sayfalama:** Odanıza ve İl/İlçeye göre veritabanından dinamik olarak çekilen Dropdown yapısı ile kolayca arama yapın. Fiyat aralıklarını (0-2M, 5-10M vb) anında süzün. Her sayfa sunucuyu yormadan 15 ilan gösterir (Pagination).
* **100x Hızlandırılmış Veritabanı:** 100 ilanı tararken SQL bağlantısını 100 defa aç/kapa yapmak yerine, In-Memory Set özelliği sayesinde arka planda saniyenin binde biri süresinde "önceden taranmış mı" kontrolü yapar. Hızlı ve yormaz.
* **Güvenli Dosya Yönetimi:** Flask Werkzeug yardımı ve mutlak yol güvenlik kalkanı sayesinde (Path Traversal önlemli) tek tuşla tüm arşivi veya sadece istenilen bir ilanı, sisteme zarar vermeden görselleriyle beraber silebilirsiniz.

---

## 📂 Proje Yapısı

```text
EmlakAvcisiPro/
├── app.py           # Web Sunucusu ve API Backend (Flask 8080 port)
├── scraper.py       # Veri Kazıma/Bot Motoru (SeleniumBase & BeautifulSoup)
├── database.py      # SQLite Tablolarının Kurulumu (Otomatik Bağlantı Yolu)
├── emlak.db         # Veritabanı dosyası (Uygulama çalışınca otomatik oluşur)
├── requirements.txt # Gerekli kütüphaneler listesi (Pip)
├── templates/       # (HTML Şablonları)
│   └── index.html   # Glassmorphism ön yüz tasarımı ve AJAX Scriptleri
└── screenshots/     # İndirilen ilan resimleri (Arşiv)
```

---

## 🛠️ Kurulum ve Çalıştırma

Kendi local ortamınızda (Localhost) kurulum yapmak veya sunucunuzda ayağa kaldırmak için adım adım şu talimatları izleyin:

### 1. Gereksinimleri Yükleyin
Bilgisayarınızda **Python 3.9 veya daha güncel bir sürümü** olduğunu teyit edin. Projeyi indirdikten veya klonladıktan sonra terminalden (veya komut satırından) proje dizinine girin ve gerekli kütüphaneleri yükleyin:

```bash
pip install -r requirements.txt
```

> **Not:** SeleniumBase kütüphanesinin sorunsuz bir şekilde webi tarayabilmesi için bilgisayarınızda Chromium tabanlı bir tarayıcı (Brave, Chrome veya Edge) bulunması gerekmektedir. 

### 2. Tarayıcı Ayarı (Önemli Not!)
Bot, bot kalkanlarını aşma performansı daha yüksek olduğundan dolayı varsayılan olarak kaynak kodlarda **Brave Browser** aramaya ayarlıdır.
Eğer sisteminizde *Brave yerine standart Google Chrome vb. yüklüyse*, uygulamanın çökmemesi için `scraper.py` dosyasını bir kod editörüyle açın ve şu ufak ayarı yapın:

- Yaklaşık 94. satırdaki `BRAVE_PATH` satırını silin veya kendi Google Chrome EXE adresinizi (`C:\Program Files\Google\Chrome\Application\chrome.exe` gibi) girin.
- Dilerseniz 98. satırdaki `, binary_location=BRAVE_PATH` ibaresini tamamen silerseniz SeleniumBase varsayılanı (Chrome'u) kendisi bulmayı deneyecektir.

### 3. Uygulamayı Başlatın
Sistemin veritabanı ön hazırlığı siz uğraşmadan `app.py` tetiklendiği an otomatik olarak gerçekleşir, tablolar yoksa kendi kurulur.
Her şeyi başlatmak için terminale gelin:

```bash
python app.py
```

Ekranda `Running on http://127.0.0.1:8080` bilgisini gördüğünüzde sisteminiz çalışıyor demektir. (Proje portu varsayılan 5000 çakışmalarını önlemek adına 8080 olarak atanmıştır).

### 4. Analiz ve Tarama Yapmak
- Web tarayıcınızı açın ve adres çubuğuna **`http://localhost:8080`** yazarak panele girin.
- Sahibinden web sitesi üzerinden dilediğiniz bir kategoriye (Örn: Trabzon Satılık Daire > Aydınlıkevler vs) girerek en üstteki arama sonucunun uzun URL'sini kopyalayın.
- İnteraktif paneldeki **Sahibinden URL'si** kutusuna bu URL'yi yapıştırıp hedef limite ulaştıktan sonra **"Botu Başlat"** butonuna basın.

Sayfayı kapatmadan arkanıza yaslanın ve ekranın sağ altında açılan durum ekranından AI (Bot) ilerleyişini izleyin. Bildirim tamamlandığında sayfayı yenileyerek arşivi doldurmuş olursunuz. 

---

## 🧹 Veritabanını Nasıl Temizlerim?
Eski arşivleri, yer kaplayan ilanları, klasörde kalmış fotoğrafları ve yorulan veritabanı yığınını silmek isterseniz sol panelin altında yer alan (Tehlikeli Bölge tabındaki) **"Tüm Arşivi Yok Et"** butonunu kullanabilirsiniz. İşlem anında her şeyi tamamen geri dönülemeyecek şekilde boşaltıp yeni görevlere hazır hale getirir.

> **Yasal Uyarı:** Bu proje açık kaynak topluluğuna katkı, veri bilimi tecrübesi, eğitim ve araştırma amaçlı bir konsept çalışmasıdır. Lütfen verileri izinli ve etik kurallar çerçevesinde, ticari kazanç hedeflemeden kullanınız. Oluşabilecek bot bloklamaları veya erişim kısıtlamaları site politikalarına aittir.