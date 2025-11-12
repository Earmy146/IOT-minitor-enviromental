import telebot
from telebot import types
import paho.mqtt.client as mqtt
import json
import threading
import time
from datetime import datetime
from gemini_config import analyze_environment, get_short_summary, format_for_telegram, ANALYSIS_INTERVAL

# ===== CẤU HÌNH =====
TELEGRAM_TOKEN = "8494895987:AAHC0g2pnAHnjx-vw9JY1aqNhkT5J2qI1FA"
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_TOPIC_DATA = "iot/env/data"
MQTT_TOPIC_STATUS = "iot/env/status"

# Thời gian gửi dữ liệu tự động (giây)
AUTO_SEND_INTERVAL = 30  # 30 giây

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

latest_analysis = None  # Lưu phân tích mới nhất từ Gemini

# Danh sách users
subscribed_users = set()
auto_data_users = set()
ai_analysis_users = set()  # Users nhận phân tích AI
alert_sent = {}

# Cấu hình thời gian phân tích AI cho từng user
user_ai_intervals = {}  # {user_id: interval_in_seconds}

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
            check_alerts(data)
        elif msg.topic == MQTT_TOPIC_STATUS:
            status = msg.payload.decode()
            print(f"📢 Trang thai: {status}")
    except Exception as e:
        print(f"✗ Loi: {e}")

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def start_mqtt():
    """MQTT với auto-reconnect"""
    while True:
        try:
            print("🔌 Dang ket noi MQTT...")
            mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            mqtt_client.loop_forever()
        except Exception as e:
            print(f"✗ Loi MQTT: {e}")
            print("🔄 Thu ket noi lai MQTT sau 10 giay...")
            time.sleep(10)

# ===== PHÂN TÍCH AI TỰ ĐỘNG =====
def auto_ai_analysis():
    """Gửi phân tích AI định kỳ cho users đã đăng ký"""
    print(f"✓ Da bat phan tich AI tu dong")
    
    last_analysis_time = {}  # Theo dõi thời gian phân tích cuối cho mỗi user
    
    while True:
        try:
            time.sleep(10)  # Kiểm tra mỗi 10 giây
            
            current_time = time.time()
            
            for user_id in list(ai_analysis_users):
                # Lấy interval của user (mặc định 30 phút)
                interval = user_ai_intervals.get(user_id, ANALYSIS_INTERVAL)
                
                # Kiểm tra đã đến lúc phân tích chưa
                last_time = last_analysis_time.get(user_id, 0)
                if current_time - last_time >= interval:
                    try:
                        print(f"🤖 Dang phan tich AI cho user {user_id}...")
                        
                        # Phân tích bằng Gemini
                        result = analyze_environment(latest_data)
                        
                        if result['success']:
                            global latest_analysis
                            latest_analysis = result
                            
                            # Format message đẹp cho Telegram
                            message = format_for_telegram(result)
                            
                            bot.send_message(user_id, message, parse_mode='HTML')
                            print(f"✓ Da gui phan tich AI den {user_id}")
                            
                            # Cập nhật thời gian
                            last_analysis_time[user_id] = current_time
                            
                        else:
                            error_msg = f"❌ Lỗi phân tích AI: {result['error']}"
                            bot.send_message(user_id, error_msg)
                            
                    except Exception as e:
                        print(f"✗ Loi gui AI den {user_id}: {e}")
                        if "bot was blocked" in str(e).lower():
                            ai_analysis_users.discard(user_id)
                            if user_id in user_ai_intervals:
                                del user_ai_intervals[user_id]
                                
        except Exception as e:
            print(f"✗ Loi phan tich AI tu dong: {e}")

# ===== GỬI DỮ LIỆU TỰ ĐỘNG =====
def auto_send_data():
    print(f"✓ Da bat gui tu dong (khoang: {AUTO_SEND_INTERVAL}s)")
    
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

🔥 <b>Chỉ số nhiệt:</b> {data['heat_index']:.1f}°C
{comfort_emoji} <b>Thoải mái:</b> {data['comfort']}/100

{fan_emoji} <b>Quạt:</b> {'BẬT' if data['fan'] else 'TẮT'}
{alert_emoji} <b>Trạng thái:</b> {'CẢNH BÁO!' if data['alert'] else 'Bình thường'}

⏰ {data['timestamp']}
            """
            
            for user_id in list(auto_data_users):
                try:
                    bot.send_message(user_id, data_text, parse_mode='HTML')
                    print(f"✓ Da gui tu dong den {user_id}")
                except Exception as e:
                    print(f"✗ Loi gui den {user_id}: {e}")
                    if "bot was blocked" in str(e).lower():
                        auto_data_users.discard(user_id)
                        
        except Exception as e:
            print(f"✗ Loi gui tu dong: {e}")

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
                print(f"✗ Loi gui canh bao den {user_id}: {e}")

# ===== TELEGRAM COMMANDS =====
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('📊 Dữ liệu')
    btn2 = types.KeyboardButton('🔔 Cảnh báo')
    btn3 = types.KeyboardButton('📈 Thống kê')
    btn4 = types.KeyboardButton('⏰ Tự động')
    btn5 = types.KeyboardButton('🤖 AI')
    btn6 = types.KeyboardButton('⚙️ Cài đặt AI')
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    
    welcome_text = """
