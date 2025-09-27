"""
VRP Yardımcı Fonksiyonları
===========================
Bu modül, VRP çözücü için yardımcı fonksiyonları içerir.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime


def csv_den_yukle(csv_dosyasi):
    """
    CSV dosyasından müşteri verilerini yükle
    
    CSV formatı:
    musteri_id,lat,lon,talep_kg,zaman_baslangic,zaman_bitis,servis_suresi
    """
    from .vrp_cozucu import VRPCozucu
    
    df = pd.read_csv(csv_dosyasi)
    
    vrp = VRPCozucu()
    
    for _, row in df.iterrows():
        vrp.musteri_ekle(
            musteri_id=row['musteri_id'],
            koordinat=(row['lat'], row['lon']),
            talep_kg=row['talep_kg'],
            zaman_penceresi=(row['zaman_baslangic'], row['zaman_bitis']),
            servis_suresi=row.get('servis_suresi', 15)
        )
    
    return vrp


def performans_raporu_olustur(cozum, dosya_adi="vrp_rapor.txt"):
    """
    Detaylı performans raporu oluştur
    """
    with open(dosya_adi, 'w', encoding='utf-8') as f:
        f.write("VRP PERFORMANS RAPORU\n")
        f.write("="*60 + "\n")
        f.write(f"Rapor Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("GENEL ÖZET\n")
        f.write("-"*40 + "\n")
        f.write(f"Toplam Mesafe: {cozum['toplam_mesafe']} km\n")
        f.write(f"Toplam Maliyet: {cozum['toplam_maliyet']} TL\n")
        f.write(f"Kullanılan Araç Sayısı: {cozum['kullanilan_araclar']}\n")
        f.write(f"Servis Edilen Müşteri: {len(cozum['servis_edilen_musteriler'])}\n\n")
        
        f.write("ARAÇ BAZLI ANALİZ\n")
        f.write("-"*40 + "\n")
        
        for rota in cozum['rotalar']:
            f.write(f"\nAraç {rota['arac_id']} - {rota['arac_tipi']}\n")
            f.write(f"  Kapasite Kullanımı: {rota['yuk']}/{rota['kapasite']} kg ")
            f.write(f"({100*rota['yuk']/rota['kapasite']:.1f}%)\n")
            f.write(f"  Mesafe: {rota['mesafe']} km\n")
            f.write(f"  Maliyet: {rota['maliyet']} TL\n")
            f.write(f"  Müşteri Sayısı: {len([d for d in rota['duraklar'] if d['tip'] == 'Müşteri'])}\n")
            
            # Zaman analizi
            baslangic = rota['duraklar'][0]['varış_zamani']
            bitis = rota['duraklar'][-1]['varış_zamani']
            f.write(f"  Çalışma Saatleri: {baslangic} - {bitis}\n")
        
        f.write("\n" + "="*60 + "\n")
        f.write("RAPOR SONU\n")
    
    print(f"Performans raporu '{dosya_adi}' olarak kaydedildi.")


def karsilastirmali_analiz(cozumler_listesi):
    """
    Birden fazla çözümü karşılaştır
    """
    labels = [f"Çözüm {i+1}" for i in range(len(cozumler_listesi))]
    mesafeler = [c['toplam_mesafe'] for c in cozumler_listesi]
    maliyetler = [c['toplam_maliyet'] for c in cozumler_listesi]
    arac_sayilari = [c['kullanilan_araclar'] for c in cozumler_listesi]
    
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
    
    # Mesafe karşılaştırması
    ax1.bar(labels, mesafeler, color='blue', alpha=0.7)
    ax1.set_ylabel('Toplam Mesafe (km)')
    ax1.set_title('Mesafe Karşılaştırması')
    ax1.grid(True, alpha=0.3)
    
    # Maliyet karşılaştırması
    ax2.bar(labels, maliyetler, color='green', alpha=0.7)
    ax2.set_ylabel('Toplam Maliyet (TL)')
    ax2.set_title('Maliyet Karşılaştırması')
    ax2.grid(True, alpha=0.3)
    
    # Araç sayısı karşılaştırması
    ax3.bar(labels, arac_sayilari, color='red', alpha=0.7)
    ax3.set_ylabel('Kullanılan Araç Sayısı')
    ax3.set_title('Araç Kullanımı Karşılaştırması')
    ax3.grid(True, alpha=0.3)
    
    plt.suptitle('VRP Çözüm Karşılaştırması', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('vrp_karsilastirma.png', dpi=100, bbox_inches='tight')
    plt.show()


def performans_grafigi_olustur(cozum, output_dir="output"):
    """
    Performans grafikleri oluştur
    """
    # Çıktı klasörünü oluştur
    os.makedirs(output_dir, exist_ok=True)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Araç kullanımı grafiği
    arac_ids = [f"Araç {r['arac_id']}" for r in cozum['rotalar']]
    mesafeler = [r['mesafe'] for r in cozum['rotalar']]
    yukler = [r['yuk'] for r in cozum['rotalar']]
    kapasiteler = [r['kapasite'] for r in cozum['rotalar']]
    
    x = np.arange(len(arac_ids))
    width = 0.35
    
    ax1.bar(x - width/2, yukler, width, label='Yük (kg)', color='skyblue')
    ax1.bar(x + width/2, kapasiteler, width, label='Kapasite (kg)', color='lightcoral')
    ax1.set_xlabel('Araçlar')
    ax1.set_ylabel('Kg')
    ax1.set_title('Araç Kapasite Kullanımı')
    ax1.set_xticks(x)
    ax1.set_xticklabels(arac_ids)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Mesafe grafiği
    ax2.bar(arac_ids, mesafeler, color='green', alpha=0.7)
    ax2.set_xlabel('Araçlar')
    ax2.set_ylabel('Mesafe (km)')
    ax2.set_title('Araç Başına Kat Edilen Mesafe')
    ax2.grid(True, alpha=0.3)
    
    # Toplam mesafeyi göster
    for i, v in enumerate(mesafeler):
        ax2.text(i, v + 1, f'{v:.1f} km', ha='center', fontsize=9)
    
    plt.suptitle(f'VRP Çözüm Analizi - Toplam: {cozum["toplam_mesafe"]:.1f} km, '
                 f'Maliyet: {cozum["toplam_maliyet"]:.1f} TL', fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    analiz_png_yolu = os.path.join(output_dir, "vrp_analiz.png")
    plt.savefig(analiz_png_yolu, dpi=100, bbox_inches='tight')
    plt.show()
    
    return analiz_png_yolu


def ornek_musteri_verisi_olustur(dosya_adi="ornek_musteriler.csv", musteri_sayisi=15):
    """
    Örnek müşteri verisi CSV dosyası oluştur
    """
    import random
    
    random.seed(42)
    
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
    
    veriler = []
    
    for i in range(min(musteri_sayisi, len(musteri_bolgeleri))):
        lat, lon, bolge, min_talep, max_talep = musteri_bolgeleri[i]
        
        # Her bölgeye küçük random offset ekle
        lat_offset = random.uniform(-0.02, 0.02)
        lon_offset = random.uniform(-0.02, 0.02)
        
        talep = random.randint(min_talep, max_talep)
        
        # Zaman penceresi (sabah 8-12 veya öğleden sonra 13-17)
        if random.random() > 0.5:
            zaman_baslangic = 480  # 08:00
            zaman_bitis = 720      # 12:00
        else:
            zaman_baslangic = 780  # 13:00
            zaman_bitis = 1020     # 17:00
        
        servis_suresi = random.randint(10, 30)
        
        veriler.append({
            'musteri_id': f"M{i+1:03d}-{bolge}",
            'lat': lat + lat_offset,
            'lon': lon + lon_offset,
            'talep_kg': talep,
            'zaman_baslangic': zaman_baslangic,
            'zaman_bitis': zaman_bitis,
            'servis_suresi': servis_suresi
        })
    
    df = pd.DataFrame(veriler)
    df.to_csv(dosya_adi, index=False, encoding='utf-8')
    print(f"Örnek müşteri verisi '{dosya_adi}' dosyasına kaydedildi.")
    
    return df


def ornek_arac_verisi_olustur(dosya_adi="ornek_araclar.csv"):
    """
    Örnek araç verisi CSV dosyası oluştur
    """
    veriler = [
        {
            'arac_id': 'ARAC-1',
            'kapasite_kg': 3000,
            'maliyet_km': 2.5,
            'max_mesafe_km': 150,
            'hiz_kmh': 40,
            'tip': '3 Ton Kamyonet'
        },
        {
            'arac_id': 'ARAC-2',
            'kapasite_kg': 6000,
            'maliyet_km': 3.5,
            'max_mesafe_km': 200,
            'hiz_kmh': 35,
            'tip': '6 Ton Kamyon'
        },
        {
            'arac_id': 'ARAC-3',
            'kapasite_kg': 3000,
            'maliyet_km': 2.5,
            'max_mesafe_km': 150,
            'hiz_kmh': 40,
            'tip': '3 Ton Kamyonet'
        }
    ]
    
    df = pd.DataFrame(veriler)
    df.to_csv(dosya_adi, index=False, encoding='utf-8')
    print(f"Örnek araç verisi '{dosya_adi}' dosyasına kaydedildi.")
    
    return df
