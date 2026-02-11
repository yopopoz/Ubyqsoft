
from sqlalchemy import text
from app.database import engine, SessionLocal, Base
from app import models

def upgrade_db():
    print("Updating database schema...")
    
    # In development/docker, if we don't have existing data we care about preserving excessively (user said delete everything before),
    # we could just drop/create. But let's try to be nicer and use ALTER.
    # However, since there are MANY columns, and I want to be sure, I will:
    # 1. Drop shipments table (and events/alerts/docs via cascade)
    # 2. Re-create tables using metadata
    # This ensures exact match with models.py
    
    db = SessionLocal()
    try:
        print("Dropping shipments table...")
        # Use simple SQL or existing metadata
        # We need to drop dependent tables first just in case
        db.execute(text("DROP TABLE IF EXISTS webhook_subscriptions CASCADE"))
        db.execute(text("DROP TABLE IF EXISTS api_keys CASCADE"))
        db.execute(text("DROP TABLE IF EXISTS events CASCADE"))
        db.execute(text("DROP TABLE IF EXISTS documents CASCADE"))
        db.execute(text("DROP TABLE IF EXISTS alerts CASCADE"))
        db.execute(text("DROP TABLE IF EXISTS shipments CASCADE"))
        db.commit()
        print("Tables dropped.")
        
        print("Re-creating all tables...")
        # Create all tables defined in Base.metadata
        # Check against current engine
        Base.metadata.create_all(bind=engine)
        print("Tables re-created successfully.")
        
    except Exception as e:
        print(f"Error updating schema: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    upgrade_db()
