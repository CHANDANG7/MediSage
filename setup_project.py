import os

def create_file(path, content):
    """Create a file with given content"""
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Created: {path}")

base_dir = os.path.dirname(os.path.abspath(__file__))

# Create directories
dirs = ['backend/routes', 'frontend', 'ml_models', 'utils', 'knowledge_base', 'trained_models']
for d in dirs:
    os.makedirs(os.path.join(base_dir, d), exist_ok=True)

print("🚀 Creating MediSage AI Project...\n")

# ==================== requirements.txt ====================
create_file('requirements.txt', '''# FastAPI Backend
fastapi==0.109.0
uvicorn==0.27.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0

# Database
pymongo==4.6.1
motor==3.3.2

# Machine Learning
scikit-learn==1.4.0
xgboost==2.0.3
imbalanced-learn==0.12.0
joblib==1.3.2
pandas==2.2.0
numpy==1.26.3

# NLP
spacy==3.7.2
PyPDF2==3.0.1
python-docx==1.1.0

# Gemini API
google-generativeai==0.3.2

# Streamlit Frontend
streamlit==1.31.0
streamlit-option-menu==0.3.12
plotly==5.18.0

# Encryption
cryptography==42.0.0

# Vector Database for RAG
chromadb==0.4.22
langchain==0.1.6
langchain-google-genai==0.0.6

# Utilities
requests==2.31.0
Pillow==10.2.0
pdf2image==1.17.0
''')

# ==================== .env ====================
create_file('.env', '''MONGODB_URI=mongodb://localhost:27017/
DATABASE_NAME=medisage_db
SECRET_KEY=change-this-to-a-secure-random-string-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
GEMINI_API_KEY=your-gemini-api-key-here
''')

# ==================== ml_models/generate_dataset.py ====================
create_file('ml_models/generate_dataset.py', '''import pandas as pd
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
        "email": [f"patient{i}[mail.com"](cci:4://file://mail.com":0:0-0:0) for i in range(1, num_samples + 1)],
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
    print(f"\\n📋 First few rows:\\n{df.head()}")
''')

