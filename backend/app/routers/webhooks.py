from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Shipment, Event
from ..live import manager
import asyncio

router = APIRouter(
    prefix="/webhooks",
    tags=["webhooks"]
)

@router.post("/carrier")
async def carrier_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Simulated Carrier Webhook.
    Payload: { "ref": "REF001", "status": "TRANSIT_OCEAN", "location": "Pacific" }
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    ref = payload.get("ref")
    status = payload.get("status")
    
    if not ref or not status:
        raise HTTPException(status_code=400, detail="Missing ref or status")

    # Find Shipment
    shipment = db.query(Shipment).filter(Shipment.reference == ref).first()
    if not shipment:
        return {"status": "ignored", "reason": "Shipment not found"}

    # Update Shipment
    shipment.status = status
    
    # Create Event
    event = Event(
        shipment_id=shipment.id,
        type=status,
        payload=payload,
        note=f"Update via Carrier Webhook. Location: {payload.get('location', 'Unknown')}"
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    # Broadcast
    await manager.broadcast("event_created")

    return {"status": "processed", "shipment": ref, "new_status": status}
