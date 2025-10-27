#include <Arduino.h>
#include <WiFi.h>
#include <DHT.h>
#include <LiquidCrystal_I2C.h>
#include <ThingSpeak.h>
#include <PubSubClient.h>

// ===== CẤU HÌNH WIFI =====
const char* ssid = "Wokwi-GUEST";
const char* password = "";

// ===== CẤU HÌNH THINGSPEAK =====
unsigned long channelID = 3123035;
const char* writeAPIKey = "OK6322WQLR29O7ZI";

// ===== CẤU HÌNH MQTT =====
const char* mqtt_server = "test.mosquitto.org";
const int mqtt_port = 1883;
const char* mqtt_topic_data = "iot/env/data";
const char* mqtt_topic_status = "iot/env/status";

WiFiClient espClient;
WiFiClient thingspeakClient;
PubSubClient mqtt(espClient);

// ===== CẤU HÌNH PHẦN CỨNG =====
#define DHTPIN 15
#define DHTTYPE DHT22
#define LDR_PIN 34
#define MQ2_PIN 35
#define LED_GREEN 25
#define LED_RED 26
#define BUZZER_PIN 27
#define RELAY_FAN 33

DHT dht(DHTPIN, DHTTYPE);

// ===== MÀN HÌNH LCD =====
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ===== BIẾN TOÀN CỤC =====
float temperature = 0;
float humidity = 0;
int lightLevel = 0;
float lightLux = 0;
int gasLevel = 0;
float gasPPM = 0;
float heatIndex = 0;
int comfortIndex = 0;

bool fanStatus = false;
bool systemAlert = false;

unsigned long lastThingSpeakUpdate = 0;
unsigned long lastMQTTUpdate = 0;
unsigned long lastSensorRead = 0;
unsigned long lastLCDUpdate = 0;

const unsigned long THINGSPEAK_INTERVAL = 20000;
const unsigned long MQTT_INTERVAL = 5000;
const unsigned long SENSOR_INTERVAL = 2000;
const unsigned long LCD_INTERVAL = 3000;

// ===== NGƯỠNG CẢNH BÁO =====
const float TEMP_MAX = 35.0;
const float TEMP_MIN = 15.0;
const float TEMP_FAN_ON = 30.0;
const float TEMP_FAN_OFF = 28.0;
const float HUMID_MAX = 80.0;
const float HUMID_MIN = 30.0;
const float LIGHT_MIN_LUX = 200.0;
const float GAS_THRESHOLD_PPM = 300.0;

int dataCount = 0;
int lcdPage = 0;

// ===== CHẾ ĐỘ TEST: Bật để dùng giá trị random, tắt để dùng cảm biến thật =====
#define TEST_MODE true  // true = random values, false = real sensors

// ===== KẾT NỐI MQTT =====
void connectMQTT() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  while (!mqtt.connected()) {
    Serial.print("Ket noi MQTT...");
    String clientId = "ESP32-" + String(random(0xffff), HEX);
    
    if (mqtt.connect(clientId.c_str())) {
      Serial.println("Thanh cong!");
      mqtt.publish(mqtt_topic_status, "truc_tuyen");
    } else {
      Serial.print("Loi: ");
      Serial.println(mqtt.state());
      delay(5000);
      return;
    }
  }
}

// ===== KHỞI TẠO =====
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n===========================================");
  Serial.println("  HE THONG GIAM SAT MOI TRUONG V5.1");
  if (TEST_MODE) {
    Serial.println("  CHE DO: THU NGHIEM (Gia tri ngau nhien)");
  } else {
    Serial.println("  CHE DO: THAT (Gia tri cam bien)");
  }
  Serial.println("===========================================");
  
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(RELAY_FAN, OUTPUT);
  pinMode(LDR_PIN, INPUT);
  pinMode(MQ2_PIN, INPUT);
  
  digitalWrite(LED_GREEN, LOW);
  digitalWrite(LED_RED, LOW);
  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(RELAY_FAN, LOW);
  
  dht.begin();
  
  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("IoT Monitor v5.1");
  lcd.setCursor(0, 1);
  if (TEST_MODE) {
    lcd.print("CHE DO THU");
  } else {
    lcd.print("CHE DO THAT");
  }
  
  delay(2000);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Ket noi WiFi...");
  Serial.print("WiFi: ");
  
  WiFi.begin(ssid, password);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println(" Thanh cong!");
    Serial.print("Dia chi IP: ");
    Serial.println(WiFi.localIP());
    lcd.setCursor(0, 1);
    lcd.print("Da ket noi!");
    digitalWrite(LED_GREEN, HIGH);
    delay(1000);
    digitalWrite(LED_GREEN, LOW);
  } else {
    Serial.println(" That bai!");
    lcd.setCursor(0, 1);
    lcd.print("Ket noi loi!");
  }
  
  ThingSpeak.begin(thingspeakClient);
  mqtt.setServer(mqtt_server, mqtt_port);
  connectMQTT();
  
  delay(2000);
  lcd.clear();
  
  Serial.println("\n✓ He thong san sang!");
  Serial.println("💡 Quat tu dong: BAT khi T >= 30°C, TAT khi T <= 28°C\n");
}

