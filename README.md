# 🌡️ Hệ Thống Giám Sát Môi Trường IoT V5.1

## 📋 Mục lục
- [Giới thiệu](#giới-thiệu)
- [Tính năng](#tính-năng)
- [Kiến trúc hệ thống](#kiến-trúc-hệ-thống)
- [Yêu cầu phần cứng](#yêu-cầu-phần-cứng)
- [Yêu cầu phần mềm](#yêu-cầu-phần-mềm)
- [Cài đặt](#cài-đặt)
- [Cấu hình](#cấu-hình)
- [Chạy hệ thống](#chạy-hệ-thống)
- [Sử dụng](#sử-dụng)
- [Xử lý lỗi](#xử-lý-lỗi)

---

## 🎯 Giới thiệu

Hệ thống giám sát môi trường IoT toàn diện với khả năng:
- ✅ Đo nhiệt độ, độ ẩm, ánh sáng, khí gas
- ✅ Tính toán chỉ số nhiệt và chỉ số thoải mái
- ✅ Điều khiển quạt tự động với hysteresis
- ✅ Gửi dữ liệu lên ThingSpeak & MQTT
- ✅ Web Dashboard thời gian thực
- ✅ Bot Telegram để giám sát từ xa
- ✅ Chế độ test với dữ liệu ngẫu nhiên

---

## 🚀 Tính năng

### 📊 Giám sát
- **Cảm biến DHT22**: Nhiệt độ (°C) và độ ẩm (%)
- **Cảm biến ánh sáng (LDR)**: Cường độ sáng (Lux)
- **Cảm biến khí gas (MQ-2)**: Nồng độ khí gas (PPM)
- **Màn hình LCD 16x2**: Hiển thị 5 trang dữ liệu luân phiên

### 🧮 Tính toán thông minh
- **Heat Index**: Nhiệt độ "cảm giác như" (dựa trên công thức NOAA)
- **Comfort Index**: Chỉ số thoải mái (0-100) từ 4 yếu tố môi trường

### 🌀 Điều khiển tự động
- **Quạt thông minh**: 
  - Bật khi nhiệt độ ≥ 30°C
  - Tắt khi nhiệt độ ≤ 28°C
  - Hysteresis 2°C tránh bật/tắt liên tục

### 🔔 Cảnh báo
- **LED**: Xanh (an toàn), Đỏ (cảnh báo)
- **Buzzer**: Kêu khi có nguy hiểm
- **Telegram**: Thông báo tức thời

### 📡 Kết nối IoT
- **MQTT**: Gửi dữ liệu mỗi 5 giây
- **ThingSpeak**: Lưu trữ mỗi 20 giây
- **WebSocket**: Cập nhật dashboard real-time

### 🧪 Chế độ thử nghiệm
- **TEST_MODE = true**: Dùng giá trị random để kiểm tra logic
- **TEST_MODE = false**: Đọc cảm biến thật

---

## 🏗️ Kiến trúc hệ thống

```
┌─────────────┐
│   ESP32     │
│  (Wokwi)    │
│             │
│ - DHT22     │
│ - LDR       │───────┐
│ - MQ-2      │       │
│ - LCD       │       │
│ - LEDs      │       │
│ - Buzzer    │       ▼
│ - Relay     │   ┌──────────┐
└─────────────┘   │   MQTT   │
                  │ Broker   │
                  └──────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
    ┌────────┐   ┌──────────┐  ┌──────────┐
    │ThingSp.│   │  Flask   │  │ Telegram │
    │ Cloud  │   │   Web    │  │   Bot    │
    └────────┘   └──────────┘  └──────────┘
```

---

## 🔧 Yêu cầu phần cứng

### Mô phỏng trên Wokwi
- ESP32 DevKit V1
- DHT22 (nhiệt độ & độ ẩm)
- Photoresistor sensor (ánh sáng)
- MQ-2 Gas sensor
- LCD 16x2 I2C
- 2x LED (xanh, đỏ)
- 1x Buzzer
- 1x Relay module
- 2x Resistor 220Ω

### Phần cứng thật (tùy chọn)
Tất cả linh kiện trên + breadboard, dây nối

---

## 💻 Yêu cầu phần mềm

### 1. **PlatformIO** (cho ESP32)
```bash
# Cài đặt PlatformIO Core
pip install platformio

# Hoặc dùng VS Code Extension
# Tìm "PlatformIO IDE" trong Extensions
```

### 2. **Python 3.8+** (cho Web & Telegram Bot)
```bash
# Kiểm tra phiên bản
python --version
```

### 3. **Node.js** (tùy chọn - cho công cụ web)
```bash
# Kiểm tra
node --version
npm --version
```

---

## 📦 Cài đặt

### **Bước 1: Clone dự án**
```bash
git clone https://github.com/your-username/iot-environmental-monitor.git
cd iot-environmental-monitor
```

### **Bước 2: Cài đặt ESP32 (PlatformIO)**

#### **2.1. Sử dụng VS Code + PlatformIO**
```bash
# Mở VS Code trong thư mục dự án
code .

# PlatformIO sẽ tự động:
# 1. Phát hiện platformio.ini
# 2. Cài đặt platform ESP32
# 3. Tải các thư viện cần thiết
```

#### **2.2. Sử dụng PlatformIO CLI**
```bash
cd esp32

# Cài đặt dependencies
pio lib install

# Build firmware
pio run

# Upload lên ESP32 (nếu có phần cứng)
pio run --target upload

# Hoặc mở Serial Monitor
pio device monitor
```

#### **2.3. Thư viện ESP32 (tự động cài qua platformio.ini)**
- DHT sensor library
- Adafruit Unified Sensor
- LiquidCrystal_I2C
- ThingSpeak
- PubSubClient (MQTT)

### **Bước 3: Cài đặt Web Dashboard**

```bash
cd web-dashboard

# Tạo virtual environment (khuyến nghị)
python -m venv venv

# Kích hoạt virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt
```

### **Bước 4: Cài đặt Telegram Bot**

```bash
cd telegram-bot

# Tạo virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Cài đặt dependencies
pip install -r requirements.txt
```

---

## ⚙️ Cấu hình

### **1. ESP32 (main.cpp)**

```cpp
// WiFi
const char* ssid = "TEN_WIFI_CUA_BAN";
const char* password = "MAT_KHAU_WIFI";

// ThingSpeak
unsigned long channelID = 3123035;  // Thay bằng Channel ID của bạn
const char* writeAPIKey = "YOUR_WRITE_API_KEY";

// MQTT
const char* mqtt_server = "test.mosquitto.org";  // Hoặc broker của bạn

// Chế độ thử nghiệm
#define TEST_MODE true  // true = random, false = real sensors
```

### **2. Web Dashboard (app.py)**

```python
# MQTT
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883

# ThingSpeak
THINGSPEAK_CHANNEL_ID = "3123035"
THINGSPEAK_READ_API_KEY = "YOUR_READ_API_KEY"
```

### **3. Telegram Bot (bot.py)**

```python
# Bot Token (lấy từ @BotFather)
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN"

# MQTT (giống như Web Dashboard)
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883

# Khoảng thời gian gửi tự động (giây)
AUTO_SEND_INTERVAL = 30
```

### **4. Tạo Telegram Bot**

```
1. Mở Telegram, tìm @BotFather
2. Gửi: /newbot
3. Đặt tên: IoT Monitor Bot
4. Đặt username: iot_monitor_bot
5. Copy token và dán vào bot.py
```

### **5. Tạo ThingSpeak Channel**

```
1. Đăng ký tài khoản tại https://thingspeak.com
2. Tạo New Channel
3. Đặt 8 fields:
   - Field 1: Temperature
   - Field 2: Humidity
   - Field 3: Light (Lux)
   - Field 4: Gas (PPM)
   - Field 5: Fan Status
   - Field 6: Heat Index
   - Field 7: Comfort Index
   - Field 8: Alert Status
4. Copy Channel ID và API Keys
```

---

## 🚀 Chạy hệ thống

### **Phương án A: Chạy trên Wokwi (Khuyến nghị cho học tập)**

#### **1. Chạy ESP32 trên Wokwi**
```
1. Truy cập: https://wokwi.com
2. Tạo New Project → ESP32
3. Copy nội dung:
   - main.cpp
   - diagram.json
   - wokwi.toml
4. Click "Start Simulation"
5. Quan sát Serial Monitor
```

#### **2. Chạy Web Dashboard**
```bash
cd web-dashboard
python app.py

# Mở trình duyệt: http://localhost:5000
```

#### **3. Chạy Telegram Bot**
```bash
cd telegram-bot
python bot.py

# Mở Telegram và gửi /start cho bot
```

### **Phương án B: Chạy với phần cứng thật**

#### **1. Upload code lên ESP32**
```bash
cd esp32
pio run --target upload
pio device monitor
```

#### **2. Chạy Web & Bot** (giống phương án A)

---

## 📱 Sử dụng

### **1. Web Dashboard**
- Truy cập: `http://localhost:5000`
- Xem dữ liệu real-time
- Theo dõi biểu đồ
- Nhận cảnh báo

### **2. Telegram Bot**

#### **Lệnh cơ bản**
```
/start      - Khởi động bot
/data       - Xem dữ liệu hiện tại
/stats      - Xem thống kê chi tiết
/help       - Hướng dẫn
```

#### **Quản lý cảnh báo**
```
/subscribe    - Đăng ký nhận cảnh báo
/unsubscribe  - Hủy cảnh báo
```

#### **Gửi tự động**
```
/auto_on   - Bật gửi dữ liệu mỗi 30 giây
/auto_off  - Tắt gửi tự động
```

### **3. ThingSpeak**
- Truy cập: `https://thingspeak.com/channels/YOUR_CHANNEL_ID`
- Xem biểu đồ lịch sử
- Export dữ liệu CSV
- Tạo visualizations

### **4. LCD (trên ESP32)**
- **Trang 1**: Nhiệt độ & Độ ẩm
- **Trang 2**: Ánh sáng
- **Trang 3**: Khí gas
- **Trang 4**: Chỉ số nhiệt & thoải mái
- **Trang 5**: Trạng thái hệ thống

---

## 🐛 Xử lý lỗi

### **Lỗi 1: ESP32 không kết nối WiFi**
```cpp
// Kiểm tra SSID và password
// Đảm bảo WiFi 2.4GHz (không hỗ trợ 5GHz)
// Thử khởi động lại ESP32
```

### **Lỗi 2: MQTT không kết nối**
```python
# Kiểm tra tường lửa
# Thử broker khác: broker.hivemq.com
# Kiểm tra port 1883 có mở không
```

### **Lỗi 3: ThingSpeak lỗi 429**
```
Nguyên nhân: Gửi quá nhanh (giới hạn 15 giây/lần)
Giải pháp: Tăng THINGSPEAK_INTERVAL trong code
```

### **Lỗi 4: Web Dashboard không hiển thị dữ liệu**
```bash
# Kiểm tra MQTT đang chạy
# Kiểm tra ESP32 đã gửi dữ liệu chưa
# Xem Console log trên trình duyệt (F12)
# Kiểm tra port 5000 không bị chiếm
```

### **Lỗi 5: Telegram Bot không phản hồi**
```python
# Kiểm tra token đúng chưa
# Bot có bị chặn không: @BotFather -> /mybots
# Kiểm tra internet connection
```

### **Lỗi 6: LCD không hiển thị**
```
- Kiểm tra địa chỉ I2C (mặc định: 0x27)
- Chạy I2C Scanner để tìm địa chỉ
- Kiểm tra dây kết nối SDA/SCL
```

---

## 📊 Ngưỡng cảnh báo

| Thông số | Ngưỡng an toàn | Cảnh báo |
|----------|----------------|----------|
| 🌡️ Nhiệt độ | 15-35°C | < 15°C hoặc > 35°C |
| 💧 Độ ẩm | 30-80% | < 30% hoặc > 80% |
| 💡 Ánh sáng | > 200 Lux | < 200 Lux |
| ☁️ Khí gas | < 300 PPM | > 300 PPM |
| 🌀 Quạt | Tự động | BẬT: ≥30°C, TẮT: ≤28°C |

---

## 🔧 Cấu trúc thư mục

```
iot-environmental-monitor/
├── esp32/
│   ├── src/
│   │   └── main.cpp          # Code ESP32
│   ├── platformio.ini        # Cấu hình PlatformIO
│   ├── diagram.json          # Sơ đồ Wokwi
│   └── wokwi.toml            # Cấu hình Wokwi
│
├── web-dashboard/
│   ├── app.py                # Flask server
│   ├── requirements.txt
│   ├── templates/
│   │   └── index.html        # Giao diện web
│   └── static/
│       ├── style.css         # CSS
│       └── app.js            # JavaScript
│
├── telegram-bot/
│   ├── bot.py                # Telegram bot
│   └── requirements.txt
│
├── README.md                 # File này
└── GIAITHICH.md             # Giải thích chi tiết
```

---

## 🎓 Học thêm

### **Tài liệu tham khảo**
- [PlatformIO Docs](https://docs.platformio.org/)
- [ESP32 Arduino Core](https://docs.espressif.com/projects/arduino-esp32/)
- [Wokwi Docs](https://docs.wokwi.com/)
- [Flask-SocketIO](https://flask-socketio.readthedocs.io/)
- [pyTelegramBotAPI](https://pytba.readthedocs.io/)
- [ThingSpeak API](https://www.mathworks.com/help/thingspeak/)

### **Video hướng dẫn** (tự làm)
- Thiết lập môi trường
- Kết nối phần cứng
- Cấu hình ThingSpeak
- Tạo Telegram Bot

---

## 📝 License

MIT License - Tự do sử dụng cho mục đích học tập và nghiên cứu.

---

## 👥 Đóng góp

Mọi đóng góp đều được chào đón! Hãy:
1. Fork dự án
2. Tạo branch mới (`git checkout -b feature/AmazingFeature`)
3. Commit (`git commit -m 'Add some AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

---

## 📧 Liên hệ

- **Email**: phimanhh85@gmail.com
- **GitHub**: 
- **Telegram**:

---

## 🙏 Cảm ơn

Cảm ơn các thư viện và công cụ mã nguồn mở:
- ESP32 Arduino Core
- Adafruit sensors
- Chart.js
- Flask & SocketIO
- python-telegram-bot
- ThingSpeak

---