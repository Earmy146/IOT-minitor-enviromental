# 🌡️ HỆ THỐNG GIÁM SÁT MÔI TRƯỜNG THÔNG MINH V2.0

**Dự án IoT nâng cao - Chạy hoàn toàn trên Wokwi**

![Version](https://img.shields.io/badge/version-2.0-blue)
![Platform](https://img.shields.io/badge/platform-ESP32-orange)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 📁 CẤU TRÚC DỰ ÁN

```
iot-environmental-monitor/
├── src/
│   └── main.cpp                  # Code chính (V2.0)
├── platformio.ini                # Cấu hình PlatformIO
├── wokwi.toml                    # Cấu hình Wokwi  
├── diagram.json                  # Sơ đồ mạch
├── README.md                     # Hướng dẫn sử dụng
└── GIAI_THICH_TINH_NANG.md      # Giải thích chi tiết (MỚI!)
```

**📖 Đọc file `GIAI_THICH_TINH_NANG.md` để hiểu rõ hơn về các tính năng!**

---

## 🚀 TÍNH NĂNG MỚI (V2.0)

### ✨ Cảm biến nâng cao
- ✅ DHT22: Nhiệt độ & độ ẩm
- ✅ LDR: Cường độ ánh sáng
- ✅ **MQ-2: Cảm biến khí gas** (NEW!)
- ✅ **Tính Heat Index** (NEW!)
- ✅ **Tính Comfort Index (0-100)** (NEW!)

### ✨ Thiết bị điều khiển
- ✅ 3 LED: Green/Red/Blue (trạng thái)
- ✅ Buzzer: Cảnh báo
- ✅ **2 Relay: Quạt & Đèn** (NEW!)
- ✅ **Nút bấm: Chuyển Auto/Manual** (NEW!)

### ✨ Kết nối IoT
- ✅ ThingSpeak: 8 Fields (thay vì 3)
- ✅ **MQTT Real-time** (NEW!)
- ✅ **Remote Control qua MQTT** (NEW!)
- ✅ WiFi tự động kết nối

### ✨ Giao diện & Thống kê
- ✅ **LCD 3 trang tự động chuyển** (NEW!)
  - Trang 1: Dữ liệu cảm biến + chỉ số
  - Trang 2: Trạng thái thiết bị
  - Trang 3: Thống kê trung bình
- ✅ **Serial Monitor đẹp với box** (NEW!)

### ✨ Tự động hóa thông minh
- ✅ **Auto Mode**: Tự động bật/tắt quạt, đèn
- ✅ **Manual Mode**: Điều khiển bằng MQTT
- ✅ **Thống kê**: Đếm số lần đo, trung bình

---

## ⚡ HƯỚNG DẪN NHANH

### Bước 1: Cài đặt (như cũ)

1. Tải **VS Code**: https://code.visualstudio.com/
2. Cài Extensions:
   - **PlatformIO IDE**
   - **Wokwi Simulator**

### Bước 2: Tạo dự án

1. Tạo thư mục `iot-environmental-monitor`
2. Copy 4 file đã cập nhật:
   - `platformio.ini` (có thêm PubSubClient)
   - `wokwi.toml`
   - `diagram.json` (có thêm MQ-2, Relay, Button)
   - `src/main.cpp` (code V2.0 nâng cao)

### Bước 3: Cấu hình ThingSpeak

**Lưu ý V2.0:** Cần tạo **8 Fields** (thay vì 3)

1. Vào https://thingspeak.com/ → New Channel

2. Điền Fields:
   ```
   Field 1: Temperature (°C)
   Field 2: Humidity (%)
   Field 3: Light Level
   Field 4: Gas Level
   Field 5: Fan Status (0/1)
   Field 6: Light Status (0/1)
   Field 7: Heat Index (°C)
   Field 8: Comfort Index (0-100)
   ```

3. Copy Channel ID và Write API Key vào `main.cpp` (dòng 18-19)

### Bước 4: Chạy dự án

```bash
# 1. Build
pio run

# 2. Chạy Wokwi
Ctrl+Shift+P → "Wokwi: Start Simulator"
```

---

## 🎮 CÁCH SỬ DỤNG

### 1. Tương tác với cảm biến

**Wokwi Simulator:**
- Click **DHT22** → Kéo nhiệt độ/độ ẩm
- Click **LDR** → Kéo ánh sáng
- Click **MQ-2** → Kéo nồng độ gas

### 2. Chuyển chế độ

**Nút MODE (Button):**
- Click để chuyển **Auto ↔ Manual**
- **Auto Mode**: Tự động điều khiển Quạt/Đèn
  - Quạt ON khi nhiệt độ > 30°C
  - Đèn ON khi ánh sáng < 300
- **Manual Mode**: Điều khiển qua MQTT

### 3. LCD tự động chuyển trang

**Mỗi 5 giây chuyển 1 trang:**
```
Trang 1: T:28.5C H:65% L:750 G:250
         HI:29.2 CI:85
         STATUS: EXCELLENT

Trang 2: === DEVICES ===
         Fan:   ON  (Auto)
         Light: OFF (Auto)
         Mode: AUTOMATIC

Trang 3: === STATISTICS ===
         Data Count: 125
         Avg T: 28.3C
         Avg H: 64.8%
```

### 4. Quan sát LED

- 💙 **LED Blue**: Đang kết nối WiFi
- 💚 **LED Green**: Hệ thống OK
- 🔴 **LED Red**: Cảnh báo
- 🔊 **Buzzer**: Kêu khi có alert

### 5. Điều khiển từ xa (MQTT)

**Dùng MQTT Client** (MQTT Explorer, MQTTX):

```
Broker: test.mosquitto.org:1883

Subscribe topics:
- iot/env/data    → Nhận dữ liệu mỗi 5s
- iot/env/status  → Nhận trạng thái hệ thống

Publish to: iot/env/control
Commands:
- FAN_ON         → Bật quạt
- FAN_OFF        → Tắt quạt
- LIGHT_ON       → Bật đèn
- LIGHT_OFF      → Tắt đèn
- AUTO_MODE      → Chuyển chế độ tự động
- MANUAL_MODE    → Chuyển chế độ thủ công
- RESET_STATS    → Reset thống kê
```

---

## 📊 OUTPUT MẪU

### Serial Monitor Output

```
========== DU LIEU CAM BIEN ==========
Nhiet do      : 28.5 *C
Do am         : 65.3 %
Anh sang      : 750 lux
Khi gas       : 250 ppm
Chi so nhiet  : 29.2 *C
Chi so thoai mai: 85/100

========== THIET BI ==========
Quat          : BAT
Den           : TAT
Che do        : TU DONG
======================================

→ Sending to ThingSpeak...
✓ ThingSpeak: Success

✓ MQTT: {"temp":28.5,"humid":65.3,"light":750,"gas":250,"fan":true,"light_relay":false,"heat_index":29.2,"comfort":85,"mode":"auto"}
```

### ThingSpeak Dashboard

**8 Biểu đồ:**
1. Temperature over time
2. Humidity over time
3. Light Level over time
4. Gas Level over time
5. Fan Status (0/1)
6. Light Status (0/1)
7. Heat Index over time
8. Comfort Index over time

---

## 🧮 CÔNG THỨC

### Heat Index (Chỉ số nhiệt)
```
HI = c1 + c2*T + c3*RH + c4*T*RH + c5*T² + c6*RH² 
     + c7*T²*RH + c8*T*RH² + c9*T²*RH²
```
Đánh giá cảm giác nhiệt thực tế khi có độ ẩm.

### Comfort Index (Chỉ số thoải mái)
```
CI = (TempScore + HumidScore + LightScore + GasScore) / 4

- TempScore  = 100 - |24 - T| * 5
- HumidScore = 100 - |60 - RH| * 2
- LightScore = Light / 10
- GasScore   = 100 - Gas / 10
```

**Đánh giá:**
- 80-100: Excellent (Tuyệt vời)
- 60-79: Good (Tốt)
- 40-59: Fair (Chấp nhận được)
- 0-39: Poor (Kém)

---

## 🎯 NGƯỠNG CẢNH BÁO

| Tham số | Min | Max | Hành động |
|---------|-----|-----|-----------|
| Nhiệt độ | 15°C | 35°C | LED đỏ + Buzzer |
| Độ ẩm | 30% | 80% | LED đỏ + Buzzer |
| Ánh sáng | 300 | - | LED đỏ + Buzzer |
| Khí gas | - | 400 | LED đỏ + Buzzer |

---

## 🔧 TỰ ĐỘNG HÓA

### Chế độ Auto

**Quạt:**
- ON: Nhiệt độ > 30°C
- OFF: Nhiệt độ ≤ 28°C

**Đèn:**
- ON: Ánh sáng < 300
- OFF: Ánh sáng ≥ 500

### Chế độ Manual

Điều khiển bằng MQTT commands (xem phần 5 ở trên).

---

## 📈 SO SÁNH V1.0 vs V2.0

| Tính năng | V1.0 | V2.0 |
|-----------|------|------|
| Cảm biến | DHT22, LDR | + MQ-2 |
| Actuator | LED, Buzzer | + 2 Relay |
| ThingSpeak Fields | 3 | 8 |
| MQTT | ❌ | ✅ |
| Remote Control | ❌ | ✅ |
| Auto/Manual Mode | ❌ | ✅ |
| LCD Pages | 1 | 3 |
| Heat Index | ❌ | ✅ |
| Comfort Index | ❌ | ✅ |
| Statistics | ❌ | ✅ |
| Button Input | ❌ | ✅ |

---

## 🐛 KHẮC PHỤC LỖI

### Lỗi: "PubSubClient.h not found"
```bash
# Kiểm tra platformio.ini có dòng:
knolleary/PubSubClient@^2.8

# Build lại:
pio run --target clean
pio run
```

### Lỗi: MQTT không kết nối
```
Kiểm tra Serial Monitor:
- Có dòng "MQTT: OK!" không?
- Nếu "Error: -2" → Broker đang bận, thử lại
- Nếu "Error: -4" → Timeout, check WiFi
```

### Relay không hoạt động
```
Trong Wokwi:
- Relay hiển thị màu xanh = ON
- Relay màu xám = OFF
- Click để test thủ công
```

### LCD không chuyển trang
```
Đợi 5 giây, tự động chuyển
Hoặc check code: lastPageChange
```

---

## 📱 TEST MQTT (Tùy chọn)

### Cài MQTT Client

**Windows/Mac/Linux:**
- MQTT Explorer: http://mqtt-explorer.com/
- MQTTX: https://mqttx.app/

### Kết nối

```
Host: test.mosquitto.org
Port: 1883
Client ID: (tự động)

Subscribe:
- iot/env/data
- iot/env/status
```

### Test Commands

```
Topic: iot/env/control

Gửi: FAN_ON
→ Quạt sẽ bật, màn hình hiển thị "Fan: ON (Man)"

Gửi: AUTO_MODE
→ Chuyển về chế độ tự động
```

---

## 📝 CHECKLIST V2.0

### Cơ bản
- [ ] VS Code + PlatformIO + Wokwi đã cài
- [ ] Tạo đủ 4 file (platformio.ini, wokwi.toml, diagram.json, main.cpp)
- [ ] ThingSpeak Channel có 8 Fields
- [ ] Cập nhật Channel ID và API Key
- [ ] Build thành công (`pio run`)
- [ ] Wokwi chạy được

### Nâng cao
- [ ] DHT22, LDR, MQ-2 hoạt động
- [ ] LCD chuyển 3 trang tự động (mỗi 5s)
- [ ] Nút MODE chuyển Auto/Manual
- [ ] Relay Quạt tự động bật khi > 30°C
- [ ] Relay Đèn tự động bật khi < 300
- [ ] ThingSpeak hiển thị 8 biểu đồ
- [ ] MQTT gửi data mỗi 5s
- [ ] Test remote control qua MQTT

---

## 🎓 NỘI DUNG BÁO CÁO GỢI Ý

### Phần nâng cao có thể thêm:

**1. Heat Index & Comfort Index**
- Giải thích công thức
- Ý nghĩa trong thực tế
- So sánh với chuẩn ASHRAE

**2. MQTT Protocol**
- QoS levels
- Publish/Subscribe model
- So sánh với HTTP

**3. Tự động hóa**
- Thuật toán điều khiển
- Hysteresis (chống dao động)
- State Machine diagram

**4. Thống kê**
- Running average
- Data logging
- Trend analysis

---

## 🚀 HƯỚNG PHÁT TRIỂN

### Có thể mở rộng thêm:

1. **Deep Sleep**: Tiết kiệm pin cho ESP32 chạy battery
2. **SD Card**: Lưu log offline
3. **Web Server**: ESP32 tự host web dashboard
4. **Blynk**: Mobile app điều khiển
5. **Machine Learning**: Dự đoán xu hướng với TensorFlow Lite
6. **Multi-sensor**: Thêm nhiều phòng
7. **Database**: MySQL/InfluxDB thay vì ThingSpeak
8. **Grafana**: Dashboard chuyên nghiệp

---

## 📚 TÀI LIỆU THAM KHẢO

- ESP32: https://docs.espressif.com/
- PlatformIO: https://docs.platformio.org/
- Wokwi: https://docs.wokwi.com/
- ThingSpeak: https://www.mathworks.com/help/thingspeak/
- MQTT: https://mqtt.org/
- PubSubClient: https://pubsubclient.knolleary.net/

---

## 📞 HỖ TRỢ

Nếu gặp vấn đề:
1. Check Serial Monitor để xem log chi tiết
2. Đọc lại phần Khắc phục lỗi
3. Kiểm tra kết nối mạng (WiFi icon trong Wokwi)

---

<div align="center">

**🎉 Chúc bạn thành công với dự án nâng cao! 🎉**

Version 2.0 - Advanced IoT Environmental Monitoring System

Made with ❤️ for IoT Students

</div>