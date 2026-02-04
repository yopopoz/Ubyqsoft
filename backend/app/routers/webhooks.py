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

    db.refresh(event)

    # Broadcast
    await manager.broadcast("event_created")

    return {"status": "processed", "shipment": ref, "new_status": status}

@router.post("/onedrive")
async def onedrive_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle OneDrive/Graph API Notifications.
    Url: /api/webhooks/onedrive
    """
    # 1. Validation Token Handshake (GET/POST?)
    # Graph API sends validationToken in query string for validation
    validation_token = request.query_params.get("validationToken")
    if validation_token:
        from fastapi.responses import Response
        return Response(content=validation_token, media_type="text/plain")

    # 2. Notification Handling
    try:
        payload = await request.json()
        logger.info(f"OneDrive Webhook Payload: {payload}")
    except:
        return {"status": "ignored", "reason": "No JSON"}

    values = payload.get("value", [])
    processed = 0
    
    from ..models import SystemSetting
    import json
    
    # Check if subscription matches ours
    sub_id_setting = db.query(SystemSetting).filter(SystemSetting.key == "ONEDRIVE_SUBSCRIPTION_ID").first()
    my_sub_id = json.loads(sub_id_setting.value) if sub_id_setting and sub_id_setting.value else None
    
    if not my_sub_id:
         return {"status": "ignored", "reason": "No active subscription locally"}

    for notification in values:
        if notification.get("subscriptionId") == my_sub_id:
            # Check client state
            if notification.get("clientState") != "secret_state_check":
                logger.warning("OneDrive Webhook: Invalid client state")
                continue
                
            # Trigger Sync in Background
            # Access resource = notification['resource'] (e.g., "me/drive/items/...")
            logger.info("Triggering OneDrive Sync from Webhook")
            
            from ..services.onedrive_client import OneDriveClient
            from ..services.excel_import import parse_excel, execute_import, ImportMode
            
            # We reuse the logic from sync.py roughly
            # Ideally this should be a shared task
            try:
                # Get file ID from config
                file_id_setting = db.query(SystemSetting).filter(SystemSetting.key == "ONEDRIVE_FILE_ID").first()
                if file_id_setting:
                    file_id = json.loads(file_id_setting.value)
                    client = OneDriveClient(db)
                    content = await client.download_file(file_id)
                    parsed_rows, _ = parse_excel(content)
                    res = execute_import(parsed_rows, ImportMode.UPDATE_OR_CREATE, db)
                    logger.info(f"Auto-Sync Result: {res}")
                    processed += 1
            except Exception as e:
                logger.error(f"Auto-Sync Failed: {e}")

    return {"status": "processed", "count": processed}
