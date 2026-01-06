"""
Detection API - Web interface for checking detection models
"""

import os
import sys
from pathlib import Path

# Add project root to path to import detection module
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def check_model_status():
    """
    Check status of detection models
    
    Returns:
        dict: Model status information
    """
    models_dir = Path(__file__).parent.parent / 'models'
    
    # Check TF-IDF + LR model
    tfidf_model = models_dir / 'phishing_detector_model.joblib'
    tfidf_vectorizer = models_dir / 'phishing_detector_vectorizer.joblib'
    tfidf_available = tfidf_model.exists() and tfidf_vectorizer.exists()
    
    # Check DistilBERT model
    distilbert_dir = models_dir / 'distilbert_phishing_detector'
    distilbert_available = distilbert_dir.exists() and (distilbert_dir / 'config.json').exists()
    
    return {
        'tfidf_lr': {
            'available': tfidf_available,
            'model_path': str(tfidf_model) if tfidf_available else None,
            'vectorizer_path': str(tfidf_vectorizer) if tfidf_available else None
        },
        'distilbert': {
            'available': distilbert_available,
            'model_path': str(distilbert_dir) if distilbert_available else None
        },
        'models_dir': str(models_dir)
    }


def test_model_with_sample(text="Subject: Urgent verification required"):
    """
    Test model with a sample text
    
    Returns:
        dict: Prediction results
    """
    models_dir = Path(__file__).parent.parent / 'models'
    results = {}
    
    # Test TF-IDF + LR if available
    tfidf_model = models_dir / 'phishing_detector_model.joblib'
    tfidf_vectorizer = models_dir / 'phishing_detector_vectorizer.joblib'
    if tfidf_model.exists() and tfidf_vectorizer.exists():
        try:
            import joblib
            import re
            import numpy as np
            
            # Load model and vectorizer
            model = joblib.load(tfidf_model)
            vectorizer = joblib.load(tfidf_vectorizer)
            
            # Preprocess text (same as training)
            def preprocess_text(text):
                if not text:
                    return ""
                text = str(text).lower()
                text = re.sub(r'[^\w\s]', ' ', text)
                text = text.strip()
                return text
            
            # Preprocess and vectorize
            processed_text = preprocess_text(text)
            text_vectorized = vectorizer.transform([processed_text])
            
            # Predict
            prediction = model.predict(text_vectorized)[0]
            probability = model.predict_proba(text_vectorized)[0]
            
            label = 'phish' if prediction == 1 else 'ham'
            prob = float(probability[1] if prediction == 1 else probability[0])
            
            results['tfidf_lr'] = {
                'available': True,
                'prediction': label,
                'confidence': prob,
                'confidence_percent': round(prob * 100, 2),
                'text': text
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            results['tfidf_lr'] = {
                'available': True,
                'error': str(e),
                'error_type': type(e).__name__
            }
    else:
        results['tfidf_lr'] = {
            'available': False,
            'message': 'Model not trained. Run: python detection/train_tfidf_lr.py'
        }
    
    # Test DistilBERT if available
    distilbert_dir = models_dir / 'distilbert_phishing_detector'
    if distilbert_dir.exists():
        try:
            from detection.eval_distilbert import predict as distilbert_predict
            
            label, prob, confidence = distilbert_predict(text, str(models_dir))
            results['distilbert'] = {
                'available': True,
                'prediction': label,
                'confidence': confidence,
                'confidence_percent': round(confidence * 100, 2),
                'probability': prob,
                'text': text
            }
        except Exception as e:
            results['distilbert'] = {
                'available': True,
                'error': str(e)
            }
    else:
        results['distilbert'] = {
            'available': False,
            'message': 'Model not trained. Run: python detection/train_distilbert.py'
        }
    
    return results

