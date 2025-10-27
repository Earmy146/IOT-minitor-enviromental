import telebot
from telebot import types
import paho.mqtt.client as mqtt
import json
import threading
import time
from datetime import datetime

# ===== CẤU HÌNH =====
TELEGRAM_TOKEN = "8494895987:AAHC0g2pnAHnjx-vw9JY1aqNhkT5J2qI1FA"
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_TOPIC_DATA = "iot/env/data"
MQTT_TOPIC_STATUS = "iot/env/status"

# Thời gian gửi dữ liệu tự động (giây)
AUTO_SEND_INTERVAL = 30  # 5 phút

bot = telebot.TeleBot(TELEGRAM_TOKEN)

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

# Danh sách users
subscribed_users = set()
auto_data_users = set()
alert_sent = {}

# ===== MQTT CALLBACKS =====
def on_connect(client, userdata, flags, rc):
    print(f"✓ Connected to MQTT! (Code: {rc})")
    client.subscribe(MQTT_TOPIC_DATA)
    client.subscribe(MQTT_TOPIC_STATUS)

def on_message(client, userdata, msg):
    global latest_data
    
    try:
        if msg.topic == MQTT_TOPIC_DATA:
            data = json.loads(msg.payload.decode())
            data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            latest_data = data
            check_alerts(data)
        elif msg.topic == MQTT_TOPIC_STATUS:
            status = msg.payload.decode()
            print(f"📢 Status: {status}")
    except Exception as e:
        print(f"✗ Error: {e}")

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def start_mqtt():
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_forever()
    except Exception as e:
        print(f"✗ MQTT Error: {e}")

# ===== GỬI DỮ LIỆU TỰ ĐỘNG =====
def auto_send_data():
    print(f"✓ Auto-send started (interval: {AUTO_SEND_INTERVAL}s)")
    
    while True:
        try:
            time.sleep(AUTO_SEND_INTERVAL)
            
            if not auto_data_users:
                continue
            
            data = latest_data
            alert_emoji = '🚨' if data['alert'] else '✅'
            fan_emoji = '🌀' if data['fan'] else '❌'
            comfort_emoji = '😊' if data['comfort'] >= 80 else '🙂' if data['comfort'] >= 60 else '😟'
            
            data_text = f"""
📊 <b>CẬP NHẬT TỰ ĐỘNG</b>

🌡️ <b>Nhiệt độ:</b> {data['temp']:.1f}°C
💧 <b>Độ ẩm:</b> {data['humid']:.1f}%
💡 <b>Ánh sáng:</b> {data['light_lux']:.1f} Lux
☁️ <b>Khí gas:</b> {data['gas_ppm']:.1f} PPM

🔥 <b>Heat Index:</b> {data['heat_index']:.1f}°C
{comfort_emoji} <b>Comfort:</b> {data['comfort']}/100

{fan_emoji} <b>Quạt:</b> {'BẬT' if data['fan'] else 'TẮT'}
{alert_emoji} <b>Trạng thái:</b> {'CẢNH BÁO!' if data['alert'] else 'Bình thường'}

⏰ {data['timestamp']}
            """
            
            for user_id in list(auto_data_users):
                try:
                    bot.send_message(user_id, data_text, parse_mode='HTML')
                    print(f"✓ Auto-sent to {user_id}")
                except Exception as e:
                    print(f"✗ Error sending to {user_id}: {e}")
                    if "bot was blocked" in str(e).lower():
                        auto_data_users.discard(user_id)
                        
        except Exception as e:
            print(f"✗ Auto-send error: {e}")

# ===== KIỂM TRA CẢNH BÁO =====
def check_alerts(data):
    global alert_sent
    alerts = []
    
    if data['temp'] > 35:
        if not alert_sent.get('temp_high'):
            alerts.append(f"🔥 CẢNH BÁO: Nhiệt độ quá cao ({data['temp']:.1f}°C)")
            alert_sent['temp_high'] = True
    else:
        alert_sent['temp_high'] = False
        
    if data['temp'] < 15:
        if not alert_sent.get('temp_low'):
            alerts.append(f"❄️ CẢNH BÁO: Nhiệt độ quá thấp ({data['temp']:.1f}°C)")
            alert_sent['temp_low'] = True
    else:
        alert_sent['temp_low'] = False
    
    if data['humid'] > 80:
        if not alert_sent.get('humid_high'):
            alerts.append(f"💧 CẢNH BÁO: Độ ẩm quá cao ({data['humid']:.1f}%)")
            alert_sent['humid_high'] = True
    else:
        alert_sent['humid_high'] = False
    
    if data['gas_ppm'] > 300:
        if not alert_sent.get('gas'):
            alerts.append(f"☠️ NGUY HIỂM: Phát hiện khí gas ({data['gas_ppm']:.1f} PPM)")
            alert_sent['gas'] = True
    else:
        alert_sent['gas'] = False
    
    # Thông báo quạt tự động
    if data['fan']:
        if not alert_sent.get('fan_on'):
            alerts.append(f"🌀 Quạt tự động BẬT (nhiệt độ: {data['temp']:.1f}°C)")
            alert_sent['fan_on'] = True
    else:
        if alert_sent.get('fan_on'):
            alerts.append(f"🌀 Quạt tự động TẮT (nhiệt độ: {data['temp']:.1f}°C)")
            alert_sent['fan_on'] = False
    
    # Gửi thông báo
    if alerts:
        for user_id in subscribed_users:
            try:
                for alert in alerts:
                    bot.send_message(user_id, alert)
            except Exception as e:
                print(f"✗ Error sending alert to {user_id}: {e}")

