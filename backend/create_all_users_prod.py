"""
Script to create all users on the production database.
Run inside the backend container:
  docker exec -it logistics_backend_prod python create_all_users_prod.py
"""
import sys
sys.path.insert(0, '/app')

from app.database import SessionLocal
from app.models import User
from app.auth import get_password_hash

db = SessionLocal()

PASSWORD = "PureTradeBbox2026!"
hashed = get_password_hash(PASSWORD)

# ============================================================
# 1. L'OREAL Client Users
# ============================================================
loreal_users = [
    {"email": "elodie.caille@loreal.com", "name": "Elodie CAILLE", "role": "client", "allowed_customer": "L'OREAL,Lancôme"},
    {"email": "sihame.bouizem@loreal.com", "name": "Sihame BOUIZEM", "role": "client", "allowed_customer": "L'OREAL,Lancôme"},
    {"email": "lea.midali@loreal.com", "name": "Léa MIDALI", "role": "client", "allowed_customer": "L'OREAL,Lancôme"},
]

# ============================================================
# 2. Pure Trade OPS Users (full access)
# ============================================================
ops_users = [
    {"email": "m.baali@pure-trade.com", "name": "Mohamed BAALI", "role": "ops", "allowed_customer": None},
    {"email": "a.dupont@pure-trade.com", "name": "Alexandre DUPONT", "role": "ops", "allowed_customer": None},
    {"email": "s.martin@pure-trade.com", "name": "Sophie MARTIN", "role": "ops", "allowed_customer": None},
    {"email": "j.bernard@pure-trade.com", "name": "Julien BERNARD", "role": "ops", "allowed_customer": None},
    {"email": "c.rousseau@pure-trade.com", "name": "Claire ROUSSEAU", "role": "ops", "allowed_customer": None},
    {"email": "p.leroy@pure-trade.com", "name": "Pierre LEROY", "role": "ops", "allowed_customer": None},
    {"email": "n.moreau@pure-trade.com", "name": "Nadia MOREAU", "role": "ops", "allowed_customer": None},
    {"email": "t.petit@pure-trade.com", "name": "Thomas PETIT", "role": "ops", "allowed_customer": None},
    {"email": "l.garcia@pure-trade.com", "name": "Laura GARCIA", "role": "ops", "allowed_customer": None},
]

# ============================================================
# 3. Admin User
# ============================================================
admin_users = [
    {"email": "a.bensaoud@pure-trade.com", "name": "Afida BENSAOUD", "role": "admin", "allowed_customer": None},
]

all_users = loreal_users + ops_users + admin_users

created = 0
updated = 0
skipped = 0

for u in all_users:
    existing = db.query(User).filter(User.email == u["email"]).first()
    if existing:
        # Update password, role and allowed_customer
        existing.password_hash = hashed
        existing.role = u["role"]
        existing.allowed_customer = u["allowed_customer"]
        existing.name = u["name"]
        updated += 1
        print(f"  UPDATED: {u['email']} (role={u['role']})")
    else:
        new_user = User(
            email=u["email"],
            password_hash=hashed,
            name=u["name"],
            role=u["role"],
            allowed_customer=u["allowed_customer"]
        )
        db.add(new_user)
        created += 1
        print(f"  CREATED: {u['email']} (role={u['role']})")

db.commit()
db.close()

print(f"\n✅ Done! Created: {created}, Updated: {updated}")
print(f"   Password for all: {PASSWORD}")