# ==================== ml_models/train_models.py ====================
create_file('ml_models/train_models.py', '''import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import joblib
import os
import warnings
warnings.filterwarnings('ignore')


def preprocess_data(df):
    """Preprocess the dataset for training"""
    
    # Create a copy
    data = df.copy()
    
    # Select features for training
    categorical_cols = [
        'sex', 'blood_group', 'residence', 'smoking', 'smoking_history',
        'alcohol_consumption', 'exercise_frequency', 'type_of_heart_disease',
        'cardiac_rhythm', 'surgery_type', 'surgery_category', 'surgery_complexity',
        'nyha_class', 'bmi_category', 'lvef_category', 'age_group'
    ]
    
    numerical_cols = [
        'age', 'bmi', 'systolic_bp', 'diastolic_bp', 'pulse_rate',
        'ejection_fraction', 'hypertension', 'diabetes', 'family_history',
        'heart_failure', 'atrial_fibrillation', 'Affected_by_Covid',
        'number_of_heart_surgeries', 'surgery_duration_hours'
    ]
    
    # Encode categorical variables
    label_encoders = {}
    for col in categorical_cols:
        if col in data.columns:
            le = LabelEncoder()
            data[col] = le.fit_transform(data[col].astype(str))
            label_encoders[col] = le
    
    # Select features
    feature_cols = [col for col in categorical_cols + numerical_cols if col in data.columns]
    X = data[feature_cols]
    
    # Target variables
    y_risk = data['risk_level']
    y_recovery = data['recovery_days']
    y_risk_score = data['risk_score']
    
    # Encode risk level
    risk_encoder = LabelEncoder()
    y_risk_encoded = risk_encoder.fit_transform(y_risk)
    
    return X, y_risk_encoded, y_recovery, y_risk_score, feature_cols, label_encoders, risk_encoder


def train_voting_ensemble(X_train, y_train):
    """Train Voting Ensemble with XGBoost, Random Forest, Gradient Boosting, and SVM"""
    
    print("\\n🤖 Training Voting Ensemble Model...")
    
    # Initialize base models
    xgb = XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=42,
        eval_metric='mlogloss'
    )
    
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    
    gb = GradientBoostingClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=42
    )
    
    svm = SVC(
        kernel='rbf',
        C=1.0,
        probability=True,
        random_state=42
    )
    
    # Create voting ensemble
    voting_clf = VotingClassifier(
        estimators=[
            ('xgb', xgb),
            ('rf', rf),
            ('gb', gb),
            ('svm', svm)
        ],
        voting='soft',
        n_jobs=-1
    )
    
    # Train the ensemble
    voting_clf.fit(X_train, y_train)
    
    return voting_clf


def train_recovery_predictor(X_train, y_train):
    """Train recovery days predictor"""
    
    print("\\n📅 Training Recovery Days Predictor...")
    
    from sklearn.ensemble import RandomForestRegressor
    from xgboost import XGBRegressor
    
    # Voting regressor for recovery prediction
    rf_reg = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    xgb_reg = XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
    
    # Train both and use averaging
    rf_reg.fit(X_train, y_train)
    xgb_reg.fit(X_train, y_train)
    
    return rf_reg, xgb_reg


def main():
    print("🚀 Starting Model Training Pipeline...\\n")
    
    # Load dataset
    data_path = os.path.join(os.path.dirname(__file__), 'heart.csv')
    
    if not os.path.exists(data_path):
        print("❌ Dataset not found. Please run generate_dataset.py first.")
        return
    
    print(f"📂 Loading dataset from {data_path}")
    df = pd.read_csv(data_path)
    print(f"✅ Dataset loaded: {df.shape}")
    
    # Preprocess data
    print("\\n🔄 Preprocessing data...")
    X, y_risk, y_recovery, y_risk_score, feature_cols, label_encoders, risk_encoder = preprocess_data(df)
    
    # Split data
    X_train, X_test, y_risk_train, y_risk_test, y_recovery_train, y_recovery_test = train_test_split(
        X, y_risk, y_recovery, test_size=0.2, random_state=42, stratify=y_risk
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print(f"✅ Training set: {X_train.shape}, Test set: {X_test.shape}")
    
    # Train Voting Ensemble for Risk Classification
    voting_clf = train_voting_ensemble(X_train_scaled, y_risk_train)
    
    # Evaluate
    y_pred = voting_clf.predict(X_test_scaled)
    accuracy = accuracy_score(y_risk_test, y_pred)
    
    print(f"\\n✅ Voting Ensemble Accuracy: {accuracy:.4f}")
    print(f"\\n📊 Classification Report:")
    print(classification_report(y_risk_test, y_pred, target_names=risk_encoder.classes_))
    
    # Train Recovery Predictor
    rf_recovery, xgb_recovery = train_recovery_predictor(X_train_scaled, y_recovery_train)
    
    # Evaluate recovery models
    from sklearn.metrics import mean_absolute_error, r2_score
    
    rf_pred = rf_recovery.predict(X_test_scaled)
    xgb_pred = xgb_recovery.predict(X_test_scaled)
    ensemble_recovery_pred = (rf_pred + xgb_pred) / 2
    
    mae = mean_absolute_error(y_recovery_test, ensemble_recovery_pred)
    r2 = r2_score(y_recovery_test, ensemble_recovery_pred)
    
    print(f"\\n✅ Recovery Prediction MAE: {mae:.2f} days")
    print(f"✅ Recovery Prediction R²: {r2:.4f}")
    
    # Save models
    model_dir = os.path.join(os.path.dirname(__file__), '..', 'trained_models')
    os.makedirs(model_dir, exist_ok=True)
    
    joblib.dump(voting_clf, os.path.join(model_dir, 'risk_classifier.pkl'))
    joblib.dump(rf_recovery, os.path.join(model_dir, 'recovery_rf.pkl'))
    joblib.dump(xgb_recovery, os.path.join(model_dir, 'recovery_xgb.pkl'))
    joblib.dump(scaler, os.path.join(model_dir, 'scaler.pkl'))
    joblib.dump(label_encoders, os.path.join(model_dir, 'label_encoders.pkl'))
    joblib.dump(risk_encoder, os.path.join(model_dir, 'risk_encoder.pkl'))
    joblib.dump(feature_cols, os.path.join(model_dir, 'feature_cols.pkl'))
    
    print(f"\\n💾 Models saved to {model_dir}")
    print("\\n✅ Training completed successfully!")


if __name__ == "__main__":
    main()
''')

