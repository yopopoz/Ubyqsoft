"""
Excel Import Service
Handles parsing, validation, and import of Excel files for shipments.
"""
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from sqlalchemy.orm import Session
from io import BytesIO
from datetime import datetime

from ..models import Shipment


class ImportMode(str, Enum):
    CREATE_ONLY = "create_only"
    UPDATE_OR_CREATE = "update_or_create"


# Mapping from Excel Header to Model Field (from import_script.py)
COL_MAPPING = {
    # Basic
    'Order number': 'order_number',
    'batch': 'batch_number',
    'BATCH': 'batch_number',
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
    'Loading Place': 'loading_place',
    'POD': 'pod',
    'Selling Incoterm city': 'incoterm_city',
    'DC to deliver': 'dc_to_deliver',
    
    # Dates
    'QC': 'qc_date',
    'ETD': 'planned_etd',
    'ETA': 'planned_eta',
    'MAD': 'mad_date',
    'DATE ITS ': 'its_date',
    'DATE ITS': 'its_date',
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
    'Status': 'excel_status',
    
    # Contacts
    'LOG contact': 'responsable_pure_trade',
    'Achat contact': 'achat_contact'
}

# Fields that should be parsed as dates
DATE_FIELDS = {'qc_date', 'planned_etd', 'planned_eta', 'mad_date', 'its_date', 'delivery_date'}

# Fields that should be parsed as floats
FLOAT_FIELDS = {'weight_kg', 'volume_cbm', 'freight_rate'}

# Fields that should be parsed as integers
INT_FIELDS = {'quantity', 'nb_pallets', 'nb_cartons', 'qty_pre_serie', 'qty_its', 'qty_foc', 'qty_packing_acc', 'qty_extra_carton'}


def _get_value(row: pd.Series, col_name: str) -> Any:
    """Safely get value from row, return None if NaN or missing."""
    if col_name not in row.index:
        return None
    v = row[col_name]
    if pd.isna(v):
        return None
    return v


def _parse_date(value: Any) -> Optional[datetime]:
    """Parse a value as datetime."""
    if value is None:
        return None
    try:
        return pd.to_datetime(value).to_pydatetime()
    except:
        return None


def _parse_float(value: Any) -> Optional[float]:
    """Parse a value as float."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            return float(value)
        except:
            return None
    return None


def _parse_int(value: Any) -> Optional[int]:
    """Parse a value as integer."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            return int(float(value))
        except:
            return None
    return None


def _build_reference(row: pd.Series) -> str:
    """Build reference from order_number and batch."""
    order_num = _get_value(row, 'Order number')
    batch = _get_value(row, 'batch')
    
    if not order_num:
        return None
    
    if batch:
        try:
            if isinstance(batch, float) and batch.is_integer():
                batch_str = str(int(batch))
            else:
                batch_str = str(batch)
        except:
            batch_str = str(batch)
        return f"{order_num}-{batch_str}"
    
    return str(order_num)


