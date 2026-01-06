#!/usr/bin/env python3
"""
End-to-end test script for Social Engineering AI system
Tests the complete workflow from scenario generation to data collection
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import csv
from datetime import datetime
from sim_server.analytics import get_all_metrics
from sim_server.detection_api import check_model_status
from sim_server.generator_api import get_available_models

def test_dataset_expansion():
    """Test if expanded dataset exists and has sufficient samples"""
    print("Testing dataset expansion...")
    
    expanded_dataset = Path("data/expanded_dataset.csv")
    if not expanded_dataset.exists():
        print("❌ Expanded dataset not found")
        return False
    
    # Count samples
    with open(expanded_dataset, 'r') as f:
        reader = csv.DictReader(f)
        samples = list(reader)
    
    phish_count = len([s for s in samples if s.get('label') == 'phish'])
    ham_count = len([s for s in samples if s.get('label') == 'ham'])
    
    print(f"✅ Expanded dataset found: {len(samples)} samples")
    print(f"   Phish: {phish_count}, Ham: {ham_count}")
    
    if len(samples) >= 500:
        print("✅ Dataset size sufficient (>= 500 samples)")
        return True
    else:
        print(f"⚠️  Dataset size below target (current: {len(samples)}, target: 500+)")
        return False

def test_human_samples():
    """Test if human-written samples are expanded"""
    print("\nTesting human-written samples...")
    
    human_file = Path("data/human_written_samples.jsonl")
    if not human_file.exists():
        print("❌ Human-written samples file not found")
        return False
    
    count = 0
    with open(human_file, 'r') as f:
        for line in f:
            if line.strip():
                count += 1
    
    print(f"✅ Human-written samples: {count} samples")
    
    if count >= 20:
        print("✅ Human samples sufficient (>= 20 samples)")
        return True
    else:
        print(f"⚠️  Human samples below target (current: {count}, target: 20+)")
        return False

def test_model_status():
    """Test model status"""
    print("\nTesting model status...")
    
    try:
        status = check_model_status()
        print(f"✅ Model status check successful")
        print(f"   TF-IDF+LR: {'Available' if status.get('tfidf_lr', {}).get('available', False) else 'Not trained'}")
        print(f"   DistilBERT: {'Available' if status.get('distilbert', {}).get('available', False) else 'Not trained'}")
        return True
    except Exception as e:
        print(f"⚠️  Model status check failed: {e}")
        return False

def test_analytics():
    """Test analytics module"""
    print("\nTesting analytics module...")
    
    try:
        metrics = get_all_metrics()
        print("✅ Analytics module working")
        print(f"   Total interactions: {metrics.get('total_interactions', 0)}")
        print(f"   Unique participants: {metrics.get('unique_participants', 0)}")
        print(f"   Advanced analytics: {metrics.get('advanced_analytics', {})}")
        return True
    except Exception as e:
        print(f"❌ Analytics test failed: {e}")
        return False

def test_generator_models():
    """Test available generator models"""
    print("\nTesting generator models...")
    
    try:
        models = get_available_models()
        print("✅ Generator models check successful")
        print(f"   Available models: {', '.join(models)}")
        return True
    except Exception as e:
        print(f"⚠️  Generator models check failed: {e}")
        return False

def test_file_structure():
    """Test if all required files exist"""
    print("\nTesting file structure...")
    
    required_files = [
        "data/expanded_dataset.csv",
        "data/human_written_samples.jsonl",
        "data/generated_samples.jsonl",
        "sim_server/app.py",
        "sim_server/analytics.py",
        "sim_server/generator_api.py",
        "sim_server/detection_api.py",
        "docs/evaluation_criteria.md"
    ]
    
    missing = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing.append(file_path)
    
    if missing:
        print(f"❌ Missing files: {', '.join(missing)}")
        return False
    else:
        print("✅ All required files present")
        return True

def run_all_tests():
    """Run all end-to-end tests"""
    print("=" * 60)
    print("END-TO-END TEST SUITE")
    print("=" * 60)
    
    results = {
        'dataset_expansion': test_dataset_expansion(),
        'human_samples': test_human_samples(),
        'model_status': test_model_status(),
        'analytics': test_analytics(),
        'generator_models': test_generator_models(),
        'file_structure': test_file_structure()
    }
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready for pilot study.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please address issues before pilot study.")
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)


