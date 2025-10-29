from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class PatientRegistration(BaseModel):
    # Basic Demographics
    age: int
    sex: str
    blood_group: str
    height_cm: float
    weight_kg: float
    contact_number: str
    residence: Optional[str] = "Urban"  # Urban, Rural, Semi-Urban
    
    # Medical History (encrypted)
    medical_history: Optional[str] = None
    chronic_conditions: Optional[List[str]] = []
    medications: Optional[List[str]] = []
    allergies: Optional[List[str]] = []
    previous_surgeries: Optional[List[str]] = []
    
    # Lifestyle Factors
    smoking: Optional[str] = "No"  # Yes, No
    smoking_history: Optional[str] = "Never"  # Never, Former, Current
    alcohol_consumption: Optional[str] = "None"  # None, Moderate, High
    exercise_frequency: Optional[str] = "Regular"  # None, Rare, Regular
    
    # Family History
    family_history: Optional[int] = 0  # 0 or 1 (binary)
    
    # Vital Signs
    systolic_bp: Optional[int] = 120
    diastolic_bp: Optional[int] = 80
    pulse_rate: Optional[int] = 75
    
    # Cardiac Conditions (binary flags)
    hypertension: Optional[int] = 0
    diabetes: Optional[int] = 0
    heart_failure: Optional[int] = 0
    atrial_fibrillation: Optional[int] = 0
    Affected_by_Covid: Optional[int] = 0  # 0 or 1
    
    # Heart Disease Details
    type_of_heart_disease: Optional[str] = "None"  # CAD, Valve, Arrhythmia, CHF, None
    ejection_fraction: Optional[int] = 55  # LVEF percentage
    cardiac_rhythm: Optional[str] = "Normal"  # Normal, AFib, Flutter
    nyha_class: Optional[str] = "I"  # I, II, III, IV
    
    # Surgery Details
    number_of_heart_surgeries: Optional[int] = 0
    surgery_type: Optional[str] = "CABG"  # CABG, Valve Replacement, Bypass, Pacemaker
    surgery_category: Optional[str] = "Major"  # Major, Intermediate, Minor
    surgery_complexity: Optional[str] = "Medium"  # Low, Medium, High
    surgery_duration_hours: Optional[float] = 4.0

class PredictionRequest(BaseModel):
    patient_data: Optional[Dict[str, Any]] = None
    use_profile: bool = False

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ScanInterpretation(BaseModel):
    scan_type: str
    findings: Optional[str] = None
