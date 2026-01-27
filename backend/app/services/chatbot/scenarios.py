from sqlalchemy.orm import Session
from sqlalchemy import func
from ...models import Shipment, Event, Alert, Document, CarrierSchedule
from ..external_data import external_service
from datetime import datetime, timedelta

class ChatbotScenarios:
    def __init__(self, db: Session, user):
        self.db = db
        self.user = user

    def _filter_shipments(self):
        """Apply RBAC: Clients see only their data."""
        query = self.db.query(Shipment)
        if self.user.role == "client":
            # Assuming 'name' or specific field links to 'customer' in Shipment
            # For Phase 1 demo, we might match partially or use a specific mapping.
            # Let's assume user.name matches Shipment.customer 
            # OR we show nothing if no match.
            query = query.filter(Shipment.customer.ilike(f"%{self.user.name}%"))
        return query

    # --- CLIENT SCENARIOS ---
    
    def get_tracking(self, ref: str):
        shipment = self._filter_shipments().filter((Shipment.reference == ref) | (Shipment.order_number == ref)).first()
        if not shipment:
            return "Commande introuvable ou accès refusé."
        
        last_event = shipment.events[0] if shipment.events else None
        loc = f" ({last_event.type})" if last_event else ""
        
        msg = f"📍 Commande {shipment.reference}:\nStatut: {shipment.status}\nPosition: {shipment.loading_place} -> {shipment.pod}{loc}.\nETA: {shipment.planned_eta}"
        
        # Check alerts
        if shipment.alerts:
            msg += f"\n⚠️ ALERTE: {shipment.alerts[0].message}"
            
        return msg

    def get_documents_status(self, ref: str):
         shipment = self._filter_shipments().filter(Shipment.reference == ref).first()
         if not shipment: return "Commande introuvable."
         
         docs = shipment.documents
         if not docs:
             return "Aucun document disponible pour le moment."
         
         doc_list = ", ".join([f"{d.type}: {d.status}" for d in docs])
         return f"📄 Documents pour {ref}: {doc_list}"

    def check_quality_compliance(self, ref: str):
        shipment = self._filter_shipments().filter(Shipment.reference == ref).first()
        if not shipment: return "Commande introuvable."
        
        # Logic based on new field
        if shipment.compliance_status == "CLEARED":
            return f"✅ Conformité validée pour {ref}. Normes respectées."
        else:
             return f"⏳ Conformité en cours de validation ({shipment.compliance_status})."

    # --- LOGISTICS (INTERNAL) SCENARIOS ---

    def analyze_warehouse_volume(self, month: int):
        if self.user.role == "client": return "Accès refusé."
        
        # Count volume arriving in Month
        # This is a tough query for SQLite/Postgres without proper date func depending on dialect,
        # sticking to Python filtering for safety in this demo phase if volume is low, 
        # or use exact SQL.
        
        start_date = datetime(2025, month, 1) # hardcoded year for demo or dynamic
        end_date = start_date + timedelta(days=32)
        
        shipments = self.db.query(Shipment).filter(Shipment.planned_eta >= start_date, Shipment.planned_eta < end_date).all()
        
        total_cbm = sum(s.volume_cbm or 0 for s in shipments)
        pallets = sum(s.nb_pallets or 0 for s in shipments)
        
        return f"📦 Prévision Entrepôt (Mois {month}):\nVolume: {total_cbm:.2f} CBM\nPalettes: {pallets}\nNombre de commandes: {len(shipments)}"

    def get_global_alerts(self):
        if self.user.role == "client": return "Accès refusé."
        
        alerts = self.db.query(Alert).filter(Alert.active == True).all()
        if not alerts:
            return "✅ Aucun aléa majeur global signalé actuellement."
        
        msg = "⚠️ Aléas Actifs:\n"
        for a in alerts:
            msg += f"- [{a.type}] {a.message} (Impact: {a.impact_days}j)\n"
        return msg

    def simulate_route_risk(self, route: str):
        # External call
        risk = external_service.check_weather_alert(route)
        if risk:
            return f"⚠️ Risque détecté sur {route}: {risk['message']}"
        return f"✅ Route {route} claire. Pas de risques majeurs signalés."

    # --- SALES (INTERNAL) SCENARIOS ---
    
    def get_campaign_status(self, campaign_ref: str):
        if self.user.role == "client": return "Accès refusé."
        # Assuming campaign tracking via 'product_description' or specific tag
        # For demo, search by loose match
        shipments = self.db.query(Shipment).filter(Shipment.product_description.ilike(f"%{campaign_ref}%")).all()
        
        if not shipments: return "Aucune commande trouvée pour cette campagne."
        
        total_qty = sum(s.quantity or 0 for s in shipments)
        on_time = sum(1 for s in shipments if s.status != "DELAYED") # Simple logic
        
        return f"📊 Campagne '{campaign_ref}':\nCommandes: {len(shipments)}\nQté Totale: {total_qty}\nCommandes à l'heure: {on_time}/{len(shipments)}"

    # --- PURCHASING (INTERNAL) SCENARIOS ---

    def supplier_performance(self, supplier_name: str):
         if self.user.role == "client": return "Accès refusé."
         
         shipments = self.db.query(Shipment).filter(Shipment.supplier.ilike(f"%{supplier_name}%")).all()
         if not shipments: return "Fournisseur inconnu."
         
         # Mock scoring
         score = 95
         for s in shipments:
             if s.status == "DELAYED": score -= 5
             
         return f"🏭 Performance {supplier_name}:\nScore: {score}/100\nVolume traité: {len(shipments)} commandes."

    # =====================================================
    # LOGISTICS SCENARIOS (ADMIN/OPS ONLY) - COMPREHENSIVE
    # =====================================================

    # =====================================================
    # LOGISTICS SCENARIOS (ADMIN/OPS ONLY) - COMPREHENSIVE
    # =====================================================

    def _require_ops(self):
        """Check if user is admin or ops"""
        if self.user.role == "client":
            return False
        return True

    def _now(self):
        """Helper to get current time with timezone awareness if needed"""
        return datetime.now().astimezone()

    def list_orders_first_fortnight(self, month: int, year: int = 2025):
        """Lister les commandes de la première quinzaine {mois année}"""
        if not self._require_ops(): return "Accès refusé."
        
        # Construct timezone aware dates if possible, or leave naive if column is naive.
        # Postgres driver usually returns aware if column is TIMESTAMPTZ.
        # But filter input usually works with naive if driver handles it, UNLESS comparing naive python object with aware DB object in python logic (not SQL).
        # However, SQL Alchemy filters `column >= value` handles conversion if configured.
        # The error likely came from python side logic or specific driver behavior.
        # Let's try passing naive objects first, but if error persists, we add timezone.
        # The previous error "TypeError: can't compare offset-naive and offset-aware datetimes" happened likely in `get_delayed_orders_this_month` where we did python math or DB comparison.
        
        start_date = datetime(year, month, 1).astimezone()
        end_date = datetime(year, month, 15, 23, 59, 59).astimezone()
        
        shipments = self.db.query(Shipment).filter(
            Shipment.planned_etd >= start_date,
            Shipment.planned_etd <= end_date
        ).all()
        
        if not shipments:
            return f"Aucune commande trouvée pour la 1ère quinzaine de {month}/{year}."
        
        result = f"📋 Commandes 1ère quinzaine {month}/{year} ({len(shipments)} total):\n"
        for s in shipments[:20]:  # Limit display
            result += f"- {s.reference} | {s.customer} | ETD: {s.planned_etd.strftime('%d/%m') if s.planned_etd else 'N/A'}\n"
        if len(shipments) > 20:
            result += f"... et {len(shipments) - 20} autres."
        return result

    def list_orders_second_fortnight(self, month: int, year: int = 2025):
        """Volume commandes seconde quinzaine {mois}"""
        if not self._require_ops(): return "Accès refusé."
        
        start_date = datetime(year, month, 16).astimezone()
        # Handle end of month
        if month == 12:
            end_date = (datetime(year + 1, 1, 1) - timedelta(seconds=1)).astimezone()
        else:
            end_date = (datetime(year, month + 1, 1) - timedelta(seconds=1)).astimezone()
        
        shipments = self.db.query(Shipment).filter(
            Shipment.planned_etd >= start_date,
            Shipment.planned_etd <= end_date
        ).all()
        
        total_cbm = sum(s.volume_cbm or 0 for s in shipments)
        total_qty = sum(s.quantity or 0 for s in shipments)
        
        return f"📦 2ème quinzaine {month}/{year}:\nCommandes: {len(shipments)}\nVolume: {total_cbm:.2f} CBM\nQuantité totale: {total_qty}"

    def get_exw_to_ddp_status(self, ref: str):
        """Statut EXW → DDP pour la commande {id}"""
        if not self._require_ops(): return "Accès refusé."
        
        shipment = self.db.query(Shipment).filter(
            (Shipment.reference == ref) | (Shipment.order_number == ref)
        ).first()
        
        if not shipment:
            return f"Commande {ref} introuvable."
        
        # Build milestone chain based on events
        events = shipment.events or []
        milestones = {
            "EXW_READY": "⬜",
            "PRODUCTION_READY": "⬜",
            "LOADING_IN_PROGRESS": "⬜",
            "EXPORT_CLEARANCE": "⬜",
            "TRANSIT_OCEAN": "⬜",
            "ARRIVAL_PORT": "⬜",
            "IMPORT_CLEARANCE": "⬜",
            "FINAL_DELIVERY": "⬜"
        }
        
        for e in events:
            if "PRODUCTION" in e.type: milestones["PRODUCTION_READY"] = "✅"
            if "LOADING" in e.type: milestones["LOADING_IN_PROGRESS"] = "✅"
            if "EXPORT" in e.type: milestones["EXPORT_CLEARANCE"] = "✅"
            if "TRANSIT" in e.type: milestones["TRANSIT_OCEAN"] = "✅"
            if "ARRIVAL" in e.type: milestones["ARRIVAL_PORT"] = "✅"
            if "IMPORT" in e.type: milestones["IMPORT_CLEARANCE"] = "✅"
            if "DELIVERY" in e.type: milestones["FINAL_DELIVERY"] = "✅"
        
        result = f"🚚 Statut EXW→DDP pour {ref}:\n"
        for m, status in milestones.items():
            result += f"{status} {m.replace('_', ' ')}\n"
        return result

    def get_delayed_orders_this_month(self):
        """Commandes en retard ce mois-ci : causes transport (maritime)"""
        if not self._require_ops(): return "Accès refusé."
        
        today = self._now()
        start_of_month = datetime(today.year, today.month, 1).astimezone()
        
        # Find shipments where planned_eta < today and status not DELIVERED
        # Note: If planned_eta in DB is NULL, this filter ignores it.
        delayed = self.db.query(Shipment).filter(
            Shipment.planned_eta < today,
            Shipment.planned_eta >= start_of_month,
            Shipment.status != "FINAL_DELIVERY"
        ).all()
        
        if not delayed:
            return "✅ Aucune commande en retard ce mois-ci."
        
        result = f"⚠️ Commandes en retard ({len(delayed)}):\n"
        for s in delayed[:15]:
            # Ensure proper subtraction - if s.planned_eta is offset-aware and today is offset-aware
            eta = s.planned_eta
            if eta and eta.tzinfo is None:
                eta = eta.astimezone()
                
            delay_days = (today - eta).days if eta else 0
            result += f"- {s.reference} | Retard: {delay_days}j | Vessel: {s.vessel or 'N/A'}\n"
        return result

    def get_port_arrivals_7_days(self):
        """Arrivées port sous 7 jours"""
        if not self._require_ops(): return "Accès refusé."
        
        today = self._now()
        next_week = today + timedelta(days=7)
        
        arrivals = self.db.query(Shipment).filter(
            Shipment.planned_eta >= today,
            Shipment.planned_eta <= next_week
        ).order_by(Shipment.planned_eta).all()
        
        if not arrivals:
            return "Aucune arrivée prévue dans les 7 prochains jours."
        
        result = f"🚢 Arrivées port sous 7 jours ({len(arrivals)}):\n"
        for s in arrivals:
            eta_str = s.planned_eta.strftime('%d/%m %Hh') if s.planned_eta else 'N/A'
            result += f"- {s.reference} | POD: {s.pod} | ETA: {eta_str}\n"
        return result

    def get_pickup_planning(self):
        """Planning pick-ups EXW (commandes prêtes)"""
        if not self._require_ops(): return "Accès refusé."
        
        # Shipments with status indicating ready for pickup
        ready = self.db.query(Shipment).filter(
            Shipment.status.in_(["PRODUCTION_READY", "ORDER_INFO"])
        ).order_by(Shipment.planned_etd).all()
        
        if not ready:
            return "Aucune commande prête pour pick-up."
        
        result = f"📦 Planning Pick-ups EXW ({len(ready)} commandes):\n"
        for s in ready[:20]:
            etd_str = s.planned_etd.strftime('%d/%m') if s.planned_etd else 'N/A'
            result += f"- {s.reference} | Client: {s.customer} | ETD cible: {etd_str} | Lieu: {s.loading_place or 'N/A'}\n"
        return result

    def get_carrier_schedules(self, carrier: str = None, month: int = None):
        """Expéditions maritimes via {transporteur} pour {mois}"""
        if not self._require_ops(): return "Accès refusé."
        
        query = self.db.query(CarrierSchedule)
        if carrier:
            query = query.filter(CarrierSchedule.carrier.ilike(f"%{carrier}%"))
        if month:
            year = datetime.now().year
            start = datetime(year, month, 1)
            if month == 12:
                end = datetime(year + 1, 1, 1)
            else:
                end = datetime(year, month + 1, 1)
            query = query.filter(CarrierSchedule.etd >= start, CarrierSchedule.etd < end)
        
        schedules = query.order_by(CarrierSchedule.etd).all()
        
        if not schedules:
            return "Aucun schedule trouvé."
        
        result = f"📅 Schedules ({len(schedules)}):\n"
        for sc in schedules[:15]:
            etd_str = sc.etd.strftime('%d/%m') if sc.etd else 'N/A'
            result += f"- {sc.carrier} | {sc.pol}→{sc.pod} | ETD: {etd_str} | Transit: {sc.transit_time_days}j\n"
        return result

    def get_ddp_milestones_standard(self):
        """Milestones logistiques standard (séquence) d'une commande"""
        if not self._require_ops(): return "Accès refusé."
        
        return """📋 Séquence DDP Standard:
1️⃣ ORDER_INFO - Commande reçue
2️⃣ PRODUCTION_READY - Marchandise prête usine
3️⃣ LOADING_IN_PROGRESS - Chargement conteneur
4️⃣ CONTAINER_READY - Conteneur scellé
5️⃣ EXPORT_CLEARANCE - Dédouanement export
6️⃣ TRANSIT_OCEAN/AIR - En transit
7️⃣ ARRIVAL_PORT - Arrivée port destination
8️⃣ IMPORT_CLEARANCE - Dédouanement import
9️⃣ FINAL_DELIVERY - Livraison finale (POD)"""

    def get_customs_sequence(self):
        """Étapes douanières pour une livraison DDP maritime (séquence)"""
        if not self._require_ops(): return "Accès refusé."
        
        return """🛃 Séquence Douanes DDP Maritime:
1. Documents préparés (Invoice, Packing List, BL)
2. Déclaration Export (pays origine)
3. Certification origine si applicable
4. Déclaration Import (pays destination)
5. Inspection physique si sélectionné
6. Paiement droits et taxes
7. Mainlevée douanes
8. Enlèvement autorisé"""

    def get_tracking_for_container(self, container: str):
        """Tracking GPS d'une commande maritime spécifique"""
        if not self._require_ops(): return "Accès refusé."
        
        shipment = self.db.query(Shipment).filter(
            Shipment.container_number.ilike(f"%{container}%")
        ).first()
        
        if not shipment:
            return f"Conteneur {container} introuvable."
        
        # Simulate GPS position
        import random
        lat = random.uniform(20.0, 45.0)
        lon = random.uniform(-120.0, 120.0)
        speed = random.uniform(10, 18)
        
        return f"""🛰️ Tracking Conteneur {container}:
Commande: {shipment.reference}
Position: {lat:.4f}°N, {lon:.4f}°E
Vitesse: {speed:.1f} nœuds
Vessel: {shipment.vessel or 'N/A'}
ETA: {shipment.planned_eta}
Dernier statut: {shipment.status}"""

    def get_readiness_for_air(self):
        """Readiness commandes en attente de schedule aérien"""
        if not self._require_ops(): return "Accès refusé."
        
        # Rush orders that might need air freight
        urgent = self.db.query(Shipment).filter(
            Shipment.rush_status == True
        ).all()
        
        if not urgent:
            return "Aucune commande urgente en attente de schedule aérien."
        
        result = f"✈️ Commandes urgentes ({len(urgent)}):\n"
        for s in urgent:
            result += f"- {s.reference} | Client: {s.customer} | ETA requise: {s.planned_eta}\n"
        return result

    def export_ddp_in_transit(self):
        """Export traçabilité pour livraisons DDP en cours"""
        if not self._require_ops(): return "Accès refusé."
        
        in_transit = self.db.query(Shipment).filter(
            Shipment.status.in_(["TRANSIT_OCEAN", "TRANSIT_AIR", "LOADING_IN_PROGRESS"])
        ).all()
        
        if not in_transit:
            return "Aucune livraison DDP en transit actuellement."
        
        result = f"🚢 DDP En Transit ({len(in_transit)}):\n"
        for s in in_transit:
            result += f"- {s.reference} | {s.customer} | Container: {s.container_number or 'N/A'} | BL: {s.bl_number or 'N/A'} | ETA: {s.planned_eta}\n"
        return result

    def check_pod_completion(self, ref: str):
        """Confirmation de complétude livraison DDP (POD)"""
        if not self._require_ops(): return "Accès refusé."
        
        shipment = self.db.query(Shipment).filter(
            (Shipment.reference == ref) | (Shipment.order_number == ref)
        ).first()
        
        if not shipment:
            return f"Commande {ref} introuvable."
        
        if shipment.status == "FINAL_DELIVERY":
            # Check for POD document
            pod_doc = next((d for d in shipment.documents if d.type == "POD"), None)
            if pod_doc:
                return f"✅ Livraison {ref} complète. POD reçu: {pod_doc.filename}"
            return f"✅ Livraison {ref} marquée complète. POD en attente de scan."
        else:
            return f"⏳ Livraison {ref} non complétée. Statut actuel: {shipment.status}"

    def analyze_delay_history(self):
        """Analyse des retards sur expéditions maritimes passées"""
        if not self._require_ops(): return "Accès refusé."
        
        # Get all completed shipments
        completed = self.db.query(Shipment).filter(
            Shipment.status == "FINAL_DELIVERY"
        ).all()
        
        if not completed:
            return "Pas assez de données historiques."
        
        delays = []
        for s in completed:
            if s.planned_eta and s.mad_date:
                diff = (s.mad_date - s.planned_eta).days
                if diff > 0:
                    delays.append(diff)
        
        if not delays:
            return "✅ Aucun retard significatif enregistré sur les livraisons passées."
        
        avg_delay = sum(delays) / len(delays)
        max_delay = max(delays)
        
        return f"""📊 Analyse Retards Maritimes:
Livraisons analysées: {len(completed)}
Avec retard: {len(delays)} ({len(delays)*100/len(completed):.1f}%)
Retard moyen: {avg_delay:.1f} jours
Retard max: {max_delay} jours"""

    def get_optimal_schedule(self, carrier: str, ready_date: str):
        """Meilleur schedule maritime {transporteur} si commande prête le {date}"""
        if not self._require_ops(): return "Accès refusé."
        
        try:
            target = datetime.strptime(ready_date, "%d/%m/%Y")
        except:
            target = datetime.now()
        
        schedules = self.db.query(CarrierSchedule).filter(
            CarrierSchedule.carrier.ilike(f"%{carrier}%"),
            CarrierSchedule.etd >= target
        ).order_by(CarrierSchedule.etd).limit(5).all()
        
        if not schedules:
            return f"Aucun schedule {carrier} trouvé après {ready_date}."
        
        result = f"📅 Schedules {carrier} disponibles:\n"
        for sc in schedules:
            etd_str = sc.etd.strftime('%d/%m/%Y') if sc.etd else 'N/A'
            eta_str = sc.eta.strftime('%d/%m/%Y') if sc.eta else 'N/A'
            result += f"- ETD: {etd_str} | ETA: {eta_str} | Transit: {sc.transit_time_days}j | Vessel: {sc.vessel_name or 'TBN'}\n"
        return result

