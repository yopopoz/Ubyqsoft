from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import json
from sqlalchemy.orm import Session
from app import models, schemas
import logging

# Setup Logger
logger = logging.getLogger("logistics_sync")

class LogisticsProvider(ABC):
    """
    Abstract Base Class for specific carrier integrations (CMA CGM, Maersk, etc.)
    Ensures a unified interface for the Sync Service ("Quietude").
    """
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'CMA_CGM')"""
        pass
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Handshake / Auth refresh."""
        pass

    @abstractmethod
    def get_tracking_events(self, reference: str, scac: str = None) -> List[Dict]:
        """
        Fetch events for a specific container/BL.
        Returns a list of standardized event dicts.
        """
        pass

class LogisticsSyncService:
    """
    Service centralizing logistics synchronization logic.
    Handles:
    1. Provider selection based on SCAC/Forwarder
    2. API Call Logging (ApiLog)
    3. Event De-duplication
    4. Shipment Status Updates
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.providers: Dict[str, LogisticsProvider] = {}
        # self.register_provider(CmaCgmProvider()) # To be implemented
        
    def register_provider(self, provider: LogisticsProvider):
        self.providers[provider.provider_name] = provider
        
    def log_api_call(self, provider: str, endpoint: str, method: str, status: int, 
                     payload: Optional[dict] = None, response: Optional[str] = None, 
                     error: Optional[str] = None, duration_ms: int = 0):
        """Securely logs API interactions to DB."""
        try:
            log_entry = models.ApiLog(
                provider=provider,
                endpoint=endpoint,
                method=method,
                status_code=status,
                request_payload=json.dumps(payload) if payload else None,
                response_body=response[:5000] if response else None, # Truncate large responses
                error_message=error,
                duration_ms=duration_ms
            )
            self.db.add(log_entry)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to write API log: {e}")
            self.db.rollback()

    def sync_shipment(self, shipment_id: int):
        """
        Main entry point to sync a shipment.
        """
        shipment = self.db.query(models.Shipment).filter(models.Shipment.id == shipment_id).first()
        if not shipment:
            return {"status": "error", "message": "Shipment not found"}

        # 1. Identify Provider
        scac = shipment.carrier_scac
        provider = self._get_provider_by_scac(scac)
        
        if not provider:
            return {"status": "skipped", "message": f"No provider for SCAC {scac}"}

        # 2. Call API (Simulated for this implementation)
        # events = provider.get_tracking_events(shipment.container_number)
        
        # 3. Update DB
        shipment.last_sync_at = datetime.utcnow()
        shipment.sync_status = "SYNCED"
        self.db.commit()
        
        return {"status": "success", "provider": provider.provider_name}
        
    def _get_provider_by_scac(self, scac: str) -> Optional[LogisticsProvider]:
        # Simple mapping logic (to be expanded)
        if scac == "CMDU":
            return self.providers.get("CMA_CGM")
        elif scac == "MAEU":
            return self.providers.get("MAERSK")
        return None
