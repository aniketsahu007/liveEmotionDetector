# 🧠 EmotionLens — Real-Time Emotion Detection

A deep learning-powered web application that detects **7 facial emotions** in real time using your webcam. Built with TensorFlow/Keras, OpenCV, and Flask.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.15-orange?logo=tensorflow&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.1-lightgrey?logo=flask&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8-green?logo=opencv&logoColor=white)

---

## ✨ Features

- 🎥 **Live Webcam Feed** — MJPEG streaming with face bounding boxes & emotion labels  
- 😄 **7 Emotions Detected** — Angry, Disgust, Fear, Happy, Neutral, Sad, Surprise  
- 📊 **Confidence Bars** — Animated real-time probability scores for each emotion  
- 📜 **Emotion History** — Scrollable log of recent detections with timestamps  
- 🎨 **Premium Dark UI** — Glassmorphism, gradient accents, micro-animations  
- 📱 **Responsive Design** — Works on desktop and mobile browsers  

---

## 📁 Project Structure

```
EMOTION_DETECTOR/
├── app.py                  # Flask web server (main entry point)
├── emotiondetector.json    # CNN model architecture
├── emotiondetector.h5      # Trained model weights
├── trainmodel.ipynb        # Jupyter notebook for model training
├── requirements.txt        # Python dependencies
├── templates/
│   └── index.html          # Frontend HTML page
├── static/
│   ├── style.css           # Stylesheet (dark theme + animations)
│   └── script.js           # Client-side JS (polling + UI updates)
├── images/                 # Training dataset (train/test splits)
└── tf_env/                 # Python virtual environment
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Webcam

### Installation

```bash
# 1. Clone or navigate to the project
cd EMOTION_DETECTOR

# 2. Create & activate a virtual environment (recommended)
python -m venv tf_env
tf_env\Scripts\activate        # Windows
# source tf_env/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt
```

### Run the App

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

---

## 🧬 Model Architecture

The emotion classifier is a **Sequential CNN** trained on 48×48 grayscale face images:

| Layer | Details |
|-------|---------|
| Conv2D × 4 | 128 → 256 → 512 → 512 filters, 3×3 kernel, ReLU |
| MaxPooling2D × 4 | 2×2 pool after each Conv block |
| Dropout × 5 | 0.4 rate (0.3 on final) for regularization |
| Dense | 512 → 256 → **7** (softmax output) |

**Face detection** uses OpenCV's Haar Cascade classifier (`haarcascade_frontalface_default.xml`).

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| ML Framework | TensorFlow 2.15 / Keras |
| Computer Vision | OpenCV 4.8 |
| Web Server | Flask 3.1 |
| Frontend | HTML5, CSS3, Vanilla JS |
| Fonts | Google Fonts (Inter) |

---

## 📦 Dependencies

```
opencv-python==4.8.1.78
tensorflow==2.15.0
numpy==1.24.3
flask==3.1.0
```

---

## 📝 License

This project is for educational purposes.

---

<p align="center">Built with ❤️ using TensorFlow & OpenCV</p>
