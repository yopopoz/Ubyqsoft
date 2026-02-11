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
    
    email = "a.bensaoud@pure-trade.com"
    name = "Afida BENSAOUD"
    password = "PureTradeBbox2026!"
    hashed_pwd = get_password_hash(password)
    role = "admin"
    
    existing = session.query(User).filter(User.email == email).first()
    if existing:
        print(f"User {email} already exists. Updating to admin...")
        existing.password_hash = hashed_pwd
        existing.name = name
        existing.role = role
        existing.allowed_customer = None # Ensure full access
    else:
        print(f"Creating user {email}")
        new_user = User(
            email=email,
            name=name,
            password_hash=hashed_pwd,
            role=role,
            allowed_customer=None
        )
        session.add(new_user)
            
    session.commit()
    print("Admin user created/updated successfully.")
    session.close()

if __name__ == "__main__":
    main()
