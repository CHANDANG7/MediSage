from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import sys
import os
import logging
import google.generativeai as genai
from typing import Dict, Any
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.auth import get_current_user
from backend.models import PredictionRequest
from backend.database import patients_collection
from ml_models.predict import RiskPredictor
from ml_models.nlp_extractor import parse_medical_report
from utils.encryption import DataEncryption

router = APIRouter()

# Initialize predictor and encryption (lazy loading)
model_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'trained_models')
predictor = None
encryption = DataEncryption()
logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
gemini_model = None

def get_predictor():
    """Lazy load predictor only when needed"""
    global predictor
    if predictor is None:
        try:
            logger.info("Loading ML models...")
            predictor = RiskPredictor(model_dir)
            logger.info("✅ ML models loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load models: {str(e)}")
            raise HTTPException(status_code=503, detail="ML models not available. Please train models first.")
    return predictor

def get_gemini_model():
    """Lazy load Gemini model"""
    global gemini_model
    if gemini_model is None:
        model_options = [
            'gemini-2.0-flash-exp',
            'gemini-2.5-pro-preview-03-25',
            'gemini-2.5-flash-preview-05-20',
            'gemini-2.0-pro-exp',
            'gemini-flash-latest',
            'gemini-pro-latest',
            'gemini-2.0-flash-lite',
        ]
        
        for model_name in model_options:
            try:
                model = genai.GenerativeModel(model_name)
                test = model.generate_content(
                    "Hi",
                    generation_config=genai.types.GenerationConfig(max_output_tokens=5)
                )
                logger.info(f"✅ Using Gemini model: {model_name}")
                gemini_model = genai.GenerativeModel(model_name)
                return gemini_model
            except Exception as e:
                logger.warning(f"Model {model_name} not available: {str(e)[:50]}")
                continue
        
        logger.warning("No Gemini models available")
        return None
    return gemini_model

def auto_detect_surgery_complexity(surgery_type: str) -> tuple:
    """Auto-detect surgery category and complexity based on surgery type"""
    surgery_mappings = {
        # Major Surgeries (High Complexity)
        "CABG": {"category": "Major", "complexity": "High"},
        "Valve Replacement": {"category": "Major", "complexity": "High"},
        "Valve Repair": {"category": "Major", "complexity": "High"},
        "Aortic Valve Replacement": {"category": "Major", "complexity": "High"},
        "Mitral Valve Replacement": {"category": "Major", "complexity": "High"},
        "Bypass Surgery": {"category": "Major", "complexity": "High"},
        "Heart Transplant": {"category": "Major", "complexity": "High"},
        "Coronary Artery Bypass Graft": {"category": "Major", "complexity": "High"},
        "Open Heart Surgery": {"category": "Major", "complexity": "High"},
        "Aortic Aneurysm Repair": {"category": "Major", "complexity": "High"},
        "LVAD Implantation": {"category": "Major", "complexity": "High"},
        
        # Intermediate Surgeries (Medium Complexity)
        "Angioplasty": {"category": "Intermediate", "complexity": "Medium"},
        "PCI": {"category": "Intermediate", "complexity": "Medium"},
        "Stent Placement": {"category": "Intermediate", "complexity": "Medium"},
        "Coronary Stenting": {"category": "Intermediate", "complexity": "Medium"},
        "Ablation": {"category": "Intermediate", "complexity": "Medium"},
        "Cardiac Ablation": {"category": "Intermediate", "complexity": "Medium"},
        "ASD Closure": {"category": "Intermediate", "complexity": "Medium"},
        "VSD Closure": {"category": "Intermediate", "complexity": "Medium"},
        "PDA Closure": {"category": "Intermediate", "complexity": "Medium"},
        "TAVI": {"category": "Intermediate", "complexity": "Medium"},
        "TAVR": {"category": "Intermediate", "complexity": "Medium"},
        "MitraClip": {"category": "Intermediate", "complexity": "Medium"},
        
        # Minor Surgeries (Low Complexity)
        "Pacemaker Implantation": {"category": "Minor", "complexity": "Low"},
        "Pacemaker": {"category": "Minor", "complexity": "Low"},
        "ICD Implantation": {"category": "Minor", "complexity": "Low"},
        "Defibrillator Implantation": {"category": "Minor", "complexity": "Low"},
        "CRT Device Implantation": {"category": "Minor", "complexity": "Low"},
        "Cardiac Catheterization": {"category": "Minor", "complexity": "Low"},
        "Diagnostic Catheterization": {"category": "Minor", "complexity": "Low"},
        "Cardiac Monitoring Device": {"category": "Minor", "complexity": "Low"},
        "Loop Recorder Implantation": {"category": "Minor", "complexity": "Low"},
    }
    
    result = surgery_mappings.get(surgery_type, {"category": "Major", "complexity": "Medium"})
    return result["category"], result["complexity"]

