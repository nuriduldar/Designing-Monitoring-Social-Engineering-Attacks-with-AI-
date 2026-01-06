"""
Flask Simulation Server for Ethical Phishing Research
DO NOT USE IN PRODUCTION - TEST ENVIRONMENT ONLY
"""

import os
import csv
import json
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
from analytics import get_all_metrics
from review_manager import load_review_queue, approve_message, reject_message, get_review_stats
from email_service import send_scenario_email, test_smtp_connection
from generator_api import generate_sample_via_api, generate_multiple_samples, get_available_models
from detection_api import check_model_status, test_model_with_sample
from translations import get_translation, get_lang, set_lang
import subprocess
import threading

# Load .env from project root (parent directory)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
print(f"✅ .env loaded from: {env_path}")
print(f"✅ GEMINI_API_KEY exists: {bool(os.getenv('GEMINI_API_KEY'))}")

app = Flask(__name__)
# WARNING: In production, SECRET_KEY must be set in .env file!
# Generate a secure key: python -c "import secrets; print(secrets.token_hex(32))"
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Configuration
LOG_PATH = os.getenv('LOG_PATH', 'interaction_logs.csv')
DATA_DIR = Path(__file__).parent.parent / 'data'
SAMPLES_FILE = DATA_DIR / 'generated_samples.jsonl'

# Ensure log file exists with header
def ensure_log_file():
    """Create log file with header if it doesn't exist"""
    if not os.path.exists(LOG_PATH):
        with open(LOG_PATH, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'participant_id', 'scenario_id', 'action', 'metadata'])

# Cache variables for performance optimization
_sample_cache = {}
_logs_cache = {}
_logs_cache_timestamp = 0
_stats_cache = {}
_stats_cache_timestamp = 0

