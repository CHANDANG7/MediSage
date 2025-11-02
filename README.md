# MediSage AI - Intelligent Medical Assistant

A comprehensive medical AI platform for post-surgery risk prediction, RAG-based medical chatbot, and medical scan interpretation.

## Features

1. **User Authentication**: Secure registration and login with encrypted patient data
2. **Post-Surgery Risk Prediction**: ML-based prediction using Voting Ensemble (XGBoost, Random Forest, Gradient Boosting, SVM)
3. **RAG Medical Chatbot**: Context-aware chatbot using patient history and medical knowledge base
4. **Medical Scan Interpretation**: AI-powered interpretation of X-rays and medical scans
5. **NEW: Gemini-Powered Report Analysis**: AI analyzes medical reports and extracts critical risk factors
6. **NEW: AI Consequence Prediction**: Personalized surgery consequence analysis using Gemini AI
7. **NEW: Auto-Detection of Surgery Complexity**: 40+ surgery types with automatic category/complexity detection
8. **NEW: Pre-Surgery Risk Factor Tracking**: Document serious conditions mentioned before surgery

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory:
```
MONGODB_URI=mongodb://localhost:27017/
DATABASE_NAME=medisage_db
SECRET_KEY=your-secret-key-here-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
GEMINI_API_KEY=your-gemini-api-key-here
```

### 3. Start MongoDB
Ensure MongoDB is running on your system.

### 4. Generate Dataset and Train Models
```bash
python ml_models/generate_dataset.py
python ml_models/train_models.py
```

### 5. Run the Application

#### Step 5a: Start FastAPI Backend

Open a terminal in the MediSage directory:

**Windows:**
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Mac/Linux:**
```bash
python3 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend running at: `http://localhost:8000`

#### Step 5b: Start Streamlit Frontend

Open **ANOTHER terminal** in the MediSage directory:

**Windows/Mac/Linux:**
```bash
cd frontend
streamlit run app.py
```

Frontend running at: `http://localhost:8501`

The browser should open automatically. If not, navigate to `http://localhost:8501`

## Project Structure
```
wind/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── auth.py                 # Authentication logic
│   ├── database.py             # Database connection
│   ├── models.py               # Pydantic models
│   └── routes/
│       ├── prediction.py       # Risk prediction endpoints
│       ├── chatbot.py          # Chatbot endpoints
│       └── scan.py             # Scan interpretation endpoints
├── frontend/
│   └── app.py                  # Streamlit application
├── ml_models/
│   ├── generate_dataset.py     # Dataset generation
│   ├── train_models.py         # Model training
│   ├── predict.py              # Prediction logic
│   └── nlp_extractor.py        # NLP feature extraction
├── utils/
│   ├── encryption.py           # Data encryption
│   └── rag_chatbot.py          # RAG implementation
├── knowledge_base/
│   └── medical_kb.txt          # Medical knowledge base
├── .env                        # Environment variables
└── requirements.txt            # Dependencies
```

## Usage

### Basic Workflow
1. **Register/Login**: Create account or login with email and password
2. **First-Time Setup**: Complete patient registration form with medical history
3. **Select Surgery Type**: Choose from 40+ surgery types (category/complexity auto-detected)
4. **Add Pre-Surgery Notes**: Document any serious risk factors mentioned by doctor/patient
5. **Risk Prediction**: 
   - **Option A**: Upload medical reports (PDF) for AI analysis
   - **Option B**: Enter data manually
6. **View Results**: See risk level, recovery days, and **AI-powered consequence analysis**
7. **Medical Chatbot**: Ask medical questions with context awareness
8. **Scan Interpretation**: Upload X-rays or scans for AI analysis

### New Features in Action

#### 1. Auto-Detection of Surgery Complexity
- Go to **Profile** → **Edit Profile** → **Surgery Info**
- Select any surgery type from dropdown (40+ options)
- System **automatically detects**:
  - Surgery Category (Major/Intermediate/Minor)
  - Surgery Complexity (High/Medium/Low)
- No manual input needed!

#### 2. Gemini-Powered Report Analysis
- Go to **Risk Prediction** → **Upload Medical Report** tab
- Upload a PDF medical report
- AI extracts:
  - Patient demographics, vital signs, cardiac conditions
  - Medical conditions, risk factors, lab values
  - Critical findings and medications
- Generates comprehensive summary
- Makes risk prediction
- Shows **personalized consequence analysis**

#### 3. AI Consequence Prediction
After any risk prediction, view:
- What the risk level means in simple terms
- Short-term, medium-term, and long-term risks
- Specific concerns based on your risk factors
- Recovery expectations and potential complications
- Risk mitigation strategies
- Decision guidance on surgery

#### 4. Pre-Surgery Risk Factors
- Document serious conditions in profile
- Add other risk factors (e.g., "having diabetes", "history of stroke")
- Used by AI to provide better consequence analysis

## 40+ Surgery Types Available

### Major Surgeries (High Complexity):
- CABG, Valve Replacement, Valve Repair
- Aortic Valve Replacement, Mitral Valve Replacement
- Bypass Surgery, Heart Transplant
- Coronary Artery Bypass Graft, Open Heart Surgery
- Aortic Aneurysm Repair, LVAD Implantation

### Intermediate Surgeries (Medium Complexity):
- Angioplasty, PCI, Stent Placement, Coronary Stenting
- Ablation, Cardiac Ablation
- ASD Closure, VSD Closure, PDA Closure
- TAVI, TAVR, MitraClip

### Minor Surgeries (Low Complexity):
- Pacemaker Implantation, Pacemaker
- ICD Implantation, Defibrillator Implantation
- CRT Device Implantation
- Cardiac Catheterization, Diagnostic Catheterization
- Cardiac Monitoring Device, Loop Recorder Implantation

## Security

- Patient data is encrypted using Fernet encryption
- JWT tokens for secure authentication
- Passwords hashed with bcrypt

## Technologies

- **Backend**: FastAPI, MongoDB
- **Frontend**: Streamlit
- **ML**: XGBoost, Random Forest, Gradient Boosting, SVM
- **AI**: Google Gemini API (2.0-flash-exp)
- **NLP**: spaCy, Gemini for report analysis
- **Vector DB**: ChromaDB for RAG
- **Security**: Fernet encryption, JWT, bcrypt

## Troubleshooting

### "ML models not available"
**Solution:** Train models first:
```bash
cd ml_models
python train_models.py
```

### "Gemini API error"
**Solution:** Check `.env` file for valid `GEMINI_API_KEY`

### "Cannot connect to backend"
**Solution:** Ensure backend is running on port 8000

### "Port already in use"
**Solution:** Use different ports:
```bash
# Backend
uvicorn backend.main:app --reload --port 8001

# Frontend
streamlit run app.py --server.port 8502
```

## What's New in v2.0

**40+ Surgery Types** with auto-detection  
**Gemini AI Integration** for report analysis  
**Consequence Prediction** using Gemini  
**Pre-Surgery Risk Tracking**  
**Automatic Complexity Detection**  
**Enhanced Security** with encrypted risk factors  
**Better UX** with informative messages

## License

MIT License