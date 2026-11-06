# ONSAHS: Final Project Documentation
## On the Spot Accident Health Status System

### 1. Overview
ONSAHS is an integrated emergency response platform that combines IoT medical sensors, AI-based injury classification, and a multi-role web ecosystem. The system is designed to minimize response time and provide paramedics/admins with critical patient data before they even arrive on the scene.

### 2. Core Components
- **AI Model:** ResNet-50 (PyTorch) fine-tuned to classify injury severity into three categories: **Mild**, **Moderate**, and **Critical**.
- **IoT Hardware:** ESP32 microcontroller reading real-time ECG, BPM, and Temperature.
- **Backend:** FastAPI (Python) server managing data flow, AI inference, and real-time vitals broadcasting.
- **Frontend Portal:** Three distinct interfaces (Reporter, Admin, Responder) built with Tailwind CSS for a modern light-mode experience.

### 3. Key Features
- **Instant AI Assessment:** Civilians upload injury photos and receive immediate severity assessments.
- **Geolocation tracking:** Automatic GPS capture of the accident site.
- **Privacy-First Visualization:** All injury images are initially blurred. Users must click to reveal the image, preventing accidental exposure to graphic content.
- **Real-time Vitals Streaming:** Admin and Responder can see live ECG and BPM graphs as soon as the ESP32 is connected to the patient.
- **Responder Dispatch:** Admins can dispatch specific responders who receive instant, pulsing alerts with patient location and severity.

### 4. Setup and Execution
1. **Server:** Run `python app.py` to start the backend.
2. **Tunneling:** Use `npx localtunnel --port 8000 --subdomain [your-subdomain]` to make the system publicly accessible.
3. **Hardware:** Flash the `esp32_iot_client.ino` to your ESP32, ensuring the Server URL matches your public tunnel or local IP.

### 5. Project Structure
- `app.py`: Main server logic.
- `model.pth`: Trained AI weights.
- `templates/`: HTML portal designs.
- `static/uploads/`: Storage for incident photos.
- `esp32_iot_client.ino`: Hardware source code.
- `train.py`: Script used for AI model training.

---
**Project Status:** Completed & Fully Functional.
