import os
import google.generativeai as genai
from datetime import datetime

class RAGChatbot:
    def __init__(self, api_key=None):
        if api_key is None:
            api_key = os.getenv('GEMINI_API_KEY')
        
        genai.configure(api_key=api_key)
        
        # Try multiple models in order of preference (based on availability check)
        # These models are confirmed available for your API key
        model_options = [
            'gemini-2.0-flash-exp',               # ✅ CONFIRMED WORKING
            'gemini-2.5-pro-preview-03-25',       # Latest Pro preview
            'gemini-2.5-flash-preview-05-20',     # Latest Flash preview
            'gemini-2.0-pro-exp',                 # Pro experimental
            'gemini-2.0-pro-exp-02-05',           # Pro experimental stable
            'gemini-exp-1206',                    # Experimental build
            'gemini-2.0-flash-thinking-exp',      # Thinking mode
            'gemini-flash-latest',                # Latest Flash stable
            'gemini-pro-latest',                  # Latest Pro stable
            'gemini-2.0-flash-lite',              # Lite version
            'gemini-2.5-flash-lite',              # 2.5 Lite
            # Legacy fallbacks (unlikely to work)
            'gemini-1.5-pro',
            'gemini-1.5-flash',
            'gemini-pro'
        ]
        
        self.model = None
        import logging
        
        for model_name in model_options:
            try:
                self.model = genai.GenerativeModel(model_name)
                # Test if model works with a simple generation
                test_response = self.model.generate_content(
                    "Hello",
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=10
                    )
                )
                logging.info(f"✅ Successfully initialized Gemini model: {model_name}")
                break
            except Exception as e:
                logging.warning(f"⚠️ Model {model_name} not available: {str(e)}")
                continue
        
        if self.model is None:
            logging.error("❌ No Gemini models available. Please check your API key and quota.")
            raise Exception("No Gemini models available")
        
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
        
        # Add knowledge base (use full knowledge base for better context)
        if self.knowledge_base:
            context_parts.append(f"=== MEDICAL KNOWLEDGE BASE ===\n{self.knowledge_base}")
        
        # Add patient history
        if patient_history and patient_history.strip():
            context_parts.append(f"\n=== PATIENT MEDICAL HISTORY ===\n{patient_history.strip()}")
        
        return "\n\n".join(context_parts)
    
    def chat(self, user_message, patient_history=None, chat_history=None):
        """Generate chat response using RAG"""
        
        # Get relevant context
        context = self.get_relevant_context(user_message, patient_history)
        
        # Build enhanced prompt
        prompt = f"""You are MediSage AI, an intelligent medical assistant specialized in post-surgery care and patient health management.

IMPORTANT INSTRUCTIONS:
1. Use the Medical Knowledge Base to provide accurate medical information
2. Reference the Patient's Medical History when giving personalized advice
3. Consider the chat history for context continuity
4. Always prioritize patient safety and encourage consulting healthcare professionals for serious concerns

{context}

=== PREVIOUS CONVERSATION ===
{chat_history if chat_history else "This is the start of the conversation."}

=== CURRENT QUESTION ===
Patient asks: {user_message}

=== YOUR RESPONSE ===
Provide a clear, compassionate, and medically informed response that:
- Addresses the patient's specific question
- References relevant information from the knowledge base
- Considers the patient's medical history if provided
- Offers practical advice and recommendations
- Advises consulting a healthcare professional when appropriate"""
        
        try:
            # Generate response with safety settings
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.95,
                    max_output_tokens=1024,
                )
            )
            
            return response.text
            
        except Exception as e:
            # Log the actual error for debugging
            import logging
            logging.error(f"RAGChatbot error: {type(e).__name__}: {str(e)}")
            
            # Handle API errors gracefully with user-friendly messages
            error_msg = str(e).lower()
            
            # Safety filter triggered
            if "safety" in error_msg or "blocked" in error_msg:
                return "I apologize, but I cannot provide a response to this query due to safety constraints. Please consult with a healthcare professional directly for medical advice."
            
            # Model not found error
            elif "404" in error_msg or "not found" in error_msg or "models/" in error_msg:
                return "⚠️ Cannot connect to AI service. The AI model is currently unavailable. Please try again later or contact support."
            
            # API key or authentication error
            elif "401" in error_msg or "403" in error_msg or "api key" in error_msg or "authentication" in error_msg:
                return "⚠️ Cannot connect to AI service. Authentication error. Please contact the system administrator."
            
            # Rate limit or quota exceeded
            elif "429" in error_msg or "quota" in error_msg or "rate limit" in error_msg:
                return "⚠️ AI service is temporarily busy. Please try again in a few moments."
            
            # Network/connection errors
            elif "connection" in error_msg or "network" in error_msg or "timeout" in error_msg:
                return "⚠️ Cannot connect to server. Please check your internet connection and try again."
            
            # Generic server error
            elif "500" in error_msg or "503" in error_msg or "internal error" in error_msg:
                return "⚠️ AI service is temporarily unavailable. Please try again later."
            
            # Unknown error - return generic message
            else:
                return "⚠️ Cannot connect to server. An unexpected error occurred. Please try again later or contact support."
