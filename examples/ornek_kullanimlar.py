"""
VRP Örnek Kullanımları
=======================
Bu modül, VRP çözücünün farklı kullanım senaryolarını gösterir.
"""

import random
import os
import sys

# src klasörünü Python path'ine ekle
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from vrp_cozucu import VRPCozucu
from utils import performans_grafigi_olustur, performans_raporu_olustur


def ornek_problem_olustur():
    """
    Örnek bir VRP problemi oluştur
    """
    # VRP çözücü oluştur (İstanbul Kadıköy merkez)
    vrp = VRPCozucu(depo_koordinat=(40.9887, 29.0303))
    
    # Araçları ekle (farklı kapasiteler)
    vrp.arac_ekle(arac_id="ARAC-1", kapasite_kg=3000, maliyet_km=2.5, 
                  max_mesafe_km=150, hiz_kmh=40, tip="3 Ton Kamyonet")
    vrp.arac_ekle(arac_id="ARAC-2", kapasite_kg=6000, maliyet_km=3.5, 
                  max_mesafe_km=200, hiz_kmh=35, tip="6 Ton Kamyon")
    vrp.arac_ekle(arac_id="ARAC-3", kapasite_kg=3000, maliyet_km=2.5, 
                  max_mesafe_km=150, hiz_kmh=40, tip="3 Ton Kamyonet")
    
    # İstanbul'da rastgele müşteriler oluştur
    random.seed(42)  # Tekrarlanabilirlik için
    
    musteri_bolgeleri = [
        # (lat, lon, bölge_adı, min_talep, max_talep)
        (41.0370, 29.0013, "Üsküdar", 100, 500),
        (41.0766, 29.0153, "Ümraniye", 150, 600),
        (41.0053, 28.9770, "Beşiktaş", 200, 700),
        (41.1066, 29.0330, "Çekmeköy", 100, 400),
        (41.0527, 29.0995, "Ataşehir", 300, 800),
        (40.9830, 29.0570, "Maltepe", 250, 650),
        (40.9661, 29.0805, "Kartal", 200, 550),
        (40.8930, 29.1989, "Pendik", 150, 450),
        (41.0186, 28.9404, "Şişli", 300, 900),
        (41.0692, 28.9869, "Kağıthane", 200, 500),
        (40.9264, 29.1245, "Tuzla", 100, 350),
        (41.0049, 28.8738, "Bakırköy", 250, 700),
        (40.9911, 28.8467, "Küçükçekmece", 200, 600),
        (41.0842, 28.7974, "Eyüpsultan", 150, 400),
        (41.1635, 29.0550, "Beykoz", 100, 300),
    ]
    
    for i, (lat, lon, bolge, min_talep, max_talep) in enumerate(musteri_bolgeleri):
        # Her bölgeye küçük random offset ekle
        lat_offset = random.uniform(-0.02, 0.02)
        lon_offset = random.uniform(-0.02, 0.02)
        
        talep = random.randint(min_talep, max_talep)
        
        # Zaman penceresi (sabah 8-12 veya öğleden sonra 13-17)
        if random.random() > 0.5:
            zaman_penceresi = (480, 720)  # 08:00-12:00
        else:
            zaman_penceresi = (780, 1020)  # 13:00-17:00
        
        vrp.musteri_ekle(
            musteri_id=f"M{i+1:03d}-{bolge}",
            koordinat=(lat + lat_offset, lon + lon_offset),
            talep_kg=talep,
            zaman_penceresi=zaman_penceresi,
            servis_suresi=random.randint(10, 30)
        )
    
    return vrp


def ornek_1_basit_kullanim():
    """
    En basit kullanım örneği
    """
    print("\n" + "="*50)
    print("ÖRNEK 1: BASİT KULLANIM")
    print("="*50)
    
    # VRP oluştur
    vrp = VRPCozucu()
    
    # 2 araç ekle
    vrp.arac_ekle("A1", kapasite_kg=1000, maliyet_km=2)
    vrp.arac_ekle("A2", kapasite_kg=1500, maliyet_km=2.5)
    
    # 5 müşteri ekle
    vrp.musteri_ekle("M1", (41.01, 29.01), 300, (480, 720))
    vrp.musteri_ekle("M2", (41.02, 29.02), 400, (480, 720))
    vrp.musteri_ekle("M3", (41.03, 29.00), 350, (780, 1020))
    vrp.musteri_ekle("M4", (40.99, 29.01), 250, (780, 1020))
    vrp.musteri_ekle("M5", (41.00, 29.03), 450, (480, 1020))
    
    # Çöz ve göster
    cozum = vrp.coz()
    if cozum:
        vrp.cozumu_yazdir()
        vrp.cozumu_gorsellestir("basit_ornek_harita.html")
        vrp.cozumu_kaydet("basit_ornek_cozum.json")
    
    return vrp