// ===== ĐỌC CẢM BIẾN VỚI TÙY CHỌN TEST MODE =====
void readSensors() {
  // Đọc DHT22 (luôn dùng giá trị thật)
  temperature = dht.readTemperature();
  humidity = dht.readHumidity();
  
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("⚠ Loi DHT22!");
    temperature = 25.0;
    humidity = 60.0;
  }
  
  if (TEST_MODE) {
    // ===== CHẾ ĐỘ TEST: Giá trị ngẫu nhiên =====
    lightLux = random(0, 1001);
    lightLevel = map(lightLux, 0, 1000, 4095, 0);
    
    gasPPM = random(0, 501);
    gasLevel = map(gasPPM, 0, 500, 0, 2048);
    
  } else {
    // ===== CHẾ ĐỘ THẬT: Đọc từ cảm biến =====
    lightLevel = analogRead(LDR_PIN);
    int invertedLight = 4095 - lightLevel;
    lightLux = map(invertedLight, 0, 4095, 0, 1000);
    lightLux = constrain(lightLux, 0, 1000);
    
    gasLevel = analogRead(MQ2_PIN);
    gasPPM = map(gasLevel, 0, 4095, 0, 1000);
    gasPPM = constrain(gasPPM, 0, 1000);
  }
  
  // Tính Heat Index
  float c1 = -8.78469475556;
  float c2 = 1.61139411;
  float c3 = 2.33854883889;
  float c4 = -0.14611605;
  float c5 = -0.012308094;
  float c6 = -0.0164248277778;
  float c7 = 0.002211732;
  float c8 = 0.00072546;
  float c9 = -0.000003582;
  
  heatIndex = c1 + c2*temperature + c3*humidity + 
              c4*temperature*humidity + c5*temperature*temperature + 
              c6*humidity*humidity + c7*temperature*temperature*humidity + 
              c8*temperature*humidity*humidity + 
              c9*temperature*temperature*humidity*humidity;
  
  // Tính Comfort Index
  float tempScore = max(0.0f, 100.0f - abs(24.0f - temperature) * 5);
  float humidScore = max(0.0f, 100.0f - abs(60.0f - humidity) * 2);
  float lightScore = min(100.0f, (lightLux / 10.0f));
  float gasScore = max(0.0f, 100.0f - (gasPPM / 10.0f));
  
  comfortIndex = (tempScore + humidScore + lightScore + gasScore) / 4;
  
  dataCount++;
}

// ===== KIỂM TRA CẢNH BÁO =====
bool checkAlerts() {
  bool alert = false;
  
  if (temperature > TEMP_MAX || temperature < TEMP_MIN) {
    alert = true;
  }
  
  if (humidity > HUMID_MAX || humidity < HUMID_MIN) {
    alert = true;
  }
  
  if (lightLux < LIGHT_MIN_LUX) {
    alert = true;
  }
  
  if (gasPPM > GAS_THRESHOLD_PPM) {
    alert = true;
  }
  
  systemAlert = alert;
  return alert;
}

// ===== ĐIỀU KHIỂN QUẠT TỰ ĐỘNG =====
void autoFanControl() {
  if (temperature >= TEMP_FAN_ON && !fanStatus) {
    fanStatus = true;
    digitalWrite(RELAY_FAN, HIGH);
    Serial.println("🌀 TU DONG: Bat quat (T >= 30°C)");
    mqtt.publish(mqtt_topic_status, "quat_bat_tu_dong");
  }
  else if (temperature <= TEMP_FAN_OFF && fanStatus) {
    fanStatus = false;
    digitalWrite(RELAY_FAN, LOW);
    Serial.println("🌀 TU DONG: Tat quat (T <= 28°C)");
    mqtt.publish(mqtt_topic_status, "quat_tat_tu_dong");
  }
}

