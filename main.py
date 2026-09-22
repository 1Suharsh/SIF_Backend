from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
import datetime
import os
from dotenv import load_dotenv

# 1. Load environment variables from the .env file
load_dotenv()

app = FastAPI()

# 2. Allow your React frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Connect to MongoDB Securely
MONGO_URI = os.getenv("MONGO_URI") 
client = MongoClient(MONGO_URI)
db = client.sifguard_db

# Create separate collections for your two features
alerts_collection = db.safety_alerts
reports_collection = db.safety_reports


# ==========================================
# DATA MODELS (What React sends to Python)
# ==========================================

class SafetyAlert(BaseModel):
    zone: str
    label: str
    severity: str
    timestamp: str = None

class ReportInput(BaseModel):
    observer_name: str
    location: str
    observation_text: str


# ==========================================
# 1. CAMERA ALERTS API (Computer Vision)
# ==========================================

@app.post("/api/alerts")
async def save_alert(alert: SafetyAlert):
    alert_dict = alert.dict()
    alert_dict["created_at"] = datetime.datetime.utcnow()
    
    # Insert into MongoDB
    result = alerts_collection.insert_one(alert_dict)
    return {"status": "success", "id": str(result.inserted_id)}

@app.get("/api/alerts")
async def get_alerts():
    alerts = list(alerts_collection.find({}, {"_id": 0}).sort("created_at", -1).limit(50))
    return {"alerts": alerts}


# ==========================================
# 2. REPORT ANALYZER API (NLP Engine)
# ==========================================

@app.post("/api/reports")
async def process_report(report: ReportInput):
    # Hackathon Logic: Analyze text keywords to simulate NLP SIF classification
    text = report.observation_text.lower()
    
    if "height" in text or "scaffold" in text or "fall" in text or "harness" in text:
        severity = "CRITICAL"
        score = 92
        is_sif = True
        rule = "Working at Height"
        action = "Dispatch safety officer to verify 100% tie-off compliance immediately."
    elif "lock" in text or "tag" in text or "loto" in text or "energy" in text:
        severity = "CRITICAL"
        score = 88
        is_sif = True
        rule = "Energy Isolation (LOTO)"
        action = "Audit LOTO permits and physical locks at the specified equipment."
    else:
        severity = "MEDIUM"
        score = 45
        is_sif = False
        rule = "General Safety"
        action = "Review during next weekly safety toolbox talk."

    # Construct the final analyzed document
    analyzed_report = {
        "observer_name": report.observer_name,
        "location": report.location,
        "observation_text": report.observation_text,
        "severity_band": severity,
        "risk_score": score,
        "is_sif_precursor": is_sif,
        "iogp_rule": rule,
        "recommended_action": action,
        "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        "created_at": datetime.datetime.utcnow()
    }

    # Save the analyzed report to MongoDB
    result = reports_collection.insert_one(analyzed_report)
    
    # Clean up the output to send back to React
    analyzed_report["id"] = str(result.inserted_id)
    analyzed_report.pop("_id", None) 
    
    return analyzed_report

@app.get("/api/reports")
async def get_reports():
    reports = list(reports_collection.find({}, {"_id": 0}).sort("created_at", -1).limit(50))
    
    # Ensure ID string is included for React mapping
    for idx, r in enumerate(reports):
        if "id" not in r:
            r["id"] = str(idx)
            
    return reports