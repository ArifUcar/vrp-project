"""
VRP Web Paneli
===============
Kullanıcı dostu web arayüzü ile VRP problemi oluşturma ve çözme
"""

import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for
import sys
sys.path.append('src')

from src.vrp_cozucu import VRPCozucu
from src.google_maps_integration import GoogleMapsVRP

app = Flask(__name__)

# Global VRP instance
current_vrp = None
current_solution = None

@app.route('/')
def index():
    """Ana sayfa"""
    return render_template('index.html')

@app.route('/araclar')
def araclar():
    """Araç yönetimi sayfası"""
    return render_template('araclar.html')

@app.route('/musteriler')
def musteriler():
    """Müşteri yönetimi sayfası"""
    return render_template('musteriler.html')

@app.route('/cozum')
def cozum():
    """Çözüm görüntüleme sayfası"""
    return render_template('cozum.html')

@app.route('/api/arac-ekle', methods=['POST'])
def api_arac_ekle():
    """API: Yeni araç ekle"""
    global current_vrp
    
    data = request.json
    
    if not current_vrp:
        current_vrp = VRPCozucu()
    
    try:
        current_vrp.arac_ekle(
            arac_id=data['arac_id'],
            kapasite_kg=int(data['kapasite_kg']),
            maliyet_km=float(data['maliyet_km']),
            max_mesafe_km=int(data['max_mesafe_km']),
            hiz_kmh=int(data['hiz_kmh']),
            tip=data['tip']
        )
        
        return jsonify({
            'success': True,
            'message': f'Araç {data["arac_id"]} başarıyla eklendi!',
            'araclar': len(current_vrp.araclar)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        })

@app.route('/api/musteri-ekle', methods=['POST'])
def api_musteri_ekle():
    """API: Yeni müşteri ekle"""
    global current_vrp
    
    data = request.json
    
    if not current_vrp:
        current_vrp = VRPCozucu()
    
    try:
        current_vrp.musteri_ekle(
            musteri_id=data['musteri_id'],
            koordinat=(float(data['lat']), float(data['lon'])),
            talep_kg=int(data['talep_kg']),
            zaman_penceresi=(int(data['zaman_baslangic']), int(data['zaman_bitis'])),
            servis_suresi=int(data['servis_suresi'])
        )
        
        return jsonify({
            'success': True,
            'message': f'Müşteri {data["musteri_id"]} başarıyla eklendi!',
            'musteriler': len(current_vrp.musteriler)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        })

@app.route('/api/araclar', methods=['GET'])
def api_araclar():
    """API: Araç listesini getir"""
    global current_vrp
    
    if not current_vrp:
        return jsonify({'araclar': []})
    
    return jsonify({'araclar': current_vrp.araclar})

@app.route('/api/musteriler', methods=['GET'])
def api_musteriler():
    """API: Müşteri listesini getir"""
    global current_vrp
    
    if not current_vrp:
        return jsonify({'musteriler': []})
    
    return jsonify({'musteriler': current_vrp.musteriler})

@app.route('/api/arac-sil/<arac_id>', methods=['DELETE'])
def api_arac_sil(arac_id):
    """API: Araç sil"""
    global current_vrp
    
    if not current_vrp:
        return jsonify({'success': False, 'message': 'VRP bulunamadı!'})
    
    # Araçları filtrele
    current_vrp.araclar = [a for a in current_vrp.araclar if a['id'] != arac_id]
    
    return jsonify({
        'success': True,
        'message': f'Araç {arac_id} silindi!',
        'araclar': len(current_vrp.araclar)
    })

@app.route('/api/musteri-sil/<musteri_id>', methods=['DELETE'])
def api_musteri_sil(musteri_id):
    """API: Müşteri sil"""
    global current_vrp
    
    if not current_vrp:
        return jsonify({'success': False, 'message': 'VRP bulunamadı!'})
    
    # Müşterileri filtrele
    current_vrp.musteriler = [m for m in current_vrp.musteriler if m['id'] != musteri_id]
    
    return jsonify({
        'success': True,
        'message': f'Müşteri {musteri_id} silindi!',
        'musteriler': len(current_vrp.musteriler)
    })

