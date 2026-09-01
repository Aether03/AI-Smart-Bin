#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>

const char* ssid = "Amirul's";
const char* password = "1234567890";

WebServer server(80);  // Must match Flask server's FORWARD_URL port
String lastClass = "none";
float lastConf = 0.0;

void handleTag() {
  if (server.hasArg("plain")) {
    String body = server.arg("plain");
    Serial.println("Received raw JSON: " + body);

    StaticJsonDocument<200> doc;
    DeserializationError error = deserializeJson(doc, body);

    if (!error) {
      lastClass = doc["class"].as<String>();
      lastConf = doc["conf"].as<float>();

      Serial.print("🧠 Object: ");
      Serial.print(lastClass);
      Serial.print(" | Confidence: ");
      Serial.println(lastConf);

      // TODO: Add actuator control here
      // e.g., if (lastClass == "plastic") moveServo(PLASTIC_BIN);

      server.sendHeader("Access-Control-Allow-Origin", "*"); // Allow Flask
      server.send(200, "text/plain", "Classification received");
    } else {
      Serial.println("❌ JSON Parsing Error");
      server.send(400, "text/plain", "Invalid JSON");
    }
  } else {
    Serial.println("⚠️ Missing POST body");
    server.send(400, "text/plain", "Missing body");
  }
}

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("✅ Connected! IP: ");
  Serial.println(WiFi.localIP());

  // Define endpoint
  server.on("/tag", HTTP_POST, handleTag);
  
  server.begin();
  Serial.println("🚀 Main Brain ready to receive on /tag");
}

void loop() {
  server.handleClient();
}
