"""
Email Service for sending simulated phishing emails via SMTP
Uses MailHog in test environment
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv('SMTP_HOST', 'localhost')
SMTP_PORT = int(os.getenv('SMTP_PORT', 1025))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')


def send_phishing_email(to_email, subject, body, from_email=None, from_name="Test Sender"):
    """
    Send a simulated phishing email via SMTP
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body (HTML or plain text)
        from_email: Sender email (defaults to test@test-environment.local)
        from_name: Sender name
    
    Returns:
        dict: {'status': 'sent'|'error', 'message': str}
    """
    if not from_email:
        from_email = 'test@test-environment.local'
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = formataddr((from_name, from_email))
        msg['To'] = to_email
        
        # Add body
        text_part = MIMEText(body, 'plain')
        html_part = MIMEText(body.replace('\n', '<br>'), 'html')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Connect to SMTP server
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            # If authentication is required
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            
            # Send email
            server.send_message(msg)
        
        return {
            'status': 'sent',
            'message': f'Email sent successfully to {to_email}',
            'smtp_host': SMTP_HOST,
            'smtp_port': SMTP_PORT
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Failed to send email: {str(e)}',
            'error': str(e)
        }


def send_scenario_email(to_email, scenario_id, scenario_text):
    """
    Send a scenario email to a participant
    
    Args:
        to_email: Recipient email
        scenario_id: Scenario identifier
        scenario_text: Scenario text content
    
    Returns:
        dict: Send result
    """
    subject = f"Test Email - Scenario {scenario_id} [TEST ENVIRONMENT]"
    body = scenario_text
    
    return send_phishing_email(
        to_email=to_email,
        subject=subject,
        body=body,
        from_email='test@test-environment.local',
        from_name='Test Environment'
    )


def test_smtp_connection():
    """Test SMTP connection"""
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.noop()
        return {
            'status': 'connected',
            'host': SMTP_HOST,
            'port': SMTP_PORT,
            'message': 'SMTP connection successful'
        }
    except Exception as e:
        return {
            'status': 'error',
            'host': SMTP_HOST,
            'port': SMTP_PORT,
            'message': f'SMTP connection failed: {str(e)}'
        }