def analyze_medical_report_with_gemini(report_text: str) -> Dict[str, Any]:
    """Analyze medical report using Gemini"""
    model = get_gemini_model()
    if not model:
        return {
            "summary": "Gemini analysis unavailable. Using NLP extraction only.",
            "extracted_risk_factors": [],
            "success": False
        }
    
    prompt = f"""You are an expert medical data analyst. Analyze the following medical report and extract all important factors that could affect post-surgery risk prediction.

Medical Report:
{report_text}

**TASK**: Extract and summarize the following information:

1. **Patient Demographics**: Age, sex, height, weight, BMI
2. **Vital Signs**: Blood pressure, pulse rate, heart rate
3. **Cardiac Conditions**: Ejection fraction, cardiac rhythm, NYHA class, type of heart disease
4. **Medical Conditions**: Hypertension, diabetes, heart failure, atrial fibrillation, COVID-19 history
5. **Risk Factors**: Smoking, alcohol, exercise, family history, obesity
6. **Lab Values**: Blood glucose, cholesterol, kidney/liver function
7. **Medications**: Current medications
8. **Critical Findings**: Abnormal findings, pre-existing complications, recent health events

**IMPORTANT**: 
- Provide a concise summary (max 500 words)
- Highlight **critical risk factors** that could impact surgery
- Use bullet points for clarity
- If not mentioned, state "Not mentioned"

Provide your analysis:"""
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                top_p=0.95,
                max_output_tokens=2048,
            )
        )
        
        return {
            "summary": response.text,
            "extracted_risk_factors": [],
            "success": True
        }
    except Exception as e:
        logger.error(f"Gemini analysis error: {str(e)}")
        return {
            "summary": "Analysis unavailable.",
            "extracted_risk_factors": [],
            "success": False,
            "error": str(e)
        }