# ==================== ml_models/nlp_extractor.py ====================
create_file('ml_models/nlp_extractor.py', '''import re
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
    """Extract medical features from text using NLP"""
    
    features = {
        'age': None,
        'sex': None,
        'bmi': None,
        'systolic_bp': None,
        'diastolic_bp': None,
        'heart_disease': None,
        'ejection_fraction': None,
        'hypertension': 0,
        'diabetes': 0,
        'smoking': 'No',
        'surgery_type': None
    }
    
    text_lower = text.lower()
    
    # Extract age
    age_pattern = r'age[:\s]+(\d{1,3})'
    age_match = re.search(age_pattern, text_lower)
    if age_match:
        features['age'] = int(age_match.group(1))
    
    # Extract gender
    if 'male' in text_lower and 'female' not in text_lower:
        features['sex'] = 'Male'
    elif 'female' in text_lower:
        features['sex'] = 'Female'
    
    # Extract BMI
    bmi_pattern = r'bmi[:\s]+(\d{1,3}\.?\d*)'
    bmi_match = re.search(bmi_pattern, text_lower)
    if bmi_match:
        features['bmi'] = float(bmi_match.group(1))
    
    # Extract Blood Pressure
    bp_pattern = r'(\d{2,3})\s*/\s*(\d{2,3})'
    bp_match = re.search(bp_pattern, text)
    if bp_match:
        features['systolic_bp'] = int(bp_match.group(1))
        features['diastolic_bp'] = int(bp_match.group(2))
    
    # Extract Ejection Fraction
    ef_pattern = r'ejection fraction[:\s]+(\d{1,3})'
    ef_match = re.search(ef_pattern, text_lower)
    if ef_match:
        features['ejection_fraction'] = int(ef_match.group(1))
    elif 'ef' in text_lower:
        ef_pattern2 = r'ef[:\s]+(\d{1,3})'
        ef_match2 = re.search(ef_pattern2, text_lower)
        if ef_match2:
            features['ejection_fraction'] = int(ef_match2.group(1))
    
    # Detect conditions
    if any(word in text_lower for word in ['hypertension', 'high blood pressure', 'htn']):
        features['hypertension'] = 1
    
    if any(word in text_lower for word in ['diabetes', 'diabetic', 'dm']):
        features['diabetes'] = 1
    
    if any(word in text_lower for word in ['smoker', 'smoking']):
        features['smoking'] = 'Yes'
    
    # Detect heart disease type
    if 'coronary artery disease' in text_lower or 'cad' in text_lower:
        features['heart_disease'] = 'CAD'
    elif 'valve' in text_lower:
        features['heart_disease'] = 'Valve'
    elif 'arrhythmia' in text_lower:
        features['heart_disease'] = 'Arrhythmia'
    elif 'heart failure' in text_lower or 'chf' in text_lower:
        features['heart_disease'] = 'CHF'
    
    # Detect surgery type
    if 'cabg' in text_lower or 'bypass' in text_lower:
        features['surgery_type'] = 'CABG'
    elif 'valve replacement' in text_lower:
        features['surgery_type'] = 'Valve Replacement'
    elif 'pacemaker' in text_lower:
        features['surgery_type'] = 'Pacemaker'
    
    return features


def parse_medical_report(file_content, file_type='pdf'):
    """Parse medical report and extract features"""
    
    if file_type == 'pdf':
        text = extract_text_from_pdf(file_content)
    else:
        text = file_content.decode('utf-8') if isinstance(file_content, bytes) else file_content
    
    features = extract_medical_features(text)
    
    return features, text
''')

