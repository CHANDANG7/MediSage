import os

def w(p, c):
    os.makedirs(os.path.dirname(p) if os.path.dirname(p) else '.', exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f: f.write(c)
    print(f"✅ {p}")

print("🚀 Creating API Routes & Frontend...\n")

# ==================== backend/auth.py ====================
w('backend/auth.py', '''from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-secret-key')
ALGORITHM = os.getenv('ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 30))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        return email
    except JWTError:
        raise credentials_exception
''')

# ==================== backend/main.py ====================
w('backend/main.py', '''from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Optional
import sys
import os

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
    
    # Create user
    user_dict = {
        "email": user.email,
        "hashed_password": hashed_password,
        "full_name": user.full_name,
        "created_at": datetime.utcnow(),
        "is_first_login": True
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

@app.get("/check-first-login")
async def check_first_login(current_user: str = Depends(get_current_user)):
    user = await users_collection.find_one({"email": current_user})
    return {"is_first_login": user.get("is_first_login", True)}

@app.post("/patient-registration")
async def patient_registration(
    patient_data: PatientRegistration,
    current_user: str = Depends(get_current_user)
):
    # Encrypt sensitive data
    patient_dict = patient_data.dict()
    patient_dict["email"] = current_user
    patient_dict["created_at"] = datetime.utcnow()
    
    # Encrypt medical data
    sensitive_fields = ["medical_history", "chronic_conditions", "medications", "allergies"]
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
    
    return {"message": "Patient registration successful"}

@app.get("/patient-profile")
async def get_patient_profile(current_user: str = Depends(get_current_user)):
    patient = await patients_collection.find_one({"email": current_user})
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    # Decrypt sensitive data
    sensitive_fields = ["medical_history", "chronic_conditions", "medications", "allergies"]
    for field in sensitive_fields:
        if patient.get(field):
            try:
                patient[field] = encryption.decrypt(patient[field])
            except:
                pass
    
    # Remove MongoDB _id
    patient.pop("_id", None)
    
    return patient

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
''')

# ==================== backend/routes/prediction.py ====================
w('backend/routes/prediction.py', '''from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.auth import get_current_user
from backend.models import PredictionRequest
from backend.database import patients_collection
from ml_models.predict import RiskPredictor
from ml_models.nlp_extractor import parse_medical_report

router = APIRouter()

# Initialize predictor
model_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'trained_models')
predictor = None

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
        patient_data = dict(patient)
    
    if not patient_data:
        raise HTTPException(status_code=400, detail="No patient data provided")
    
    # Make prediction
    result = predictor.predict(patient_data)
    
    return result

@router.post("/extract-from-report")
async def extract_from_report(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):
    # Read file
    file_content = await file.read()
    
    # Extract features
    features, text = parse_medical_report(file_content, file_type='pdf')
    
    return {
        "extracted_features": features,
        "extracted_text": text[:500]  # First 500 chars
    }
''')

# ==================== backend/routes/chatbot.py ====================
w('backend/routes/chatbot.py', '''from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.auth import get_current_user
from backend.models import ChatMessage
from backend.database import patients_collection, chat_sessions_collection
from utils.rag_chatbot import RAGChatbot
from utils.encryption import DataEncryption

router = APIRouter()

# Initialize chatbot
chatbot = RAGChatbot()
encryption = DataEncryption()

@router.post("/chat")
async def chat(
    message: ChatMessage,
    current_user: str = Depends(get_current_user)
):
    # Get patient history
    patient = await patients_collection.find_one({"email": current_user})
    patient_history = ""
    
    if patient:
        # Decrypt and format patient history
        medical_history = patient.get("medical_history", "")
        if medical_history:
            try:
                medical_history = encryption.decrypt(medical_history)
            except:
                pass
        
        patient_history = f"""
Age: {patient.get('age')}
Sex: {patient.get('sex')}
Medical History: {medical_history}
Chronic Conditions: {patient.get('chronic_conditions', [])}
"""
    
    # Get chat history
    session_id = message.session_id or current_user
    chat_history = []
    
    if session_id:
        sessions = await chat_sessions_collection.find(
            {"session_id": session_id}
        ).sort("timestamp", -1).limit(5).to_list(length=5)
        
        chat_history = [
            f"User: {s['user_message']}\\nAssistant: {s['bot_response']}"
            for s in reversed(sessions)
        ]
    
    chat_history_text = "\\n".join(chat_history)
    
    # Generate response
    response = chatbot.chat(
        user_message=message.message,
        patient_history=patient_history,
        chat_history=chat_history_text
    )
    
    # Save to database
    chat_record = {
        "session_id": session_id,
        "user_email": current_user,
        "user_message": message.message,
        "bot_response": response,
        "timestamp": datetime.utcnow()
    }
    
    await chat_sessions_collection.insert_one(chat_record)
    
    return {"response": response, "session_id": session_id}

@router.get("/chat-history")
async def get_chat_history(
    session_id: str = None,
    current_user: str = Depends(get_current_user)
):
    session_id = session_id or current_user
    
    sessions = await chat_sessions_collection.find(
        {"session_id": session_id}
    ).sort("timestamp", -1).limit(20).to_list(length=20)
    
    # Format for response
    history = [
        {
            "user": s["user_message"],
            "assistant": s["bot_response"],
            "timestamp": s["timestamp"]
        }
        for s in reversed(sessions)
    ]
    
    return {"history": history}
''')

# ==================== backend/routes/scan.py ====================
w('backend/routes/scan.py', '''from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import google.generativeai as genai
from PIL import Image
import io
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.auth import get_current_user
from PyPDF2 import PdfReader

router = APIRouter()

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

@router.post("/interpret-scan")
async def interpret_scan(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):
    file_content = await file.read()
    
    try:
        # Check if PDF or image
        if file.filename.lower().endswith('.pdf'):
            # Extract images from PDF
            pdf_reader = PdfReader(io.BytesIO(file_content))
            
            # Extract text from PDF
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            
            # Use Gemini to interpret the scan report text
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""You are a medical AI assistant. Analyze this medical scan report and provide a clear, patient-friendly interpretation.

Medical Report:
{text}

Please provide:
1. Summary of findings
2. Key observations
3. What the patient should know
4. Recommendations

Use simple language that a non-medical person can understand."""
            
            response = model.generate_content(prompt)
            interpretation = response.text
            
        else:
            # For image files
            image = Image.open(io.BytesIO(file_content))
            
            # Use Gemini Vision (gemini-1.5-flash supports both text and images)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = """You are a medical AI assistant. Analyze this medical scan/X-ray image and provide:
1. Type of scan (X-ray, CT, MRI, etc.)
2. Body part scanned
3. Observable findings
4. Potential concerns
5. Patient-friendly explanation

Use simple, clear language."""
            
            response = model.generate_content([prompt, image])
            interpretation = response.text
        
        return {
            "interpretation": interpretation,
            "filename": file.filename,
            "file_type": "pdf" if file.filename.lower().endswith('.pdf') else "image"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interpreting scan: {str(e)}")
''')

print("\n✅ All API routes created!")
print("Next: Run setup_frontend.py to create Streamlit app")