🌡️ <b>Chào mừng đến với Hệ Thống Giám Sát IoT V5.1 + AI!</b>

Hệ thống giám sát môi trường thông minh với phân tích AI.

<b>Lệnh có sẵn:</b>
/start - Bắt đầu
/data - Xem dữ liệu hiện tại
/subscribe - Đăng ký cảnh báo
/unsubscribe - Hủy cảnh báo
/auto_on - Bật gửi dữ liệu tự động
/auto_off - Tắt gửi tự động
/stats - Xem thống kê chi tiết

<b>🤖 Lệnh AI mới:</b>
/ai_now - Phân tích AI ngay lập tức
/ai_on - Bật phân tích AI định kỳ
/ai_off - Tắt phân tích AI
/ai_interval - Đặt chu kỳ phân tích (phút)

/help - Hướng dẫn

Hoặc dùng nút bên dưới! 👇
    """
    
    bot.send_message(message.chat.id, welcome_text, parse_mode='HTML', reply_markup=markup)

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
<b>📖 HƯỚNG DẪN SỬ DỤNG</b>

<b>1. Xem dữ liệu:</b>
   /data - Dữ liệu cảm biến thời gian thực

<b>2. Cảnh báo:</b>
   /subscribe - Nhận cảnh báo tự động
   /unsubscribe - Tắt cảnh báo

<b>3. Gửi tự động:</b>
   /auto_on - Nhận dữ liệu mỗi 30 giây
   /auto_off - Tắt gửi tự động

<b>4. Thống kê:</b>
   /stats - Xem chi tiết đầy đủ

<b>🤖 5. Phân tích AI (MỚI):</b>
   /ai_now - Phân tích ngay lập tức
   /ai_on - Bật phân tích định kỳ (mặc định 30 phút)
   /ai_off - Tắt phân tích định kỳ
   /ai_interval - Đặt chu kỳ (10-120 phút)

<b>Ngưỡng cảnh báo:</b>
🌡️ Nhiệt độ: 15-35°C
💧 Độ ẩm: 30-80%
💡 Ánh sáng: >200 Lux
☠️ Khí gas: <300 PPM

<b>Quạt tự động:</b>
🌀 BẬT khi nhiệt độ ≥ 30°C
🌀 TẮT khi nhiệt độ ≤ 28°C
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

🔥 <b>Chỉ số nhiệt:</b> {data['heat_index']:.1f}°C
{comfort_emoji} <b>Thoải mái:</b> {data['comfort']}/100

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
                              f"Bạn sẽ nhận dữ liệu mỗi {AUTO_SEND_INTERVAL} giây.")

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
└ Chỉ số nhiệt: {data['heat_index']:.1f}°C
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
└ BẬT khi nhiệt độ ≥ 30°C
└ TẮT khi nhiệt độ ≤ 28°C

⏰ Cập nhật lúc: {data['timestamp']}
    """
    
    bot.send_message(message.chat.id, stats_text, parse_mode='HTML')

# ===== LỆNH AI MỚI =====
@bot.message_handler(commands=['ai_now'])
def ai_analyze_now(message):
    """Phân tích AI ngay lập tức"""
    user_id = message.chat.id
    
    # Gửi thông báo đang xử lý
    processing_msg = bot.send_message(user_id, "🤖 Đang phân tích bằng AI...\n⏳ Vui lòng đợi 5-10 giây")
    
    try:
        result = analyze_environment(latest_data)
        
        # Xóa thông báo đang xử lý
        bot.delete_message(user_id, processing_msg.message_id)
        
        if result['success']:
            global latest_analysis
            latest_analysis = result
            
            # Format đẹp cho Telegram
            response = format_for_telegram(result)
            
            bot.send_message(user_id, response, parse_mode='HTML')
        else:
            bot.send_message(user_id, f"❌ <b>Lỗi phân tích AI:</b>\n{result['error']}", parse_mode='HTML')
            
    except Exception as e:
        bot.delete_message(user_id, processing_msg.message_id)
        bot.send_message(user_id, f"❌ <b>Lỗi:</b> {str(e)}", parse_mode='HTML')

@bot.message_handler(commands=['ai_on'])
def ai_on(message):
    """Bật phân tích AI định kỳ"""
    user_id = message.chat.id
    ai_analysis_users.add(user_id)
    
    # Lấy interval hiện tại hoặc dùng mặc định
    interval = user_ai_intervals.get(user_id, ANALYSIS_INTERVAL)
    interval_minutes = interval // 60
    
    bot.send_message(user_id, 
        f"🤖 Đã bật phân tích AI định kỳ!\n\n"
        f"⏰ Chu kỳ hiện tại: {interval_minutes} phút\n"
        f"📊 Bạn sẽ nhận phân tích AI tự động\n\n"
        f"Dùng /ai_interval để thay đổi chu kỳ (10-120 phút)")

