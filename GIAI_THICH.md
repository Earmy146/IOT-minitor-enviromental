# 📖 GIẢI THÍCH CHI TIẾT CÁC TÍNH NĂNG

## 🎯 TỔNG QUAN HỆ THỐNG

Hệ thống giám sát môi trường thông minh giúp:
- **Đo đạc**: Tự động đo nhiệt độ, độ ẩm, ánh sáng, khí gas
- **Cảnh báo**: Báo động khi môi trường không an toàn
- **Tự động hóa**: Tự động bật quạt khi nóng, bật đèn khi tối
- **Giám sát từ xa**: Xem dữ liệu trên điện thoại/máy tính qua Internet

---

## 📡 PHẦN 1: CẢM BIẾN (Đo đạc)

### 1. DHT22 - Cảm biến nhiệt độ & độ ẩm

**Là gì?**
- Đo nhiệt độ không khí (°C)
- Đo độ ẩm không khí (%)

**Tại sao cần?**
- Nhiệt độ quá cao/thấp → Không thoải mái, ảnh hưởng sức khỏe
- Độ ẩm quá cao → Mốc, vi khuẩn phát triển
- Độ ẩm quá thấp → Khô da, khó thở

**Ứng dụng thực tế:**
- Phòng ngủ: 20-24°C, 50-60% RH
- Phòng máy chủ: 18-27°C, 45-55% RH
- Nhà kính trồng rau: 25-30°C, 60-80% RH

**Trong code:**
```cpp
temperature = dht.readTemperature();  // Đọc nhiệt độ
humidity = dht.readHumidity();        // Đọc độ ẩm
```

---

### 2. LDR - Cảm biến ánh sáng

**Là gì?**
- Light Dependent Resistor (điện trở phụ thuộc ánh sáng)
- Đo cường độ ánh sáng (0-1000 lux)

**Tại sao cần?**
- Ánh sáng yếu → Mỏi mắt khi làm việc/học
- Ánh sáng quá mạnh → Chói mắt, tốn điện

**Ứng dụng thực tế:**
- Tự động bật đèn khi trời tối
- Điều chỉnh độ sáng màn hình điện thoại
- Đèn đường tự động sáng vào ban đêm

**Trong code:**
```cpp
int ldrValue = analogRead(LDR_PIN);
lightLevel = map(ldrValue, 0, 4095, 0, 1000);
```

**Giá trị tham khảo:**
- 0-200: Tối (cần đèn)
- 200-500: Ánh sáng yếu
- 500-800: Đủ sáng
- 800-1000: Rất sáng

---

### 3. MQ-2 - Cảm biến khí gas

**Là gì?**
- Phát hiện khí gas dễ cháy (LPG, propane, methane)
- Đo nồng độ khí (0-1000 ppm)

**Tại sao cần?**
- Gas rò rỉ → Nguy hiểm cháy nổ, ngộ độc
- Phát hiện sớm → Cảnh báo kịp thời

**Ứng dụng thực tế:**
- Nhà bếp: Phát hiện gas rò rỉ từ bếp
- Nhà máy: Giám sát khu vực nguy hiểm
- Hầm xe: Phát hiện khí CO từ xe

**Trong code:**
```cpp
int mq2Value = analogRead(MQ2_PIN);
gasLevel = map(mq2Value, 0, 4095, 0, 1000);
```

**Ngưỡng nguy hiểm:**
- < 400: An toàn
- 400-600: Cảnh báo
- > 600: Nguy hiểm!

---

## 🎛️ PHẦN 2: THIẾT BỊ ĐIỀU KHIỂN (Actuators)

### 1. LED (Đèn chỉ thị)

**3 màu LED:**

🟢 **LED Xanh (Green)** - D25
- Sáng: Mọi thứ bình thường
- Tắt: Có vấn đề

🔴 **LED Đỏ (Red)** - D26
- Sáng: Cảnh báo (nhiệt độ, độ ẩm, gas vượt ngưỡng)
- Tắt: An toàn

🔵 **LED Xanh dương (Blue)** - D14
- Sáng: Đang kết nối WiFi
- Tắt: Đã kết nối xong

