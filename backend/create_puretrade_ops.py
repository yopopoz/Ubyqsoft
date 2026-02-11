import sys
import os
from sqlalchemy import text

# Ensure backend directory is in python path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models import User
from app.auth import get_password_hash

def main():
    session = SessionLocal()
    
    users = [
        {"email": "a.vignon@pure-trade.com", "name": "Antoinette VIGNON"},
        {"email": "m.khider@pure-trade.com", "name": "Morad KHIDER"},
        {"email": "n.drame@pure-trade.com", "name": "Ngoné DRAMÉ"},
        {"email": "axu@puretradeshanghai.com", "name": "Anny XU"},
        {"email": "c.couturier@pure-trade.com", "name": "Corinne Couturier"},
        {"email": "l.dervaux@pure-trade.com", "name": "Ludivine DERVAUX"},
        {"email": "a.horeau@pure-trade.com", "name": "Antoine HOREAU"},
        {"email": "pa.fondeur@pure-trade.com", "name": "Pierre-Antoine FONDEUR"},
        {"email": "v.honore@pure-trade.com", "name": "Virginie HONORE"},
    ]
    
    password = "PureTradeBbox2026!"
    hashed_pwd = get_password_hash(password)
    
    role = "ops"
    
    for u in users:
        existing = session.query(User).filter(User.email == u["email"]).first()
        if existing:
            print(f"User {u['email']} already exists. Updating...")
            existing.password_hash = hashed_pwd
            existing.name = u["name"]
            existing.role = role
            existing.allowed_customer = None # Ensure they have full access
        else:
            print(f"Creating user {u['email']}")
            new_user = User(
                email=u["email"],
                name=u["name"],
                password_hash=hashed_pwd,
                role=role,
                allowed_customer=None
            )
            session.add(new_user)
            
    session.commit()
    print("Pure Trade OPS users created/updated successfully.")
    session.close()

if __name__ == "__main__":
    main()
