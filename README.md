# MediSage AI - Intelligent Medical Assistant

A comprehensive medical AI platform for post-surgery risk prediction, RAG-based medical chatbot, and medical scan interpretation.

## Features

1. **User Authentication**: Secure registration and login with encrypted patient data
2. **Post-Surgery Risk Prediction**: ML-based prediction using Voting Ensemble (XGBoost, Random Forest, Gradient Boosting, SVM)
3. **RAG Medical Chatbot**: Context-aware chatbot using patient history and medical knowledge base
4. **Medical Scan Interpretation**: AI-powered interpretation of X-rays and medical scans

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

**Start FastAPI Backend:**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Start Streamlit Frontend:**
```bash
streamlit run frontend/app.py
```

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

1. **Register/Login**: Create account or login with email and password
2. **First-Time Setup**: Complete patient registration form with medical history
3. **Risk Prediction**: Upload medical reports or enter data manually
4. **Medical Chatbot**: Ask medical questions with context awareness
5. **Scan Interpretation**: Upload X-rays or scans for AI analysis

## Security

- Patient data is encrypted using Fernet encryption
- JWT tokens for secure authentication
- Passwords hashed with bcrypt

## Technologies

- **Backend**: FastAPI, MongoDB
- **Frontend**: Streamlit
- **ML**: XGBoost, Random Forest, Gradient Boosting, SVM
- **AI**: Google Gemini API
- **NLP**: spaCy
- **Vector DB**: ChromaDB for RAG

## License

MIT License