**Trong code:**
```cpp
digitalWrite(LED_GREEN, HIGH);  // Bật LED xanh
digitalWrite(LED_RED, HIGH);    // Bật LED đỏ
```

---

### 2. Buzzer (Còi cảnh báo)

**Là gì?**
- Loa nhỏ phát ra tiếng beep

**Khi nào kêu?**
- Nhiệt độ > 35°C hoặc < 15°C
- Độ ẩm > 80% hoặc < 30%
- Ánh sáng < 300 lux
- Khí gas > 400 ppm

**Trong code:**
```cpp
tone(BUZZER_PIN, 1000, 200);  // Kêu 1000Hz trong 200ms
```

---

### 3. Relay (Công tắc điện tử)

**Relay là gì?**
- Công tắc điều khiển bằng tín hiệu điện
- ESP32 gửi tín hiệu → Relay bật/tắt thiết bị điện

**Relay 1 - Quạt (Fan) - D33**

*Tự động (Auto Mode):*
- Nhiệt độ > 30°C → Tự động BẬT quạt
- Nhiệt độ ≤ 28°C → Tự động TẮT quạt

*Thủ công (Manual Mode):*
- Điều khiển bằng MQTT: `FAN_ON` / `FAN_OFF`

**Relay 2 - Đèn (Light) - D32**

*Tự động (Auto Mode):*
- Ánh sáng < 300 lux → Tự động BẬT đèn
- Ánh sáng ≥ 500 lux → Tự động TẮT đèn

*Thủ công (Manual Mode):*
- Điều khiển bằng MQTT: `LIGHT_ON` / `LIGHT_OFF`

**Trong code:**
```cpp
// Ví dụ: Tự động bật quạt
if (temperature > 30.0 && !fanStatus) {
    fanStatus = true;
    digitalWrite(RELAY_FAN, HIGH);  // Bật quạt
    Serial.println("Quat: BAT");
}
```

---

### 4. Button (Nút bấm MODE)

**Chức năng:**
- Chuyển đổi giữa 2 chế độ:
  - **AUTO**: Hệ thống tự động điều khiển quạt, đèn
  - **MANUAL**: Bạn điều khiển bằng MQTT

**Cách dùng:**
- Nhấn 1 lần → Chuyển AUTO ↔ MANUAL
- LCD sẽ hiển thị chế độ hiện tại

**Trong code:**
```cpp
if (buttonState == LOW && lastButtonState == HIGH) {
    autoMode = !autoMode;  // Đảo ngược chế độ
}
```

---

## 📊 PHẦN 3: CHỈ SỐ TÍNH TOÁN

### 1. Heat Index (Chỉ số nhiệt)

**Là gì?**
- Nhiệt độ "cảm nhận được" khi có độ ẩm
- Ví dụ: 30°C + độ ẩm 80% = cảm giác như 35°C

**Tại sao cần?**
- Độ ẩm cao làm mồ hôi khó bay hơi
- Cơ thể khó tản nhiệt → Cảm giác nóng hơn

**Công thức:**
```
HI = c1 + c2*T + c3*RH + c4*T*RH + c5*T² + c6*RH² + ...
```
(Công thức phức tạp của NOAA - Cơ quan Khí tượng Mỹ)

**Ví dụ:**
- Nhiệt độ 32°C, độ ẩm 60% → Heat Index = 35.6°C
- Nhiệt độ 32°C, độ ẩm 90% → Heat Index = 42.1°C (nguy hiểm!)

---

### 2. Comfort Index (Chỉ số thoải mái)

**Là gì?**
- Đánh giá tổng thể môi trường có thoải mái không (0-100 điểm)
- Tính dựa trên: Nhiệt độ, độ ẩm, ánh sáng, khí gas

