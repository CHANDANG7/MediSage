import re
import spacy
from PyPDF2 import PdfReader
import io


# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except:
    print("⚠️ spaCy model not found. Please run: python -m spacy download en_core_web_sm")
    nlp = None


def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file"""
    try:
        pdf_reader = PdfReader(io.BytesIO(pdf_file))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return ""


def extract_medical_features(text):
    """Extract 15+ medical features from text using NLP and regex patterns"""
    
    # Initialize all features with defaults (30+ features)
    features = {
        # Demographics
        'age': None,
        'sex': None,
        'height_cm': None,
        'weight_kg': None,
        'bmi': None,
        'residence': 'Urban',
        
        # Vital Signs
        'systolic_bp': None,
        'diastolic_bp': None,
        'pulse_rate': None,
        
        # Cardiac Health
        'ejection_fraction': None,
        'cardiac_rhythm': 'Normal',
        'nyha_class': 'I',
        'type_of_heart_disease': None,
        
        # Medical Conditions (binary)
        'hypertension': 0,
        'diabetes': 0,
        'heart_failure': 0,
        'atrial_fibrillation': 0,
        'Affected_by_Covid': 0,
        'family_history': 0,
        
        # Lifestyle
        'smoking': 'No',
        'smoking_history': 'Never',
        'alcohol_consumption': 'None',
        'exercise_frequency': 'Regular',
        
        # Surgery Details
        'surgery_type': None,
        'surgery_category': 'Major',
        'surgery_complexity': 'Medium',
        'number_of_heart_surgeries': 0,
        
        # Medical History
        'medical_history': '',
        'chronic_conditions': [],
        'medications': [],
        'allergies': []
    }
    
    text_lower = text.lower()
    
    # === DEMOGRAPHICS ===
    # Extract age
    age_patterns = [r'age[:\s]+(\d{1,3})', r'(\d{1,3})\s*y(?:ear)?s?\s*old', r'(\d{1,3})\s*yo']
    for pattern in age_patterns:
        age_match = re.search(pattern, text_lower)
        if age_match:
            features['age'] = int(age_match.group(1))
            break
    
    # Extract gender
    if 'male' in text_lower and 'female' not in text_lower:
        features['sex'] = 'Male'
    elif 'female' in text_lower:
        features['sex'] = 'Female'
    
    # Extract height
    height_patterns = [r'height[:\s]+(\d{2,3})\s*cm', r'(\d{2,3})\s*cm\s*tall']
    for pattern in height_patterns:
        height_match = re.search(pattern, text_lower)
        if height_match:
            features['height_cm'] = int(height_match.group(1))
            break
    
    # Extract weight
    weight_patterns = [r'weight[:\s]+(\d{2,3})\s*kg', r'(\d{2,3})\s*kg\s*weight']
    for pattern in weight_patterns:
        weight_match = re.search(pattern, text_lower)
        if weight_match:
            features['weight_kg'] = int(weight_match.group(1))
            break
    
    # Extract BMI
    bmi_pattern = r'bmi[:\s]+(\d{1,3}\.?\d*)'
    bmi_match = re.search(bmi_pattern, text_lower)
    if bmi_match:
        features['bmi'] = float(bmi_match.group(1))
    elif features['height_cm'] and features['weight_kg']:
        features['bmi'] = features['weight_kg'] / ((features['height_cm']/100) ** 2)
    
    # === VITAL SIGNS ===
    # Extract Blood Pressure
    bp_patterns = [r'bp[:\s]*(\d{2,3})\s*/\s*(\d{2,3})', r'(\d{2,3})\s*/\s*(\d{2,3})\s*mmhg']
    for pattern in bp_patterns:
        bp_match = re.search(pattern, text_lower)
        if bp_match:
            features['systolic_bp'] = int(bp_match.group(1))
            features['diastolic_bp'] = int(bp_match.group(2))
            break
    
    # Extract Pulse/Heart Rate
    pulse_patterns = [r'pulse[:\s]+(\d{2,3})', r'heart rate[:\s]+(\d{2,3})', r'hr[:\s]+(\d{2,3})\s*bpm']
    for pattern in pulse_patterns:
        pulse_match = re.search(pattern, text_lower)
        if pulse_match:
            features['pulse_rate'] = int(pulse_match.group(1))
            break
    
    # === CARDIAC HEALTH ===
    # Extract Ejection Fraction
    ef_patterns = [r'ejection fraction[:\s]+(\d{1,3})', r'ef[:\s]+(\d{1,3})\s*%', r'lvef[:\s]+(\d{1,3})']
    for pattern in ef_patterns:
        ef_match = re.search(pattern, text_lower)
        if ef_match:
            features['ejection_fraction'] = int(ef_match.group(1))
            break
    
    # Extract Cardiac Rhythm
    if any(word in text_lower for word in ['atrial fibrillation', 'afib', 'a-fib']):
        features['cardiac_rhythm'] = 'AFib'
        features['atrial_fibrillation'] = 1
    elif 'flutter' in text_lower:
        features['cardiac_rhythm'] = 'Flutter'
    elif any(word in text_lower for word in ['normal sinus', 'regular rhythm', 'normal rhythm']):
        features['cardiac_rhythm'] = 'Normal'
    
    # Extract NYHA Class
    nyha_pattern = r'nyha\s*(?:class)?\s*([i1-4]+)'
    nyha_match = re.search(nyha_pattern, text_lower)
    if nyha_match:
        nyha_value = nyha_match.group(1).upper()
        if nyha_value in ['I', 'II', 'III', 'IV', '1', '2', '3', '4']:
            features['nyha_class'] = {'1': 'I', '2': 'II', '3': 'III', '4': 'IV'}.get(nyha_value, nyha_value)
    
    # === MEDICAL CONDITIONS ===
    # Hypertension
    if any(word in text_lower for word in ['hypertension', 'high blood pressure', 'htn']):
        features['hypertension'] = 1
    
    # Diabetes
    if any(word in text_lower for word in ['diabetes', 'diabetic', 'dm', 'type 2 diabetes', 'type 1 diabetes']):
        features['diabetes'] = 1
    
    # Heart Failure
    if any(word in text_lower for word in ['heart failure', 'chf', 'congestive heart failure']):
        features['heart_failure'] = 1
    
    # Atrial Fibrillation (already set above)
    
    # COVID-19
    if any(word in text_lower for word in ['covid', 'covid-19', 'coronavirus', 'sars-cov-2']):
        features['Affected_by_Covid'] = 1
    
    # Family History
    if any(word in text_lower for word in ['family history', 'familial', 'hereditary']):
        features['family_history'] = 1
    
    # === LIFESTYLE ===
    # Smoking
    if any(word in text_lower for word in ['current smoker', 'active smoker']):
        features['smoking'] = 'Yes'
        features['smoking_history'] = 'Current'
    elif any(word in text_lower for word in ['former smoker', 'ex-smoker', 'quit smoking']):
        features['smoking'] = 'No'
        features['smoking_history'] = 'Former'
    elif any(word in text_lower for word in ['smoker', 'smoking']):
        features['smoking'] = 'Yes'
        features['smoking_history'] = 'Current'
    elif any(word in text_lower for word in ['non-smoker', 'never smoked', 'non smoker']):
        features['smoking'] = 'No'
        features['smoking_history'] = 'Never'
    
    # Alcohol
    if any(word in text_lower for word in ['heavy drinker', 'alcoholic', 'excessive alcohol']):
        features['alcohol_consumption'] = 'High'
    elif any(word in text_lower for word in ['moderate drinker', 'social drinker', 'occasional alcohol']):
        features['alcohol_consumption'] = 'Moderate'
    elif any(word in text_lower for word in ['non-drinker', 'no alcohol', 'abstinent']):
        features['alcohol_consumption'] = 'None'
    
    # Exercise
    if any(word in text_lower for word in ['sedentary', 'no exercise', 'inactive']):
        features['exercise_frequency'] = 'None'
    elif any(word in text_lower for word in ['occasional exercise', 'rarely exercises']):
        features['exercise_frequency'] = 'Rare'
    elif any(word in text_lower for word in ['regular exercise', 'active', 'exercises regularly']):
        features['exercise_frequency'] = 'Regular'
    
    # === HEART DISEASE TYPE ===
    if 'coronary artery disease' in text_lower or 'cad' in text_lower:
        features['type_of_heart_disease'] = 'CAD'
    elif 'valve' in text_lower and 'disease' in text_lower:
        features['type_of_heart_disease'] = 'Valve'
    elif 'arrhythmia' in text_lower:
        features['type_of_heart_disease'] = 'Arrhythmia'
    elif 'heart failure' in text_lower or 'chf' in text_lower:
        features['type_of_heart_disease'] = 'CHF'
    
    # === SURGERY DETAILS ===
    # Surgery type
    if 'cabg' in text_lower or 'coronary artery bypass' in text_lower:
        features['surgery_type'] = 'CABG'
    elif 'valve replacement' in text_lower:
        features['surgery_type'] = 'Valve Replacement'
    elif 'bypass' in text_lower and 'cabg' not in text_lower:
        features['surgery_type'] = 'Bypass'
    elif 'pacemaker' in text_lower:
        features['surgery_type'] = 'Pacemaker'
    
    # Surgery category
    if any(word in text_lower for word in ['major surgery', 'complex surgery']):
        features['surgery_category'] = 'Major'
    elif any(word in text_lower for word in ['minor surgery', 'simple surgery']):
        features['surgery_category'] = 'Minor'
    elif 'intermediate' in text_lower:
        features['surgery_category'] = 'Intermediate'
    
    # Number of previous surgeries
    prev_surgery_patterns = [r'(\d+)\s*previous\s*(?:heart\s*)?surger(?:y|ies)', 
                            r'(\d+)\s*prior\s*(?:heart\s*)?surger(?:y|ies)']
    for pattern in prev_surgery_patterns:
        match = re.search(pattern, text_lower)
        if match:
            features['number_of_heart_surgeries'] = int(match.group(1))
            break
    
    # === MEDICAL HISTORY & MEDICATIONS ===
    # Extract medications
    medication_keywords = ['aspirin', 'clopidogrel', 'metoprolol', 'lisinopril', 'atorvastatin', 
                          'warfarin', 'insulin', 'metformin', 'furosemide', 'digoxin']
    found_meds = [med for med in medication_keywords if med in text_lower]
    if found_meds:
        features['medications'] = found_meds
    
    # Extract chronic conditions
    chronic_keywords = ['hypertension', 'diabetes', 'copd', 'asthma', 'kidney disease', 
                       'liver disease', 'stroke', 'heart attack', 'mi']
    found_conditions = [cond for cond in chronic_keywords if cond in text_lower]
    if found_conditions:
        features['chronic_conditions'] = found_conditions
    
    # Extract allergies
    allergy_pattern = r'allerg(?:y|ies)[:\s]+([^.\n]+)'
    allergy_match = re.search(allergy_pattern, text_lower)
    if allergy_match:
        allergies_text = allergy_match.group(1)
        if 'none' not in allergies_text and 'nkda' not in allergies_text:
            features['allergies'] = [allergies_text.strip()]
    
    return features


def parse_medical_report(file_content, file_type='pdf'):
    """Parse medical report and extract features"""
    
    if file_type == 'pdf':
        text = extract_text_from_pdf(file_content)
    else:
        text = file_content.decode('utf-8') if isinstance(file_content, bytes) else file_content
    
    features = extract_medical_features(text)
    
    return features, text
