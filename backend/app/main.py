from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base, SessionLocal
from .routers import auth, shipments, events, chatbot, reports, webhooks, sync, settings, auth_microsoft
from .models import User
from .auth import get_password_hash
from .live import manager
from .scheduler import start_scheduler
from fastapi import WebSocket, WebSocketDisconnect
from .observers import setup_observers

# Setup SQLAlchemy Event Listeners (Observers)
setup_observers()

# Create tables on startup (for Phase 1 simplicity)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Logistics Chatbot Ultimate Plus")

# Include Routers
app.include_router(auth.router)
app.include_router(shipments.router)
app.include_router(events.router)
app.include_router(chatbot.router)
app.include_router(reports.router)
app.include_router(webhooks.router)
app.include_router(sync.router)
app.include_router(settings.router)
app.include_router(auth_microsoft.router)

@app.websocket("/ws/shipments")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# CORS Configuration
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    start_scheduler()
    db = SessionLocal()
    try:
        # Create initial admin
        user = db.query(User).filter(User.email == "admin@example.com").first()
        if not user:
            print("Creating initial admin user...")
            admin = User(
                email="admin@example.com",
                password_hash=get_password_hash("ChangeMe123!"),
                role="admin",
                name="System Admin"
            )
            db.add(admin)
            db.commit()
            print("Admin user created: admin@example.com / ChangeMe123!")
        
        # Seed demo data
        from .seed import seed_database
        seed_database(db)
        
    finally:
        db.close()

@app.get("/health")
def read_health():
    return {"status": "ok"}
