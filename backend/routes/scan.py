from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import google.generativeai as genai
from PIL import Image
import io
import os
import sys
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.auth import get_current_user
from PyPDF2 import PdfReader

router = APIRouter()
logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Initialize model with fallback mechanism
def get_gemini_model():
    """Get available Gemini model with fallback"""
    model_options = [
        'gemini-2.0-flash-exp',
        'gemini-2.5-pro-preview-03-25',
        'gemini-2.5-flash-preview-05-20',
        'gemini-2.0-pro-exp',
        'gemini-flash-latest',
        'gemini-pro-latest',
        'gemini-2.0-flash-lite',
    ]
    
    for model_name in model_options:
        try:
            model = genai.GenerativeModel(model_name)
            # Test with a simple generation
            test = model.generate_content(
                "Hi",
                generation_config=genai.types.GenerationConfig(max_output_tokens=5)
            )
            logger.info(f"✅ Using Gemini model for scan: {model_name}")
            return genai.GenerativeModel(model_name)
        except Exception as e:
            logger.warning(f"Model {model_name} not available: {str(e)[:50]}")
            continue
    
    raise Exception("No Gemini models available for scan interpretation")

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
            model = get_gemini_model()
            
            prompt = f"""You are a kind doctor explaining medical test results to a patient who doesn't understand medical terms.

Medical Report:
{text}

🗣️ IMPORTANT: Explain this report like you're talking to someone who never went to medical school. Use everyday words, not medical terms.

Please explain:

1. **What was tested?** (Say it simply - like "heart scan" instead of "cardiac imaging")

2. **What did we find?** (Use simple words like "normal", "swollen", "blocked" instead of medical terms)

3. **Is this good or bad news?** (Be honest but kind)

4. **What should the patient do next?** (Simple steps like "see your doctor", "take medicine", "come back in 2 weeks")

5. **Should they worry?** (Reassure them or tell them to take it seriously)

Remember: Talk like a caring family doctor, not a medical textbook! Use "you" and "your" to make it personal."""
            
            response = model.generate_content(prompt)
            interpretation = response.text
            
        else:
            # For image files
            image = Image.open(io.BytesIO(file_content))
            
            # Use Gemini Vision for image analysis
            model = get_gemini_model()
            
            prompt = """You are a kind doctor showing a patient their scan results. Explain what you see in very simple words.

🗣️ IMPORTANT: No medical jargon! Talk like you're explaining to your grandmother.

Please tell the patient:

1. **What kind of picture is this?** (X-ray? CT scan? MRI? Say it simply)

2. **What part of the body are we looking at?** (Chest? Head? Leg?)

3. **What do you see in the picture?** (Use everyday words like "dark spot", "white area", "looks normal", "looks swollen")

4. **What does this mean for the patient?**
   - If it looks normal: Say "Good news! Everything looks fine"
   - If there's a problem: Explain it kindly (like "I see some fluid in your lungs which means...")

5. **What should they do next?** (Simple actions like "talk to your doctor", "need more tests", "start treatment")

6. **Should they be worried?** (Be honest but comforting)

Talk directly to the patient using "you" and "your". Be warm and caring, like talking to a family member."""
            
            response = model.generate_content([prompt, image])
            interpretation = response.text
        
        return {
            "interpretation": interpretation,
            "filename": file.filename,
            "file_type": "pdf" if file.filename.lower().endswith('.pdf') else "image"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interpreting scan: {str(e)}")
