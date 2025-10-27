from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt
import json
import threading
from datetime import datetime
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'iot-secret-key-2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Cấu hình MQTT
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_TOPIC_DATA = "iot/env/data"
MQTT_TOPIC_STATUS = "iot/env/status"

# Cấu hình ThingSpeak
THINGSPEAK_CHANNEL_ID = "3123035"
THINGSPEAK_READ_API_KEY = "Z4CZ734O6MNLPA2U"

# Lưu trữ dữ liệu
latest_data = {
    'temp': 0,
    'humid': 0,
    'light_lux': 0,
    'gas_ppm': 0,
    'heat_index': 0,
    'comfort': 0,
    'fan': False,
    'alert': False,
    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
}

history_data = []
max_history = 50

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    print(f"✓ Da ket noi MQTT Broker! (Ma: {rc})")
    client.subscribe(MQTT_TOPIC_DATA)
    client.subscribe(MQTT_TOPIC_STATUS)
    print(f"📡 Da dang ky:")
    print(f"   - {MQTT_TOPIC_DATA}")
    print(f"   - {MQTT_TOPIC_STATUS}")

def on_message(client, userdata, msg):
    global latest_data, history_data
    
    try:
        if msg.topic == MQTT_TOPIC_DATA:
            data = json.loads(msg.payload.decode())
            data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            latest_data = data
            
            history_data.append(data)
            if len(history_data) > max_history:
                history_data.pop(0)
            
            socketio.emit('sensor_update', data)
            
            print(f"📊 T={data['temp']}°C, H={data['humid']}%, L={data['light_lux']}Lux, G={data['gas_ppm']}PPM, Quat={'BAT' if data['fan'] else 'TAT'}")
            
        elif msg.topic == MQTT_TOPIC_STATUS:
            status = msg.payload.decode()
            print(f"📢 Trang thai: {status}")
            socketio.emit('status_update', {'status': status})
            
    except json.JSONDecodeError as e:
        print(f"✗ Loi JSON: {e}")
    except Exception as e:
        print(f"✗ Loi: {e}")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"⚠️ Mat ket noi MQTT. Dang ket noi lai...")

# Khởi tạo MQTT
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.on_disconnect = on_disconnect

def start_mqtt():
    try:
        print(f"🔌 Dang ket noi MQTT: {MQTT_BROKER}:{MQTT_PORT}")
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_forever()
    except Exception as e:
        print(f"✗ Loi MQTT: {e}")

mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
mqtt_thread.start()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    return jsonify(latest_data)

@app.route('/api/history')
def get_history():
    return jsonify(history_data)

@app.route('/api/thingspeak')
def get_thingspeak():
    try:
        url = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/feeds.json"
        params = {
            'results': 20,
            'api_key': THINGSPEAK_READ_API_KEY
        }
        print(f"📡 Dang lay du lieu ThingSpeak...")
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'feeds' in data:
            print(f"✓ Da lay {len(data['feeds'])} ban ghi")
        
        return jsonify(data)
    except Exception as e:
        print(f"✗ Loi ThingSpeak: {e}")
        return jsonify({'error': str(e)}), 500

# SocketIO Events
@socketio.on('connect')
def handle_connect():
    print('✓ Khach web da ket noi')
    emit('sensor_update', latest_data)

@socketio.on('disconnect')
def handle_disconnect():
    print('✗ Khach web mat ket noi')

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  🌐 Hệ Thống Giám Sát Môi Trường IoT V5.1")
    print("="*60)
    print(f"  MQTT Broker   : {MQTT_BROKER}:{MQTT_PORT}")
    print(f"  ThingSpeak ID : {THINGSPEAK_CHANNEL_ID}")
    print(f"  URL may chu   : http://localhost:5000")
    print("="*60)
    print("  📝 Tinh nang:")
    print("     - Quat tu dong (BAT: ≥30°C, TAT: ≤28°C)")
    print("     - Tinh toan chi so thoai mai")
    print("     - Giam sat chi so nhiet")
    print("     - CHE DO THU: Gia tri cam bien ngau nhien de kiem tra")
    print("     - CHE DO THAT: Doc du lieu cam bien thuc te")
    print("="*60 + "\n")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)