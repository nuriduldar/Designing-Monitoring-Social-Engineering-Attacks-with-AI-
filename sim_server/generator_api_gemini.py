"""
Gemini API integration for phishing sample generation
Google Gemini API integration for phishing sample generation
"""

import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Try to import google-generativeai
try:
    import google.generativeai as genai
    GEMINI_SDK_AVAILABLE = True
except ImportError:
    GEMINI_SDK_AVAILABLE = False
    print("⚠️ google-generativeai package not installed. Install with: pip3 install google-generativeai")

def generate_with_gemini(prompt, tone="urgent", role="employee"):
    """
    Generate phishing sample using Google Gemini API
    
    Args:
        prompt: Generation prompt
        tone: Message tone (urgent, polite, authoritative, etc.)
        role: Target role (employee, customer, etc.)
    
    Returns:
        Generated text with [TEST ENVIRONMENT] tags
    """
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key or api_key == 'YOUR_GEMINI_API_KEY_HERE':
        raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in .env file.")
    
    if not GEMINI_SDK_AVAILABLE:
        raise ImportError("google-generativeai package not installed. Install with: pip3 install google-generativeai")
    
    try:
        # Configure Gemini API
        genai.configure(api_key=api_key)
        
        # Use latest Gemini models (try gemini-2.5-flash first, then fallback)
        model = None
        model_names = [
            'gemini-2.5-flash',      # Latest fast model
            'gemini-2.5-pro',        # Latest pro model
            'gemini-2.0-flash',      # Alternative
            'gemini-flash-latest',    # Latest flash
            'gemini-pro-latest'       # Latest pro
        ]
        
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                break
            except Exception:
                continue
        
        if model is None:
            raise ValueError("No working Gemini model found. Please check your API key and model availability.")
        
        # Enhanced prompt for better results
        enhanced_prompt = f"""Generate a realistic phishing email message with the following characteristics:
- Tone: {tone}
- Target Role: {role}
- Must include: [TEST ENVIRONMENT] at the beginning and end
- Must be realistic and convincing
- Should include common phishing tactics (urgency, authority, etc.)
- Length: 100-300 words
- Format: Email format with subject and body

Generate the phishing email:"""
        
        # Generate content
        response = model.generate_content(enhanced_prompt)
        
        # Extract text from response
        generated_text = response.text.strip()
        
        # Ensure [TEST ENVIRONMENT] tags are present
        if "[TEST ENVIRONMENT]" not in generated_text:
            generated_text = f"[TEST ENVIRONMENT] {generated_text} [TEST ENVIRONMENT]"
        
        return generated_text
        
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        raise

def generate_sample_via_gemini_api(tone="urgent", role="employee", scenario_id=None):
    """
    Generate a single phishing sample via Gemini API
    
    Returns:
        dict with id, text, tone, role, created_at
    """
    try:
        # Use the generate_with_gemini function which handles the prompt internally
        text = generate_with_gemini("", tone, role)
        
        if scenario_id is None:
            scenario_id = f"scenario_gemini_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return {
            "id": scenario_id,
            "text": text,
            "tone": tone,
            "role": role,
            "created_at": datetime.now().isoformat() + "Z",
            "source": "gemini"
        }
    except Exception as e:
        print(f"Error generating with Gemini: {e}")
        raise

def generate_multiple_samples_gemini(count=5, tone="urgent", role="employee"):
    """
    Generate multiple samples using Gemini API
    
    Returns:
        list of sample dicts
    """
    samples = []
    for i in range(count):
        try:
            sample = generate_sample_via_gemini_api(tone=tone, role=role)
            samples.append(sample)
        except Exception as e:
            print(f"Error generating sample {i+1}: {e}")
            continue
    
    return samples

# Note: Full implementation will be completed when Gemini API key is available
# This file serves as a placeholder for the final integration phase


