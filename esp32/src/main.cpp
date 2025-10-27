#include <Arduino.h>
#include <WiFi.h>
#include <DHT.h>
#include <LiquidCrystal_I2C.h>
#include <ThingSpeak.h>
#include <PubSubClient.h>

// ===== CẤU HÌNH WIFI =====
const char* tenWifi = "Wokwi-GUEST";
const char* matKhau = "";

// ===== CẤU HÌNH THINGSPEAK =====
unsigned long maKenh = 3123035;
const char* khaiGhi = "OK6322WQLR29O7ZI";

// ===== CẤU HÌNH MQTT =====
const char* maychu_mqtt = "test.mosquitto.org";
const int cong_mqtt = 1883;
const char* chuDe_duLieu = "iot/moitruong/dulieu";
const char* chuDe_trangThai = "iot/moitruong/trangthai";

WiFiClient khachEsp;
WiFiClient khachThingSpeak;
PubSubClient mqtt(khachEsp);

// ===== CẤU HÌNH PHẦN CỨNG =====
#define CHAN_DHT 15
#define KIEU_DHT DHT22
#define CHAN_LDR 34
#define CHAN_MQ2 35
#define DEN_XANH 25
#define DEN_DO 26
#define COI_BAO 27
#define RELE_QUAT 33

DHT dht(CHAN_DHT, KIEU_DHT);

// ===== MÀN HÌNH LCD =====
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ===== BIẾN TOÀN CỤC =====
float nhietDo = 0;
float doAm = 0;
int capDoAnhSang = 0;
float anhSangLux = 0;
int capDoKhi = 0;
float khiPPM = 0;
float chiSoNhiet = 0;
int chiSoThoaiMai = 0;

bool trangThaiQuat = false;
bool canhBaoHeThong = false;

unsigned long lanCapNhatThingSpeakCuoi = 0;
unsigned long lanCapNhatMQTTCuoi = 0;
unsigned long lanDocCamBienCuoi = 0;
unsigned long lanCapNhatLCDCuoi = 0;

const unsigned long KHOANG_THINGSPEAK = 20000;
const unsigned long KHOANG_MQTT = 5000;
const unsigned long KHOANG_CAM_BIEN = 2000;
const unsigned long KHOANG_LCD = 3000;

// ===== NGƯỠNG CẢNH BÁO =====
const float NHIET_TOI_DA = 35.0;
const float NHIET_TOI_THIEU = 15.0;
const float NHIET_BAT_QUAT = 30.0;   // Bật quạt khi >= 30°C
const float NHIET_TAT_QUAT = 28.0;   // Tắt quạt khi <= 28°C
const float AM_TOI_DA = 80.0;
const float AM_TOI_THIEU = 30.0;
const float SANG_TOI_THIEU_LUX = 200.0;
const float NGUONG_KHI_PPM = 300.0;

int soDuLieu = 0;
int trangLCD = 0;

// ===== CHẾ ĐỘ THỬ NGHIỆM: Bật để dùng giá trị ngẫu nhiên, tắt để dùng cảm biến thật =====
#define CHE_DO_THU true  // true = giá trị ngẫu nhiên, false = cảm biến thật

