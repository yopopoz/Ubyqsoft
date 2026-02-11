from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List, Any
from datetime import datetime

# --- Auth ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    role: str = "client"
    allowed_customer: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- Events ---
class EventBase(BaseModel):
    type: str
    payload: Optional[dict] = None
    note: Optional[str] = None
    critical: bool = False
    timestamp: Optional[datetime] = None
    
    source: str = "MANUAL"
    external_id: Optional[str] = None

class EventCreate(EventBase):
    shipment_id: int

class Event(EventBase):
    id: int
    shipment_id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Shipments ---
class ShipmentBase(BaseModel):
    reference: str
    customer: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    incoterm: str = "FOB"
    planned_etd: Optional[datetime] = None
    planned_eta: Optional[datetime] = None
    container_number: Optional[str] = None
    seal_number: Optional[str] = None
    
    sku: Optional[str] = None
    product_description: Optional[str] = None
    product_description_old: Optional[str] = None
    quantity: Optional[int] = None
    
    qty_pre_serie: Optional[int] = None
    qty_its: Optional[int] = None
    qty_foc: Optional[int] = None
    qty_packing_acc: Optional[int] = None
    qty_extra_carton: Optional[int] = None

    weight_kg: Optional[float] = None
    volume_cbm: Optional[float] = None
    nb_pallets: Optional[int] = None
    nb_cartons: Optional[int] = None

    order_number: Optional[str] = None
    batch_number: Optional[str] = None
    
    supplier: Optional[str] = None
    supplier_contact: Optional[str] = None
    
    incoterm_city: Optional[str] = None
    dc_to_deliver: Optional[str] = None
    
    loading_place: Optional[str] = None
    pod: Optional[str] = None

    mad_date: Optional[datetime] = None
    its_date: Optional[datetime] = None
    qc_date: Optional[datetime] = None
    delivery_date: Optional[datetime] = None

    vessel: Optional[str] = None
    bl_number: Optional[str] = None

    forwarder_ref: Optional[str] = None
    pure_trade_ref: Optional[str] = None

    interlocuteur: Optional[str] = None
    forwarder_name: Optional[str] = None
    
    responsable_pure_trade: Optional[str] = None
    achat_contact: Optional[str] = None
    
    transport_mode: Optional[str] = None
    eto: Optional[str] = None
    hs_code: Optional[str] = None
    freight_rate: Optional[float] = None
    
    comments_forwarder: Optional[str] = None
    comments_internal: Optional[str] = None
    
    departure_stat: Optional[str] = None
    found_stat: Optional[str] = None
    shipment_ref_external: Optional[str] = None

    # API Sync Fields
    carrier_scac: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    sync_status: Optional[str] = "IDLE"
    next_poll_at: Optional[datetime] = None

class ShipmentCreate(ShipmentBase):
    pass

class Shipment(ShipmentBase):
    id: int
    status: str
    created_at: datetime
    events: List[Event] = []

    model_config = ConfigDict(from_attributes=True)


# --- Excel Import ---
from enum import Enum

class ImportMode(str, Enum):
    CREATE_ONLY = "create_only"
    UPDATE_OR_CREATE = "update_or_create"


class ImportPreviewRow(BaseModel):
    row_number: int
    reference: Optional[str] = None
    customer: Optional[str] = None
    order_number: Optional[str] = None
    planned_etd: Optional[datetime] = None
    status: str  # "new", "update", "error"
    error: Optional[str] = None


class ImportPreviewResult(BaseModel):
    rows: List[ImportPreviewRow]
    columns_found: List[str]
    total_rows: int
    new_count: int
    update_count: int
    error_count: int


class ImportResultError(BaseModel):
    row: int
    reference: Optional[str] = None
    error: str


class ImportResult(BaseModel):
    created: int
    updated: int
    skipped: int
    errors: List[ImportResultError] = []
    total_processed: int = 0

# --- OneDrive Sync ---
class OneDriveFile(BaseModel):
    id: str
    name: str
    path: str
    lastModified: str

class SyncConfig(BaseModel):
    file_id: str
    file_name: str

class SyncResult(ImportResult):
    pass