**Cách tính:**
```
Điểm nhiệt độ = 100 - |24 - nhiệt độ| × 5
  → Nhiệt độ lý tưởng: 24°C
  → 24°C = 100 điểm
  → 20°C hoặc 28°C = 80 điểm

Điểm độ ẩm = 100 - |60 - độ ẩm| × 2
  → Độ ẩm lý tưởng: 60%
  → 60% = 100 điểm
  → 50% hoặc 70% = 80 điểm

Điểm ánh sáng = ánh sáng / 10
  → 500 lux = 50 điểm
  → 800 lux = 80 điểm

Điểm gas = 100 - gas / 10
  → 0 ppm = 100 điểm
  → 400 ppm = 60 điểm

Comfort Index = Trung bình 4 điểm trên
```

**Đánh giá:**
- 80-100: Tuyệt vời (Excellent) 😊
- 60-79: Tốt (Good) 🙂
- 40-59: Chấp nhận được (Fair) 😐
- 0-39: Kém (Poor) ☹️

**Ví dụ:**
```
Phòng A: T=24°C, RH=60%, L=700, G=100
→ CI = (100 + 100 + 70 + 90) / 4 = 90 → Tuyệt vời!

Phòng B: T=35°C, RH=90%, L=200, G=500
→ CI = (45 + 40 + 20 + 50) / 4 = 39 → Kém!
```

---

## 🌐 PHẦN 4: KẾT NỐI IoT

### 1. WiFi

**Chức năng:**
- Kết nối ESP32 vào mạng Internet
- Trong Wokwi: Tự động kết nối với "Wokwi-GUEST"

**Trong code:**
```cpp
WiFi.begin(ssid, password);
// Đợi kết nối...
if (WiFi.status() == WL_CONNECTED) {
    Serial.println("WiFi ket noi thanh cong!");
}
```

---

### 2. ThingSpeak (Cloud IoT Platform)

**ThingSpeak là gì?**
- Website miễn phí lưu trữ dữ liệu IoT
- Tự động tạo biểu đồ, theo dõi từ xa

**Hoạt động như thế nào?**
1. ESP32 đo cảm biến → Có dữ liệu
2. ESP32 gửi dữ liệu lên ThingSpeak (qua WiFi)
3. ThingSpeak lưu trữ và vẽ biểu đồ
4. Bạn mở website ThingSpeak → Xem biểu đồ

**Trong code:**
```cpp
ThingSpeak.setField(1, temperature);    // Field 1: Nhiệt độ
ThingSpeak.setField(2, humidity);       // Field 2: Độ ẩm
ThingSpeak.setField(3, lightLevel);     // Field 3: Ánh sáng
// ... (8 fields total)

int status = ThingSpeak.writeFields(channelID, writeAPIKey);
// status = 200 → Thành công!
```

**Tần suất gửi:**
- Mỗi 20 giây gửi 1 lần
- ThingSpeak miễn phí giới hạn: tối thiểu 15 giây/lần

**8 Fields trong ThingSpeak:**
1. Temperature (Nhiệt độ)
2. Humidity (Độ ẩm)
3. Light Level (Ánh sáng)
4. Gas Level (Khí gas)
5. Fan Status (Quạt: 0=Tắt, 1=Bật)
6. Light Status (Đèn: 0=Tắt, 1=Bật)
7. Heat Index (Chỉ số nhiệt)
8. Comfort Index (Chỉ số thoải mái)

---

### 3. MQTT (Message Queue Telemetry Transport)

**MQTT là gì?**
- Giao thức truyền tin IoT nhanh, nhẹ
- Hoạt động theo mô hình Publish/Subscribe

**Giải thích đơn giản:**
- **Broker**: Máy chủ trung gian (test.mosquitto.org)
- **Publisher**: Thiết bị gửi tin (ESP32)
- **Subscriber**: Thiết bị/App nhận tin (điện thoại của bạn)
- **Topic**: Kênh truyền tin (giống như kênh TV)

**Ví dụ thực tế:**
```
ESP32 → Publish vào topic "iot/env/data"
      → Tin nhắn: {"temp":28.5, "humid":65, ...}

Điện thoại → Subscribe topic "iot/env/data"
           → Nhận được tin: {"temp":28.5, "humid":65, ...}
           → Hiển thị lên app
```

**3 Topics trong dự án:**

