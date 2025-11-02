import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Configuration
NUM_PATIENTS = 5000  # Number of patients to generate

# Define surgery types with their characteristics
SURGERY_TYPES = {
    # Major Surgeries (High Complexity)
    "CABG": {"category": "Major", "complexity": "High", "duration": (4, 8), "base_risk": 0.12, "recovery": (14, 30)},
    "Valve Replacement": {"category": "Major", "complexity": "High", "duration": (3, 6), "base_risk": 0.15, "recovery": (12, 25)},
    "Valve Repair": {"category": "Major", "complexity": "High", "duration": (3, 6), "base_risk": 0.13, "recovery": (12, 25)},
    "Aortic Valve Replacement": {"category": "Major", "complexity": "High", "duration": (3, 6), "base_risk": 0.16, "recovery": (14, 28)},
    "Mitral Valve Replacement": {"category": "Major", "complexity": "High", "duration": (3, 6), "base_risk": 0.14, "recovery": (14, 28)},
    "Bypass Surgery": {"category": "Major", "complexity": "High", "duration": (4, 8), "base_risk": 0.12, "recovery": (14, 30)},
    "Heart Transplant": {"category": "Major", "complexity": "High", "duration": (6, 12), "base_risk": 0.25, "recovery": (30, 90)},
    "Coronary Artery Bypass Graft": {"category": "Major", "complexity": "High", "duration": (4, 8), "base_risk": 0.12, "recovery": (14, 30)},
    "Open Heart Surgery": {"category": "Major", "complexity": "High", "duration": (4, 10), "base_risk": 0.18, "recovery": (20, 40)},
    "Aortic Aneurysm Repair": {"category": "Major", "complexity": "High", "duration": (4, 8), "base_risk": 0.20, "recovery": (21, 45)},
    "LVAD Implantation": {"category": "Major", "complexity": "High", "duration": (4, 8), "base_risk": 0.22, "recovery": (28, 60)},
    
    # Intermediate Surgeries (Medium Complexity)
    "Angioplasty": {"category": "Intermediate", "complexity": "Medium", "duration": (1, 3), "base_risk": 0.05, "recovery": (3, 7)},
    "PCI": {"category": "Intermediate", "complexity": "Medium", "duration": (1, 3), "base_risk": 0.05, "recovery": (3, 7)},
    "Stent Placement": {"category": "Intermediate", "complexity": "Medium", "duration": (1, 3), "base_risk": 0.06, "recovery": (3, 7)},
    "Coronary Stenting": {"category": "Intermediate", "complexity": "Medium", "duration": (1, 3), "base_risk": 0.06, "recovery": (3, 7)},
    "Ablation": {"category": "Intermediate", "complexity": "Medium", "duration": (2, 4), "base_risk": 0.07, "recovery": (5, 10)},
    "Cardiac Ablation": {"category": "Intermediate", "complexity": "Medium", "duration": (2, 4), "base_risk": 0.07, "recovery": (5, 10)},
    "ASD Closure": {"category": "Intermediate", "complexity": "Medium", "duration": (2, 4), "base_risk": 0.08, "recovery": (7, 14)},
    "VSD Closure": {"category": "Intermediate", "complexity": "Medium", "duration": (2, 4), "base_risk": 0.08, "recovery": (7, 14)},
    "PDA Closure": {"category": "Intermediate", "complexity": "Medium", "duration": (1, 3), "base_risk": 0.07, "recovery": (5, 10)},
    "TAVI": {"category": "Intermediate", "complexity": "Medium", "duration": (2, 4), "base_risk": 0.09, "recovery": (7, 14)},
    "TAVR": {"category": "Intermediate", "complexity": "Medium", "duration": (2, 4), "base_risk": 0.09, "recovery": (7, 14)},
    "MitraClip": {"category": "Intermediate", "complexity": "Medium", "duration": (2, 3), "base_risk": 0.08, "recovery": (5, 10)},
    
    # Minor Surgeries (Low Complexity)
    "Pacemaker Implantation": {"category": "Minor", "complexity": "Low", "duration": (1, 2), "base_risk": 0.03, "recovery": (2, 5)},
    "Pacemaker": {"category": "Minor", "complexity": "Low", "duration": (1, 2), "base_risk": 0.03, "recovery": (2, 5)},
    "ICD Implantation": {"category": "Minor", "complexity": "Low", "duration": (1, 2), "base_risk": 0.04, "recovery": (3, 7)},
    "Defibrillator Implantation": {"category": "Minor", "complexity": "Low", "duration": (1, 2), "base_risk": 0.04, "recovery": (3, 7)},
    "CRT Device Implantation": {"category": "Minor", "complexity": "Low", "duration": (1, 2), "base_risk": 0.04, "recovery": (3, 7)},
    "Cardiac Catheterization": {"category": "Minor", "complexity": "Low", "duration": (0.5, 2), "base_risk": 0.02, "recovery": (1, 3)},
    "Diagnostic Catheterization": {"category": "Minor", "complexity": "Low", "duration": (0.5, 2), "base_risk": 0.02, "recovery": (1, 3)},
    "Cardiac Monitoring Device": {"category": "Minor", "complexity": "Low", "duration": (0.5, 1), "base_risk": 0.02, "recovery": (1, 2)},
    "Loop Recorder Implantation": {"category": "Minor", "complexity": "Low", "duration": (0.5, 1), "base_risk": 0.02, "recovery": (1, 2)},
}

