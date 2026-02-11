from sqlalchemy import event
from .models import Shipment, Event, WebhookSubscription
from .database import SessionLocal
import pandas as pd
import os
import logging
import httpx
import json
import threading
from datetime import datetime

logger = logging.getLogger(__name__)

EXPORT_PATH = os.path.join(os.getcwd(), "shipments_mirror.csv")

# -------------------------------------------------------------------------
# Webhook Dispatcher Logic
# -------------------------------------------------------------------------

def send_webhook(url, payload, secret=None):
    """
    Sends a webhook payload to the specified URL in a separate thread (fire-and-forget).
    """
    def _send():
        try:
            headers = {"Content-Type": "application/json", "User-Agent": "BBOXL-Webhook/1.0"}
            if secret:
                headers["X-Hub-Signature"] = secret # simplistic signature
            
            # Using httpx for requests
            response = httpx.post(url, json=payload, headers=headers, timeout=5.0)
            logger.info(f"Webhook sent to {url} | Status: {response.status_code}")
        except Exception as e:
            logger.error(f"Webhook failed for {url}: {e}")

    thread = threading.Thread(target=_send)
    thread.start()


def dispatch_event_webhooks(mapper, connection, target):
    """
    Triggered when a new Event is inserted.
    """
    try:
        # We need to query subscriptions. Using a new session is safest.
        session = SessionLocal()
        try:
            # Get all active subscriptions
            subs = session.query(WebhookSubscription).filter(WebhookSubscription.is_active == True).all()
            
            event_type = target.type
            payload = {
                "event": "event.created",
                "type": event_type,
                "shipment_id": target.shipment_id,
                "timestamp": target.timestamp.isoformat() if target.timestamp else datetime.now().isoformat(),
                "data": target.payload
            }
            
            for sub in subs:
                # Check if subscription wants this event
                # We assume sub.events is a list of strings
                if event_type in sub.events or "*" in sub.events:
                    send_webhook(sub.url, payload, sub.secret)
                    
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error dispatching event webhooks: {e}")

def dispatch_shipment_created_webhook(mapper, connection, target):
    """
    Triggered when a new Shipment is inserted.
    """
    try:
        session = SessionLocal()
        try:
            subs = session.query(WebhookSubscription).filter(WebhookSubscription.is_active == True).all()
            
            payload = {
                "event": "shipment.created",
                "shipment_id": target.id,
                "reference": target.reference,
                "timestamp": target.created_at.isoformat() if target.created_at else datetime.now().isoformat()
            }
            
            for sub in subs:
                if "shipment.created" in sub.events or "*" in sub.events:
                    send_webhook(sub.url, payload, sub.secret)
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error dispatching shipment webhooks: {e}")


# -------------------------------------------------------------------------
# CSV Export Logic
# -------------------------------------------------------------------------

def export_shipments_to_csv_simulation(mapper, connection, target):
    """
    Observer function triggered after a Shipment is updated or inserted.
    It dumps the current state of the shipments table to a CSV file,
    simulating a write-back to the Master File.
    """
    try:
        logger.info(f"Observer: Shipment {target.reference} changed. Regenerating mirror CSV...")
        
        session = SessionLocal()
        try:
            query = session.query(Shipment)
            df = pd.read_sql(query.statement, session.bind)
            
            # Save to CSV
            df.to_csv(EXPORT_PATH, index=False, encoding='utf-8-sig')
            logger.info(f"Observer: Mirror CSV saved to {EXPORT_PATH}")
            
        except Exception as e:
            logger.error(f"Observer Error: {e}")
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Observer Safety Catch: {e}")

def setup_observers():
    # CSV Mirror
    event.listen(Shipment, 'after_update', export_shipments_to_csv_simulation)
    event.listen(Shipment, 'after_insert', export_shipments_to_csv_simulation)
    
    # Webhooks
    event.listen(Event, 'after_insert', dispatch_event_webhooks)
    event.listen(Shipment, 'after_insert', dispatch_shipment_created_webhook)
