import streamlit as st
from streamlit_option_menu import option_menu
import requests
import json
import plotly.graph_objects as go
from PIL import Image
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from io import BytesIO
from datetime import datetime

import os
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Page config
st.set_page_config(page_title="MediSage AI", page_icon="🏥", layout="wide")

# Session state initialization
if 'token' not in st.session_state:
    st.session_state.token = None
if 'is_first_login' not in st.session_state:
    st.session_state.is_first_login = False
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Home"

def make_request(endpoint, method="GET", data=None, files=None, auth=True):
    """Make API request"""
    headers = {}
    if auth and st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    
    url = f"{API_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            if files:
                response = requests.post(url, headers=headers, files=files, data=data)
            else:
                headers["Content-Type"] = "application/json"
                response = requests.post(url, headers=headers, json=data)
        
        return response
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None

def login_page():
    """Login/Register page"""
    st.title("🏥 MediSage AI - Login")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login to your account")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            # Send as form data, not JSON (OAuth2 requirement)
            try:
                response = requests.post(
                    f"{API_URL}/token",
                    data={"username": email, "password": password},
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
            except Exception as e:
                st.error(f"Connection error: {str(e)}")
                response = None
            
            
            if response and response.status_code == 200:
                result = response.json()
                st.session_state.token = result["access_token"]
                
                # Check first login
                check_response = make_request("/check-first-login", "GET")
                if check_response and check_response.status_code == 200:
                    st.session_state.is_first_login = check_response.json()["is_first_login"]
                
                st.success("✅ Login successful!")
                st.rerun()
            elif response and response.status_code == 401:
                st.error("❌ Invalid email or password")
            else:
                st.error("❌ Login failed. Please try again.")
    
    with tab2:
        st.subheader("Create new account")
        full_name = st.text_input("Full Name")
        email_reg = st.text_input("Email", key="reg_email")
        password_reg = st.text_input("Password", type="password", key="reg_password")
        password_conf = st.text_input("Confirm Password", type="password")
        
        if st.button("Register"):
            if password_reg != password_conf:
                st.error("Passwords don't match")
            else:
                data = {
                    "email": email_reg,
                    "password": password_reg,
                    "full_name": full_name
                }
                response = make_request("/register", "POST", data=data, auth=False)
                
                if response and response.status_code == 200:
                    result = response.json()
                    st.session_state.token = result["access_token"]
                    st.session_state.is_first_login = True
                    st.success("Registration successful!")
                    st.rerun()
                else:
                    st.error("Registration failed")

def patient_registration_page():
    """Comprehensive patient registration form with all ML features"""
    st.title("📋 Comprehensive Patient Registration")
    st.write("Please complete your detailed medical profile for accurate risk predictions")
    
    # Check if profile already exists
    check_response = make_request("/patient-profile", "GET")
    if check_response and check_response.status_code == 200:
        st.warning("⚠️ You have already registered! Redirecting to your profile...")
        st.info("You can view and edit your profile from the Profile menu.")
        if st.button("Go to Dashboard"):
            st.session_state.is_first_login = False
            st.rerun()
        return
    
    # Create tabs for organized form
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👤 Basic Info",
        "💓 Vital Signs & Cardiac",
        "🏥 Medical Conditions",
        "💊 Surgery & Treatment",
        "📝 Additional Info"
    ])
    
    # Tab 1: Basic Demographics
    with tab1:
        st.subheader("Basic Demographics")
        col1, col2 = st.columns(2)
        
        with col1:
            age = st.number_input("Age *", min_value=1, max_value=120, value=50)
            sex = st.selectbox("Sex *", ["Male", "Female"])
            blood_group = st.selectbox("Blood Group *", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
            height_cm = st.number_input("Height (cm) *", min_value=50, max_value=250, value=170)
            weight_kg = st.number_input("Weight (kg) *", min_value=20, max_value=200, value=70)
        
        with col2:
            contact_number = st.text_input("Contact Number *")
            residence = st.selectbox("Residence", ["Urban", "Rural", "Semi-Urban"])
            st.info(f"**Calculated BMI:** {round(weight_kg / ((height_cm/100) ** 2), 1)}")
    
    # Tab 2: Vital Signs & Cardiac
    with tab2:
        st.subheader("Vital Signs & Cardiac Health")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Vital Signs**")
            systolic_bp = st.number_input("Systolic Blood Pressure (mmHg)", min_value=80, max_value=200, value=120)
            diastolic_bp = st.number_input("Diastolic Blood Pressure (mmHg)", min_value=40, max_value=130, value=80)
            pulse_rate = st.number_input("Pulse Rate (bpm)", min_value=40, max_value=150, value=75)
            
            st.markdown("**Heart Disease Details**")
            type_of_heart_disease = st.selectbox(
                "Type of Heart Disease",
                ["None", "CAD", "Valve", "Arrhythmia", "CHF"]
            )
            ejection_fraction = st.number_input(
                "Ejection Fraction / LVEF (%)",
                min_value=10, max_value=80, value=55,
                help="Left Ventricular Ejection Fraction - measure of heart pump efficiency"
            )
        
        with col2:
            st.markdown("**Cardiac Status**")
            cardiac_rhythm = st.selectbox(
                "Cardiac Rhythm",
                ["Normal", "AFib", "Flutter"]
            )
            nyha_class = st.selectbox(
                "NYHA Class",
                ["I", "II", "III", "IV"],
                help="New York Heart Association functional classification"
            )
    
    # Tab 3: Medical Conditions
    with tab3:
        st.subheader("Medical Conditions & History")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Chronic Conditions (Check if applicable)**")
            hypertension = st.checkbox("Hypertension (High Blood Pressure)")
            diabetes = st.checkbox("Diabetes")
            heart_failure = st.checkbox("Heart Failure")
            atrial_fibrillation = st.checkbox("Atrial Fibrillation")
            Affected_by_Covid = st.checkbox("Affected by COVID-19")
            
            family_history_bin = st.checkbox("Family History of Heart Disease")
        
        with col2:
            st.markdown("**Lifestyle Factors**")
            smoking = st.selectbox("Current Smoking Status", ["No", "Yes"])
            smoking_history = st.selectbox(
                "Smoking History",
                ["Never", "Former", "Current"]
            )
            alcohol_consumption = st.selectbox(
                "Alcohol Consumption",
                ["None", "Moderate", "High"]
            )
            exercise_frequency = st.selectbox(
                "Exercise Frequency",
                ["Regular", "Rare", "None"]
            )
        
        st.markdown("**Medical History Details**")
        medical_history = st.text_area(
            "Medical History",
            help="Provide details about your medical conditions, past illnesses, etc."
        )
        chronic_conditions_list = st.text_area(
            "Chronic Conditions Details",
            help="List any chronic conditions (one per line)"
        )
    
    # Tab 4: Surgery & Treatment
    with tab4:
        st.subheader("Surgery & Treatment Information")
        
        # Define all surgery types
        all_surgery_types = [
            # Major Surgeries
            "CABG", "Valve Replacement", "Valve Repair", "Aortic Valve Replacement", 
            "Mitral Valve Replacement", "Bypass Surgery", "Heart Transplant", 
            "Coronary Artery Bypass Graft", "Open Heart Surgery", "Aortic Aneurysm Repair", 
            "LVAD Implantation",
            # Intermediate Surgeries
            "Angioplasty", "PCI", "Stent Placement", "Coronary Stenting", 
            "Ablation", "Cardiac Ablation", "ASD Closure", "VSD Closure", 
            "PDA Closure", "TAVI", "TAVR", "MitraClip",
            # Minor Surgeries
            "Pacemaker Implantation", "Pacemaker", "ICD Implantation", 
            "Defibrillator Implantation", "CRT Device Implantation", 
            "Cardiac Catheterization", "Diagnostic Catheterization", 
            "Cardiac Monitoring Device", "Loop Recorder Implantation"
        ]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Surgery Details**")
            number_of_heart_surgeries = st.number_input(
                "Number of Previous Heart Surgeries",
                min_value=0, max_value=10, value=0
            )
            surgery_type = st.selectbox(
                "Type of Surgery (Current/Planned) *",
                all_surgery_types,
                help="Select the type of cardiac surgery"
            )
            st.info("ℹ️ Surgery category and complexity will be automatically detected based on surgery type")
        
        with col2:
            surgery_duration_hours = st.number_input(
                "Expected Surgery Duration (hours)",
                min_value=0.5, max_value=12.0, value=4.0, step=0.5
            )
            
            previous_surgeries = st.text_area(
                "Previous Surgeries (one per line)",
                help="List all previous surgeries"
            )
        
        # Pre-surgery risk factors section
        st.divider()
        st.subheader("⚠️ Pre-Surgery Risk Factors")
        st.markdown("Document any serious conditions or risk factors mentioned by doctor/patient before surgery")
        
        col1, col2 = st.columns(2)
        with col1:
            pre_surgery_notes = st.text_area(
                "Pre-Surgery Notes",
                help="Important risk factors, serious conditions, or concerns mentioned before surgery",
                height=100
            )
        with col2:
            other_risk_factors = st.text_area(
                "Other Risk Factors (one per line)",
                help="E.g., 'having diabetes', 'history of stroke', 'kidney disease'",
                height=100
            )
    
    # Tab 5: Additional Information
    with tab5:
        st.subheader("Additional Medical Information")
        col1, col2 = st.columns(2)
        
        with col1:
            medications = st.text_area(
                "Current Medications (one per line)",
                help="List all medications you are currently taking"
            )
        
        with col2:
            allergies = st.text_area(
                "Allergies (one per line)",
                help="List any drug or other allergies"
            )
    
    # Submit button
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✅ Submit Complete Registration", use_container_width=True, type="primary"):
            # Prepare comprehensive data
            data = {
                # Basic Demographics
                "age": age,
                "sex": sex,
                "blood_group": blood_group,
                "height_cm": height_cm,
                "weight_kg": weight_kg,
                "contact_number": contact_number,
                "residence": residence,
                
                # Vital Signs
                "systolic_bp": systolic_bp,
                "diastolic_bp": diastolic_bp,
                "pulse_rate": pulse_rate,
                
                # Cardiac Conditions (binary)
                "hypertension": 1 if hypertension else 0,
                "diabetes": 1 if diabetes else 0,
                "heart_failure": 1 if heart_failure else 0,
                "atrial_fibrillation": 1 if atrial_fibrillation else 0,
                "Affected_by_Covid": 1 if Affected_by_Covid else 0,
                "family_history": 1 if family_history_bin else 0,
                
                # Heart Disease Details
                "type_of_heart_disease": type_of_heart_disease,
                "ejection_fraction": ejection_fraction,
                "cardiac_rhythm": cardiac_rhythm,
                "nyha_class": nyha_class,
                
                # Lifestyle
                "smoking": smoking,
                "smoking_history": smoking_history,
                "alcohol_consumption": alcohol_consumption,
                "exercise_frequency": exercise_frequency,
                
                # Surgery Details
                "number_of_heart_surgeries": number_of_heart_surgeries,
                "surgery_type": surgery_type,
                "surgery_category": "Major",  # Will be auto-detected by backend
                "surgery_complexity": "Medium",  # Will be auto-detected by backend
                "surgery_duration_hours": surgery_duration_hours,
                
                # Additional Info (for encryption)
                "medical_history": medical_history,
                "chronic_conditions": chronic_conditions_list.split("\n") if chronic_conditions_list else [],
                "medications": medications.split("\n") if medications else [],
                "allergies": allergies.split("\n") if allergies else [],
                "previous_surgeries": previous_surgeries.split("\n") if previous_surgeries else [],
                
                # Pre-Surgery Risk Factors
                "pre_surgery_notes": pre_surgery_notes,
                "other_risk_factors": other_risk_factors.split("\n") if other_risk_factors else []
            }
            
            with st.spinner("Submitting registration..."):
                response = make_request("/patient-registration", "POST", data=data)
                
                if response and response.status_code == 200:
                    result = response.json()
                    st.success("✅ Registration completed successfully!")
                    if "note" in result:
                        st.info(f"ℹ️ {result['note']}")
                    st.session_state.is_first_login = False
                    st.balloons()
                    st.rerun()
                elif response and response.status_code == 400:
                    result = response.json()
                    st.error(f"❌ {result.get('detail', 'Registration failed. Profile already exists.')}")
                    if st.button("Go to Profile Page"):
                        st.session_state.is_first_login = False
                        st.rerun()
                else:
                    st.error("❌ Registration failed. Please try again.")

def home_page():
    """Home page"""
    st.title("🏥 MediSage AI - Intelligent Medical Assistant")
    
    st.markdown("""
    ## Welcome to MediSage AI
    
    Your comprehensive AI-powered medical assistant for post-surgery risk prediction, 
    medical consultation, and scan interpretation.
    
    ### Our Features:
    
    - **🎯 Risk Prediction**: Advanced ML-based post-surgery risk assessment using ensemble models
    - **💬 Medical Chatbot**: Context-aware AI assistant for medical queries
    - **🔬 Scan Interpretation**: AI-powered interpretation of medical scans and X-rays
    
    ### How It Works:
    
    1. **Secure Authentication**: Your data is encrypted and securely stored
    2. **Patient Profile**: Complete your medical history once
    3. **AI Analysis**: Get instant predictions and insights
    4. **Continuous Support**: 24/7 medical chatbot assistance
    
    ### Technology Stack:
    
    - **ML Models**: XGBoost, Random Forest, Gradient Boosting, SVM (Voting Ensemble)
    - **AI**: Google Gemini API for conversational AI and scan interpretation
    - **Security**: End-to-end encryption for patient data
    - **RAG**: Retrieval-Augmented Generation for context-aware responses
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Accuracy", "90%>", "ML Model Performance")
    with col2:
        st.metric("Response Time", "<2s", "Average API Response")
    with col3:
        st.metric("Security", "AES-256", "Encryption Standard")

def risk_prediction_page():
    """Risk prediction page"""
    st.title("🎯 Post-Surgery Risk Prediction")
    
    tab1, tab2 = st.tabs(["Manual Input", "Upload Medical Report"])
    
    with tab1:
        st.subheader("Enter Patient Data")
        
        use_profile = st.checkbox("Use my patient profile data")
        
        if not use_profile:
            st.info("📊 Enter at least 15 features for accurate risk prediction")
            
            # Organize into expandable sections
            with st.expander("👤 Basic Demographics", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    age = st.number_input("Age *", min_value=1, max_value=120, value=50)
                    sex = st.selectbox("Sex *", ["Male", "Female"])
                    weight_kg = st.number_input("Weight (kg)", min_value=20, max_value=200, value=70)
                with col2:
                    height_cm = st.number_input("Height (cm)", min_value=50, max_value=250, value=170)
                    bmi = round(weight_kg / ((height_cm/100) ** 2), 1)
                    st.metric("Calculated BMI", bmi)
                    residence = st.selectbox("Residence", ["Urban", "Rural", "Semi-Urban"])
            
            with st.expander("💓 Vital Signs & Cardiac Health", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    systolic_bp = st.number_input("Systolic BP (mmHg) *", min_value=80, max_value=200, value=120)
                    diastolic_bp = st.number_input("Diastolic BP (mmHg) *", min_value=40, max_value=130, value=80)
                    pulse_rate = st.number_input("Pulse Rate (bpm)", min_value=40, max_value=150, value=75)
                with col2:
                    ejection_fraction = st.number_input("Ejection Fraction (%) *", min_value=10, max_value=80, value=55)
                    cardiac_rhythm = st.selectbox("Cardiac Rhythm", ["Normal", "AFib", "Flutter"])
                    nyha_class = st.selectbox("NYHA Class", ["I", "II", "III", "IV"])
            
            with st.expander("🏥 Medical Conditions", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Chronic Conditions**")
                    hypertension = st.selectbox("Hypertension *", ["No", "Yes"])
                    diabetes = st.selectbox("Diabetes *", ["No", "Yes"])
                    heart_failure = st.selectbox("Heart Failure", ["No", "Yes"])
                    atrial_fibrillation = st.selectbox("Atrial Fibrillation", ["No", "Yes"])
                with col2:
                    st.markdown("**Lifestyle & History**")
                    smoking = st.selectbox("Smoking *", ["No", "Yes"])
                    Affected_by_Covid = st.selectbox("Affected by COVID-19", ["No", "Yes"])
                    family_history = st.selectbox("Family History of Heart Disease", ["No", "Yes"])
                    type_of_heart_disease = st.selectbox("Type of Heart Disease", ["None", "CAD", "Valve", "Arrhythmia", "CHF"])
            
            with st.expander("💊 Surgery Details", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    surgery_types = [
                        # Major Surgeries
                        "CABG", "Valve Replacement", "Valve Repair", "Aortic Valve Replacement", 
                        "Mitral Valve Replacement", "Bypass Surgery", "Heart Transplant", 
                        "Coronary Artery Bypass Graft", "Open Heart Surgery", "Aortic Aneurysm Repair", 
                        "LVAD Implantation",
                        # Intermediate Surgeries
                        "Angioplasty", "PCI", "Stent Placement", "Coronary Stenting", 
                        "Ablation", "Cardiac Ablation", "ASD Closure", "VSD Closure", 
                        "PDA Closure", "TAVI", "TAVR", "MitraClip",
                        # Minor Surgeries
                        "Pacemaker Implantation", "Pacemaker", "ICD Implantation", 
                        "Defibrillator Implantation", "CRT Device Implantation", 
                        "Cardiac Catheterization", "Diagnostic Catheterization", 
                        "Cardiac Monitoring Device", "Loop Recorder Implantation"
                    ]
                    surgery_type = st.selectbox("Surgery Type *", surgery_types)
                    st.info("ℹ️ Category & complexity are auto-detected based on surgery type")
                with col2:
                    number_of_heart_surgeries = st.number_input("Previous Heart Surgeries", min_value=0, max_value=10, value=0)
                    surgery_duration_hours = st.number_input("Expected Surgery Duration (hours)", min_value=0.5, max_value=12.0, value=4.0, step=0.5)
            
            with st.expander("⚠️ Pre-Surgery Risk Factors", expanded=False):
                st.markdown("Document any serious conditions or risk factors mentioned before surgery")
                col1, col2 = st.columns(2)
                with col1:
                    pre_surgery_notes = st.text_area(
                        "Pre-Surgery Notes",
                        help="Important risk factors, serious conditions, or concerns mentioned before surgery",
                        height=100,
                        placeholder="E.g., Patient has severe diabetes and recent MI"
                    )
                with col2:
                    other_risk_factors_input = st.text_area(
                        "Other Risk Factors (one per line)",
                        help="E.g., 'having diabetes', 'history of stroke', 'kidney disease'",
                        height=100,
                        placeholder="having diabetes\nhistory of stroke\nkidney disease"
                    )
        
        if st.button("Predict Risk"):
            data = {
                "use_profile": use_profile
            }
            
            if not use_profile:
                data["patient_data"] = {
                    # Demographics
                    "age": age,
                    "sex": sex,
                    "height_cm": height_cm,
                    "weight_kg": weight_kg,
                    "bmi": bmi,
                    "residence": residence,
                    
                    # Vital Signs
                    "systolic_bp": systolic_bp,
                    "diastolic_bp": diastolic_bp,
                    "pulse_rate": pulse_rate,
                    
                    # Cardiac
                    "ejection_fraction": ejection_fraction,
                    "cardiac_rhythm": cardiac_rhythm,
                    "nyha_class": nyha_class,
                    "type_of_heart_disease": type_of_heart_disease,
                    
                    # Medical Conditions (convert Yes/No to 1/0)
                    "hypertension": 1 if hypertension == "Yes" else 0,
                    "diabetes": 1 if diabetes == "Yes" else 0,
                    "heart_failure": 1 if heart_failure == "Yes" else 0,
                    "atrial_fibrillation": 1 if atrial_fibrillation == "Yes" else 0,
                    "Affected_by_Covid": 1 if Affected_by_Covid == "Yes" else 0,
                    "family_history": 1 if family_history == "Yes" else 0,
                    
                    # Lifestyle
                    "smoking": smoking,
                    
                    # Surgery
                    "surgery_type": surgery_type,
                    "surgery_category": "Major",  # Will be auto-detected by backend
                    "surgery_complexity": "Medium",  # Will be auto-detected by backend
                    "surgery_duration_hours": surgery_duration_hours,
                    "number_of_heart_surgeries": number_of_heart_surgeries,
                    
                    # Pre-Surgery Risk Factors
                    "pre_surgery_notes": pre_surgery_notes,
                    "other_risk_factors": other_risk_factors_input.split("\n") if other_risk_factors_input else []
                }
            
            response = make_request("/api/predict-risk", "POST", data=data)
            
            if response and response.status_code == 200:
                result = response.json()
                
                st.success("Prediction Complete!")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Risk Level", result["risk_level"])
                with col2:
                    st.metric("Risk Score", f"{result['risk_score']}%")
                with col3:
                    st.metric("Recovery Days", result["recovery_days"])
                
                # Risk gauge chart
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=result["risk_score"],
                    title={'text': "Risk Score"},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 30], 'color': "lightgreen"},
                            {'range': [30, 60], 'color': "yellow"},
                            {'range': [60, 80], 'color': "orange"},
                            {'range': [80, 100], 'color': "red"}
                        ]
                    }
                ))
                st.plotly_chart(fig)
                
                # Probabilities
                st.subheader("Risk Probabilities")
                prob_data = result.get("risk_probabilities", {})
                if prob_data:
                    for level, prob in prob_data.items():
                        st.progress(prob / 100, text=f"{level}: {prob}%")
                
                # Top influential features (SHAP explainability)
                st.subheader("🔍 Top 3 Influential Features")
                st.write("These features had the most impact on the prediction:")
                
                top_features = result.get("top_features", [])
                if top_features:
                    for i, feature_info in enumerate(top_features, 1):
                        feature_name = feature_info['feature'].replace('_', ' ').title()
                        importance = feature_info['importance']
                        
                        # Create a nice display for each feature
                        with st.container():
                            col_a, col_b = st.columns([3, 1])
                            with col_a:
                                st.write(f"**{i}. {feature_name}**")
                            with col_b:
                                st.write(f"Impact: {importance:.3f}")
                            
                            # Visual bar
                            st.progress(min(importance, 1.0))
                else:
                    st.info("Feature importance analysis not available")
                
                # Display consequences analysis from Gemini
                st.divider()
                st.subheader("⚠️ Surgery Consequences & Recommendations")
                st.markdown("**What happens if the patient undergoes surgery:**")
                
                consequences = result.get("consequences", "")
                if consequences and consequences != "Consequence analysis unavailable.":
                    st.markdown(consequences)
                else:
                    # Fallback if Gemini is unavailable
                    st.info("💡 AI-powered consequence analysis is currently unavailable. Please consult with your surgeon for personalized guidance.")
                    
                    # Show basic consequence info based on risk level
                    risk_level = result.get("risk_level", "Medium")
                    if risk_level == "Low":
                        st.success("✅ **Low Risk Surgery**: Generally favorable outcomes expected with proper post-operative care.")
                    elif risk_level == "Medium":
                        st.warning("⚠️ **Medium Risk Surgery**: Moderate complications possible. Close monitoring recommended during recovery.")
                    elif risk_level == "High":
                        st.error("🔴 **High Risk Surgery**: Significant complications possible. Intensive post-operative care required.")
                    else:
                        st.error("🛑 **Critical Risk Surgery**: Severe complications likely. Requires specialized care and extended monitoring.")
            else:
                st.error("Prediction failed. Make sure models are trained.")
    
    with tab2:
        st.subheader("Upload Medical Report (PDF)")
        st.info("📝 Upload a medical report to automatically extract features and predict risk")
        
        uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
        
        if uploaded_file and st.button("🔍 Extract Features & Predict Risk", type="primary", use_container_width=True):
            with st.spinner("Analyzing medical report with NLP..."):
                files = {"file": uploaded_file.getvalue()}
                response = make_request("/api/extract-from-report", "POST", files={"file": uploaded_file})
                
                if response and response.status_code == 200:
                    result = response.json()
                    
                    # Show extraction success
                    st.success(f"✅ Successfully extracted {result.get('features_count', 0)} features from report!")
                    
                    # Show prediction results (same format as manual input)
                    st.divider()
                    st.subheader("🎯 Prediction Results")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        risk_level = result.get("risk_level", "Unknown")
                        risk_color = {"Low": "🟢", "Medium": "🟡", "High": "🟠", "Critical": "🔴"}.get(risk_level, "⚪")
                        st.metric("Risk Level", f"{risk_color} {risk_level}")
                    with col2:
                        st.metric("Risk Score", f"{result.get('risk_score', 0)}%")
                    with col3:
                        st.metric("Recovery Days", result.get("recovery_days", "N/A"))
                    
                    # Risk gauge chart
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=result.get("risk_score", 0),
                        title={'text': "Risk Score"},
                        gauge={
                            'axis': {'range': [None, 100]},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [0, 30], 'color': "lightgreen"},
                                {'range': [30, 60], 'color': "yellow"},
                                {'range': [60, 80], 'color': "orange"},
                                {'range': [80, 100], 'color': "red"}
                            ]
                        }
                    ))
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Risk Probabilities
                    st.subheader("📊 Risk Probabilities")
                    prob_data = result.get("risk_probabilities", {})
                    if prob_data:
                        for level, prob in prob_data.items():
                            st.progress(prob / 100, text=f"{level}: {prob}%")
                    
                    # Top influential features
                    st.subheader("🔍 Top 3 Influential Features")
                    st.write("These features had the most impact on the prediction:")
                    
                    top_features = result.get("top_features", [])
                    if top_features:
                        for i, feature_info in enumerate(top_features, 1):
                            feature_name = feature_info.get('feature', 'Unknown')
                            importance = feature_info.get('importance', 0)
                            
                            col_a, col_b = st.columns([3, 1])
                            with col_a:
                                st.write(f"**{i}. {feature_name}**")
                            with col_b:
                                st.write(f"Impact: {importance:.3f}")
                            
                            st.progress(min(importance, 1.0))
                    else:
                        st.info("Feature importance analysis not available")
                    
                    # Display consequences analysis from Gemini
                    st.divider()
                    st.subheader("⚠️ Surgery Consequences & Recommendations")
                    consequences = result.get("consequences", "")
                    if consequences and consequences != "Consequence analysis unavailable.":
                        st.markdown(consequences)
                    else:
                        st.info("💡 AI-powered consequence analysis is currently unavailable. Please consult with your surgeon for personalized guidance.")
                    
                    # Show Gemini report analysis
                    if result.get("gemini_success"):
                        st.divider()
                        st.subheader("🤖 AI Medical Report Analysis")
                        with st.expander("📄 View Detailed Gemini Analysis", expanded=True):
                            gemini_summary = result.get("gemini_summary", "Analysis unavailable")
                            st.markdown(gemini_summary)
                            
                            # Show extracted risk factors if available
                            if result.get("extracted_features", {}).get("other_risk_factors"):
                                st.subheader("⚠️ Identified Risk Factors")
                                risk_factors = result.get("extracted_features", {}).get("other_risk_factors", "")
                                if isinstance(risk_factors, str) and risk_factors:
                                    factors_list = risk_factors.split("|")
                                    for factor in factors_list:
                                        st.markdown(f"- ⚠️ {factor}")
                                elif isinstance(risk_factors, list):
                                    for factor in risk_factors:
                                        st.markdown(f"- ⚠️ {factor}")
                    
                    # Show extracted features in expandable section
                    st.divider()
                    with st.expander("📝 View All Extracted Features & Report Text"):
                        st.subheader("Extracted Features")
                        extracted = result.get("extracted_features", {})
                        
                        # Display in organized tabs
                        tab_demo, tab_vital, tab_cardiac, tab_conditions = st.tabs([
                            "Demographics", "Vital Signs", "Cardiac", "Conditions"
                        ])
                        
                        with tab_demo:
                            st.json({
                                "age": extracted.get("age"),
                                "sex": extracted.get("sex"),
                                "height_cm": extracted.get("height_cm"),
                                "weight_kg": extracted.get("weight_kg"),
                                "bmi": extracted.get("bmi")
                            })
                        
                        with tab_vital:
                            st.json({
                                "systolic_bp": extracted.get("systolic_bp"),
                                "diastolic_bp": extracted.get("diastolic_bp"),
                                "pulse_rate": extracted.get("pulse_rate")
                            })
                        
                        with tab_cardiac:
                            st.json({
                                "ejection_fraction": extracted.get("ejection_fraction"),
                                "cardiac_rhythm": extracted.get("cardiac_rhythm"),
                                "type_of_heart_disease": extracted.get("type_of_heart_disease"),
                                "nyha_class": extracted.get("nyha_class")
                            })
                        
                        with tab_conditions:
                            st.json({
                                "hypertension": extracted.get("hypertension"),
                                "diabetes": extracted.get("diabetes"),
                                "heart_failure": extracted.get("heart_failure"),
                                "atrial_fibrillation": extracted.get("atrial_fibrillation"),
                                "Affected_by_Covid": extracted.get("Affected_by_Covid"),
                                "smoking": extracted.get("smoking")
                            })
                        
                        # Surgery details
                        st.subheader("🏥 Surgery Details")
                        st.json({
                            "surgery_type": extracted.get("surgery_type"),
                            "surgery_category": extracted.get("surgery_category"),
                            "surgery_complexity": extracted.get("surgery_complexity"),
                            "number_of_heart_surgeries": extracted.get("number_of_heart_surgeries")
                        })
                        
                        # Pre-surgery risk factors
                        if extracted.get("pre_surgery_notes") or extracted.get("other_risk_factors"):
                            st.subheader("⚠️ Pre-Surgery Risk Factors")
                            if extracted.get("pre_surgery_notes"):
                                st.text_area("Pre-Surgery Notes:", extracted.get("pre_surgery_notes"), height=100, disabled=True)
                            if extracted.get("other_risk_factors"):
                                st.write("**Other Risk Factors:**")
                                risk_factors = extracted.get("other_risk_factors")
                                if isinstance(risk_factors, str):
                                    for factor in risk_factors.split("|"):
                                        if factor:
                                            st.markdown(f"- {factor}")
                                elif isinstance(risk_factors, list):
                                    for factor in risk_factors:
                                        st.markdown(f"- {factor}")
                        
                        st.subheader("Report Preview")
                        st.text_area("First 500 characters:", result.get("extracted_text", ""), height=150, disabled=True)
                
                else:
                    st.error("❌ Failed to process medical report. Please check the file format.")

def chatbot_page():
    """RAG Chatbot page"""
    st.title("💬 Medical Chatbot")
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about your health..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get bot response
        data = {"message": prompt}
        response = make_request("/api/chat", "POST", data=data)
        
        if response and response.status_code == 200:
            result = response.json()
            bot_message = result["response"]
            
            st.session_state.messages.append({"role": "assistant", "content": bot_message})
            with st.chat_message("assistant"):
                st.markdown(bot_message)
        else:
            st.error("Failed to get response")

def profile_page():
    """Patient profile page with view and edit capabilities"""
    st.title("👤 My Medical Profile")
    
    # Fetch profile
    response = make_request("/patient-profile", "GET")
    
    if not response or response.status_code != 200:
        st.error("❌ Unable to load profile. Please try again.")
        return
    
    profile = response.json()
    
    # Toggle between view and edit mode
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    
    col1, col2, col3 = st.columns([3, 1, 1])
    with col2:
        if st.button("✏️ Edit Profile" if not st.session_state.edit_mode else "🔙 Cancel Edit", use_container_width=True):
            st.session_state.edit_mode = not st.session_state.edit_mode
            st.rerun()
    
    if not st.session_state.edit_mode:
        # VIEW MODE - Display all information
        st.divider()
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "👤 Basic Info",
            "💓 Vital Signs",
            "🏥 Medical History",
            "💊 Surgery Info",
            "📝 Additional"
        ])
        
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Age", profile.get('age'))
                st.metric("Sex", profile.get('sex'))
                st.metric("Blood Group", profile.get('blood_group'))
                st.metric("Height (cm)", profile.get('height_cm'))
            with col2:
                st.metric("Weight (kg)", profile.get('weight_kg'))
                bmi = round(profile.get('weight_kg', 70) / ((profile.get('height_cm', 170)/100) ** 2), 1)
                st.metric("BMI", bmi)
                st.metric("Residence", profile.get('residence', 'N/A'))
                st.metric("Contact", profile.get('contact_number'))
        
        with tab2:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Systolic BP", f"{profile.get('systolic_bp', 'N/A')} mmHg")
                st.metric("Diastolic BP", f"{profile.get('diastolic_bp', 'N/A')} mmHg")
                st.metric("Pulse Rate", f"{profile.get('pulse_rate', 'N/A')} bpm")
                st.metric("Ejection Fraction", f"{profile.get('ejection_fraction', 'N/A')}%")
            with col2:
                st.metric("Heart Disease Type", profile.get('type_of_heart_disease', 'N/A'))
                st.metric("Cardiac Rhythm", profile.get('cardiac_rhythm', 'N/A'))
                st.metric("NYHA Class", profile.get('nyha_class', 'N/A'))
        
        with tab3:
            st.subheader("Conditions")
            conditions = []
            if profile.get('hypertension'): conditions.append("✔️ Hypertension")
            if profile.get('diabetes'): conditions.append("✔️ Diabetes")
            if profile.get('heart_failure'): conditions.append("✔️ Heart Failure")
            if profile.get('atrial_fibrillation'): conditions.append("✔️ Atrial Fibrillation")
            if profile.get('Affected_by_Covid'): conditions.append("✔️ COVID-19 Affected")
            if profile.get('family_history'): conditions.append("✔️ Family History")
            
            if conditions:
                for condition in conditions:
                    st.write(condition)
            else:
                st.info("No chronic conditions recorded")
            
            st.subheader("Lifestyle")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Smoking:** {profile.get('smoking', 'N/A')}")
                st.write(f"**Smoking History:** {profile.get('smoking_history', 'N/A')}")
            with col2:
                st.write(f"**Alcohol:** {profile.get('alcohol_consumption', 'N/A')}")
                st.write(f"**Exercise:** {profile.get('exercise_frequency', 'N/A')}")
            
            st.subheader("Medical History")
            st.text_area("Details", profile.get('medical_history', 'None recorded'), disabled=True, height=100)
        
        with tab4:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Previous Heart Surgeries", profile.get('number_of_heart_surgeries', 0))
                st.metric("Surgery Type", profile.get('surgery_type', 'N/A'))
                st.metric("Surgery Category", profile.get('surgery_category', 'N/A'))
            with col2:
                st.metric("Surgery Complexity", profile.get('surgery_complexity', 'N/A') + " (Auto-detected)")
                st.metric("Expected Duration (hrs)", profile.get('surgery_duration_hours', 'N/A'))
            
            # Display pre-surgery notes if available
            if profile.get('pre_surgery_notes'):
                st.subheader("Pre-Surgery Risk Factors")
                st.text_area("Notes from doctor/patient", profile.get('pre_surgery_notes', ''), disabled=True, height=100)
        
        with tab5:
            st.subheader("Medications")
            meds = profile.get('medications', [])
            if meds and meds != ['']:
                for med in meds:
                    if med.strip():
                        st.write(f"• {med}")
            else:
                st.info("No medications recorded")
            
            st.subheader("Allergies")
            allergies = profile.get('allergies', [])
            if allergies and allergies != ['']:
                for allergy in allergies:
                    if allergy.strip():
                        st.write(f"⚠️ {allergy}")
            else:
                st.info("No allergies recorded")
    
    else:
        # EDIT MODE - Show editable form (reuse registration form logic)
        st.info("✏️ Edit Mode: Update your medical information below")
        
        # Create tabs for organized editing
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "👤 Basic Info",
            "💓 Vital Signs & Cardiac",
            "🏥 Medical Conditions",
            "💊 Surgery & Treatment",
            "📝 Additional Info"
        ])
        
        # Pre-fill all form fields with existing data
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                age = st.number_input("Age *", value=profile.get('age', 50))
                sex = st.selectbox("Sex *", ["Male", "Female"], index=0 if profile.get('sex') == 'Male' else 1)
                blood_group = st.selectbox("Blood Group *", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"],
                                          index=["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"].index(profile.get('blood_group', 'O+')))
                height_cm = st.number_input("Height (cm) *", value=profile.get('height_cm', 170))
                weight_kg = st.number_input("Weight (kg) *", value=profile.get('weight_kg', 70))
            with col2:
                contact_number = st.text_input("Contact Number *", value=profile.get('contact_number', ''))
                residence = st.selectbox("Residence", ["Urban", "Rural", "Semi-Urban"],
                                        index=["Urban", "Rural", "Semi-Urban"].index(profile.get('residence', 'Urban')))
        
        with tab2:
            col1, col2 = st.columns(2)
            with col1:
                systolic_bp = st.number_input("Systolic BP", value=profile.get('systolic_bp', 120))
                diastolic_bp = st.number_input("Diastolic BP", value=profile.get('diastolic_bp', 80))
                pulse_rate = st.number_input("Pulse Rate", value=profile.get('pulse_rate', 75))
                type_of_heart_disease = st.selectbox("Heart Disease Type",
                    ["None", "CAD", "Valve", "Arrhythmia", "CHF"],
                    index=["None", "CAD", "Valve", "Arrhythmia", "CHF"].index(profile.get('type_of_heart_disease', 'None')))
                ejection_fraction = st.number_input("Ejection Fraction", value=profile.get('ejection_fraction', 55))
            with col2:
                cardiac_rhythm = st.selectbox("Cardiac Rhythm", ["Normal", "AFib", "Flutter"],
                    index=["Normal", "AFib", "Flutter"].index(profile.get('cardiac_rhythm', 'Normal')))
                nyha_class = st.selectbox("NYHA Class", ["I", "II", "III", "IV"],
                    index=["I", "II", "III", "IV"].index(profile.get('nyha_class', 'I')))
        
        with tab3:
            col1, col2 = st.columns(2)
            with col1:
                hypertension = st.checkbox("Hypertension", value=bool(profile.get('hypertension')))
                diabetes = st.checkbox("Diabetes", value=bool(profile.get('diabetes')))
                heart_failure = st.checkbox("Heart Failure", value=bool(profile.get('heart_failure')))
                atrial_fibrillation = st.checkbox("Atrial Fibrillation", value=bool(profile.get('atrial_fibrillation')))
                Affected_by_Covid = st.checkbox("COVID-19", value=bool(profile.get('Affected_by_Covid')))
                family_history_bin = st.checkbox("Family History", value=bool(profile.get('family_history')))
            with col2:
                smoking = st.selectbox("Smoking", ["No", "Yes"], index=1 if profile.get('smoking') == 'Yes' else 0)
                smoking_history = st.selectbox("Smoking History", ["Never", "Former", "Current"],
                    index=["Never", "Former", "Current"].index(profile.get('smoking_history', 'Never')))
                alcohol_consumption = st.selectbox("Alcohol", ["None", "Moderate", "High"],
                    index=["None", "Moderate", "High"].index(profile.get('alcohol_consumption', 'None')))
                exercise_frequency = st.selectbox("Exercise", ["Regular", "Rare", "None"],
                    index=["Regular", "Rare", "None"].index(profile.get('exercise_frequency', 'Regular')))
            medical_history = st.text_area("Medical History", value=profile.get('medical_history', ''))
            chronic_conditions = profile.get('chronic_conditions', [])
            if isinstance(chronic_conditions, str):
                chronic_conditions_list = st.text_area("Chronic Conditions", value=chronic_conditions)
            else:
                chronic_conditions_list = st.text_area("Chronic Conditions", value='\n'.join(chronic_conditions) if chronic_conditions else '')
        
        with tab4:
            col1, col2 = st.columns(2)
            with col1:
                number_of_heart_surgeries = st.number_input("Previous Surgeries", value=profile.get('number_of_heart_surgeries', 0))
                surgery_type = st.selectbox("Surgery Type *", ["CABG", "Valve Replacement", "Bypass", "Pacemaker", "Angioplasty", "Stent Placement", "Ablation"],
                    index=["CABG", "Valve Replacement", "Bypass", "Pacemaker", "Angioplasty", "Stent Placement", "Ablation"].index(profile.get('surgery_type', 'CABG')) if profile.get('surgery_type') in ["CABG", "Valve Replacement", "Bypass", "Pacemaker", "Angioplasty", "Stent Placement", "Ablation"] else 0)
                st.info("ℹ️ Surgery category and complexity will be auto-detected based on surgery type")
            with col2:
                surgery_duration_hours = st.number_input("Duration (hrs)", value=float(profile.get('surgery_duration_hours', 4.0)))
                prev_surgeries = profile.get('previous_surgeries', [])
                previous_surgeries = st.text_area("Previous Surgeries List", 
                    value='\n'.join(prev_surgeries) if isinstance(prev_surgeries, list) else str(prev_surgeries or ''))
            
            # Pre-surgery risk factors
            st.subheader("Pre-Surgery Risk Factors")
            pre_surgery_notes = st.text_area(
                "Important risk factors mentioned by doctor/patient before surgery",
                value=profile.get('pre_surgery_notes', ''),
                height=100,
                help="Document any serious conditions or concerns mentioned before surgery"
            )
            other_risk_factors_list = profile.get('other_risk_factors', [])
            other_risk_factors = st.text_area(
                "Other Risk Factors (one per line)",
                value='\n'.join(other_risk_factors_list) if isinstance(other_risk_factors_list, list) else str(other_risk_factors_list or ''),
                height=80,
                help="E.g., 'having diabetes', 'history of stroke', 'kidney disease'"
            )
        
        with tab5:
            col1, col2 = st.columns(2)
            with col1:
                meds = profile.get('medications', [])
                medications = st.text_area("Medications", 
                    value='\n'.join(meds) if isinstance(meds, list) else str(meds or ''))
            with col2:
                allergy_list = profile.get('allergies', [])
                allergies = st.text_area("Allergies", 
                    value='\n'.join(allergy_list) if isinstance(allergy_list, list) else str(allergy_list or ''))
        
        # Save button
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("💾 Save Changes", use_container_width=True, type="primary"):
                update_data = {
                    "age": age, "sex": sex, "blood_group": blood_group,
                    "height_cm": height_cm, "weight_kg": weight_kg,
                    "contact_number": contact_number, "residence": residence,
                    "systolic_bp": systolic_bp, "diastolic_bp": diastolic_bp,
                    "pulse_rate": pulse_rate,
                    "hypertension": 1 if hypertension else 0,
                    "diabetes": 1 if diabetes else 0,
                    "heart_failure": 1 if heart_failure else 0,
                    "atrial_fibrillation": 1 if atrial_fibrillation else 0,
                    "Affected_by_Covid": 1 if Affected_by_Covid else 0,
                    "family_history": 1 if family_history_bin else 0,
                    "type_of_heart_disease": type_of_heart_disease,
                    "ejection_fraction": ejection_fraction,
                    "cardiac_rhythm": cardiac_rhythm,
                    "nyha_class": nyha_class,
                    "smoking": smoking, "smoking_history": smoking_history,
                    "alcohol_consumption": alcohol_consumption,
                    "exercise_frequency": exercise_frequency,
                    "number_of_heart_surgeries": number_of_heart_surgeries,
                    "surgery_type": surgery_type,
                    "surgery_category": "Major",  # Will be auto-detected by backend
                    "surgery_complexity": "Medium",  # Will be auto-detected by backend
                    "surgery_duration_hours": surgery_duration_hours,
                    "medical_history": medical_history,
                    "chronic_conditions": chronic_conditions_list.split("\n") if chronic_conditions_list else [],
                    "medications": medications.split("\n") if medications else [],
                    "allergies": allergies.split("\n") if allergies else [],
                    "previous_surgeries": previous_surgeries.split("\n") if previous_surgeries else [],
                    "pre_surgery_notes": pre_surgery_notes,
                    "other_risk_factors": other_risk_factors.split("\n") if other_risk_factors else []
                }
                
                with st.spinner("Saving changes..."):
                    response = make_request("/patient-profile", "PUT", data=update_data)
                    
                    if response and response.status_code == 200:
                        st.success("✅ Profile updated successfully!")
                        st.session_state.edit_mode = False
                        st.rerun()
                    else:
                        st.error("❌ Failed to update profile. Please try again.")

def scan_interpretation_page():
    """Scan interpretation page"""
    st.title("🔬 Medical Scan Interpretation")
    
    st.write("Upload X-rays, CT scans, MRI images, or medical reports for AI interpretation")
    
    uploaded_file = st.file_uploader(
        "Choose a file", 
        type=["pdf", "jpg", "jpeg", "png", "webp", "bmp", "tiff", "tif", "gif"]
    )
    
    if uploaded_file:
        # Display uploaded file
        if uploaded_file.type == "application/pdf":
            st.write("📄 PDF uploaded")
        else:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Scan", use_container_width=True)
        
        if st.button("Interpret Scan"):
            with st.spinner("Analyzing scan..."):
                # Reset file pointer to beginning
                uploaded_file.seek(0)
                
                # Prepare file for upload
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                
                response = make_request(
                    "/api/interpret-scan", 
                    "POST", 
                    files=files
                )
                
                if response and response.status_code == 200:
                    result = response.json()
                    
                    st.success("✅ Analysis Complete!")
                    
                    # Display interpretation in a nice card
                    st.markdown("---")
                    st.subheader("👨‍⚕️ Doctor's Explanation (In Simple Words)")
                    
                    # Show interpretation with good visibility
                    st.info(result['interpretation'])
                    
                    st.markdown("---")
                    
                    # Download button for PDF
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        # Generate PDF content
                        try:
                            from reportlab.lib.pagesizes import letter
                            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                            from reportlab.lib.units import inch
                            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
                            from reportlab.lib.enums import TA_CENTER, TA_LEFT
                            
                            buffer = BytesIO()
                            doc = SimpleDocTemplate(buffer, pagesize=letter)
                            story = []
                            styles = getSampleStyleSheet()
                            
                            # Title style
                            title_style = ParagraphStyle(
                                'CustomTitle',
                                parent=styles['Heading1'],
                                fontSize=24,
                                textColor='#2196F3',
                                spaceAfter=30,
                                alignment=TA_CENTER
                            )
                            
                            # Body style
                            body_style = ParagraphStyle(
                                'CustomBody',
                                parent=styles['Normal'],
                                fontSize=12,
                                leading=20,
                                spaceAfter=12
                            )
                            
                            # Add title
                            story.append(Paragraph("Medical Scan Interpretation", title_style))
                            story.append(Spacer(1, 0.2*inch))
                            
                            # Add date and file info
                            info_text = f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>"
                            info_text += f"<b>File:</b> {result.get('filename', 'N/A')}<br/>"
                            info_text += f"<b>Type:</b> {result.get('file_type', 'N/A').upper()}"
                            story.append(Paragraph(info_text, body_style))
                            story.append(Spacer(1, 0.3*inch))
                            
                            # Add interpretation heading
                            heading_style = ParagraphStyle(
                                'Heading',
                                parent=styles['Heading2'],
                                fontSize=16,
                                textColor='#333333',
                                spaceAfter=15
                            )
                            story.append(Paragraph("Doctor's Explanation (In Simple Words)", heading_style))
                            
                            # Add interpretation text
                            interpretation_text = result['interpretation'].replace('\n', '<br/>')
                            story.append(Paragraph(interpretation_text, body_style))
                            
                            # Add disclaimer
                            story.append(Spacer(1, 0.4*inch))
                            disclaimer_style = ParagraphStyle(
                                'Disclaimer',
                                parent=styles['Normal'],
                                fontSize=10,
                                textColor='#666666',
                                leftIndent=20,
                                rightIndent=20,
                                borderWidth=1,
                                borderColor='#CCCCCC',
                                borderPadding=10
                            )
                            disclaimer_text = (
                                "<b>Important Note:</b> This is an AI-generated explanation to help you understand "
                                "your scan. It is NOT a final diagnosis. Please show this to your doctor and follow "
                                "their professional medical advice."
                            )
                            story.append(Paragraph(disclaimer_text, disclaimer_style))
                            
                            # Build PDF
                            doc.build(story)
                            pdf_data = buffer.getvalue()
                            buffer.close()
                            
                            # Download button
                            filename = f"scan_interpretation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                            st.download_button(
                                label="📥 Download PDF",
                                data=pdf_data,
                                file_name=filename,
                                mime="application/pdf",
                                use_container_width=True
                            )
                        except ImportError:
                            st.error("📦 PDF generation requires reportlab. Install with: pip install reportlab")
                    
                    st.markdown("---")
                    
                    # Important disclaimer
                    st.warning(
                        "💡 **Important Note:**\n\n"
                        "This is an AI explanation to help you understand your scan. "
                        "It is NOT a final diagnosis.\n\n"
                        "✅ **Next Steps:**\n"
                        "- Show this to your doctor\n"
                        "- Ask questions if you don't understand something\n"
                        "- Follow your doctor's advice, not just this AI explanation"
                    )
                    
                    # File info
                    with st.expander("📝 Scan Details"):
                        st.write(f"**File Name:** {result.get('filename', 'N/A')}")
                        st.write(f"**File Type:** {result.get('file_type', 'N/A').upper()}")
                
                else:
                    st.error("❌ Interpretation failed. Please try again or contact support.")

def main():
    """Main app"""
    # Check authentication
    if not st.session_state.token:
        login_page()
        return
    
    # Check first login
    if st.session_state.is_first_login:
        patient_registration_page()
        return
    
    # Sidebar navigation
    with st.sidebar:
        st.title("🏥 MediSage AI")
        
        selected = option_menu(
            menu_title=None,
            options=["Home", "Profile", "Risk Prediction", "Medical Chatbot", "Scan Interpretation"],
            icons=["house", "person-circle", "activity", "chat", "file-medical"],
            default_index=0
        )
        
        st.divider()
        
        if st.button("Logout"):
            st.session_state.token = None
            st.session_state.is_first_login = False
            st.session_state.messages = []
            st.rerun()
    
    # Route to pages
    if selected == "Home":
        home_page()
    elif selected == "Profile":
        profile_page()
    elif selected == "Risk Prediction":
        risk_prediction_page()
    elif selected == "Medical Chatbot":
        chatbot_page()
    elif selected == "Scan Interpretation":
        scan_interpretation_page()

if __name__ == "__main__":
    main()
