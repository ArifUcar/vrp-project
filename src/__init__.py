"""
VRP Çözücü Paketi
==================
Vehicle Routing Problem çözücü modülü
"""

from .vrp_cozucu import VRPCozucu, GercekZamanliVRP
from .utils import (
    csv_den_yukle,
    performans_raporu_olustur,
    karsilastirmali_analiz,
    performans_grafigi_olustur,
    ornek_musteri_verisi_olustur,
    ornek_arac_verisi_olustur
)

# Google Maps entegrasyonu (opsiyonel)
try:
    from .google_maps_integration import GoogleMapsAPI, GoogleMapsVRP
    GOOGLE_MAPS_AVAILABLE = True
except ImportError:
    GOOGLE_MAPS_AVAILABLE = False

__version__ = "1.0.0"
__author__ = "VRP Çözücü Ekibi"
__email__ = "vrp@example.com"

__all__ = [
    'VRPCozucu',
    'GercekZamanliVRP',
    'csv_den_yukle',
    'performans_raporu_olustur',
    'karsilastirmali_analiz',
    'performans_grafigi_olustur',
    'ornek_musteri_verisi_olustur',
    'ornek_arac_verisi_olustur',
    'GOOGLE_MAPS_AVAILABLE'
]

# Google Maps modüllerini de ekle
if GOOGLE_MAPS_AVAILABLE:
    __all__.extend(['GoogleMapsAPI', 'GoogleMapsVRP'])