// ===== ĐIỀU KHIỂN LED & BUZZER =====
void controlIndicators() {
  if (systemAlert) {
    digitalWrite(LED_GREEN, LOW);
    digitalWrite(LED_RED, HIGH);
    tone(BUZZER_PIN, 1000, 200);
  } else {
    digitalWrite(LED_GREEN, HIGH);
    digitalWrite(LED_RED, LOW);
    noTone(BUZZER_PIN);
  }
}

// ===== CẬP NHẬT LCD =====
void updateLCD() {
  static unsigned long lastPageChange = 0;
  
  if (millis() - lastPageChange > LCD_INTERVAL) {
    lcdPage = (lcdPage + 1) % 5;
    lastPageChange = millis();
    lcd.clear();
  }
  
  if (lcdPage == 0) {
    // Trang 1: Nhiệt độ & Độ ẩm
    lcd.setCursor(0, 0);
    lcd.print("T:");
    lcd.print(temperature, 1);
    lcd.write(223);
    lcd.print("C ");
    
    if (temperature > TEMP_MAX) {
      lcd.print("NONG!");
    } else if (temperature < TEMP_MIN) {
      lcd.print("LANH");
    } else {
      lcd.print("TOT ");
    }
    
    lcd.setCursor(0, 1);
    lcd.print("H:");
    lcd.print(humidity, 1);
    lcd.print("% ");
    
    if (humidity > HUMID_MAX) {
      lcd.print("CAO ");
    } else if (humidity < HUMID_MIN) {
      lcd.print("THAP");
    } else {
      lcd.print("TOT ");
    }
    
  } else if (lcdPage == 1) {
    // Trang 2: Ánh sáng
    lcd.setCursor(0, 0);
    lcd.print("Sang:");
    lcd.print((int)lightLux);
    lcd.print(" Lux  ");
    
    lcd.setCursor(0, 1);
    if (lightLux < LIGHT_MIN_LUX) {
      lcd.print("Trang thai: TOI");
    } else {
      lcd.print("Trang thai: TOT");
    }
    
  } else if (lcdPage == 2) {
    // Trang 3: Khí gas
    lcd.setCursor(0, 0);
    lcd.print("Khi:");
    lcd.print((int)gasPPM);
    lcd.print(" PPM   ");
    
    lcd.setCursor(0, 1);
    if (gasPPM > GAS_THRESHOLD_PPM) {
      lcd.print("NGUY HIEM!!!  ");
    } else {
      lcd.print("Trang thai: TOT");
    }
    
  } else if (lcdPage == 3) {
    // Trang 4: Chỉ số
    lcd.setCursor(0, 0);
    lcd.print("Thoai mai:");
    lcd.print(comfortIndex);
    lcd.print("/100");
    
    lcd.setCursor(0, 1);
    lcd.print("Chi so:");
    lcd.print(heatIndex, 1);
    lcd.write(223);
    lcd.print("C  ");
    
  } else {
    // Trang 5: Trạng thái
    lcd.setCursor(0, 0);
    if (systemAlert) {
      lcd.print("! CANH BAO !   ");
    } else {
      lcd.print("He thong TOT   ");
    }
    
    lcd.setCursor(0, 1);
    lcd.print("Quat:");
    lcd.print(fanStatus ? "BAT" : "TAT");
    lcd.print(" #");
    lcd.print(dataCount);
    lcd.print("    ");
  }
}

// ===== GỬI THINGSPEAK =====
void sendThingSpeak() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  Serial.println("\n→ Dang gui den ThingSpeak...");
  
  ThingSpeak.setField(1, temperature);
  ThingSpeak.setField(2, humidity);
  ThingSpeak.setField(3, lightLux);
  ThingSpeak.setField(4, gasPPM);
  ThingSpeak.setField(5, fanStatus ? 1 : 0);
  ThingSpeak.setField(6, heatIndex);
  ThingSpeak.setField(7, comfortIndex);
  ThingSpeak.setField(8, systemAlert ? 1 : 0);
  
  int status = ThingSpeak.writeFields(channelID, writeAPIKey);
  
  if (status == 200) {
    Serial.println("✓ ThingSpeak: Thanh cong");
  } else {
    Serial.print("✗ Loi ThingSpeak: ");
    Serial.println(status);
  }
}

