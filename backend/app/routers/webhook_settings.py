from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import WebhookSubscription, EventType, User
from ..security import get_current_user
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime
import uuid

router = APIRouter(
    prefix="/settings/webhooks",
    tags=["settings"]
)

class WebhookCreate(BaseModel):
    url: HttpUrl
    events: List[str]
    is_active: bool = True

class WebhookUpdate(BaseModel):
    url: Optional[HttpUrl] = None
    events: Optional[List[str]] = None
    is_active: Optional[bool] = None

class WebhookResponse(BaseModel):
    id: int
    url: HttpUrl
    events: List[str]
    is_active: bool
    created_at: datetime
    last_triggered_at: Optional[datetime]
    secret: Optional[str]

    class Config:
        orm_mode = True

@router.get("/", response_model=List[WebhookResponse])
def get_webhooks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(WebhookSubscription).all()

@router.post("/", response_model=WebhookResponse)
def create_webhook(
    webhook: WebhookCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Generate a random secret for HMAC signing (future proofing)
    secret = str(uuid.uuid4())
    
    new_hook = WebhookSubscription(
        url=str(webhook.url),
        events=webhook.events,
        is_active=webhook.is_active,
        secret=secret
    )
    db.add(new_hook)
    db.commit()
    db.refresh(new_hook)
    return new_hook

@router.put("/{webhook_id}", response_model=WebhookResponse)
def update_webhook(
    webhook_id: int,
    webhook: WebhookUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_hook = db.query(WebhookSubscription).filter(WebhookSubscription.id == webhook_id).first()
    if not db_hook:
        raise HTTPException(status_code=404, detail="Webhook not found")
        
    if webhook.url:
        db_hook.url = str(webhook.url)
    if webhook.events is not None:
        db_hook.events = webhook.events
    if webhook.is_active is not None:
        db_hook.is_active = webhook.is_active
        
    db.commit()
    db.refresh(db_hook)
    return db_hook

@router.delete("/{webhook_id}")
def delete_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    db_hook = db.query(WebhookSubscription).filter(WebhookSubscription.id == webhook_id).first()
    if not db_hook:
        raise HTTPException(status_code=404, detail="Webhook not found")
        
    db.delete(db_hook)
    db.commit()
    return {"status": "deleted"}
