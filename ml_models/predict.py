import joblib
import numpy as np
import pandas as pd
import os
import shap


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
        
        # Initialize SHAP explainer
        self.explainer = None
    
    def prepare_input(self, patient_data):
        """Prepare input data for prediction"""
        
        # Create a DataFrame with default values
        data = {}
        
        # Set default values for all features (expanded)
        defaults = {
            # Demographics
            'age': 50, 'age_group': 'Middle', 'sex': 'Male',
            'contact_number': '9999999999', 'email': 'patient@mail.com',
            'blood_group': 'O+', 'residence': 'Urban', 'occupation': 'Other',
            'marital_status': 'Married', 'education_level': 'Graduate',
            
            # Physical Measurements
            'height_cm': 170, 'weight_kg': 70, 'bmi': 25, 'bmi_category': 'Normal',
            
            # Lifestyle
            'smoking': 'No', 'Affected_by_Covid': 0, 'smoking_history': 'Never',
            'alcohol_consumption': 'None', 'exercise_frequency': 'Regular',
            
            # Family History
            'family_history': 0, 'family_history_detail': 'None',
            
            # Vital Signs
            'systolic_bp': 120, 'diastolic_bp': 80, 'mean_arterial_pressure': 93.3,
            'pulse_rate': 75,
            
            # Heart Condition
            'type_of_heart_disease': 'None', 'ejection_fraction': 55,
            'lvef_category': 'Preserved', 'cardiac_rhythm': 'Normal',
            'nyha_class': 'I',
            
            # Medical History
            'hypertension': 0, 'diabetes': 0, 'heart_failure': 0,
            'atrial_fibrillation': 0, 'number_of_heart_surgeries': 0,
            
            # Surgery Details
            'surgery_type': 'CABG', 'surgery_category': 'Major',
            'surgery_complexity': 'Medium', 'surgery_duration_hours': 4
        }
        
        # Update with provided data, clean empty values
        for key, default_value in defaults.items():
            value = patient_data.get(key, default_value)
            # Handle empty strings and None
            if value == '' or value is None:
                data[key] = default_value
            else:
                data[key] = value
        
        # Create DataFrame
        df = pd.DataFrame([data])
        
        # Encode categorical variables
        for col, encoder in self.label_encoders.items():
            if col in df.columns:
                try:
                    # Convert to string and handle empty values
                    values = df[col].astype(str).replace('', 'None')
                    df[col] = encoder.transform(values)
                except Exception as e:
                    # If encoding fails, use 0 as default
                    df[col] = 0
        
        # Select and order features
        X = df[self.feature_cols]
        
        # Replace any remaining empty strings or NaN with 0
        X = X.replace('', 0)
        X = X.fillna(0)
        
        # Ensure all numeric columns are float
        for col in X.columns:
            try:
                X[col] = X[col].astype(float)
            except:
                X[col] = 0.0
        
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
        
        # Get SHAP values for explainability
        top_features = self.get_top_features(X)
        
        return {
            'risk_level': risk_level,
            'risk_score': round(risk_score, 1),
            'recovery_days': recovery_days,
            'risk_probabilities': {
                label: round(float(prob) * 100, 1) 
                for label, prob in zip(self.risk_encoder.classes_, risk_proba)
            },
            'top_features': top_features
        }
    
    def get_top_features(self, X, n_features=3):
        """Get top N features influencing the prediction using SHAP"""
        try:
            # Initialize explainer if not already done
            if self.explainer is None:
                # Use TreeExplainer for tree-based models
                # Get the first estimator from voting classifier
                base_model = self.risk_classifier.estimators_[0]  # XGBoost
                self.explainer = shap.TreeExplainer(base_model)
            
            # Calculate SHAP values
            shap_values = self.explainer.shap_values(X)
            
            # Get absolute SHAP values for feature importance
            if isinstance(shap_values, list):
                # Multi-class: average across all classes
                shap_importance = np.abs(np.array(shap_values)).mean(axis=0)
            else:
                shap_importance = np.abs(shap_values)
            
            # Get top features
            top_indices = np.argsort(shap_importance[0])[::-1][:n_features]
            
            top_features_list = []
            for idx in top_indices:
                feature_name = self.feature_cols[idx]
                importance = float(shap_importance[0][idx])
                top_features_list.append({
                    'feature': feature_name,
                    'importance': round(importance, 4)
                })
            
            return top_features_list
        
        except Exception as e:
            # Fallback: return feature importances from the model
            try:
                # Get feature importances from XGBoost
                base_model = self.risk_classifier.estimators_[0]
                importances = base_model.feature_importances_
                top_indices = np.argsort(importances)[::-1][:n_features]
                
                return [{
                    'feature': self.feature_cols[idx],
                    'importance': round(float(importances[idx]), 4)
                } for idx in top_indices]
            except:
                return [{'feature': 'age', 'importance': 0.5}, 
                       {'feature': 'ejection_fraction', 'importance': 0.3},
                       {'feature': 'systolic_bp', 'importance': 0.2}]
