"""
Review Manager for Human-in-the-Loop approval system
Manages pending, approved, and rejected AI-generated messages
"""

import json
import os
from pathlib import Path
from datetime import datetime


REVIEW_QUEUE_FILE = 'review_queue.jsonl'
APPROVED_FILE = 'data/generated_samples.jsonl'
REJECTED_FILE = 'generator/rejected_outputs.jsonl'
BLOCKED_FILE = 'generator/blocked_outputs.log'


def load_blocked_outputs():
    """Load blocked outputs from log file"""
    items = []
    
    if not os.path.exists(BLOCKED_FILE):
        return items
    
    current_item = {}
    with open(BLOCKED_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('[') and 'BLOCKED' in line:
                # New blocked item
                if current_item:
                    items.append(current_item)
                current_item = {
                    'timestamp': line[1:20] if '[' in line else '',
                    'status': 'blocked',
                    'text': ''
                }
            elif line.startswith('Text:'):
                current_item['text'] = line.replace('Text:', '').strip()
            elif line.startswith('Reason:'):
                current_item['reason'] = line.replace('Reason:', '').strip()
    
    if current_item:
        items.append(current_item)
    
    return items


def load_review_queue():
    """Load items pending review"""
    items = []
    
    if os.path.exists(REVIEW_QUEUE_FILE):
        with open(REVIEW_QUEUE_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        item = json.loads(line)
                        items.append(item)
                    except json.JSONDecodeError:
                        continue
    
    # Also check blocked outputs
    blocked = load_blocked_outputs()
    for item in blocked:
        item['id'] = f"blocked_{len(items)}"
        item['flagged_keywords'] = extract_flagged_keywords(item.get('text', ''))
        items.append(item)
    
    return items


def extract_flagged_keywords(text):
    """Extract flagged keywords from text"""
    keywords = ['password', 'credentials', 'ssn', 'bank', 'credit card', 'social security']
    found = []
    text_lower = text.lower()
    for keyword in keywords:
        if keyword in text_lower:
            found.append(keyword)
    return found


def approve_message(item_id):
    """Approve a message and move it to approved samples"""
    # This would move the item from review queue to approved
    # For now, just return success
    return {'status': 'approved', 'message': 'Message approved'}


def reject_message(item_id, reason=''):
    """Reject a message and log it"""
    # Log rejection
    rejected_dir = Path(REJECTED_FILE).parent
    rejected_dir.mkdir(parents=True, exist_ok=True)
    
    with open(REJECTED_FILE, 'a', encoding='utf-8') as f:
        rejection = {
            'id': item_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'reason': reason
        }
        f.write(json.dumps(rejection, ensure_ascii=False) + '\n')
    
    return {'status': 'rejected', 'message': 'Message rejected and logged'}


def get_review_stats():
    """Get review statistics"""
    approved_count = 0
    rejected_count = 0
    pending_count = 0
    
    if os.path.exists(APPROVED_FILE):
        with open(APPROVED_FILE, 'r', encoding='utf-8') as f:
            approved_count = len([l for l in f if l.strip()])
    
    if os.path.exists(REJECTED_FILE):
        with open(REJECTED_FILE, 'r', encoding='utf-8') as f:
            rejected_count = len([l for l in f if l.strip()])
    
    pending_count = len(load_review_queue())
    
    return {
        'approved': approved_count,
        'rejected': rejected_count,
        'pending': pending_count
    }

