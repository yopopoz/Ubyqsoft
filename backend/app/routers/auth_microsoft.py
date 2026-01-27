from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import SystemSetting, User
from ..security import get_current_user
import httpx
import urllib.parse
import json

router = APIRouter(prefix="/auth/microsoft", tags=["auth"])

# These should ideally come from the database (SystemSettings)
# But for the initial redirect we need to read them.
def get_ms_config(db: Session):
    client_id = db.query(SystemSetting).filter(SystemSetting.key == "MS_CLIENT_ID").first()
    client_secret = db.query(SystemSetting).filter(SystemSetting.key == "MS_CLIENT_SECRET").first()
    tenant_id = db.query(SystemSetting).filter(SystemSetting.key == "MS_TENANT_ID").first()
    
    return {
        "client_id": json.loads(client_id.value) if client_id else None,
        "client_secret": json.loads(client_secret.value) if client_secret else None,
        "tenant_id": json.loads(tenant_id.value) if tenant_id else "common"
    }

@router.get("/login")
def login_microsoft(db: Session = Depends(get_db)):
    config = get_ms_config(db)
    if not config["client_id"]:
        raise HTTPException(status_code=400, detail="Microsoft Client ID not configured in settings")

    # Scopes for Graph API
    scopes = ["User.Read", "Mail.ReadWrite", "Calendars.ReadWrite", "Files.ReadWrite.All", "offline_access"]
    
    params = {
        "client_id": config["client_id"],
        "response_type": "code",
        "redirect_uri": "http://localhost:8000/auth/microsoft/callback",
        "response_mode": "query",
        "scope": " ".join(scopes),
        "state": "12345" # Should be random
    }
    
    url = f"https://login.microsoftonline.com/{config['tenant_id']}/oauth2/v2.0/authorize?{urllib.parse.urlencode(params)}"
    return {"url": url}

@router.get("/callback")
async def callback_microsoft(code: str, state: str, db: Session = Depends(get_db)):
    config = get_ms_config(db)
    if not config["client_id"] or not config["client_secret"]:
        raise HTTPException(status_code=400, detail="Microsoft config missing")
        
    token_url = f"https://login.microsoftonline.com/{config['tenant_id']}/oauth2/v2.0/token"
    
    data = {
        "client_id": config["client_id"],
        "scope": "User.Read Mail.ReadWrite Calendars.ReadWrite Files.ReadWrite.All offline_access",
        "code": code,
        "redirect_uri": "http://localhost:8000/auth/microsoft/callback",
        "grant_type": "authorization_code",
        "client_secret": config["client_secret"]
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(token_url, data=data)
        
    if resp.status_code != 200:
        return RedirectResponse(url="http://localhost:3000/admin/settings?error=microsoft_auth_failed")
        
    tokens = resp.json()
    
    # Save tokens to settings (or a specific user_tokens table if multi-user)
    # For this app, assuming global system admin integration
    
    # Update DB
    def update_setting(key, val):
        s = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if not s:
            s = SystemSetting(key=key, value=json.dumps(val), is_encrypted=True)
            db.add(s)
        else:
            s.value = json.dumps(val)
    
    update_setting("MS_ACCESS_TOKEN", tokens.get("access_token"))
    update_setting("MS_REFRESH_TOKEN", tokens.get("refresh_token"))
    
    db.commit()
    
    return RedirectResponse(url="http://localhost:3000/admin/settings?tab=cloud&success=true")
