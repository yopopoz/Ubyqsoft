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

@router.post("/master")
def sync_master_file(background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Triggers synchronization from Master Excel file.
    Example path: '/app/Master file - 19-01-2026.xlsx'
    """
    # Verify Admin or Ops role
    if current_user.role not in ["admin", "ops"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Hardcoded path for now
    master_path = "/app/master.xlsx"
    
    # Logic to find the real file if temp is gone (which I deleted...)
    # I should have kept the files or the user needs to upload them.
    # Given the previous context, the user said "Use files in BBOX L/".
    # In Docker, we need these files mounted.
    # The docker-compose mounts `./backend:/app`. 
    # So if I copy the files to `./backend/`, they will be in `/app/`.
    
    # Let's search for the file dynamically
    found_path = None
    for f in os.listdir("/app"):
        if "Master file" in f and f.endswith(".xlsx"):
            found_path = os.path.join("/app", f)
            break
            
    if not found_path:
        raise HTTPException(status_code=404, detail="Master file not found in /app")

    service = SyncService(db)
    
    try:
        result = service.sync_files(found_path)
        return {"status": "success", "details": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