// ===== GỬI MQTT =====
void sendMQTT() {
  if (!mqtt.connected()) {
    connectMQTT();
    return;
  }
  
  String payload = "{";
  payload += "\"temp\":" + String(temperature, 1) + ",";
  payload += "\"humid\":" + String(humidity, 1) + ",";
  payload += "\"light_lux\":" + String(lightLux, 1) + ",";
  payload += "\"gas_ppm\":" + String(gasPPM, 1) + ",";
  payload += "\"heat_index\":" + String(heatIndex, 1) + ",";
  payload += "\"comfort\":" + String(comfortIndex) + ",";
  payload += "\"fan\":" + String(fanStatus ? "true" : "false") + ",";
  payload += "\"alert\":" + String(systemAlert ? "true" : "false");
  payload += "}";
  
  mqtt.publish(mqtt_topic_data, payload.c_str());
  Serial.println("✓ MQTT: " + payload);
}

// ===== IN SERIAL =====
void printSerial() {
  Serial.println("\n========== DU LIEU CAM BIEN ==========");
  Serial.print("Nhiet do: ");
  Serial.print(temperature, 1);
  Serial.print(" °C ");
  Serial.println(temperature > TEMP_MAX ? "[NONG]" : temperature < TEMP_MIN ? "[LANH]" : "[TOT]");
  
  Serial.print("Do am   : ");
  Serial.print(humidity, 1);
  Serial.print(" % ");
  Serial.println(humidity > HUMID_MAX ? "[CAO]" : humidity < HUMID_MIN ? "[THAP]" : "[TOT]");
  
  Serial.print("Anh sang: ");
  Serial.print(lightLux, 1);
  Serial.print(" Lux");
  if (TEST_MODE) Serial.print(" [NGAU NHIEN]");
  else {
    Serial.print(" (Tho:");
    Serial.print(lightLevel);
    Serial.print(")");
  }
  Serial.println(lightLux < LIGHT_MIN_LUX ? " [TOI]" : " [SANG]");
  
  Serial.print("Khi gas : ");
  Serial.print(gasPPM, 1);
  Serial.print(" PPM");
  if (TEST_MODE) Serial.print(" [NGAU NHIEN]");
  else {
    Serial.print(" (Tho:");
    Serial.print(gasLevel);
    Serial.print(")");
  }
  Serial.println(gasPPM > GAS_THRESHOLD_PPM ? " [NGUY HIEM]" : " [AN TOAN]");
  
  Serial.print("Chi so nhiet: ");
  Serial.print(heatIndex, 1);
  Serial.println(" °C");
  
  Serial.print("Thoai mai   : ");
  Serial.print(comfortIndex);
  Serial.println("/100");
  
  Serial.println("\n========== TRANG THAI ==========");
  Serial.print("Quat    : ");
  Serial.println(fanStatus ? "BAT" : "TAT");
  Serial.print("Canh bao: ");
  Serial.println(systemAlert ? "CO" : "KHONG");
  Serial.print("Du lieu #: ");
  Serial.println(dataCount);
  Serial.println("====================================\n");
}

// ===== VÒNG LẶP CHÍNH =====
void loop() {
  unsigned long currentTime = millis();
  
  if (mqtt.connected()) {
    mqtt.loop();
  } else {
    connectMQTT();
  }
  
  if (currentTime - lastSensorRead >= SENSOR_INTERVAL) {
    readSensors();
    checkAlerts();
    autoFanControl();
    controlIndicators();
    printSerial();
    lastSensorRead = currentTime;
  }
  
  if (currentTime - lastLCDUpdate >= LCD_INTERVAL) {
    updateLCD();
    lastLCDUpdate = currentTime;
  }
  
  if (currentTime - lastThingSpeakUpdate >= THINGSPEAK_INTERVAL) {
    sendThingSpeak();
    lastThingSpeakUpdate = currentTime;
  }
  
  if (currentTime - lastMQTTUpdate >= MQTT_INTERVAL) {
    sendMQTT();
    lastMQTTUpdate = currentTime;
  }
  
  delay(100);
}