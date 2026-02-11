"""
Script to delete all existing shipments and import new data from Excel file.
Run inside the Docker container:
    docker exec -it logistics_backend_prod python replace_shipments.py
"""
import pandas as pd
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import Shipment, Event, Alert, Document
from app.services.excel_import import COL_MAPPING, DATE_FIELDS, FLOAT_FIELDS, INT_FIELDS, _parse_date, _parse_float, _parse_int, _get_value


def build_reference(row):
    """Build reference from order_number and batch."""
    order_num = _get_value(row, 'Order number')
    # Handle both 'batch' and 'BATCH'
    batch = _get_value(row, 'BATCH')
    if batch is None:
        batch = _get_value(row, 'batch')
    
    if not order_num:
        return None
    
    if batch is not None:
        try:
            if isinstance(batch, float) and batch == int(batch):
                batch_str = str(int(batch))
            else:
                batch_str = str(batch)
        except:
            batch_str = str(batch)
        return f"{order_num}-{batch_str}"
    
    return str(order_num)


def replace_all_shipments():
    session = SessionLocal()
    try:
        # 1. Count existing shipments
        existing_count = session.query(Shipment).count()
        existing_events = session.query(Event).count()
        print(f"Found {existing_count} existing shipments and {existing_events} events.")
        
        # 2. Delete all related data first (cascade should handle but let's be explicit)
        print("Deleting all alerts...")
        session.query(Alert).delete()
        
        print("Deleting all documents...")
        session.query(Document).delete()
        
        print("Deleting all events...")
        session.query(Event).delete()
        
        print("Deleting all shipments...")
        session.query(Shipment).delete()
        session.commit()
        print(f"✓ Deleted {existing_count} shipments and {existing_events} events.")
        
        # 3. Read new Excel file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        excel_path = os.path.join(base_dir, "data", "import_source.xlsx")
        
        if not os.path.exists(excel_path):
            print(f"ERROR: Excel file not found at {excel_path}")
            return
        
        print(f"Reading Excel from: {excel_path}")
        df = pd.read_excel(excel_path)
        print(f"Found {len(df)} rows in Excel.")
        print(f"Columns: {list(df.columns)}")
        
        # 4. Import each row
        created = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Build reference
                reference = build_reference(row)
                if not reference:
                    errors.append(f"Row {index+2}: No reference (Order number missing)")
                    continue
                
                # Build shipment data
                data = {'reference': reference}
                
                for excel_col, model_field in COL_MAPPING.items():
                    value = _get_value(row, excel_col)
                    
                    if model_field in DATE_FIELDS:
                        data[model_field] = _parse_date(value)
                    elif model_field in FLOAT_FIELDS:
                        data[model_field] = _parse_float(value)
                    elif model_field in INT_FIELDS:
                        data[model_field] = _parse_int(value)
                    else:
                        data[model_field] = str(value).strip() if value is not None else None
                
                # Add origin/destination
                data['origin'] = str(_get_value(row, 'Loading Place')).strip() if _get_value(row, 'Loading Place') else None
                data['destination'] = str(_get_value(row, 'POD')).strip() if _get_value(row, 'POD') else None
                
                # Set status from Excel Status column
                raw_status = _get_value(row, 'Status')
                if raw_status:
                    data['status'] = str(raw_status).strip()
                else:
                    data['status'] = 'CREATED'
                
                data['created_at'] = datetime.now()
                
                shipment = Shipment(**data)
                session.add(shipment)
                created += 1
                print(f"  ✓ Row {index+2}: {reference} - {data.get('customer', 'N/A')}")
                
            except Exception as e:
                errors.append(f"Row {index+2}: {str(e)}")
                print(f"  ✗ Row {index+2}: ERROR - {str(e)}")
        
        session.commit()
        
        print(f"\n{'='*50}")
        print(f"IMPORT COMPLETE")
        print(f"{'='*50}")
        print(f"Created: {created}")
        print(f"Errors: {len(errors)}")
        
        if errors:
            print("\nErrors:")
            for e in errors:
                print(f"  - {e}")
        
        # Verify
        final_count = session.query(Shipment).count()
        print(f"\nTotal shipments in database: {final_count}")
        
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    replace_all_shipments()
