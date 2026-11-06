#include <WiFi.h>
#include <HTTPClient.h>

// ===== Sensor Pins =====
const int ECG_PIN = 34;        // AD8232 ECG OUTPUT
const int HEART_PIN = 35;      // HBT v2 Heartbeat sensor
const int LM35_PIN = 32;       // LM35 analog output pin

// ===== WiFi credentials =====
const char* ssid = "OnePlus 12";        
const char* password = "whatforyou"; 

// ===== Python Dashboard Server Details =====
// Change this to the IP address of the laptop running `app.py`
const char* serverUrl = "http://192.168.1.100:8000/api/vitals"; // REPLACE WITH YOUR LAPTOP'S IP

unsigned long lastTime = 0;
// Send data 10 times a second to match the old dashboard's smooth graphs
unsigned long timerDelay = 100;

// ===== Mapping Functions (From your original code) =====
float mapToBPM(int rawValue, bool isWomen) {
  if (isWomen) return map(rawValue, 1800, 1900, 55, 108);
  else return map(rawValue, 1800, 1900, 49, 100);
}

float mapToPWavelength(int rawValue) {
  return map(rawValue, 1800, 1900, 81, 130);
}

float mapToPRInterval(int rawValue) {
  return map(rawValue, 1800, 1900, 119, 210);
}

float mapToQRSDuration(int rawValue) {
  return map(rawValue, 1800, 1900, 74, 110);
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(ECG_PIN, INPUT);
  pinMode(HEART_PIN, INPUT);
  pinMode(LM35_PIN, INPUT);

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi. IP address: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  // Check if it's time to send data and WiFi is connected
  if ((millis() - lastTime) > timerDelay) {
    if(WiFi.status() == WL_CONNECTED){
      HTTPClient http;
      
      // Read sensors
      int ecgValue = analogRead(ECG_PIN);
      int heartValue = analogRead(HEART_PIN);

      // Temperature
      int lm35Value = analogRead(LM35_PIN);
      float voltage = (lm35Value / 4095.0) * 3.3;
      float temperature = voltage / 0.01;

      // Calculations
      bool isWomen = false;
      float bpm = mapToBPM(ecgValue, isWomen);
      float pWave = mapToPWavelength(ecgValue);
      float prInterval = mapToPRInterval(ecgValue);
      float qrsDuration = mapToQRSDuration(ecgValue);

      // Construct JSON payload manually (no extra library needed)
      String jsonPayload = "{";
      jsonPayload += "\"ecg\":" + String(ecgValue) + ",";
      jsonPayload += "\"bpm\":" + String(bpm) + ",";
      jsonPayload += "\"p_wave\":" + String(pWave) + ",";
      jsonPayload += "\"pr_interval\":" + String(prInterval) + ",";
      jsonPayload += "\"qrs\":" + String(qrsDuration) + ",";
      jsonPayload += "\"temperature\":" + String(temperature);
      jsonPayload += "}";

      // Send HTTP POST request
      http.begin(serverUrl);
      http.addHeader("Content-Type", "application/json");
      int httpResponseCode = http.POST(jsonPayload);
      
      // We don't need to print the response every 100ms, just free resources
      http.end();
    }
    else {
      Serial.println("WiFi Disconnected");
    }
    lastTime = millis();
  }
}