1. **iot/env/data** (ESP32 → App)
   - ESP32 gửi dữ liệu mỗi 5 giây
   - Format: JSON
   ```json
   {
     "temp": 28.5,
     "humid": 65.3,
     "light": 750,
     "gas": 250,
     "fan": true,
     "light_relay": false
   }
   ```

2. **iot/env/control** (App → ESP32)
   - App gửi lệnh điều khiển
   - Commands:
     - `FAN_ON` → Bật quạt
     - `FAN_OFF` → Tắt quạt
     - `LIGHT_ON` → Bật đèn
     - `LIGHT_OFF` → Tắt đèn
     - `AUTO_MODE` → Chế độ tự động
     - `MANUAL_MODE` → Chế độ thủ công

3. **iot/env/status** (ESP32 → App)
   - ESP32 báo trạng thái hệ thống
   - Ví dụ: "online", "fan_auto_on", "alert"

**Tại sao dùng MQTT thay vì ThingSpeak?**
- MQTT: Real-time (tức thì), 2 chiều
- ThingSpeak: Chậm hơn (20s), 1 chiều

---

## 🖥️ PHẦN 5: LCD (Màn hình hiển thị)

**LCD 20x4:**
- 20 ký tự × 4 dòng
- Hiển thị thông tin trực tiếp trên thiết bị

**Tự động chuyển 3 trang (mỗi 5 giây):**

### Trang 1: Dữ liệu cảm biến
```
T:28.5C H:65%
L:750 G:250
HI:29.2 CI:85
STATUS: EXCELLENT
```

### Trang 2: Trạng thái thiết bị
```
=== DEVICES ===
Fan:   ON  (Auto)
Light: OFF (Auto)
Mode: AUTOMATIC
```

### Trang 3: Thống kê
```
=== STATISTICS ===
Data Count: 125
Avg T: 28.3C
Avg H: 64.8%
```

---

## 🔄 PHẦN 6: HAI CHẾ ĐỘ HOẠT ĐỘNG

### CHẾ ĐỘ 1: AUTO (Tự động)

**Đặc điểm:**
- Hệ thống tự quyết định
- Không cần can thiệp

**Quy tắc:**

1. **Quạt:**
   - Nhiệt độ > 30°C → Tự động BẬT
   - Nhiệt độ ≤ 28°C → Tự động TẮT
   - *Lý do có 2°C chênh lệch: Tránh bật tắt liên tục*

2. **Đèn:**
   - Ánh sáng < 300 lux → Tự động BẬT
   - Ánh sáng ≥ 500 lux → Tự động TẮT

**Ưu điểm:**
- Tiện lợi, không cần thao tác
- Tiết kiệm điện (bật đúng lúc cần)

**Nhược điểm:**
- Không linh hoạt theo ý muốn cá nhân

---

### CHẾ ĐỘ 2: MANUAL (Thủ công)

**Đặc điểm:**
- Bạn điều khiển mọi thứ
- Dùng MQTT để gửi lệnh

**Cách điều khiển:**
1. Cài MQTT Client (MQTT Explorer, MQTTX)
2. Kết nối: `test.mosquitto.org:1883`
3. Publish vào topic `iot/env/control`:
   - `FAN_ON` → Bật quạt
   - `FAN_OFF` → Tắt quạt
   - `LIGHT_ON` → Bật đèn
   - `LIGHT_OFF` → Tắt đèn

**Ưu điểm:**
- Linh hoạt, điều khiển từ xa
- Theo ý muốn cá nhân

**Nhược điểm:**
- Phải thao tác thủ công
- Có thể quên tắt → Lãng phí điện

---

### Chuyển đổi giữa 2 chế độ:

**Cách 1: Nhấn nút MODE** (trên Wokwi)
- Click button → Chuyển AUTO ↔ MANUAL

**Cách 2: Qua MQTT**
- Publish `AUTO_MODE` hoặc `MANUAL_MODE`

---

## 📈 PHẦN 7: THỐNG KÊ

**Hệ thống tự động ghi nhận:**
- Số lần đo: `dataCount`
- Tổng nhiệt độ: `tempSum`
- Tổng độ ẩm: `humidSum`

