"""
Generator API - Web interface for generating phishing samples
Supports: Google Gemini API, Local Llama-2, and deterministic templates
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add generator directory to path
GENERATOR_DIR = Path(__file__).parent.parent / 'generator'
sys.path.insert(0, str(GENERATOR_DIR))

from generate_phishing import generate_sample, save_sample, check_safety, log_blocked_output

# Try to import Llama-2 support
try:
    from generate_with_llama import generate_sample_llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False
    print("Llama-2 support not available (transformers/torch not installed)")

# Try to import Gemini API support
GEMINI_AVAILABLE = False
try:
    # First check if SDK is installed
    try:
        import google.generativeai as genai
        SDK_AVAILABLE = True
    except ImportError:
        SDK_AVAILABLE = False
        print("⚠️ google-generativeai SDK not installed. Install with: pip3 install google-generativeai")
    
    # Then try to import our wrapper
    if SDK_AVAILABLE:
        try:
            from sim_server.generator_api_gemini import generate_sample_via_gemini_api
            GEMINI_AVAILABLE = True
            print("✅ Gemini API support loaded successfully")
        except Exception as e:
            GEMINI_AVAILABLE = False
            print(f"⚠️ Failed to import generator_api_gemini: {e}")
    else:
        GEMINI_AVAILABLE = False
except Exception as e:
    GEMINI_AVAILABLE = False
    print(f"⚠️ Gemini API support not available: {e}")
    print("   Install with: pip3 install google-generativeai")
except Exception as e:
    GEMINI_AVAILABLE = False
    print(f"⚠️ Gemini API support error: {e}")


def generate_sample_via_api(tone='polite', target_role='employee', use_llama=False, use_gemini=True, llama_model_path=None):
    """
    Generate a phishing sample via API
    
    Args:
        tone: Tone of the message
        target_role: Target role
        use_llama: Whether to use local Llama-2 model
        use_gemini: Whether to use Google Gemini API (default: True)
        llama_model_path: Path to local Llama-2 model
    
    Returns:
        dict: Result with sample or error
    """
    global GEMINI_AVAILABLE  # Declare at function start
    
    try:
        # Priority: Gemini > Llama-2 > Local templates
        gemini_available = False
        llama_available = False
        
        # Always try Gemini first if enabled
        if use_gemini:
            # Force reload .env to ensure API key is loaded
            from dotenv import load_dotenv
            from pathlib import Path
            env_path = Path(__file__).parent.parent / '.env'
            load_dotenv(dotenv_path=env_path, override=True)
            
            # Check if Gemini SDK is available - try to re-import if needed
            gemini_key = os.getenv('GEMINI_API_KEY')
            print(f"DEBUG: use_gemini={use_gemini}, GEMINI_AVAILABLE={GEMINI_AVAILABLE}, gemini_key exists={bool(gemini_key)}")
            
            # If GEMINI_AVAILABLE is False, try to re-check
            if not GEMINI_AVAILABLE:
                print(f"DEBUG: GEMINI_AVAILABLE=False, attempting to re-check...")
                try:
                    import google.generativeai as genai
                    # Try to import the function again
                    import sys
                    if 'sim_server.generator_api_gemini' in sys.modules:
                        del sys.modules['sim_server.generator_api_gemini']
                    from sim_server.generator_api_gemini import generate_sample_via_gemini_api
                    # Update global flag (already declared at function start)
                    GEMINI_AVAILABLE = True
                    print(f"DEBUG: ✅ GEMINI_AVAILABLE set to True after re-check")
                except Exception as e:
                    print(f"DEBUG: ❌ Re-check failed: {e}")
                    GEMINI_AVAILABLE = False
            
            if gemini_key:
                print(f"DEBUG: gemini_key length={len(gemini_key)}, is_placeholder={gemini_key == 'YOUR_GEMINI_API_KEY_HERE'}")
            
            # Check if we can use Gemini
            if GEMINI_AVAILABLE and gemini_key and gemini_key != 'YOUR_GEMINI_API_KEY_HERE' and len(gemini_key) > 10:
                gemini_available = True
                print(f"DEBUG: ✅ gemini_available={gemini_available}")
            else:
                print(f"DEBUG: ❌ gemini_available=False")
                if not GEMINI_AVAILABLE:
                    print(f"DEBUG:   Reason: GEMINI_AVAILABLE=False")
                elif not gemini_key:
                    print(f"DEBUG:   Reason: gemini_key is None or empty")
                elif gemini_key == 'YOUR_GEMINI_API_KEY_HERE':
                    print(f"DEBUG:   Reason: gemini_key is placeholder")
                elif len(gemini_key) <= 10:
                    print(f"DEBUG:   Reason: gemini_key too short ({len(gemini_key)} chars)")
        
        if use_llama and LLAMA_AVAILABLE:
            llama_available = True
        
        # Generate sample based on available options
        # If use_gemini is True, we MUST use Gemini (don't fallback to local_template)
        if use_gemini:
            if not gemini_available:
                return {
                    'status': 'error',
                    'message': 'Gemini API is requested but not available. Please check GEMINI_API_KEY in .env file.',
                    'tone': tone,
                    'role': target_role
                }
            
            # Use Google Gemini API (required if use_gemini=True)
            try:
                print(f"DEBUG: Attempting Gemini generation with tone={tone}, role={target_role}")
                gemini_result = generate_sample_via_gemini_api(tone, target_role)
                text = gemini_result.get('text', '')
                if text:
                    source = 'gemini'
                    print(f"DEBUG: Gemini generation SUCCESS, source set to 'gemini'")
                else:
                    return {
                        'status': 'error',
                        'message': 'Gemini API returned empty text. Please try again.',
                        'tone': tone,
                        'role': target_role
                    }
            except Exception as e:
                print(f"DEBUG: Gemini generation failed: {e}")
                import traceback
                traceback.print_exc()
                return {
                    'status': 'error',
                    'message': f'Gemini API generation failed: {str(e)}. Please check your API key and try again.',
                    'tone': tone,
                    'role': target_role
                }
        elif not gemini_available:
            # Only use fallback if use_gemini=False
            if llama_available:
                # Use local Llama-2
                text = generate_sample_llama(tone, target_role, llama_model_path)
                source = 'llama2_local'
            else:
                # Use deterministic templates
                text = generate_sample(tone, target_role, local_mode=True)
                source = 'local_template'
        
        if text is None:
            return {
                'status': 'blocked',
                'message': 'Generated text was blocked by safety checks',
                'tone': tone,
                'role': target_role
            }
        
        # Save sample with source information
        try:
            scenario_id = save_sample(text, tone, target_role, source=source)
            print(f"DEBUG: Sample saved with ID: {scenario_id}, source: {source}")
        except Exception as e:
            print(f"ERROR: Failed to save sample: {e}")
            import traceback
            traceback.print_exc()
            # Still return success but log the error
            scenario_id = f"scenario_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        return {
            'status': 'success',
            'scenario_id': scenario_id,
            'text': text,
            'tone': tone,
            'role': target_role,
            'source': source,
            'preview': text[:200] + '...' if len(text) > 200 else text,
            'message': f'Sample generated successfully with {source}'
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'tone': tone,
            'role': target_role
        }


def generate_multiple_samples(count=5, use_llama=False, use_gemini=True, llama_model_path=None):
    """Generate multiple samples"""
    tones = ['urgent', 'polite', 'curious', 'authoritative', 'friendly']
    results = []
    
    for i in range(count):
        tone = tones[i % len(tones)]
        result = generate_sample_via_api(tone, 'employee', use_llama, use_gemini, llama_model_path)
        results.append(result)
    
    success_count = len([r for r in results if r['status'] == 'success'])
    blocked_count = len([r for r in results if r['status'] == 'blocked'])
    
    return {
        'status': 'completed',
        'total': count,
        'success': success_count,
        'blocked': blocked_count,
        'results': results
    }


def get_available_models():
    """Get list of available AI models"""
    # Check Gemini availability with explicit env loading
    from dotenv import load_dotenv
    from pathlib import Path
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(dotenv_path=env_path, override=True)
    
    gemini_key = os.getenv('GEMINI_API_KEY')
    
    # Debug logging
    print(f"DEBUG get_available_models: GEMINI_AVAILABLE={GEMINI_AVAILABLE}")
    print(f"DEBUG get_available_models: gemini_key exists={bool(gemini_key)}")
    print(f"DEBUG get_available_models: gemini_key length={len(gemini_key) if gemini_key else 0}")
    print(f"DEBUG get_available_models: gemini_key != placeholder={gemini_key != 'YOUR_GEMINI_API_KEY_HERE' if gemini_key else False}")
    
    gemini_available = bool(
        GEMINI_AVAILABLE and 
        gemini_key and 
        gemini_key != 'YOUR_GEMINI_API_KEY_HERE' and
        len(gemini_key) > 10
    )
    
    print(f"DEBUG get_available_models: Final gemini_available={gemini_available}")
    
    models = {
        'local_template': {
            'name': 'Local Templates',
            'available': True,
            'description': 'Deterministic safe templates (no AI)'
        },
        'gemini': {
            'name': 'Google Gemini API',
            'available': gemini_available,
            'description': 'Requires GEMINI_API_KEY in .env'
        },
        'llama2_local': {
            'name': 'Llama-2 Local',
            'available': LLAMA_AVAILABLE,
            'description': 'Requires transformers and torch packages'
        }
    }
    return models