def predict_surgery_consequences(risk_data: Dict[str, Any]) -> str:
    """Predict consequences using Gemini"""
    model = get_gemini_model()
    if not model:
        risk_level = risk_data.get('risk_level', 'Unknown')
        risk_score = risk_data.get('risk_score', 0)
        recovery_days = risk_data.get('recovery_days', 0)
        return f"""**Risk Assessment Summary**

Based on your {risk_level} risk level (score: {risk_score}/100):

**Expected Recovery**: {recovery_days} days

**Important**: Please consult with your cardiac surgeon to discuss your specific risk factors, personalized surgery recommendations, and post-operative care requirements.
"""
    
    risk_level = risk_data.get('risk_level', 'Unknown')
    risk_score = risk_data.get('risk_score', 0)
    recovery_days = risk_data.get('recovery_days', 0)
    patient_data = risk_data.get('patient_data', {})
    report_summary = risk_data.get('report_summary', '')
    
    # Format patient info
    info_parts = []
    if patient_data.get('age'):
        info_parts.append(f"- Age: {patient_data['age']} years")
    if patient_data.get('sex'):
        info_parts.append(f"- Sex: {patient_data['sex']}")
    if patient_data.get('surgery_type'):
        info_parts.append(f"- Planned Surgery: {patient_data['surgery_type']}")
    
    conditions = []
    if patient_data.get('hypertension'): conditions.append("Hypertension")
    if patient_data.get('diabetes'): conditions.append("Diabetes")
    if patient_data.get('heart_failure'): conditions.append("Heart Failure")
    if patient_data.get('atrial_fibrillation'): conditions.append("Atrial Fibrillation")
    if conditions:
        info_parts.append(f"- Medical Conditions: {', '.join(conditions)}")
    
    if patient_data.get('smoking') == 'Yes':
        info_parts.append("- Smoker: Yes")
    if patient_data.get('pre_surgery_notes'):
        info_parts.append(f"- Pre-surgery Notes: {patient_data['pre_surgery_notes']}")
    if patient_data.get('other_risk_factors'):
        info_parts.append(f"- Other Risk Factors: {', '.join(patient_data.get('other_risk_factors', []))}")
    
    patient_info = '\n'.join(info_parts) if info_parts else "Limited patient information available"
    
    # Build specific risk factors list
    specific_risks = []
    if patient_data.get('ejection_fraction', 55) < 40:
        specific_risks.append(f"Low ejection fraction ({patient_data.get('ejection_fraction')}%) - heart pumping weakness")
    if patient_data.get('age', 0) > 70:
        specific_risks.append(f"Advanced age ({patient_data.get('age')} years) - slower healing")
    if patient_data.get('diabetes'):
        specific_risks.append("Diabetes - increased infection risk and slower wound healing")
    if patient_data.get('hypertension'):
        specific_risks.append("High blood pressure - bleeding and stroke risk")
    if patient_data.get('heart_failure'):
        specific_risks.append("Heart failure - reduced cardiac reserve")
    if patient_data.get('smoking') == 'Yes':
        specific_risks.append("Active smoking - lung complications and poor healing")
    if patient_data.get('number_of_heart_surgeries', 0) > 0:
        specific_risks.append(f"Previous heart surgeries ({patient_data.get('number_of_heart_surgeries')}) - scar tissue complications")
    
    risk_factors_text = "\n".join([f"- {risk}" for risk in specific_risks]) if specific_risks else "- No major risk factors identified"
    
    prompt = f"""You are a cardiac surgeon giving DIRECT, SPECIFIC advice to this patient about their surgery even after they got to know what is the percentage of level of risk the surgery involves.

**PATIENT'S ACTUAL SITUATION**:
- Risk Level: **{risk_level}** (Score: {risk_score}/100)
- Expected Recovery: **{recovery_days} days**
- Surgery: {patient_data.get('surgery_type', 'Cardiac surgery')}
- Age: {patient_data.get('age', 'Unknown')} years, Sex: {patient_data.get('sex', 'Unknown')}

**THEIR SPECIFIC RISK FACTORS**:
{risk_factors_text}

**THEIR MEDICAL CONDITIONS**:
{patient_info}

{f'**FROM THEIR MEDICAL REPORT**:\n{report_summary}' if report_summary else ''}

**YOUR TASK**: Give DIRECT, SPECIFIC consequences for THIS patient. Be concrete and personalized.

**Format your response EXACTLY like this**:

### What This Risk Level Means For You
[1-2 sentences explaining what {risk_level} risk ({risk_score}%) means specifically for them]

### If You Proceed With Surgery - What Will Happen:

**Immediate Risks (First 24-48 hours):**
- [Specific risk based on their conditions]
- [Another specific risk]
- [Probability if possible, e.g., "15-20% chance of..."]

**Recovery Period (Next {recovery_days} days):**
- [What they'll experience day-by-day]
- [Specific challenges based on their diabetes/age/etc.]
- [Expected milestones]

**Your Specific Concerns:**
[Address each of their risk factors directly - diabetes, age, EF, etc.]

### What You Must Do Before Surgery:
1. [Specific action based on their conditions]
2. [Another specific action]
3. [Third specific action]

### Bottom Line - Should You Do This Surgery?
[Direct recommendation considering their risk level and factors]

**CRITICAL RULES**:
- Be SPECIFIC to their age, conditions, and risk factors
- Use actual numbers from their data
- No generic advice - everything must be personalized
- Be direct and honest
- Keep under 500 words
- Use simple language

Provide your analysis:"""
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                top_p=0.95,
                max_output_tokens=2048,
            )
        )
        return response.text
    except Exception as e:
        logger.error(f"Consequence prediction error: {str(e)}")
        return f"""**Risk Assessment Summary**

Based on your {risk_level} risk level (score: {risk_score}/100):

**Expected Recovery**: {recovery_days} days

**Important**: Please consult with your cardiac surgeon to discuss your specific risk factors and personalized recommendations.
"""

