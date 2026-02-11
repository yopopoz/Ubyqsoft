from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float, Enum, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from .database import Base

class EventType(str, enum.Enum):
    PRODUCTION_READY = "PRODUCTION_READY"
    LOADING_IN_PROGRESS = "LOADING_IN_PROGRESS"
    SEAL_NUMBER_CUTOFF = "SEAL_NUMBER_CUTOFF"
    EXPORT_CLEARANCE_CAMBODIA = "EXPORT_CLEARANCE_CAMBODIA"
    TRANSIT_OCEAN = "TRANSIT_OCEAN"
    ARRIVAL_PORT_NYNJ = "ARRIVAL_PORT_NYNJ"
    IMPORT_CLEARANCE_CBP = "IMPORT_CLEARANCE_CBP"
    FINAL_DELIVERY = "FINAL_DELIVERY"
    ORDER_INFO = "ORDER_INFO"
    CONTAINER_READY_FOR_DEPARTURE = "CONTAINER_READY_FOR_DEPARTURE"
    PHOTOS_CONTAINER_WEIGHT = "PHOTOS_CONTAINER_WEIGHT"
    GPS_POSITION_ETA_ETD = "GPS_POSITION_ETA_ETD"
    UNLOADING_GATE_OUT = "UNLOADING_GATE_OUT"
    CUSTOMS_STATUS_DECLARATION = "CUSTOMS_STATUS_DECLARATION"
    UNLOADING_TIME_CHECKS = "UNLOADING_TIME_CHECKS"
    LOGISTICS_DB_UPDATE = "LOGISTICS_DB_UPDATE"
    CHATBOT_QUERY = "CHATBOT_QUERY"
    REALTIME_DASHBOARD = "REALTIME_DASHBOARD"
    PROACTIVE_ALERT = "PROACTIVE_ALERT"
    REPORTING_ANALYTICS = "REPORTING_ANALYTICS"
    USERS_CLIENT = "USERS_CLIENT"
    USERS_LOGISTICS = "USERS_LOGISTICS"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String)
    role = Column(String, default="client") # client, ops, admin
    allowed_customer = Column(String, nullable=True) # If set, restrict access to this customer
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String, unique=True, index=True, nullable=False) # PO Number
    customer = Column(String, index=True)
    origin = Column(String)
    destination = Column(String)
    incoterm = Column(String, default="FOB")
    
    planned_etd = Column(DateTime(timezone=True), nullable=True)
    planned_eta = Column(DateTime(timezone=True), nullable=True)
    
    container_number = Column(String, nullable=True)
    seal_number = Column(String, nullable=True)
    
    # Goods Info
    sku = Column(String, nullable=True)
    product_description = Column(String, nullable=True) # Product description (customer)
    product_description_old = Column(String, nullable=True) # Product description (old)
    quantity = Column(Integer, nullable=True) # Qty
    
    # New Qty fields
    qty_pre_serie = Column(Integer, nullable=True)
    qty_its = Column(Integer, nullable=True)
    qty_foc = Column(Integer, nullable=True)
    qty_packing_acc = Column(Integer, nullable=True)
    qty_extra_carton = Column(Integer, nullable=True)

    weight_kg = Column(Float, nullable=True) # Total GW (kg)
    volume_cbm = Column(Float, nullable=True) # Actual volume cbm
    nb_pallets = Column(Integer, nullable=True)
    nb_cartons = Column(Integer, nullable=True)
    
    # Extras
    order_number = Column(String, index=True, nullable=True)
    batch_number = Column(String, nullable=True) # batch
    
    supplier = Column(String, nullable=True)
    supplier_contact = Column(String, nullable=True) # Contact (Supplier)
    
    incoterm_city = Column(String, nullable=True) # Selling Incoterm city
    dc_to_deliver = Column(String, nullable=True) # DC to deliver
    
    loading_place = Column(String, nullable=True) # Loading Place
    pod = Column(String, nullable=True) # POD
    
    qc_date = Column(DateTime(timezone=True), nullable=True) # QC
    
    mad_date = Column(DateTime(timezone=True), nullable=True) # MAD
    its_date = Column(DateTime(timezone=True), nullable=True) # DATE ITS
    delivery_date = Column(DateTime(timezone=True), nullable=True) # Delivery date
    
    vessel = Column(String, nullable=True)
    bl_number = Column(String, nullable=True)
    
    forwarder_ref = Column(String, nullable=True) # REF CLASQUIN
    pure_trade_ref = Column(String, nullable=True) # REF PURE TRADE
    
    interlocuteur = Column(String, nullable=True)
    forwarder_name = Column(String, nullable=True) # Forwarder
    
    responsable_pure_trade = Column(String, nullable=True)
    achat_contact = Column(String, nullable=True) # Achat contact
    
    # Transport
    transport_mode = Column(String, nullable=True) # MODE
    eto = Column(String, nullable=True) # ETO
    hs_code = Column(String, nullable=True)
    freight_rate = Column(Float, nullable=True) # Taux fret
    
    # Comments / Status
    comments_forwarder = Column(String, nullable=True)
    comments_internal = Column(Text, nullable=True) # Commentaires
    
    departure_stat = Column(String, nullable=True) # Départ
    found_stat = Column(String, nullable=True) # Trouvé
    shipment_ref_external = Column(String, nullable=True) # Shipment N°
    

    
    # Business Logic Fields
    margin_percent = Column(Float, nullable=True)
    budget_status = Column(String, default="ON_TRACK") # ON_TRACK, OVER_BUDGET
    compliance_status = Column(String, default="PENDING") # PENDING, CHARGED, CLEARED
    rush_status = Column(Boolean, default=False)
    eco_friendly_flag = Column(Boolean, default=False)
    
    status = Column(String, default="ORDER_INFO") # Stores last EventType
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # API Sync Fields
    carrier_scac = Column(String, nullable=True, index=True) # SCAC Code (e.g. CMDU, MAEU)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    sync_status = Column(String, default="IDLE") # IDLE, SYNCING, ERROR
    next_poll_at = Column(DateTime(timezone=True), nullable=True) # Respect Retry-After

    events = relationship("Event", back_populates="shipment", cascade="all, delete-orphan", order_by="desc(Event.timestamp)")

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False)
    type = Column(String, nullable=False) # EventType
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    payload = Column(JSON, nullable=True)
    note = Column(Text, nullable=True)
    
    # Event Provenance
    source = Column(String, default="MANUAL") # MANUAL, API_CMA, API_MAERSK, etc.
    external_id = Column(String, nullable=True, index=True) # External Event ID for dedup

    shipment = relationship("Shipment", back_populates="events")

