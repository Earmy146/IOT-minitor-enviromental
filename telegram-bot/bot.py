import telebot
from telebot import types
import paho.mqtt.client as mqtt
import json
import threading
import time
from datetime import datetime

# ===== CẤU HÌNH =====
MA_TELEGRAM = "8494895987:AAHC0g2pnAHnjx-vw9JY1aqNhkT5J2qI1FA"
MAY_CHU_MQTT = "test.mosquitto.org"
CONG_MQTT = 1883
CHU_DE_DU_LIEU = "iot/moitruong/dulieu"
CHU_DE_TRANG_THAI = "iot/moitruong/trangthai"

# Thời gian gửi dữ liệu tự động (giây)
KHOANG_TU_DONG = 30  # 30 giây

bot = telebot.TeleBot(MA_TELEGRAM)

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

# Danh sách người dùng
nguoi_dung_dang_ky = set()
nguoi_dung_tu_dong = set()
canh_bao_da_gui = {}

# ===== MQTT CALLBACKS =====
def khi_ket_noi(khach, du_lieu_nguoi_dung, co, ma_ket_qua):
    print(f"✓ Da ket noi MQTT! (Ma: {ma_ket_qua})")
    khach.subscribe(CHU_DE_DU_LIEU)
    khach.subscribe(CHU_DE_TRANG_THAI)

def khi_nhan_tin(khach, du_lieu_nguoi_dung, tin):
    global du_lieu_moi_nhat
    
    try:
        if tin.topic == CHU_DE_DU_LIEU:
            du_lieu = json.loads(tin.payload.decode())
            du_lieu['thoi_gian'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            du_lieu_moi_nhat = du_lieu
            kiem_tra_canh_bao(du_lieu)
        elif tin.topic == CHU_DE_TRANG_THAI:
            trang_thai = tin.payload.decode()
            print(f"📢 Trang thai: {trang_thai}")
    except Exception as loi:
        print(f"✗ Loi: {loi}")

khach_mqtt = mqtt.Client()
khach_mqtt.on_connect = khi_ket_noi
khach_mqtt.on_message = khi_nhan_tin

def khoi_dong_mqtt():
    try:
        khach_mqtt.connect(MAY_CHU_MQTT, CONG_MQTT, 60)
        khach_mqtt.loop_forever()
    except Exception as loi:
        print(f"✗ Loi MQTT: {loi}")

# ===== GỬI DỮ LIỆU TỰ ĐỘNG =====
def gui_du_lieu_tu_dong():
    print(f"✓ Da bat gui tu dong (khoang: {KHOANG_TU_DONG}s)")
    
    while True:
        try:
            time.sleep(KHOANG_TU_DONG)
            
            if not nguoi_dung_tu_dong:
                continue
            
            dl = du_lieu_moi_nhat
            bieu_tuong_canh_bao = '🚨' if dl['canh_bao'] else '✅'
            bieu_tuong_quat = '🌀' if dl['quat'] else '❌'
            bieu_tuong_thoai_mai = '😊' if dl['thoai_mai'] >= 80 else '🙂' if dl['thoai_mai'] >= 60 else '😟'
            
            van_ban_du_lieu = f"""
📊 <b>CẬP NHẬT TỰ ĐỘNG</b>

🌡️ <b>Nhiệt độ:</b> {dl['nhiet_do']:.1f}°C
💧 <b>Độ ẩm:</b> {dl['do_am']:.1f}%
💡 <b>Ánh sáng:</b> {dl['anh_sang_lux']:.1f} Lux
☁️ <b>Khí gas:</b> {dl['khi_ppm']:.1f} PPM

🔥 <b>Chỉ số nhiệt:</b> {dl['chi_so_nhiet']:.1f}°C
{bieu_tuong_thoai_mai} <b>Thoải mái:</b> {dl['thoai_mai']}/100

{bieu_tuong_quat} <b>Quạt:</b> {'BẬT' if dl['quat'] else 'TẮT'}
{bieu_tuong_canh_bao} <b>Trạng thái:</b> {'CẢNH BÁO!' if dl['canh_bao'] else 'Bình thường'}

⏰ {dl['thoi_gian']}
            """
            
            for ma_nguoi_dung in list(nguoi_dung_tu_dong):
                try:
                    bot.send_message(ma_nguoi_dung, van_ban_du_lieu, parse_mode='HTML')
                    print(f"✓ Da gui tu dong den {ma_nguoi_dung}")
                except Exception as loi:
                    print(f"✗ Loi gui den {ma_nguoi_dung}: {loi}")
                    if "bot was blocked" in str(loi).lower():
                        nguoi_dung_tu_dong.discard(ma_nguoi_dung)
                        
        except Exception as loi:
            print(f"✗ Loi gui tu dong: {loi}")

# ===== KIỂM TRA CẢNH BÁO =====
def kiem_tra_canh_bao(du_lieu):
    global canh_bao_da_gui
    cac_canh_bao = []
    
    if du_lieu['nhiet_do'] > 35:
        if not canh_bao_da_gui.get('nhiet_cao'):
            cac_canh_bao.append(f"🔥 CẢNH BÁO: Nhiệt độ quá cao ({du_lieu['nhiet_do']:.1f}°C)")
            canh_bao_da_gui['nhiet_cao'] = True
    else:
        canh_bao_da_gui['nhiet_cao'] = False
        
    if du_lieu['nhiet_do'] < 15:
        if not canh_bao_da_gui.get('nhiet_thap'):
            cac_canh_bao.append(f"❄️ CẢNH BÁO: Nhiệt độ quá thấp ({du_lieu['nhiet_do']:.1f}°C)")
            canh_bao_da_gui['nhiet_thap'] = True
    else:
        canh_bao_da_gui['nhiet_thap'] = False
    
    if du_lieu['do_am'] > 80:
        if not canh_bao_da_gui.get('am_cao'):
            cac_canh_bao.append(f"💧 CẢNH BÁO: Độ ẩm quá cao ({du_lieu['do_am']:.1f}%)")
            canh_bao_da_gui['am_cao'] = True
    else:
        canh_bao_da_gui['am_cao'] = False
    
    if du_lieu['khi_ppm'] > 300:
        if not canh_bao_da_gui.get('khi'):
            cac_canh_bao.append(f"☠️ NGUY HIỂM: Phát hiện khí gas ({du_lieu['khi_ppm']:.1f} PPM)")
            canh_bao_da_gui['khi'] = True
    else:
        canh_bao_da_gui['khi'] = False
    
    # Thông báo quạt tự động
    if du_lieu['quat']:
        if not canh_bao_da_gui.get('quat_bat'):
            cac_canh_bao.append(f"🌀 Quạt tự động BẬT (nhiệt độ: {du_lieu['nhiet_do']:.1f}°C)")
            canh_bao_da_gui['quat_bat'] = True
    else:
        if canh_bao_da_gui.get('quat_bat'):
            cac_canh_bao.append(f"🌀 Quạt tự động TẮT (nhiệt độ: {du_lieu['nhiet_do']:.1f}°C)")
            canh_bao_da_gui['quat_bat'] = False
    
    # Gửi thông báo
    if cac_canh_bao:
        for ma_nguoi_dung in nguoi_dung_dang_ky:
            try:
                for canh_bao in cac_canh_bao:
                    bot.send_message(ma_nguoi_dung, canh_bao)
            except Exception as loi:
                print(f"✗ Loi gui canh bao den {ma_nguoi_dung}: {loi}")

# ===== LỆNH TELEGRAM =====
@bot.message_handler(commands=['start', 'batdau'])
def gui_chao_mung(tin_nhan):
    ban_phim = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    nut1 = types.KeyboardButton('📊 Dữ liệu')
    nut2 = types.KeyboardButton('🔔 Cảnh báo')
    nut3 = types.KeyboardButton('📈 Thống kê')
    nut4 = types.KeyboardButton('⏰ Tự động')
    ban_phim.add(nut1, nut2, nut3, nut4)
    
    van_ban_chao = """
🌡️ <b>Chào mừng đến với Hệ Thống Giám Sát V5.1!</b>

Hệ thống giám sát môi trường thông minh.

<b>Lệnh có sẵn:</b>
/batdau - Bắt đầu
/dulieu - Xem dữ liệu hiện tại
/dangky - Đăng ký cảnh báo
/huydangky - Hủy cảnh báo
/battudong - Bật gửi dữ liệu tự động (30 giây)
/tattudong - Tắt gửi tự động
/thongke - Xem thống kê chi tiết
/huongdan - Hướng dẫn

Hoặc dùng nút bên dưới! 👇
    """
    
    bot.send_message(tin_nhan.chat.id, van_ban_chao, parse_mode='HTML', reply_markup=ban_phim)

@bot.message_handler(commands=['help', 'huongdan'])
def gui_huong_dan(tin_nhan):
    van_ban_huong_dan = """
<b>📖 HƯỚNG DẪN SỬ DỤNG</b>

<b>1. Xem dữ liệu:</b>
   /dulieu - Dữ liệu cảm biến thời gian thực

<b>2. Cảnh báo:</b>
   /dangky - Nhận cảnh báo tự động
   /huydangky - Tắt cảnh báo

<b>3. Gửi tự động:</b>
   /battudong - Nhận dữ liệu mỗi 30 giây
   /tattuong - Tắt gửi tự động

<b>4. Thống kê:</b>
   /thongke - Xem chi tiết đầy đủ

<b>Ngưỡng cảnh báo:</b>
🌡️ Nhiệt độ: 15-35°C
💧 Độ ẩm: 30-80%
💡 Ánh sáng: >200 Lux
☠️ Khí gas: <300 PPM

<b>Quạt tự động:</b>
🌀 BẬT khi nhiệt độ ≥ 30°C
🌀 TẮT khi nhiệt độ ≤ 28°C
    """
    bot.send_message(tin_nhan.chat.id, van_ban_huong_dan, parse_mode='HTML')

@bot.message_handler(commands=['data', 'dulieu'])
def gui_du_lieu(tin_nhan):
    dl = du_lieu_moi_nhat
    
    # Biểu tượng theo trạng thái
    bt_nhiet = '🔥' if dl['nhiet_do'] > 35 else '❄️' if dl['nhiet_do'] < 15 else '🌡️'
    bt_am = '💧' if dl['do_am'] > 80 or dl['do_am'] < 30 else '💦'
    bt_sang = '💡' if dl['anh_sang_lux'] < 200 else '☀️'
    bt_khi = '☠️' if dl['khi_ppm'] > 300 else '✅'
    bt_thoai_mai = '😊' if dl['thoai_mai'] >= 80 else '🙂' if dl['thoai_mai'] >= 60 else '😟'
    bt_quat = '🌀' if dl['quat'] else '❌'
    
    van_ban_du_lieu = f"""
📊 <b>DỮ LIỆU CẢM BIẾN</b>

{bt_nhiet} <b>Nhiệt độ:</b> {dl['nhiet_do']:.1f}°C
{bt_am} <b>Độ ẩm:</b> {dl['do_am']:.1f}%
{bt_sang} <b>Ánh sáng:</b> {dl['anh_sang_lux']:.1f} Lux
{bt_khi} <b>Khí gas:</b> {dl['khi_ppm']:.1f} PPM

🔥 <b>Chỉ số nhiệt:</b> {dl['chi_so_nhiet']:.1f}°C
{bt_thoai_mai} <b>Thoải mái:</b> {dl['thoai_mai']}/100

<b>━━━━━━━━━━━━━━━━━</b>

{bt_quat} <b>Quạt:</b> {'🟢 BẬT' if dl['quat'] else '🔴 TẮT'}
{'🚨' if dl['canh_bao'] else '✅'} <b>Trạng thái:</b> {'CẢNH BÁO!' if dl['canh_bao'] else 'Bình thường'}

⏰ <b>Cập nhật:</b> {dl['thoi_gian']}
    """
    
    bot.send_message(tin_nhan.chat.id, van_ban_du_lieu, parse_mode='HTML')

@bot.message_handler(commands=['subscribe', 'dangky'])
def dang_ky_canh_bao(tin_nhan):
    ma_nguoi_dung = tin_nhan.chat.id
    nguoi_dung_dang_ky.add(ma_nguoi_dung)
    bot.send_message(ma_nguoi_dung, "✅ Đã đăng ký nhận cảnh báo tự động!\n\n"
                              "Bạn sẽ nhận thông báo khi:\n"
                              "• Nhiệt độ vượt ngưỡng\n"
                              "• Độ ẩm bất thường\n"
                              "• Phát hiện khí gas\n"
                              "• Quạt tự động bật/tắt")

@bot.message_handler(commands=['unsubscribe', 'huydangky'])
def huy_dang_ky_canh_bao(tin_nhan):
    ma_nguoi_dung = tin_nhan.chat.id
    if ma_nguoi_dung in nguoi_dung_dang_ky:
        nguoi_dung_dang_ky.remove(ma_nguoi_dung)
    bot.send_message(ma_nguoi_dung, "❌ Đã hủy đăng ký cảnh báo!")

@bot.message_handler(commands=['auto_on', 'battudong'])
def bat_tu_dong(tin_nhan):
    ma_nguoi_dung = tin_nhan.chat.id
    nguoi_dung_tu_dong.add(ma_nguoi_dung)
    bot.send_message(ma_nguoi_dung, f"⏰ Đã bật gửi dữ liệu tự động!\n\n"
                              f"Bạn sẽ nhận dữ liệu mỗi {KHOANG_TU_DONG} giây.")

@bot.message_handler(commands=['auto_off', 'tattuong'])
def tat_tu_dong(tin_nhan):
    ma_nguoi_dung = tin_nhan.chat.id
    if ma_nguoi_dung in nguoi_dung_tu_dong:
        nguoi_dung_tu_dong.remove(ma_nguoi_dung)
    bot.send_message(ma_nguoi_dung, "⏰ Đã tắt gửi dữ liệu tự động!")

@bot.message_handler(commands=['stats', 'thongke'])
def gui_thong_ke(tin_nhan):
    dl = du_lieu_moi_nhat
    
    # Đánh giá từng chỉ số
    trang_thai_nhiet = '⚠️ Quá cao' if dl['nhiet_do'] > 35 else '⚠️ Quá thấp' if dl['nhiet_do'] < 15 else '✅ Bình thường'
    trang_thai_am = '⚠️ Quá ẩm' if dl['do_am'] > 80 else '⚠️ Quá khô' if dl['do_am'] < 30 else '✅ Bình thường'
    trang_thai_sang = '⚠️ Tối' if dl['anh_sang_lux'] < 200 else '✅ Đủ sáng'
    trang_thai_khi = '🚨 NGUY HIỂM!' if dl['khi_ppm'] > 300 else '✅ An toàn'
    trang_thai_thoai_mai = '🌟 Tuyệt vời' if dl['thoai_mai'] >= 80 else '👍 Tốt' if dl['thoai_mai'] >= 60 else '👎 Kém'
    
    van_ban_thong_ke = f"""
📈 <b>THỐNG KÊ CHI TIẾT</b>

<b>🌡️ Nhiệt độ:</b>
└ Hiện tại: {dl['nhiet_do']:.1f}°C
└ Chỉ số nhiệt: {dl['chi_so_nhiet']:.1f}°C
└ Trạng thái: {trang_thai_nhiet}

<b>💧 Độ ẩm:</b>
└ Hiện tại: {dl['do_am']:.1f}%
└ Trạng thái: {trang_thai_am}

<b>💡 Ánh sáng:</b>
└ Hiện tại: {dl['anh_sang_lux']:.1f} Lux
└ Trạng thái: {trang_thai_sang}

<b>☁️ Khí gas:</b>
└ Hiện tại: {dl['khi_ppm']:.1f} PPM
└ Trạng thái: {trang_thai_khi}

<b>😊 Chỉ số thoải mái:</b>
└ {dl['thoai_mai']}/100
└ Đánh giá: {trang_thai_thoai_mai}

<b>🌀 Quạt:</b>
└ Trạng thái: {'BẬT' if dl['quat'] else 'TẮT'}
└ Chế độ: TỰ ĐỘNG
└ BẬT khi nhiệt độ ≥ 30°C
└ TẮT khi nhiệt độ ≤ 28°C

⏰ Cập nhật lúc: {dl['thoi_gian']}
    """
    
    bot.send_message(tin_nhan.chat.id, van_ban_thong_ke, parse_mode='HTML')

# ===== XỬ LÝ NÚT NHẤN =====
@bot.message_handler(func=lambda tin_nhan: tin_nhan.text == '📊 Dữ liệu')
def xu_ly_nut_du_lieu(tin_nhan):
    gui_du_lieu(tin_nhan)

@bot.message_handler(func=lambda tin_nhan: tin_nhan.text == '🔔 Cảnh báo')
def xu_ly_nut_canh_bao(tin_nhan):
    ma_nguoi_dung = tin_nhan.chat.id
    if ma_nguoi_dung in nguoi_dung_dang_ky:
        bot.send_message(ma_nguoi_dung, "✅ Bạn đã đăng ký cảnh báo.\n\n"
                                 "Gửi /huydangky để hủy.")
    else:
        bot.send_message(ma_nguoi_dung, "❌ Bạn chưa đăng ký cảnh báo.\n\n"
                                 "Gửi /dangky để đăng ký.")

@bot.message_handler(func=lambda tin_nhan: tin_nhan.text == '📈 Thống kê')
def xu_ly_nut_thong_ke(tin_nhan):
    gui_thong_ke(tin_nhan)

@bot.message_handler(func=lambda tin_nhan: tin_nhan.text == '⏰ Tự động')
def xu_ly_nut_tu_dong(tin_nhan):
    ma_nguoi_dung = tin_nhan.chat.id
    if ma_nguoi_dung in nguoi_dung_tu_dong:
        bot.send_message(ma_nguoi_dung, f"⏰ Gửi tự động đang BẬT (mỗi {KHOANG_TU_DONG} giây)\n\n"
                                 "Gửi /tattuong để tắt.")
    else:
        bot.send_message(ma_nguoi_dung, "⏰ Gửi tự động đang TẮT.\n\n"
                                 "Gửi /battuong để bật.")

# ===== CHƯƠNG TRÌNH CHÍNH =====
if __name__ == '__main__':
    print("\n" + "="*50)
    print("  🤖 Hệ Thống Giám Sát V5.1 - Bot Telegram")
    print("="*50)
    print(f"  Máy chủ MQTT: {MAY_CHU_MQTT}:{CONG_MQTT}")
    print(f"  Khoảng gửi tự động: {KHOANG_TU_DONG}s")
    print("="*50 + "\n")
    
    # Chạy MQTT trong luồng riêng
    luong_mqtt = threading.Thread(target=khoi_dong_mqtt, daemon=True)
    luong_mqtt.start()
    
    # Chạy gửi tự động trong luồng riêng
    luong_tu_dong = threading.Thread(target=gui_du_lieu_tu_dong, daemon=True)
    luong_tu_dong.start()
    
    # Chạy bot
    print("✓ Bot dang chay! Nhan Ctrl+C de dung.\n")
    bot.polling(none_stop=True)