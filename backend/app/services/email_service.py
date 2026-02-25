import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from .database import get_db
from .models import SystemSetting
import json

def get_smtp_config(db: Session):
    """Retrieve SMTP configuration from SystemSettings."""
    settings = db.query(SystemSetting).all()
    config = {}
    for s in settings:
        if s.key.startswith("SMTP_"):
            try:
                # Value could be stored as JSON string "smtp.office365.com" or just raw string
                config[s.key] = json.loads(s.value)
            except:
                config[s.key] = s.value
    return config

def send_email(to_email: str, subject: str, body: str, db: Session = None, is_html: bool = False):
    """Send an email using SMTP configuration from database."""
    if db is None:
        from .database import SessionLocal
        db = SessionLocal()
        
    config = get_smtp_config(db)
    
    host = config.get("SMTP_HOST")
    port = config.get("SMTP_PORT", 587)
    security = config.get("SMTP_SECURITY", "STARTTLS")
    user = config.get("SMTP_USER")
    password = config.get("SMTP_PASSWORD")
    
    if not host or not user or not password:
        raise ValueError("Configuration SMTP incomplète")
        
    try:
        port = int(port)
    except:
        port = 587

    msg = MIMEMultipart()
    msg['From'] = user
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'html' if is_html else 'plain'))

    try:
        if security == "SSL/TLS":
            server = smtplib.SMTP_SSL(host, port)
        else:
            server = smtplib.SMTP(host, port)
            if security == "STARTTLS":
                server.starttls()
                
        server.login(user, password)
        server.send_message(msg)
        server.quit()
        return True, "Email envoyé avec succès"
    except Exception as e:
        return False, str(e)