def generate_patient_data():
    """Generate synthetic patient data for cardiac surgery risk prediction"""
    
    data = []
    
    for i in range(NUM_PATIENTS):
        patient_id = f"P{i+1:04d}"
        
        # Basic Demographics
        age = int(np.random.normal(60, 15))
        age = max(18, min(95, age))  # Clamp between 18-95
        
        if age < 40:
            age_group = "Young"
        elif age < 65:
            age_group = "Middle"
        else:
            age_group = "Old"
        
        sex = random.choice(["Male", "Female"])
        blood_group = random.choice(["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
        residence = random.choice(["Urban", "Rural", "Semi-Urban"])
        occupation = random.choice(["Teacher", "Engineer", "Doctor", "Business", "Retired", "Other"])
        marital_status = random.choice(["Single", "Married", "Divorced", "Widowed"])
        education_level = random.choice(["High School", "Graduate", "Postgraduate", "PhD"])
        
        # Physical Measurements
        height_cm = np.random.normal(170, 10)
        height_cm = max(150, min(200, height_cm))
        
        weight_kg = np.random.normal(75, 15)
        weight_kg = max(45, min(150, weight_kg))
        
        bmi = weight_kg / ((height_cm / 100) ** 2)
        
        if bmi < 18.5:
            bmi_category = "Underweight"
        elif bmi < 25:
            bmi_category = "Normal"
        elif bmi < 30:
            bmi_category = "Overweight"
        else:
            bmi_category = "Obese"
        
        # Lifestyle Factors
        smoking = random.choice(["Yes", "No"])
        smoking_history = random.choice(["Never", "Former", "Current"])
        alcohol_consumption = random.choice(["None", "Moderate", "High"])
        exercise_frequency = random.choice(["None", "Rare", "Regular"])
        Affected_by_Covid = random.choice([0, 1])
        
        # Family History
        family_history = random.choice([0, 1])
        family_history_detail = random.choice(["None", "Hypertension", "Diabetes", "Heart Disease"]) if family_history else "None"
        
        # Vital Signs
        systolic_bp = int(np.random.normal(130, 20))
        systolic_bp = max(90, min(200, systolic_bp))
        
        diastolic_bp = int(np.random.normal(80, 12))
        diastolic_bp = max(60, min(120, diastolic_bp))
        
        mean_arterial_pressure = round((systolic_bp + 2 * diastolic_bp) / 3, 1)
        
        pulse_rate = int(np.random.normal(75, 15))
        pulse_rate = max(50, min(120, pulse_rate))
        
        # Heart Disease Details
        type_of_heart_disease = random.choice(["None", "CAD", "Valve", "Arrhythmia", "CHF"])
        
        ejection_fraction = int(np.random.normal(55, 15))
        ejection_fraction = max(20, min(75, ejection_fraction))
        
        if ejection_fraction < 40:
            lvef_category = "Reduced"
        elif ejection_fraction < 50:
            lvef_category = "Mildly Reduced"
        else:
            lvef_category = "Preserved"
        
        nyha_class = random.choice(["I", "II", "III", "IV"])
        cardiac_rhythm = random.choice(["Normal", "AFib", "Flutter"])
        
        # Medical Conditions
        hypertension = 1 if systolic_bp > 140 or diastolic_bp > 90 else random.choice([0, 1])
        diabetes = random.choice([0, 1])
        heart_failure = 1 if ejection_fraction < 40 else random.choice([0, 0, 1])
        atrial_fibrillation = 1 if cardiac_rhythm == "AFib" else 0
        
        # Surgery Details
        surgery_type = random.choice(list(SURGERY_TYPES.keys()))
        surgery_info = SURGERY_TYPES[surgery_type]
        
        surgery_category = surgery_info["category"]
        surgery_complexity = surgery_info["complexity"]
        surgery_duration_hours = round(random.uniform(*surgery_info["duration"]), 1)
        
        number_of_heart_surgeries = random.choice([0, 0, 0, 1, 1, 2])  # Most have 0-1 previous surgeries
        
        # Pre-Surgery Risk Factors (NEW - for Gemini integration)
        # Generate realistic pre-surgery notes based on patient conditions
        pre_surgery_notes_list = []
        other_risk_factors_list = []
        
        if diabetes:
            other_risk_factors_list.append("having diabetes")
            if random.random() > 0.7:
                pre_surgery_notes_list.append("Patient has uncontrolled diabetes with HbA1c > 8")
        
        if hypertension and systolic_bp > 160:
            other_risk_factors_list.append("severe hypertension")
            pre_surgery_notes_list.append("Severe hypertension requiring medication adjustment")
        
        if heart_failure:
            other_risk_factors_list.append("history of heart failure")
            pre_surgery_notes_list.append("Patient has chronic heart failure")
        
        if ejection_fraction < 40:
            pre_surgery_notes_list.append(f"Reduced ejection fraction ({ejection_fraction}%)")
        
        if atrial_fibrillation:
            other_risk_factors_list.append("atrial fibrillation")
        
        if smoking == "Yes" or smoking_history == "Current":
            other_risk_factors_list.append("active smoker")
            if random.random() > 0.6:
                pre_surgery_notes_list.append("Patient continues to smoke despite warnings")
        
        if bmi_category == "Obese":
            other_risk_factors_list.append("obesity")
        
        if age > 75:
            other_risk_factors_list.append("advanced age")
            if random.random() > 0.5:
                pre_surgery_notes_list.append(f"Patient is {age} years old with multiple comorbidities")
        
        if Affected_by_Covid:
            other_risk_factors_list.append("recent COVID-19 infection")
            pre_surgery_notes_list.append("Patient recovered from COVID-19 within past 6 months")
        
        if number_of_heart_surgeries > 0:
            other_risk_factors_list.append(f"previous heart surgery ({number_of_heart_surgeries}x)")
        
        # Add some random critical conditions
        critical_conditions = [
            "history of stroke",
            "kidney disease",
            "liver dysfunction",
            "chronic lung disease",
            "peripheral vascular disease",
            "anemia",
        ]
        
        if random.random() > 0.7:  # 30% chance of additional risk factor
            selected_condition = random.choice(critical_conditions)
            other_risk_factors_list.append(selected_condition)
            if random.random() > 0.5:
                pre_surgery_notes_list.append(f"Patient has {selected_condition}")
        
        # Create consolidated pre-surgery notes
        pre_surgery_notes = "; ".join(pre_surgery_notes_list) if pre_surgery_notes_list else ""
        other_risk_factors = other_risk_factors_list if other_risk_factors_list else []
        
        # Count total risk factors for scoring
        num_risk_factors = len(other_risk_factors_list)
        
        # Calculate Risk Score (0-100)
        risk_score = surgery_info["base_risk"] * 100
        
        # Add risk from pre-surgery risk factors
        risk_score += num_risk_factors * 3  # Each risk factor adds 3 points
        
        # Risk factors that increase risk
        if age > 70:
            risk_score += 10
        elif age > 60:
            risk_score += 5
        
        if ejection_fraction < 40:
            risk_score += 15
        elif ejection_fraction < 50:
            risk_score += 8
        
        if hypertension:
            risk_score += 5
        if diabetes:
            risk_score += 7
        if heart_failure:
            risk_score += 12
        if atrial_fibrillation:
            risk_score += 8
        if Affected_by_Covid:
            risk_score += 6
        
        if smoking == "Yes" or smoking_history == "Current":
            risk_score += 6
        
        if bmi_category == "Obese":
            risk_score += 5
        elif bmi_category == "Underweight":
            risk_score += 4
        
        if number_of_heart_surgeries > 0:
            risk_score += number_of_heart_surgeries * 4
        
        if nyha_class == "IV":
            risk_score += 10
        elif nyha_class == "III":
            risk_score += 6
        
        # Add some randomness
        risk_score += random.uniform(-5, 5)
        risk_score = max(0, min(100, risk_score))  # Clamp 0-100
        
        # Determine Risk Level
        if risk_score < 30:
            risk_level = "Low"
        elif risk_score < 60:
            risk_level = "Medium"
        elif risk_score < 80:
            risk_level = "High"
        else:
            risk_level = "Critical"
        
        # Calculate Recovery Days
        base_recovery = random.randint(*surgery_info["recovery"])
        
        # Adjust based on risk factors
        recovery_modifier = 1.0
        if age > 70:
            recovery_modifier += 0.3
        if ejection_fraction < 40:
            recovery_modifier += 0.4
        if diabetes:
            recovery_modifier += 0.2
        if heart_failure:
            recovery_modifier += 0.3
        if bmi_category == "Obese":
            recovery_modifier += 0.2
        
        recovery_days = int(base_recovery * recovery_modifier)
        recovery_days = max(1, recovery_days)
        
        # Contact Info
        contact_number = f"{random.randint(7000000000, 9999999999)}"
        email = f"patient{i+1}@mail.com"
        patient_name = f"Patient_{i+1}"
        
        # Additional fields
        num_surgeries_type = random.choice(["CABG", "Valve", "Other", "None"])
        joint_case = random.choice(["Yes", "No"])
        surgery_mortality_risk = round(surgery_info["base_risk"], 2)
        typical_recovery_days_surgery = int((surgery_info["recovery"][0] + surgery_info["recovery"][1]) / 2)
        
        # Create patient record
        patient = {
            "patient_id": patient_id,
            "patient_name": patient_name,
            "age": age,
            "age_group": age_group,
            "sex": sex,
            "contact_number": contact_number,
            "email": email,
            "blood_group": blood_group,
            "residence": residence,
            "occupation": occupation,
            "marital_status": marital_status,
            "education_level": education_level,
            "height_cm": round(height_cm, 1),
            "weight_kg": round(weight_kg, 1),
            "bmi": round(bmi, 1),
            "bmi_category": bmi_category,
            "smoking": smoking,
            "Affected_by_Covid": Affected_by_Covid,
            "smoking_history": smoking_history,
            "alcohol_consumption": alcohol_consumption,
            "exercise_frequency": exercise_frequency,
            "family_history": family_history,
            "family_history_detail": family_history_detail,
            "systolic_bp": systolic_bp,
            "diastolic_bp": diastolic_bp,
            "mean_arterial_pressure": mean_arterial_pressure,
            "pulse_rate": pulse_rate,
            "type_of_heart_disease": type_of_heart_disease,
            "ejection_fraction": ejection_fraction,
            "lvef_category": lvef_category,
            "nyha_class": nyha_class,
            "cardiac_rhythm": cardiac_rhythm,
            "number_of_heart_surgeries": number_of_heart_surgeries,
            "num_surgeries_type": num_surgeries_type,
            "joint_case": joint_case,
            "surgery_type": surgery_type,
            "surgery_category": surgery_category,
            "surgery_complexity": surgery_complexity,
            "surgery_duration_hours": surgery_duration_hours,
            "surgery_mortality_risk": surgery_mortality_risk,
            "typical_recovery_days_surgery": typical_recovery_days_surgery,
            "risk_score": round(risk_score, 1),
            "risk_level": risk_level,
            "recovery_days": recovery_days,
            "hypertension": hypertension,
            "diabetes": diabetes,
            "heart_failure": heart_failure,
            "atrial_fibrillation": atrial_fibrillation,
            "pre_surgery_notes": pre_surgery_notes,
            "other_risk_factors": "|".join(other_risk_factors) if other_risk_factors else "",  # Pipe-separated string
            "num_risk_factors": num_risk_factors,
        }
        
        data.append(patient)
    
    return pd.DataFrame(data)

def main():
    """Generate and save the dataset"""
    print("\n" + "="*60)
    print("🏥 CARDIAC SURGERY RISK PREDICTION - DATASET GENERATOR")
    print("="*60)
    
    print(f"\n📊 Generating {NUM_PATIENTS} patient records...")
    df = generate_patient_data()
    
    print("\n✅ Dataset generated successfully!")
    print(f"\n📈 Dataset Statistics:")
    print(f"   - Total Patients: {len(df)}")
    print(f"   - Features: {len(df.columns)}")
    print(f"\n🏥 Surgery Distribution:")
    print(df['surgery_category'].value_counts())
    print(f"\n⚠️ Risk Level Distribution:")
    print(df['risk_level'].value_counts())
    
    # Save to CSV
    output_file = "heart.csv"
    df.to_csv(output_file, index=False)
    print(f"\n💾 Dataset saved to: {output_file}")
    
    print("\n" + "="*60)
    print("✅ DATASET GENERATION COMPLETE!")
    print("="*60)
    print("\n🚀 Next Step: Run 'python train_models.py' to train the models\n")

if __name__ == "__main__":
    main()