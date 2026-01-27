
import pandas as pd
import sys
import os
from datetime import datetime, timedelta

# Ensure we can import app modules
sys.path.append(os.getcwd())

from app.database import SessionLocal, engine
from app.models import Base, Shipment, Event, EventType

def parse_date(date_val):
    if pd.isna(date_val):
        return None
    if isinstance(date_val, datetime):
        return date_val
    try:
        return pd.to_datetime(date_val)
    except:
        return None

def clean_float(val):
    if pd.isna(val):
        return None
    try:
        return float(val)
    except:
        return None

def clean_int(val):
    if pd.isna(val):
        return None
    try:
        return int(val)
    except:
        return None

def clean_str(val):
    if pd.isna(val) or str(val).strip() == "":
        return None
    return str(val).strip()

def import_data():
    session = SessionLocal()
    try:
        print("Starting data import...")
        
        # 1. Clear existing data
        print("Clearing existing shipments and events...")
        session.query(Event).delete()
        session.query(Shipment).delete()
        session.commit()
        
        # 2. Read Excel
        # Use relative path compatible with Docker container structure
        # Assuming script is run from /app or project root
        base_dir = os.path.dirname(os.path.abspath(__file__))
        excel_path = os.path.join(base_dir, "data", "import_source.xlsx")
        
        if not os.path.exists(excel_path):
             # Fallback for local run if needed/different CWD
             excel_path = os.path.join(os.getcwd(), "data", "import_source.xlsx")

        print(f"Reading Excel from: {excel_path}")
        df = pd.read_excel(excel_path)
        
        print(f"Found {len(df)} rows in Excel.")
        
        seen_refs = set()
        for index, row in df.iterrows():
            base_ref = clean_str(row.get("Order number"))
            if not base_ref:
                print(f"Skipping row {index}: No Order number")
                continue
            
            # Handle Duplicates
            ref = base_ref
            count = 1
            while ref in seen_refs:
                count += 1
                ref = f"{base_ref}-{count}"
            seen_refs.add(ref)
            
            print(f"Processing row {index}: Ref '{ref}' (Original: {base_ref})")
                
            shipment = Shipment(
                reference=ref,
                order_number=base_ref,
                customer=clean_str(row.get("Client")),
                sku=clean_str(row.get("SKU")),
                product_description=clean_str(row.get("Product description (customer)")),
                quantity=clean_int(row.get("Qty")),
                supplier=clean_str(row.get("Supplier")),
                incoterm=clean_str(row.get("Selling Incoterm")),
                incoterm_city=clean_str(row.get("Selling Incoterm city")),
                loading_place=clean_str(row.get("Loading Place")),
                planned_etd=parse_date(row.get("ETD")),
                planned_eta=parse_date(row.get("ETA")),
                mad_date=parse_date(row.get("MAD")),
                nb_cartons=clean_int(row.get("Nb of cartons")),
                volume_cbm=clean_float(row.get("Actual volume cbm")),
                weight_kg=clean_float(row.get("Total GW (kg)")),
                nb_pallets=clean_int(row.get("Nb of pallets")),
                vessel=clean_str(row.get("VESSEL")),
                pod=clean_str(row.get("POD")),
                forwarder_ref=clean_str(row.get("Forwarder")), # Storing Forwarder Name as Ref
                pure_trade_ref=clean_str(row.get("Pure Trade")),
                its_date=parse_date(row.get("DATE ITS ")),
                bl_number=clean_str(row.get("BL n°")),
                container_number=clean_str(row.get("Container nb")),
                interlocuteur=clean_str(row.get("LOG contact"))
            )
            
            # Status Mapping
            raw_status = clean_str(row.get("Status"))
            status = EventType.ORDER_INFO # Default
            
            if raw_status:
                if "Prod" in raw_status:
                    status = EventType.PRODUCTION_READY
                elif "Transit" in raw_status or "Sea" in str(row.get("MODE", "")):
                    status = EventType.TRANSIT_OCEAN
            
            shipment.status = status
            session.add(shipment)
            session.flush() # Get ID
            
            # Create Events
            # 1. ORDER_INFO (Created at somewhat arbitrary time, using MAD - 30 days or ETD - 30 days)
            base_date = shipment.mad_date or shipment.planned_etd
            if base_date:
                session.add(Event(
                    shipment_id=shipment.id,
                    type=EventType.ORDER_INFO,
                    timestamp=base_date - timedelta(days=30),
                    note="Imported from Excel"
                ))

            # 2. PRODUCTION_READY (at MAD date)
            if shipment.mad_date:
                 session.add(Event(
                    shipment_id=shipment.id,
                    type=EventType.PRODUCTION_READY,
                    timestamp=shipment.mad_date,
                    note="MAD Date"
                ))
            
            # 3. TRANSIT_OCEAN (at ETD)
            if shipment.planned_etd:
                 session.add(Event(
                    shipment_id=shipment.id,
                    type=EventType.TRANSIT_OCEAN,
                    timestamp=shipment.planned_etd,
                    note="ETD Date"
                ))

            # Set status event
            # If current status is one of the above, ensure we have an event for it if not already covered
            # (Simplification: The above logic covers the main milestones)

        session.commit()
        print("Import completed successfully!")
        
    except Exception as e:
        print(f"Error importing data: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    import_data()
