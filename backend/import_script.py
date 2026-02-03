
import pandas as pd
import os
import sys
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models

# Mapping from Excel Header to Model Field
COL_MAPPING = {
    # Basic
    'Order number': 'order_number',
    'batch': 'batch_number',
    'Client': 'customer',
    'SKU': 'sku',
    
    # Descriptions
    'Product description (old)': 'product_description_old',
    'Product description (customer)': 'product_description',
    
    # Quantities
    'Qty': 'quantity',
    'Pré-série qty': 'qty_pre_serie',
    'ITS qty': 'qty_its',
    'FOC qty': 'qty_foc',
    'Packing Acc qty': 'qty_packing_acc',
    'Extra carton qty': 'qty_extra_carton',
    
    'Nb of cartons': 'nb_cartons',
    'Actual volume cbm': 'volume_cbm',
    'Total GW (kg)': 'weight_kg',
    'Nb of pallets': 'nb_pallets',
    
    # Partners
    'Supplier': 'supplier',
    'Contact': 'supplier_contact',
    'Pure Trade': 'pure_trade_ref',
    
    # Locations
    'Loading Place': 'loading_place', # Also mapped to origin
    'POD': 'pod', # Also mapped to destination
    'Selling Incoterm city': 'incoterm_city',
    'DC to deliver': 'dc_to_deliver',
    
    # Dates
    'QC': 'qc_date',
    'ETD': 'planned_etd',
    'ETA': 'planned_eta',
    'MAD': 'mad_date',
    'DATE ITS ': 'its_date',
    'Delivery date': 'delivery_date',
    
    # Shipping Info
    'Selling Incoterm': 'incoterm',
    'MODE': 'transport_mode',
    'VESSEL': 'vessel',
    'BL n°': 'bl_number',
    'Container nb': 'container_number',
    'Forwarder': 'forwarder_name',
    'NR BOOKING': 'forwarder_ref',
    'ETO': 'eto',
    'Shipment N°': 'shipment_ref_external',
    
    # Others
    'Comments for forwarder': 'comments_forwarder',
    'Commentaires': 'comments_internal',
    'HS code': 'hs_code',
    'Taux fret': 'freight_rate',
    'Départ': 'departure_stat',
    'Trouvé': 'found_stat',
    
    # Contacts
    'LOG contact': 'responsable_pure_trade',
    'Achat contact': 'achat_contact'
}

def run_import():
    db = SessionLocal()
    print("Starting import...")
    
    slug_file = "Extrac MF - 25LAN034 BBOX - 27012026 rev INTER part OK ABE 020226.xlsx"
    # Try current dir or parent or app dir
    possible_paths = [
        "import_data.xlsx", 
        "app/import_data.xlsx",
        slug_file,
        f"../{slug_file}"
    ]
    
    file_path = None
    for p in possible_paths:
        if os.path.exists(p):
            file_path = p
            break
            
    if not file_path:
        print("Import file not found!")
        return

    print(f"Reading {file_path}...")
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        print(f"Error reading Excel: {e}")
        return

    count = 0
    errors = 0
    
    for index, row in df.iterrows():
        try:
            # Helper to safely get value
            def val(col_name):
                if col_name not in row:
                    return None
                v = row[col_name]
                if pd.isna(v):
                    return None
                return v

            # Construct Reference: Order number - batch
            # If batch is missing, handle gracefully
            order_num = val('Order number')
            batch = val('batch')
            
            if not order_num:
                # Fallback if no order number
                ref = f"REF-{index}"
            else:
                if batch:
                    # Ensure batch is string and integer-like if possible
                    # e.g. 1.0 -> 1
                    try:
                       if isinstance(batch, float) and batch.is_integer():
                           batch_str = str(int(batch))
                       else:
                           batch_str = str(batch)
                    except:
                        batch_str = str(batch)
                    
                    ref = f"{order_num}-{batch_str}"
                else:
                    ref = str(order_num)
            
            # Helper for dates
            def get_date(col):
                v = val(col)
                if v:
                    try:
                        return pd.to_datetime(v).to_pydatetime()
                    except:
                        return None
                return None

            # Helper to get float or None
            def get_float(col):
                v = val(col)
                if v is None:
                    return None
                if isinstance(v, (int, float)):
                    return float(v)
                if isinstance(v, str):
                    v = v.strip()
                    if not v:
                        return None
                    try:
                        return float(v)
                    except:
                        return None
                return None
            
            # Helper to get int or None
            def get_int(col):
                v = val(col)
                if v is None:
                    return None
                if isinstance(v, (int, float)):
                    return int(v)
                if isinstance(v, str):
                    v = v.strip()
                    if not v:
                        return None
                    try:
                        return int(float(v)) # Handle "1.0" string
                    except:
                        return None
                return None

            shipment_data = {}
            
            # 1. Map generic columns
            for excel_col, model_field in COL_MAPPING.items():
                if 'date' in model_field or 'etd' in model_field or 'eta' in model_field or 'qc' in model_field:
                     shipment_data[model_field] = get_date(excel_col)
                elif model_field in ['weight_kg', 'volume_cbm', 'freight_rate', 'quantity', 'nb_pallets', 'nb_cartons', 
                                     'qty_pre_serie', 'qty_its', 'qty_foc', 'qty_packing_acc', 'qty_extra_carton']:
                     if model_field in ['weight_kg', 'volume_cbm', 'freight_rate']:
                         shipment_data[model_field] = get_float(excel_col)
                     else:
                         shipment_data[model_field] = get_int(excel_col)
                else:
                     shipment_data[model_field] = val(excel_col)
            
            # 2. Specific requested mappings (overrides or additions)
            # loading place corresponds a l'origine
            shipment_data['origin'] = val('Loading Place')
            
            # pod correspond à l'arrivée (destination)
            shipment_data['destination'] = val('POD')
            
            # Set mandatory / calculated fields
            shipment_data['reference'] = str(ref)
            shipment_data['created_at'] = pd.Timestamp.now().to_pydatetime()
            shipment_data['status'] = val('Status') or "CREATED"
            
            # Create object
            shipment = models.Shipment(**shipment_data)
            db.add(shipment)
            count += 1
            
        except Exception as e:
            print(f"Error row {index}: {e}")
            errors += 1
            
    try:
        db.commit()
        print(f"Import finished. Imported: {count}, Errors: {errors}")
    except Exception as e:
        print(f"Commit error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_import()
