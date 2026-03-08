import cv2
import json
import numpy as np
from flask import Flask, Response, render_template, jsonify
from keras.models import model_from_json
import threading
import time
from collections import deque, Counter

app = Flask(__name__)

# ── Load model (with Keras 2/3 compatibility) ──────────────────────────────
def _patch_model_json(path):
    """Make Keras-3-saved JSON loadable in Keras 2 (TF 2.15)."""
    with open(path, "r") as f:
        cfg = json.load(f)

    def _fix(obj):
        if isinstance(obj, dict):
            if "batch_shape" in obj and "batch_input_shape" not in obj:
                obj["batch_input_shape"] = obj.pop("batch_shape")
            if "dtype" in obj and isinstance(obj["dtype"], dict):
                obj["dtype"] = obj["dtype"].get("config", {}).get("name", "float32")
            for key in ("module", "registered_name", "build_config",
                        "compile_config"):
                obj.pop(key, None)
            for v in obj.values():
                _fix(v)
        elif isinstance(obj, list):
            for item in obj:
                _fix(item)

    _fix(cfg)
    return json.dumps(cfg)

model_json = _patch_model_json("emotiondetector.json")
model = model_from_json(model_json)
model.load_weights("emotiondetector.h5")
model.compile(optimizer='adam', loss='categorical_crossentropy')

# ── Face detector ───────────────────────────────────────────────────────────
haar_file = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(haar_file)

# ── Labels & emoji mapping ──────────────────────────────────────────────────
labels = {0: 'angry', 1: 'disgust', 2: 'fear', 3: 'happy',
          4: 'neutral', 5: 'sad', 6: 'surprise'}

# ── Shared state (thread-safe) ──────────────────────────────────────────────
lock = threading.Lock()
current_emotion = "neutral"
current_confidences = {label: 0.0 for label in labels.values()}
emotion_history = []              # last 10 entries
face_detected = False


def extract_features(image):
    feature = np.array(image)
    feature = feature.reshape(1, 48, 48, 1)
    return feature / 255.0


def generate_frames():
    """Yield MJPEG frames with face rectangles & emotion labels."""
    global current_emotion, current_confidences, emotion_history, face_detected

    webcam = cv2.VideoCapture(0)
    webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    frame_skip_rate = 3
    frame_count = 0
    
    # Emotion Smoothing Buffer: Stores the last 5 predictions for up to 5 faces
    emotion_buffers = [deque(maxlen=5) for _ in range(5)]
    
    # State for skipped frames
    last_faces = []
    last_smoothed_emotions = []

    # FPS Calculation
    prev_frame_time = time.time()
    fps = 0

    while True:
        # Safety Check: auto-reconnect if camera read fails
        ret, frame = webcam.read()
        if not ret:
            print("Warning: Failed to grab frame. Retrying in 1s...")
            time.sleep(1)
            webcam.release()
            webcam = cv2.VideoCapture(0)
            continue

        # Resize frames explicitly for consistent processing speed
        frame = cv2.resize(frame, (640, 480))
        
        frame_count += 1
        
        # Calculate FPS
        new_frame_time = time.time()
        fps_diff = new_frame_time - prev_frame_time
        if fps_diff > 0:
            fps = 1 / fps_diff
        prev_frame_time = new_frame_time
        
        # Determine if we should process this frame or skip
        process_this_frame = (frame_count % frame_skip_rate == 0)

        if process_this_frame:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
            
            last_faces = []
            last_smoothed_emotions = []
            detected = False
            
            try:
                # Multi-Face Processing
                for i, (x, y, w, h) in enumerate(faces):
                    detected = True
                    roi = gray[y:y + h, x:x + w]
                    roi_resized = cv2.resize(roi, (48, 48))
                    img = extract_features(roi_resized)
                    
                    pred = model.predict(img, verbose=0)
                    prediction_label = labels[pred.argmax()]
                    
                    # Store prediction in smoothing buffer (up to 5 faces)
                    if i < len(emotion_buffers):
                        emotion_buffers[i].append(prediction_label)
                        # Get most frequent emotion
                        most_common_emotion = Counter(emotion_buffers[i]).most_common(1)[0][0]
                    else:
                        most_common_emotion = prediction_label

                    last_faces.append((x, y, w, h))
                    last_smoothed_emotions.append(most_common_emotion)
                    
                    # Update global shared state for the frontend (using primary face)
                    if i == 0:
                        with lock:
                            current_emotion = most_common_emotion
                            current_confidences = {
                                labels[j]: round(float(pred[0][j]) * 100, 1)
                                for j in range(7)
                            }
                            emotion_history.append({
                                "emotion": most_common_emotion,
                                "time": time.strftime("%H:%M:%S")
                            })
                            emotion_history = emotion_history[-10:]

            except cv2.error:
                pass
                
            # Clear buffers for faces that disappeared
            if len(faces) < len(emotion_buffers):
                for i in range(len(faces), len(emotion_buffers)):
                    emotion_buffers[i].clear()

            with lock:
                face_detected = detected

        # Draw overlays (happens every frame, using updated or cached data)
        for i, (x, y, w, h) in enumerate(last_faces):
            label = last_smoothed_emotions[i]
            
            # Outer glow
            cv2.rectangle(frame, (x - 2, y - 2), (x + w + 2, y + h + 2), (138, 43, 226), 2)
            # Main box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), 2)

            # Label background & text
            label_size = cv2.getTextSize(label.upper(), cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            cv2.rectangle(frame, (x, y - label_size[1] - 14), (x + label_size[0] + 10, y), (138, 43, 226), -1)
            cv2.putText(frame, label.upper(), (x + 5, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Draw FPS Counter
        fps_text = f"FPS: {int(fps)}"
        cv2.putText(frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        # Encode frame as JPEG
        try:
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        except cv2.error:
            pass

    webcam.release()


# ── Routes ──────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/emotion_data')
def emotion_data():
    with lock:
        return jsonify({
            "emotion": current_emotion,
            "confidences": current_confidences,
            "history": emotion_history,
            "face_detected": face_detected
        })


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