def ornek_2_buyuk_problem():
    """
    Büyük ölçekli problem örneği
    """
    print("\n" + "="*50)
    print("ÖRNEK 2: BÜYÜK ÖLÇEKLİ PROBLEM")
    print("="*50)
    
    vrp = VRPCozucu()
    
    # 10 araç ekle
    for i in range(5):
        vrp.arac_ekle(f"Kamyonet-{i+1}", kapasite_kg=3000, maliyet_km=2.5)
    for i in range(5):
        vrp.arac_ekle(f"Kamyon-{i+1}", kapasite_kg=6000, maliyet_km=3.5)
    
    # 50 müşteri ekle
    random.seed(123)
    for i in range(50):
        lat = 41.0 + random.uniform(-0.15, 0.15)
        lon = 29.0 + random.uniform(-0.15, 0.15)
        talep = random.randint(100, 800)
        
        if i % 3 == 0:
            zaman = (480, 720)  # Sabah
        elif i % 3 == 1:
            zaman = (720, 900)  # Öğle
        else:
            zaman = (900, 1020)  # Öğleden sonra
        
        vrp.musteri_ekle(f"M{i+1}", (lat, lon), talep, zaman)
    
    # Çöz
    cozum = vrp.coz(zaman_limiti=60)
    
    if cozum:
        print(f"\n✅ {len(vrp.musteriler)} müşteri için çözüm bulundu!")
        print(f"Toplam mesafe: {cozum['toplam_mesafe']} km")
        print(f"Kullanılan araç: {cozum['kullanilan_araclar']}")
        
        # Performans raporu oluştur
        performans_raporu_olustur(cozum, "buyuk_problem_rapor.txt")
        
        # Grafik oluştur
        performans_grafigi_olustur(cozum, "output")
    
    return vrp


def ornek_3_csv_verisi():
    """
    CSV dosyasından veri yükleme örneği
    """
    print("\n" + "="*50)
    print("ÖRNEK 3: CSV VERİSİ İLE ÇALIŞMA")
    print("="*50)
    
    from utils import csv_den_yukle, ornek_musteri_verisi_olustur, ornek_arac_verisi_olustur
    
    # Önce örnek veri dosyalarını oluştur
    print("1. Örnek veri dosyaları oluşturuluyor...")
    ornek_musteri_verisi_olustur("data/ornek_musteriler.csv", 10)
    ornek_arac_verisi_olustur("data/ornek_araclar.csv")
    
    # CSV'den müşteri verilerini yükle
    print("2. CSV'den müşteri verileri yükleniyor...")
    vrp = csv_den_yukle("data/ornek_musteriler.csv")
    
    # Araçları ekle
    print("3. Araçlar ekleniyor...")
    vrp.arac_ekle("ARAC-1", kapasite_kg=3000, maliyet_km=2.5, tip="3 Ton Kamyonet")
    vrp.arac_ekle("ARAC-2", kapasite_kg=6000, maliyet_km=3.5, tip="6 Ton Kamyon")
    
    # Problemi çöz
    print("4. Problem çözülüyor...")
    cozum = vrp.coz()
    
    if cozum:
        print("5. Sonuçlar kaydediliyor...")
        vrp.cozumu_yazdir()
        vrp.cozumu_gorsellestir("csv_ornek_harita.html")
        vrp.cozumu_kaydet("csv_ornek_cozum.json")
    
    return vrp


def ornek_4_gercek_zamanli():
    """
    Gerçek zamanlı VRP örneği
    """
    print("\n" + "="*50)
    print("ÖRNEK 4: GERÇEK ZAMANLI VRP")
    print("="*50)
    
    from vrp_cozucu import GercekZamanliVRP
    
    # Başlangıç VRP'si oluştur
    vrp = VRPCozucu()
    vrp.arac_ekle("ARAC-1", kapasite_kg=3000, maliyet_km=2.5)
    vrp.arac_ekle("ARAC-2", kapasite_kg=3000, maliyet_km=2.5)
    
    # İlk müşterileri ekle
    vrp.musteri_ekle("M1", (41.01, 29.01), 300, (480, 720))
    vrp.musteri_ekle("M2", (41.02, 29.02), 400, (480, 720))
    
    # Gerçek zamanlı VRP oluştur
    gercek_zamanli = GercekZamanliVRP(vrp)
    
    # İlk çözümü al
    print("1. İlk çözüm oluşturuluyor...")
    ilk_cozum = vrp.coz()
    if ilk_cozum:
        print(f"   İlk çözüm: {len(ilk_cozum['rotalar'])} araç kullanıldı")
    
    # Yeni müşteriler ekle
    print("2. Yeni müşteriler ekleniyor...")
    yeni_musteriler = [
        {
            'musteri_id': 'M3',
            'koordinat': (41.03, 29.00),
            'talep_kg': 350,
            'zaman_penceresi': (780, 1020),
            'servis_suresi': 20
        },
        {
            'musteri_id': 'M4',
            'koordinat': (40.99, 29.01),
            'talep_kg': 250,
            'zaman_penceresi': (780, 1020),
            'servis_suresi': 15
        },
        {
            'musteri_id': 'M5',
            'koordinat': (41.00, 29.03),
            'talep_kg': 450,
            'zaman_penceresi': (480, 1020),
            'servis_suresi': 25
        }
    ]
    
    for musteri in yeni_musteriler:
        gercek_zamanli.yeni_musteri_ekle(musteri)
    
    print("3. Rotalar güncellendi!")
    print(f"   Toplam müşteri sayısı: {len(vrp.musteriler)}")
    
    return gercek_zamanli


