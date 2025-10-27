from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt
import json
import threading
from datetime import datetime
import requests

ung_dung = Flask(__name__)
ung_dung.config['SECRET_KEY'] = 'iot-khoa-bi-mat-2024'
socketio = SocketIO(ung_dung, cors_allowed_origins="*")

# Cấu hình MQTT
MAY_CHU_MQTT = "test.mosquitto.org"
CONG_MQTT = 1883
CHU_DE_DU_LIEU = "iot/moitruong/dulieu"
CHU_DE_TRANG_THAI = "iot/moitruong/trangthai"

# Cấu hình ThingSpeak
MA_KENH_THINGSPEAK = "3123035"
KHAI_DOC_THINGSPEAK = "Z4CZ734O6MNLPA2U"

# Lưu trữ dữ liệu
du_lieu_moi_nhat = {
    'nhiet_do': 0,
    'do_am': 0,
    'anh_sang_lux': 0,
    'khi_ppm': 0,
    'chi_so_nhiet': 0,
    'thoai_mai': 0,
    'quat': False,
    'canh_bao': False,
    'thoi_gian': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
}

du_lieu_lich_su = []
toi_da_lich_su = 50

# MQTT Callbacks
def khi_ket_noi(khach, du_lieu_nguoi_dung, co, ma_ket_qua):
    print(f"✓ Da ket noi MQTT Broker! (Ma: {ma_ket_qua})")
    khach.subscribe(CHU_DE_DU_LIEU)
    khach.subscribe(CHU_DE_TRANG_THAI)
    print(f"📡 Da dang ky:")
    print(f"   - {CHU_DE_DU_LIEU}")
    print(f"   - {CHU_DE_TRANG_THAI}")

def khi_nhan_tin(khach, du_lieu_nguoi_dung, tin):
    global du_lieu_moi_nhat, du_lieu_lich_su
    
    try:
        if tin.topic == CHU_DE_DU_LIEU:
            du_lieu = json.loads(tin.payload.decode())
            du_lieu['thoi_gian'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            du_lieu_moi_nhat = du_lieu
            
            du_lieu_lich_su.append(du_lieu)
            if len(du_lieu_lich_su) > toi_da_lich_su:
                du_lieu_lich_su.pop(0)
            
            socketio.emit('sensor_update', du_lieu)
            
            print(f"📊 T={du_lieu['nhiet_do']}°C, H={du_lieu['do_am']}%, L={du_lieu['anh_sang_lux']}Lux, G={du_lieu['khi_ppm']}PPM, Quat={'BAT' if du_lieu['quat'] else 'TAT'}")
            
        elif tin.topic == CHU_DE_TRANG_THAI:
            trang_thai = tin.payload.decode()
            print(f"📢 Trang thai: {trang_thai}")
            socketio.emit('status_update', {'trang_thai': trang_thai})
            
    except json.JSONDecodeError as loi:
        print(f"✗ Loi JSON: {loi}")
    except Exception as loi:
        print(f"✗ Loi: {loi}")

def khi_mat_ket_noi(khach, du_lieu_nguoi_dung, ma_ket_qua):
    if ma_ket_qua != 0:
        print(f"⚠️ Mat ket noi MQTT. Dang ket noi lai...")

# Khởi tạo MQTT
khach_mqtt = mqtt.Client()
khach_mqtt.on_connect = khi_ket_noi
khach_mqtt.on_message = khi_nhan_tin
khach_mqtt.on_disconnect = khi_mat_ket_noi

def khoi_dong_mqtt():
    try:
        print(f"🔌 Dang ket noi MQTT: {MAY_CHU_MQTT}:{CONG_MQTT}")
        khach_mqtt.connect(MAY_CHU_MQTT, CONG_MQTT, 60)
        khach_mqtt.loop_forever()
    except Exception as loi:
        print(f"✗ Loi MQTT: {loi}")

luong_mqtt = threading.Thread(target=khoi_dong_mqtt, daemon=True)
luong_mqtt.start()

# Định tuyến (Routes)
@ung_dung.route('/')
def trang_chu():
    return render_template('index.html')

@ung_dung.route('/api/data')
@ung_dung.route('/api/dulieu')
def lay_du_lieu():
    return jsonify(du_lieu_moi_nhat)

@ung_dung.route('/api/history')
@ung_dung.route('/api/lichsu')
def lay_lich_su():
    return jsonify(du_lieu_lich_su)

@ung_dung.route('/api/thingspeak')
def lay_thingspeak():
    try:
        duong_dan = f"https://api.thingspeak.com/channels/{MA_KENH_THINGSPEAK}/feeds.json"
        tham_so = {
            'results': 20,
            'api_key': KHAI_DOC_THINGSPEAK
        }
        print(f"📡 Dang lay du lieu ThingSpeak...")
        phan_hoi = requests.get(duong_dan, params=tham_so, timeout=10)
        du_lieu = phan_hoi.json()
        
        if 'feeds' in du_lieu:
            print(f"✓ Da lay {len(du_lieu['feeds'])} ban ghi")
        
        return jsonify(du_lieu)
    except Exception as loi:
        print(f"✗ Loi ThingSpeak: {loi}")
        return jsonify({'loi': str(loi)}), 500

# Sự kiện SocketIO
@socketio.on('connect')
def xu_ly_ket_noi():
    print('✓ Khach web da ket noi')
    emit('sensor_update', du_lieu_moi_nhat)

@socketio.on('disconnect')
def xu_ly_mat_ket_noi():
    print('✗ Khach web mat ket noi')

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  🌐 Hệ Thống Giám Sát Môi Trường IoT V5.1")
    print("="*60)
    print(f"  MQTT Broker   : {MAY_CHU_MQTT}:{CONG_MQTT}")
    print(f"  ThingSpeak ID : {MA_KENH_THINGSPEAK}")
    print(f"  URL máy chủ   : http://localhost:5000")
    print("="*60)
    print("  📝 Tính năng:")
    print("     - Quạt tự động (BẬT: ≥30°C, TẮT: ≤28°C)")
    print("     - Tính toán chỉ số thoải mái")
    print("     - Giám sát chỉ số nhiệt")
    print("     - CHẾ ĐỘ THỬ: Giá trị cảm biến ngẫu nhiên để kiểm tra")
    print("     - CHẾ ĐỘ THẬT: Đọc dữ liệu cảm biến thực tế")
    print("="*60 + "\n")
    
    socketio.run(ung_dung, host='0.0.0.0', port=5000, debug=True)