// ===== KẾT NỐI MQTT =====
void ketNoiMQTT() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  while (!mqtt.connected()) {
    Serial.print("Ket noi MQTT...");
    String maKhach = "ESP32-" + String(random(0xffff), HEX);
    
    if (mqtt.connect(maKhach.c_str())) {
      Serial.println("Thanh cong!");
      mqtt.publish(chuDe_trangThai, "truc tuyen");
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
  if (CHE_DO_THU) {
    Serial.println("  CHE DO: THU NGHIEM (Gia tri ngau nhien)");
  } else {
    Serial.println("  CHE DO: THAT (Gia tri cam bien)");
  }
  Serial.println("===========================================");
  
  pinMode(DEN_XANH, OUTPUT);
  pinMode(DEN_DO, OUTPUT);
  pinMode(COI_BAO, OUTPUT);
  pinMode(RELE_QUAT, OUTPUT);
  pinMode(CHAN_LDR, INPUT);
  pinMode(CHAN_MQ2, INPUT);
  
  digitalWrite(DEN_XANH, LOW);
  digitalWrite(DEN_DO, LOW);
  digitalWrite(COI_BAO, LOW);
  digitalWrite(RELE_QUAT, LOW);
  
  dht.begin();
  
  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("IoT Giam Sat v5");
  lcd.setCursor(0, 1);
  if (CHE_DO_THU) {
    lcd.print("CHE DO THU");
  } else {
    lcd.print("CHE DO THAT");
  }
  
  delay(2000);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Ket noi WiFi...");
  Serial.print("WiFi: ");
  
  WiFi.begin(tenWifi, matKhau);
  int soLan = 0;
  while (WiFi.status() != WL_CONNECTED && soLan < 30) {
    delay(500);
    Serial.print(".");
    soLan++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println(" Thanh cong!");
    Serial.print("Dia chi IP: ");
    Serial.println(WiFi.localIP());
    lcd.setCursor(0, 1);
    lcd.print("Da ket noi!");
    digitalWrite(DEN_XANH, HIGH);
    delay(1000);
    digitalWrite(DEN_XANH, LOW);
  } else {
    Serial.println(" That bai!");
    lcd.setCursor(0, 1);
    lcd.print("Ket noi loi!");
  }
  
  ThingSpeak.begin(khachThingSpeak);
  mqtt.setServer(maychu_mqtt, cong_mqtt);
  ketNoiMQTT();
  
  delay(2000);
  lcd.clear();
  
  Serial.println("\n✓ He thong san sang hoat dong!");
  Serial.println("💡 Quat tu dong: BAT khi >= 30°C, TAT khi <= 28°C\n");
}

// ===== ĐỌC CẢM BIẾN VỚI TÙY CHỌN CHẾ ĐỘ THỬ NGHIỆM =====
void docCamBien() {
  // Đọc DHT22 (luôn dùng giá trị thật)
  nhietDo = dht.readTemperature();
  doAm = dht.readHumidity();
  
  if (isnan(nhietDo) || isnan(doAm)) {
    Serial.println("⚠ Loi DHT22!");
    nhietDo = 25.0;  // Giá trị mặc định
    doAm = 60.0;
  }
  
  if (CHE_DO_THU) {
    // ===== CHẾ ĐỘ THỬ NGHIỆM: Giá trị ngẫu nhiên để kiểm tra =====
    
    // LDR: Giả lập ánh sáng từ 0-1000 Lux
    anhSangLux = random(0, 1001);
    capDoAnhSang = map(anhSangLux, 0, 1000, 4095, 0);
    
    // MQ2: Giả lập khí gas từ 0-500 PPM
    khiPPM = random(0, 501);
    capDoKhi = map(khiPPM, 0, 500, 0, 2048);
    
  } else {
    // ===== CHẾ ĐỘ THẬT: Đọc từ cảm biến analog =====
    
    // ĐỌC LDR
    capDoAnhSang = analogRead(CHAN_LDR);
    // Wokwi LDR: Giá trị CAO = TỐI, THẤP = SÁNG
    // Đảo ngược để có logic đúng
    int anhSangDaoNguoc = 4095 - capDoAnhSang;
    anhSangLux = map(anhSangDaoNguoc, 0, 4095, 0, 1000);
    anhSangLux = constrain(anhSangLux, 0, 1000);
    
    // ĐỌC MQ2
    capDoKhi = analogRead(CHAN_MQ2);
    // Wokwi MQ2: Giá trị THẤP = KHÔNG GAS, CAO = CÓ GAS
    khiPPM = map(capDoKhi, 0, 4095, 0, 1000);
    khiPPM = constrain(khiPPM, 0, 1000);
  }
  
  // Tính chỉ số nhiệt (cảm giác nhiệt độ)
  float h1 = -8.78469475556;
  float h2 = 1.61139411;
  float h3 = 2.33854883889;
  float h4 = -0.14611605;
  float h5 = -0.012308094;
  float h6 = -0.0164248277778;
  float h7 = 0.002211732;
  float h8 = 0.00072546;
  float h9 = -0.000003582;
  
  chiSoNhiet = h1 + h2*nhietDo + h3*doAm + 
               h4*nhietDo*doAm + h5*nhietDo*nhietDo + 
               h6*doAm*doAm + h7*nhietDo*nhietDo*doAm + 
               h8*nhietDo*doAm*doAm + 
               h9*nhietDo*nhietDo*doAm*doAm;
  
  // Tính chỉ số thoải mái (0-100) - Chỉ số tổng hợp
  float diemNhiet = max(0.0f, 100.0f - abs(24.0f - nhietDo) * 5);
  float diemAm = max(0.0f, 100.0f - abs(60.0f - doAm) * 2);
  float diemSang = min(100.0f, (anhSangLux / 10.0f));
  float diemKhi = max(0.0f, 100.0f - (khiPPM / 10.0f));
  
  chiSoThoaiMai = (diemNhiet + diemAm + diemSang + diemKhi) / 4;
  
  soDuLieu++;
}

// ===== KIỂM TRA CẢNH BÁO =====
bool kiemTraCanhBao() {
  bool canhBao = false;
  
  if (nhietDo > NHIET_TOI_DA || nhietDo < NHIET_TOI_THIEU) {
    canhBao = true;
  }
  
  if (doAm > AM_TOI_DA || doAm < AM_TOI_THIEU) {
    canhBao = true;
  }
  
  if (anhSangLux < SANG_TOI_THIEU_LUX) {
    canhBao = true;
  }
  
  if (khiPPM > NGUONG_KHI_PPM) {
    canhBao = true;
  }
  
  canhBaoHeThong = canhBao;
  return canhBao;
}

// ===== ĐIỀU KHIỂN QUẠT TỰ ĐỘNG =====
void dieuKhienQuatTuDong() {
  // Bật quạt khi nhiệt độ >= 30°C
  if (nhietDo >= NHIET_BAT_QUAT && !trangThaiQuat) {
    trangThaiQuat = true;
    digitalWrite(RELE_QUAT, HIGH);
    Serial.println("🌀 TU DONG: Bat quat (Nhiet do >= 30°C)");
    mqtt.publish(chuDe_trangThai, "quat_bat_tu_dong");
  }
  // Tắt quạt khi nhiệt độ <= 28°C (tránh bật tắt liên tục)
  else if (nhietDo <= NHIET_TAT_QUAT && trangThaiQuat) {
    trangThaiQuat = false;
    digitalWrite(RELE_QUAT, LOW);
    Serial.println("🌀 TU DONG: Tat quat (Nhiet do <= 28°C)");
    mqtt.publish(chuDe_trangThai, "quat_tat_tu_dong");
  }
}

// ===== ĐIỀU KHIỂN ĐÈN & COI BÁO =====
void dieuKhienChiBao() {
  if (canhBaoHeThong) {
    digitalWrite(DEN_XANH, LOW);
    digitalWrite(DEN_DO, HIGH);
    tone(COI_BAO, 1000, 200);
  } else {
    digitalWrite(DEN_XANH, HIGH);
    digitalWrite(DEN_DO, LOW);
    noTone(COI_BAO);
  }
}

// ===== CẬP NHẬT LCD (16x2) - HIỂN THỊ LUÂN PHIÊN =====
void capNhatLCD() {
  static unsigned long lanDoiTrangCuoi = 0;
  
  if (millis() - lanDoiTrangCuoi > KHOANG_LCD) {
    trangLCD = (trangLCD + 1) % 5;  // 5 trang
    lanDoiTrangCuoi = millis();
    lcd.clear();
  }
  
  if (trangLCD == 0) {
    // Trang 1: Nhiệt độ & Độ ẩm
    lcd.setCursor(0, 0);
    lcd.print("T:");
    lcd.print(nhietDo, 1);
    lcd.write(223);
    lcd.print("C ");
    
    if (nhietDo > NHIET_TOI_DA) {
      lcd.print("NONG!");
    } else if (nhietDo < NHIET_TOI_THIEU) {
      lcd.print("LANH");
    } else {
      lcd.print("TOT ");
    }
    
    lcd.setCursor(0, 1);
    lcd.print("H:");
    lcd.print(doAm, 1);
    lcd.print("% ");
    
    if (doAm > AM_TOI_DA) {
      lcd.print("CAO ");
    } else if (doAm < AM_TOI_THIEU) {
      lcd.print("THAP");
    } else {
      lcd.print("TOT ");
    }
    
  } else if (trangLCD == 1) {
    // Trang 2: Ánh sáng
    lcd.setCursor(0, 0);
    lcd.print("Sang:");
    lcd.print((int)anhSangLux);
    lcd.print(" Lux  ");
    
    lcd.setCursor(0, 1);
    if (anhSangLux < SANG_TOI_THIEU_LUX) {
      lcd.print("Trang thai: TOI");
    } else {
      lcd.print("Trang thai: TOT");
    }
    
  } else if (trangLCD == 2) {
    // Trang 3: Khí gas
    lcd.setCursor(0, 0);
    lcd.print("Khi:");
    lcd.print((int)khiPPM);
    lcd.print(" PPM   ");
    
    lcd.setCursor(0, 1);
    if (khiPPM > NGUONG_KHI_PPM) {
      lcd.print("NGUY HIEM!!!  ");
    } else {
      lcd.print("Trang thai: TOT");
    }
    
  } else if (trangLCD == 3) {
    // Trang 4: Chỉ số thoải mái & Chỉ số nhiệt
    lcd.setCursor(0, 0);
    lcd.print("Thoai mai:");
    lcd.print(chiSoThoaiMai);
    lcd.print("/100");
    
    lcd.setCursor(0, 1);
    lcd.print("Chi so:");
    lcd.print(chiSoNhiet, 1);
    lcd.write(223);
    lcd.print("C  ");
    
  } else {
    // Trang 5: Trạng thái hệ thống
    lcd.setCursor(0, 0);
    if (canhBaoHeThong) {
      lcd.print("! CANH BAO !   ");
    } else {
      lcd.print("He thong TOT   ");
    }
    
    lcd.setCursor(0, 1);
    lcd.print("Quat:");
    lcd.print(trangThaiQuat ? "BAT" : "TAT");
    lcd.print(" #");
    lcd.print(soDuLieu);
    lcd.print("    ");
  }
}

// ===== GỬI THINGSPEAK =====
void guiThingSpeak() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  Serial.println("\n→ Dang gui den ThingSpeak...");
  
  ThingSpeak.setField(1, nhietDo);
  ThingSpeak.setField(2, doAm);
  ThingSpeak.setField(3, anhSangLux);
  ThingSpeak.setField(4, khiPPM);
  ThingSpeak.setField(5, trangThaiQuat ? 1 : 0);
  ThingSpeak.setField(6, chiSoNhiet);
  ThingSpeak.setField(7, chiSoThoaiMai);
  ThingSpeak.setField(8, canhBaoHeThong ? 1 : 0);
  
  int trangThai = ThingSpeak.writeFields(maKenh, khaiGhi);
  
  if (trangThai == 200) {
    Serial.println("✓ ThingSpeak: Thanh cong");
  } else {
    Serial.print("✗ Loi ThingSpeak: ");
    Serial.println(trangThai);
  }
}

