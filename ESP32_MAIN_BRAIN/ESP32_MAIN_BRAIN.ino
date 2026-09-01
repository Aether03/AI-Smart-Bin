#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>  // NOT the AVR "Servo" library — that one doesn't drive ESP32 PWM correctly.

const char* ssid = "Amirul's";
const char* password = "1234567890";

WebServer server(80);  // Must match Flask server's FORWARD_URL port
String lastClass = "none";
float lastConf = 0.0;

// =====================================================================
// ACTUATOR CONFIG — sorting servo
//
// !! UNTESTED ON REAL HARDWARE !! These pin/angle/timing values are
// best-guess defaults written with no servo, motor driver, or physical
// bin available to test against. Recalibrate every constant below once
// real hardware is wired up.
//
// Assumption: a single SG90-style hobby servo turns a rotating
// chute/platform to one of four fixed angles (one per class), holds it
// there for SORT_DWELL_MS so the item can drop, then returns to a
// neutral "ready" angle.
//
// POWER: a hobby servo should be driven from its own 5V supply (with a
// common ground back to the ESP32), NOT the ESP32's own 3.3V/5V pin —
// especially once more than one servo, or a higher-torque servo than an
// SG90, is added. The ESP32's onboard regulator cannot supply that kind
// of current and will brown out / reset under servo stall load.
// =====================================================================
const int SERVO_PIN = 13;  // Any free PWM-capable GPIO; confirm it's not a strapping pin on your board.

// Pulse widths (µs) for 0°/180° — typical SG90 range, tune to your servo's datasheet.
const int SERVO_MIN_PULSE_US = 500;
const int SERVO_MAX_PULSE_US = 2400;

// One fixed angle per class, spread across the servo's full sweep, plus a neutral ready angle.
const int SERVO_ANGLE_READY          = 90;   // Neutral position between drops
const int SERVO_ANGLE_NON_RECYCLABLE = 0;
const int SERVO_ANGLE_PLASTIC        = 45;
const int SERVO_ANGLE_PAPER          = 135;
const int SERVO_ANGLE_ALUMINIUM      = 180;

const unsigned long SORT_DWELL_MS = 1500;  // How long to hold the sorting angle before returning to ready.

Servo sortServo;

// Maps a classification string to a bin angle and drives the servo there and back.
// Matching is deliberately loose (substring, case-insensitive) since the exact class
// names returned by the model ("Plastic" vs "Bottle", "Aluminium" vs "Aluminium Cans")
// depend on how it was trained — see server.py / Dataset/Combined_YOLODataset/data.yaml.
// Anything unrecognized falls back to the Non-Recyclable bin.
void routeToBin(String className) {
  String lower = className;
  lower.toLowerCase();

  int targetAngle = SERVO_ANGLE_NON_RECYCLABLE;
  String binLabel = "Non-Recyclable";

  if (lower.indexOf("plastic") >= 0 || lower.indexOf("bottle") >= 0) {
    targetAngle = SERVO_ANGLE_PLASTIC;
    binLabel = "Plastic";
  } else if (lower.indexOf("paper") >= 0) {
    targetAngle = SERVO_ANGLE_PAPER;
    binLabel = "Paper";
  } else if (lower.indexOf("alumin") >= 0 || lower.indexOf("can") >= 0) {
    targetAngle = SERVO_ANGLE_ALUMINIUM;
    binLabel = "Aluminium Cans";
  } else if (lower.indexOf("non-recycl") < 0 && lower.indexOf("trash") < 0) {
    Serial.println("⚠️ Unrecognized class '" + className + "', defaulting to Non-Recyclable bin");
  }

  Serial.println("🦾 Sorting to " + binLabel + " bin (servo -> " + String(targetAngle) + "°)");
  sortServo.write(targetAngle);
  delay(SORT_DWELL_MS);  // Hold position so the item can drop into the chute.

  sortServo.write(SERVO_ANGLE_READY);
  Serial.println("↩️ Servo back at ready position (" + String(SERVO_ANGLE_READY) + "°)");
}

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

      routeToBin(lastClass);

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

  // Set up the sorting servo and park it at the neutral ready position.
  sortServo.setPeriodHertz(50);
  sortServo.attach(SERVO_PIN, SERVO_MIN_PULSE_US, SERVO_MAX_PULSE_US);
  sortServo.write(SERVO_ANGLE_READY);
  Serial.println("🎯 Sorting servo attached on pin " + String(SERVO_PIN) + ", parked at ready position");

  // Define endpoint
  server.on("/tag", HTTP_POST, handleTag);

  server.begin();
  Serial.println("🚀 Main Brain ready to receive on /tag");
}

void loop() {
  server.handleClient();
}
