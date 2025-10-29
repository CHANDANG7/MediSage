from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta, datetime
from typing import Optional
import sys
import os
import pandas as pd
import numpy as np
import asyncio
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from backend.models import *
from backend.auth import *
from backend.database import users_collection, patients_collection, chat_sessions_collection
from utils.encryption import DataEncryption
from routes.prediction import router as prediction_router
from routes.chatbot import router as chatbot_router
from routes.scan import router as scan_router

app = FastAPI(title="MediSage AI API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(prediction_router, prefix="/api", tags=["Prediction"])
app.include_router(chatbot_router, prefix="/api", tags=["Chatbot"])
app.include_router(scan_router, prefix="/api", tags=["Scan"])

encryption = DataEncryption()
logger = logging.getLogger(__name__)

# Model retraining configuration
DATASET_PATH = os.path.join(os.path.dirname(__file__), '..', 'ml_models', 'heart.csv')
RETRAIN_THRESHOLD = 10  # Retrain after 10 new patients
RETRAINING_LOG_PATH = os.path.join(os.path.dirname(__file__), '..', 'ml_models', 'retraining_log.csv')

@app.get("/")
async def root():
    return {"message": "MediSage AI API", "status": "running"}

@app.post("/register", response_model=Token)
async def register(user: UserRegister):
    # Check if user exists
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = get_password_hash(user.password)
    
    # Encrypt sensitive user data (full_name)
    encrypted_full_name = encryption.encrypt(user.full_name)
    
    # Create user
    user_dict = {
        "email": user.email,  # Email not encrypted (needed for login)
        "full_name": encrypted_full_name,  # Encrypted
        "hashed_password": hashed_password,  # Already hashed (secure)
        "is_first_login": True,
        "created_at": datetime.utcnow()
    }
    
    await users_collection.insert_one(user_dict)
    
    # Create token
    access_token = create_access_token(
        data={"sub": user.email}, 
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint - expects form data with username and password fields"""
    user = await users_collection.find_one({"email": form_data.username})
    
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user["email"]}, 
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login", response_model=Token)
async def login_json(credentials: UserLogin):
    """Alternative login endpoint - accepts JSON with email and password"""
    user = await users_collection.find_one({"email": credentials.email})
    
    if not user or not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(
        data={"sub": user["email"]}, 
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/check-first-login")
async def check_first_login(current_user: str = Depends(get_current_user)):
    user = await users_collection.find_one({"email": current_user})
    return {"is_first_login": user.get("is_first_login", True)}

@app.post("/patient-registration")
async def patient_registration(
    patient_data: PatientRegistration,
    current_user: str = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    # Check if patient already registered
    existing_patient = await patients_collection.find_one({"email": current_user})
    
    if existing_patient:
        raise HTTPException(
            status_code=400,
            detail="Patient profile already exists. Please use the profile edit page to update your information."
        )
    
    # Encrypt sensitive data
    patient_dict = patient_data.dict()
    patient_dict["email"] = current_user  # Not encrypted (needed for lookup)
    patient_dict["created_at"] = datetime.utcnow()
    
    # Define all sensitive fields to encrypt (PII + Medical)
    sensitive_fields = [
        # Personal Identifiable Information
        "contact_number",
        
        # Medical Data
        "medical_history",
        "chronic_conditions", 
        "medications", 
        "allergies",
        "previous_surgeries"
    ]
    
    # Encrypt all sensitive fields
    encrypted_data = {}
    for field in sensitive_fields:
        if patient_dict.get(field):
            encrypted_data[field] = encryption.encrypt(str(patient_dict[field]))
        else:
            encrypted_data[field] = None
    
    patient_dict.update(encrypted_data)
    
    # Save to database
    await patients_collection.insert_one(patient_dict)
    
    # Update user's first login status
    await users_collection.update_one(
        {"email": current_user},
        {"$set": {"is_first_login": False}}
    )
    
    # Add background task for model retraining
    if background_tasks:
        background_tasks.add_task(
            add_patient_to_training_dataset,
            patient_data.dict()
        )
    
    return {"message": "Patient registration successful", "note": "Data will be used to improve predictions"}

@app.get("/patient-profile")
async def get_patient_profile(current_user: str = Depends(get_current_user)):
    """Get patient profile with decrypted data"""
    patient = await patients_collection.find_one({"email": current_user})
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    # Decrypt all sensitive fields
    sensitive_fields = [
        "contact_number",
        "medical_history", 
        "chronic_conditions", 
        "medications", 
        "allergies",
        "previous_surgeries"
    ]
    
    for field in sensitive_fields:
        if patient.get(field):
            try:
                patient[field] = encryption.decrypt(patient[field])
            except Exception as e:
                # If decryption fails, keep original (might be unencrypted old data)
                logger.warning(f"Failed to decrypt {field}: {str(e)}")
                pass
    
    # Remove MongoDB _id
    patient.pop("_id", None)
    
    return patient

@app.put("/patient-profile")
async def update_patient_profile(
    patient_data: PatientRegistration,
    current_user: str = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    """Update existing patient profile"""
    # Check if patient exists
    existing_patient = await patients_collection.find_one({"email": current_user})
    
    if not existing_patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    # Prepare update data
    patient_dict = patient_data.dict()
    patient_dict["updated_at"] = datetime.utcnow()
    
    # Define all sensitive fields to encrypt
    sensitive_fields = [
        "contact_number",
        "medical_history", 
        "chronic_conditions", 
        "medications", 
        "allergies",
        "previous_surgeries"
    ]
    
    # Encrypt all sensitive fields
    encrypted_data = {}
    for field in sensitive_fields:
        if patient_dict.get(field):
            encrypted_data[field] = encryption.encrypt(str(patient_dict[field]))
        else:
            encrypted_data[field] = None
    
    patient_dict.update(encrypted_data)
    
    # Remove email from update (shouldn't change)
    patient_dict.pop("email", None)
    
    # Update in database
    await patients_collection.update_one(
        {"email": current_user},
        {"$set": patient_dict}
    )
    
    # Add background task for model retraining with updated data
    if background_tasks:
        background_tasks.add_task(
            add_patient_to_training_dataset,
            patient_data.dict()
        )
    
    return {"message": "Profile updated successfully", "note": "Updated data will be used to improve predictions"}

# ===== ASYNC MODEL RETRAINING FUNCTIONS =====

def prepare_patient_record_for_training(patient_data):
    """Prepare patient data for dataset insertion with feature engineering"""
    
    # Calculate BMI
    height_m = patient_data.get('height_cm', 170) / 100
    weight_kg = patient_data.get('weight_kg', 70)
    bmi = round(weight_kg / (height_m ** 2), 1)
    
    # Determine categories
    age = patient_data.get('age', 50)
    age_group = "Young" if age < 35 else ("Middle" if age < 55 else "Old")
    bmi_category = "Underweight" if bmi < 18.5 else ("Normal" if bmi < 25 else ("Overweight" if bmi < 30 else "Obese"))
    
    ef = patient_data.get('ejection_fraction', 55)
    lvef_category = "Reduced" if ef < 40 else ("Mid-range" if ef < 50 else "Preserved")
    
    # Calculate MAP
    systolic = patient_data.get('systolic_bp', 120)
    diastolic = patient_data.get('diastolic_bp', 80)
    map_value = round(diastolic + (systolic - diastolic) / 3, 1)
    
    # Estimate risk score
    risk_score = (
        (age - 20) / 70 * 0.25 +
        (bmi - 18) / 20 * 0.15 +
        (systolic - 100) / 80 * 0.15 +
        (patient_data.get('hypertension', 0) * 0.1) +
        (patient_data.get('heart_failure', 0) * 0.1) +
        (patient_data.get('atrial_fibrillation', 0) * 0.05) +
        (patient_data.get('Affected_by_Covid', 0) * 0.05)
    ) * 100
    risk_score = round(np.clip(risk_score, 5, 95), 1)
    
    # Determine risk level and recovery
    if risk_score < 30:
        risk_level = "Low"
        recovery_days = np.random.randint(5, 10)
    elif risk_score < 60:
        risk_level = "Medium"
        recovery_days = np.random.randint(10, 20)
    elif risk_score < 80:
        risk_level = "High"
        recovery_days = np.random.randint(20, 35)
    else:
        risk_level = "Critical"
        recovery_days = np.random.randint(30, 50)
    
    # Build complete record matching training data format
    record = {
        "patient_id": f"P{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "patient_name": f"Patient_{datetime.utcnow().strftime('%Y%m%d')}",
        "age": age, "age_group": age_group,
        "sex": patient_data.get('sex', 'Male'),
        "contact_number": patient_data.get('contact_number', '9999999999'),
        "email": patient_data.get('email', 'patient@mail.com'),
        "blood_group": patient_data.get('blood_group', 'O+'),
        "residence": patient_data.get('residence', 'Urban'),
        "occupation": "Other", "marital_status": "Married", "education_level": "Graduate",
        "height_cm": patient_data.get('height_cm', 170),
        "weight_kg": weight_kg, "bmi": bmi, "bmi_category": bmi_category,
        "smoking": patient_data.get('smoking', 'No'),
        "Affected_by_Covid": patient_data.get('Affected_by_Covid', 0),
        "smoking_history": patient_data.get('smoking_history', 'Never'),
        "alcohol_consumption": patient_data.get('alcohol_consumption', 'None'),
        "exercise_frequency": patient_data.get('exercise_frequency', 'Regular'),
        "family_history": patient_data.get('family_history', 0),
        "family_history_detail": "None",
        "systolic_bp": systolic, "diastolic_bp": diastolic,
        "mean_arterial_pressure": map_value,
        "pulse_rate": patient_data.get('pulse_rate', 75),
        "type_of_heart_disease": patient_data.get('type_of_heart_disease', 'None'),
        "ejection_fraction": ef, "lvef_category": lvef_category,
        "cardiac_rhythm": patient_data.get('cardiac_rhythm', 'Normal'),
        "nyha_class": patient_data.get('nyha_class', 'I'),
        "hypertension": patient_data.get('hypertension', 0),
        "diabetes": patient_data.get('diabetes', 0),
        "heart_failure": patient_data.get('heart_failure', 0),
        "atrial_fibrillation": patient_data.get('atrial_fibrillation', 0),
        "number_of_heart_surgeries": patient_data.get('number_of_heart_surgeries', 0),
        "num_surgeries_type": patient_data.get('surgery_type', 'CABG'),
        "joint_case": "No",
        "surgery_type": patient_data.get('surgery_type', 'CABG'),
        "surgery_category": patient_data.get('surgery_category', 'Major'),
        "surgery_complexity": patient_data.get('surgery_complexity', 'Medium'),
        "surgery_duration_hours": patient_data.get('surgery_duration_hours', 4.0),
        "surgery_mortality_risk": round(risk_score / 100 * 0.3, 2),
        "typical_recovery_days_surgery": recovery_days,
        "risk_score": risk_score, "risk_level": risk_level, "recovery_days": recovery_days
    }
    
    return record


def add_patient_to_training_dataset(patient_data):
    """Add patient to training dataset and check if retraining is needed"""
    try:
        logger.info("📊 Adding patient data to training dataset...")
        
        # Check if dataset exists
        if not os.path.exists(DATASET_PATH):
            logger.warning(f"Dataset not found at {DATASET_PATH}")
            return
        
        # Load existing dataset
        df = pd.read_csv(DATASET_PATH)
        
        # Prepare patient record
        patient_record = prepare_patient_record_for_training(patient_data)
        
        # Append to dataset
        new_df = pd.concat([df, pd.DataFrame([patient_record])], ignore_index=True)
        new_df.to_csv(DATASET_PATH, index=False)
        
        logger.info(f"✅ Patient data added. Dataset size: {len(new_df)}")
        
        # Log the event
        log_retraining_event("patient_added", len(new_df))
        
        # Check if retraining is needed
        check_and_trigger_retraining()
        
    except Exception as e:
        logger.error(f"❌ Error adding patient to dataset: {str(e)}")


def log_retraining_event(event, dataset_size):
    """Log retraining events"""
    try:
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': event,
            'dataset_size': dataset_size
        }
        
        if os.path.exists(RETRAINING_LOG_PATH):
            log_df = pd.read_csv(RETRAINING_LOG_PATH)
            log_df = pd.concat([log_df, pd.DataFrame([log_entry])], ignore_index=True)
        else:
            log_df = pd.DataFrame([log_entry])
        
        log_df.to_csv(RETRAINING_LOG_PATH, index=False)
    except Exception as e:
        logger.error(f"❌ Error logging event: {str(e)}")


def check_and_trigger_retraining():
    """Check if enough new patients to trigger retraining"""
    try:
        if not os.path.exists(RETRAINING_LOG_PATH):
            return
        
        log_df = pd.read_csv(RETRAINING_LOG_PATH)
        
        # Count patients added since last retrain
        patients_added = log_df[log_df['event'] == 'patient_added'].shape[0]
        retrains_completed = log_df[log_df['event'] == 'retrain_completed'].shape[0]
        patients_since_retrain = patients_added - retrains_completed
        
        if patients_since_retrain >= RETRAIN_THRESHOLD:
            logger.info(f"🔄 Triggering model retraining ({patients_since_retrain} new patients)")
            # Run retraining in background
            asyncio.create_task(retrain_models_async())
        else:
            logger.info(f"⏳ Retraining threshold not reached ({patients_since_retrain}/{RETRAIN_THRESHOLD})")
            
    except Exception as e:
        logger.error(f"❌ Error checking retraining threshold: {str(e)}")


async def retrain_models_async():
    """Retrain models asynchronously"""
    try:
        logger.info("🚀 Starting model retraining...")
        
        # Import and run training
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from ml_models.train_models import main as train_main
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, train_main)
        
        logger.info("✅ Model retraining completed successfully!")
        log_retraining_event("retrain_completed", 0)
        
    except Exception as e:
        logger.error(f"❌ Model retraining failed: {str(e)}")
        log_retraining_event("retrain_failed", 0)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
