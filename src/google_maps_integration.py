"""
Google Maps API Entegrasyonu
============================
Bu modül, Google Maps API ile gerçek mesafe ve süre hesaplamaları yapar.
"""

import os
import requests
import time
import json
from typing import List, Tuple, Dict, Optional
import numpy as np
from dotenv import load_dotenv

# Environment dosyasını yükle
load_dotenv('environment.env')


class GoogleMapsAPI:
    """
    Google Maps API ile çalışma sınıfı
    """
    
    def __init__(self):
        """
        Google Maps API başlatıcı
        """
        self.api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        self.base_url = "https://maps.googleapis.com/maps/api"
        self.max_requests_per_minute = int(os.getenv('MAX_REQUESTS_PER_MINUTE', 50))
        self.debug_mode = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
        
        # Rate limiting için
        self.last_request_time = 0
        self.request_count = 0
        
        if not self.api_key or self.api_key == 'your_google_maps_api_key_here':
            print("⚠️  UYARI: Google Maps API anahtarı bulunamadı!")
            print("   environment.env dosyasına GOOGLE_MAPS_API_KEY ekleyin.")
            self.api_available = False
        else:
            self.api_available = True
            print("✅ Google Maps API hazır!")
    
    def _rate_limit(self):
        """
        API rate limiting uygula
        """
        current_time = time.time()
        if current_time - self.last_request_time < 60:  # Son 1 dakika içinde
            self.request_count += 1
            if self.request_count >= self.max_requests_per_minute:
                sleep_time = 60 - (current_time - self.last_request_time)
                if self.debug_mode:
                    print(f"⏳ Rate limit: {sleep_time:.1f} saniye bekleniyor...")
                time.sleep(sleep_time)
                self.request_count = 0
                self.last_request_time = time.time()
        else:
            self.request_count = 0
            self.last_request_time = current_time
    
    def _make_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """
        Google Maps API'ye istek gönder
        """
        if not self.api_available:
            return None
        
        self._rate_limit()
        
        params['key'] = self.api_key
        url = f"{self.base_url}/{endpoint}/json"
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') != 'OK':
                print(f"❌ API Hatası: {data.get('status')} - {data.get('error_message', 'Bilinmeyen hata')}")
                return None
            
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ İstek hatası: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse hatası: {e}")
            return None
    
    def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Adresi koordinatlara çevir
        
        Args:
            address: Adres string'i
            
        Returns:
            (lat, lon) tuple veya None
        """
        params = {
            'address': address,
            'language': os.getenv('DEFAULT_LANGUAGE', 'tr')
        }
        
        data = self._make_request('geocode', params)
        if data and data.get('results'):
            location = data['results'][0]['geometry']['location']
            return (location['lat'], location['lng'])
        
        return None
    
    def reverse_geocode(self, lat: float, lon: float) -> Optional[str]:
        """
        Koordinatları adrese çevir
        
        Args:
            lat: Enlem
            lon: Boylam
            
        Returns:
            Adres string'i veya None
        """
        params = {
            'latlng': f"{lat},{lon}",
            'language': os.getenv('DEFAULT_LANGUAGE', 'tr')
        }
        
        data = self._make_request('geocode', params)
        if data and data.get('results'):
            return data['results'][0]['formatted_address']
        
        return None
    
    def get_distance_matrix(self, origins: List[Tuple[float, float]], 
                           destinations: List[Tuple[float, float]]) -> Optional[np.ndarray]:
        """
        Mesafe matrisi al
        
        Args:
            origins: Başlangıç noktaları [(lat, lon), ...]
            destinations: Varış noktaları [(lat, lon), ...]
            
        Returns:
            Mesafe matrisi (numpy array) veya None
        """
        if not self.api_available:
            return None
        
        # Google Maps API maksimum 25x25 matris destekler
        if len(origins) > 25 or len(destinations) > 25:
            print("⚠️  UYARI: Google Maps API maksimum 25x25 matris destekler!")
            print("   Haversine formülü kullanılacak.")
            return None
        
        # Koordinatları string'e çevir
        origins_str = [f"{lat},{lon}" for lat, lon in origins]
        destinations_str = [f"{lat},{lon}" for lat, lon in destinations]
        
        params = {
            'origins': '|'.join(origins_str),
            'destinations': '|'.join(destinations_str),
            'mode': os.getenv('DEFAULT_TRAVEL_MODE', 'driving'),
            'units': os.getenv('DEFAULT_UNITS', 'metric'),
            'language': os.getenv('DEFAULT_LANGUAGE', 'tr')
        }
        
        data = self._make_request('distancematrix', params)
        if not data:
            return None
        
        # Mesafe matrisini oluştur
        matrix = np.zeros((len(origins), len(destinations)))
        
        for i, row in enumerate(data['rows']):
            for j, element in enumerate(row['elements']):
                if element['status'] == 'OK':
                    # Mesafe (metre cinsinden)
                    distance = element['distance']['value']
                    matrix[i][j] = distance / 1000  # km'ye çevir
                else:
                    print(f"⚠️  Mesafe hesaplanamadı: {element.get('status')}")
                    matrix[i][j] = float('inf')
        
        return matrix
    
    def get_directions(self, origin: Tuple[float, float], 
                      destination: Tuple[float, float]) -> Optional[Dict]:
        """
        İki nokta arası rota bilgisi al
        
        Args:
            origin: Başlangıç koordinatı (lat, lon)
            destination: Varış koordinatı (lat, lon)
            
        Returns:
            Rota bilgileri dictionary'si veya None
        """
        params = {
            'origin': f"{origin[0]},{origin[1]}",
            'destination': f"{destination[0]},{destination[1]}",
            'mode': os.getenv('DEFAULT_TRAVEL_MODE', 'driving'),
            'units': os.getenv('DEFAULT_UNITS', 'metric'),
            'language': os.getenv('DEFAULT_LANGUAGE', 'tr')
        }
        
        data = self._make_request('directions', params)
        if not data or not data.get('routes'):
            return None
        
        route = data['routes'][0]
        leg = route['legs'][0]
        
        return {
            'distance': leg['distance']['value'] / 1000,  # km
            'duration': leg['duration']['value'] / 60,    # dakika
            'start_address': leg['start_address'],
            'end_address': leg['end_address'],
            'steps': leg['steps']
        }
    
    def get_traffic_aware_distance(self, origin: Tuple[float, float], 
                                  destination: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        """
        Trafik bilgisi ile mesafe ve süre al
        
        Args:
            origin: Başlangıç koordinatı (lat, lon)
            destination: Varış koordinatı (lat, lon)
            
        Returns:
            (mesafe_km, süre_dakika) tuple veya None
        """
        params = {
            'origin': f"{origin[0]},{origin[1]}",
            'destination': f"{destination[0]},{destination[1]}",
            'mode': os.getenv('DEFAULT_TRAVEL_MODE', 'driving'),
            'units': os.getenv('DEFAULT_UNITS', 'metric'),
            'language': os.getenv('DEFAULT_LANGUAGE', 'tr'),
            'departure_time': 'now',  # Gerçek zamanlı trafik
            'traffic_model': 'best_guess'
        }
        
        data = self._make_request('directions', params)
        if not data or not data.get('routes'):
            return None
        
        route = data['routes'][0]
        leg = route['legs'][0]
        
        distance_km = leg['distance']['value'] / 1000
        duration_min = leg['duration']['value'] / 60
        
        return (distance_km, duration_min)


class GoogleMapsVRP:
    """
    Google Maps API ile gelişmiş VRP çözücü
    """
    
    def __init__(self, vrp_cozucu):
        """
        Args:
            vrp_cozucu: Mevcut VRP çözücü instance'ı
        """
        self.vrp = vrp_cozucu
        self.google_maps = GoogleMapsAPI()
        
    def gercek_mesafe_matrisi_olustur(self) -> Optional[np.ndarray]:
        """
        Google Maps API ile gerçek mesafe matrisi oluştur
        """
        if not self.google_maps.api_available:
            print("⚠️  Google Maps API kullanılamıyor, Haversine formülü kullanılacak.")
            return self.vrp.mesafe_matrisi_olustur()
        
        print("🗺️  Google Maps API ile gerçek mesafe matrisi oluşturuluyor...")
        
        # Tüm lokasyonlar (depo + müşteriler)
        lokasyonlar = [self.vrp.depo_koordinat] + [m['koordinat'] for m in self.vrp.musteriler]
        
        # Google Maps API ile mesafe matrisi al
        mesafe_matrisi = self.google_maps.get_distance_matrix(lokasyonlar, lokasyonlar)
        
        if mesafe_matrisi is not None:
            self.vrp.mesafe_matrisi = mesafe_matrisi
            # Zaman matrisi için Google Maps'ten gerçek süreleri al
            self.vrp.zaman_matrisi = self._gercek_zaman_matrisi_olustur(lokasyonlar)
            print("✅ Google Maps mesafe matrisi oluşturuldu!")
            return mesafe_matrisi
        else:
            print("⚠️  Google Maps API hatası, Haversine formülü kullanılacak.")
            return self.vrp.mesafe_matrisi_olustur()
    
    def _gercek_zaman_matrisi_olustur(self, lokasyonlar: List[Tuple[float, float]]) -> np.ndarray:
        """
        Google Maps API ile gerçek zaman matrisi oluştur
        """
        n = len(lokasyonlar)
        zaman_matrisi = np.zeros((n, n))
        
        print("⏱️  Gerçek zaman bilgileri alınıyor...")
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    # Google Maps'ten gerçek süre al
                    result = self.google_maps.get_traffic_aware_distance(
                        lokasyonlar[i], lokasyonlar[j]
                    )
                    
                    if result:
                        mesafe_km, sure_dakika = result
                        zaman_matrisi[i][j] = sure_dakika
                    else:
                        # Fallback: mesafeden hesapla
                        mesafe_km = self.vrp.mesafe_matrisi[i][j]
                        zaman_matrisi[i][j] = (mesafe_km / 40) * 60  # 40 km/h varsayılan hız
        
        return zaman_matrisi
    
    def rota_detaylarini_al(self, rota_koordinatlari: List[Tuple[float, float]]) -> List[Dict]:
        """
        Rota için detaylı Google Maps bilgileri al
        
        Args:
            rota_koordinatlari: Rota noktaları [(lat, lon), ...]
            
        Returns:
            Rota detayları listesi
        """
        if not self.google_maps.api_available:
            return []
        
        rota_detaylari = []
        
        for i in range(len(rota_koordinatlari) - 1):
            origin = rota_koordinatlari[i]
            destination = rota_koordinatlari[i + 1]
            
            directions = self.google_maps.get_directions(origin, destination)
            if directions:
                rota_detaylari.append({
                    'from': origin,
                    'to': destination,
                    'distance_km': directions['distance'],
                    'duration_min': directions['duration'],
                    'start_address': directions['start_address'],
                    'end_address': directions['end_address'],
                    'steps': directions['steps']
                })
        
        return rota_detaylari
    
    def cozumu_google_maps_ile_gorsellestir(self, harita_dosyasi: str = "google_maps_harita.html"):
        """
        Google Maps ile çözümü görselleştir
        """
        if not self.google_maps.api_available:
            print("⚠️  Google Maps API kullanılamıyor, standart harita oluşturulacak.")
            return self.vrp.cozumu_gorsellestir(harita_dosyasi)
        
        if not self.vrp.cozum:
            print("Önce problemi çözmelisiniz!")
            return
        
        print("🗺️  Google Maps ile harita oluşturuluyor...")
        
        # HTML template
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>VRP Çözümü - Google Maps</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://maps.googleapis.com/maps/api/js?key={self.google_maps.api_key}&libraries=geometry"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; }}
        #map {{ height: 100vh; width: 100%; }}
        #info {{ position: absolute; top: 10px; right: 10px; background: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); max-width: 300px; }}
        .route-info {{ margin: 10px 0; padding: 10px; background: #f5f5f5; border-radius: 3px; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div id="info">
        <h3>🚛 VRP Çözüm Özeti</h3>
        <p><strong>Toplam Mesafe:</strong> {self.vrp.cozum['toplam_mesafe']} km</p>
        <p><strong>Toplam Maliyet:</strong> {self.vrp.cozum['toplam_maliyet']} TL</p>
        <p><strong>Kullanılan Araç:</strong> {self.vrp.cozum['kullanilan_araclar']}</p>
        <p><strong>Servis Edilen Müşteri:</strong> {len(self.vrp.cozum['servis_edilen_musteriler'])}</p>
    </div>

    <script>
        function initMap() {{
            // Harita merkezi (depo)
            const center = {{ lat: {self.vrp.depo_koordinat[0]}, lng: {self.vrp.depo_koordinat[1]} }};
            
            const map = new google.maps.Map(document.getElementById("map"), {{
                zoom: 11,
                center: center,
                mapTypeId: 'roadmap'
            }});
            
            // Renkler
            const colors = ['#FF0000', '#0000FF', '#00FF00', '#FF00FF', '#FFA500', '#800080', '#008000', '#000080'];
            
            // Depo marker'ı
            new google.maps.Marker({{
                position: center,
                map: map,
                title: 'DEPO',
                icon: {{
                    url: 'https://maps.google.com/mapfiles/ms/icons/red-dot.png',
                    scaledSize: new google.maps.Size(30, 30)
                }}
            }});
            
            // Rotaları çiz
            {self._generate_route_script()}
        }}
    </script>
    
    <script async defer src="https://maps.googleapis.com/maps/api/js?key={self.google_maps.api_key}&callback=initMap"></script>
</body>
</html>
        """
        
        # Dosyayı kaydet
        output_path = os.path.join("output", harita_dosyasi)
        os.makedirs("output", exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Google Maps haritası '{output_path}' olarak kaydedildi!")
        return output_path
    
    def _generate_route_script(self) -> str:
        """
        Rota çizimi için JavaScript kodu oluştur (Directions API ile gerçek yollar)
        """
        script_parts = []
        colors = ['#FF0000', '#0000FF', '#00FF00', '#FF00FF', '#FFA500', '#800080', '#008000', '#000080']
        
        script_parts.append("""
        // Directions Service ve Renderer
        const directionsService = new google.maps.DirectionsService();
        const directionsRenderer = new google.maps.DirectionsRenderer({
            suppressMarkers: true,
            preserveViewport: true
        });
        directionsRenderer.setMap(map);
        
        // Rota çizme fonksiyonu
        function drawRoute(waypoints, color, routeIndex) {
            const request = {
                origin: waypoints[0],
                destination: waypoints[waypoints.length - 1],
                waypoints: waypoints.slice(1, -1).map(point => ({
                    location: point,
                    stopover: true
                })),
                travelMode: google.maps.TravelMode.DRIVING,
                optimizeWaypoints: false
            };
            
            directionsService.route(request, function(result, status) {
                if (status === 'OK') {
                    const renderer = new google.maps.DirectionsRenderer({
                        suppressMarkers: true,
                        polylineOptions: {
                            strokeColor: color,
                            strokeWeight: 4,
                            strokeOpacity: 0.8
                        }
                    });
                    renderer.setDirections(result);
                    renderer.setMap(map);
                } else {
                    console.log('Rota çizilemedi:', status);
                }
            });
        }
        
        // Rotaları çiz
        """)
        
        for i, rota in enumerate(self.vrp.cozum['rotalar']):
            color = colors[i % len(colors)]
            
            # Rota koordinatları
            coordinates = [f"{{lat: {durak['koordinat'][0]}, lng: {durak['koordinat'][1]}}}" 
                          for durak in rota['duraklar']]
            
            script_parts.append(f"""
            // Araç {rota['arac_id']} - {rota['arac_tipi']} rotası
            const route{i}Waypoints = [{', '.join(coordinates)}];
            drawRoute(route{i}Waypoints, '{color}', {i});
            """)
            
            # Müşteri marker'ları
            for j, durak in enumerate(rota['duraklar']):
                if durak['tip'] == 'Müşteri':
                    script_parts.append(f"""
                    new google.maps.Marker({{
                        position: {{lat: {durak['koordinat'][0]}, lng: {durak['koordinat'][1]}}},
                        map: map,
                        title: 'Müşteri {durak['id']} - {durak['talep']} kg - Sıra: {j}',
                        icon: {{
                            url: 'https://maps.google.com/mapfiles/ms/icons/blue-dot.png',
                            scaledSize: new google.maps.Size(25, 25)
                        }},
                        label: {{
                            text: '{j}',
                            color: 'white',
                            fontWeight: 'bold',
                            fontSize: '12px'
                        }}
                    }});
                    """)
        
        return '\n'.join(script_parts)