**Tính trung bình:**
```cpp
float avgTemp = tempSum / dataCount;
float avgHumid = humidSum / dataCount;
```

**Ứng dụng:**
- Biết nhiệt độ trung bình trong ngày
- So sánh giữa các ngày
- Phát hiện xu hướng (ngày càng nóng, càng ẩm...)

**Reset thống kê:**
- Gửi MQTT: `RESET_STATS`

---

## 🎯 TÓM TẮT QUY TRÌNH HOẠT ĐỘNG

```
BẮT ĐẦU
  ↓
1. Khởi động ESP32
   → Kết nối WiFi
   → Kết nối MQTT Broker
   ↓
2. Đọc cảm biến (mỗi 2 giây)
   → DHT22: Nhiệt độ, Độ ẩm
   → LDR: Ánh sáng
   → MQ-2: Khí gas
   ↓
3. Tính toán
   → Heat Index
   → Comfort Index
   ↓
4. Kiểm tra cảnh báo
   → Có vượt ngưỡng? → BẬT LED đỏ + Buzzer
   → An toàn? → BẬT LED xanh
   ↓
5. Chế độ AUTO?
   → Có: Tự động điều khiển Quạt/Đèn
   → Không: Chờ lệnh MQTT
   ↓
6. Hiển thị
   → LCD: Chuyển 3 trang
   → Serial Monitor: In dữ liệu
   ↓
7. Gửi IoT
   → ThingSpeak: Mỗi 20 giây
   → MQTT: Mỗi 5 giây
   ↓
8. Lặp lại từ bước 2
```

---

## 💡 CÂU HỎI THƯỜNG GẶP

### Q1: Tại sao cần Heat Index khi đã có nhiệt độ?

**A:** Nhiệt độ không nói lên tất cả! 

Ví dụ:
- Phòng A: 30°C, độ ẩm 40% → Cảm giác khô ráo, chịu được
- Phòng B: 30°C, độ ẩm 80% → Cảm giác ngột ngạt, rất khó chịu

Heat Index = Nhiệt độ "thực sự cảm nhận được" khi có độ ẩm.

---

### Q2: Comfort Index khác Heat Index thế nào?

**A:**
- **Heat Index**: Chỉ tính nhiệt độ + độ ẩm
- **Comfort Index**: Tính tổng thể (nhiệt độ + độ ẩm + ánh sáng + gas)

Comfort Index toàn diện hơn, đánh giá môi trường tổng thể.

---

### Q3: Tại sao Quạt bật ở 30°C nhưng tắt ở 28°C?

**A:** Để tránh hiện tượng "dao động" (oscillation).

Nếu bật/tắt cùng 1 ngưỡng (ví dụ 29°C):
- 29.1°C → Bật quạt
- Quạt thổi → 28.9°C → Tắt quạt
- Tắt quạt → Nóng lại 29.1°C → Bật quạt
- → Bật tắt liên tục!

Có 2°C chênh lệch (hysteresis) → Ổn định hơn.

---

### Q4: MQTT và ThingSpeak, dùng cái nào?

**A:** Dùng CẢ HAI, mỗi cái có ưu điểm riêng:

**ThingSpeak:**
- Lưu trữ lâu dài (vài tháng)
- Vẽ biểu đồ đẹp
- Dễ phân tích xu hướng
- Nhưng chậm (20 giây)

**MQTT:**
- Real-time (5 giây)
- Điều khiển 2 chiều
- Nhanh, tức thì
- Nhưng không lưu trữ

---

### Q5: Làm sao biết hệ thống đang ở chế độ nào?

**A:** Có 3 cách:
1. Xem LCD - Trang 2: Dòng cuối "Mode: AUTOMATIC" hoặc "MANUAL"
2. Xem Serial Monitor: In ra "Che do: TU DONG" hoặc "THU CONG"
3. Subscribe MQTT topic `iot/env/status`: Nhận "auto_mode" hoặc "manual_mode"

---

### Q6: Tại sao có 3 LED thay vì 1?

**A:** Mỗi LED có nhiệm vụ riêng:

