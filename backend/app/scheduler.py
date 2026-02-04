from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import Shipment
from datetime import datetime, timezone

def check_sla_violations():
    """
    Periodic job to check for shipments past their ETA.
    """
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        late_shipments = db.query(Shipment).filter(
            Shipment.planned_eta < now,
            Shipment.status != "FINAL_DELIVERY"
        ).all()
        
        if late_shipments:
            print(f"[ALERT] Found {len(late_shipments)} late shipments!")
            for s in late_shipments:
                print(f" - Shipment {s.reference} is late. ETA was {s.planned_eta}")
        else:
            print("[INFO] No SLA violations found.")
            
    except Exception as e:
        print(f"Error in scheduler: {e}")
    finally:
        db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Check every 1 minute for demo purposes (real app: every hour)
    scheduler.add_job(check_sla_violations, 'interval', minutes=1)
    scheduler.start()
    print("Scheduler started...")
    
    # Renewal job (Check daily)
    scheduler.add_job(renew_onedrive_subscription, 'interval', days=1)

def renew_onedrive_subscription():
    """
    Check if we have an active subscription closer to expiry and renew it.
    """
    db = SessionLocal()
    try:
        from .services.onedrive_client import OneDriveClient
        from .models import SystemSetting
        import json
        
        sub_id = db.query(SystemSetting).filter(SystemSetting.key == "ONEDRIVE_SUBSCRIPTION_ID").first()
        if sub_id and sub_id.value:
            real_id = json.loads(sub_id.value)
            client = OneDriveClient(db)
            # Just blindly renew daily is safe enough (expires in 3 days)
            print(f"Renewing subscription {real_id}...")
            client.renew_subscription(real_id)
            print("Subscription renewed.")
    except Exception as e:
        print(f"Failed to renew subscription: {e}")
    finally:
        db.close()

