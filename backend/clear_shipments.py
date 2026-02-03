
from app.database import SessionLocal
from app import models
from sqlalchemy import text

def clear_all_shipments():
    db = SessionLocal()
    try:
        # Option 1: Delete children explicitly
        db.query(models.Event).delete()
        db.query(models.Document).delete()
        db.query(models.Alert).delete()
        db.query(models.Shipment).delete()
        
        db.commit()
        print("Cleared all shipments.")
        
    except Exception as e:
        print(f"Error clearing shipments: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clear_all_shipments()
