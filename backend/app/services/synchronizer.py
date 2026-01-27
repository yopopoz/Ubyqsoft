import pandas as pd
import logging
from sqlalchemy.orm import Session
from ..models import Shipment, Event, EventType
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class SyncService:
    def __init__(self, db: Session):
        self.db = db

    def parse_date(self, date_val):
        """
        Robust date parsing handling Excel serials, DD/MM/YYYY, YYYY-MM-DD
        """
        if pd.isna(date_val) or date_val == "" or str(date_val).strip() == "" or str(date_val).strip() == "#N/A":
            return None
        
        # If it's already a datetime object (common with openpyxl engine)
        if isinstance(date_val, datetime):
            # logger.info(f"Checking date year: {date_val.year}")
            if date_val.year < 2000 or date_val.year > 2100:
                print(f"DEBUG: Date {date_val} out of range (year {date_val.year}), ignored.")
                return None
            return date_val

        try:
            # Pandas to_datetime is very powerful
            # dayfirst=True to prefer DD/MM/YYYY
            dt = pd.to_datetime(date_val, dayfirst=True, errors='coerce')
            if pd.isna(dt):
                return None
            
            # Sanity check
            if dt.year < 2000 or dt.year > 2100:
                logger.warning(f"Date {dt} out of range, ignored.")
                return None
            
            return dt.to_pydatetime()
        except Exception as e:
            logger.warning(f"Date parse error for {date_val}: {e}")
            return None

    def sync_files(self, master_path: str, pure_trade_path: str = None):
        """
        Syncs Master file (and optionally Pure Trade file) to DB.
        """
        if not os.path.exists(master_path):
            raise FileNotFoundError(f"Master file not found: {master_path}")

        # 1. Load Master File
        df_master = pd.read_excel(master_path, engine="openpyxl")
        
        shipments_processed = 0
        shipments_created = 0
        shipments_updated = 0

        # Mapping: Model Field -> CSV/Excel Column Name (approximate based on analysis)
        # Note: Adjust column names to match EXACTLY what pandas reads (stripped)
        
        df_master.columns = [str(c).strip() for c in df_master.columns]
        
        # Deduplicate by Order number, keeping the last entry (assuming it's the most recent or relevant)
        if "Order number" in df_master.columns:
            logger.info("Deduplicating Master File based on 'Order number'...")
            # Normalize column to ensure duplicates are caught (whitespace, type)
            df_master["Order number"] = df_master["Order number"].astype(str).str.strip()
            # Replace 'nan' string with actual None or filter them out
            df_master = df_master[df_master["Order number"] != "nan"]
            
            initial_count = len(df_master)
            df_master = df_master.drop_duplicates(subset=["Order number"], keep="last")
            df_master = df_master.drop_duplicates(subset=["Order number"], keep="last")
            logger.info(f"Removed {initial_count - len(df_master)} duplicates.")

        # 2. OPTIONAL: Load Pure Trade File and Merge
        if pure_trade_path and os.path.exists(pure_trade_path):
            try:
                logger.info(f"Merging with Pure Trade file: {pure_trade_path}")
                # Load all sheets to check names, or just try
                xl = pd.ExcelFile(pure_trade_path, engine="openpyxl")
                # Default to first sheet
                sheet_to_use = xl.sheet_names[0]
                
                # Try to find 'ON BOARD' ignoring whitespace
                for s in xl.sheet_names:
                    if "ON BOARD" in s.upper():
                         sheet_to_use = s
                         break
                
                logger.info(f"Using sheet: '{sheet_to_use}'")
                df_pure = pd.read_excel(pure_trade_path, engine="openpyxl", sheet_name=sheet_to_use)
                df_pure.columns = [str(c).strip() for c in df_pure.columns]
                
                # Normalize Join Key 'REF'
                if "REF" in df_pure.columns:
                    df_pure["REF"] = df_pure["REF"].astype(str).str.strip()
                    # Drop duplicates in Pure Trade too?
                    df_pure = df_pure.drop_duplicates(subset=["REF"], keep="last")
                    
                    # Merge: Left join on Master (Order number) = Pure (REF)
                    # We only want to enrich Master data
                    df_master = pd.merge(
                        df_master, 
                        df_pure[["REF", "INTERLOCUTEUR", "RESPONSABLE DE COMPTE PURE TRADE", "NBR DE PALETTE"]], 
                        left_on="Order number", 
                        right_on="REF", 
                        how="left"
                    )
                    logger.info(f"Merged Pure Trade data. Columns now: {df_master.columns.tolist()}")
            except Exception as e:
                logger.warning(f"Failed to merge Pure Trade file: {e}")

        for _, row in df_master.iterrows():
            order_number = row.get("Order number")
            if not order_number or pd.isna(order_number):
                continue

            # Convert to string to be safe
            order_ref = str(order_number).strip()

            # --- Extract fields ---
            shipment_data = {
                "reference": order_ref,
                "customer": row.get("Client"),
                "sku": row.get("SKU"),
                "product_description": row.get("Product description (customer)"),
                "quantity": self._safe_int(row.get("Qty")),
                "supplier": row.get("Supplier"),
                "incoterm": row.get("Selling Incoterm"),
                "incoterm_city": row.get("Selling Incoterm city"),
                "loading_place": row.get("Loading Place"),
                "planned_etd": self.parse_date(row.get("ETD")),
                "planned_eta": self.parse_date(row.get("ETA")),
                "mad_date": self.parse_date(row.get("MAD")),
                "nb_cartons": self._safe_int(row.get("Nb of cartons")),
                "volume_cbm": self._safe_float(row.get("Actual volume cbm")),
                "weight_kg": self._safe_float(row.get("Total GW (kg)")),
                "vessel": row.get("VESSEL"),
                "pod": row.get("POD"),
                "forwarder_ref": str(row.get("Shipment N°") or row.get("NR BOOKING") or "") if not pd.isna(row.get("Shipment N°") or row.get("NR BOOKING")) else None,
                "its_date": self.parse_date(row.get("DATE ITS")),
                "bl_number": str(row.get("BL n°")) if not pd.isna(row.get("BL n°")) else None,
                "container_number": str(row.get("Container nb")) if not pd.isna(row.get("Container nb")) else None,
                
                # Merged from Pure Trade
                "pure_trade_ref": str(row.get("REF")) if not pd.isna(row.get("REF")) else None,
                "interlocuteur": row.get("INTERLOCUTEUR"),
                "responsable_pure_trade": row.get("RESPONSABLE DE COMPTE PURE TRADE"),
                "nb_pallets": self._safe_int(row.get("NBR DE PALETTE"))
            }
            
            # --- Check Existing ---
            shipment = self.db.query(Shipment).filter(Shipment.reference == order_ref).first()
            
            try:
                with self.db.begin_nested():
                    if shipment:
                        # Update logic
                        changed = self._update_model(shipment, shipment_data)
                        if changed:
                            self.db.flush()
                            shipments_updated += 1
                    else:
                        # Create logic
                        new_shipment = Shipment(**shipment_data)
                        self.db.add(new_shipment)
                        self.db.flush() # Force SQL execution to catch error
                        shipments_created += 1
            except Exception as e:
                logger.error(f"Error processing shipment {order_ref}: {e}")
                logger.error(f"Data: {shipment_data}")
                # No need to manual rollback, begin_nested handles it on exception
                continue # Skip bad row
            
            shipments_processed += 1

        self.db.commit()
        return {
            "processed": shipments_processed,
            "created": shipments_created,
            "updated": shipments_updated
        }

    def _safe_int(self, val):
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return None

    def _safe_float(self, val):
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    def _update_model(self, model_instance, data):
        changed = False
        for key, value in data.items():
            current_value = getattr(model_instance, key)
            # Naive comparison, can be improved for dates
            if current_value != value:
                # Handle nuances like None vs "" or float precision
                if value is None and current_value is None:
                    continue
                setattr(model_instance, key, value)
                changed = True
        return changed
