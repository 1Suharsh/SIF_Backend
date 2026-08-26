from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

# --- 1. INITIALIZE FASTAPI & CORS ---
app = FastAPI(title="SIFGuard API", version="1.0")

# Allow your React frontend (usually localhost:5173 for Vite) to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. DATABASE SETUP (Mock In-Memory for Hackathon) ---
# Note: For production, you would connect to MongoDB here using PyMongo:
# client = MongoClient("mongodb+srv://<user>:<password>@cluster.mongodb.net/")
# db = client.sifguard
# But for a seamless demo without setting up an Atlas account today, we use an in-memory list:
db_reports = []

# --- 3. DATA MODELS ---
class ReportInput(BaseModel):
    observer_name: str
    location: str
    observation_text: str

class SafetyReport(BaseModel):
    id: str
    timestamp: str
    observer_name: str
    location: str
    observation_text: str
    is_sif_precursor: bool
    risk_score: int
    severity_band: str
    iogp_rule: str
    recommended_action: str

# --- 4. THE INTELLIGENCE ENGINE (NLP & RULE MAPPING) ---
def analyze_safety_text(text: str):
    """
    Simulates the NLP rule-assisted classification mentioned in the pitch.
    Scans text for SIF precursors, maps to IOGP rules, and calculates risk.
    """
    text_lower = text.lower()
    
    # Default Safe Baseline
    analysis = {
        "is_sif_precursor": False,
        "risk_score": 15,
        "severity_band": "LOW",
        "iogp_rule": "General Safety",
        "recommended_action": "Standard observation recorded. No immediate escalation."
    }

    # Rule 1: Working at Height
    if any(word in text_lower for word in ["height", "fall", "scaffold", "harness", "roof", "ladder"]):
        analysis = {
            "is_sif_precursor": True,
            "risk_score": 92,
            "severity_band": "CRITICAL",
            "iogp_rule": "Working at Height",
            "recommended_action": "IMMEDIATE: Halt work. Verify 100% tie-off and inspect fall arrest system."
        }
    
    # Rule 2: Energy Isolation (LOTO)
    elif any(word in text_lower for word in ["electrical", "wire", "shock", "lockout", "tagout", "voltage"]):
        analysis = {
            "is_sif_precursor": True,
            "risk_score": 88,
            "severity_band": "CRITICAL",
            "iogp_rule": "Energy Isolation",
            "recommended_action": "IMMEDIATE: Stop equipment. Verify zero energy state and apply physical locks."
        }
        
    # Rule 3: Safe Mechanical Lifting / Machinery
    elif any(word in text_lower for word in ["crane", "lift", "suspended", "load", "forklift", "crush"]):
        analysis = {
            "is_sif_precursor": True,
            "risk_score": 75,
            "severity_band": "HIGH",
            "iogp_rule": "Safe Mechanical Lifting",
            "recommended_action": "PRIORITY: Clear the drop zone. Verify load stability and operator certification."
        }
        
    # Rule 4: PPE / Basic Compliance
    elif any(word in text_lower for word in ["ppe", "helmet", "glasses", "vest", "boots", "gloves"]):
        analysis = {
            "is_sif_precursor": False,
            "risk_score": 45,
            "severity_band": "MEDIUM",
            "iogp_rule": "PPE Compliance",
            "recommended_action": "Provide replacement PPE and issue a verbal safety reminder to the worker."
        }

    return analysis

# --- 5. API ROUTES ---

@app.post("/api/reports", response_model=SafetyReport)
async def submit_report(report: ReportInput):
    """
    Endpoint to submit a new free-text observation.
    The AI Engine processes it, scores it, and saves it.
    """
    # 1. Run the NLP Intelligence Engine
    ai_analysis = analyze_safety_text(report.observation_text)
    
    # 2. Construct the final report document
    new_report = SafetyReport(
        id=str(uuid.uuid4()),
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        observer_name=report.observer_name,
        location=report.location,
        observation_text=report.observation_text,
        is_sif_precursor=ai_analysis["is_sif_precursor"],
        risk_score=ai_analysis["risk_score"],
        severity_band=ai_analysis["severity_band"],
        iogp_rule=ai_analysis["iogp_rule"],
        recommended_action=ai_analysis["recommended_action"]
    )
    
    # 3. Save to database
    db_reports.append(new_report)
    
    return new_report

@app.get("/api/reports", response_model=List[SafetyReport])
async def get_reports():
    """
    Endpoint for the React dashboard to fetch all processed reports,
    sorted by the most recent first.
    """
    return sorted(db_reports, key=lambda x: x.timestamp, reverse=True)

@app.get("/")
async def root():
    return {"status": "SIFGuard FastAPI Backend is Online!"}