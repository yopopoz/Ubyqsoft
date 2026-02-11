from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Event, Shipment, User
from ..schemas import Event as EventSchema, EventCreate
from ..security import get_current_user, require_ops_or_admin, require_any
from ..live import manager
import os

router = APIRouter(
    prefix="/events",
    tags=["events"]
)

API_KEY = "dev"

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=400, detail="Invalid API Key")
    return x_api_key

@router.post("/", response_model=EventSchema)
async def create_event(
    event: EventCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_ops_or_admin)
):
    """Create event - Requires 'ops' or 'admin' role"""
    # Check if shipment exists
    shipment = db.query(Shipment).filter(Shipment.id == event.shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Create Event
    db_event = Event(**event.model_dump())
    db.add(db_event)
    
    # Update Shipment Status
    shipment.status = event.type
    
    # Business Logic: Update Shipment fields based on Event Payload
    if event.payload:
        p = event.payload
        
        if event.type == "SEAL_NUMBER_CUTOFF" and "seal_number" in p:
            shipment.seal_number = p["seal_number"]
            
        elif event.type == "CONTAINER_READY_FOR_DEPARTURE" and "container_number" in p:
            shipment.container_number = p["container_number"]
            
        elif event.type == "PHOTOS_CONTAINER_WEIGHT" and "weight_kg" in p:
            try:
                shipment.weight_kg = float(p["weight_kg"])
            except:
                pass
        
        elif event.type == "GPS_POSITION_ETA_ETD" and "new_eta" in p and p["new_eta"]:
            # Update Planned ETA if changed
            try:
                from datetime import datetime
                # new_eta is 'YYYY-MM-DD' from date picker or datetime string
                # We need to be careful with parsing
                shipment.planned_eta = datetime.fromisoformat(p["new_eta"].replace('Z', '+00:00'))
            except:
                pass
                
        elif event.type == "TRANSIT_OCEAN":
            if "vessel_name" in p:
                shipment.vessel = p["vessel_name"]
            # voyage_ref could also be stored if there was a column, currently maybe just in event note?

    db.commit()
    db.refresh(db_event)
    
    # Broadcast update
    await manager.broadcast(f"event_created")
    
    return db_event

@router.get("/shipments/{shipment_id}", response_model=List[EventSchema])
def read_shipment_events(shipment_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_any)):
    """Read events - All authenticated users"""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        return []
        
    if current_user.allowed_customer:
        allowed = [c.strip() for c in current_user.allowed_customer.split(',')]
        if shipment.customer not in allowed:
            raise HTTPException(status_code=403, detail="Not authorized to view this shipment's events")

    events = db.query(Event).filter(Event.shipment_id == shipment_id).order_by(Event.timestamp.desc()).all()
    return events
