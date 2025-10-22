# 🌡️ HỆ THỐNG GIÁM SÁT MÔI TRƯỜNG IOT V3.0

**Dự án IoT hoàn chỉnh với ESP32 + Web Dashboard + Telegram Bot**

![Version](https://img.shields.io/badge/version-3.0-blue)
![Platform](https://img.shields.io/badge/ESP32-Wokwi-orange)
![Python](https://img.shields.io/badge/Python-3.8+-green)

---

## 📁 CẤU TRÚC DỰ ÁN

```
iot-environmental-monitor-v3/
│
├── esp32/                          # ESP32 Code (Wokwi)
│   ├── src/main.cpp
│   ├── platformio.ini
│   ├── wokwi.toml
│   └── diagram.json
│
├── web-dashboard/                  # Web Dashboard
│   ├── app.py                      # Flask Server
│   ├── requirements.txt
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── style.css
│       └── app.js
│
├── telegram-bot/                   # Telegram Bot
│   ├── bot.py
│   └── requirements.txt
│
└── README.md
```

---

## 🚀 TÍNH NĂNG MỚI (V3.0)

### ✨ ESP32 (Wokwi)
- DHT22, LDR, MQ-2 sensors
- 2 Relay (Quạt, Đèn)
- Auto/Manual Mode
- ThingSpeak + MQTT
- LCD 3 trang

### ✨ Web Dashboard (MỚI!)
- Hiển thị real-time
- Biểu đồ 24h
- Thống kê
- Responsive design
- Auto refresh 10s

### ✨ Telegram Bot (MỚI!)
- Báo cáo tự động mỗi 15 phút
- Cảnh báo khẩn cấp
- Format đẹp với HTML
- Emoji trực quan

---

## ⚡ HƯỚNG DẪN CÀI ĐẶT

### PHẦN 1: ESP32 (Wokwi)

#### Bước 1: Cài VS Code + Extensions
- PlatformIO IDE
- Wokwi Simulator

#### Bước 2: Tạo ThingSpeak Channel
1. Vào https://thingspeak.com/ → Đăng ký
2. Tạo Channel với **8 Fields**:
   - Field 1: Temperature
   - Field 2: Humidity
   - Field 3: Light Level
   - Field 4: Gas Level
   - Field 5: Fan Status
   - Field 6: Light Status
   - Field 7: Heat Index
   - Field 8: Comfort Index

3. Lấy **Channel ID** và **Write API Key**

#### Bước 3: Cập nhật Code
Mở `esp32/src/main.cpp`, sửa dòng 13-14:
```cpp
unsigned long channelID = 3123035;  // ← Thay số của bạn
const char* writeAPIKey = "YOUR_KEY";  // ← Thay key của bạn
```

#### Bước 4: Build & Run
```bash
cd esp32
pio run
# Ctrl+Shift+P → Wokwi: Start Simulator
```

---

### PHẦN 2: Web Dashboard

#### Bước 1: Cài Python
```bash
# Kiểm tra Python đã cài chưa
python --version  # Cần Python 3.8+
```

#### Bước 2: Cài thư viện
```bash
cd web-dashboard
pip install -r requirements.txt
```

#### Bước 3: Cấu hình
Mở `app.py`, sửa dòng 7-8:
```python
CHANNEL_ID = "3123035"  # ← Channel ID của bạn
READ_API_KEY = "YOUR_READ_API_KEY"  # ← Read API Key (tùy chọn)
```

#### Bước 4: Chạy Server
```bash
python app.py
```

Mở browser: **http://localhost:5000**

---

### PHẦN 3: Telegram Bot

#### Bước 1: Tạo Bot
1. Mở Telegram → Chat với **@BotFather**
2. Gửi: `/newbot`
3. Đặt tên bot: `IoT Monitor Bot`
4. Đặt username: `your_iot_bot`
5. Nhận **Bot Token**: `123456:ABC-DEF...`

#### Bước 2: Lấy Chat ID

**Cách 1: Gửi tin cho bot**
```
1. Tìm bot vừa tạo trên Telegram
2. Nhấn START
3. Gửi tin nhắn bất kỳ
4. Vào: https://api.telegram.org/bot<BOT_TOKEN>/getUpdates
5. Tìm "chat":{"id":123456789}
```

**Cách 2: Dùng @userinfobot**
```
1. Chat với @userinfobot
2. Gửi tin nhắn
3. Bot trả về Chat ID của bạn
```

#### Bước 3: Cấu hình Bot
Mở `telegram-bot/bot.py`, sửa dòng 6-7:
```python
BOT_TOKEN = "123456:ABC-DEF..."  # ← Bot Token
CHAT_ID = "123456789"            # ← Chat ID của bạn
```

#### Bước 4: Cài thư viện
```bash
cd telegram-bot
pip install -r requirements.txt
```

#### Bước 5: Chạy Bot
```bash
python bot.py
```

Bot sẽ:
- Gửi test message
- Gửi báo cáo ngay lập tức
- Tự động gửi mỗi 15 phút

---

## 📊 DEMO

### 1. ESP32 trên Wokwi
```
LCD Page 1:
┌────────────────────┐
│ T:28.5C H:65%      │
│ L:750 G:250        │
│ HI:29.2 CI:85      │
│ STATUS: EXCELLENT  │
└────────────────────┘
```

### 2. Web Dashboard
```
http://localhost:5000

📊 Cards:
- Nhiệt độ: 28.5°C ✅ Tốt
- Độ ẩm: 65.3% ✅ Tốt
- Ánh sáng: 750 lux ✅ Vừa phải
- Khí gas: 250 ppm ✅ An toàn

📈 Biểu đồ:
- Nhiệt độ & Độ ẩm (24h)
- Ánh sáng & Khí gas (24h)

📊 Thống kê:
- TB Nhiệt độ: 28.3°C
- TB Độ ẩm: 64.8%
- Số lần đo: 4320
```

### 3. Telegram Bot
```
🌡️ BÁO CÁO MÔI TRƯỜNG
⏰ 22/10/2024 14:00:00

━━━━━━━━━━━━━━━━━━━━
📊 DỮ LIỆU CẢM BIẾN

🌡️ Nhiệt độ: 28.5°C
   Trạng thái: ✅ Tốt

💧 Độ ẩm: 65.3%
   Trạng thái: ✅ Tốt

💡 Ánh sáng: 750 lux
   Trạng thái: ✅ Vừa phải

✅ Khí gas: 250 ppm
   Trạng thái: ✅ An toàn

━━━━━━━━━━━━━━━━━━━━
📈 CHỈ SỐ TÍNH TOÁN

🔥 Heat Index: 29.2°C
😊 Comfort Index: 85/100
   🙂 Tốt

━━━━━━━━━━━━━━━━━━━━
🎛️ THIẾT BỊ

🌀 Quạt: BẬT ✅
💡 Đèn: TẮT ⭕
```

---

## 🔧 SO SÁNH CÁC PHIÊN BẢN

| Tính năng | V1.0 | V2.0 | V3.0 |
|-----------|------|------|------|
| Cảm biến | 2 | 3 | 3 |
| Relay | 0 | 2 | 2 |
| ThingSpeak | 3 fields | 8 fields | 8 fields |
| MQTT | ❌ | ✅ | ✅ |
| Web Dashboard | ❌ | ❌ | ✅ |
| Telegram Bot | ❌ | ❌ | ✅ |
| Auto Mode | ❌ | ✅ | ✅ |
| Biểu đồ | ❌ | ❌ | ✅ |
| Thống kê | ❌ | ✅ | ✅ |
| Cảnh báo tự động | ❌ | ❌ | ✅ |

---

## 🐛 KHẮC PHỤC LỖI

### ESP32 (Wokwi)

**Lỗi: firmware.bin not found**
```bash
cd esp32
pio run --target clean
pio run
```

**Lỗi: ThingSpeak 400**
- Check Channel ID và API Key
- Đảm bảo có đủ 8 Fields

---

### Web Dashboard

**Lỗi: ModuleNotFoundError**
```bash
pip install -r requirements.txt
```

**Lỗi: Port 5000 đang dùng**
```python
# Sửa trong app.py dòng cuối:
app.run(debug=True, host='0.0.0.0', port=5001)  # Đổi port
```

**Dashboard không cập nhật**
- Check ESP32 đang gửi data lên ThingSpeak
- Xem Console browser (F12) để debug
- Check Channel ID trong `app.py`

---

### Telegram Bot

**Lỗi: Unauthorized**
- Check Bot Token đúng chưa
- Bot Token format: `123456:ABC-DEF...`

**Lỗi: Chat not found**
- Chat ID phải là số (không có dấu ngoặc)
- Đảm bảo đã gửi tin cho bot trước
- Thử lại với @userinfobot

**Bot không gửi tin**
- Check kết nối Internet
- Thử test bằng browser:
  ```
  https://api.telegram.org/bot<TOKEN>/sendMessage?chat_id=<CHAT_ID>&text=test
  ```

---

## 📱 CÁCH SỬ DỤNG

### 1. Chạy toàn bộ hệ thống

```bash
# Terminal 1: ESP32 (Wokwi)
cd esp32
pio run
# Ctrl+Shift+P → Wokwi: Start

# Terminal 2: Web Dashboard
cd web-dashboard
python app.py

# Terminal 3: Telegram Bot
cd telegram-bot
python bot.py
```

### 2. Truy cập

- **Wokwi**: VS Code (mạch mô phỏng)
- **Web**: http://localhost:5000
- **Telegram**: Nhận tin tự động mỗi 15 phút

### 3. Tương tác

**ESP32:**
- Kéo cảm biến trên Wokwi
- Nhấn nút MODE → Chuyển Auto/Manual
- Xem Serial Monitor

**Web Dashboard:**
- Tự động refresh 10 giây
- Click biểu đồ để zoom
- Responsive trên mobile

**Telegram:**
- Nhận báo cáo tự động
- Cảnh báo khẩn cấp khi gas > 600 ppm
- Không cần thao tác gì

---

## 📈 LUỒNG DỮ LIỆU

```
┌─────────┐
│ ESP32   │ ─┐
│ (Wokwi) │  │
└─────────┘  │
             │ WiFi
             ↓
      ┌─────────────┐
      │ ThingSpeak  │ ← Lưu trữ Cloud
      │   (Cloud)   │
      └─────────────┘
             │
        ┌────┴────┐
        ↓         ↓
  ┌──────────┐  ┌──────────┐
  │   Web    │  │ Telegram │
  │Dashboard │  │   Bot    │
  └──────────┘  └──────────┘
        ↓              ↓
  Browser         Telegram App
   (PC/Phone)      (Phone)
```

**Giải thích:**
1. ESP32 đọc cảm biến → Gửi ThingSpeak (mỗi 20s)
2. Web Dashboard đọc ThingSpeak → Hiển thị (mỗi 10s)
3. Telegram Bot đọc ThingSpeak → Gửi báo cáo (mỗi 15 phút)

---

## 🎯 TÍNH NĂNG NỔI BẬT

### 1. Web Dashboard

**Ưu điểm:**
- ✅ Xem dữ liệu real-time từ mọi nơi
- ✅ Biểu đồ trực quan, dễ phân tích
- ✅ Responsive: Chạy tốt trên điện thoại
- ✅ Không cần cài app

**Công nghệ:**
- Backend: Flask (Python)
- Frontend: HTML/CSS/JavaScript
- Chart: Chart.js
- API: RESTful

**Các API có sẵn:**
```
GET /api/latest          → Dữ liệu mới nhất
GET /api/history/24      → Lịch sử 24h
GET /api/statistics      → Thống kê
```

---

### 2. Telegram Bot

**Ưu điểm:**
- ✅ Nhận thông báo trên điện thoại
- ✅ Không cần mở app riêng
- ✅ Lưu trữ lịch sử báo cáo
- ✅ Cảnh báo khẩn cấp tức thì

**Tần suất:**
- Báo cáo thường: Mỗi 15 phút
- Kiểm tra khẩn cấp: Mỗi 1 phút
- Cảnh báo ngay: Khi gas > 600 ppm

**Có thể mở rộng:**
- Điều khiển thiết bị qua lệnh
- Gửi vào Group/Channel
- Nhiều người nhận báo cáo

---

## 🔐 BẢO MẬT

### ThingSpeak
- Write API Key: Giữ bí mật (để gửi data)
- Read API Key: Tùy chọn (nếu channel private)

### Telegram
- Bot Token: GIỮ BÍ MẬT, không commit lên Git
- Chat ID: Không quan trọng lắm

### Best Practices
```python
# ĐỪNG làm thế này:
BOT_TOKEN = "123456:ABC-DEF..."  # Trong code

# NÊN làm thế này:
# Dùng file .env
from dotenv import load_env
load_env()
BOT_TOKEN = os.getenv("BOT_TOKEN")
```

---

## 📝 CHECKLIST ĐẦY ĐỦ

### ESP32
- [ ] Wokwi chạy được
- [ ] LCD hiển thị dữ liệu
- [ ] ThingSpeak nhận được data (check trên web)
- [ ] 8 Fields có dữ liệu

### Web Dashboard
- [ ] Flask server chạy (http://localhost:5000)
- [ ] 4 cards hiển thị số liệu
- [ ] 2 biểu đồ vẽ được
- [ ] Thống kê hiển thị
- [ ] Tự động refresh

### Telegram Bot
- [ ] Bot gửi test message thành công
- [ ] Nhận báo cáo đầu tiên
- [ ] Đợi 15 phút → Nhận báo cáo tiếp theo
- [ ] Format tin nhắn đẹp (có emoji, bold)

---

## 🎓 HƯỚNG DẪN LÀM BÁO CÁO

### Cấu trúc báo cáo đề xuất

**1. GIỚI THIỆU**
- Vấn đề cần giải quyết
- Mục tiêu dự án
- Phạm vi ứng dụng

**2. CƠ SỞ LÝ THUYẾT**
- ESP32, cảm biến (DHT22, LDR, MQ-2)
- ThingSpeak API
- Flask Web Framework
- Telegram Bot API
- Giao thức HTTP/REST

**3. THIẾT KẾ HỆ THỐNG**
- Sơ đồ tổng thể (3 thành phần)
- Sơ đồ mạch ESP32 (chụp Wokwi)
- Sơ đồ luồng dữ liệu
- Database schema (ThingSpeak 8 fields)

**4. THỰC HIỆN**
- Code ESP32 (giải thích các hàm chính)
- Code Web Dashboard (Flask routes)
- Code Telegram Bot (lên lịch)
- Quá trình test và debug

**5. KẾT QUẢ**
- Screenshot Wokwi
- Screenshot Web Dashboard
- Screenshot tin nhắn Telegram
- Biểu đồ ThingSpeak
- Bảng so sánh trước/sau

**6. ĐÁNH GIÁ**
- Ưu điểm: Hoàn chỉnh, đa nền tảng, dễ mở rộng
- Nhược điểm: Phụ thuộc Internet, giới hạn ThingSpeak free
- So sánh với các giải pháp tương tự

**7. KẾT LUẬN & HƯỚNG PHÁT TRIỂN**
- Đạt được mục tiêu
- Ứng dụng thực tế
- Mở rộng: Mobile app, AI/ML, nhiều phòng

---

## 🎬 KỊCH BẢN DEMO (10 PHÚT)

### Phút 1-2: Giới thiệu
*"Em xin giới thiệu đồ án IoT hoàn chỉnh với 3 thành phần: ESP32, Web Dashboard, và Telegram Bot."*

### Phút 3-4: ESP32 (Wokwi)
1. Mở VS Code → Show Wokwi Simulator
2. Giải thích mạch: DHT22, LDR, MQ-2, Relay, LED
3. Kéo nhiệt độ lên 35°C → LED đỏ sáng, Buzzer kêu
4. Show Serial Monitor: Log chi tiết
5. Show LCD: 3 trang tự động chuyển

### Phút 5-6: Web Dashboard
1. Mở browser: http://localhost:5000
2. Show 4 cards real-time
3. Show 2 biểu đồ 24h
4. Show thống kê
5. F5 refresh → Dữ liệu cập nhật

### Phút 7-8: Telegram Bot
1. Mở Telegram trên điện thoại
2. Show báo cáo định kỳ (có sẵn)
3. Giải thích format tin nhắn
4. Show code lên lịch 15 phút

### Phút 9-10: Tổng kết & Q&A
1. Luồng dữ liệu: ESP32 → ThingSpeak → Web/Telegram
2. Ưu điểm: Đa nền tảng, real-time, tự động
3. Ứng dụng: Smart home, nhà kính, phòng server
4. Trả lời câu hỏi

---

## 🚀 HƯỚNG PHÁT TRIỂN

### Ngắn hạn (1-2 tuần)
- [ ] Thêm database MySQL (lưu lâu dài)
- [ ] Thêm user authentication (Web)
- [ ] Export data ra CSV/Excel
- [ ] Dark mode cho Web

### Trung hạn (1-2 tháng)
- [ ] Mobile App (React Native)
- [ ] Điều khiển qua Telegram (bot commands)
- [ ] Email notification
- [ ] Grafana dashboard

### Dài hạn (3-6 tháng)
- [ ] AI/ML: Dự đoán xu hướng
- [ ] Multi-room support
- [ ] Video streaming (ESP32-CAM)
- [ ] Voice control (Google Assistant)

---

## 📚 TÀI LIỆU THAM KHẢO

### Công nghệ sử dụng
- **ESP32**: https://docs.espressif.com/
- **Flask**: https://flask.palletsprojects.com/
- **Chart.js**: https://www.chartjs.org/
- **Telegram Bot API**: https://core.telegram.org/bots/api
- **ThingSpeak**: https://www.mathworks.com/help/thingspeak/

### Học thêm
- **Python Flask Tutorial**: https://www.tutorialspoint.com/flask/
- **Telegram Bot Python**: https://github.com/python-telegram-bot/python-telegram-bot
- **RESTful API Design**: https://restfulapi.net/

---

## 💬 HỖ TRỢ

### Gặp vấn đề?
1. Đọc lại phần "Khắc phục lỗi"
2. Check Serial Monitor / Console log
3. Test từng thành phần riêng lẻ:
   - ESP32: `pio device monitor`
   - Web: Mở http://localhost:5000 trực tiếp
   - Telegram: Test bằng API URL

### Liên hệ
- GitHub Issues: (link repo của bạn)
- Email: your.email@example.com

---

## 📜 LICENSE

MIT License - Tự do sử dụng cho mục đích học tập và nghiên cứu.

---

<div align="center">

**🎉 Chúc bạn thành công với dự án IoT hoàn chỉnh! 🎉**

**Version 3.0** - Complete IoT Solution

Made with ❤️ by IoT Students

</div>