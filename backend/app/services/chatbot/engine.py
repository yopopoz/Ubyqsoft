import re
from datetime import datetime
from .scenarios import ChatbotScenarios

class ChatbotEngine:
    def __init__(self, db, user):
        self.scenarios = ChatbotScenarios(db, user)
        self.user = user

    def _extract_entities(self, msg: str):
        """Extract key entities from user message"""
        entities = {}
        
        # Extract REF (e.g. 25DOG007, REF123)
        ref_match = re.search(r'\b(2[0-9][A-Z]{3}[0-9]{3}|REF\w+)\b', msg)
        entities['ref'] = ref_match.group(0) if ref_match else None
        
        # Extract Month (janvier, février, etc. or numbers)
        month_map = {
            'JANVIER': 1, 'FEVRIER': 2, 'FÉVRIER': 2, 'MARS': 3, 'AVRIL': 4,
            'MAI': 5, 'JUIN': 6, 'JUILLET': 7, 'AOUT': 8, 'AOÛT': 8,
            'SEPTEMBRE': 9, 'OCTOBRE': 10, 'NOVEMBRE': 11, 'DECEMBRE': 12, 'DÉCEMBRE': 12
        }
        for m_name, m_num in month_map.items():
            if m_name in msg:
                entities['month'] = m_num
                break
        if 'month' not in entities:
            month_num = re.search(r'\b(0?[1-9]|1[0-2])\b', msg)
            if month_num:
                entities['month'] = int(month_num.group(0))
        
        # Extract Container
        container_match = re.search(r'\b([A-Z]{4}[0-9]{7})\b', msg)
        entities['container'] = container_match.group(0) if container_match else None
        
        # Extract Carrier name (after "via" or "transporteur")
        carrier_match = re.search(r'(?:VIA|TRANSPORTEUR)\s+(\w+)', msg)
        entities['carrier'] = carrier_match.group(1) if carrier_match else None
        
        # Extract Date (dd/mm/yyyy or dd/mm)
        date_match = re.search(r'\b(\d{1,2}/\d{1,2}(?:/\d{4})?)\b', msg)
        entities['date'] = date_match.group(0) if date_match else None
        
        return entities

    def process(self, message: str):
        msg = message.upper()
        entities = self._extract_entities(msg)
        ref = entities.get('ref')
        month = entities.get('month', datetime.now().month)
        container = entities.get('container')
        carrier = entities.get('carrier')
        date_str = entities.get('date')
        
        # =====================================================
        # INTENT CLASSIFICATION (Keyword Rules)
        # =====================================================
        
        # --- TRACKING ---
        if any(x in msg for x in ["OU EST", "OÙ EST", "POSITION", "STATUT COMMANDE", "TRACKING", "SUIVI", "WHERE IS"]):
            if ref:
                return self.scenarios.get_tracking(ref)
            return "Merci de préciser la référence de la commande (ex: 25DOG007)."

        # --- EXW TO DDP STATUS ---
        if any(x in msg for x in ["EXW", "DDP", "STATUT EXW", "JALONS"]):
            if ref:
                return self.scenarios.get_exw_to_ddp_status(ref)
            return "Précisez la référence pour voir le statut EXW→DDP."

        # --- FIRST FORTNIGHT ---
        if any(x in msg for x in ["PREMIERE QUINZAINE", "PREMIÈRE QUINZAINE", "1ERE QUINZAINE", "1ÈRE QUINZAINE"]):
            return self.scenarios.list_orders_first_fortnight(month)

        # --- SECOND FORTNIGHT ---
        if any(x in msg for x in ["SECONDE QUINZAINE", "2EME QUINZAINE", "2ÈME QUINZAINE", "DEUXIEME QUINZAINE"]):
            return self.scenarios.list_orders_second_fortnight(month)

        # --- DELAYS ---
        if any(x in msg for x in ["RETARD", "EN RETARD", "DELAYED", "RETARDS"]):
            return self.scenarios.get_delayed_orders_this_month()

        # --- PORT ARRIVALS ---
        if any(x in msg for x in ["ARRIVEE PORT", "ARRIVÉES PORT", "ARRIVALS", "SOUS 7 JOURS", "7 JOURS"]):
            return self.scenarios.get_port_arrivals_7_days()

        # --- PICKUP PLANNING ---
        if any(x in msg for x in ["PICK-UP", "PICKUP", "ENLÈVEMENT", "PRÊTES POUR"]):
            return self.scenarios.get_pickup_planning()

        # --- CARRIER SCHEDULES ---
        if any(x in msg for x in ["SCHEDULE", "SCHEDULES", "HORAIRES", "MARITIME VIA"]):
            return self.scenarios.get_carrier_schedules(carrier, month)

        # --- OPTIMAL SCHEDULE ---
        if any(x in msg for x in ["MEILLEUR SCHEDULE", "SCHEDULE OPTIMAL", "PRÊTE LE"]):
            if carrier and date_str:
                return self.scenarios.get_optimal_schedule(carrier, date_str)
            return "Précisez le transporteur et la date (ex: 'Meilleur schedule CMA CGM si prête le 15/02/2025')."

        # --- DDP MILESTONES ---
        if any(x in msg for x in ["MILESTONES", "SÉQUENCE DDP", "ETAPES DDP", "ÉTAPES DDP", "SEQUENCE STANDARD"]):
            return self.scenarios.get_ddp_milestones_standard()

        # --- CUSTOMS SEQUENCE ---
        if any(x in msg for x in ["DOUANE", "DOUANES", "CUSTOMS", "DÉDOUANEMENT"]):
            return self.scenarios.get_customs_sequence()

        # --- CONTAINER TRACKING ---
        if any(x in msg for x in ["CONTENEUR", "CONTAINER", "GPS"]):
            if container:
                return self.scenarios.get_tracking_for_container(container)
            if ref:
                # Try to find container from ref
                return self.scenarios.get_tracking(ref)
            return "Précisez le numéro de conteneur (ex: MSKU1234567)."

        # --- AIR FREIGHT READINESS ---
        if any(x in msg for x in ["AÉRIEN", "AERIEN", "URGENT", "AIR FREIGHT", "AVION"]):
            return self.scenarios.get_readiness_for_air()

        # --- DDP IN TRANSIT ---
        if any(x in msg for x in ["EN TRANSIT", "TRANSIT", "DDP EN COURS"]):
            return self.scenarios.export_ddp_in_transit()

        # --- POD COMPLETION ---
        if any(x in msg for x in ["POD", "LIVRAISON COMPLÈTE", "LIVRAISON COMPLETE", "COMPLÉTUDE"]):
            if ref:
                return self.scenarios.check_pod_completion(ref)
            return "Précisez la référence pour vérifier le POD."

        # --- DELAY ANALYSIS ---
        if any(x in msg for x in ["ANALYSE RETARD", "HISTORIQUE RETARD", "RETARDS PASSÉS"]):
            return self.scenarios.analyze_delay_history()

        # --- DOCUMENTS ---
        if any(x in msg for x in ["DOCUMENT", "FACTURE", "BL ", "PACKING LIST"]):
            if ref:
                return self.scenarios.get_documents_status(ref)
            return "Pour quelle commande cherchez-vous des documents ?"

        # --- RISKS / ALERTS ---
        if any(x in msg for x in ["METEO", "MÉTÉO", "ALEA", "ALÉA", "ALEAS", "ALÉAS", "RISQUE", "GREVE", "GRÈVE", "CONGESTION", "TEMPÊTE", "TEMPETE"]):
            if "ROUTE" in msg or "MER" in msg:
                return self.scenarios.simulate_route_risk("ASIA-EUROPE")
            return self.scenarios.get_global_alerts()

        # --- WAREHOUSE VOLUME ---
        if any(x in msg for x in ["VOLUME", "ENTREPOT", "ENTREPÔT", "WAREHOUSE", "OCCUPATION"]):
            return self.scenarios.analyze_warehouse_volume(month)

        # --- CAMPAIGN STATUS ---
        if any(x in msg for x in ["CAMPAGNE", "CAMPAIGN", "KPI"]):
            return self.scenarios.get_campaign_status("PROMO")

        # --- SUPPLIER PERFORMANCE ---
        if any(x in msg for x in ["FOURNISSEUR", "SUPPLIER", "PERFORMANCE USINE", "USINE"]):
            return self.scenarios.supplier_performance("Pure Trade")

        # --- COMPLIANCE ---
        if any(x in msg for x in ["CONFORMITÉ", "CONFORMITE", "QUALITÉ", "QUALITE", "ESG", "NORME"]):
            if ref:
                return self.scenarios.check_quality_compliance(ref)
            return "Précisez la référence pour vérifier la conformité."

        # Fallback
        return """Je ne suis pas sûr de comprendre. Essayez:
• 'Où est 25DOG007 ?'
• 'Commandes première quinzaine janvier'
• 'Arrivées port sous 7 jours'
• 'Statut EXW→DDP pour 25DOG007'
• 'Aléas météo actuels'
• 'Schedules maritimes janvier'"""