# Load sample from JSONL - OPTIMIZED WITH CACHE
def load_sample(scenario_id, lang='en'):
    """Load a sample from generated_samples.jsonl or human_written_samples.jsonl matching scenario_id - OPTIMIZED"""
    cache_key = f"{scenario_id}_{lang}"
    
    # Check cache first
    if cache_key in _sample_cache:
        return _sample_cache[cache_key]
    
    if lang == 'tr':
        default_text = f"[TEST ORTAMI] Bu, {scenario_id} senaryosu için simüle edilmiş bir phishing mesajıdır. GERÇEK KİMLİK BİLGİLERİ GİRMEYİN."
    else:
        default_text = f"[TEST ENVIRONMENT] This is a simulated phishing message for scenario {scenario_id}. DO NOT ENTER REAL CREDENTIALS."
    
    result_text = default_text
    HUMAN_FILE = DATA_DIR / 'human_written_samples.jsonl'
    EXPANDED_DATASET = DATA_DIR / 'expanded_dataset.csv'
    
    # Try expanded dataset first (most scenarios are here)
    if EXPANDED_DATASET.exists():
        try:
            import csv
            with open(EXPANDED_DATASET, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('id') == str(scenario_id):
                        text = row.get('text', '')
                        if text:
                            # Translate if Turkish is selected
                            if lang == 'tr':
                                result_text = translate_text_with_gemini(text, 'tr')
                            else:
                                result_text = text
                            break
        except Exception as e:
            print(f"Error loading dataset sample: {e}")
    
    # Try human-written samples if not found
    if result_text == default_text and HUMAN_FILE.exists():
        try:
            with open(HUMAN_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        sample = json.loads(line)
                        if sample.get('id') == scenario_id or sample.get('scenario_id') == scenario_id:
                            text = sample.get('text', default_text)
                            # Translate if Turkish is selected
                            if lang == 'tr' and text and text != default_text:
                                result_text = translate_text_with_gemini(text, 'tr')
                            else:
                                result_text = text
                            break
        except (json.JSONDecodeError, KeyError, IOError) as e:
            print(f"Error loading human sample: {e}")
    
    # Try AI-generated samples if not found
    if result_text == default_text and SAMPLES_FILE.exists():
        try:
            with open(SAMPLES_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        sample = json.loads(line)
                        if sample.get('id') == scenario_id or sample.get('scenario_id') == scenario_id:
                            text = sample.get('text', default_text)
                            # Translate if Turkish is selected
                            if lang == 'tr' and text and text != default_text:
                                result_text = translate_text_with_gemini(text, 'tr')
                            else:
                                result_text = text
                            break
        except (json.JSONDecodeError, KeyError, IOError) as e:
            print(f"Error loading AI sample: {e}")
    
    # Cache the result
    _sample_cache[cache_key] = result_text
    
    return result_text

@app.route('/set_language/<lang>')
def set_language(lang):
    """Set language preference"""
    set_lang(lang)
    return jsonify({'status': 'success', 'language': lang}), 200

@app.route('/')
def index():
    """Main index page"""
    lang = get_lang()
    return render_template('index.html', lang=lang, t=get_translation)

@app.route('/scenario/<scenario_id>')
def scenario(scenario_id):
    """Render phishing scenario page (default: email)"""
    lang = get_lang()
    phishing_text = load_sample(scenario_id, lang)
    return render_template('phishing_page.html', 
                         phishing_text=phishing_text, 
                         scenario_id=scenario_id,
                         lang=lang, t=get_translation)

@app.route('/scenario/<scenario_id>/spear')
def scenario_spear(scenario_id):
    """Render spear-phishing scenario page"""
    lang = get_lang()
    phishing_text = load_sample(scenario_id, lang)
    return render_template('spear_phishing_page.html', 
                         phishing_text=phishing_text, 
                         scenario_id=scenario_id,
                         lang=lang, t=get_translation)

@app.route('/scenario/<scenario_id>/sms')
def scenario_sms(scenario_id):
    """Render SMS phishing scenario page"""
    lang = get_lang()
    phishing_text = load_sample(scenario_id, lang)
    return render_template('sms_phishing_page.html', 
                         phishing_text=phishing_text, 
                         scenario_id=scenario_id,
                         lang=lang, t=get_translation)

@app.route('/scenario/<scenario_id>/login')
def scenario_login(scenario_id):
    """Render fake login page scenario"""
    lang = get_lang()
    phishing_text = load_sample(scenario_id, lang)
    return render_template('fake_login_page.html', 
                         phishing_text=phishing_text, 
                         scenario_id=scenario_id,
                         lang=lang, t=get_translation)

@app.route('/scenario/<scenario_id>/social')
def scenario_social(scenario_id):
    """Render social media trap scenario"""
    lang = get_lang()
    phishing_text = load_sample(scenario_id, lang)
    return render_template('social_media_trap.html', 
                         phishing_text=phishing_text, 
                         scenario_id=scenario_id,
                         lang=lang, t=get_translation)

@app.route('/click', methods=['POST'])
def record_click():
    """Record user interaction"""
    try:
        data = request.get_json()
        participant_id = data.get('participant', 'unknown')
        scenario_id = data.get('scenario', 'unknown')
        action = data.get('action', 'click')
        metadata = json.dumps(data.get('metadata', {}))
        
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Ensure log file exists
        ensure_log_file()
        
        # Append to CSV
        with open(LOG_PATH, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, participant_id, scenario_id, action, metadata])
        
        return jsonify({'status': 'recorded', 'timestamp': timestamp}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/logs')
def get_logs():
    """Get last N log entries (JSON API) - OPTIMIZED WITH CACHE"""
    global _logs_cache_timestamp
    try:
        last_n = int(request.args.get('last', 10))
        
        # Check if log file changed
        log_timestamp = get_file_timestamp(LOG_PATH) if os.path.exists(LOG_PATH) else 0
        cache_key = f"api_{last_n}_{log_timestamp}"
        
        # Return cached version if available and file hasn't changed
        if cache_key in _logs_cache and log_timestamp == _logs_cache_timestamp:
            logs = _logs_cache[cache_key]
        else:
            if not os.path.exists(LOG_PATH):
                logs = []
            else:
                logs = []
                with open(LOG_PATH, 'r', newline='') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    for row in rows[-last_n:]:
                        logs.append(row)
            
            # Update cache
            _logs_cache[cache_key] = logs
            _logs_cache_timestamp = log_timestamp
        
        return jsonify({'logs': logs}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/logs/view')
def view_logs():
    """View logs in HTML page - OPTIMIZED WITH CACHE"""
    global _logs_cache_timestamp
    try:
        last_n = int(request.args.get('last', 50))
        
        # Check if log file changed
        log_timestamp = get_file_timestamp(LOG_PATH) if os.path.exists(LOG_PATH) else 0
        cache_key = f"view_{last_n}_{log_timestamp}"
        
        # Return cached version if available and file hasn't changed
        if cache_key in _logs_cache and log_timestamp == _logs_cache_timestamp:
            logs = _logs_cache[cache_key]
        else:
            if not os.path.exists(LOG_PATH):
                logs = []
            else:
                logs = []
                with open(LOG_PATH, 'r', newline='') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    for row in rows[-last_n:]:
                        logs.append(row)
                logs.reverse()  # Most recent first
            
            # Update cache
            _logs_cache[cache_key] = logs
            _logs_cache_timestamp = log_timestamp
        
        lang = get_lang()
        return render_template('logs.html', logs=logs, total=len(logs), lang=lang, t=get_translation)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/stats')
def stats():
    """Statistics page - OPTIMIZED WITH CACHE"""
    global _stats_cache_timestamp
    try:
        # Check if log file changed
        log_timestamp = get_file_timestamp(LOG_PATH) if os.path.exists(LOG_PATH) else 0
        
        # Return cached version if available and file hasn't changed
        if log_timestamp == _stats_cache_timestamp and 'data' in _stats_cache:
            stats_data = _stats_cache['data']
            scenario_count = _stats_cache.get('scenario_count', 5)
        else:
            stats_data = {
                'total_interactions': 0,
                'unique_participants': set(),
                'scenario_counts': {},
                'recent_activity': []
            }
            
            if os.path.exists(LOG_PATH):
                with open(LOG_PATH, 'r', newline='') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    stats_data['total_interactions'] = len(rows)
                    
                    for row in rows:
                        stats_data['unique_participants'].add(row.get('participant_id', 'unknown'))
                        scenario = row.get('scenario_id', 'unknown')
                        stats_data['scenario_counts'][scenario] = stats_data['scenario_counts'].get(scenario, 0) + 1
                    
                    stats_data['recent_activity'] = rows[-10:]
                    stats_data['recent_activity'].reverse()
            
            stats_data['unique_participants'] = len(stats_data['unique_participants'])
            
            # Count available scenarios (use cached scenarios if available)
            if 'en' in _scenarios_cache:
                scenario_count = len(_scenarios_cache['en'])
            else:
                scenario_count = 0
                if SAMPLES_FILE.exists():
                    with open(SAMPLES_FILE, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                scenario_count += 1
            
            # Update cache
            _stats_cache['data'] = stats_data
            _stats_cache['scenario_count'] = scenario_count
            _stats_cache_timestamp = log_timestamp
        
        lang = get_lang()
        return render_template('stats.html', 
                             stats=stats_data, 
                             scenario_count=max(scenario_count, 5),
                             lang=lang, t=get_translation)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Translation cache to avoid re-translating the same text
_translation_cache = {}
_translation_cache_file = DATA_DIR / 'translations_cache.json'

# Scenario cache to avoid re-reading files on every request
_scenarios_cache = {}
_scenarios_cache_timestamp = {}
_scenarios_cache_file_timestamps = {}

def load_translation_cache():
    """Load translation cache from file"""
    global _translation_cache
    if _translation_cache_file.exists():
        try:
            with open(_translation_cache_file, 'r', encoding='utf-8') as f:
                _translation_cache = json.load(f)
                print(f"✅ Loaded {len(_translation_cache)} cached translations")
        except Exception as e:
            print(f"⚠️ Error loading translation cache: {e}")
            _translation_cache = {}

def save_translation_cache():
    """Save translation cache to file"""
    try:
        with open(_translation_cache_file, 'w', encoding='utf-8') as f:
            json.dump(_translation_cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Error saving translation cache: {e}")

def get_file_timestamp(file_path):
    """Get file modification timestamp"""
    try:
        return os.path.getmtime(file_path)
    except:
        return 0

def load_scenarios_cached(lang='en'):
    """Load scenarios with caching - only reload if files changed"""
    cache_key = lang
    HUMAN_FILE = DATA_DIR / 'human_written_samples.jsonl'
    EXPANDED_DATASET = DATA_DIR / 'expanded_dataset.csv'
    
    # Check if cache is valid
    files_changed = False
    current_timestamps = {}
    
    if HUMAN_FILE.exists():
        current_timestamps['human'] = get_file_timestamp(HUMAN_FILE)
        if current_timestamps['human'] != _scenarios_cache_file_timestamps.get('human', 0):
            files_changed = True
    
    if SAMPLES_FILE.exists():
        current_timestamps['samples'] = get_file_timestamp(SAMPLES_FILE)
        if current_timestamps['samples'] != _scenarios_cache_file_timestamps.get('samples', 0):
            files_changed = True
    
    if EXPANDED_DATASET.exists():
        current_timestamps['dataset'] = get_file_timestamp(EXPANDED_DATASET)
        if current_timestamps['dataset'] != _scenarios_cache_file_timestamps.get('dataset', 0):
            files_changed = True
    
    # Return cached version if files haven't changed
    if cache_key in _scenarios_cache and not files_changed:
        return _scenarios_cache[cache_key]
    
    # Files changed or cache miss - reload
    scenarios_list = []
    seen_ids = set()  # Use set for O(1) duplicate checking
    
    # Load human-written samples
    if HUMAN_FILE.exists():
        try:
            with open(HUMAN_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        sample = json.loads(line)
                        scenario_id = sample.get('id', 'unknown')
                        if scenario_id in seen_ids:
                            continue
                        seen_ids.add(scenario_id)
                        text = sample.get('text', '')
                        # Translate if Turkish is selected (with caching)
                        if lang == 'tr' and text:
                            translated_text = translate_text_with_gemini(text, 'tr')
                            preview = translated_text[:100] + '...' if len(translated_text) > 100 else translated_text
                        else:
                            translated_text = text
                            preview = text[:100] + '...' if len(text) > 100 else text
                        scenarios_list.append({
                            'id': scenario_id,
                            'tone': sample.get('tone', 'unknown'),
                            'role': sample.get('role', 'unknown'),
                            'created_at': sample.get('created_at', 'unknown'),
                            'source': 'human',
                            'preview': preview,
                            'text': translated_text
                        })
        except Exception as e:
            print(f"Error loading human scenarios: {e}")
    
    # Load AI-generated samples (including Gemini)
    if SAMPLES_FILE.exists():
        try:
            with open(SAMPLES_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        sample = json.loads(line)
                        scenario_id = sample.get('id', 'unknown')
                        if scenario_id in seen_ids:
                            continue
                        seen_ids.add(scenario_id)
                        text = sample.get('text', '')
                        sample_source = sample.get('source', 'ai')
                        if sample_source == 'gemini':
                            sample_source = 'gemini'
                        elif sample_source in ['ai', 'local_template', 'llama2_local']:
                            sample_source = 'ai'
                        # Translate if Turkish is selected (with caching)
                        if lang == 'tr' and text:
                            translated_text = translate_text_with_gemini(text, 'tr')
                            preview = translated_text[:100] + '...' if len(translated_text) > 100 else translated_text
                        else:
                            translated_text = text
                            preview = text[:100] + '...' if len(text) > 100 else text
                        scenarios_list.append({
                            'id': scenario_id,
                            'tone': sample.get('tone', 'unknown'),
                            'role': sample.get('role', 'unknown'),
                            'created_at': sample.get('created_at', 'unknown'),
                            'source': sample_source,
                            'preview': preview,
                            'text': translated_text
                        })
        except Exception as e:
            print(f"Error loading AI scenarios: {e}")
    
    # Load scenarios from expanded dataset
    if EXPANDED_DATASET.exists():
        try:
            import csv
            with open(EXPANDED_DATASET, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    label = row.get('label', '').lower()
                    scenario_id = row.get('id', f"dataset_{len(scenarios_list)}")
                    if scenario_id in seen_ids:
                        continue
                    seen_ids.add(scenario_id)
                    text = row.get('text', '')
                    
                    if label == 'phish' or (label == 'ham' or label == 'legitimate'):
                        # Translate if Turkish is selected (with caching)
                        if lang == 'tr' and text:
                            translated_text = translate_text_with_gemini(text, 'tr')
                            preview = translated_text[:100] + '...' if len(translated_text) > 100 else translated_text
                        else:
                            translated_text = text
                            preview = text[:100] + '...' if len(text) > 100 else text
                        scenarios_list.append({
                            'id': scenario_id,
                            'tone': row.get('tone', 'unknown'),
                            'role': row.get('role', 'unknown'),
                            'created_at': row.get('created_by', 'dataset'),
                            'source': 'dataset',
                            'preview': preview,
                            'text': translated_text,
                            'label': 'phish' if label == 'phish' else 'ham'
                        })
        except Exception as e:
            print(f"Error loading dataset scenarios: {e}")
    
    # Sort by ID
    scenarios_list.sort(key=lambda x: x['id'])
    
    # Update cache
    _scenarios_cache[cache_key] = scenarios_list
    _scenarios_cache_file_timestamps.update(current_timestamps)
    
    # Save translation cache at the end
    if lang == 'tr' and _translation_cache:
        save_translation_cache()
    
    return scenarios_list

# Load cache on startup
load_translation_cache()

def translate_text_with_gemini(text, target_lang='tr'):
    """Translate text using free translation library with caching - NO API COST"""
    if target_lang == 'en' or not text:
        return text
    
    # Check cache first
    text_hash = str(hash(text))
    if text_hash in _translation_cache:
        return _translation_cache[text_hash]
    
    # Translate if not in cache
    try:
        # Try using deep-translator (free, no API key needed for basic usage)
        from deep_translator import GoogleTranslator
        
        # Preserve [TEST ENVIRONMENT] tags
        test_env_tag = '[TEST ENVIRONMENT]'
        has_tag = test_env_tag in text
        
        # Translate
        translator = GoogleTranslator(source='en', target='tr')
        translated = translator.translate(text)
        
        # Ensure [TEST ENVIRONMENT] tags are preserved
        if has_tag and '[TEST ENVIRONMENT]' not in translated:
            # Replace Turkish version if it exists
            translated = translated.replace('[TEST ORTAMI]', '[TEST ENVIRONMENT]')
            # If tag was at the beginning, ensure it's there
            if text.startswith(test_env_tag) and not translated.startswith(test_env_tag):
                translated = test_env_tag + ' ' + translated
        
        # Cache the translation
        _translation_cache[text_hash] = translated
        # Save cache periodically (every 10 new translations)
        if len(_translation_cache) % 10 == 0:
            save_translation_cache()
        
        return translated
    except Exception as e:
        # If translation fails, cache the original text to avoid retrying
        print(f"Translation error for text (first 50 chars): {text[:50]}... Error: {e}")
        _translation_cache[text_hash] = text  # Cache original to avoid retrying
        return text  # Return original on error
    except ImportError:
        # If deep-translator is not installed, try googletrans as fallback
        try:
            from googletrans import Translator
            translator = Translator()
            result = translator.translate(text, src='en', dest='tr')
            translated = result.text
            
            # Preserve [TEST ENVIRONMENT] tags
            if '[TEST ENVIRONMENT]' in text:
                translated = translated.replace('[TEST ORTAMI]', '[TEST ENVIRONMENT]')
            
            # Cache the translation
            _translation_cache[text_hash] = translated
            if len(_translation_cache) % 10 == 0:
                save_translation_cache()
            
            return translated
        except ImportError:
            print("⚠️ Translation libraries not installed. Install with: pip3 install deep-translator")
            # Cache original to avoid retrying
            _translation_cache[text_hash] = text
            return text  # Return original if no translator available
    except Exception as e:
        print(f"Translation error: {e}")
        # Cache original to avoid retrying
        _translation_cache[text_hash] = text
        return text  # Return original on error

@app.route('/scenarios')
def scenarios():
    """List all available scenarios (from JSONL files and expanded dataset) - OPTIMIZED WITH CACHE"""
    lang = get_lang()
    
    # Use cached scenarios (only reload if files changed)
    # This function already loads all scenarios from all sources with duplicate checking
    scenarios_list = load_scenarios_cached(lang)
    
    # Add default scenarios if none found
    if not scenarios_list:
        tones = ['urgent', 'polite', 'curious', 'authoritative', 'friendly']
        for i in range(1, 6):
            scenarios_list.append({
                'id': f'scenario_00{i}',
                'tone': tones[i-1],
                'role': 'employee',
                'created_at': '2024-01-15T10:30:00Z',
                'source': 'ai',
                'preview': f'[TEST ENVIRONMENT] Simulated phishing message for scenario {i}...',
                'text': f'[TEST ENVIRONMENT] Simulated phishing message for scenario {i}...'
            })
    
    return render_template('scenarios.html', scenarios=scenarios_list, lang=lang, t=get_translation)

@app.route('/analytics')
def analytics():
    """Detailed analytics and metrics page"""
    lang = get_lang()
    try:
        metrics = get_all_metrics(LOG_PATH)
        return render_template('analytics.html', metrics=metrics, lang=lang, t=get_translation)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/survey/pre')
def pre_survey():
    """Pre-study survey page"""
    lang = get_lang()
    return render_template('pre_survey.html', lang=lang, t=get_translation)

@app.route('/survey/post')
def post_survey():
    """Post-study survey page"""
    lang = get_lang()
    return render_template('post_survey.html', lang=lang, t=get_translation)

@app.route('/survey/submit', methods=['POST'])
def submit_survey():
    """Submit survey responses"""
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        # Save to surveys CSV
        surveys_file = 'survey_responses.csv'
        file_exists = os.path.exists(surveys_file)
        
        # Get all field names (excluding metadata fields)
        field_names = [k for k in data.keys() if k not in ['timestamp', 'participant_id', 'survey_type']]
        
        with open(surveys_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                # Write header
                header = ['timestamp', 'participant_id', 'survey_type'] + sorted(field_names)
                writer.writerow(header)
            
            # Write data row
            timestamp = data.get('timestamp', datetime.utcnow().isoformat() + 'Z')
            participant_id = data.get('participant_id', 'unknown')
            survey_type = data.get('survey_type', 'unknown')
            
            row = [timestamp, participant_id, survey_type]
            row.extend([str(data.get(k, '')) for k in sorted(field_names)])
            writer.writerow(row)
        
        return jsonify({
            'status': 'success', 
            'message': 'Survey submitted successfully',
            'participant_id': participant_id,
            'survey_type': survey_type
        }), 200
    
    except Exception as e:
        print(f"Survey submit error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'message': 'Error submitting survey'}), 400

@app.route('/review/queue')
def review_queue():
    """Get review queue page"""
    return render_template('review_queue.html')

@app.route('/review/queue/api')
def review_queue_api():
    """Get review queue items (JSON API)"""
    try:
        items = load_review_queue()
        # Add safety checks
        for item in items:
            text = item.get('text', '')
            item['has_test_tag'] = '[TEST ENVIRONMENT]' in text
            item['flagged_keywords'] = []
            keywords = ['password', 'credentials', 'ssn', 'bank', 'credit card', 'social security']
            text_lower = text.lower()
            for keyword in keywords:
                if keyword in text_lower:
                    item['flagged_keywords'].append(keyword)
        
        return jsonify({'items': items, 'count': len(items)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/review/approve', methods=['POST'])
def review_approve():
    """Approve a message"""
    try:
        data = request.get_json()
        item_id = data.get('id')
        result = approve_message(item_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/review/reject', methods=['POST'])
def review_reject():
    """Reject a message"""
    try:
        data = request.get_json()
        item_id = data.get('id')
        reason = data.get('reason', '')
        result = reject_message(item_id, reason)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/review/stats')
def review_stats():
    """Get review statistics"""
    try:
        stats = get_review_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/email/send', methods=['POST'])
def send_email():
    """Send a scenario email via SMTP"""
    try:
        data = request.get_json()
        to_email = data.get('to_email')
        scenario_id = data.get('scenario_id')
        
        if not to_email or not scenario_id:
            return jsonify({'error': 'Missing to_email or scenario_id'}), 400
        
        # Load scenario text
        scenario_text = load_sample(scenario_id)
        
        # Send email
        result = send_scenario_email(to_email, scenario_id, scenario_text)
        
        return jsonify(result), 200 if result['status'] == 'sent' else 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/email/test')
def test_email_connection():
    """Test SMTP connection"""
    try:
        result = test_smtp_connection()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/scenarios/manage')
def manage_scenarios():
    """Manage scenarios page"""
    lang = get_lang()
    return render_template('manage_scenarios.html', lang=lang, t=get_translation)

@app.route('/scenarios/create', methods=['POST'])
def create_scenario():
    """Create a new scenario"""
    try:
        data = request.get_json()
        scenario_id = data.get('scenario_id')
        source = data.get('source', 'ai')
        tone = data.get('tone', 'polite')
        role = data.get('role', 'employee')
        text = data.get('text', '')
        
        if not scenario_id or not text:
            return jsonify({'error': 'Missing scenario_id or text'}), 400
        
        # Ensure [TEST ENVIRONMENT] tag
        if '[TEST ENVIRONMENT]' not in text:
            text = f"[TEST ENVIRONMENT] {text} [TEST ENVIRONMENT]"
        
        scenario = {
            'id': scenario_id,
            'text': text,
            'tone': tone,
            'role': role,
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'source': source
        }
        
        # Save to appropriate file
        if source == 'human':
            target_file = DATA_DIR / 'human_written_samples.jsonl'
        else:
            target_file = SAMPLES_FILE
        
        with open(target_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(scenario, ensure_ascii=False) + '\n')
        
        return jsonify({'status': 'created', 'scenario_id': scenario_id}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/scenarios/delete/<scenario_id>', methods=['DELETE'])
def delete_scenario(scenario_id):
    """Delete a scenario"""
    try:
        deleted = False
        
        # Try human file first
        human_file = DATA_DIR / 'human_written_samples.jsonl'
        if human_file.exists():
            lines = []
            with open(human_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        sample = json.loads(line)
                        if sample.get('id') != scenario_id:
                            lines.append(line)
                        else:
                            deleted = True
            
            if deleted:
                with open(human_file, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
        
        # Try AI file
        if not deleted and SAMPLES_FILE.exists():
            lines = []
            with open(SAMPLES_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        sample = json.loads(line)
                        if sample.get('id') != scenario_id:
                            lines.append(line)
                        else:
                            deleted = True
            
            if deleted:
                with open(SAMPLES_FILE, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
        
        if deleted:
            return jsonify({'status': 'deleted', 'scenario_id': scenario_id}), 200
        else:
            return jsonify({'error': 'Scenario not found'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/generate', methods=['POST'])
def api_generate():
    """Generate phishing sample via API"""
    try:
        data = request.get_json() or {}
        tone = data.get('tone', 'polite')
        role = data.get('role', 'employee')
        use_llama = data.get('use_llama', False)
        use_gemini = data.get('use_gemini', True)  # Default to True (use Gemini)
        llama_model_path = data.get('llama_model_path', None)
        count = data.get('count', 1)
        
        if count > 1:
            result = generate_multiple_samples(count, use_llama, use_gemini, llama_model_path)
        else:
            result = generate_sample_via_api(tone=tone, target_role=role, use_llama=use_llama, use_gemini=use_gemini, llama_model_path=llama_model_path)
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/model/status')
def api_model_status():
    """Get detection model status"""
    try:
        status = check_model_status()
        return jsonify(status), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/model/test', methods=['POST'])
def api_model_test():
    """Test detection model with sample text"""
    try:
        data = request.get_json() or {}
        text = data.get('text', 'Subject: Urgent verification required')
        
        results = test_model_with_sample(text)
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/generate/models')
def api_available_models():
    """Get available AI models for generation"""
    try:
        # Force reload .env
        from dotenv import load_dotenv
        from pathlib import Path
        env_path = Path(__file__).parent.parent / '.env'
        load_dotenv(dotenv_path=env_path, override=True)
        
        # Debug logging
        import os
        gemini_key = os.getenv('GEMINI_API_KEY')
        print(f"DEBUG: GEMINI_API_KEY exists: {bool(gemini_key)}")
        print(f"DEBUG: GEMINI_API_KEY length: {len(gemini_key) if gemini_key else 0}")
        
        models = get_available_models()
        print(f"DEBUG: Gemini available in models: {models['gemini']['available']}")
        return jsonify(models), 200
    except Exception as e:
        print(f"ERROR in api_available_models: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400

@app.route('/train')
def train_model_page():
    """Train model page"""
    lang = get_lang()
    return render_template('train_model.html', lang=lang, t=get_translation)

@app.route('/api/model/train/tfidf-lr', methods=['POST'])
def api_train_tfidf_lr():
    """Train TF-IDF + Logistic Regression model"""
    try:
        # Run training script (use simple version to avoid pandas issues)
        script_path = Path(__file__).parent.parent / 'detection' / 'train_tfidf_lr_simple.py'
        data_path = Path(__file__).parent.parent / 'data' / 'expanded_dataset.csv'
        models_dir = Path(__file__).parent.parent / 'models'
        
        if not data_path.exists():
            return jsonify({
                'status': 'error',
                'message': f'Data file not found: {data_path}'
            }), 400
        
        # Run training in background thread
        def run_training():
            try:
                result = subprocess.run(
                    ['python3', str(script_path), '--data-path', str(data_path), '--output-dir', str(models_dir)],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes timeout
                )
                return result
            except subprocess.TimeoutExpired:
                return None
        
        result = run_training()
        
        if result and result.returncode == 0:
            # Parse metrics from output
            output = result.stdout
            metrics = {
                'accuracy': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'f1': 0.0
            }
            
            # Try to parse metrics from output
            import re
            accuracy_match = re.search(r'Test Accuracy:\s+([\d.]+)', output)
            precision_match = re.search(r'Precision:\s+([\d.]+)', output)
            recall_match = re.search(r'Recall:\s+([\d.]+)', output)
            f1_match = re.search(r'F1-Score:\s+([\d.]+)', output)
            
            if accuracy_match:
                metrics['accuracy'] = float(accuracy_match.group(1))
            if precision_match:
                metrics['precision'] = float(precision_match.group(1))
            if recall_match:
                metrics['recall'] = float(recall_match.group(1))
            if f1_match:
                metrics['f1'] = float(f1_match.group(1))
            
            # If metrics file exists, read from there
            metrics_file = models_dir / 'model_metrics.txt'
            if metrics_file.exists():
                try:
                    with open(metrics_file, 'r') as f:
                        content = f.read()
                        # Parse from metrics file
                        for line in content.split('\n'):
                            if 'Accuracy:' in line:
                                match = re.search(r'Accuracy:\s+([\d.]+)', line)
                                if match:
                                    metrics['accuracy'] = float(match.group(1))
                            elif 'Precision:' in line:
                                match = re.search(r'Precision:\s+([\d.]+)', line)
                                if match:
                                    metrics['precision'] = float(match.group(1))
                            elif 'Recall:' in line:
                                match = re.search(r'Recall:\s+([\d.]+)', line)
                                if match:
                                    metrics['recall'] = float(match.group(1))
                            elif 'F1-Score:' in line:
                                match = re.search(r'F1-Score:\s+([\d.]+)', line)
                                if match:
                                    metrics['f1'] = float(match.group(1))
                except Exception:
                    pass
            
            return jsonify({
                'status': 'success',
                'message': 'Model trained successfully',
                'model_path': str(models_dir / 'phishing_detector_model.joblib'),
                'metrics': metrics
            }), 200
        else:
            error_msg = result.stderr if result else 'Training timeout'
            return jsonify({
                'status': 'error',
                'message': f'Training failed: {error_msg}'
            }), 400
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/model/train/distilbert', methods=['POST'])
def api_train_distilbert():
    """Train DistilBERT model (async)"""
    try:
        script_path = Path(__file__).parent.parent / 'detection' / 'train_distilbert.py'
        data_path = Path(__file__).parent.parent / 'data' / 'expanded_dataset.csv'
        models_dir = Path(__file__).parent.parent / 'models'
        distilbert_dir = models_dir / 'distilbert_phishing_detector'
        
        # Check if model already exists
        if distilbert_dir.exists() and (distilbert_dir / 'config.json').exists():
            return jsonify({
                'status': 'already_trained',
                'message': 'DistilBERT model is already trained. Model files exist.',
                'model_path': str(distilbert_dir)
            }), 200
        
        if not data_path.exists():
            return jsonify({
                'status': 'error',
                'message': f'Data file not found: {data_path}'
            }), 400
        
        # Check if training is already running
        try:
            import psutil
            training_running = False
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and 'train_distilbert.py' in ' '.join(cmdline):
                        training_running = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if training_running:
                return jsonify({
                    'status': 'running',
                    'message': 'DistilBERT training is already in progress. Please wait for it to complete.'
                }), 200
        except ImportError:
            # psutil not available, skip check
            pass
        
        # Start training in background
        def run_training():
            try:
                result = subprocess.run(
                    ['python3', str(script_path), '--data-path', str(data_path), '--output-dir', str(models_dir)],
                    capture_output=True,
                    text=True,
                    timeout=1800  # 30 minutes timeout
                )
                if result.returncode == 0:
                    print("✅ DistilBERT training completed successfully")
                else:
                    print(f"❌ DistilBERT training failed: {result.stderr}")
            except subprocess.TimeoutExpired:
                print("❌ DistilBERT training timeout (30 minutes)")
            except Exception as e:
                print(f"❌ Training error: {e}")
        
        thread = threading.Thread(target=run_training)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'started',
            'message': 'DistilBERT training started in background. This may take 10-30 minutes. The model will be available when training completes.'
        }), 200
    
    except ImportError:
        # psutil not available, continue without checking
        pass
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/model/train/status')
def api_train_status():
    """Get training status"""
    try:
        models_dir = Path(__file__).parent.parent / 'models'
        distilbert_dir = models_dir / 'distilbert_phishing_detector'
        
        # Check if model exists
        if distilbert_dir.exists() and (distilbert_dir / 'config.json').exists():
            return jsonify({
                'status': 'completed',
                'percent': 100,
                'message': 'DistilBERT model is trained and ready'
            }), 200
        
        # Check if training is running
        try:
            import psutil
            training_running = False
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and 'train_distilbert.py' in ' '.join(cmdline):
                        training_running = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except ImportError:
            training_running = False
        
        if training_running:
            return jsonify({
                'status': 'running',
                'percent': 50,  # Estimated
                'message': 'DistilBERT training in progress...'
            }), 200
        
        return jsonify({
            'status': 'idle',
            'percent': 0,
            'message': 'No training in progress'
        }), 200
    except ImportError:
        # psutil not available
        models_dir = Path(__file__).parent.parent / 'models'
        distilbert_dir = models_dir / 'distilbert_phishing_detector'
        if distilbert_dir.exists() and (distilbert_dir / 'config.json').exists():
            return jsonify({
                'status': 'completed',
                'percent': 100,
                'message': 'DistilBERT model is trained and ready'
            }), 200
        return jsonify({
            'status': 'unknown',
            'percent': 0,
            'message': 'Cannot determine training status'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'percent': 0,
            'message': str(e)
        }), 400

if __name__ == '__main__':
    ensure_log_file()
    app.run(host='0.0.0.0', port=5000, debug=True)

