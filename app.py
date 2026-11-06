import os
import math
import threading
import time
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
from fastapi import FastAPI, UploadFile, File, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import io
import uuid
from datetime import datetime

app = FastAPI(title="ONSAHS - Emergency Response Hub")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup Templates
base_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(base_dir, "static")),
    name="static"
)

# Vitals In-Memory Store
latest_vitals = {
    "ecg": 0.85,
    "bpm": 138.0,
    "p_wave": 80,
    "pr_interval": 240,
    "qrs": 140,
    "temperature": 35.3,
}

# ECG Simulation
def generate_ecg_value(t):
    """Simulates a basic ECG waveform"""
    t = t % 1.0

    if 0.0 <= t < 0.2:
        return 0.25 * math.sin(math.pi * t / 0.2)
    elif 0.2 <= t < 0.25:
        return -0.5 * math.sin(math.pi * (t - 0.2) / 0.05)
    elif 0.25 <= t < 0.32:
        return 1.5 * math.sin(math.pi * (t - 0.25) / 0.07)
    elif 0.32 <= t < 0.37:
        return -0.3 * math.sin(math.pi * (t - 0.32) / 0.05)
    elif 0.4 <= t < 0.7:
        return 0.4 * math.sin(math.pi * (t - 0.4) / 0.3)
    else:
        return 0.0


def ecg_simulation_loop():
    t = 0.0
    while True:
        bpm = latest_vitals["bpm"]
        speed = bpm / 60.0

        latest_vitals["ecg"] = generate_ecg_value(t * speed)

        latest_vitals["pr_interval"] = round(240 + 15 * math.sin(t * 0.3), 1)
        latest_vitals["qrs"] = round(140 + 10 * math.sin(t * 0.5 + 1.2), 1)
        latest_vitals["p_wave"] = round(80 + 12 * math.sin(t * 0.4 + 0.7), 1)
        latest_vitals["bpm"] = round(138 + 8 * math.sin(t * 0.2), 1)
        latest_vitals["spo2"] = round(91.0 + 1.5 * math.sin(t * 0.15), 1)

        t += 0.05
        if t > 1000:
            t = 0.0

        time.sleep(0.05)


# Start ECG simulation
ecg_thread = threading.Thread(target=ecg_simulation_loop, daemon=True)
ecg_thread.start()

# Stores
incidents = []
available_responders = ["Medic Alpha", "Medic Bravo", "Rapid Response 1"]

# Models
class VitalsPayload(BaseModel):
    ecg: float
    bpm: float
    p_wave: float = 0.0
    pr_interval: float = 0.0
    qrs: float = 0.0
    temperature: float


class AssignPayload(BaseModel):
    incident_id: str
    responder: str


# AI Model
device = torch.device("cpu")
model = None

class_mapping = {
    0: "Critical",
    1: "Mild",
    2: "Moderate"
}


def load_model():
    global model
    model_path = os.path.join(base_dir, "model.pth")

    if os.path.exists(model_path):
        print("Loading AI Model...")
        model = models.resnet50()
        num_ftrs = model.fc.in_features
        model.fc = nn.Linear(num_ftrs, 3)

        model.load_state_dict(torch.load(model_path, map_location=device))
        model.eval()

        print("Model Loaded Successfully!")
    else:
        print("Model weights not found. Mocking AI.")


load_model()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        [0.485, 0.456, 0.406],
        [0.229, 0.224, 0.225]
    )
])

# ---------------- HTML ----------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="reporter.html"
    )


@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html"
    )


@app.get("/responder", response_class=HTMLResponse)
async def responder_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="responder.html"
    )

# ---------------- VITALS ----------------
@app.post("/api/vitals")
async def receive_vitals(payload: VitalsPayload):
    global latest_vitals
    latest_vitals["victim"] = payload.dict()
    return {"status": "success"}


@app.get("/api/vitals")
async def get_vitals():
    return latest_vitals


@app.get("/api/vitals/{patient_type}")
async def get_vitals_by_type(patient_type: str):
    if patient_type in latest_vitals:
        return latest_vitals[patient_type]

    return JSONResponse(
        {"status": "error", "message": "Patient type not found"},
        status_code=404
    )

# ---------------- INCIDENTS ----------------
@app.post("/api/predict")
async def predict_injury(
    file: UploadFile = File(...),
    latitude: str = Form(None),
    longitude: str = Form(None)
):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")

        severity = "Unknown"

        if model is not None:
            input_tensor = transform(image).unsqueeze(0)

            with torch.no_grad():
                output = model(input_tensor)
                probabilities = torch.nn.functional.softmax(output[0], dim=0)
                confidence, predicted = torch.max(probabilities, 0)

                if confidence.item() < 0.65:
                    severity = "Not an Injury / Unrecognized"
                else:
                    severity = class_mapping.get(predicted.item(), "Unknown")
        else:
            severity = "Pending Model Training"

        incident_id = str(uuid.uuid4())

        image_filename = f"{incident_id}.jpg"
        image_path = os.path.join(base_dir, "static", "uploads", image_filename)
        image.save(image_path, "JPEG")

        image_url = f"/static/uploads/{image_filename}"

        report = {
            "id": incident_id,
            "filename": file.filename,
            "image_url": image_url,
            "severity": severity,
            "latitude": latitude,
            "longitude": longitude,
            "status": "Pending",
            "assigned_responder": None,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        incidents.insert(0, report)

        if len(incidents) > 20:
            incidents.pop()

        return JSONResponse({
            "status": "success",
            "incident_id": incident_id,
            "severity": severity,
            "filename": file.filename,
            "image_url": image_url
        })

    except Exception as e:
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500
        )


@app.get("/api/reports")
async def get_reports():
    return incidents


@app.get("/api/incident/{incident_id}")
async def get_single_incident(incident_id: str):
    for i in incidents:
        if i["id"] == incident_id:
            return i

    return JSONResponse(
        {"status": "error", "message": "Not Found"},
        status_code=404
    )

# ---------------- RESPONDERS ----------------
@app.get("/api/responders")
async def get_responders():
    return available_responders


@app.post("/api/assign")
async def assign_responder(payload: AssignPayload):
    for i in incidents:
        if i["id"] == payload.incident_id:
            i["assigned_responder"] = payload.responder
            i["status"] = "Responder Dispatched"
            return {"status": "success"}

    return JSONResponse(
        {"status": "error", "message": "Incident not found"},
        status_code=404
    )


@app.get("/api/responder/{responder_name}")
async def get_responder_assignment(responder_name: str):
    for i in incidents:
        if i["assigned_responder"] == responder_name:
            return {"has_assignment": True, "incident": i}

    return {"has_assignment": False}


# ---------------- RUN ----------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)