#!/usr/bin/env python3
"""
Test script for Gemini API integration
Run this to verify your API key is working correctly
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gemini_api():
    """Test Gemini API connection and generation"""
    
    print("🔍 Testing Gemini API Integration...")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment variables!")
        print("\n📝 To fix this:")
        print("1. Create a .env file in the project root")
        print("2. Add: GEMINI_API_KEY=your_api_key_here")
        print("3. Get your API key from: https://aistudio.google.com/app/apikey")
        return False
    
    if api_key == 'YOUR_GEMINI_API_KEY_HERE':
        print("❌ GEMINI_API_KEY is still set to placeholder value!")
        print("Please set your actual API key in .env file")
        return False
    
    print(f"✅ API Key found (length: {len(api_key)} characters)")
    
    # Check if google-generativeai is installed
    try:
        import google.generativeai as genai
        print("✅ google-generativeai package is installed")
    except ImportError:
        print("❌ google-generativeai package not installed!")
        print("\n📝 To install:")
        print("pip3 install google-generativeai")
        return False
    
    # Test API connection
    try:
        print("\n🔌 Testing API connection...")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        print("✅ API connection successful!")
        
        # Test generation
        print("\n📝 Testing sample generation...")
        test_prompt = "Generate a short test message with [TEST ENVIRONMENT] tags."
        response = model.generate_content(test_prompt)
        
        generated_text = response.text.strip()
        print(f"✅ Generation successful!")
        print(f"\n📄 Generated text:")
        print("-" * 50)
        print(generated_text)
        print("-" * 50)
        
        # Check if [TEST ENVIRONMENT] tags are present
        if "[TEST ENVIRONMENT]" in generated_text:
            print("\n✅ [TEST ENVIRONMENT] tags found in generated text")
        else:
            print("\n⚠️ [TEST ENVIRONMENT] tags not found (will be added automatically)")
        
        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED!")
        print("✅ Gemini API is ready to use!")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing Gemini API: {e}")
        print("\n📝 Possible issues:")
        print("1. API key is invalid - check it in Google AI Studio")
        print("2. API quota exceeded - wait a few minutes")
        print("3. Network connection issue - check your internet")
        return False

if __name__ == "__main__":
    success = test_gemini_api()
    sys.exit(0 if success else 1)

