from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.auth import get_current_user
from backend.models import PredictionRequest
from backend.database import patients_collection
from ml_models.predict import RiskPredictor
from ml_models.nlp_extractor import parse_medical_report
from utils.encryption import DataEncryption

router = APIRouter()

# Initialize predictor and encryption
model_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'trained_models')
predictor = None
encryption = DataEncryption()
logger = logging.getLogger(__name__)

try:
    predictor = RiskPredictor(model_dir)
except:
    print("⚠️ Models not trained yet. Please run ml_models/train_models.py")

@router.post("/predict-risk")
async def predict_risk(
    request: PredictionRequest,
    current_user: str = Depends(get_current_user)
):
    if predictor is None:
        raise HTTPException(status_code=503, detail="ML models not available. Please train models first.")
    
    patient_data = request.patient_data
    
    # If use_profile is True, fetch patient data from database
    if request.use_profile:
        patient = await patients_collection.find_one({"email": current_user})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient profile not found")
        
        # Decrypt sensitive fields from profile
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
                    logger.warning(f"Failed to decrypt {field}: {str(e)}")
                    pass
        
        # Convert to dict and extract all relevant features (15+ features)
        patient_data = {
            # Demographics (4 features)
            "age": patient.get("age"),
            "sex": patient.get("sex"),
            "height_cm": patient.get("height_cm"),
            "weight_kg": patient.get("weight_kg"),
            "bmi": patient.get("weight_kg", 70) / ((patient.get("height_cm", 170)/100) ** 2) if patient.get("height_cm") and patient.get("weight_kg") else 25,
            "residence": patient.get("residence", "Urban"),
            
            # Vital Signs (3 features)
            "systolic_bp": patient.get("systolic_bp", 120),
            "diastolic_bp": patient.get("diastolic_bp", 80),
            "pulse_rate": patient.get("pulse_rate", 75),
            
            # Cardiac Health (4 features)
            "ejection_fraction": patient.get("ejection_fraction", 55),
            "cardiac_rhythm": patient.get("cardiac_rhythm", "Normal"),
            "nyha_class": patient.get("nyha_class", "I"),
            "type_of_heart_disease": patient.get("type_of_heart_disease", "None"),
            
            # Medical Conditions (6 features)
            "hypertension": patient.get("hypertension", 0),
            "diabetes": patient.get("diabetes", 0),
            "heart_failure": patient.get("heart_failure", 0),
            "atrial_fibrillation": patient.get("atrial_fibrillation", 0),
            "Affected_by_Covid": patient.get("Affected_by_Covid", 0),
            "family_history": patient.get("family_history", 0),
            
            # Lifestyle (4 features)
            "smoking": patient.get("smoking", "No"),
            "smoking_history": patient.get("smoking_history", "Never"),
            "alcohol_consumption": patient.get("alcohol_consumption", "None"),
            "exercise_frequency": patient.get("exercise_frequency", "Regular"),
            
            # Surgery Details (4 features)
            "surgery_type": patient.get("surgery_type", "CABG"),
            "surgery_category": patient.get("surgery_category", "Major"),
            "surgery_complexity": patient.get("surgery_complexity", "Medium"),
            "number_of_heart_surgeries": patient.get("number_of_heart_surgeries", 0),
            
            # Medical History (decrypted)
            "medical_history": patient.get("medical_history", ""),
            "chronic_conditions": patient.get("chronic_conditions", []),
            "medications": patient.get("medications", []),
            "allergies": patient.get("allergies", []),
            "previous_surgeries": patient.get("previous_surgeries", [])
        }
    
    if not patient_data:
        raise HTTPException(status_code=400, detail="No patient data provided")
    
    # Make prediction with all features
    result = predictor.predict(patient_data)
    
    return result

@router.post("/extract-from-report")
async def extract_from_report(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):
    """Extract features from medical report and make risk prediction"""
    
    if predictor is None:
        raise HTTPException(status_code=503, detail="ML models not available. Please train models first.")
    
    # Read file
    file_content = await file.read()
    
    # Extract features from report using NLP
    features, text = parse_medical_report(file_content, file_type='pdf')
    
    # Count extracted features
    extracted_count = sum(1 for v in features.values() if v is not None and v != '' and v != [] and v != 0)
    
    logger.info(f"Extracted {extracted_count} features from medical report")
    
    # Make prediction using extracted features
    try:
        prediction_result = predictor.predict(features)
        
        return {
            "success": True,
            "extracted_features": features,
            "extracted_text": text[:500],  # First 500 chars for reference
            "features_count": extracted_count,
            
            # Include prediction results
            "risk_level": prediction_result["risk_level"],
            "risk_score": prediction_result["risk_score"],
            "recovery_days": prediction_result["recovery_days"],
            "risk_probabilities": prediction_result.get("risk_probabilities", {}),
            "top_features": prediction_result.get("top_features", [])
        }
    
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to make prediction: {str(e)}. Extracted {extracted_count} features."
        )
