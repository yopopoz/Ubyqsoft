from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import SystemSetting, User
from ..security import get_current_user
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json

router = APIRouter(prefix="/settings", tags=["settings"])

class SettingUpdate(BaseModel):
    key: str
    value: Any
    is_encrypted: bool = False

class SettingResponse(BaseModel):
    key: str
    value: Any
    updated_at: str

@router.get("/", response_model=Dict[str, Any])
def get_all_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    settings = db.query(SystemSetting).all()
    result = {}
    for s in settings:
        try:
            val = json.loads(s.value)
        except:
            val = s.value
        result[s.key] = val
    return result

@router.post("/", status_code=status.HTTP_200_OK)
def update_settings(
    settings: List[SettingUpdate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    for s_update in settings:
        setting = db.query(SystemSetting).filter(SystemSetting.key == s_update.key).first()
        val_str = json.dumps(s_update.value) if isinstance(s_update.value, (dict, list, bool)) else str(s_update.value)
        
        if not setting:
            setting = SystemSetting(
                key=s_update.key,
                value=val_str,
                is_encrypted=s_update.is_encrypted
            )
            db.add(setting)
        else:
            setting.value = val_str
            setting.is_encrypted = s_update.is_encrypted
            
    db.commit()
    return {"status": "ok"}

class TestEmailRequest(BaseModel):
    to_email: str

@router.post("/test-email", status_code=status.HTTP_200_OK)
def test_email(
    request: TestEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    from ..services.email_service import send_email
    
    success, message = send_email(
        to_email=request.to_email,
        subject="Test de configuration SMTP - Logistics Chatbot",
        body="Ceci est un test pour vérifier que la configuration SMTP fonctionne correctement.",
        db=db
    )
    
    if not success:
        raise HTTPException(status_code=500, detail=message)
        
    return {"status": "ok", "message": message}
