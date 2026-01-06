"""
Analytics module for calculating detailed metrics
Precision, Recall, F1-score, CTR, Response Time, etc.
"""

import csv
import json
import os
from datetime import datetime
from collections import defaultdict
from pathlib import Path
import statistics


def load_logs(log_path='interaction_logs.csv'):
    """Load interaction logs from CSV"""
    if not os.path.exists(log_path):
        return []
    
    logs = []
    with open(log_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            logs.append(row)
    
    return logs


def calculate_ctr(logs):
    """Calculate Click-Through Rate"""
    if not logs:
        return 0.0
    
    total_views = len([l for l in logs if l.get('action') == 'view'])
    total_clicks = len([l for l in logs if l.get('action') in ['click', 'form_submit', 'social_media_click']])
    
    if total_views == 0:
        return 0.0
    
    return (total_clicks / (total_views + total_clicks)) * 100


def calculate_response_times(logs):
    """Calculate response times from metadata"""
    response_times = []
    
    for log in logs:
        try:
            metadata = json.loads(log.get('metadata', '{}'))
            if 'timestamp' in metadata:
                # Calculate time difference if available
                log_time = datetime.fromisoformat(log.get('timestamp', '').replace('Z', '+00:00'))
                metadata_time = datetime.fromisoformat(metadata['timestamp'].replace('Z', '+00:00'))
                diff = abs((log_time - metadata_time).total_seconds())
                if diff > 0:
                    response_times.append(diff)
        except (json.JSONDecodeError, ValueError, KeyError):
            continue
    
    if not response_times:
        return {
            'mean': 0.0,
            'median': 0.0,
            'min': 0.0,
            'max': 0.0
        }
    
    return {
        'mean': statistics.mean(response_times),
        'median': statistics.median(response_times),
        'min': min(response_times),
        'max': max(response_times)
    }


def calculate_model_metrics(true_labels, predicted_labels):
    """Calculate Precision, Recall, F1-score"""
    from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score, confusion_matrix
    
    if len(true_labels) == 0 or len(predicted_labels) == 0:
        return {
            'accuracy': 0.0,
            'precision': 0.0,
            'recall': 0.0,
            'f1': 0.0,
            'confusion_matrix': [[0, 0], [0, 0]]
        }
    
    accuracy = accuracy_score(true_labels, predicted_labels)
    precision = precision_score(true_labels, predicted_labels, average='binary', zero_division=0)
    recall = recall_score(true_labels, predicted_labels, average='binary', zero_division=0)
    f1 = f1_score(true_labels, predicted_labels, average='binary', zero_division=0)
    cm = confusion_matrix(true_labels, predicted_labels).tolist()
    
    return {
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'f1': float(f1),
        'confusion_matrix': cm
    }


def calculate_scenario_stats(logs):
    """Calculate statistics per scenario"""
    scenario_stats = defaultdict(lambda: {
        'total_interactions': 0,
        'clicks': 0,
        'views': 0,
        'unique_participants': set()
    })
    
    for log in logs:
        scenario_id = log.get('scenario_id', 'unknown')
        action = log.get('action', 'unknown')
        participant_id = log.get('participant_id', 'unknown')
        
        scenario_stats[scenario_id]['total_interactions'] += 1
        scenario_stats[scenario_id]['unique_participants'].add(participant_id)
        
        if action in ['click', 'form_submit', 'social_media_click']:
            scenario_stats[scenario_id]['clicks'] += 1
        elif action == 'view':
            scenario_stats[scenario_id]['views'] += 1
    
    # Convert sets to counts
    for scenario_id in scenario_stats:
        scenario_stats[scenario_id]['unique_participants'] = len(scenario_stats[scenario_id]['unique_participants'])
        total = scenario_stats[scenario_id]['total_interactions']
        clicks = scenario_stats[scenario_id]['clicks']
        scenario_stats[scenario_id]['ctr'] = (clicks / total * 100) if total > 0 else 0.0
    
    return dict(scenario_stats)


def calculate_attack_type_stats(logs):
    """Calculate statistics per attack type"""
    attack_stats = defaultdict(lambda: {
        'total': 0,
        'clicks': 0,
        'unique_participants': set()
    })
    
    for log in logs:
        try:
            metadata = json.loads(log.get('metadata', '{}'))
            attack_type = metadata.get('attack_type', 'email_phishing')
            participant_id = log.get('participant_id', 'unknown')
            action = log.get('action', 'unknown')
            
            attack_stats[attack_type]['total'] += 1
            attack_stats[attack_type]['unique_participants'].add(participant_id)
            
            if action in ['click', 'form_submit', 'social_media_click']:
                attack_stats[attack_type]['clicks'] += 1
        except (json.JSONDecodeError, KeyError):
            continue
    
    # Convert sets to counts
    for attack_type in attack_stats:
        attack_stats[attack_type]['unique_participants'] = len(attack_stats[attack_type]['unique_participants'])
        total = attack_stats[attack_type]['total']
        clicks = attack_stats[attack_type]['clicks']
        attack_stats[attack_type]['ctr'] = (clicks / total * 100) if total > 0 else 0.0
    
    return dict(attack_stats)


def calculate_ai_vs_human_stats(logs, samples_file='data/generated_samples.jsonl', human_file='data/human_written_samples.jsonl'):
    """Compare AI-generated vs human-written message effectiveness"""
    import json
    
    # Load sample sources
    ai_scenarios = set()
    human_scenarios = set()
    
    if os.path.exists(samples_file):
        with open(samples_file, 'r') as f:
            for line in f:
                if line.strip():
                    sample = json.loads(line)
                    ai_scenarios.add(sample.get('id', ''))
    
    if os.path.exists(human_file):
        with open(human_file, 'r') as f:
            for line in f:
                if line.strip():
                    sample = json.loads(line)
                    human_scenarios.add(sample.get('id', ''))
    
    ai_logs = [l for l in logs if l.get('scenario_id', '') in ai_scenarios]
    human_logs = [l for l in logs if l.get('scenario_id', '') in human_scenarios]
    
    ai_clicks = len([l for l in ai_logs if l.get('action') in ['click', 'form_submit', 'social_media_click']])
    human_clicks = len([l for l in human_logs if l.get('action') in ['click', 'form_submit', 'social_media_click']])
    
    ai_total = len(ai_logs)
    human_total = len(human_logs)
    
    return {
        'ai': {
            'total': ai_total,
            'clicks': ai_clicks,
            'ctr': (ai_clicks / ai_total * 100) if ai_total > 0 else 0.0
        },
        'human': {
            'total': human_total,
            'clicks': human_clicks,
            'ctr': (human_clicks / human_total * 100) if human_total > 0 else 0.0
        }
    }


def calculate_time_series(logs, interval='hour'):
    """Calculate time-series metrics (CTR over time)"""
    time_series = defaultdict(lambda: {'views': 0, 'clicks': 0})
    
    for log in logs:
        try:
            timestamp = datetime.fromisoformat(log.get('timestamp', '').replace('Z', '+00:00'))
            
            if interval == 'hour':
                time_key = timestamp.strftime('%Y-%m-%d %H:00')
            elif interval == 'day':
                time_key = timestamp.strftime('%Y-%m-%d')
            elif interval == 'week':
                time_key = timestamp.strftime('%Y-W%W')
            else:
                time_key = timestamp.strftime('%Y-%m-%d %H:00')
            
            action = log.get('action', 'unknown')
            if action == 'view':
                time_series[time_key]['views'] += 1
            elif action in ['click', 'form_submit', 'social_media_click']:
                time_series[time_key]['clicks'] += 1
        except (ValueError, KeyError):
            continue
    
    # Calculate CTR for each time interval
    result = {}
    for time_key, data in time_series.items():
        total = data['views'] + data['clicks']
        ctr = (data['clicks'] / total * 100) if total > 0 else 0.0
        result[time_key] = {
            'views': data['views'],
            'clicks': data['clicks'],
            'total': total,
            'ctr': ctr
        }
    
    return result


def calculate_participant_segmentation(logs):
    """Segment participants by susceptibility level"""
    participant_stats = defaultdict(lambda: {
        'total_interactions': 0,
        'clicks': 0,
        'views': 0,
        'response_times': []
    })
    
    for log in logs:
        participant_id = log.get('participant_id', 'unknown')
        action = log.get('action', 'unknown')
        
        participant_stats[participant_id]['total_interactions'] += 1
        
        if action in ['click', 'form_submit', 'social_media_click']:
            participant_stats[participant_id]['clicks'] += 1
        elif action == 'view':
            participant_stats[participant_id]['views'] += 1
        
        # Calculate response time if available
        try:
            metadata = json.loads(log.get('metadata', '{}'))
            if 'timestamp' in metadata:
                log_time = datetime.fromisoformat(log.get('timestamp', '').replace('Z', '+00:00'))
                metadata_time = datetime.fromisoformat(metadata['timestamp'].replace('Z', '+00:00'))
                diff = abs((log_time - metadata_time).total_seconds())
                if diff > 0:
                    participant_stats[participant_id]['response_times'].append(diff)
        except (json.JSONDecodeError, ValueError, KeyError):
            continue
    
    # Calculate susceptibility scores
    segments = {
        'high': [],
        'medium': [],
        'low': []
    }
    
    for participant_id, stats in participant_stats.items():
        total = stats['total_interactions']
        clicks = stats['clicks']
        ctr = (clicks / total * 100) if total > 0 else 0.0
        
        avg_response_time = statistics.mean(stats['response_times']) if stats['response_times'] else 60.0
        
        # Susceptibility scoring
        # High: CTR > 15% or (CTR > 10% and response_time < 10s)
        # Medium: CTR 5-15% or (CTR > 0% and response_time < 30s)
        # Low: CTR < 5% or no clicks
        
        if ctr > 15 or (ctr > 10 and avg_response_time < 10):
            segments['high'].append({
                'participant_id': participant_id,
                'ctr': ctr,
                'avg_response_time': avg_response_time,
                'total_interactions': total,
                'clicks': clicks
            })
        elif ctr > 5 or (ctr > 0 and avg_response_time < 30):
            segments['medium'].append({
                'participant_id': participant_id,
                'ctr': ctr,
                'avg_response_time': avg_response_time,
                'total_interactions': total,
                'clicks': clicks
            })
        else:
            segments['low'].append({
                'participant_id': participant_id,
                'ctr': ctr,
                'avg_response_time': avg_response_time,
                'total_interactions': total,
                'clicks': clicks
            })
    
    return segments


def detect_attack_patterns(logs):
    """Detect patterns in attack effectiveness"""
    patterns = {
        'most_effective_attack_type': None,
        'most_effective_tone': None,
        'peak_engagement_time': None,
        'common_click_patterns': []
    }
    
    # Most effective attack type
    attack_stats = calculate_attack_type_stats(logs)
    if attack_stats:
        most_effective = max(attack_stats.items(), key=lambda x: x[1].get('ctr', 0))
        patterns['most_effective_attack_type'] = {
            'type': most_effective[0],
            'ctr': most_effective[1].get('ctr', 0)
        }
    
    # Most effective tone (from scenario metadata)
    tone_stats = defaultdict(lambda: {'total': 0, 'clicks': 0})
    for log in logs:
        try:
            metadata = json.loads(log.get('metadata', '{}'))
            tone = metadata.get('tone', 'unknown')
            action = log.get('action', 'unknown')
            
            tone_stats[tone]['total'] += 1
            if action in ['click', 'form_submit', 'social_media_click']:
                tone_stats[tone]['clicks'] += 1
        except (json.JSONDecodeError, KeyError):
            continue
    
    if tone_stats:
        for tone, stats in tone_stats.items():
            stats['ctr'] = (stats['clicks'] / stats['total'] * 100) if stats['total'] > 0 else 0.0
        
        most_effective_tone = max(tone_stats.items(), key=lambda x: x[1].get('ctr', 0))
        patterns['most_effective_tone'] = {
            'tone': most_effective_tone[0],
            'ctr': most_effective_tone[1].get('ctr', 0)
        }
    
    # Peak engagement time
    time_series = calculate_time_series(logs, interval='hour')
    if time_series:
        peak_time = max(time_series.items(), key=lambda x: x[1].get('clicks', 0))
        patterns['peak_engagement_time'] = {
            'time': peak_time[0],
            'clicks': peak_time[1].get('clicks', 0)
        }
    
    return patterns


def calculate_susceptibility_score(participant_id, logs):
    """Calculate individual susceptibility score for a participant"""
    participant_logs = [l for l in logs if l.get('participant_id') == participant_id]
    
    if not participant_logs:
        return 0.0
    
    total = len(participant_logs)
    clicks = len([l for l in participant_logs if l.get('action') in ['click', 'form_submit', 'social_media_click']])
    ctr = (clicks / total * 100) if total > 0 else 0.0
    
    # Calculate average response time
    response_times = []
    for log in participant_logs:
        try:
            metadata = json.loads(log.get('metadata', '{}'))
            if 'timestamp' in metadata:
                log_time = datetime.fromisoformat(log.get('timestamp', '').replace('Z', '+00:00'))
                metadata_time = datetime.fromisoformat(metadata['timestamp'].replace('Z', '+00:00'))
                diff = abs((log_time - metadata_time).total_seconds())
                if diff > 0:
                    response_times.append(diff)
        except (json.JSONDecodeError, ValueError, KeyError):
            continue
    
    avg_response_time = statistics.mean(response_times) if response_times else 60.0
    
    # Normalize scores (0-100 scale)
    normalized_ctr = min(ctr / 20.0, 1.0) * 100  # Cap at 20% CTR = 100
    normalized_response = max(0, 100 - (avg_response_time / 60.0 * 100))  # Faster = higher score
    
    # Weighted score
    susceptibility_score = (normalized_ctr * 0.5) + (normalized_response * 0.3) + (min(clicks * 10, 100) * 0.2)
    
    return round(susceptibility_score, 2)


def get_all_metrics(log_path='interaction_logs.csv'):
    """Get all calculated metrics including advanced analytics"""
    logs = load_logs(log_path)
    
    if not logs:
        return {
            'total_interactions': 0,
            'unique_participants': 0,
            'ctr': 0.0,
            'response_times': {
                'mean': 0.0,
                'median': 0.0,
                'min': 0.0,
                'max': 0.0
            },
            'scenario_stats': {},
            'attack_type_stats': {},
            'ai_vs_human': {
                'ai': {'total': 0, 'clicks': 0, 'ctr': 0.0},
                'human': {'total': 0, 'clicks': 0, 'ctr': 0.0}
            },
            'time_series': {},
            'participant_segmentation': {'high': [], 'medium': [], 'low': []},
            'attack_patterns': {},
            'advanced_analytics': {
                'time_series_available': False,
                'segmentation_available': False,
                'pattern_detection_available': False
            }
        }
    
    unique_participants = len(set(l.get('participant_id', '') for l in logs))
    
    # Calculate advanced analytics
    time_series = calculate_time_series(logs, interval='hour')
    participant_segmentation = calculate_participant_segmentation(logs)
    attack_patterns = detect_attack_patterns(logs)
    
    return {
        'total_interactions': len(logs),
        'unique_participants': unique_participants,
        'ctr': calculate_ctr(logs),
        'response_times': calculate_response_times(logs),
        'scenario_stats': calculate_scenario_stats(logs),
        'attack_type_stats': calculate_attack_type_stats(logs),
        'ai_vs_human': calculate_ai_vs_human_stats(logs),
        'time_series': time_series,
        'participant_segmentation': participant_segmentation,
        'attack_patterns': attack_patterns,
        'advanced_analytics': {
            'time_series_available': len(time_series) > 0,
            'segmentation_available': len(participant_segmentation['high']) + len(participant_segmentation['medium']) + len(participant_segmentation['low']) > 0,
            'pattern_detection_available': len(attack_patterns) > 0
        }
    }

