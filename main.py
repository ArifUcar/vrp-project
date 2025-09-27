#!/usr/bin/env python3
"""
VRP Ana Çalıştırma Dosyası
==========================
Bu dosya, VRP çözücünün ana fonksiyonlarını içerir.
"""

import os
import sys

# src klasörünü Python path'ine ekle
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.vrp_cozucu import VRPCozucu
from src.utils import performans_grafigi_olustur
from examples.ornek_kullanimlar import ornek_problem_olustur


def main():
    """
    Ana fonksiyon - VRP problemini çöz ve görselleştir
    """
    print("🚛 Vehicle Routing Problem (VRP) Çözücü")
    print("="*60)
    
    # Google Maps kullanımı kontrolü
    google_maps_kullan = input("\n🗺️  Google Maps API kullanmak istiyor musunuz? (e/h): ").lower() == 'e'
    
    # Örnek problem oluştur
    print("\n1. Problem oluşturuluyor...")
    vrp = ornek_problem_olustur()
    print(f"   ✅ {len(vrp.musteriler)} müşteri eklendi")
    print(f"   ✅ {len(vrp.araclar)} araç eklendi")
    
    # Mesafe matrisi oluştur
    print("\n2. Mesafe matrisi hesaplanıyor...")
    if google_maps_kullan:
        print("   🗺️  Google Maps API ile gerçek mesafeler alınıyor...")
    vrp.mesafe_matrisi_olustur(google_maps_kullan=google_maps_kullan)
    print("   ✅ Mesafe matrisi hazırlandı")
    
    # Problemi çöz
    print("\n3. Optimizasyon yapılıyor...")
    cozum = vrp.coz(zaman_limiti=30)
    
    if cozum:
        # Sonuçları yazdır
        print("\n4. Çözüm bulundu!")
        vrp.cozumu_yazdir()
        
        # Çıktı klasörünü oluştur
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        # Çözümü kaydet
        print("\n5. Çözüm kaydediliyor...")
        vrp.cozumu_kaydet(os.path.join(output_dir, "vrp_cozum.json"))
        
        # Harita oluştur
        print("\n6. Harita oluşturuluyor...")
        if google_maps_kullan:
            vrp.cozumu_gorsellestir(os.path.join(output_dir, "google_maps_harita.html"), google_maps_kullan=True)
            vrp.cozumu_gorsellestir(os.path.join(output_dir, "folium_harita.html"), google_maps_kullan=False)
        else:
            vrp.cozumu_gorsellestir(os.path.join(output_dir, "vrp_harita.html"), google_maps_kullan=False)
        
        # Performans grafiği
        print("\n7. Performans grafiği oluşturuluyor...")
        analiz_png_yolu = performans_grafigi_olustur(cozum, output_dir)
        
        print("\n" + "="*60)
        print("✅ TÜM İŞLEMLER TAMAMLANDI!")
        print("="*60)
        print("\n📁 Oluşturulan dosyalar:")
        print(f"  📄 {os.path.join(output_dir, 'vrp_cozum.json')}    - Çözüm detayları")
        if google_maps_kullan:
            print(f"  🗺️  {os.path.join(output_dir, 'google_maps_harita.html')}   - Google Maps haritası")
            print(f"  🗺️  {os.path.join(output_dir, 'folium_harita.html')}   - Folium haritası")
        else:
            print(f"  🗺️  {os.path.join(output_dir, 'vrp_harita.html')}   - İnteraktif harita")
        print(f"  📊 {analiz_png_yolu}    - Performans grafikleri")
        
    else:
        print("\n❌ Çözüm bulunamadı! Kısıtlamaları gevşetmeyi deneyin.")


