from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session
from .models import Shipment, Event, User
from .auth import get_password_hash

# Sample data
CUSTOMERS = ["Carrefour", "Auchan", "Leclerc", "Amazon FR", "Decathlon", "IKEA", "Leroy Merlin", "Boulanger", "Fnac", "Darty"]
ORIGINS = ["Shanghai, China", "Shenzhen, China", "Ningbo, China", "Busan, South Korea", "Tokyo, Japan", "Ho Chi Minh, Vietnam", "Bangkok, Thailand", "Mumbai, India"]
DESTINATIONS = ["Le Havre, France", "Marseille, France", "Anvers, Belgium", "Rotterdam, Netherlands", "Hamburg, Germany", "Barcelona, Spain"]
SKUS = ["ELEC-TV-55", "FURN-SOFA-3P", "TEXT-SHIRT-M", "ELEC-PHONE-X", "TOY-LEGO-500", "SPORT-BIKE-MTB", "HOME-LAMP-LED", "ELEC-LAPTOP-15"]
INCOTERMS = ["FOB", "CIF", "EXW", "DDP", "DAP"]

EVENT_TYPES = [
    "ORDER_INFO",
    "PRODUCTION_READY",
    "SEAL_NUMBER_CUTOFF",
    "CONTAINER_DEPARTURE_FACTORY",
    "TRANSIT_PORT_OF_LOADING",
    "BILL_OF_LADING_RELEASED",
    "TRANSIT_OCEAN",
    "TRANSIT_PORT_OF_DISCHARGE",
    "CUSTOMS_CLEARANCE",
    "FINAL_DELIVERY"
]

def seed_database(db: Session):
    try:
        # Check if we already have demo data
        existing = db.query(Shipment).filter(Shipment.reference.like("DEMO%")).first()
        if existing:
            return
        
        print("Seeding database with demo data...")
        
        # Create demo users
        demo_users = [
            {"email": "ops@demo.com", "name": "Ops User", "role": "ops", "password": "ops"},
            {"email": "client@demo.com", "name": "Client User", "role": "client", "password": "client"},
        ]
        
        for u in demo_users:
            existing_user = db.query(User).filter(User.email == u["email"]).first()
            if not existing_user:
                new_user = User(
                    email=u["email"],
                    name=u["name"],
                    role=u["role"],
                    password_hash=get_password_hash(u["password"])
                )
                db.add(new_user)
        
        db.commit()
        
        # Create 10 demo shipments
        for i in range(1, 11):
            ref = f"DEMO{str(i).zfill(3)}"
            
            # Random dates
            created = datetime.now() - timedelta(days=random.randint(10, 60))
            etd = created + timedelta(days=random.randint(5, 15))
            eta = etd + timedelta(days=random.randint(20, 40))
            
            # Random progress
            progress = random.randint(1, len(EVENT_TYPES))
            
            shipment = Shipment(
                reference=ref,
                customer=random.choice(CUSTOMERS),
                origin=random.choice(ORIGINS),
                destination=random.choice(DESTINATIONS),
                sku=random.choice(SKUS),
                incoterm=random.choice(INCOTERMS),
                quantity=random.randint(100, 5000),
                weight_kg=random.randint(500, 20000),
                volume_cbm=round(random.uniform(5, 50), 2),
                planned_etd=etd,
                planned_eta=eta,
                status=EVENT_TYPES[progress - 1],
                container_number=f"CONT{random.randint(100000, 999999)}" if progress > 3 else None,
                seal_number=f"SEAL{random.randint(10000, 99999)}" if progress > 2 else None,
                created_at=created
            )
            db.add(shipment)
            db.flush()
            
            # Create events
            event_time = created
            for j in range(progress):
                event_time = event_time + timedelta(hours=random.randint(12, 72))
                event = Event(
                    shipment_id=shipment.id,
                    type=EVENT_TYPES[j],
                    timestamp=event_time,
                    note=f"Auto-generated event for {ref}"
                    # critical field removed as it does not exist in the model
                )
                db.add(event)
        
        db.commit()
        print("✅ Demo data seeded successfully!")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
