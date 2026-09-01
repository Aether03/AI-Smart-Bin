# AI Smart Bin

Smart waste-sorting bin: an ESP32-CAM captures a photo of an item, a YOLOv8 model (trained on a custom COCO-derived dataset) classifies it, and the result is forwarded to a second ESP32 that's meant to drive the physical sorting. A companion "TrashGeeks" web prototype explores a points/rewards layer for users.

## How it works

1. **ESP32-CAM** (`ESP32_CAM/ESP32_CAM.ino`) connects to Wi-Fi, captures a frame, and POSTs it to the Flask server's `/classify` endpoint. It also serves a live MJPEG preview stream at its own IP.
2. **Flask server** (`server.py`) runs the trained YOLOv8 model (`runs/detect/train5/weights/best.pt`) on the incoming image, returns `{class, conf}`, and forwards the same JSON to the "main brain" ESP32's `/tag` endpoint.
3. **ESP32 Main Brain** (`ESP32_MAIN_BRAIN/ESP32_MAIN_BRAIN.ino`) receives the classification over HTTP and drives a servo to route the item to the matching bin. This actuator logic is untested on real hardware — see "Known limitations" below.
4. **TrashGeeks web prototype** (`trashgeeks_webpage/mobilewebpage3.html`) is a standalone front-end mockup (login, points, reward redemption) for a possible rewards system. It runs on browser `localStorage` and isn't wired to the classification pipeline yet.

## Waste categories

| Label | Class |
|---|---|
| 0 | Non-Recyclable |
| 1 | Plastic |
| 2 | Paper |
| 3 | Aluminium Cans |

## Setup

1. **Update the hardcoded network config** before flashing anything:
   - `ESP32_CAM/ESP32_CAM.ino` — `ssid`, `password`, and `serverUrl` (your Flask machine's IP)
   - `ESP32_MAIN_BRAIN/ESP32_MAIN_BRAIN.ino` — `ssid`, `password`
   - `server.py` — `ESP32_MAIN_IP` / `ESP32_MAIN_PORT` (the Main Brain's IP)
2. **Flash the firmware** via Arduino IDE — `ESP32_CAM.ino` to the ESP32-CAM module (needs the `esp32` board package for the camera driver), `ESP32_MAIN_BRAIN.ino` to the second ESP32 (needs the `ArduinoJson` and `ESP32Servo` libraries).
3. **Run the server**: `pip install flask ultralytics opencv-python numpy requests`, then `python server.py`.
4. Power on both ESP32 boards. The CAM captures and classifies continuously; results are printed by the Main Brain over serial.
5. Open `trashgeeks_webpage/mobilewebpage3.html` in a browser to view the rewards-UI prototype (standalone, not yet connected to live classifications).

## Model

YOLOv8, trained on a filtered/merged COCO2017 subset (see `filter_bottle_subset.py`, `merge_datasets.py`, `convert_coco_to_yolo_split_yaml.py`). Training metrics and curves for the deployed run are in `runs/detect/train5/`.

## Known limitations

- **Actuator control is UNTESTED ON REAL HARDWARE.** `ESP32_MAIN_BRAIN.ino` now includes servo-based sorting logic (drives an `ESP32Servo`-controlled hobby servo to one of four fixed angles based on the classified item, holds it, then returns to a neutral "ready" angle), but it was written with no servo, motor driver, or physical bin available to verify against. The servo pin, per-class angles, and dwell timing are best-guess placeholders (see the `ACTUATOR CONFIG` block at the top of the file) and need to be calibrated against the actual build before relying on them. No test footage or hardware run exists for this part of the pipeline.
- Wi-Fi credentials and server IPs are hardcoded for a specific local network and need updating per deployment.
- The rewards webpage is a UI prototype only; it isn't connected to the detection pipeline.