def interaktif_mod():
    """
    Kullanıcı ile etkileşimli mod
    """
    print("\n🎯 İNTERAKTİF VRP ÇÖZÜCÜ")
    print("="*40)
    
    # Depo koordinatlarını al
    print("\n📍 Depo koordinatları:")
    try:
        lat = float(input("Enlem (lat): "))
        lon = float(input("Boylam (lon): "))
        depo_koordinat = (lat, lon)
    except ValueError:
        print("Geçersiz koordinat! Varsayılan İstanbul koordinatı kullanılıyor.")
        depo_koordinat = (41.0082, 28.9784)
    
    vrp = VRPCozucu(depo_koordinat)
    
    # Araç sayısını al
    try:
        arac_sayisi = int(input("\n🚛 Kaç araç eklemek istiyorsunuz? "))
    except ValueError:
        arac_sayisi = 3
    
    # Araçları ekle
    for i in range(arac_sayisi):
        print(f"\nAraç {i+1}:")
        try:
            kapasite = int(input("Kapasite (kg): "))
            maliyet = float(input("Km başına maliyet (TL): "))
            tip = input("Araç tipi: ")
        except ValueError:
            kapasite = 3000
            maliyet = 2.5
            tip = "Kamyonet"
        
        vrp.arac_ekle(f"ARAC-{i+1}", kapasite, maliyet, tip=tip)
    
    # Müşteri sayısını al
    try:
        musteri_sayisi = int(input(f"\n👥 Kaç müşteri eklemek istiyorsunuz? "))
    except ValueError:
        musteri_sayisi = 5
    
    # Müşterileri ekle
    for i in range(musteri_sayisi):
        print(f"\nMüşteri {i+1}:")
        try:
            lat = float(input("Enlem: "))
            lon = float(input("Boylam: "))
            talep = int(input("Talep (kg): "))
            baslangic = int(input("Başlangıç saati (dakika, örn: 480=08:00): "))
            bitis = int(input("Bitiş saati (dakika, örn: 720=12:00): "))
        except ValueError:
            print("Geçersiz değer! Varsayılan değerler kullanılıyor.")
            lat = 41.0 + (i * 0.01)
            lon = 29.0 + (i * 0.01)
            talep = 300
            baslangic = 480
            bitis = 720
        
        vrp.musteri_ekle(f"M{i+1}", (lat, lon), talep, (baslangic, bitis))
    
    # Problemi çöz
    print("\n🔧 Problem çözülüyor...")
    cozum = vrp.coz()
    
    if cozum:
        vrp.cozumu_yazdir()
        
        # Sonuçları kaydet
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        vrp.cozumu_kaydet(os.path.join(output_dir, "interaktif_cozum.json"))
        vrp.cozumu_gorsellestir(os.path.join(output_dir, "interaktif_harita.html"))
        performans_grafigi_olustur(cozum, output_dir)
        
        print(f"\n✅ Sonuçlar '{output_dir}' klasörüne kaydedildi!")
    else:
        print("\n❌ Çözüm bulunamadı!")


def menu():
    """
    Ana menü
    """
    while True:
        print("\n" + "="*50)
        print("🚛 VRP ÇÖZÜCÜ ANA MENÜ")
        print("="*50)
        print("1. Örnek problem çalıştır")
        print("2. İnteraktif mod")
        print("3. Örnek kullanımları göster")
        print("4. Çıkış")
        
        try:
            secim = input("\nSeçiminizi yapın (1-4): ")
            
            if secim == "1":
                main()
            elif secim == "2":
                interaktif_mod()
            elif secim == "3":
                from examples.ornek_kullanimlar import tum_ornekleri_calistir
                tum_ornekleri_calistir()
            elif secim == "4":
                print("\n👋 Görüşürüz!")
                break
            else:
                print("\n❌ Geçersiz seçim! Lütfen 1-4 arası bir sayı girin.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Program sonlandırıldı!")
            break
        except Exception as e:
            print(f"\n❌ Hata oluştu: {e}")


if __name__ == "__main__":
    # Komut satırı argümanlarını kontrol et
    if len(sys.argv) > 1:
        if sys.argv[1] == "--interactive" or sys.argv[1] == "-i":
            interaktif_mod()
        elif sys.argv[1] == "--examples" or sys.argv[1] == "-e":
            from examples.ornek_kullanimlar import tum_ornekleri_calistir
            tum_ornekleri_calistir()
        elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("""
🚛 VRP Çözücü Kullanımı:

python main.py                    # Ana menüyü göster
python main.py --interactive      # İnteraktif mod
python main.py --examples         # Örnek kullanımları çalıştır
python main.py --help             # Bu yardım mesajını göster

Örnekler:
python main.py -i                 # İnteraktif mod
python main.py -e                 # Örnekleri çalıştır
            """)
        else:
            print(f"❌ Bilinmeyen argüman: {sys.argv[1]}")
            print("Yardım için: python main.py --help")
    else:
        # Argüman yoksa menüyü göster
        menu()
