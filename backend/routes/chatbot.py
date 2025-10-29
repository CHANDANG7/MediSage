from fastapi import APIRouter, Depends, HTTPException
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

# Initialize chatbot with error handling
import logging
logger = logging.getLogger(__name__)

try:
    chatbot = RAGChatbot()
    logger.info("✅ Chatbot initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize chatbot: {str(e)}")
    chatbot = None

encryption = DataEncryption()

@router.post("/chat")
async def chat(
    message: ChatMessage,
    current_user: str = Depends(get_current_user)
):
    # Check if chatbot is available
    if chatbot is None:
        return {
            "response": "⚠️ AI service is currently unavailable. Please contact the administrator.",
            "session_id": message.session_id or current_user
        }
    # Get patient medical history for context
    patient = await patients_collection.find_one({"email": current_user})
    patient_history = ""
    
    if patient:
        # Build patient history context
        history_parts = []
        
        # Decrypt and add all relevant medical fields
        medical_fields = {
            "medical_history": "Medical History",
            "chronic_conditions": "Chronic Conditions",
            "medications": "Current Medications",
            "allergies": "Allergies",
            "previous_surgeries": "Previous Surgeries"
        }
        
        for field, label in medical_fields.items():
            if patient.get(field):
                try:
                    decrypted_value = encryption.decrypt(patient[field])
                    if decrypted_value and decrypted_value.strip():
                        history_parts.append(f"{label}: {decrypted_value}")
                except Exception as e:
                    # Log but don't fail
                    import logging
                    logging.warning(f"Failed to decrypt {field}: {str(e)}")
                    pass
        
        # Add non-encrypted relevant medical data
        if patient.get("age"):
            history_parts.append(f"Age: {patient['age']}")
        if patient.get("sex"):
            history_parts.append(f"Sex: {patient['sex']}")
        if patient.get("type_of_heart_disease") and patient.get("type_of_heart_disease") != "None":
            history_parts.append(f"Heart Disease: {patient['type_of_heart_disease']}")
        
        patient_history = "\n".join(history_parts)
    
    # Get chat history
    session_id = message.session_id or current_user
    chat_history = []
    
    if session_id:
        sessions = await chat_sessions_collection.find(
            {"session_id": session_id}
        ).sort("timestamp", -1).limit(5).to_list(length=5)
        
        chat_history = [
            f"User: {s['user_message']}\nAssistant: {s['bot_response']}"
            for s in reversed(sessions)
        ]
    
    chat_history_text = "\n".join(chat_history)
    
    # Generate response with error handling
    try:
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
        
    except Exception as e:
        # Log the error
        import logging
        logging.error(f"Chat endpoint error: {str(e)}")
        
        # Return user-friendly error message
        error_response = "⚠️ Cannot connect to server. The AI service is temporarily unavailable. Please try again later."
        
        # Still save the error to chat history for tracking
        chat_record = {
            "session_id": session_id,
            "user_email": current_user,
            "user_message": message.message,
            "bot_response": error_response,
            "timestamp": datetime.utcnow(),
            "error": True
        }
        
        try:
            await chat_sessions_collection.insert_one(chat_record)
        except:
            pass  # Don't fail if we can't save to DB
        
        return {"response": error_response, "session_id": session_id}

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
