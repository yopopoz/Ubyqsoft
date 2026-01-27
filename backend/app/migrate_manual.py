import os
from sqlalchemy import create_engine, text

# Use the same DATABASE_URL as in the app, or default to localhost
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://app:app@localhost:5432/logistics")

def migrate():
    print(f"Connecting to database: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)
    
    new_columns = [
        ("order_number", "VARCHAR"),
        ("product_description", "VARCHAR"),
        ("supplier", "VARCHAR"),
        ("incoterm_city", "VARCHAR"),
        ("loading_place", "VARCHAR"),
        ("pod", "VARCHAR"),
        ("mad_date", "TIMESTAMP WITH TIME ZONE"),
        ("its_date", "TIMESTAMP WITH TIME ZONE"),
        ("nb_pallets", "INTEGER"),
        ("nb_cartons", "INTEGER"),
        ("vessel", "VARCHAR"),
        ("bl_number", "VARCHAR"),
        ("forwarder_ref", "VARCHAR"),
        ("pure_trade_ref", "VARCHAR"),
        ("interlocuteur", "VARCHAR"),
        ("responsable_pure_trade", "VARCHAR"),
        # Chatbot Business Fields
        ("margin_percent", "FLOAT"),
        ("budget_status", "VARCHAR DEFAULT 'ON_TRACK'"),
        ("compliance_status", "VARCHAR DEFAULT 'PENDING'"),
        ("rush_status", "BOOLEAN DEFAULT FALSE"),
        ("eco_friendly_flag", "BOOLEAN DEFAULT FALSE"),
    ]

    with engine.connect() as conn:
        print("Starting migration...")
        for col_name, col_type in new_columns:
            try:
                # 'ADD COLUMN IF NOT EXISTS' is supported in Postgres 9.6+
                query = text(f"ALTER TABLE shipments ADD COLUMN IF NOT EXISTS {col_name} {col_type};")
                conn.execute(query)
                print(f"Checked/Added column: {col_name}")
            except Exception as e:
                print(f"Error adding column {col_name}: {e}")

        # Create index properly
        title = "ix_shipments_order_number"
        try:
            # Check if index exists or just try creating it with IF NOT EXISTS
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS {title} ON shipments (order_number);"))
            print(f"Checked/Created index: {title}")
        except Exception as e:
            print(f"Error creating index {title}: {e}")
            
        conn.commit()
    
    # Create new tables using SQLAlchemy metadata
    from app.models import Base
    print("Creating new tables (Alerts, Documents, CarrierSchedules)...")
    Base.metadata.create_all(bind=engine)
    print("New tables created/verified.")
    
    print("Migration finished successfully.")

if __name__ == "__main__":
    migrate()
