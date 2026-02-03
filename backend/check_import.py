
from app.database import SessionLocal
from app import models

db = SessionLocal()
count = db.query(models.Shipment).count()
print(f"Total shipments: {count}")

if count > 0:
    first = db.query(models.Shipment).first()
    print(f"Sample: Ref={first.reference}, Origin={first.origin}, Dest={first.destination}, Forwarder={first.forwarder_name}")
    print(f"Extra: Batch={first.batch_number}, Qty={first.quantity}, IncotermCity={first.incoterm_city}")

db.close()
