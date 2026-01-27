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
