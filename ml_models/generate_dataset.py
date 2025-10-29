import pandas as pd
import numpy as np
import random
import os


def generate_dataset(num_samples=2000):
    """Generate a realistic synthetic dataset for heart surgery risk prediction."""
    
    np.random.seed(42)
    random.seed(42)
    
    ages = np.random.randint(20, 90, size=num_samples)
    bmi = np.round(np.random.uniform(18, 38, size=num_samples), 1)
    systolic_bp = np.random.randint(100, 180, size=num_samples)
    diastolic_bp = np.random.randint(60, 110, size=num_samples)
    heart_disease = np.random.choice(["CAD", "Valve", "Arrhythmia", "CHF", "None"], size=num_samples, p=[0.35, 0.25, 0.15, 0.15, 0.10])
    ejection_fraction = np.random.randint(25, 70, size=num_samples)
    hypertension = np.random.choice([0, 1], size=num_samples, p=[0.4, 0.6])
    diabetes = np.random.choice([0, 1], size=num_samples, p=[0.7, 0.3])
    pulmonary_hypertension = np.random.choice([0, 1], size=num_samples, p=[0.8, 0.2])
    stroke_history = np.random.choice([0, 1], size=num_samples, p=[0.9, 0.1])
    heart_failure = np.random.choice([0, 1], size=num_samples, p=[0.75, 0.25])
    atrial_fibrillation = np.random.choice([0, 1], size=num_samples, p=[0.85, 0.15])
    affected_by_covid = np.random.choice([0, 1], size=num_samples, p=[0.85, 0.15])
    
    # Simulate risk based on health factors
    risk_score = (
        (ages - 20) / 70 * 0.25 +
        (bmi - 18) / 20 * 0.15 +
        (systolic_bp - 100) / 80 * 0.15 +
        (hypertension * 0.1) +
        (heart_failure * 0.1) +
        (atrial_fibrillation * 0.05) +
        (affected_by_covid * 0.05) +
        np.random.normal(0, 0.05, num_samples)
    ) * 100
    
    risk_score = np.clip(risk_score, 5, 95).round(1)
    
    # Risk levels based on score thresholds
    risk_level = pd.cut(
        risk_score,
        bins=[0, 30, 60, 80, 100],
        labels=["Low", "Medium", "High", "Critical"]
    )
    
    # Recovery days correlated with risk
    recovery_days = np.where(risk_level == "Low", np.random.randint(5, 10, size=num_samples),
                    np.where(risk_level == "Medium", np.random.randint(10, 20, size=num_samples),
                    np.where(risk_level == "High", np.random.randint(20, 35, size=num_samples),
                    np.random.randint(30, 50, size=num_samples))))
    
    # Construct dataframe
    data = {
        "patient_id": [f"P{str(i).zfill(4)}" for i in range(1, num_samples + 1)],
        "patient_name": [f"Patient_{i}" for i in range(1, num_samples + 1)],
        "age": ages,
        "age_group": pd.cut(ages, bins=[0, 35, 55, 120], labels=["Young", "Middle", "Old"]),
        "sex": np.random.choice(["Male", "Female"], size=num_samples),
        "contact_number": [random.randint(7000000000, 9999999999) for _ in range(num_samples)],
        "email": [f"patient{i}@mail.com" for i in range(1, num_samples + 1)],
        "blood_group": np.random.choice(["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"], size=num_samples),
        "residence": np.random.choice(["Urban", "Rural", "Semi-Urban"], size=num_samples),
        "occupation": np.random.choice(["Engineer", "Teacher", "Doctor", "Farmer", "Other"], size=num_samples),
        "marital_status": np.random.choice(["Single", "Married", "Divorced", "Widowed"], size=num_samples),
        "education_level": np.random.choice(["High School", "Graduate", "Postgraduate", "PhD"], size=num_samples),
        "height_cm": np.random.randint(150, 190, size=num_samples),
        "weight_kg": np.random.randint(50, 100, size=num_samples),
        "bmi": bmi,
        "bmi_category": pd.cut(bmi, bins=[0, 18.5, 25, 30, 100], labels=["Underweight", "Normal", "Overweight", "Obese"]),
        "smoking": np.random.choice(["Yes", "No"], size=num_samples, p=[0.3, 0.7]),
        "Affected_by_Covid": affected_by_covid,
        "smoking_history": np.random.choice(["Never", "Former", "Current"], size=num_samples),
        "alcohol_consumption": np.random.choice(["None", "Moderate", "High"], size=num_samples, p=[0.5, 0.4, 0.1]),
        "exercise_frequency": np.random.choice(["None", "Rare", "Regular"], size=num_samples, p=[0.3, 0.4, 0.3]),
        "family_history": np.random.choice([0, 1], size=num_samples, p=[0.6, 0.4]),
        "family_history_detail": np.random.choice(["Heart Disease", "Diabetes", "Hypertension", "None"], size=num_samples, p=[0.3, 0.2, 0.3, 0.2]),
        "systolic_bp": systolic_bp,
        "diastolic_bp": diastolic_bp,
        "mean_arterial_pressure": np.round(diastolic_bp + (systolic_bp - diastolic_bp) / 3, 1),
        "pulse_rate": np.random.randint(60, 110, size=num_samples),
        "type_of_heart_disease": heart_disease,
        "ejection_fraction": ejection_fraction,
        "lvef_category": pd.cut(ejection_fraction, bins=[0, 40, 50, 100], labels=["Reduced", "Mid-range", "Preserved"]),
        "nyha_class": np.random.choice(["I", "II", "III", "IV"], size=num_samples, p=[0.4, 0.3, 0.2, 0.1]),
        "cardiac_rhythm": np.random.choice(["Normal", "AFib", "Flutter"], size=num_samples, p=[0.8, 0.15, 0.05]),
        "number_of_heart_surgeries": np.random.randint(0, 3, size=num_samples),
        "num_surgeries_type": np.random.choice(["CABG", "Valve", "Bypass", "Other"], size=num_samples),
        "joint_case": np.random.choice(["Yes", "No"], size=num_samples),
        "surgery_type": np.random.choice(["CABG", "Valve Replacement", "Bypass", "Pacemaker"], size=num_samples),
        "surgery_category": np.random.choice(["Major", "Intermediate", "Minor"], size=num_samples, p=[0.5, 0.3, 0.2]),
        "surgery_complexity": np.random.choice(["Low", "Medium", "High"], size=num_samples, p=[0.3, 0.4, 0.3]),
        "surgery_duration_hours": np.round(np.random.uniform(2, 8, size=num_samples), 1),
        "surgery_mortality_risk": np.round(risk_score / 100 * 0.3, 2),
        "typical_recovery_days_surgery": np.random.randint(5, 30, size=num_samples),
        "risk_score": risk_score,
        "risk_level": risk_level,
        "recovery_days": recovery_days
    }
    
    df = pd.DataFrame(data)
    return df


if __name__ == "__main__":
    df = generate_dataset(2000)
    save_path = os.path.join(os.path.dirname(__file__), "heart.csv")
    df.to_csv(save_path, index=False)
    print(f"✅ Realistic dataset saved successfully at: {save_path}")
    print(f"📊 Dataset shape: {df.shape}")
    print(f"\n📋 First few rows:\n{df.head()}")
