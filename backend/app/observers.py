from sqlalchemy import event
from .models import Shipment
from .database import SessionLocal
import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

EXPORT_PATH = os.path.join(os.getcwd(), "shipments_mirror.csv")

def export_shipments_to_csv_simulation(mapper, connection, target):
    """
    Observer function triggered after a Shipment is updated or inserted.
    It dumps the current state of the shipments table to a CSV file,
    simulating a write-back to the Master File.
    """
    # Use a separate session or connection to avoid messing with the current transaction?
    # Actually, we can just use a new SessionLocal.
    # Note: 'target' is the instance being modified.
    
    try:
        logger.info(f"Observer: Shipment {target.reference} changed. Regenerating mirror CSV...")
        
        # We need to query the DB. Since we are in an event, be careful with sessions.
        # It's safer to schedule this externally or use a dedicated session.
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
    event.listen(Shipment, 'after_update', export_shipments_to_csv_simulation)
    event.listen(Shipment, 'after_insert', export_shipments_to_csv_simulation)
