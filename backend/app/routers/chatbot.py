from fastapi import APIRouter, Depends
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

class ChatResponse(BaseModel):
    response: str

from ..services.chatbot.engine import ChatbotEngine

@router.post("/query", response_model=ChatResponse)
def query_chatbot(request: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    engine = ChatbotEngine(db, current_user)
    response_text = engine.process(request.message)
    return {"response": response_text}