// ===== GỬI MQTT =====
void guiMQTT() {
  if (!mqtt.connected()) {
    ketNoiMQTT();
    return;
  }
  
  String duLieu = "{";
  duLieu += "\"nhiet_do\":" + String(nhietDo, 1) + ",";
  duLieu += "\"do_am\":" + String(doAm, 1) + ",";
  duLieu += "\"anh_sang_lux\":" + String(anhSangLux, 1) + ",";
  duLieu += "\"khi_ppm\":" + String(khiPPM, 1) + ",";
  duLieu += "\"chi_so_nhiet\":" + String(chiSoNhiet, 1) + ",";
  duLieu += "\"thoai_mai\":" + String(chiSoThoaiMai) + ",";
  duLieu += "\"quat\":" + String(trangThaiQuat ? "true" : "false") + ",";
  duLieu += "\"canh_bao\":" + String(canhBaoHeThong ? "true" : "false");
  duLieu += "}";
  
  mqtt.publish(chuDe_duLieu, duLieu.c_str());
  Serial.println("✓ MQTT: " + duLieu);
}

// ===== IN RA SERIAL =====
void inSerial() {
  Serial.println("\n========== DU LIEU CAM BIEN ==========");
  Serial.print("Nhiet do: ");
  Serial.print(nhietDo, 1);
  Serial.print(" °C ");
  Serial.println(nhietDo > NHIET_TOI_DA ? "[NONG]" : nhietDo < NHIET_TOI_THIEU ? "[LANH]" : "[TOT]");
  
  Serial.print("Do am   : ");
  Serial.print(doAm, 1);
  Serial.print(" % ");
  Serial.println(doAm > AM_TOI_DA ? "[CAO]" : doAm < AM_TOI_THIEU ? "[THAP]" : "[TOT]");
  
  Serial.print("Anh sang: ");
  Serial.print(anhSangLux, 1);
  Serial.print(" Lux");
  if (CHE_DO_THU) Serial.print(" [NGAU NHIEN]");
  else {
    Serial.print(" (Tho:");
    Serial.print(capDoAnhSang);
    Serial.print(")");
  }
  Serial.println(anhSangLux < SANG_TOI_THIEU_LUX ? " [TOI]" : " [SANG]");
  
  Serial.print("Khi gas : ");
  Serial.print(khiPPM, 1);
  Serial.print(" PPM");
  if (CHE_DO_THU) Serial.print(" [NGAU NHIEN]");
  else {
    Serial.print(" (Tho:");
    Serial.print(capDoKhi);
    Serial.print(")");
  }
  Serial.println(khiPPM > NGUONG_KHI_PPM ? " [NGUY HIEM]" : " [AN TOAN]");
  
  Serial.print("Chi so nhiet: ");
  Serial.print(chiSoNhiet, 1);
  Serial.println(" °C");
  
  Serial.print("Thoai mai   : ");
  Serial.print(chiSoThoaiMai);
  Serial.println("/100");
  
  Serial.println("\n========== TRANG THAI ==========");
  Serial.print("Quat    : ");
  Serial.println(trangThaiQuat ? "BAT" : "TAT");
  Serial.print("Canh bao: ");
  Serial.println(canhBaoHeThong ? "CO" : "KHONG");
  Serial.print("Du lieu #: ");
  Serial.println(soDuLieu);
  Serial.println("====================================\n");
}

