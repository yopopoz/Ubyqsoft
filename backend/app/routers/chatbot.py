from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..database import get_db
from ..models import Shipment, User
from ..security import get_current_user

router = APIRouter(
    prefix="/chatbot",
    tags=["chatbot"]
)

class ChatRequest(BaseModel):
    message: str

# ChatResponse model is no longer used for the main query but kept for reference if needed
class ChatResponse(BaseModel):
    response: str

from ..services.chatbot.engine import ChatbotEngine

@router.post("/query")
def query_chatbot(request: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    engine = ChatbotEngine(db, current_user)
    
    return StreamingResponse(
        engine.process_stream(request.message), 
        media_type="text/plain"
    )
