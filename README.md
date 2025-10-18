# 🌡️ HỆ THỐNG GIÁM SÁT MÔI TRƯỜNG THÔNG MINH

Dự án IoT mô phỏng hoàn toàn trên Wokwi - Không cần phần cứng

---

## 📁 CẤU TRÚC DỰ ÁN

```
iot-environmental-monitor/
├── src/
│   └── main.cpp          # Code chính
├── platformio.ini        # Cấu hình PlatformIO
├── wokwi.toml           # Cấu hình Wokwi  
├── diagram.json         # Sơ đồ mạch
└── README.md            # File này
```

---

## ⚡ HƯỚNG DẪN NHANH

### Bước 1: Cài đặt phần mềm

1. **Tải VS Code**: https://code.visualstudio.com/

2. **Cài Extension trong VS Code:**
   - Nhấn `Ctrl+Shift+X`
   - Tìm và cài **"PlatformIO IDE"**
   - Tìm và cài **"Wokwi Simulator"**
   - Restart VS Code

### Bước 2: Tạo dự án

1. Tạo thư mục `iot-environmental-monitor`

2. Tạo 4 file với nội dung như artifacts đã cung cấp:
   - `platformio.ini`
   - `wokwi.toml`
   - `diagram.json`
   - `src/main.cpp`

### Bước 3: Cấu hình ThingSpeak

1. Vào https://thingspeak.com/ → Đăng ký miễn phí

2. Tạo Channel mới:
   - **Channels** → **New Channel**
   - **Name**: Environmental Monitor
   - **Field 1**: Temperature
   - **Field 2**: Humidity
   - **Field 3**: Light Level
   - Click **Save Channel**

3. Lấy API Keys:
   - Vào tab **API Keys**
   - Copy **Channel ID** (ví dụ: 2785680)
   - Copy **Write API Key** (ví dụ: ABC123XYZ)

4. Cập nhật `src/main.cpp`:
   ```cpp
   // Dòng 11-17
   unsigned long channelID = 2785680;  // ← Thay số của bạn
   const char* writeAPIKey = "YOUR_WRITE_API_KEY";  // ← Thay key của bạn
   ```

### Bước 4: Chạy dự án

1. Mở Terminal trong VS Code (`Ctrl + ` `)

2. Build firmware:
   ```bash
   pio run
   ```

3. Chạy Wokwi:
   - Nhấn `Ctrl+Shift+P`
   - Gõ: `Wokwi: Start Simulator`
   - Nhấn Enter

4. Thử nghiệm:
   - Click vào DHT22 → Kéo thanh nhiệt độ/độ ẩm
   - Click vào LDR → Kéo thanh ánh sáng
   - Quan sát LCD, LED, Buzzer
   - Xem Serial Monitor

5. Kiểm tra ThingSpeak:
   - Đợi 20 giây
   - Refresh trang ThingSpeak
   - Xem biểu đồ

---

## 🎯 TÍNH NĂNG

✅ Đo nhiệt độ & độ ẩm (DHT22)  
✅ Đo cường độ ánh sáng (LDR)  
✅ Hiển thị trên LCD 20x4  
✅ Cảnh báo LED + Buzzer  
✅ Gửi dữ liệu lên ThingSpeak mỗi 20 giây  
✅ Kết nối WiFi tự động  

---

## 🐛 KHẮC PHỤC LỖI

### Lỗi: "Could not find firmware.bin"
```bash
pio run --target clean
pio run
```

### Lỗi: ThingSpeak trả về 0 hoặc 400
- Kiểm tra Channel ID và Write API Key
- Đảm bảo đã Save Channel trên ThingSpeak
- ThingSpeak yêu cầu tối thiểu 15 giây giữa các lần gửi

### LCD không hiển thị
- Trong Wokwi, LCD tự động hoạt động
- Kiểm tra code có `lcd.init()` và `lcd.backlight()`
- Build lại: `pio run`

---

## 📊 DEMO

### Trạng thái bình thường
```
LCD:
┌────────────────────┐
│ Nhiet do: 28.5C    │
│ Do am:    65.3%    │
│ Anh sang: 750      │
│ Trang thai: TOT    │
└────────────────────┘

💚 LED Xanh: Sáng
🔴 LED Đỏ: Tắt
🔇 Buzzer: Im lặng
```

### Trạng thái cảnh báo (nhiệt độ > 35°C)
```
LCD:
┌────────────────────────┐
│ Nhiet do: 38.2C      │
│ Do am:    65.3%      │
│ Anh sang: 750        │
│ Trang thai: CANH BAO │
└────────────────────────┘

💚 LED Xanh: Tắt
🔴 LED Đỏ: Sáng
🔊 Buzzer: Kêu
```

---

## 📝 CHECKLIST

- [ ] Đã cài VS Code + PlatformIO + Wokwi
- [ ] Đã tạo đủ 4 file
- [ ] Đã tạo ThingSpeak Channel
- [ ] Đã cập nhật Channel ID và API Key
- [ ] Chạy `pio run` thành công
- [ ] Wokwi Simulator chạy được
- [ ] LCD hiển thị dữ liệu
- [ ] ThingSpeak nhận được dữ liệu

---

## 📞 TÀI LIỆU THAM KHẢO

- PlatformIO: https://docs.platformio.org/
- Wokwi: https://docs.wokwi.com/
- ThingSpeak: https://www.mathworks.com/help/thingspeak/

---

**Made with ❤️ for IoT Students**