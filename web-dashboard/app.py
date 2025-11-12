from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt
import json
import requests
from datetime import datetime
import threading
import time
from gemini_config import analyze_environment, get_short_summary, format_for_telegram

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# ===== CẤU HÌNH =====
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_TOPIC_DATA = "iot/env/data"
MQTT_TOPIC_STATUS = "iot/env/status"

THINGSPEAK_CHANNEL = "3123035"
THINGSPEAK_READ_KEY = "OK6322WQLR29O7ZI"

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

latest_ai_analysis = None  # Lưu phân tích AI mới nhất
ai_analysis_interval = 30 * 60  # Mặc định 30 phút
last_ai_analysis_time = 0
ai_enabled = True  # Bật/tắt AI

# ===== MQTT CALLBACKS =====
def on_connect(client, userdata, flags, rc):
    print(f"✓ Da ket noi MQTT! (Ma: {rc})")
    client.subscribe(MQTT_TOPIC_DATA)
    client.subscribe(MQTT_TOPIC_STATUS)

def on_message(client, userdata, msg):
    global latest_data
    
    try:
        if msg.topic == MQTT_TOPIC_DATA:
            data = json.loads(msg.payload.decode())
            data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            latest_data = data
            
            # Gửi qua WebSocket
            socketio.emit('sensor_update', data)
            print(f"📊 Cap nhat: T={data['temp']:.1f}°C, H={data['humid']:.1f}%")
            
        elif msg.topic == MQTT_TOPIC_STATUS:
            status = msg.payload.decode()
            socketio.emit('status_update', {'status': status})
            print(f"📢 Trang thai: {status}")
            
    except Exception as e:
        print(f"✗ Loi xu ly MQTT: {e}")

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def start_mqtt():
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_forever()
    except Exception as e:
        print(f"✗ Loi MQTT: {e}")

# ===== PHÂN TÍCH AI TỰ ĐỘNG =====
def auto_ai_analysis():
    """Chạy phân tích AI định kỳ"""
    global latest_ai_analysis, last_ai_analysis_time
    
    print(f"✓ Da bat phan tich AI tu dong (chu ky: {ai_analysis_interval // 60} phut)")
    
    while True:
        try:
            time.sleep(10)  # Kiểm tra mỗi 10 giây
            
            if not ai_enabled:
                continue
            
            current_time = time.time()
            
            # Kiểm tra đã đến lúc phân tích chưa
            if current_time - last_ai_analysis_time >= ai_analysis_interval:
                print("🤖 Bat dau phan tich AI...")
                
                result = analyze_environment(latest_data)
                
                if result['success']:
                    latest_ai_analysis = result
                    
                    # Gửi qua WebSocket
                    socketio.emit('ai_analysis', {
                        'analysis': result['analysis'],
                        'priority': result['priority'],
                        'timestamp': result['timestamp'],
                        'summary': get_short_summary(result)
                    })
                    
                    print(f"✓ Phan tich AI thanh cong - Muc do: {result['priority']}")
                else:
                    print(f"✗ Loi phan tich AI: {result['error']}")
                
                last_ai_analysis_time = current_time
                
        except Exception as e:
            print(f"✗ Loi phan tich AI tu dong: {e}")

# ===== ROUTES =====
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    """API lấy dữ liệu hiện tại"""
    return jsonify(latest_data)

@app.route('/api/thingspeak')
def get_thingspeak():
    """API lấy dữ liệu từ ThingSpeak"""
    try:
        url = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL}/feeds.json?api_key={THINGSPEAK_READ_KEY}&results=100"
        response = requests.get(url, timeout=10)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/now', methods=['POST'])
def ai_analyze_now():
    """API phân tích AI ngay lập tức"""
    try:
        result = analyze_environment(latest_data)
        
        if result['success']:
            global latest_ai_analysis
            latest_ai_analysis = result
            
            return jsonify({
                'success': True,
                'analysis': result['analysis'],
                'priority': result['priority'],
                'timestamp': result['timestamp'],
                'summary': get_short_summary(result)
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ai/latest')
def get_latest_ai():
    """API lấy phân tích AI mới nhất"""
    if latest_ai_analysis and latest_ai_analysis['success']:
        return jsonify({
            'success': True,
            'analysis': latest_ai_analysis['analysis'],
            'priority': latest_ai_analysis['priority'],
            'timestamp': latest_ai_analysis['timestamp'],
            'summary': get_short_summary(latest_ai_analysis)
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Chưa có phân tích nào'
        })

@app.route('/api/ai/config', methods=['GET', 'POST'])
def ai_config():
    """API cấu hình AI"""
    global ai_analysis_interval, ai_enabled
    
    if request.method == 'POST':
        data = request.json
        
        if 'interval' in data:
            interval_minutes = int(data['interval'])
            if 10 <= interval_minutes <= 120:
                ai_analysis_interval = interval_minutes * 60
                
        if 'enabled' in data:
            ai_enabled = bool(data['enabled'])
        
        return jsonify({
            'success': True,
            'interval_minutes': ai_analysis_interval // 60,
            'enabled': ai_enabled
        })
    else:
        return jsonify({
            'interval_minutes': ai_analysis_interval // 60,
            'enabled': ai_enabled
        })

# ===== WEBSOCKET EVENTS =====
@socketio.on('connect')
def handle_connect():
    print('✓ Client da ket noi WebSocket')
    emit('sensor_update', latest_data)
    
    # Gửi phân tích AI nếu có
    if latest_ai_analysis and latest_ai_analysis['success']:
        emit('ai_analysis', {
            'analysis': latest_ai_analysis['analysis'],
            'priority': latest_ai_analysis['priority'],
            'timestamp': latest_ai_analysis['timestamp'],
            'summary': get_short_summary(latest_ai_analysis)
        })

@socketio.on('disconnect')
def handle_disconnect():
    print('✗ Client da ngat ket noi')

@socketio.on('request_ai_analysis')
def handle_ai_request():
    """Xử lý yêu cầu phân tích AI từ client"""
    try:
        result = analyze_environment(latest_data)
        
        if result['success']:
            global latest_ai_analysis
            latest_ai_analysis = result
            
            emit('ai_analysis', {
                'analysis': result['analysis'],
                'priority': result['priority'],
                'timestamp': result['timestamp'],
                'summary': get_short_summary(result)
            })
        else:
            emit('ai_error', {'error': result['error']})
            
    except Exception as e:
        emit('ai_error', {'error': str(e)})

# ===== MAIN =====
if __name__ == '__main__':
    print("\n" + "="*50)
    print("  🌐 Flask Web Server + AI - IoT Monitor V5.1")
    print("="*50)
    print(f"  MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"  Chu ky AI: {ai_analysis_interval // 60} phut")
    print(f"  Web: http://localhost:5000")
    print("="*50 + "\n")
    
    # Chạy MQTT trong thread riêng
    mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
    mqtt_thread.start()
    
    # Chạy AI analysis trong thread riêng
    ai_thread = threading.Thread(target=auto_ai_analysis, daemon=True)
    ai_thread.start()
    
    # Chạy Flask
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)