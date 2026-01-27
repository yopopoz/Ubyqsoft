from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Shipment, User
from ..schemas import Shipment as ShipmentSchema, ShipmentCreate
from ..security import get_current_user, require_ops_or_admin, require_any
import os

router = APIRouter(
    prefix="/shipments",
    tags=["shipments"]
)

API_KEY_NAME = "X-API-Key"
API_KEY = "dev"

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=400, detail="Invalid API Key")
    return x_api_key

@router.post("/", response_model=ShipmentSchema)
def create_shipment(
    shipment: ShipmentCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_ops_or_admin)
):
    """Create shipment - Requires 'ops' or 'admin' role"""
    db_shipment = Shipment(**shipment.model_dump())
    db.add(db_shipment)
    db.commit()
    db.refresh(db_shipment)
    return db_shipment

@router.get("/", response_model=List[ShipmentSchema])
def read_shipments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(require_any)):
    """Read shipments - All authenticated users (client, ops, admin)"""
    shipments = db.query(Shipment).offset(skip).limit(limit).all()
    return shipments

@router.get("/{shipment_id}", response_model=ShipmentSchema)
def read_shipment(shipment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if shipment is None:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment
