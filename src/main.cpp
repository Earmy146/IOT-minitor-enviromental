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
const char* mqtt_topic_control = "iot/env/control";
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
#define LED_BLUE 14
#define BUZZER_PIN 27
#define RELAY_FAN 33
#define RELAY_LIGHT 32
#define BUTTON_MODE 13

DHT dht(DHTPIN, DHTTYPE);
LiquidCrystal_I2C lcd(0x27, 20, 4);

// ===== BIẾN TOÀN CỤC =====
float temperature = 0;
float humidity = 0;
int lightLevel = 0;
int gasLevel = 0;
float heatIndex = 0;
int comfortIndex = 0;

bool fanStatus = false;
bool lightRelayStatus = false;
bool autoMode = true;
bool systemAlert = false;

unsigned long lastThingSpeakUpdate = 0;
unsigned long lastMQTTUpdate = 0;
unsigned long lastSensorRead = 0;
unsigned long lastLCDUpdate = 0;

const unsigned long THINGSPEAK_INTERVAL = 20000;
const unsigned long MQTT_INTERVAL = 5000;
const unsigned long SENSOR_INTERVAL = 2000;
const unsigned long LCD_INTERVAL = 1000;

// ===== NGƯỠNG CẢNH BÁO =====
const float TEMP_MAX = 35.0;
const float TEMP_MIN = 15.0;
const float HUMID_MAX = 80.0;
const float HUMID_MIN = 30.0;
const int LIGHT_MIN = 300;
const int GAS_THRESHOLD = 400;

// ===== THỐNG KÊ =====
int dataCount = 0;
float tempSum = 0;
float humidSum = 0;

// ===== MQTT CALLBACK =====
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  Serial.print("MQTT nhận: ");
  Serial.print(topic);
  Serial.print(" -> ");
  Serial.println(message);
  
  if (String(topic) == mqtt_topic_control) {
    if (message == "FAN_ON") {
      fanStatus = true;
      digitalWrite(RELAY_FAN, HIGH);
      autoMode = false;
    }
    else if (message == "FAN_OFF") {
      fanStatus = false;
      digitalWrite(RELAY_FAN, LOW);
      autoMode = false;
    }
    else if (message == "LIGHT_ON") {
      lightRelayStatus = true;
      digitalWrite(RELAY_LIGHT, HIGH);
      autoMode = false;
    }
    else if (message == "LIGHT_OFF") {
      lightRelayStatus = false;
      digitalWrite(RELAY_LIGHT, LOW);
      autoMode = false;
    }
    else if (message == "AUTO_MODE") {
      autoMode = true;
    }
    else if (message == "MANUAL_MODE") {
      autoMode = false;
    }
    else if (message == "RESET_STATS") {
      dataCount = 0;
      tempSum = 0;
      humidSum = 0;
    }
  }
}

