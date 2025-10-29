import pandas as pd
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
    
    print("\n🤖 Training Voting Ensemble Model...")
    
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
    
    print("\n📅 Training Recovery Days Predictor...")
    
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
    print("🚀 Starting Model Training Pipeline...\n")
    
    # Load dataset
    data_path = os.path.join(os.path.dirname(__file__), 'heart.csv')
    
    if not os.path.exists(data_path):
        print("❌ Dataset not found. Please run generate_dataset.py first.")
        return
    
    print(f"📂 Loading dataset from {data_path}")
    df = pd.read_csv(data_path)
    print(f"✅ Dataset loaded: {df.shape}")
    
    # Preprocess data
    print("\n🔄 Preprocessing data...")
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
    
    print(f"\n✅ Voting Ensemble Accuracy: {accuracy:.4f}")
    print(f"\n📊 Classification Report:")
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
    
    print(f"\n✅ Recovery Prediction MAE: {mae:.2f} days")
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
    
    print(f"\n💾 Models saved to {model_dir}")
    print("\n✅ Training completed successfully!")


if __name__ == "__main__":
    main()
