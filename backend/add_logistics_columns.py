
from sqlalchemy import text
from app.database import engine

def migrate():
    print("Applying Logistics API Schema Changes...")
    with engine.connect() as conn:
        try:
            # 1. Create api_logs table
            print("Creating api_logs table...")
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS api_logs (
                id SERIAL PRIMARY KEY,
                provider VARCHAR,
                endpoint VARCHAR,
                method VARCHAR,
                status_code INTEGER,
                request_payload TEXT,
                response_body TEXT,
                error_message TEXT,
                duration_ms INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """))
            
            # 2. Add columns to shipments
            print("Adding columns to shipments...")
            try:
                conn.execute(text("ALTER TABLE shipments ADD COLUMN IF NOT EXISTS carrier_scac VARCHAR;"))
                conn.execute(text("ALTER TABLE shipments ADD COLUMN IF NOT EXISTS last_sync_at TIMESTAMP WITH TIME ZONE;"))
                conn.execute(text("ALTER TABLE shipments ADD COLUMN IF NOT EXISTS sync_status VARCHAR DEFAULT 'IDLE';"))
                conn.execute(text("ALTER TABLE shipments ADD COLUMN IF NOT EXISTS next_poll_at TIMESTAMP WITH TIME ZONE;"))
            except Exception as e:
                print(f"Skipping shipment columns (may exist): {e}")

            # 3. Add columns to events
            print("Adding columns to events...")
            try:
                conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS source VARCHAR DEFAULT 'MANUAL';"))
                conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS external_id VARCHAR;"))
            except Exception as e:
                print(f"Skipping event columns (may exist): {e}")
                
            conn.commit()
            print("Migration completed successfully.")
        except Exception as e:
            print(f"Migration failed: {e}")
            conn.rollback()

if __name__ == "__main__":
    migrate()
