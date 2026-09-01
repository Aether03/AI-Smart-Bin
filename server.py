# server.py
from flask import Flask, request, jsonify
from ultralytics import YOLO
import cv2
import numpy as np
import requests
import os

print("✅ Imports complete")

app = Flask(__name__)

# -------------------------
# Model selection
# -------------------------
# Use the built-in lightweight YOLOv8 nano model (works well for CPU)
print("⏳ Loading YOLO model...")

model = YOLO('yolov8n.pt')

print("✅ Model loaded successfully")

# If you later train a custom model, put its path here and uncomment:
model = YOLO('runs/detect/train5/weights/best.pt')
# -------------------------

# Configure where to forward the result (the ESP32 main brain).
# Replace these values with the actual IP and port of your ESP32 main device.
ESP32_MAIN_IP = "10.62.147.21"   # <-- change to your ESP32 main IP
ESP32_MAIN_PORT = 80          # <-- change to your ESP32 main port
FORWARD_URL = f"http://{ESP32_MAIN_IP}:{ESP32_MAIN_PORT}/tag"

@app.route('/classify', methods=['POST'])
def classify():
    """
    Accepts multipart/form POST with file field 'image'.
    Returns JSON: { 'class': 'Plastic', 'conf': 0.87 }
    Also attempts to forward same JSON to the ESP32 main brain.
    """
    if 'image' not in request.files:
        return jsonify({'error': 'no file part named "image"'}), 400

    # Read image bytes from request and convert to OpenCV image
    file_bytes = request.files['image'].read()
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return jsonify({'error': 'cannot decode image'}), 400

    # Run YOLO inference (imgsz=640 for balanced speed/accuracy)
    results = model(img, imgsz=640)[0]

    # Determine best detection: choose highest-confidence box if present
    if not results.boxes or len(results.boxes) == 0:
        tag = "Unknown"
        conf = 0.0
    else:
        confs = results.boxes.conf.cpu().numpy()
        cls_ids = results.boxes.cls.cpu().numpy().astype(int)
        max_idx = confs.argmax()
        conf = float(confs[max_idx])
        cls_id = int(cls_ids[max_idx])
        tag = results.names[cls_id]

    response = {'class': tag, 'conf': conf}

    # Try forwarding classification to ESP32 main brain (non-blocking best-effort)
    try:
        # small timeout so server doesn't hang waiting for ESP32
        requests.post(FORWARD_URL, json=response, timeout=1.5)
    except Exception as e:
        # Print error for debugging; but still return classification
        print("Forwarding to ESP32 failed:", e)

    return jsonify(response)


if __name__ == '__main__':
    # Run app on all network interfaces (accessible on your LAN)
    app.run(host='0.0.0.0', port=5000, debug=False)