@app.route('/api/coz', methods=['POST'])
def api_coz():
    """API: VRP problemini çöz"""
    global current_vrp, current_solution
    
    if not current_vrp:
        return jsonify({'success': False, 'message': 'Önce araç ve müşteri ekleyin!'})
    
    if len(current_vrp.araclar) == 0:
        return jsonify({'success': False, 'message': 'En az bir araç ekleyin!'})
    
    if len(current_vrp.musteriler) == 0:
        return jsonify({'success': False, 'message': 'En az bir müşteri ekleyin!'})
    
    try:
        data = request.json
        google_maps_kullan = data.get('google_maps_kullan', False)
        zaman_limiti = data.get('zaman_limiti', 30)
        esnek_kisitlamalar = data.get('esnek_kisitlamalar', True)
        
        # Mesafe matrisi oluştur
        current_vrp.mesafe_matrisi_olustur(google_maps_kullan=google_maps_kullan)
        
        # Problemi çöz
        current_solution = current_vrp.coz(zaman_limiti=zaman_limiti, esnek_kisitlamalar=esnek_kisitlamalar)
        
        if current_solution:
            return jsonify({
                'success': True,
                'message': 'Çözüm bulundu!',
                'cozum': current_solution
            })
        else:
            # Debug bilgileri topla
            debug_info = {
                'arac_sayisi': len(current_vrp.araclar),
                'musteri_sayisi': len(current_vrp.musteriler),
                'toplam_talep': sum(m['talep'] for m in current_vrp.musteriler),
                'toplam_kapasite': sum(a['kapasite'] for a in current_vrp.araclar),
                'depo_ayarli': current_vrp.depo_koordinat is not None,
                'mesafe_matrisi_var': hasattr(current_vrp, 'mesafe_matrisi') and current_vrp.mesafe_matrisi is not None
            }
            
            return jsonify({
                'success': False,
                'message': 'Çözüm bulunamadı! Kısıtlamaları gevşetmeyi deneyin.',
                'debug_info': debug_info
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        })

@app.route('/api/harita-olustur', methods=['POST'])
def api_harita_olustur():
    """API: Harita oluştur"""
    global current_vrp, current_solution
    
    if not current_solution:
        return jsonify({'success': False, 'message': 'Önce problemi çözün!'})
    
    try:
        data = request.json
        google_maps_kullan = data.get('google_maps_kullan', False)
        harita_adi = data.get('harita_adi', 'vrp_harita.html')
        
        # Harita oluştur
        harita_yolu = current_vrp.cozumu_gorsellestir(
            harita_dosyasi=harita_adi,
            google_maps_kullan=google_maps_kullan
        )
        
        return jsonify({
            'success': True,
            'message': 'Harita oluşturuldu!',
            'harita_yolu': harita_yolu
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        })

@app.route('/api/depo-ayarla', methods=['POST'])
def api_depo_ayarla():
    """API: Depo koordinatlarını ayarla"""
    global current_vrp
    
    data = request.json
    
    if not current_vrp:
        current_vrp = VRPCozucu()
    
    try:
        current_vrp.depo_koordinat = (float(data['lat']), float(data['lon']))
        
        return jsonify({
            'success': True,
            'message': 'Depo koordinatları güncellendi!',
            'depo': current_vrp.depo_koordinat
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        })

@app.route('/api/durum', methods=['GET'])
def api_durum():
    """API: Sistem durumunu getir"""
    global current_vrp, current_solution
    
    durum = {
        'vrp_var': current_vrp is not None,
        'arac_sayisi': len(current_vrp.araclar) if current_vrp else 0,
        'musteri_sayisi': len(current_vrp.musteriler) if current_vrp else 0,
        'cozum_var': current_solution is not None,
        'depo': current_vrp.depo_koordinat if current_vrp else None
    }
    
    return jsonify(durum)

if __name__ == '__main__':
    # Templates klasörünü oluştur
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    print("🚛 VRP Web Paneli başlatılıyor...")
    print("📱 Tarayıcınızda http://localhost:8080 adresini açın")
    
    app.run(debug=True, host='0.0.0.0', port=8080)
