#include <Arduino.h>
#include <WiFi.h>
#include <DHT.h>
#include <LiquidCrystal_I2C.h>
#include <ThingSpeak.h>

// ===== CẤU HÌNH WIFI =====
const char* ssid = "Wokwi-GUEST";  // WiFi mặc định của Wokwi
const char* password = "";

// ===== CẤU HÌNH THINGSPEAK =====
// HƯỚNG DẪN LẤY THÔNG TIN:
// 1. Vào https://thingspeak.com/ → Đăng ký (miễn phí)
// 2. Tạo New Channel với 3 Fields: Temperature, Humidity, Light Level
// 3. Vào tab API Keys → Copy Channel ID và Write API Key
// 4. Paste vào 2 dòng dưới đây:

unsigned long channelID = 3123035;  // ← Thay số này bằng Channel ID của bạn
const char* writeAPIKey = "OK6322WQLR29O7ZI";  // ← Thay chuỗi này bằng Write API Key

WiFiClient client;

// ===== CẤU HÌNH PHẦN CỨNG =====
#define DHTPIN 15          // DHT22 data pin
#define DHTTYPE DHT22
#define LDR_PIN 34         // Analog pin cho LDR
#define LED_GREEN 25       // LED xanh (trạng thái tốt)
#define LED_RED 26         // LED đỏ (cảnh báo)
#define BUZZER_PIN 27      // Buzzer

DHT dht(DHTPIN, DHTTYPE);
LiquidCrystal_I2C lcd(0x27, 20, 4);  // LCD 20x4

// ===== BIẾN TOÀN CỤC =====
float temperature = 0;
float humidity = 0;
int lightLevel = 0;
unsigned long lastUpdate = 0;
const unsigned long UPDATE_INTERVAL = 20000;  // Gửi dữ liệu mỗi 20 giây

// ===== NGƯỠNG CẢNH BÁO =====
const float TEMP_MAX = 35.0;
const float TEMP_MIN = 15.0;
const float HUMID_MAX = 80.0;
const float HUMID_MIN = 30.0;
const int LIGHT_MIN = 500;  // Quá tối

// ===== HÀM KHỞI TẠO =====
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n=== HỆ THỐNG GIÁM SÁT MÔI TRƯỜNG ===");
  
  // Khởi tạo các chân
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LDR_PIN, INPUT);
  
  // Tắt cảnh báo ban đầu
  digitalWrite(LED_RED, LOW);
  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(LED_GREEN, HIGH);
  
  // Khởi tạo DHT
  dht.begin();
  
  // Khởi tạo LCD
  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("  IoT MONITOR");
  lcd.setCursor(0, 1);
  lcd.print("  Khoi tao...");
  
  // Kết nối WiFi
  Serial.print("Đang kết nối WiFi");
  lcd.setCursor(0, 2);
  lcd.print("Ket noi WiFi...");
  
  WiFi.begin(ssid, password);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nĐã kết nối WiFi!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
    lcd.setCursor(0, 2);
    lcd.print("WiFi: Ket noi OK  ");
  } else {
    Serial.println("\nLỗi kết nối WiFi!");
    lcd.setCursor(0, 2);
    lcd.print("WiFi: Loi!        ");
  }
  
  // Khởi tạo ThingSpeak
  ThingSpeak.begin(client);
  
  delay(2000);
  lcd.clear();
}

// ===== ĐỌC CẢM BIẾN =====
void readSensors() {
  // Đọc DHT22
  temperature = dht.readTemperature();
  humidity = dht.readHumidity();
  
  // Đọc LDR
  int ldrValue = analogRead(LDR_PIN);
  lightLevel = map(ldrValue, 0, 4095, 0, 1000);  // Chuyển sang thang 0-1000
  
  // Kiểm tra lỗi đọc DHT
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("Lỗi đọc DHT22!");
    temperature = 0;
    humidity = 0;
  }
}

