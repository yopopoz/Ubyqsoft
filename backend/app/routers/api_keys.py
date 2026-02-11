from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import ApiKey, User
from ..security import get_current_user
from ..auth import get_password_hash # We can use this for hashing keys too
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import secrets

router = APIRouter(
    prefix="/settings/api-keys",
    tags=["settings"]
)

class ApiKeyCreate(BaseModel):
    name: str
    scopes: Optional[List[str]] = []

class ApiKeyResponse(BaseModel):
    id: int
    name: str
    prefix: str
    created_at: datetime
    last_used_at: Optional[datetime]
    is_active: bool

    class Config:
        orm_mode = True

class ApiKeyCreatedResponse(ApiKeyResponse):
    key: str # The full key, returned only on creation

@router.get("/", response_model=List[ApiKeyResponse])
def get_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    keys = db.query(ApiKey).filter(ApiKey.is_active == True).all()
    # Pydantic orm_mode will map `key_prefix` to `prefix` if defined, wait, no.
    # We need to map explicitly or change pydantic model field name.
    # Let's clean up response manually or use property.
    return [
        ApiKeyResponse(
            id=k.id,
            name=k.name,
            prefix=k.key_prefix,
            created_at=k.created_at,
            last_used_at=k.last_used_at,
            is_active=k.is_active
        ) for k in keys
    ]

@router.post("/", response_model=ApiKeyCreatedResponse)
def create_api_key(
    key_data: ApiKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Generate Key
    raw_key = f"pk_live_{secrets.token_urlsafe(32)}"
    prefix = raw_key[:12] # pk_live_xxxx
    hashed_key = get_password_hash(raw_key)
    
    new_key = ApiKey(
        name=key_data.name,
        key_prefix=prefix,
        key_hash=hashed_key,
        scopes=key_data.scopes,
        created_by_user_id=current_user.id
    )
    
    db.add(new_key)
    db.commit()
    db.refresh(new_key)
    
    return ApiKeyCreatedResponse(
        id=new_key.id,
        name=new_key.name,
        prefix=new_key.key_prefix,
        created_at=new_key.created_at,
        last_used_at=new_key.last_used_at,
        is_active=new_key.is_active,
        key=raw_key
    )

@router.delete("/{key_id}")
def revoke_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
        
    # Hard delete or Soft delete? Code seems to imply soft delete (is_active), but user might want revoke.
    # Let's delete for now to keep DB clean, or just set is_active=False.
    # The frontend "Revoke" usually means disable.
    db.delete(key) # Simple delete
    db.commit()
    
    return {"status": "revoked"}
