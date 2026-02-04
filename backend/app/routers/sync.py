from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.synchronizer import SyncService
from ..security import get_current_user
import os

router = APIRouter(
    prefix="/sync",
    tags=["sync"],
    responses={404: {"description": "Not found"}},
)

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..services.onedrive_client import OneDriveClient
from ..services.excel_import import parse_excel, execute_import, ImportMode
from ..models import SystemSetting
from ..schemas import OneDriveFile, SyncConfig, SyncResult, ImportResultError
from ..security import get_current_user, require_ops_or_admin
import json
from datetime import datetime

router = APIRouter(
    prefix="/sync",
    tags=["sync"],
    responses={404: {"description": "Not found"}},
)

@router.get("/onedrive/files", response_model=List[OneDriveFile])
async def list_onedrive_files(
    db: Session = Depends(get_db),
    current_user = Depends(require_ops_or_admin)
):
    """List Excel files from connected OneDrive"""
    client = OneDriveClient(db)
    try:
        files = await client.list_excel_files()
        return [OneDriveFile(**f) for f in files]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/onedrive/config")
def configure_sync_file(
    config: SyncConfig,
    db: Session = Depends(get_db),
    current_user = Depends(require_ops_or_admin)
):
    """Save the OneDrive file ID to sync"""
    
    def update_setting(key, val):
        s = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if not s:
            s = SystemSetting(key=key, value=json.dumps(val), is_encrypted=True)
            db.add(s)
        else:
            s.value = json.dumps(val)
            
    update_setting("ONEDRIVE_FILE_ID", config.file_id)
    update_setting("ONEDRIVE_FILE_NAME", config.file_name)
    db.commit()
    return {"status": "success"}

@router.get("/onedrive/config")
def get_sync_config(
    db: Session = Depends(get_db),
    current_user = Depends(require_ops_or_admin)
):
    """Get current sync config"""
    file_id = db.query(SystemSetting).filter(SystemSetting.key == "ONEDRIVE_FILE_ID").first()
    file_name = db.query(SystemSetting).filter(SystemSetting.key == "ONEDRIVE_FILE_NAME").first()
    last_run = db.query(SystemSetting).filter(SystemSetting.key == "SYNC_LAST_RUN").first()
    
    return {
        "file_id": json.loads(file_id.value) if file_id and file_id.value else None,
        "file_name": json.loads(file_name.value) if file_name and file_name.value else None,
        "last_run": json.loads(last_run.value) if last_run and last_run.value else None
    }

@router.post("/onedrive/run", response_model=SyncResult)
async def run_onedrive_sync(
    db: Session = Depends(get_db),
    current_user = Depends(require_ops_or_admin)
):
    """Manually trigger sync from configured OneDrive file"""
    file_id_setting = db.query(SystemSetting).filter(SystemSetting.key == "ONEDRIVE_FILE_ID").first()
    if not file_id_setting or not file_id_setting.value:
        raise HTTPException(status_code=400, detail="No sync file configured")
        
    file_id = json.loads(file_id_setting.value)
    
    client = OneDriveClient(db)
    try:
        # Download
        content = await client.download_file(file_id)
        
        # Parse & Import
        parsed_rows, _ = parse_excel(content)
        result = execute_import(parsed_rows, ImportMode.UPDATE_OR_CREATE, db)
        
        # Update last run
        s = db.query(SystemSetting).filter(SystemSetting.key == "SYNC_LAST_RUN").first()
        now_str = datetime.now().isoformat()
        if not s:
            s = SystemSetting(key="SYNC_LAST_RUN", value=json.dumps(now_str), is_encrypted=True)
            db.add(s)
        else:
            s.value = json.dumps(now_str)
        db.commit()
        
        return SyncResult(
            created=result['created'],
            updated=result['updated'],
            skipped=result['skipped'],
            errors=[ImportResultError(row=e['row'], reference=e['reference'], error=e['error']) for e in result['errors']],
            total_processed=result['total_processed']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@router.post("/onedrive/subscribe")
async def toggle_realtime(
    enable: bool,
    db: Session = Depends(get_db),
    current_user = Depends(require_ops_or_admin)
):
    """Enable or Disable Realtime Sync (Webhooks)"""
    client = OneDriveClient(db)
    
    if enable:
        # Get file ID
        file_id_setting = db.query(SystemSetting).filter(SystemSetting.key == "ONEDRIVE_FILE_ID").first()
        if not file_id_setting or not file_id_setting.value:
            raise HTTPException(status_code=400, detail="No sync file configured")
        file_id = json.loads(file_id_setting.value)
        
        try:
             # Check if already exists? Graph allows multiple, but we only store one.
             # Ideally we check expiration, but let's just create new one for simplicity in this phase
             sub = await client.create_subscription(file_id)
             return {"status": "enabled", "subscription": sub}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to enable realtime: {e}")
    else:
        # Disable logic (Not strictly required for MVP, let it expire or implement delete later)
        # For now we just return disabled status, cleaner implementation would call delete subscription API
        return {"status": "disabled", "message": "Subscription will expire automatically in < 3 days."}

@router.get("/onedrive/subscription")
def get_subscription_status(
    db: Session = Depends(get_db),
    current_user = Depends(require_ops_or_admin)
):
    """Get status of subscription"""
    client = OneDriveClient(db)
    info = client.get_subscription_info()
    return info or {"active": False}