# ===== TELEGRAM COMMANDS =====
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('📊 Dữ liệu')
    btn2 = types.KeyboardButton('🔔 Cảnh báo')
    btn3 = types.KeyboardButton('📈 Thống kê')
    btn4 = types.KeyboardButton('⏰ Auto')
    markup.add(btn1, btn2, btn3, btn4)
    
    welcome_text = """
🌡️ <b>Chào mừng đến với IoT Monitor V5.1!</b>

Hệ thống giám sát môi trường thông minh.

<b>Lệnh có sẵn:</b>
/start - Bắt đầu
/data - Xem dữ liệu hiện tại
/subscribe - Đăng ký cảnh báo
/unsubscribe - Hủy cảnh báo
/auto_on - Bật gửi dữ liệu tự động (5 phút)
/auto_off - Tắt gửi tự động
/stats - Xem thống kê chi tiết
/help - Hướng dẫn

Hoặc dùng nút bên dưới! 👇
    """
    
    bot.send_message(message.chat.id, welcome_text, parse_mode='HTML', reply_markup=markup)

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
<b>📖 HƯỚNG DẪN SỬ DỤNG</b>

<b>1. Xem dữ liệu:</b>
   /data - Dữ liệu cảm biến realtime

<b>2. Cảnh báo:</b>
   /subscribe - Nhận cảnh báo tự động
   /unsubscribe - Tắt cảnh báo

<b>3. Gửi tự động:</b>
   /auto_on - Nhận dữ liệu mỗi 5 phút
   /auto_off - Tắt gửi tự động

<b>4. Thống kê:</b>
   /stats - Xem chi tiết đầy đủ

<b>Ngưỡng cảnh báo:</b>
🌡️ Nhiệt độ: 15-35°C
💧 Độ ẩm: 30-80%
💡 Ánh sáng: >200 Lux
☠️ Khí gas: <300 PPM

<b>Quạt tự động:</b>
🌀 BẬT khi T ≥ 30°C
🌀 TẮT khi T ≤ 28°C
    """
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

@bot.message_handler(commands=['data'])
def send_data(message):
    data = latest_data
    
    # Emoji theo trạng thái
    temp_emoji = '🔥' if data['temp'] > 35 else '❄️' if data['temp'] < 15 else '🌡️'
    humid_emoji = '💧' if data['humid'] > 80 or data['humid'] < 30 else '💦'
    light_emoji = '💡' if data['light_lux'] < 200 else '☀️'
    gas_emoji = '☠️' if data['gas_ppm'] > 300 else '✅'
    comfort_emoji = '😊' if data['comfort'] >= 80 else '🙂' if data['comfort'] >= 60 else '😟'
    fan_emoji = '🌀' if data['fan'] else '❌'
    
    data_text = f"""
📊 <b>DỮ LIỆU CẢM BIẾN</b>

{temp_emoji} <b>Nhiệt độ:</b> {data['temp']:.1f}°C
{humid_emoji} <b>Độ ẩm:</b> {data['humid']:.1f}%
{light_emoji} <b>Ánh sáng:</b> {data['light_lux']:.1f} Lux
{gas_emoji} <b>Khí gas:</b> {data['gas_ppm']:.1f} PPM

🔥 <b>Heat Index:</b> {data['heat_index']:.1f}°C
{comfort_emoji} <b>Comfort:</b> {data['comfort']}/100

<b>━━━━━━━━━━━━━━━━━</b>

{fan_emoji} <b>Quạt:</b> {'🟢 BẬT' if data['fan'] else '🔴 TẮT'}
{'🚨' if data['alert'] else '✅'} <b>Trạng thái:</b> {'CẢNH BÁO!' if data['alert'] else 'Bình thường'}

