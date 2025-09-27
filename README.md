# 🚛 Vehicle Routing Problem (VRP) Çözücü

Bu proje, lojistik şirketlerinin araç filolarını optimize etmek için geliştirilmiş kapsamlı bir **Vehicle Routing Problem (VRP)** çözücüsüdür.

## 📋 Özellikler

### 🎯 Ana Özellikler
- **Farklı kapasiteli araçlar** (3 ton kamyonet, 6 ton kamyon vb.)
- **Zaman penceresi kısıtlamaları** (müşterilerin belirli saatlerde hizmet alması)
- **Gerçek mesafe hesaplama** (Haversine formülü ile)
- **🗺️ Google Maps API entegrasyonu** (gerçek trafik bilgisi ile)
- **Şehir içi trafik faktörü** (%30 ek mesafe)
- **Maliyet optimizasyonu** (araç başına farklı maliyetler)

### 📊 Çıktılar
- **İnteraktif harita** (Folium ile)
- **Performans grafikleri** (Matplotlib ile)
- **Detaylı raporlar** (JSON formatında)
- **Zaman çizelgeleri**

## 🛠️ Kurulum

### Gereksinimler
- Python 3.7+
- OR-Tools (Google'ın optimizasyon kütüphanesi)

### Kurulum Adımları

1. **Projeyi klonlayın:**
```bash
git clone <repository-url>
cd vrp_project
```

2. **Sanal ortam oluşturun:**
```bash
python -m venv vrp_env
source vrp_env/bin/activate  # Linux/Mac
# veya
vrp_env\Scripts\activate     # Windows
```

3. **Gerekli kütüphaneleri yükleyin:**
```bash
pip install -r requirements.txt
```

4. **Google Maps API anahtarını ayarlayın:**
```bash
# environment.env dosyasını düzenleyin
GOOGLE_MAPS_API_KEY=your_actual_api_key_here
```

> **Not:** Google Maps API anahtarı olmadan da çalışır, ancak gerçek mesafe ve trafik bilgileri için API anahtarı gereklidir.

## 🚀 Kullanım

### Hızlı Başlangıç

```python
from src.vrp_cozucu import VRPCozucu

# VRP çözücü oluştur
vrp = VRPCozucu(depo_koordinat=(41.0082, 28.9784))

# Araçları ekle
vrp.arac_ekle("ARAC-1", kapasite_kg=3000, maliyet_km=2.5, tip="3 Ton Kamyonet")
vrp.arac_ekle("ARAC-2", kapasite_kg=6000, maliyet_km=3.5, tip="6 Ton Kamyon")

# Müşterileri ekle
vrp.musteri_ekle("M1", (41.01, 29.01), 300, (480, 720))  # 08:00-12:00
vrp.musteri_ekle("M2", (41.02, 29.02), 400, (780, 1020))  # 13:00-17:00

# Problemi çöz
cozum = vrp.coz()

# Sonuçları görüntüle
vrp.cozumu_yazdir()
vrp.cozumu_gorsellestir("harita.html")
```

### Komut Satırı Kullanımı

```bash
# Ana menüyü göster
python main.py

# İnteraktif mod
python main.py --interactive

# Örnek kullanımları çalıştır
python main.py --examples

# Yardım
python main.py --help
```

## 📁 Proje Yapısı

```
vrp_project/
├── src/                    # Ana kaynak kodlar
│   ├── vrp_cozucu.py      # VRP çözücü sınıfı
│   └── utils.py           # Yardımcı fonksiyonlar
├── examples/              # Örnek kullanımlar
│   └── ornek_kullanimlar.py
├── data/                  # Veri dosyaları
├── output/                # Çıktı dosyaları
├── main.py               # Ana çalıştırma dosyası
├── requirements.txt      # Gerekli kütüphaneler
└── README.md            # Bu dosya
```

## 📊 Örnek Sonuçlar

### Çıktı Örneği
```
============================================================
VEHİCLE ROUTİNG PROBLEM ÇÖZÜMÜ
============================================================

------------------------------------------------------------
ARAÇ 0 - 3 Ton Kamyonet (Kapasite: 3000 kg)
------------------------------------------------------------
Toplam Mesafe: 45.2 km
Toplam Yük: 2850 kg
Maliyet: 113.0 TL

Rota Detayı:
  0. DEPO - Varış: 08:00
  1. Müşteri M001-Üsküdar - Talep: 450 kg, Varış: 08:45, Toplam Yük: 450 kg
  2. Müşteri M002-Ümraniye - Talep: 600 kg, Varış: 09:30, Toplam Yük: 1050 kg
  ...

============================================================
ÖZET
============================================================
Toplam Mesafe: 127.8 km
Toplam Maliyet: 445.5 TL
Kullanılan Araç Sayısı: 3
Servis Edilen Müşteri Sayısı: 15
============================================================
```

## 🎯 Kullanım Senaryoları

Bu çözücü şu durumlarda kullanılabilir:

1. **Kargo şirketleri** - Paket dağıtımı
2. **Market zincirleri** - Ürün teslimatı  
3. **Temizlik şirketleri** - Servis rotaları
4. **Teknik servis** - Bakım ziyaretleri
5. **Yemek teslimatı** - Restoran dağıtımı
6. **Sağlık hizmetleri** - Evde bakım rotaları

## 🔧 Gelişmiş Özellikler

### CSV Veri Yükleme
```python
from src.utils import csv_den_yukle

# CSV dosyasından müşteri verilerini yükle
vrp = csv_den_yukle("musteriler.csv")
```

### Gerçek Zamanlı VRP
```python
from src.vrp_cozucu import GercekZamanliVRP

# Dinamik müşteri ekleme
gercek_zamanli = GercekZamanliVRP(vrp)
gercek_zamanli.yeni_musteri_ekle(musteri_bilgileri)
```

### Performans Analizi
```python
from src.utils import performans_raporu_olustur, karsilastirmali_analiz

# Detaylı rapor oluştur
performans_raporu_olustur(cozum, "rapor.txt")

# Çözümleri karşılaştır
karsilastirmali_analiz([cozum1, cozum2, cozum3])
```

## 📈 Performans

- **Küçük problemler** (≤20 müşteri): < 5 saniye
- **Orta problemler** (21-50 müşteri): 5-30 saniye  
- **Büyük problemler** (51+ müşteri): 30+ saniye

## 🤝 Katkıda Bulunma

1. Projeyi fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakın.

## 📞 İletişim

- **Proje Sahibi**: [Adınız]
- **Email**: [email@example.com]
- **GitHub**: [github.com/username]

## 🙏 Teşekkürler

- **Google OR-Tools** - Optimizasyon algoritmaları için
- **Folium** - İnteraktif haritalar için
- **Matplotlib** - Grafik çizimi için

---

⭐ **Bu projeyi beğendiyseniz yıldız vermeyi unutmayın!**
