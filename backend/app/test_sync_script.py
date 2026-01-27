from app.database import SessionLocal
from app.services.synchronizer import SyncService
import logging

from app.observers import setup_observers

logging.basicConfig(level=logging.INFO)
# Setup observers for the test
setup_observers()

def run():
    db = SessionLocal()
    try:
        service = SyncService(db)
        print("Starting sync...")
        # Since we are running inside /app, the file is ./master.xlsx
        res = service.sync_files("/app/master.xlsx", "/app/pure_trade.xlsx")
        print("Sync Result:", res)
    except Exception as e:
        print("Error:", e)
    finally:
        db.close()

if __name__ == "__main__":
    run()