⏰ <b>Cập nhật:</b> {data['timestamp']}
    """
    
    bot.send_message(message.chat.id, data_text, parse_mode='HTML')

@bot.message_handler(commands=['subscribe'])
def subscribe_alerts(message):
    user_id = message.chat.id
    subscribed_users.add(user_id)
    bot.send_message(user_id, "✅ Đã đăng ký nhận cảnh báo tự động!\n\n"
                              "Bạn sẽ nhận thông báo khi:\n"
                              "• Nhiệt độ vượt ngưỡng\n"
                              "• Độ ẩm bất thường\n"
                              "• Phát hiện khí gas\n"
                              "• Quạt tự động bật/tắt")

@bot.message_handler(commands=['unsubscribe'])
def unsubscribe_alerts(message):
    user_id = message.chat.id
    if user_id in subscribed_users:
        subscribed_users.remove(user_id)
    bot.send_message(user_id, "❌ Đã hủy đăng ký cảnh báo!")

@bot.message_handler(commands=['auto_on'])
def auto_on(message):
    user_id = message.chat.id
    auto_data_users.add(user_id)
    bot.send_message(user_id, f"⏰ Đã bật gửi dữ liệu tự động!\n\n"
                              f"Bạn sẽ nhận dữ liệu mỗi {AUTO_SEND_INTERVAL//60} phút.")

@bot.message_handler(commands=['auto_off'])
def auto_off(message):
    user_id = message.chat.id
    if user_id in auto_data_users:
        auto_data_users.remove(user_id)
    bot.send_message(user_id, "⏰ Đã tắt gửi dữ liệu tự động!")

@bot.message_handler(commands=['stats'])
def send_stats(message):
    data = latest_data
    
    # Đánh giá từng chỉ số
    temp_status = '⚠️ Quá cao' if data['temp'] > 35 else '⚠️ Quá thấp' if data['temp'] < 15 else '✅ Bình thường'
    humid_status = '⚠️ Quá ẩm' if data['humid'] > 80 else '⚠️ Quá khô' if data['humid'] < 30 else '✅ Bình thường'
    light_status = '⚠️ Tối' if data['light_lux'] < 200 else '✅ Đủ sáng'
    gas_status = '🚨 NGUY HIỂM!' if data['gas_ppm'] > 300 else '✅ An toàn'
    comfort_status = '🌟 Tuyệt vời' if data['comfort'] >= 80 else '👍 Tốt' if data['comfort'] >= 60 else '👎 Kém'
    
    stats_text = f"""
📈 <b>THỐNG KÊ CHI TIẾT</b>

<b>🌡️ Nhiệt độ:</b>
└ Hiện tại: {data['temp']:.1f}°C
└ Heat Index: {data['heat_index']:.1f}°C
└ Trạng thái: {temp_status}

<b>💧 Độ ẩm:</b>
└ Hiện tại: {data['humid']:.1f}%
└ Trạng thái: {humid_status}

<b>💡 Ánh sáng:</b>
└ Hiện tại: {data['light_lux']:.1f} Lux
└ Trạng thái: {light_status}

<b>☁️ Khí gas:</b>
└ Hiện tại: {data['gas_ppm']:.1f} PPM
└ Trạng thái: {gas_status}

<b>😊 Chỉ số thoải mái:</b>
└ {data['comfort']}/100
└ Đánh giá: {comfort_status}

<b>🌀 Quạt:</b>
└ Trạng thái: {'BẬT' if data['fan'] else 'TẮT'}
└ Chế độ: TỰ ĐỘNG
└ BẬT khi T ≥ 30°C
└ TẮT khi T ≤ 28°C

⏰ Cập nhật lúc: {data['timestamp']}
    """
    
    bot.send_message(message.chat.id, stats_text, parse_mode='HTML')

# ===== MESSAGE HANDLERS =====
@bot.message_handler(func=lambda message: message.text == '📊 Dữ liệu')
def handle_data_button(message):
    send_data(message)

@bot.message_handler(func=lambda message: message.text == '🔔 Cảnh báo')
def handle_alert_button(message):
    user_id = message.chat.id
    if user_id in subscribed_users:
        bot.send_message(user_id, "✅ Bạn đã đăng ký cảnh báo.\n\n"
                                 "Gửi /unsubscribe để hủy.")
    else:
        bot.send_message(user_id, "❌ Bạn chưa đăng ký cảnh báo.\n\n"
                                 "Gửi /subscribe để đăng ký.")

@bot.message_handler(func=lambda message: message.text == '📈 Thống kê')
def handle_stats_button(message):
    send_stats(message)

@bot.message_handler(func=lambda message: message.text == '⏰ Auto')
def handle_auto_button(message):
    user_id = message.chat.id
    if user_id in auto_data_users:
        bot.send_message(user_id, f"⏰ Gửi tự động đang BẬT (mỗi {AUTO_SEND_INTERVAL//60} phút)\n\n"
                                 "Gửi /auto_off để tắt.")
    else:
        bot.send_message(user_id, "⏰ Gửi tự động đang TẮT.\n\n"
                                 "Gửi /auto_on để bật.")

# ===== MAIN =====
if __name__ == '__main__':
    print("\n" + "="*50)
    print("  🤖 IoT Monitor V5.1 - Telegram Bot")
    print("="*50)
    print(f"  MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"  Auto-send interval: {AUTO_SEND_INTERVAL}s")
    print("="*50 + "\n")
    
    # Chạy MQTT trong thread riêng
    mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
    mqtt_thread.start()
    
    # Chạy auto-send trong thread riêng
    auto_thread = threading.Thread(target=auto_send_data, daemon=True)
    auto_thread.start()
    
    # Chạy bot
    print("✓ Bot is running! Press Ctrl+C to stop.\n")
    bot.polling(none_stop=True)