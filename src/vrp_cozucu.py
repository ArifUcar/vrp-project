"""
Vehicle Routing Problem (VRP) Çözücü
=====================================
Bu modül, farklı kapasiteli araçlar ve zaman pencereleri ile 
rotalama optimizasyonu yapar.

Gerekli kütüphaneler:
pip install ortools numpy pandas matplotlib folium
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import random
import math
import json
from datetime import datetime, timedelta
import folium
import os


class VRPCozucu:
    """
    Vehicle Routing Problem Çözücü Sınıfı
    
    Özellikler:
    - Farklı kapasiteli araçlar (3 ton, 6 ton vb.)
    - Zaman penceresi kısıtlamaları
    - Farklı araç tipleri için farklı maliyetler
    - Gerçek hayat kısıtlamaları
    """
    
    def __init__(self, depo_koordinat=(41.0082, 28.9784)):  # İstanbul koordinatı
        """
        Args:
            depo_koordinat: Depo/merkez koordinatları (lat, lon)
        """
        self.depo_koordinat = depo_koordinat
        self.musteriler = []
        self.araclar = []
        self.mesafe_matrisi = None
        self.zaman_matrisi = None
        self.cozum = None
        
    def musteri_ekle(self, musteri_id, koordinat, talep_kg, 
                     zaman_penceresi=(480, 1020), servis_suresi=15):
        """
        Yeni müşteri ekle
        
        Args:
            musteri_id: Müşteri kimliği
            koordinat: (lat, lon) tuple
            talep_kg: Talep miktarı (kg)
            zaman_penceresi: (başlangıç_dk, bitiş_dk) - 480=08:00, 1020=17:00
            servis_suresi: Müşteride geçirilecek süre (dakika)
        """
        self.musteriler.append({
            'id': musteri_id,
            'koordinat': koordinat,
            'talep': talep_kg,
            'zaman_penceresi': zaman_penceresi,
            'servis_suresi': servis_suresi
        })
    
    def arac_ekle(self, arac_id, kapasite_kg, maliyet_km=1.0, 
                  max_mesafe_km=200, hiz_kmh=50, tip="Kamyon"):
        """
        Yeni araç ekle
        
        Args:
            arac_id: Araç kimliği
            kapasite_kg: Araç kapasitesi (kg)
            maliyet_km: Km başına maliyet
            max_mesafe_km: Maksimum gidebileceği mesafe
            hiz_kmh: Ortalama hız (km/saat)
            tip: Araç tipi
        """
        self.araclar.append({
            'id': arac_id,
            'kapasite': kapasite_kg,
            'maliyet_km': maliyet_km,
            'max_mesafe': max_mesafe_km,
            'hiz': hiz_kmh,
            'tip': tip
        })
    
    def haversine_mesafe(self, coord1, coord2):
        """
        İki koordinat arası Haversine mesafesi (km)
        """
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        R = 6371  # Dünya yarıçapı (km)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    def mesafe_matrisi_olustur(self, google_maps_kullan=False):
        """
        Tüm noktalar arası mesafe ve zaman matrislerini oluştur
        
        Args:
            google_maps_kullan: Google Maps API ile gerçek mesafeleri al
        """
        # Google Maps kullanımı kontrolü
        if google_maps_kullan:
            try:
                from .google_maps_integration import GoogleMapsVRP
                google_vrp = GoogleMapsVRP(self)
                return google_vrp.gercek_mesafe_matrisi_olustur()
            except ImportError:
                print("⚠️  Google Maps entegrasyonu bulunamadı, Haversine formülü kullanılacak.")
            except Exception as e:
                print(f"⚠️  Google Maps hatası: {e}, Haversine formülü kullanılacak.")

        # Standart Haversine hesaplama
        return self._haversine_mesafe_matrisi_olustur()
    
    def _haversine_mesafe_matrisi_olustur(self):
        """
        Haversine formülü ile mesafe matrisi oluştur
        """
        # Tüm lokasyonlar (depo + müşteriler)
        lokasyonlar = [self.depo_koordinat] + [m['koordinat'] for m in self.musteriler]
        n = len(lokasyonlar)
        
        # Mesafe matrisi (km)
        self.mesafe_matrisi = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i != j:
                    mesafe = self.haversine_mesafe(lokasyonlar[i], lokasyonlar[j])
                    # Şehir içi trafik faktörü (1.3x)
                    self.mesafe_matrisi[i][j] = mesafe * 1.3
        
        # Zaman matrisi (dakika) - ortalama 40 km/h şehir içi hız
        self.zaman_matrisi = (self.mesafe_matrisi / 40) * 60
        
        return self.mesafe_matrisi
    
    def veri_modeli_olustur(self):
        """
        OR-Tools için veri modeli oluştur
        """
        if self.mesafe_matrisi is None:
            self.mesafe_matrisi_olustur()
        
        veri = {}
        
        # Mesafe matrisi (integer'a çevir - OR-Tools gereksinimi)
        veri['mesafe_matrisi'] = (self.mesafe_matrisi * 1000).astype(int)
        veri['zaman_matrisi'] = self.zaman_matrisi.astype(int)
        
        # Araç sayısı
        veri['arac_sayisi'] = len(self.araclar)
        
        # Depo indeksi
        veri['depo'] = 0
        
        # Talepler (depo için 0, müşteriler için gerçek talep)
        veri['talepler'] = [0] + [m['talep'] for m in self.musteriler]
        
        # Araç kapasiteleri
        veri['arac_kapasiteleri'] = [a['kapasite'] for a in self.araclar]
        
        # Zaman pencereleri
        veri['zaman_pencereleri'] = [(0, 1440)]  # Depo tüm gün açık
        for musteri in self.musteriler:
            veri['zaman_pencereleri'].append(musteri['zaman_penceresi'])
        
        # Servis süreleri
        veri['servis_sureleri'] = [0] + [m['servis_suresi'] for m in self.musteriler]
        
        return veri
    
    def coz(self, zaman_limiti=30, esnek_kisitlamalar=True):
        """
        VRP problemini çöz
        
        Args:
            zaman_limiti: Çözüm için maksimum süre (saniye)
            esnek_kisitlamalar: Kısıtlamaları gevşet (True/False)
            
        Returns:
            Çözüm dictionary'si
        """
        # Esnek kısıtlamalar için araç kapasitelerini artır
        if esnek_kisitlamalar:
            print("🔧 Esnek kısıtlamalar aktif - araç kapasiteleri artırılıyor...")
            for arac in self.araclar:
                arac['kapasite'] = int(arac['kapasite'] * 1.5)  # %50 artır
                arac['max_mesafe'] = int(arac['max_mesafe'] * 1.2)  # %20 artır
        
        # Veri modelini oluştur
        veri = self.veri_modeli_olustur()
        
        # Routing Index Manager oluştur
        manager = pywrapcp.RoutingIndexManager(
            len(veri['mesafe_matrisi']),
            veri['arac_sayisi'],
            veri['depo']
        )
        
        # Routing Model oluştur
        routing = pywrapcp.RoutingModel(manager)
        
        # Mesafe callback fonksiyonu
        def mesafe_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return veri['mesafe_matrisi'][from_node][to_node]
        
        transit_callback_index = routing.RegisterTransitCallback(mesafe_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # Kapasite kısıtı ekle
        def talep_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return veri['talepler'][from_node]
        
        talep_callback_index = routing.RegisterUnaryTransitCallback(talep_callback)
        routing.AddDimensionWithVehicleCapacity(
            talep_callback_index,
            0,  # Slack yok
            veri['arac_kapasiteleri'],  # Araç kapasiteleri
            True,  # Start cumul to zero
            'Kapasite'
        )
        
        # Zaman penceresi kısıtı ekle
        def zaman_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            servis_suresi = veri['servis_sureleri'][from_node]
            return veri['zaman_matrisi'][from_node][to_node] + servis_suresi
        
        zaman_callback_index = routing.RegisterTransitCallback(zaman_callback)
        routing.AddDimension(
            zaman_callback_index,
            1440,  # Maksimum bekleme süresi
            1440,  # Maksimum zaman
            False,  # Start cumul to zero
            'Zaman'
        )
        
        zaman_dimension = routing.GetDimensionOrDie('Zaman')
        for lokasyon_idx, zaman_penceresi in enumerate(veri['zaman_pencereleri']):
            if lokasyon_idx == veri['depo']:
                continue
            index = manager.NodeToIndex(lokasyon_idx)
            zaman_dimension.CumulVar(index).SetRange(zaman_penceresi[0], zaman_penceresi[1])
        
        # Depo için zaman penceresini ayarla
        depo_idx = veri['depo']
        for arac_id in range(veri['arac_sayisi']):
            index = routing.Start(arac_id)
            zaman_dimension.CumulVar(index).SetRange(
                veri['zaman_pencereleri'][depo_idx][0],
                veri['zaman_pencereleri'][depo_idx][1]
            )
        
        # Çözüm parametreleri
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.FromSeconds(zaman_limiti)
        
        # Problemi çöz
        solution = routing.SolveWithParameters(search_parameters)
        
        if solution:
            self.cozum = self._cozumu_isle(veri, manager, routing, solution)
            return self.cozum
        else:
            print("Çözüm bulunamadı!")
            return None
    
    def _cozumu_isle(self, veri, manager, routing, solution):
        """
        OR-Tools çözümünü işle ve formatlı sonuç döndür
        """
        cozum = {
            'rotalar': [],
            'toplam_mesafe': 0,
            'toplam_maliyet': 0,
            'kullanilan_araclar': 0,
            'servis_edilen_musteriler': []
        }
        
        toplam_mesafe = 0
        toplam_maliyet = 0
        
        for arac_id in range(veri['arac_sayisi']):
            index = routing.Start(arac_id)
            rota = {
                'arac_id': arac_id,
                'arac_tipi': self.araclar[arac_id]['tip'],
                'kapasite': self.araclar[arac_id]['kapasite'],
                'duraklar': [],
                'mesafe': 0,
                'maliyet': 0,
                'yuk': 0,
                'zaman_cetveli': []
            }
            
            rota_mesafe = 0
            rota_yuk = 0
            
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                
                # Zaman bilgisini al
                zaman_var = routing.GetDimensionOrDie('Zaman').CumulVar(index)
                zaman = solution.Min(zaman_var)
                
                if node_index == 0:
                    rota['duraklar'].append({
                        'tip': 'Depo',
                        'id': 'DEPO',
                        'koordinat': self.depo_koordinat,
                        'yuk': rota_yuk,
                        'varış_zamani': self._dakika_to_saat(zaman)
                    })
                else:
                    musteri = self.musteriler[node_index - 1]
                    rota_yuk += musteri['talep']
                    rota['duraklar'].append({
                        'tip': 'Müşteri',
                        'id': musteri['id'],
                        'koordinat': musteri['koordinat'],
                        'talep': musteri['talep'],
                        'yuk': rota_yuk,
                        'varış_zamani': self._dakika_to_saat(zaman)
                    })
                    if musteri['id'] not in cozum['servis_edilen_musteriler']:
                        cozum['servis_edilen_musteriler'].append(musteri['id'])
                
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                rota_mesafe += routing.GetArcCostForVehicle(previous_index, index, arac_id) / 1000
            
            # Son depo dönüşü
            node_index = manager.IndexToNode(index)
            zaman_var = routing.GetDimensionOrDie('Zaman').CumulVar(index)
            zaman = solution.Min(zaman_var)
            
            rota['duraklar'].append({
                'tip': 'Depo',
                'id': 'DEPO',
                'koordinat': self.depo_koordinat,
                'yuk': 0,
                'varış_zamani': self._dakika_to_saat(zaman)
            })
            
            rota['mesafe'] = round(rota_mesafe, 2)
            rota['yuk'] = rota_yuk
            rota['maliyet'] = round(rota_mesafe * self.araclar[arac_id]['maliyet_km'], 2)
            
            # Sadece kullanılan araçları ekle
            if len(rota['duraklar']) > 2:  # Depo-Depo'dan fazlası varsa
                cozum['rotalar'].append(rota)
                toplam_mesafe += rota_mesafe
                toplam_maliyet += rota['maliyet']
                cozum['kullanilan_araclar'] += 1
        
        cozum['toplam_mesafe'] = round(toplam_mesafe, 2)
        cozum['toplam_maliyet'] = round(toplam_maliyet, 2)
        
        return cozum
    
    def _dakika_to_saat(self, dakika):
        """Dakikayı saat:dakika formatına çevir"""
        saat = int(dakika // 60)
        dk = int(dakika % 60)
        return f"{saat:02d}:{dk:02d}"
    
    def cozumu_gorsellestir(self, harita_dosyasi=None, google_maps_kullan=False):
        """
        Çözümü interaktif harita üzerinde göster
        
        Args:
            harita_dosyasi: Harita dosya adı
            google_maps_kullan: Google Maps API kullanılsın mı?
        """
        if not self.cozum:
            print("Önce problemi çözmelisiniz!")
            return

        # Google Maps kullanımı kontrolü
        if google_maps_kullan:
            try:
                from .google_maps_integration import GoogleMapsVRP
                google_vrp = GoogleMapsVRP(self)
                return google_vrp.cozumu_google_maps_ile_gorsellestir(harita_dosyasi)
            except ImportError:
                print("⚠️  Google Maps entegrasyonu bulunamadı, standart harita oluşturulacak.")
            except Exception as e:
                print(f"⚠️  Google Maps hatası: {e}, standart harita oluşturulacak.")

        # Standart Folium haritası
        desktop_path = os.path.expanduser("~/Desktop")
        if harita_dosyasi is None:
            harita_dosyasi = "vrp_harita.html"
        tam_yol = os.path.join(desktop_path, harita_dosyasi)

        # Harita oluştur
        m = folium.Map(location=self.depo_koordinat, zoom_start=11)
        
        # Renk paleti
        renkler = ['red', 'blue', 'green', 'purple', 'orange', 
                   'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen',
                   'cadetblue', 'darkpurple', 'white', 'pink', 'lightblue',
                   'lightgreen', 'gray', 'black', 'lightgray']
        
        # Depoyu ekle
        folium.Marker(
            self.depo_koordinat,
            popup=f"<b>DEPO</b>",
            tooltip="Depo",
            icon=folium.Icon(color='black', icon='home', prefix='fa')
        ).add_to(m)
        
        # Her rotayı farklı renkle çiz
        for i, rota in enumerate(self.cozum['rotalar']):
            renk = renkler[i % len(renkler)]
            
            # Rota noktaları
            rota_koordinatlari = [durak['koordinat'] for durak in rota['duraklar']]
            
            # Rota çizgisi
            folium.PolyLine(
                rota_koordinatlari,
                color=renk,
                weight=3,
                opacity=0.8,
                popup=f"Araç {rota['arac_id']} - {rota['arac_tipi']}"
            ).add_to(m)
            
            # Müşteri noktaları
            for j, durak in enumerate(rota['duraklar']):
                if durak['tip'] == 'Müşteri':
                    folium.CircleMarker(
                        durak['koordinat'],
                        radius=8,
                        popup=f"""
                        <b>Müşteri: {durak['id']}</b><br>
                        Talep: {durak['talep']} kg<br>
                        Varış: {durak['varış_zamani']}<br>
                        Araç: {rota['arac_id']} ({rota['arac_tipi']})
                        """,
                        tooltip=f"Müşteri {durak['id']}",
                        color=renk,
                        fill=True,
                        fillOpacity=0.7
                    ).add_to(m)
                    
                    # Sıra numarası ekle
                    folium.Marker(
                        durak['koordinat'],
                        icon=folium.DivIcon(
                            html=f'<div style="font-size: 12pt; color: white; background-color: {renk}; '
                                 f'border-radius: 50%; width: 20px; height: 20px; text-align: center;">'
                                 f'{j}</div>'
                        )
                    ).add_to(m)
        
        # Özet bilgi ekle
        ozet_html = f"""
        <div style="position: fixed; 
                    top: 10px; 
                    right: 10px; 
                    width: 300px; 
                    background-color: white; 
                    z-index: 1000; 
                    border: 2px solid grey; 
                    border-radius: 5px;
                    padding: 10px">
            <h4>VRP Çözüm Özeti</h4>
            <b>Toplam Mesafe:</b> {self.cozum['toplam_mesafe']} km<br>
            <b>Toplam Maliyet:</b> {self.cozum['toplam_maliyet']} TL<br>
            <b>Kullanılan Araç:</b> {self.cozum['kullanilan_araclar']}<br>
            <b>Servis Edilen Müşteri:</b> {len(self.cozum['servis_edilen_musteriler'])}
        </div>
        """
        m.get_root().html.add_child(folium.Element(ozet_html))
        
        # Haritayı kaydet
        m.save(tam_yol)
        print(f"Harita '{tam_yol}' olarak kaydedildi.")
        return m
    
    def cozumu_yazdir(self):
        """
        Çözümü detaylı olarak yazdır
        """
        if not self.cozum:
            print("Önce problemi çözmelisiniz!")
            return
        
        print("\n" + "="*80)
        print("VEHİCLE ROUTİNG PROBLEM ÇÖZÜMÜ")
        print("="*80)
        
        for rota in self.cozum['rotalar']:
            print(f"\n{'-'*60}")
            print(f"ARAÇ {rota['arac_id']} - {rota['arac_tipi']} (Kapasite: {rota['kapasite']} kg)")
            print(f"{'-'*60}")
            print(f"Toplam Mesafe: {rota['mesafe']} km")
            print(f"Toplam Yük: {rota['yuk']} kg")
            print(f"Maliyet: {rota['maliyet']} TL")
            print(f"\nRota Detayı:")
            
            for i, durak in enumerate(rota['duraklar']):
                if durak['tip'] == 'Depo':
                    print(f"  {i}. DEPO - Varış: {durak['varış_zamani']}")
                else:
                    print(f"  {i}. Müşteri {durak['id']} - "
                          f"Talep: {durak['talep']} kg, "
                          f"Varış: {durak['varış_zamani']}, "
                          f"Toplam Yük: {durak['yuk']} kg")
        
        print(f"\n{'='*80}")
        print(f"ÖZET")
        print(f"{'='*80}")
        print(f"Toplam Mesafe: {self.cozum['toplam_mesafe']} km")
        print(f"Toplam Maliyet: {self.cozum['toplam_maliyet']} TL")
        print(f"Kullanılan Araç Sayısı: {self.cozum['kullanilan_araclar']}")
        print(f"Servis Edilen Müşteri Sayısı: {len(self.cozum['servis_edilen_musteriler'])}")
        print("="*80)
    
    def cozumu_kaydet(self, dosya_adi=None):
        """
        Çözümü JSON formatında kaydet
        """
        if not self.cozum:
            print("Önce problemi çözmelisiniz!")
            return

        # Masaüstü yolu
        desktop_path = os.path.expanduser("~/Desktop")
        if dosya_adi is None:
            dosya_adi = "vrp_cozum.json"
        tam_yol = os.path.join(desktop_path, dosya_adi)

        # 'set' tipini 'list'e çevir
        cozum_json = self.cozum.copy()
        cozum_json['servis_edilen_musteriler'] = list(cozum_json['servis_edilen_musteriler'])

        with open(tam_yol, 'w', encoding='utf-8') as f:
            json.dump(cozum_json, f, ensure_ascii=False, indent=2)
        print(f"Çözüm '{tam_yol}' dosyasına kaydedildi.")


class GercekZamanliVRP:
    """
    Gerçek zamanlı VRP çözücü (dinamik müşteri ekleme)
    """
    
    def __init__(self, vrp_cozucu):
        self.vrp = vrp_cozucu
        self.aktif_rotalar = []
        self.bekleyen_musteriler = []
        
    def yeni_musteri_ekle(self, musteri_bilgileri):
        """
        Çalışma zamanında yeni müşteri ekle ve rotaları güncelle
        """
        self.bekleyen_musteriler.append(musteri_bilgileri)
        
        # Belirli sayıda müşteri birikince yeniden optimize et
        if len(self.bekleyen_musteriler) >= 5:
            self.rotalari_guncelle()
    
    def rotalari_guncelle(self):
        """
        Mevcut rotaları yeni müşterilerle güncelle
        """
        for musteri in self.bekleyen_musteriler:
            self.vrp.musteri_ekle(**musteri)
        
        self.bekleyen_musteriler = []
        
        # Yeniden çöz
        yeni_cozum = self.vrp.coz()
        
        if yeni_cozum:
            self.aktif_rotalar = yeni_cozum['rotalar']
            print(f"Rotalar güncellendi! Yeni müşteri sayısı: {len(self.vrp.musteriler)}")
