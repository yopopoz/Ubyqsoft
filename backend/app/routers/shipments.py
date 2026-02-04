from fastapi import APIRouter, Depends, HTTPException, Header, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Shipment, User
from ..schemas import Shipment as ShipmentSchema, ShipmentCreate, ImportMode, ImportPreviewResult, ImportResult, ImportPreviewRow
from ..security import get_current_user, require_ops_or_admin, require_any
from ..services.excel_import import parse_excel, validate_and_preview, execute_import
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


# --- Excel Import Endpoints ---

@router.post("/import/preview", response_model=ImportPreviewResult)
async def preview_import(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_ops_or_admin)
):
    """
    Preview Excel file before import.
    Returns parsed rows with status (new/update/error).
    Requires 'ops' or 'admin' role.
    """
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400, 
            detail="Format invalide. Seuls les fichiers .xlsx et .xls sont acceptés."
        )
    
    try:
        content = await file.read()
        parsed_rows, columns = parse_excel(content)
        preview_rows = validate_and_preview(parsed_rows, db)
        
        # Count statuses
        new_count = sum(1 for r in preview_rows if r['status'] == 'new')
        update_count = sum(1 for r in preview_rows if r['status'] == 'update')
        error_count = sum(1 for r in preview_rows if r['status'] == 'error')
        
        return ImportPreviewResult(
            rows=[ImportPreviewRow(**r) for r in preview_rows],
            columns_found=columns,
            total_rows=len(preview_rows),
            new_count=new_count,
            update_count=update_count,
            error_count=error_count
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


@router.post("/import", response_model=ImportResult)
async def import_excel(
    file: UploadFile = File(...),
    mode: ImportMode = Form(default=ImportMode.UPDATE_OR_CREATE),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_ops_or_admin)
):
    """
    Execute Excel import with specified mode.
    
    Modes:
    - create_only: Only create new shipments, skip existing references
    - update_or_create: Update if exists, create if new (default)
    
    Requires 'ops' or 'admin' role.
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Format invalide. Seuls les fichiers .xlsx et .xls sont acceptés."
        )
    
    try:
        content = await file.read()
        parsed_rows, _ = parse_excel(content)
        result = execute_import(parsed_rows, mode, db)
        
        return ImportResult(
            created=result['created'],
            updated=result['updated'],
            skipped=result['skipped'],
            errors=[{"row": e['row'], "reference": e['reference'], "error": e['error']} for e in result['errors']],
            total_processed=result['total_processed']
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