class Alert(Base):
    """
    Gestion des Aléas (Risques / Disruptions) - Weather, Strikes, etc.
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False) # WEATHER, STRIKE, CUSTOMS, PORT_CONGESTION, PANDEMIC, FINANCIAL, ETC.
    severity = Column(String, default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    message = Column(Text, nullable=False)
    impact_days = Column(Integer, default=0)
    category = Column(String, default="LOGISTICS") # LOGISTICS, PURCHASING, SALES, CLIENT

    # Can be linked to a specific shipment or global (e.g. route based)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=True)
    linked_route = Column(String, nullable=True) # e.g. "ASIA-USEC"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    active = Column(Boolean, default=True)

    shipment = relationship("Shipment", back_populates="alerts")

class Document(Base):
    """
    Documents légaux et logistiques (BL, Packing List, QC Report, etc.)
    """
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False)
    type = Column(String, nullable=False) # BL, INVOICE, PACKING_LIST, QC_REPORT, CUSTOMS_DEC
    filename = Column(String, nullable=False)
    url = Column(String, nullable=False) # S3 link or local path
    status = Column(String, default="PENDING") # PENDING, VALIDATED, REJECTED
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    shipment = relationship("Shipment", back_populates="documents")

class CarrierSchedule(Base):
    """
    Schedules théoriques des transporteurs
    """
    __tablename__ = "carrier_schedules"

    id = Column(Integer, primary_key=True, index=True)
    carrier = Column(String, index=True)
    pol = Column(String, index=True)
    pod = Column(String, index=True)
    mode = Column(String, default="SEA") # SEA, AIR, RAIL
    etd = Column(DateTime(timezone=True))
    eta = Column(DateTime(timezone=True))
    transit_time_days = Column(Integer)
    vessel_name = Column(String, nullable=True)
    voyage_ref = Column(String, nullable=True)

class SystemSetting(Base):
    __tablename__ = "system_settings"

    key = Column(String, primary_key=True, index=True)
    value = Column(Text, nullable=True)
    is_encrypted = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ApiLog(Base):
    """
    Log des appels API pour le debugging et la sécurité (Quietude).
    """
    __tablename__ = "api_logs"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, index=True) # e.g. "CMA_CGM", "MAERSK", "VESSELFINDER"
    endpoint = Column(String)
    method = Column(String) # GET, POST
    status_code = Column(Integer)
    request_payload = Column(Text, nullable=True) # Redacted if necessary
    response_body = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Update Shipment Relationships
Shipment.alerts = relationship("Alert", back_populates="shipment")
Shipment.documents = relationship("Document", back_populates="shipment")

class WebhookSubscription(Base):
    """
    To register external services that want to be notified of events.
    """
    __tablename__ = "webhook_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    events = Column(JSON, nullable=False) # List of EventType strings
    secret = Column(String, nullable=True) # For HMAC signature
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    failure_count = Column(Integer, default=0)

class ApiKey(Base):
    """
    To allow external applications to access the API securely.
    """
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False) # e.g. "Zapier Integration"
    key_prefix = Column(String, nullable=False) # first 8 chars for identification
    key_hash = Column(String, nullable=False, unique=True, index=True) # Hashed full key
    scopes = Column(JSON, nullable=True) # List of permissions e.g. ["read:shipments", "write:webhooks"]
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)