def parse_excel(file_content: bytes) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Parse Excel file and return list of row data with parsed values.
    
    Returns:
        Tuple of (parsed_rows, columns_found)
    """
    try:
        df = pd.read_excel(BytesIO(file_content))
    except Exception as e:
        raise ValueError(f"Erreur lecture Excel: {str(e)}")
    
    parsed_rows = []
    
    for index, row in df.iterrows():
        row_data = {
            'row_number': index + 2,  # +2 because Excel is 1-indexed and has header
            'data': {},
            'reference': None,
            'error': None
        }
        
        try:
            # Build reference
            reference = _build_reference(row)
            if not reference:
                row_data['error'] = "Référence manquante (Order number requis)"
                parsed_rows.append(row_data)
                continue
            
            row_data['reference'] = reference
            row_data['data']['reference'] = reference
            
            # Map columns
            for excel_col, model_field in COL_MAPPING.items():
                value = _get_value(row, excel_col)
                
                if model_field in DATE_FIELDS:
                    row_data['data'][model_field] = _parse_date(value)
                elif model_field in FLOAT_FIELDS:
                    row_data['data'][model_field] = _parse_float(value)
                elif model_field in INT_FIELDS:
                    row_data['data'][model_field] = _parse_int(value)
                else:
                    row_data['data'][model_field] = str(value) if value is not None else None
            
            # Add origin/destination from loading_place/pod
            row_data['data']['origin'] = _get_value(row, 'Loading Place')
            row_data['data']['destination'] = _get_value(row, 'POD')

            # --- Status Inference Logic ---
            excel_status_val = row_data['data'].get('excel_status')
            dep_stat = row_data['data'].get('departure_stat')
            
            inferred_status = None
            
            # 1. Primary check on new 'Status' column
            if excel_status_val and isinstance(excel_status_val, str):
                s = excel_status_val.upper().strip()
                if "ON BOARD" in s:
                    inferred_status = "TRANSIT_OCEAN"
                elif "READY" in s:
                    inferred_status = "CONTAINER_READY_FOR_DEPARTURE"
                elif "PROD" in s:
                    inferred_status = "PRODUCTION_READY"
                elif "DELIVERED" in s:
                    inferred_status = "FINAL_DELIVERY"
            
            # 2. Fallback check on 'Départ' if not found
            if not inferred_status and dep_stat and isinstance(dep_stat, str):
                s = dep_stat.upper().strip()
                if "ON BOARD" in s or "TRANSIT" in s:
                    inferred_status = "TRANSIT_OCEAN"
            
            # 3. Last fallback: Check delivery_date
            if not inferred_status and row_data['data'].get('delivery_date'):
                inferred_status = "FINAL_DELIVERY"
                
            if inferred_status:
                row_data['data']['status'] = inferred_status
            
        except Exception as e:
            row_data['error'] = f"Erreur parsing: {str(e)}"
        
        parsed_rows.append(row_data)
    
    return parsed_rows, list(df.columns)


def validate_and_preview(
    parsed_rows: List[Dict[str, Any]], 
    db: Session
) -> List[Dict[str, Any]]:
    """
    Validate rows and check for existing references.
    Key Logic matches execute_import: Order + Batch.
    """
    # Map existing shipments by (order_number, batch_number)
    existing_shipments_map = {}
    all_shipments = db.query(Shipment).all()
    
    for s in all_shipments:
        order_key = str(s.order_number).strip() if s.order_number else None
        batch_key = _normalize_batch(s.batch_number)
        
        if order_key:
             existing_shipments_map[(order_key, batch_key)] = True
    
    preview_rows = []
    
    for row in parsed_rows:
        row_order = row.get('data', {}).get('order_number')
        row_batch = row.get('data', {}).get('batch_number')
        
        lookup_order = str(row_order).strip() if row_order else None
        lookup_batch = _normalize_batch(row_batch)
        lookup_key = (lookup_order, lookup_batch)
        
        exists = False
        if lookup_order:
             exists = lookup_key in existing_shipments_map
        
        preview_row = {
            'row_number': row['row_number'],
            'reference': row.get('reference'),
            'customer': row.get('data', {}).get('customer'),
            'order_number': row.get('data', {}).get('order_number'),
            'planned_etd': row.get('data', {}).get('planned_etd'),
            'status': 'error' if row.get('error') else ('update' if exists else 'new'),
            'error': row.get('error')
        }
        preview_rows.append(preview_row)
    
    return preview_rows


def _normalize_batch(batch_val: Any) -> Optional[str]:
    """Normalize batch value to string, handling float integers."""
    if batch_val is None:
        return None
    try:
        if isinstance(batch_val, float) and batch_val.is_integer():
            return str(int(batch_val))
        return str(batch_val).strip()
    except:
        return str(batch_val).strip()

def execute_import(
    parsed_rows: List[Dict[str, Any]],
    mode: ImportMode,
    db: Session
) -> Dict[str, Any]:
    """
    Execute the import with the given mode.
    Key Logic: Update existing by (Order number + Batch), Create otherwise.
    """
    created = 0
    updated = 0
    skipped = 0
    errors = []
    
    # Map existing shipments by (order_number, batch_number)
    # Be careful: batch_number in DB might be None, empty string, or various formats.
    # We normalize to string if possible for matching.
    existing_shipments_map = {}
    
    all_shipments = db.query(Shipment).all()
    for s in all_shipments:
        order_key = str(s.order_number).strip() if s.order_number else None
        batch_key = _normalize_batch(s.batch_number)
        
        if order_key:
             # Use a tuple key: (order, batch)
             # Note: If batch is None, key is (order, None)
             existing_shipments_map[(order_key, batch_key)] = s
    
    # Track processed in this batch to handle duplicates within the file itself
    # If file has 2 rows for same shipment, second one should UPDATE the first one (which might be new)
    
    for row in parsed_rows:
        if row.get('error'):
            errors.append({
                'row': row['row_number'],
                'reference': row.get('reference'),
                'error': row['error']
            })
            continue
        
        # Get identifying info from ROW data
        row_order = row['data'].get('order_number')
        row_batch = row['data'].get('batch_number')
        
        # Validate critical fields
        if not row_order:
             errors.append({
                'row': row['row_number'],
                'reference': None,
                'error': 'Order number manquant (requis pour identification)'
            })
             continue

        # Normalize keys for lookup
        lookup_order = str(row_order).strip()
        lookup_batch = _normalize_batch(row_batch)
        lookup_key = (lookup_order, lookup_batch)
        
        try:
            # 1. Check if shipment exists (in DB or created in this session)
            existing = existing_shipments_map.get(lookup_key)
            
            if existing:
                # UPDATE MODE
                if mode == ImportMode.CREATE_ONLY:
                    skipped += 1
                    continue

                old_status = existing.status
                new_status = row['data'].get('status')
                
                # Update fields
                data = row['data'].copy()
                data.pop('reference', None)  # Don't update reference, keep original
                data.pop('excel_status', None) # Temporary extraction field, don't store it in DB directly
                
                for key, value in data.items():
                    if value is not None and hasattr(existing, key):
                        setattr(existing, key, value)
                
                # Alert Logic
                if new_status == "TRANSIT_OCEAN" and old_status != "TRANSIT_OCEAN":
                    # Close "LOADING" alerts
                    for alert in existing.alerts:
                        if alert.active and "LOADING" in alert.type:
                             alert.active = False
                    
                    # Create DELAY alert check
                    if existing.planned_eta and existing.planned_eta.date() < datetime.now().date():
                        from ..models import Alert
                        new_alert = Alert(
                            shipment_id=existing.id,
                            type="DELAY",
                            severity="HIGH",
                            message=f"Expédition en transit mais ETA dépassée ({existing.planned_eta.strftime('%d/%m/%Y')})",
                            active=True
                        )
                        db.add(new_alert)

                updated += 1
                
            else:
                # CREATE MODE
                data = row['data'].copy()
                
                # Ensure reference is set (computed)
                reference = row.get('reference')
                if not reference:
                     # Fallback if parsing didn't set it (shouldn't happen strictly)
                     reference = f"{lookup_order}-{lookup_batch}" if lookup_batch else lookup_order
                
                data['reference'] = reference
                data.pop('excel_status', None) # Don't store this in DB schema
                
                if 'status' not in data:
                     data['status'] = 'CREATED'
                
                data['created_at'] = datetime.now()
                
                shipment = Shipment(**data)
                db.add(shipment)
                db.flush()  # Get ID and make available
                
                # Add to map so subsequent rows update it
                existing_shipments_map[lookup_key] = shipment
                created += 1
                
        except Exception as e:
            errors.append({
                'row': row['row_number'],
                'reference': row.get('reference'),
                'error': str(e)
            })
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise ValueError(f"Erreur commit: {str(e)}")
    
    return {
        'created': created,
        'updated': updated,
        'skipped': skipped,
        'errors': errors,
        'total_processed': created + updated + skipped + len(errors)
    }