@router.post("/predict-risk")
async def predict_risk(
    request: PredictionRequest,
    current_user: str = Depends(get_current_user)
):
    predictor = get_predictor()  # Lazy load
    
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
            "previous_surgeries",
            "pre_surgery_notes"  # Added new field
        ]
        
        for field in sensitive_fields:
            if patient.get(field):
                try:
                    patient[field] = encryption.decrypt(patient[field])
                except Exception as e:
                    logger.warning(f"Failed to decrypt {field}: {str(e)}")
                    pass
        
        # Auto-detect surgery complexity based on surgery type
        surgery_type = patient.get("surgery_type", "CABG")
        category, complexity = auto_detect_surgery_complexity(surgery_type)
        
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
            
            # Surgery Details (4 features) - Auto-detected
            "surgery_type": surgery_type,
            "surgery_category": category,
            "surgery_complexity": complexity,
            "number_of_heart_surgeries": patient.get("number_of_heart_surgeries", 0),
            
            # Medical History (decrypted)
            "medical_history": patient.get("medical_history", ""),
            "chronic_conditions": patient.get("chronic_conditions", []),
            "medications": patient.get("medications", []),
            "allergies": patient.get("allergies", []),
            "previous_surgeries": patient.get("previous_surgeries", []),
            
            # Pre-surgery risk factors
            "pre_surgery_notes": patient.get("pre_surgery_notes", ""),
            "other_risk_factors": patient.get("other_risk_factors", [])
        }
    else:
        # Auto-detect surgery complexity for manual input
        if patient_data and patient_data.get("surgery_type"):
            category, complexity = auto_detect_surgery_complexity(patient_data["surgery_type"])
            patient_data["surgery_category"] = category
            patient_data["surgery_complexity"] = complexity
    
    if not patient_data:
        raise HTTPException(status_code=400, detail="No patient data provided")
    
    # Make prediction with all features
    result = predictor.predict(patient_data)
    
    # Add consequence prediction using Gemini
    try:
        consequence_analysis = predict_surgery_consequences({
            'risk_level': result['risk_level'],
            'risk_score': result['risk_score'],
            'recovery_days': result['recovery_days'],
            'patient_data': patient_data
        })
        result['consequences'] = consequence_analysis
    except Exception as e:
        logger.warning(f"Failed to generate consequences: {str(e)}")
        result['consequences'] = "Consequence analysis unavailable."
    
    return result

@router.post("/extract-from-report")
async def extract_from_report(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):
    """Extract features from medical report and make risk prediction"""
    
    predictor = get_predictor()  # Lazy load
    
    # Read file
    file_content = await file.read()
    
    # Extract features from report using NLP
    features, text = parse_medical_report(file_content, file_type='pdf')
    
    # Auto-detect surgery complexity if surgery type is extracted
    if features.get("surgery_type"):
        category, complexity = auto_detect_surgery_complexity(features["surgery_type"])
        features["surgery_category"] = category
        features["surgery_complexity"] = complexity
    
    # Count extracted features
    extracted_count = sum(1 for v in features.values() if v is not None and v != '' and v != [] and v != 0)
    
    logger.info(f"Extracted {extracted_count} features from medical report")
    
    # Analyze report with Gemini for comprehensive summary
    gemini_analysis = analyze_medical_report_with_gemini(text)
    
    # Make prediction using extracted features
    try:
        prediction_result = predictor.predict(features)
        
        # Add consequence prediction using Gemini
        try:
            consequence_analysis = predict_surgery_consequences({
                'risk_level': prediction_result['risk_level'],
                'risk_score': prediction_result['risk_score'],
                'recovery_days': prediction_result['recovery_days'],
                'patient_data': features,
                'report_summary': gemini_analysis.get('summary', '')
            })
            prediction_result['consequences'] = consequence_analysis
        except Exception as e:
            logger.warning(f"Failed to generate consequences: {str(e)}")
            prediction_result['consequences'] = "Consequence analysis unavailable."
        
        return {
            "success": True,
            "extracted_features": features,
            "extracted_text": text[:500],  # First 500 chars for reference
            "features_count": extracted_count,
            
            # Gemini analysis
            "gemini_summary": gemini_analysis.get('summary', 'Analysis unavailable'),
            "gemini_success": gemini_analysis.get('success', False),
            
            # Include prediction results
            "risk_level": prediction_result["risk_level"],
            "risk_score": prediction_result["risk_score"],
            "recovery_days": prediction_result["recovery_days"],
            "risk_probabilities": prediction_result.get("risk_probabilities", {}),
            "top_features": prediction_result.get("top_features", []),
            "consequences": prediction_result.get("consequences", "")
        }
    
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to make prediction: {str(e)}. Extracted {extracted_count} features."
        )
