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
    product_description = Column(String, nullable=True)
    quantity = Column(Integer, nullable=True)
    weight_kg = Column(Float, nullable=True)
    volume_cbm = Column(Float, nullable=True)
    nb_pallets = Column(Integer, nullable=True)
    nb_cartons = Column(Integer, nullable=True)
    
    # Extras
    order_number = Column(String, index=True, nullable=True) # Master: Order number
    supplier = Column(String, nullable=True)
    incoterm_city = Column(String, nullable=True)
    loading_place = Column(String, nullable=True) # POL
    pod = Column(String, nullable=True) # Port of Discharge
    
    mad_date = Column(DateTime(timezone=True), nullable=True) # Date MAD Marchandise
    its_date = Column(DateTime(timezone=True), nullable=True)
    
    vessel = Column(String, nullable=True)
    bl_number = Column(String, nullable=True)
    
    forwarder_ref = Column(String, nullable=True) # REF CLASQUIN
    pure_trade_ref = Column(String, nullable=True) # REF PURE TRADE
    
    interlocuteur = Column(String, nullable=True)
    responsable_pure_trade = Column(String, nullable=True)
    

    
    # Business Logic Fields
    margin_percent = Column(Float, nullable=True)
    budget_status = Column(String, default="ON_TRACK") # ON_TRACK, OVER_BUDGET
    compliance_status = Column(String, default="PENDING") # PENDING, CHARGED, CLEARED
    rush_status = Column(Boolean, default=False)
    eco_friendly_flag = Column(Boolean, default=False)
    
    status = Column(String, default="ORDER_INFO") # Stores last EventType
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    events = relationship("Event", back_populates="shipment", cascade="all, delete-orphan", order_by="desc(Event.timestamp)")

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False)
    type = Column(String, nullable=False) # EventType
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    payload = Column(JSON, nullable=True)
    note = Column(Text, nullable=True)
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

# Update Shipment Relationships
Shipment.alerts = relationship("Alert", back_populates="shipment")
Shipment.documents = relationship("Document", back_populates="shipment")

# Add new columns to Shipment for business logic
# Note: These lines perform mapped column injection to the existing class if it was already defined, 
# but here we are editing the file definition so we just add them to the class above.
# I will edit the Shipment class code block directly to be cleaner.