// ===== KIỂM TRA VÀ CẢNH BÁO =====
bool checkWarnings() {
  bool warning = false;
  
  if (temperature > TEMP_MAX || temperature < TEMP_MIN) {
    warning = true;
    Serial.println("⚠ CẢNH BÁO: Nhiệt độ bất thường!");
  }
  
  if (humidity > HUMID_MAX || humidity < HUMID_MIN) {
    warning = true;
    Serial.println("⚠ CẢNH BÁO: Độ ẩm bất thường!");
  }
  
  if (lightLevel < LIGHT_MIN) {
    warning = true;
    Serial.println("⚠ CẢNH BÁO: Ánh sáng yếu!");
  }
  
  return warning;
}

// ===== HIỂN THỊ LCD =====
void updateLCD() {
  lcd.clear();
  
  // Dòng 1: Nhiệt độ
  lcd.setCursor(0, 0);
  lcd.print("Nhiet do: ");
  lcd.print(temperature, 1);
  lcd.print("C");
  
  // Dòng 2: Độ ẩm
  lcd.setCursor(0, 1);
  lcd.print("Do am:    ");
  lcd.print(humidity, 1);
  lcd.print("%");
  
  // Dòng 3: Ánh sáng
  lcd.setCursor(0, 2);
  lcd.print("Anh sang: ");
  lcd.print(lightLevel);
  
  // Dòng 4: Trạng thái
  lcd.setCursor(0, 3);
  if (checkWarnings()) {
    lcd.print("Trang thai: CANH BAO");
  } else {
    lcd.print("Trang thai: TOT     ");
  }
}

// ===== GỬI DỮ LIỆU LÊN THINGSPEAK =====
void sendToThingSpeak() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi chưa kết nối!");
    return;
  }
  
  Serial.println("\n--- Gửi dữ liệu lên ThingSpeak ---");
  
  ThingSpeak.setField(1, temperature);
  ThingSpeak.setField(2, humidity);
  ThingSpeak.setField(3, lightLevel);
  
  int status = ThingSpeak.writeFields(channelID, writeAPIKey);
  
  if (status == 200) {
    Serial.println("✓ Gửi dữ liệu thành công!");
  } else {
    Serial.print("✗ Lỗi gửi dữ liệu. Code: ");
    Serial.println(status);
  }
}

// ===== ĐIỀU KHIỂN LED VÀ BUZZER =====
void controlAlerts(bool warning) {
  if (warning) {
    digitalWrite(LED_GREEN, LOW);
    digitalWrite(LED_RED, HIGH);
    // Kêu buzzer ngắt quãng
    tone(BUZZER_PIN, 1000, 200);
  } else {
    digitalWrite(LED_GREEN, HIGH);
    digitalWrite(LED_RED, LOW);
    noTone(BUZZER_PIN);
  }
}

// ===== VÒNG LẶP CHÍNH =====
void loop() {
  // Đọc cảm biến
  readSensors();
  
  // In ra Serial Monitor
  Serial.println("\n===== DỮ LIỆU CẢM BIẾN =====");
  Serial.print("Nhiệt độ: ");
  Serial.print(temperature);
  Serial.println(" °C");
  Serial.print("Độ ẩm: ");
  Serial.print(humidity);
  Serial.println(" %");
  Serial.print("Ánh sáng: ");
  Serial.println(lightLevel);
  
  // Cập nhật LCD
  updateLCD();
  
  // Kiểm tra và cảnh báo
  bool hasWarning = checkWarnings();
  controlAlerts(hasWarning);
  
  // Gửi dữ liệu lên ThingSpeak (mỗi 20 giây)
  unsigned long currentTime = millis();
  if (currentTime - lastUpdate >= UPDATE_INTERVAL) {
    sendToThingSpeak();
    lastUpdate = currentTime;
  }
  
  delay(2000);  // Đọc cảm biến mỗi 2 giây
}