def ornek_5_google_maps():
    """
    Google Maps API ile VRP örneği
    """
    print("\n" + "="*50)
    print("ÖRNEK 5: GOOGLE MAPS API İLE VRP")
    print("="*50)
    
    try:
        from google_maps_integration import GoogleMapsAPI, GoogleMapsVRP
        
        # Google Maps API kontrolü
        google_api = GoogleMapsAPI()
        if not google_api.api_available:
            print("⚠️  Google Maps API anahtarı bulunamadı!")
            print("   environment.env dosyasına GOOGLE_MAPS_API_KEY ekleyin.")
            return None
        
        # VRP oluştur
        vrp = VRPCozucu(depo_koordinat=(41.0082, 28.9784))  # İstanbul
        
        # Araçları ekle
        vrp.arac_ekle("ARAC-1", kapasite_kg=3000, maliyet_km=2.5, tip="3 Ton Kamyonet")
        vrp.arac_ekle("ARAC-2", kapasite_kg=6000, maliyet_km=3.5, tip="6 Ton Kamyon")
        
        # Müşterileri ekle (İstanbul'daki gerçek konumlar)
        musteri_konumlari = [
            ("M1", (41.0370, 29.0013), 300, (480, 720)),  # Üsküdar
            ("M2", (41.0766, 29.0153), 400, (480, 720)),  # Ümraniye
            ("M3", (41.0053, 28.9770), 350, (780, 1020)),  # Beşiktaş
            ("M4", (41.0527, 29.0995), 450, (780, 1020)),  # Ataşehir
            ("M5", (40.9830, 29.0570), 250, (480, 1020)),  # Maltepe
        ]
        
        for musteri_id, koordinat, talep, zaman_penceresi in musteri_konumlari:
            vrp.musteri_ekle(musteri_id, koordinat, talep, zaman_penceresi)
        
        print("1. Google Maps API ile gerçek mesafeler alınıyor...")
        
        # Google Maps ile mesafe matrisi oluştur
        google_vrp = GoogleMapsVRP(vrp)
        mesafe_matrisi = google_vrp.gercek_mesafe_matrisi_olustur()
        
        if mesafe_matrisi is not None:
            print("   ✅ Google Maps mesafe matrisi oluşturuldu!")
            
            # Problemi çöz
            print("2. Optimizasyon yapılıyor...")
            cozum = vrp.coz()
            
            if cozum:
                print("3. Sonuçlar kaydediliyor...")
                vrp.cozumu_yazdir()
                
                # Google Maps haritası oluştur
                print("4. Google Maps haritası oluşturuluyor...")
                google_vrp.cozumu_google_maps_ile_gorsellestir("google_maps_ornek.html")
                
                # Standart harita da oluştur
                vrp.cozumu_gorsellestir("folium_ornek.html")
                
                print("✅ Google Maps örneği tamamlandı!")
                print("   📁 Oluşturulan dosyalar:")
                print("   🗺️  output/google_maps_ornek.html - Google Maps haritası")
                print("   🗺️  output/folium_ornek.html - Folium haritası")
                
                return google_vrp
            else:
                print("❌ Çözüm bulunamadı!")
        else:
            print("⚠️  Google Maps API hatası, standart yöntem kullanılacak.")
            vrp.mesafe_matrisi_olustur()
            cozum = vrp.coz()
            if cozum:
                vrp.cozumu_yazdir()
                vrp.cozumu_gorsellestir("standart_ornek.html")
    
    except ImportError:
        print("⚠️  Google Maps entegrasyonu bulunamadı!")
        print("   pip install requests python-dotenv")
    except Exception as e:
        print(f"❌ Hata: {e}")
    
    return None


def tum_ornekleri_calistir():
    """
    Tüm örnekleri sırayla çalıştır
    """
    print("🚛 VRP ÖRNEK KULLANIMLARI")
    print("="*60)
    
    try:
        # Örnek 1: Basit kullanım
        print("\n📋 Örnek 1 çalıştırılıyor...")
        ornek_1_basit_kullanim()
        
        # Örnek 2: Büyük problem
        print("\n📋 Örnek 2 çalıştırılıyor...")
        ornek_2_buyuk_problem()
        
        # Örnek 3: CSV verisi
        print("\n📋 Örnek 3 çalıştırılıyor...")
        ornek_3_csv_verisi()
        
        # Örnek 4: Gerçek zamanlı
        print("\n📋 Örnek 4 çalıştırılıyor...")
        ornek_4_gercek_zamanli()
        
        # Örnek 5: Google Maps
        print("\n📋 Örnek 5 çalıştırılıyor...")
        ornek_5_google_maps()
        
        print("\n✅ Tüm örnekler başarıyla tamamlandı!")
        
    except Exception as e:
        print(f"\n❌ Hata oluştu: {e}")


if __name__ == "__main__":
    # Sadece bu dosyayı çalıştırırsanız tüm örnekleri çalıştırır
    tum_ornekleri_calistir()
