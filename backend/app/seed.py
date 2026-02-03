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
        
        # Demo shipments generation removed per user request
        # for i in range(1, 11): ...
        
        db.commit()
        print("✅ Demo users check complete (Demo shipments disabled).")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