// ===== VÒNG LẶP CHÍNH =====
void loop() {
  unsigned long thoiGianHienTai = millis();
  
  if (mqtt.connected()) {
    mqtt.loop();
  } else {
    ketNoiMQTT();
  }
  
  // Đọc cảm biến
  if (thoiGianHienTai - lanDocCamBienCuoi >= KHOANG_CAM_BIEN) {
    docCamBien();
    kiemTraCanhBao();
    dieuKhienQuatTuDong();
    dieuKhienChiBao();
    inSerial();
    lanDocCamBienCuoi = thoiGianHienTai;
  }
  
  // Cập nhật LCD
  if (thoiGianHienTai - lanCapNhatLCDCuoi >= KHOANG_LCD) {
    capNhatLCD();
    lanCapNhatLCDCuoi = thoiGianHienTai;
  }
  
  // Gửi ThingSpeak
  if (thoiGianHienTai - lanCapNhatThingSpeakCuoi >= KHOANG_THINGSPEAK) {
    guiThingSpeak();
    lanCapNhatThingSpeakCuoi = thoiGianHienTai;
  }
  
  // Gửi MQTT
  if (thoiGianHienTai - lanCapNhatMQTTCuoi >= KHOANG_MQTT) {
    guiMQTT();
    lanCapNhatMQTTCuoi = thoiGianHienTai;
  }
  
  delay(100);
}