@bot.message_handler(commands=['ai_off'])
def ai_off(message):
    """Tắt phân tích AI định kỳ"""
    user_id = message.chat.id
    if user_id in ai_analysis_users:
        ai_analysis_users.remove(user_id)
    bot.send_message(user_id, "🤖 Đã tắt phân tích AI định kỳ!")

@bot.message_handler(commands=['ai_interval'])
def ai_set_interval(message):
    """Đặt chu kỳ phân tích AI"""
    user_id = message.chat.id
    
    msg = bot.send_message(user_id, 
        "⏰ Nhập chu kỳ phân tích AI (phút):\n\n"
        "• Tối thiểu: 10 phút\n"
        "• Tối đa: 120 phút\n"
        "• Mặc định: 30 phút\n\n"
        "Ví dụ: Nhập <code>15</code> cho 15 phút", 
        parse_mode='HTML')
    
    bot.register_next_step_handler(msg, process_ai_interval)

def process_ai_interval(message):
    """Xử lý chu kỳ AI từ user"""
    user_id = message.chat.id
    
    try:
        minutes = int(message.text)
        
        if minutes < 10 or minutes > 120:
            bot.send_message(user_id, 
                "❌ Chu kỳ không hợp lệ!\n"
                "Vui lòng nhập từ 10-120 phút.")
            return
        
        # Lưu interval (chuyển sang giây)
        user_ai_intervals[user_id] = minutes * 60
        
        bot.send_message(user_id, 
            f"✅ Đã đặt chu kỳ phân tích AI: {minutes} phút\n\n"
            f"Dùng /ai_on để bật phân tích tự động.")
            
    except ValueError:
        bot.send_message(user_id, 
            "❌ Vui lòng nhập số nguyên!\n"
            "Ví dụ: 30")

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

@bot.message_handler(func=lambda message: message.text == '⏰ Tự động')
def handle_auto_button(message):
    user_id = message.chat.id
    if user_id in auto_data_users:
        bot.send_message(user_id, f"⏰ Gửi tự động đang BẬT (mỗi {AUTO_SEND_INTERVAL} giây)\n\n"
                                 "Gửi /auto_off để tắt.")
    else:
        bot.send_message(user_id, "⏰ Gửi tự động đang TẮT.\n\n"
                                 "Gửi /auto_on để bật.")

@bot.message_handler(func=lambda message: message.text == '🤖 AI')
def handle_ai_button(message):
    ai_analyze_now(message)

@bot.message_handler(func=lambda message: message.text == '⚙️ Cài đặt AI')
def handle_ai_settings_button(message):
    user_id = message.chat.id
    interval = user_ai_intervals.get(user_id, ANALYSIS_INTERVAL)
    interval_minutes = interval // 60
    status = "BẬT" if user_id in ai_analysis_users else "TẮT"
    
    settings_text = f"""
⚙️ <b>CÀI ĐẶT AI</b>

🤖 Trạng thái: {status}
⏰ Chu kỳ: {interval_minutes} phút

<b>Lệnh:</b>
/ai_on - Bật phân tích định kỳ
/ai_off - Tắt phân tích
/ai_interval - Đặt chu kỳ (10-120 phút)
/ai_now - Phân tích ngay
    """
    
    bot.send_message(user_id, settings_text, parse_mode='HTML')

# ===== MAIN =====
if __name__ == '__main__':
    print("\n" + "="*50)
    print("  🤖 Hệ Thống Giám Sát IoT V5.1 + AI - Bot Telegram")
    print("="*50)
    print(f"  MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"  Khoang gui tu dong: {AUTO_SEND_INTERVAL}s")
    print(f"  Chu ky AI mac dinh: {ANALYSIS_INTERVAL // 60} phut")
    print("="*50 + "\n")
    
    # Chạy MQTT trong thread riêng
    mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
    mqtt_thread.start()
    
    # Chạy auto-send trong thread riêng
    auto_thread = threading.Thread(target=auto_send_data, daemon=True)
    auto_thread.start()
    
    # Chạy AI analysis trong thread riêng
    ai_thread = threading.Thread(target=auto_ai_analysis, daemon=True)
    ai_thread.start()
    
    # Chạy bot với error handling và auto-reconnect
    print("✓ Bot dang chay! Nhan Ctrl+C de dung.\n")
    
    while True:
        try:
            # Polling với timeout ngắn hơn để tránh timeout lâu
            bot.polling(none_stop=True, interval=0, timeout=20)
            
        except KeyboardInterrupt:
            print("\n\n🛑 Dang dung bot...")
            print("👋 Tam biet!")
            break
            
        except Exception as e:
            error_message = str(e)
            
            # Kiểm tra loại lỗi
            if "timeout" in error_message.lower():
                print(f"\n⚠️ Loi timeout: Ket noi Telegram bi gian doan")
            elif "connection" in error_message.lower():
                print(f"\n⚠️ Loi ket noi: Khong the ket noi den Telegram")
            else:
                print(f"\n⚠️ Loi: {error_message}")
            
            print("🔄 Thu ket noi lai sau 5 giay...")
            time.sleep(5)
            print("🔌 Dang ket noi lai...")