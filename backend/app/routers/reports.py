from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from openpyxl import Workbook
from io import BytesIO
from ..database import get_db
from ..models import Shipment, User
from ..security import require_ops_or_admin

router = APIRouter(
    prefix="/reports",
    tags=["reports"]
)

@router.get("/shipments_export")
def export_shipments(db: Session = Depends(get_db), current_user: User = Depends(require_ops_or_admin)):
    """Export shipments - Requires 'ops' or 'admin' role"""
    query = db.query(Shipment)
    
    if current_user.allowed_customer:
        query = query.filter(Shipment.customer == current_user.allowed_customer)
        
    shipments = query.all()
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Shipments"
    
    # Headers
    headers = ["ID", "Reference", "Customer", "Origin", "Destination", "Status", "ETA"]
    ws.append(headers)
    
    # Data
    for s in shipments:
        ws.append([
            s.id,
            s.reference,
            s.customer,
            s.origin,
            s.destination,
            s.status,
            s.planned_eta
        ])
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    headers = {
        'Content-Disposition': 'attachment; filename="shipments_export.xlsx"'
    }
    return StreamingResponse(output, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
