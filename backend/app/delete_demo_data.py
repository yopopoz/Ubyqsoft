
from app.database import SessionLocal
from app.models import Shipment

def delete_demo():
    db = SessionLocal()
    try:
        print("Searching for DEMO shipments to delete...")
        
        # Find shipments starting with "DEMO"
        query = db.query(Shipment).filter(Shipment.reference.like('DEMO%'))
        count = query.count()
        
        if count > 0:
            print(f"Found {count} shipments to delete.")
            # Delete them
            query.delete(synchronize_session=False)
            db.commit()
            print("Deletion complete.")
        else:
            print("No shipments found starting with 'DEMO'.")
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    delete_demo()
