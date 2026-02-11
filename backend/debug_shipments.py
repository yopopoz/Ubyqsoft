import sys
import os

# Set up path to include app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import Shipment

def debug_shipments():
    session = SessionLocal()
    try:
        shipments = session.query(Shipment).all()
        print(f"Total Shipments: {len(shipments)}")
        print(f"{'ID':<5} {'Reference':<20} {'Status':<30} {'Departure Stat':<30}")
        print("-" * 85)
        for s in shipments:
            dep = s.departure_stat if s.departure_stat else "None"
            print(f"{s.id:<5} {s.reference:<20} {s.status:<30} {dep:<30}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    debug_shipments()