// ===== KẾT NỐI MQTT =====
void connectMQTT() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  while (!mqtt.connected()) {
    Serial.print("Kết nối MQTT...");
    String clientId = "ESP32-" + String(random(0xffff), HEX);
    
    if (mqtt.connect(clientId.c_str())) {
      Serial.println("OK!");
      mqtt.subscribe(mqtt_topic_control);
      mqtt.publish(mqtt_topic_status, "online");
    } else {
      Serial.print("Lỗi: ");
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
  
  Serial.println("\n================================================");
  Serial.println("  HE THONG GIAM SAT MOI TRUONG V2.0");
  Serial.println("  Advanced IoT Environmental Monitor");
  Serial.println("================================================");
  
  // Khởi tạo GPIO
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  pinMode(LED_BLUE, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(RELAY_FAN, OUTPUT);
  pinMode(RELAY_LIGHT, OUTPUT);
  pinMode(BUTTON_MODE, INPUT_PULLUP);
  pinMode(LDR_PIN, INPUT);
  pinMode(MQ2_PIN, INPUT);
  
  digitalWrite(LED_GREEN, LOW);
  digitalWrite(LED_RED, LOW);
  digitalWrite(LED_BLUE, HIGH);
  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(RELAY_FAN, LOW);
  digitalWrite(RELAY_LIGHT, LOW);
  
  // Khởi tạo cảm biến
  dht.begin();
  
  // Khởi tạo LCD
  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(3, 0);
  lcd.print("SMART IoT V2.0");
  lcd.setCursor(2, 1);
  lcd.print("Environmental");
  lcd.setCursor(4, 2);
  lcd.print("Monitor Pro");
  lcd.setCursor(3, 3);
  lcd.print("Initializing...");
  
  delay(2000);
  
  // Kết nối WiFi
  lcd.clear();
  lcd.setCursor(0, 1);
  lcd.print("Connecting WiFi...");
  Serial.print("WiFi: ");
  
  WiFi.begin(ssid, password);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println(" OK!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
    lcd.setCursor(0, 2);
    lcd.print("WiFi: Connected");
    digitalWrite(LED_BLUE, LOW);
    digitalWrite(LED_GREEN, HIGH);
  } else {
    Serial.println(" FAIL!");
    lcd.setCursor(0, 2);
    lcd.print("WiFi: Failed!");
  }
  
  // Khởi tạo ThingSpeak
  ThingSpeak.begin(thingspeakClient);
  Serial.println("ThingSpeak: Ready");
  
  // Khởi tạo MQTT
  mqtt.setServer(mqtt_server, mqtt_port);
  mqtt.setCallback(mqttCallback);
  connectMQTT();
  
  delay(2000);
  lcd.clear();
  
  Serial.println("\n✓ Hệ thống sẵn sàng!\n");
}

// ===== ĐỌC CẢM BIẾN =====
void readSensors() {
  temperature = dht.readTemperature();
  humidity = dht.readHumidity();
  
  int ldrValue = analogRead(LDR_PIN);
  lightLevel = map(ldrValue, 0, 4095, 0, 1000);
  
  int mq2Value = analogRead(MQ2_PIN);
  gasLevel = map(mq2Value, 0, 4095, 0, 1000);
  
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("⚠ DHT22 Error!");
    temperature = 0;
    humidity = 0;
  } else {
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
    
    // Tính Comfort Index (0-100)
    float tempScore = max(0.0f, 100.0f - abs(24.0f - temperature) * 5);
    float humidScore = max(0.0f, 100.0f - abs(60.0f - humidity) * 2);
    float lightScore = min(100.0f, (lightLevel / 10.0f));
    float gasScore = max(0.0f, 100.0f - (gasLevel / 10.0f));
    
    comfortIndex = (tempScore + humidScore + lightScore + gasScore) / 4;
    
    // Cập nhật thống kê
    dataCount++;
    tempSum += temperature;
    humidSum += humidity;
  }
}

// ===== KIỂM TRA CẢNH BÁO =====
bool checkAlerts() {
  bool alert = false;
  
  if (temperature > TEMP_MAX || temperature < TEMP_MIN) {
    alert = true;
    Serial.println("🔥 ALERT: Temperature out of range!");
  }
  
  if (humidity > HUMID_MAX || humidity < HUMID_MIN) {
    alert = true;
    Serial.println("💧 ALERT: Humidity out of range!");
  }
  
  if (lightLevel < LIGHT_MIN) {
    alert = true;
    Serial.println("💡 ALERT: Low light level!");
  }
  
  if (gasLevel > GAS_THRESHOLD) {
    alert = true;
    Serial.println("☠️  ALERT: Gas detected!");
  }
  
  systemAlert = alert;
  return alert;
}

// ===== ĐIỀU KHIỂN TỰ ĐỘNG =====
void autoControl() {
  if (!autoMode) return;
  
  // Tự động bật quạt khi nhiệt độ > 30°C
  if (temperature > 30.0 && !fanStatus) {
    fanStatus = true;
    digitalWrite(RELAY_FAN, HIGH);
    Serial.println("🌀 Auto: Fan ON");
    mqtt.publish(mqtt_topic_status, "fan_auto_on");
  }
  else if (temperature <= 28.0 && fanStatus) {
    fanStatus = false;
    digitalWrite(RELAY_FAN, LOW);
    Serial.println("🌀 Auto: Fan OFF");
    mqtt.publish(mqtt_topic_status, "fan_auto_off");
  }
  
  // Tự động bật đèn khi ánh sáng < 300
  if (lightLevel < 300 && !lightRelayStatus) {
    lightRelayStatus = true;
    digitalWrite(RELAY_LIGHT, HIGH);
    Serial.println("💡 Auto: Light ON");
    mqtt.publish(mqtt_topic_status, "light_auto_on");
  }
  else if (lightLevel >= 500 && lightRelayStatus) {
    lightRelayStatus = false;
    digitalWrite(RELAY_LIGHT, LOW);
    Serial.println("💡 Auto: Light OFF");
    mqtt.publish(mqtt_topic_status, "light_auto_off");
  }
}

// ===== ĐIỀU KHIỂN LED & BUZZER =====
void controlIndicators() {
  if (systemAlert) {
    digitalWrite(LED_GREEN, LOW);
    digitalWrite(LED_RED, HIGH);
    tone(BUZZER_PIN, 1000, 200);
  } else if (comfortIndex < 60) {
    digitalWrite(LED_GREEN, LOW);
    digitalWrite(LED_RED, HIGH);
    noTone(BUZZER_PIN);
  } else {
    digitalWrite(LED_GREEN, HIGH);
    digitalWrite(LED_RED, LOW);
    noTone(BUZZER_PIN);
  }
}

// ===== CẬP NHẬT LCD =====
void updateLCD() {
  static int page = 0;
  static unsigned long lastPageChange = 0;
  
  // Tự động chuyển trang mỗi 5 giây
  if (millis() - lastPageChange > 5000) {
    page = (page + 1) % 3;
    lastPageChange = millis();
    lcd.clear();
  }
  
  switch(page) {
    case 0: // Trang 1: Dữ liệu cơ bản
      lcd.setCursor(0, 0);
      lcd.print("T:");
      lcd.print(temperature, 1);
      lcd.print("C H:");
      lcd.print(humidity, 0);
      lcd.print("%");
      
      lcd.setCursor(0, 1);
      lcd.print("L:");
      lcd.print(lightLevel);
      lcd.print(" G:");
      lcd.print(gasLevel);
      
      lcd.setCursor(0, 2);
      lcd.print("HI:");
      lcd.print(heatIndex, 1);
      lcd.print(" CI:");
      lcd.print(comfortIndex);
      
      lcd.setCursor(0, 3);
      if (systemAlert) {
        lcd.print("STATUS: ALERT!    ");
      } else if (comfortIndex >= 80) {
        lcd.print("STATUS: EXCELLENT ");
      } else if (comfortIndex >= 60) {
        lcd.print("STATUS: GOOD      ");
      } else {
        lcd.print("STATUS: POOR      ");
      }
      break;
      
    case 1: // Trang 2: Thiết bị
      lcd.setCursor(0, 0);
      lcd.print("=== DEVICES ===");
      
      lcd.setCursor(0, 1);
      lcd.print("Fan:   ");
      lcd.print(fanStatus ? "ON " : "OFF");
      lcd.print(autoMode ? " (Auto)" : " (Man)");
      
      lcd.setCursor(0, 2);
      lcd.print("Light: ");
      lcd.print(lightRelayStatus ? "ON " : "OFF");
      lcd.print(autoMode ? " (Auto)" : " (Man)");
      
      lcd.setCursor(0, 3);
      lcd.print("Mode: ");
      lcd.print(autoMode ? "AUTOMATIC  " : "MANUAL     ");
      break;
      
    case 2: // Trang 3: Thống kê
      lcd.setCursor(0, 0);
      lcd.print("=== STATISTICS ===");
      
      lcd.setCursor(0, 1);
      lcd.print("Data Count: ");
      lcd.print(dataCount);
      
      lcd.setCursor(0, 2);
      if (dataCount > 0) {
        lcd.print("Avg T: ");
        lcd.print(tempSum/dataCount, 1);
        lcd.print("C");
      }
      
      lcd.setCursor(0, 3);
      if (dataCount > 0) {
        lcd.print("Avg H: ");
        lcd.print(humidSum/dataCount, 1);
        lcd.print("%");
      }
      break;
  }
}

// ===== GỬI THINGSPEAK =====
void sendThingSpeak() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  Serial.println("\n→ Sending to ThingSpeak...");
  
  ThingSpeak.setField(1, temperature);
  ThingSpeak.setField(2, humidity);
  ThingSpeak.setField(3, lightLevel);
  ThingSpeak.setField(4, gasLevel);
  ThingSpeak.setField(5, fanStatus ? 1 : 0);
  ThingSpeak.setField(6, lightRelayStatus ? 1 : 0);
  ThingSpeak.setField(7, heatIndex);
  ThingSpeak.setField(8, comfortIndex);
  
  int status = ThingSpeak.writeFields(channelID, writeAPIKey);
  
  if (status == 200) {
    Serial.println("✓ ThingSpeak: Success");
  } else {
    Serial.print("✗ ThingSpeak Error: ");
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
  payload += "\"light\":" + String(lightLevel) + ",";
  payload += "\"gas\":" + String(gasLevel) + ",";
  payload += "\"fan\":" + String(fanStatus ? "true" : "false") + ",";
  payload += "\"light_relay\":" + String(lightRelayStatus ? "true" : "false") + ",";
  payload += "\"heat_index\":" + String(heatIndex, 1) + ",";
  payload += "\"comfort\":" + String(comfortIndex) + ",";
  payload += "\"mode\":\"" + String(autoMode ? "auto" : "manual") + "\"";
  payload += "}";
  
  mqtt.publish(mqtt_topic_data, payload.c_str());
  Serial.println("✓ MQTT: " + payload);
}

// ===== IN SERIAL =====
void printSerial() {
  Serial.println("\n========== DU LIEU CAM BIEN ==========");
  Serial.print("Nhiet do      : ");
  Serial.print(temperature, 1);
  Serial.println(" *C");
  
  Serial.print("Do am         : ");
  Serial.print(humidity, 1);
  Serial.println(" %");
  
  Serial.print("Anh sang      : ");
  Serial.print(lightLevel);
  Serial.println(" lux");
  
  Serial.print("Khi gas       : ");
  Serial.print(gasLevel);
  Serial.println(" ppm");
  
  Serial.print("Chi so nhiet  : ");
  Serial.print(heatIndex, 1);
  Serial.println(" *C");
  
  Serial.print("Chi so thoai mai: ");
  Serial.print(comfortIndex);
  Serial.println("/100");
  
  Serial.println("\n========== THIET BI ==========");
  Serial.print("Quat          : ");
  Serial.println(fanStatus ? "BAT" : "TAT");
  
  Serial.print("Den           : ");
  Serial.println(lightRelayStatus ? "BAT" : "TAT");
  
  Serial.print("Che do        : ");
  Serial.println(autoMode ? "TU DONG" : "THU CONG");
  
  Serial.println("======================================\n");
}

// ===== VÒNG LẶP CHÍNH =====
void loop() {
  unsigned long currentTime = millis();
  
  // Duy trì kết nối MQTT
  if (mqtt.connected()) {
    mqtt.loop();
  } else {
    connectMQTT();
  }
  
  // Kiểm tra nút chuyển chế độ
  static bool lastButtonState = HIGH;
  bool buttonState = digitalRead(BUTTON_MODE);
  if (buttonState == LOW && lastButtonState == HIGH) {
    delay(50); // Debounce
    autoMode = !autoMode;
    Serial.println(autoMode ? "→ AUTO MODE" : "→ MANUAL MODE");
    mqtt.publish(mqtt_topic_status, autoMode ? "auto_mode" : "manual_mode");
  }
  lastButtonState = buttonState;
  
  // Đọc cảm biến
  if (currentTime - lastSensorRead >= SENSOR_INTERVAL) {
    readSensors();
    checkAlerts();
    autoControl();
    controlIndicators();
    printSerial();
    lastSensorRead = currentTime;
  }
  
  // Cập nhật LCD
  if (currentTime - lastLCDUpdate >= LCD_INTERVAL) {
    updateLCD();
    lastLCDUpdate = currentTime;
  }
  
  // Gửi ThingSpeak
  if (currentTime - lastThingSpeakUpdate >= THINGSPEAK_INTERVAL) {
    sendThingSpeak();
    lastThingSpeakUpdate = currentTime;
  }
  
  // Gửi MQTT
  if (currentTime - lastMQTTUpdate >= MQTT_INTERVAL) {
    sendMQTT();
    lastMQTTUpdate = currentTime;
  }
  
  delay(100);
}