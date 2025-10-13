import csv
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

ALERT_FILE = "alerts.csv"
DEFORESTATION_THRESHOLD = 0.05  # 5% deforestation triggers alert

def initialize_alert_file():
    """Create alert CSV file with headers if it doesn't exist"""
    if not os.path.exists(ALERT_FILE):
        with open(ALERT_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'region', 'confidence', 'deforestation_percentage', 'alert_level'])

def log_deforestation_alert(region, confidence, bbox=None):
    """
    Log deforestation alert if confidence exceeds threshold
    """
    initialize_alert_file()
    
    if confidence < DEFORESTATION_THRESHOLD:
        return False, "No significant deforestation detected"
    
    # Determine alert level
    if confidence > 0.2:  # 20%
        alert_level = "CRITICAL"
    elif confidence > 0.1:  # 10%
        alert_level = "HIGH"
    else:
        alert_level = "MEDIUM"
    
    timestamp = datetime.utcnow().isoformat()
    deforestation_percentage = round(confidence * 100, 2)
    
    # Log to CSV
    with open(ALERT_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            timestamp, 
            region, 
            round(confidence, 4), 
            deforestation_percentage,
            alert_level
        ])
    
    print(f"🚨 DEFORESTATION ALERT: {alert_level} - {deforestation_percentage}% in region {region}")
    
    # Optional: Send email notification
    # send_email_alert(region, confidence, alert_level)
    
    return True, f"{alert_level} alert logged - {deforestation_percentage}% deforestation detected"

def send_email_alert(region, confidence, alert_level):
    """
    Optional: Send email notification for high-priority alerts
    Configure your email settings here
    """
    # Email configuration (update with your settings)
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    EMAIL_USER = "your_email@gmail.com"
    EMAIL_PASS = "your_password"
    ALERT_EMAIL = "alerts@yourorganization.com"
    
    if alert_level in ["HIGH", "CRITICAL"]:
        try:
            msg = MIMEText(f"""
            DEFORESTATION ALERT - {alert_level}
            
            Region: {region}
            Deforestation Level: {confidence*100:.2f}%
            Timestamp: {datetime.utcnow().isoformat()}
            
            Immediate investigation recommended.
            """)
            
            msg['Subject'] = f"🚨 {alert_level} Deforestation Alert"
            msg['From'] = EMAIL_USER
            msg['To'] = ALERT_EMAIL
            
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_USER, EMAIL_PASS)
                server.send_message(msg)
                
            print(f"Email alert sent for {alert_level} deforestation")
            
        except Exception as e:
            print(f"Failed to send email alert: {e}")

def get_recent_alerts(limit=10):
    """Get recent alerts for dashboard display"""
    if not os.path.exists(ALERT_FILE):
        return []
    
    alerts = []
    try:
        with open(ALERT_FILE, 'r') as f:
            reader = csv.DictReader(f)
            alerts = list(reader)
        
        # Sort by timestamp (most recent first) and limit
        alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        return alerts[:limit]
        
    except Exception as e:
        print(f"Error reading alerts: {e}")
        return []
