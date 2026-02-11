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
    
    # 1. Add column if not exists
    print("Checking for allowed_customer column...")
    try:
        # PostgreSQL syntax
        session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS allowed_customer VARCHAR;"))
        session.commit()
        print("Column 'allowed_customer' ensured.")
    except Exception as e:
        print(f"Error adding column (might be sqlite?): {e}")
        session.rollback()
        # Fallback for SQLite if needed, though config says Postgres
        try:
            session.execute(text("ALTER TABLE users ADD COLUMN allowed_customer VARCHAR;"))
            session.commit()
        except:
            session.rollback()

    # 2. Create users
    users = [
        {"email": "elodie.caille@loreal.com", "name": "CAILLE Elodie"},
        {"email": "sihame.bouizem@loreal.com", "name": "BOUIZEM Sihame"},
        {"email": "lea.midali@loreal.com", "name": "MIDALI Lea"},
    ]
    
    password = "PureTradeBbox2026!"
    hashed_pwd = get_password_hash(password)
    
    # Using L'OREAL and Lancôme to be safe
    allowed_customers_str = "L'OREAL,Lancôme" 
    
    for u in users:
        existing = session.query(User).filter(User.email == u["email"]).first()
        if existing:
            print(f"User {u['email']} already exists. Updating...")
            existing.allowed_customer = allowed_customers_str
            existing.password_hash = hashed_pwd
            existing.name = u["name"]
        else:
            print(f"Creating user {u['email']}")
            new_user = User(
                email=u["email"],
                name=u["name"],
                password_hash=hashed_pwd,
                role="client",
                allowed_customer=allowed_customers_str
            )
            session.add(new_user)
            
    session.commit()
    print("Users created/updated successfully.")
    session.close()

if __name__ == "__main__":
    main()
