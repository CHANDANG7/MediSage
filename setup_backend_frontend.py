import os

def w(p, c):
    os.makedirs(os.path.dirname(p) if os.path.dirname(p) else '.', exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f: f.write(c)
    print(f"✅ {p}")

print("🚀 Creating Backend & Frontend Files...\n")

# ==================== utils/encryption.py ====================
w('utils/encryption.py', '''from cryptography.fernet import Fernet
import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

class DataEncryption:
    def __init__(self, password=None):
        if password is None:
            password = os.getenv('SECRET_KEY', 'default-secret-key-change-this')
        
        # Derive key from password
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'medisage-salt-2024',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.cipher = Fernet(key)
    
    def encrypt(self, data):
        """Encrypt string data"""
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data).decode()
    
    def decrypt(self, encrypted_data):
        """Decrypt data"""
        if isinstance(encrypted_data, str):
            encrypted_data = encrypted_data.encode()
        return self.cipher.decrypt(encrypted_data).decode()
    
    def encrypt_dict(self, data_dict):
        """Encrypt dictionary values"""
        encrypted = {}
        for key, value in data_dict.items():
            if value is not None:
                encrypted[key] = self.encrypt(str(value))
        return encrypted
    
    def decrypt_dict(self, encrypted_dict):
        """Decrypt dictionary values"""
        decrypted = {}
        for key, value in encrypted_dict.items():
            if value is not None:
                try:
                    decrypted[key] = self.decrypt(value)
                except:
                    decrypted[key] = value
        return decrypted
''')

# ==================== utils/rag_chatbot.py ====================
w('utils/rag_chatbot.py', '''import os
import google.generativeai as genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from datetime import datetime

class RAGChatbot:
    def __init__(self, api_key=None):
        if api_key is None:
            api_key = os.getenv('GEMINI_API_KEY')
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Load knowledge base
        self.knowledge_base = self.load_knowledge_base()
    
    def load_knowledge_base(self):
        """Load medical knowledge base"""
        kb_path = os.path.join(os.path.dirname(__file__), '..', 'knowledge_base', 'medical_kb.txt')
        
        if os.path.exists(kb_path):
            with open(kb_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def get_relevant_context(self, query, patient_history=None):
        """Get relevant context from knowledge base and patient history"""
        context_parts = []
        
        # Add knowledge base
        if self.knowledge_base:
            context_parts.append(f"Medical Knowledge Base:\\n{self.knowledge_base[:2000]}")
        
        # Add patient history
        if patient_history:
            context_parts.append(f"\\nPatient Medical History:\\n{patient_history}")
        
        return "\\n\\n".join(context_parts)
    
    def chat(self, user_message, patient_history=None, chat_history=None):
        """Generate chat response using RAG"""
        
        # Get relevant context
        context = self.get_relevant_context(user_message, patient_history)
        
        # Build prompt
        prompt = f"""You are MediSage AI, a helpful medical assistant. Answer the user's question based on the provided context and chat history.

Context:
{context}

Chat History:
{chat_history if chat_history else "No previous messages"}

User Question: {user_message}

Provide a clear, helpful, and medically accurate response. If you're unsure, advise consulting a healthcare professional."""
        
        # Generate response
        response = self.model.generate_content(prompt)
        
        return response.text
''')

# ==================== knowledge_base/medical_kb.txt ====================
w('knowledge_base/medical_kb.txt', '''MEDICAL KNOWLEDGE BASE - SURGERY & RECOVERY

HEART SURGERY TYPES:
1. CABG (Coronary Artery Bypass Grafting): Surgery to improve blood flow to the heart. Typical recovery: 6-12 weeks.
2. Valve Replacement: Replacing damaged heart valves. Recovery: 8-12 weeks.
3. Pacemaker Implantation: Device to regulate heartbeat. Recovery: 2-4 weeks.
4. Bypass Surgery: Creating new routes for blood flow. Recovery: 6-10 weeks.

COMMON SYMPTOMS:
- Chest Pain: May indicate heart problems, angina, or post-surgery healing.
- Shortness of Breath: Common after heart surgery, improves with time.
- Fatigue: Normal during recovery, gradually improves.
- Swelling: Common in legs after surgery, usually temporary.

POST-SURGERY CARE:
- Take prescribed medications regularly
- Follow dietary restrictions (low sodium, heart-healthy diet)
- Gradual increase in physical activity
- Attend all follow-up appointments
- Monitor for signs of infection
- Manage stress and get adequate rest

RISK FACTORS:
- Age: Risk increases with age
- Hypertension: High blood pressure increases surgical risk
- Diabetes: Affects healing and recovery
- Smoking: Significantly increases complications
- Obesity: Higher BMI increases risk
- Previous heart conditions: May complicate surgery

RECOVERY TIMELINE:
- Week 1-2: Hospital stay, initial recovery
- Week 3-6: Gradual return to light activities
- Week 7-12: Continued improvement, cardiac rehabilitation
- Month 4-6: Most patients return to normal activities

EMERGENCY SIGNS (Call doctor immediately):
- Severe chest pain
- Difficulty breathing
- Irregular heartbeat
- Fever above 100.4°F
- Excessive swelling or redness at incision site
- Unusual bleeding

LIFESTYLE MODIFICATIONS:
- Heart-healthy diet (Mediterranean diet recommended)
- Regular exercise (as approved by doctor)
- Stress management
- Quit smoking
- Limit alcohol consumption
- Maintain healthy weight

MEDICATIONS COMMONLY PRESCRIBED:
- Beta-blockers: Control heart rate and blood pressure
- ACE inhibitors: Help heart pump more efficiently
- Statins: Lower cholesterol
- Blood thinners: Prevent blood clots
- Diuretics: Reduce fluid buildup
''')

# ==================== backend/database.py ====================
w('backend/database.py', '''from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'medisage_db')

# Async client for FastAPI
async_client = AsyncIOMotorClient(MONGODB_URI)
async_db = async_client[DATABASE_NAME]

# Collections
users_collection = async_db['users']
patients_collection = async_db['patients']
chat_sessions_collection = async_db['chat_sessions']

def get_database():
    """Get database instance"""
    return async_db
''')

# ==================== backend/models.py ====================
w('backend/models.py', '''from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class PatientRegistration(BaseModel):
    age: int
    sex: str
    blood_group: str
    height_cm: float
    weight_kg: float
    contact_number: str
    medical_history: Optional[str] = None
    chronic_conditions: Optional[List[str]] = []
    medications: Optional[List[str]] = []
    allergies: Optional[List[str]] = []
    previous_surgeries: Optional[List[str]] = []
    family_history: Optional[str] = None
    smoking: Optional[str] = "No"
    alcohol_consumption: Optional[str] = "None"
    exercise_frequency: Optional[str] = "Regular"

class PredictionRequest(BaseModel):
    patient_data: Optional[Dict[str, Any]] = None
    use_profile: bool = False

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ScanInterpretation(BaseModel):
    scan_type: str
    findings: Optional[str] = None
''')

# ==================== backend/__init__.py ====================
w('backend/__init__.py', '')
w('backend/routes/__init__.py', '')
w('ml_models/__init__.py', '')
w('utils/__init__.py', '')

print("\n✅ Backend utilities and models created!")
print("Next: Run setup_api.py to create API routes")