from app.database import SessionLocal, engine
from app.models import Base, User, Shipment, Event, EventType
from app.auth import get_password_hash
from datetime import datetime, timedelta
import random

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

def seed():
    db = SessionLocal()
    try:
        print("Seeding data...")

        # 1. Create Users
        users = [
            {"email": "admin@example.com", "password": "admin", "role": "admin", "name": "Admin User"},
            {"email": "ops@demo.com", "password": "ops", "role": "ops", "name": "Operations Manager"},
            {"email": "client@demo.com", "password": "client", "role": "client", "name": "Client Account"},
        ]

        for u in users:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if not existing:
                user = User(
                    email=u["email"],
                    password_hash=get_password_hash(u["password"]),
                    role=u["role"],
                    name=u["name"]
                )
                db.add(user)
                print(f"Created user: {u['email']}")
        
        db.commit()

        # 2. Create Shipments if none exist
        if db.query(Shipment).count() == 0:
            print("Creating sample shipments...")
            customers = ["Carrefour", "Decathlon", "Leroy Merlin", "Auchan", "Fnac"]
            origins = ["Shanghai, CN", "Shenzhen, CN", "Ho Chi Minh, VN", "Ningbo, CN"]
            destinations = ["Le Havre, FR", "Marseille, FR", "Anvers, BE"]
            incoterms = ["FOB", "FOB", "CIF", "DDP"]

            for i in range(17):
                ref = f"PO-{2024001 + i}"
                etd = datetime.now() - timedelta(days=random.randint(10, 60))
                eta = etd + timedelta(days=45)
                
                status_list = [
                    EventType.ORDER_INFO,
                    EventType.PRODUCTION_READY,
                    EventType.LOADING_IN_PROGRESS,
                    EventType.TRANSIT_OCEAN,
                    EventType.TRANSIT_OCEAN,
                    EventType.ARRIVAL_PORT_NYNJ, # Using existing enum but mapped to FR ports logically
                    EventType.FINAL_DELIVERY
                ]
                
                # Random progress
                current_step = random.randint(0, len(status_list) - 1)
                final_status = status_list[current_step]
                
                if current_step < 3:
                     # Not yet departed
                     actual_etd = None
                else:
                     actual_etd = etd

                s = Shipment(
                    reference=ref,
                    customer=random.choice(customers),
                    origin=random.choice(origins),
                    destination=random.choice(destinations),
                    incoterm=random.choice(incoterms),
                    planned_etd=etd,
                    planned_eta=eta,
                    quantity=random.randint(1000, 50000),
                    sku=f"SKU-{random.randint(100,999)}",
                    weight_kg=random.randint(500, 20000),
                    status=final_status,
                    vessel=f"EVER {['GIVEN', 'GREEN', 'GLORY', 'GIANT'][random.randint(0,3)]}",
                    container_number=f"CNTR{random.randint(100000,999999)}"
                )
                db.add(s)
                db.commit()
                db.refresh(s)

                # Create Events for this shipment up to current step
                for step in range(current_step + 1):
                    evt_type = status_list[step]
                    evt_time = etd + timedelta(days=step * 5)
                    
                    e = Event(
                        shipment_id=s.id,
                        type=evt_type,
                        timestamp=evt_time,
                        note=f"Automatic event: {evt_type}"
                    )
                    db.add(e)
                
                print(f"Created shipment {ref} with status {final_status}")
            
            db.commit()
        else:
            print("Shipments already exist, skipping.")

    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
