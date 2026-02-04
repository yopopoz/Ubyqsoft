"""
OneDrive Client Service
Interact with Microsoft Graph API to list and download files.
"""
import httpx
import json
import logging
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException

from ..models import SystemSetting
from ..routers.auth_microsoft import get_ms_config

logger = logging.getLogger(__name__)

GRAPH_API_URL = "https://graph.microsoft.com/v1.0"
# Default to puretrack.cloud as confirmed by user, can be moved to settings later
PUBLIC_API_URL = "https://api.puretrack.cloud" 


class OneDriveClient:
    def __init__(self, db: Session):
        self.db = db
        self.access_token = self._get_access_token()
        
    def _get_access_token(self) -> str:
        """Get access token from settings, refresh if needed (basic implementation)"""
        # Note: In a production app, we should check expiration and auto-refresh using the refresh token
        # For now, we rely on the token being valid or the user re-authenticating
        token_setting = self.db.query(SystemSetting).filter(SystemSetting.key == "MS_ACCESS_TOKEN").first()
        if not token_setting or not token_setting.value:
             # Try refreshing if we have refresh token
             refresh_token = self.db.query(SystemSetting).filter(SystemSetting.key == "MS_REFRESH_TOKEN").first()
             if refresh_token and refresh_token.value:
                 return self._refresh_token(json.loads(refresh_token.value))
             raise HTTPException(status_code=401, detail="Not authenticated with Microsoft")
             
        try:
            return json.loads(token_setting.value)
        except:
             return token_setting.value

    def _refresh_token(self, refresh_token: str) -> str:
        """Refresh auth token"""
        config = get_ms_config(self.db)
        if not config["client_id"] or not config["client_secret"]:
            raise Exception("Microsoft config missing")
            
        token_url = f"https://login.microsoftonline.com/{config['tenant_id']}/oauth2/v2.0/token"
        
        data = {
            "client_id": config["client_id"],
            "scope": "User.Read Mail.ReadWrite Calendars.ReadWrite Files.ReadWrite.All offline_access",
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "client_secret": config["client_secret"]
        }
        
        # We need synchronous call here or async context, sticking to httpx.Client for simplicity in synch context
        # But this service might be called from async route. Let's use httpx.Client for now
        with httpx.Client() as client:
            resp = client.post(token_url, data=data)
            
        if resp.status_code != 200:
             raise HTTPException(status_code=401, detail="Failed to refresh Microsoft token")
             
        tokens = resp.json()
        new_access_token = tokens.get("access_token")
        new_refresh_token = tokens.get("refresh_token")
        
        # Update DB
        self._update_setting("MS_ACCESS_TOKEN", new_access_token)
        if new_refresh_token:
            self._update_setting("MS_REFRESH_TOKEN", new_refresh_token)
        self.db.commit()
        
        return new_access_token

    def _update_setting(self, key, val):
        s = self.db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if not s:
            s = SystemSetting(key=key, value=json.dumps(val), is_encrypted=True)
            self.db.add(s)
        else:
            s.value = json.dumps(val)

    async def list_excel_files(self) -> List[Dict[str, Any]]:
        """List recent Excel files from OneDrive root and recent"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        files = []
        
        async with httpx.AsyncClient() as client:
            # 1. Search for .xlsx files (simple search)
            # Query for name ending in xlsx
            search_url = f"{GRAPH_API_URL}/me/drive/root/search(q='.xlsx')"
            resp = await client.get(search_url, headers=headers)
            
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("value", []):
                    if item.get("file") and item["name"].endswith((".xlsx", ".xls")):
                        files.append({
                            "id": item["id"],
                            "name": item["name"],
                            "path": item.get("parentReference", {}).get("path", "").replace("/drive/root:", ""),
                            "lastModified": item.get("lastModifiedDateTime")
                        })
                        
        return files[:20] # Return top 20

    async def download_file(self, file_id: str) -> bytes:
        """Download file content"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"{GRAPH_API_URL}/me/drive/items/{file_id}/content"
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, follow_redirects=True)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="Failed to download file from OneDrive")
            return resp.content

    async def create_subscription(self, file_id: str) -> Dict[str, Any]:
        """Create a subscription for the specified file"""
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        url = f"{GRAPH_API_URL}/subscriptions"
        
        # Calculate expiration time (max 3 days, safe 2 days)
        from datetime import datetime, timedelta
        expiration = (datetime.utcnow() + timedelta(days=2)).isoformat() + "Z"

        payload = {
            "changeType": "updated",
            "notificationUrl": f"{PUBLIC_API_URL}/webhooks/onedrive",
            "resource": f"/me/drive/items/{file_id}",
            "expirationDateTime": expiration,
            "clientState": "secret_state_check" # Simple security check
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 201:
                logger.error(f"Subscription failed: {resp.text}")
                raise HTTPException(status_code=resp.status_code, detail=f"Failed to create subscription: {resp.text}")
            
            data = resp.json()
            # Save subscription ID in DB
            self._update_setting("ONEDRIVE_SUBSCRIPTION_ID", data["id"])
            self._update_setting("ONEDRIVE_SUBSCRIPTION_EXPIRY", data["expirationDateTime"])
            self.db.commit()
            return data

    async def renew_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Renew existing subscription"""
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        url = f"{GRAPH_API_URL}/subscriptions/{subscription_id}"
        
        from datetime import datetime, timedelta
        expiration = (datetime.utcnow() + timedelta(days=2)).isoformat() + "Z"
        
        payload = {
            "expirationDateTime": expiration
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.patch(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="Failed to renew subscription")
                
            data = resp.json()
            self._update_setting("ONEDRIVE_SUBSCRIPTION_EXPIRY", data["expirationDateTime"])
            self.db.commit()
            return data
            
    def get_subscription_info(self) -> Dict[str, Any]:
        """Get local info about subscription"""
        sub_id = self.db.query(SystemSetting).filter(SystemSetting.key == "ONEDRIVE_SUBSCRIPTION_ID").first()
        expiry = self.db.query(SystemSetting).filter(SystemSetting.key == "ONEDRIVE_SUBSCRIPTION_EXPIRY").first()
        
        if not sub_id or not sub_id.value:
            return None
            
        return {
            "id": json.loads(sub_id.value),
            "expirationDateTime": json.loads(expiry.value) if expiry else None
        }

