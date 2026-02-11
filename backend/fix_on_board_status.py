import sys
import os

# Set up path to include app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import Shipment
from sqlalchemy import or_

def fix_on_board_status():
    session = SessionLocal()
    try:
        # Find shipments with "ON BOARD" in departure_stat OR status is "ON BOARD"
        shipments = session.query(Shipment).filter(
            or_(
                Shipment.departure_stat.ilike("%ON BOARD%"),
                Shipment.status.ilike("%ON BOARD%"),
                Shipment.status == "ON_BOARD"
            )
        ).filter(Shipment.status != "TRANSIT_OCEAN").all()

        print(f"Found {len(shipments)} shipments to update.")

        count = 0
        for s in shipments:
            if s.status != "TRANSIT_OCEAN":
                print(f"Updating {s.reference}: {s.status} -> TRANSIT_OCEAN (Departure: {s.departure_stat})")
                s.status = "TRANSIT_OCEAN"
                count += 1
        
        if count > 0:
            session.commit()
            print(f"Successfully updated {count} shipments.")
        else:
            print("No shipments needed updating.")

    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    fix_on_board_status()