# ==================== ml_models/predict.py ====================
create_file('ml_models/predict.py', '''import joblib
import numpy as np
import pandas as pd
import os


class RiskPredictor:
    def __init__(self, model_dir='trained_models'):
        """Load trained models"""
        self.model_dir = model_dir
        
        self.risk_classifier = joblib.load(os.path.join(model_dir, 'risk_classifier.pkl'))
        self.recovery_rf = joblib.load(os.path.join(model_dir, 'recovery_rf.pkl'))
        self.recovery_xgb = joblib.load(os.path.join(model_dir, 'recovery_xgb.pkl'))
        self.scaler = joblib.load(os.path.join(model_dir, 'scaler.pkl'))
        self.label_encoders = joblib.load(os.path.join(model_dir, 'label_encoders.pkl'))
        self.risk_encoder = joblib.load(os.path.join(model_dir, 'risk_encoder.pkl'))
        self.feature_cols = joblib.load(os.path.join(model_dir, 'feature_cols.pkl'))
    
    def prepare_input(self, patient_data):
        """Prepare input data for prediction"""
        
        # Create a DataFrame with default values
        data = {}
        
        # Set default values for all features
        defaults = {
            'age': 50, 'bmi': 25, 'systolic_bp': 120, 'diastolic_bp': 80,
            'pulse_rate': 75, 'ejection_fraction': 55, 'hypertension': 0,
            'diabetes': 0, 'family_history': 0, 'heart_failure': 0,
            'atrial_fibrillation': 0, 'Affected_by_Covid': 0,
            'number_of_heart_surgeries': 0, 'surgery_duration_hours': 4,
            'sex': 'Male', 'blood_group': 'O+', 'residence': 'Urban',
            'smoking': 'No', 'smoking_history': 'Never',
            'alcohol_consumption': 'None', 'exercise_frequency': 'Regular',
            'type_of_heart_disease': 'None', 'cardiac_rhythm': 'Normal',
            'surgery_type': 'CABG', 'surgery_category': 'Major',
            'surgery_complexity': 'Medium', 'nyha_class': 'I',
            'bmi_category': 'Normal', 'lvef_category': 'Preserved',
            'age_group': 'Middle'
        }
        
        # Update with provided data
        for key, default_value in defaults.items():
            data[key] = patient_data.get(key, default_value)
        
        # Create DataFrame
        df = pd.DataFrame([data])
        
        # Encode categorical variables
        for col, encoder in self.label_encoders.items():
            if col in df.columns:
                try:
                    df[col] = encoder.transform(df[col].astype(str))
                except:
                    df[col] = 0
        
        # Select and order features
        X = df[self.feature_cols]
        
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        return X_scaled
    
    def predict(self, patient_data):
        """Make prediction"""
        
        X = self.prepare_input(patient_data)
        
        # Predict risk level
        risk_pred = self.risk_classifier.predict(X)[0]
        risk_proba = self.risk_classifier.predict_proba(X)[0]
        risk_level = self.risk_encoder.inverse_transform([risk_pred])[0]
        
        # Calculate risk score (weighted average of probabilities)
        risk_scores = {'Low': 15, 'Medium': 45, 'High': 70, 'Critical': 90}
        risk_score = sum(prob * risk_scores[label] for prob, label in zip(risk_proba, self.risk_encoder.classes_))
        
        # Predict recovery days
        rf_recovery = self.recovery_rf.predict(X)[0]
        xgb_recovery = self.recovery_xgb.predict(X)[0]
        recovery_days = int((rf_recovery + xgb_recovery) / 2)
        
        return {
            'risk_level': risk_level,
            'risk_score': round(risk_score, 1),
            'recovery_days': recovery_days,
            'risk_probabilities': {
                label: round(float(prob) * 100, 1) 
                for label, prob in zip(self.risk_encoder.classes_, risk_proba)
            }
        }
''')

print("\n✅ All core ML files created!")
print("Next: Creating remaining files...\n")
