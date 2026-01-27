from app.database import SessionLocal
from sqlalchemy import text

try:
    db = SessionLocal()
    result = db.execute(text("SELECT 1"))
    print("DATABASE_CONNECTION_SUCCESS")
    db.close()
except Exception as e:
    print(f"DATABASE_CONNECTION_FAILURE: {e}")
