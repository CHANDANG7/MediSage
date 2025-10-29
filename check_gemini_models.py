#!/usr/bin/env python3
"""Check which Gemini models are available for your API key"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("❌ GEMINI_API_KEY not found in .env file")
    exit(1)

print(f"🔑 Using API key: {api_key[:10]}...{api_key[-4:]}")
print("🔍 Checking available Gemini models...\n")

genai.configure(api_key=api_key)

try:
    # List all available models
    models = genai.list_models()
    
    print("✅ Available Models:")
    print("=" * 60)
    
    for model in models:
        # Check if model supports generateContent
        if 'generateContent' in model.supported_generation_methods:
            print(f"✅ {model.name}")
            print(f"   Display Name: {model.display_name}")
            print("-" * 60)
    
    print("\n💡 Testing models...\n")
    
    # Test common models
    test_models = [
        'gemini-2.0-flash-exp',
        'gemini-1.5-pro-latest',
        'gemini-1.5-flash-latest',
        'gemini-1.5-pro',
        'gemini-1.5-flash',
        'gemini-pro'
    ]
    
    working_models = []
    
    for model_name in test_models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                "Hello",
                generation_config=genai.types.GenerationConfig(max_output_tokens=5)
            )
            print(f"✅ {model_name} - WORKING")
            working_models.append(model_name)
        except Exception as e:
            print(f"❌ {model_name} - NOT AVAILABLE")
    
    if working_models:
        print(f"\n🎉 Found {len(working_models)} working model(s):")
        for model in working_models:
            print(f"   ✅ {model}")
    else:
        print("\n⚠️ No working models found!")
        print("   Solutions:")
        print("   1. Regenerate API key at: https://makersuite.google.com/app/apikey")
        print("   2. Check quota at: https://console.cloud.google.com/")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")
    print("\n🔧 Try: pip install --upgrade google-generativeai")