🔵 **LED Blue (Xanh dương)**
- Chỉ sáng 1 lần khi khởi động
- Đang kết nối WiFi
- Tắt = Đã kết nối xong

💚 **LED Green (Xanh lá)**
- Trạng thái bình thường
- Sáng = Mọi thứ OK
- Tắt = Có vấn đề

🔴 **LED Red (Đỏ)**
- Cảnh báo
- Sáng = Có thông số vượt ngưỡng
- Tắt = An toàn

Nhìn LED biết ngay trạng thái, không cần xem màn hình!

---

### Q7: Tôi có thể thay đổi ngưỡng cảnh báo không?

**A:** Có! Sửa trong code (dòng 42-47):

```cpp
const float TEMP_MAX = 35.0;      // ← Thay số này
const float TEMP_MIN = 15.0;      // ← Thay số này
const float HUMID_MAX = 80.0;     // ← Thay số này
const float HUMID_MIN = 30.0;     // ← Thay số này
const int LIGHT_MIN = 500;        // ← Thay số này
const int GAS_THRESHOLD = 400;    // ← Thay số này
```

Ví dụ bạn muốn cảnh báo nhiệt độ > 32°C:
```cpp
const float TEMP_MAX = 32.0;  // Thay 35 thành 32
```

Sau đó build lại: `pio run`

---

## 🎯 KẾT LUẬN

### Hệ thống này giải quyết vấn đề gì?

**Vấn đề 1: Giám sát môi trường thủ công tốn thời gian**
→ Giải pháp: Tự động đo, hiển thị 24/7

**Vấn đề 2: Không biết khi nào môi trường nguy hiểm**
→ Giải pháp: Cảnh báo ngay khi vượt ngưỡng

**Vấn đề 3: Quên bật quạt/đèn**
→ Giải pháp: Tự động hóa thông minh

**Vấn đề 4: Không theo dõi được khi đi xa**
→ Giải pháp: IoT Cloud (ThingSpeak + MQTT)

---

### Ứng dụng thực tế

1. **Nhà thông minh**
   - Tự động điều hòa nhiệt độ
   - Tiết kiệm điện

2. **Nhà kính trồng rau**
   - Giám sát điều kiện cây trồng
   - Tăng năng suất

3. **Phòng máy chủ**
   - Cảnh báo nhiệt độ cao → Tránh hỏng máy
   - Phát hiện gas/khói → Phòng cháy

4. **Phòng bảo quản**
   - Dược phẩm, thực phẩm cần nhiệt độ ổn định
   - Ghi log để kiểm tra

5. **Phòng lab**
   - Môi trường ảnh hưởng kết quả thí nghiệm
   - Cần giám sát chính xác

---

### Điểm mạnh của dự án

✅ **Đầy đủ tính năng IoT**: Cảm biến + Cloud + Tự động hóa  
✅ **Thông minh**: Tự động học và điều chỉnh  
✅ **Linh hoạt**: Auto + Manual mode  
✅ **Dễ mở rộng**: Thêm cảm biến/thiết bị dễ dàng  
✅ **Tiết kiệm**: Không tốn chi phí vận hành  
✅ **Giáo dục**: Học được nhiều công nghệ IoT  

---

## 📚 TÀI LIỆU THAM KHẢO

### Về cảm biến
- DHT22 Datasheet: https://www.sparkfun.com/datasheets/Sensors/Temperature/DHT22.pdf
- MQ-2 Datasheet: https://www.pololu.com/file/0J309/MQ2.pdf

### Về giao thức
- MQTT Protocol: https://mqtt.org/
- I2C Communication: https://www.nxp.com/docs/en/user-guide/UM10204.pdf

### Về IoT Platform
- ThingSpeak Documentation: https://www.mathworks.com/help/thingspeak/
- MQTT Broker: http://test.mosquitto.org/

### Về tính toán
- Heat Index Formula (NOAA): https://www.weather.gov/ama/heatindex
- Indoor Air Quality Standards: https://www.epa.gov/indoor-air-quality-iaq

---

**Hy vọng giải thích này giúp bạn hiểu rõ hơn về hệ thống! 🎓**