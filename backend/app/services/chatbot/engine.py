import os
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from ...database import engine as db_engine

# Complete SQL prompt with all templates for Groq
SQL_PROMPT = """Tu es un expert SQL PostgreSQL pour une application de suivi logistique. Génère UNIQUEMENT une requête SQL valide, sans explication.

=== TABLES DISPONIBLES ===

SHIPMENTS (expéditions):
id, reference, batch_number, order_number, sku, customer, status, origin, destination, planned_etd, planned_eta, container_number, seal_number, vessel, quantity, weight_kg, volume_cbm, supplier, forwarder_name, qc_date, mad_date, its_date, delivery_date, transport_mode, compliance_status, rush_status, incoterm, comments_internal, created_at

EVENTS (jalons/étapes):
id, shipment_id, type, timestamp, note
Types: ORDER_INFO, PRODUCTION_READY, LOADING_IN_PROGRESS, TRANSIT_OCEAN, ARRIVAL_PORT, IMPORT_CLEARANCE, FINAL_DELIVERY, GPS_POSITION, CUSTOMS_STATUS

ALERTS (aléas/risques):
id, type, severity, message, impact_days, category, shipment_id, linked_route, active, created_at
Types: WEATHER, STRIKE, CUSTOMS, PORT_CONGESTION, PANDEMIC, FINANCIAL
Severity: LOW, MEDIUM, HIGH, CRITICAL

DOCUMENTS:
id, shipment_id, type, filename, url, status, uploaded_at
Types: BL, INVOICE, PACKING_LIST, QC_REPORT, CUSTOMS_DEC

CARRIER_SCHEDULES (horaires transporteurs):
id, carrier, pol, pod, mode, etd, eta, transit_time_days, vessel_name, voyage_ref

=== RÈGLES IMPORTANTES ===
- lot/numéro de lot → batch_number
- commande/PO/référence → reference
- aléa/risque → alerts
- jalon/étape → events
- Pour chercher X: WHERE reference ILIKE '%X%' OR batch_number ILIKE '%X%'
- Toujours LIMIT 10 sauf si stats

=== TEMPLATES PAR CATÉGORIE ===

--- RECHERCHE & STATUT ---
Q: où est ma commande X / statut X / position X
SQL: SELECT reference, batch_number, status, planned_eta, vessel FROM shipments WHERE reference ILIKE '%X%' OR batch_number ILIKE '%X%' LIMIT 5;

Q: statut détaillé X / tout sur commande X
SQL: SELECT reference, batch_number, status, customer, origin, destination, planned_etd, planned_eta, vessel, transport_mode FROM shipments WHERE reference ILIKE '%X%' OR batch_number ILIKE '%X%' LIMIT 5;

Q: ETD / date départ usine X
SQL: SELECT reference, batch_number, planned_etd, origin, status FROM shipments WHERE reference ILIKE '%X%' OR batch_number ILIKE '%X%' LIMIT 5;

Q: ETA / arrivée prévue X
SQL: SELECT reference, batch_number, planned_eta, destination, vessel FROM shipments WHERE reference ILIKE '%X%' OR batch_number ILIKE '%X%' LIMIT 5;

Q: conteneur X / tracking conteneur
SQL: SELECT reference, batch_number, container_number, seal_number, vessel, status FROM shipments WHERE container_number ILIKE '%X%' OR reference ILIKE '%X%' LIMIT 5;

--- RETARDS & URGENCES ---
Q: retards / articles en retard
SQL: SELECT reference, status, planned_eta, planned_eta - CURRENT_DATE as jours_retard FROM shipments WHERE planned_eta < CURRENT_DATE AND status NOT ILIKE '%DELIVER%' LIMIT 10;

Q: commandes urgentes / rush
SQL: SELECT reference, status, planned_eta, customer FROM shipments WHERE rush_status = true LIMIT 10;

Q: retards maritimes
SQL: SELECT reference, status, planned_eta, CURRENT_DATE - planned_eta as jours_retard, vessel FROM shipments WHERE planned_eta < CURRENT_DATE AND status NOT ILIKE '%DELIVER%' AND transport_mode ILIKE '%SEA%' LIMIT 10;

--- ALÉAS & RISQUES ---
Q: aléas actifs / risques en cours
SQL: SELECT type, severity, message, impact_days, linked_route FROM alerts WHERE active = true ORDER BY severity DESC, created_at DESC LIMIT 15;

Q: alertes critiques
SQL: SELECT type, message, impact_days, linked_route FROM alerts WHERE severity = 'CRITICAL' AND active = true LIMIT 10;

Q: aléas météo / tempêtes
SQL: SELECT type, severity, message, impact_days, linked_route FROM alerts WHERE type = 'WEATHER' AND active = true LIMIT 10;

Q: congestion ports
SQL: SELECT type, message, impact_days, linked_route FROM alerts WHERE type = 'PORT_CONGESTION' AND active = true LIMIT 10;

Q: grèves
SQL: SELECT type, message, severity, impact_days FROM alerts WHERE type = 'STRIKE' AND active = true LIMIT 10;

Q: aléas douanes
SQL: SELECT type, message, severity, impact_days FROM alerts WHERE type = 'CUSTOMS' AND active = true LIMIT 10;

Q: risques par route / aléas maritimes
SQL: SELECT type, message, linked_route, impact_days FROM alerts WHERE linked_route IS NOT NULL AND active = true LIMIT 10;

Q: statistiques aléas
SQL: SELECT type, COUNT(*) as nb, AVG(impact_days) as impact_moyen FROM alerts WHERE active = true GROUP BY type;

--- JALONS & TRAÇABILITÉ ---
Q: historique jalons X / étapes X
SQL: SELECT e.type, e.timestamp, e.note, s.reference FROM events e JOIN shipments s ON e.shipment_id = s.id WHERE s.reference ILIKE '%X%' OR s.batch_number ILIKE '%X%' ORDER BY e.timestamp DESC LIMIT 20;

Q: tracking GPS / position temps réel
SQL: SELECT e.type, e.timestamp, e.note, s.reference, s.vessel FROM events e JOIN shipments s ON e.shipment_id = s.id WHERE e.type = 'GPS_POSITION' ORDER BY e.timestamp DESC LIMIT 10;

Q: douanes / customs status
SQL: SELECT e.type, e.timestamp, e.note, s.reference FROM events e JOIN shipments s ON e.shipment_id = s.id WHERE e.type IN ('CUSTOMS_STATUS', 'IMPORT_CLEARANCE') ORDER BY e.timestamp DESC LIMIT 10;

--- DOCUMENTS ---
Q: documents X / BL / facture X
SQL: SELECT d.type, d.filename, d.status, d.uploaded_at FROM documents d JOIN shipments s ON d.shipment_id = s.id WHERE s.reference ILIKE '%X%' OR s.batch_number ILIKE '%X%' LIMIT 10;

Q: rapport qualité / QC report X
SQL: SELECT d.type, d.filename, d.status, d.uploaded_at FROM documents d JOIN shipments s ON d.shipment_id = s.id WHERE d.type = 'QC_REPORT' AND (s.reference ILIKE '%X%' OR s.batch_number ILIKE '%X%') LIMIT 5;

--- QUALITÉ & CONFORMITÉ ---
Q: QC validé / contrôle qualité X
SQL: SELECT reference, batch_number, qc_date, compliance_status FROM shipments WHERE reference ILIKE '%X%' OR batch_number ILIKE '%X%' LIMIT 5;

Q: conformité / compliance X
SQL: SELECT reference, batch_number, compliance_status, qc_date FROM shipments WHERE reference ILIKE '%X%' OR batch_number ILIKE '%X%' LIMIT 5;

Q: date livraison X
SQL: SELECT reference, batch_number, delivery_date, planned_eta, destination FROM shipments WHERE reference ILIKE '%X%' OR batch_number ILIKE '%X%' LIMIT 5;

--- CLIENTS & FOURNISSEURS ---
Q: commandes client X
SQL: SELECT reference, status, planned_eta, customer FROM shipments WHERE customer ILIKE '%X%' LIMIT 10;

Q: commandes fournisseur X
SQL: SELECT reference, status, supplier, planned_etd FROM shipments WHERE supplier ILIKE '%X%' LIMIT 10;

Q: volume par client
SQL: SELECT customer, COUNT(*) as nb_commandes, SUM(quantity) as total_qty FROM shipments GROUP BY customer ORDER BY nb_commandes DESC LIMIT 10;

--- TRANSPORT & SCHEDULES ---
Q: en transit
SQL: SELECT reference, vessel, planned_eta, status FROM shipments WHERE status ILIKE '%TRANSIT%' LIMIT 10;

Q: livrés / terminés
SQL: SELECT reference, status, delivery_date FROM shipments WHERE status ILIKE '%DELIVER%' OR status ILIKE '%FINAL%' LIMIT 10;

Q: expéditions maritimes
SQL: SELECT reference, transport_mode, vessel, status, planned_eta FROM shipments WHERE transport_mode ILIKE '%SEA%' LIMIT 10;

Q: expéditions aériennes
SQL: SELECT reference, transport_mode, status, planned_eta FROM shipments WHERE transport_mode ILIKE '%AIR%' LIMIT 10;

Q: schedules / horaires transporteurs
SQL: SELECT carrier, pol, pod, etd, eta, transit_time_days, vessel_name FROM carrier_schedules WHERE etd >= CURRENT_DATE ORDER BY etd LIMIT 10;

Q: meilleur schedule maritime
SQL: SELECT carrier, pol, pod, etd, eta, transit_time_days FROM carrier_schedules WHERE mode = 'SEA' AND etd >= CURRENT_DATE ORDER BY transit_time_days, etd LIMIT 10;

Q: arrivées 7 jours
SQL: SELECT reference, planned_eta, destination, vessel FROM shipments WHERE planned_eta BETWEEN CURRENT_DATE AND CURRENT_DATE + 7 ORDER BY planned_eta LIMIT 10;

--- DDP & INCOTERMS ---
Q: commandes DDP
SQL: SELECT reference, status, incoterm, planned_eta FROM shipments WHERE incoterm = 'DDP' LIMIT 10;

Q: DDP en transit
SQL: SELECT reference, status, vessel, planned_eta FROM shipments WHERE incoterm = 'DDP' AND status ILIKE '%TRANSIT%' LIMIT 10;

Q: commandes par incoterm
SQL: SELECT incoterm, COUNT(*) as nb FROM shipments WHERE incoterm IS NOT NULL GROUP BY incoterm ORDER BY nb DESC;

--- STATISTIQUES ---
Q: stats par statut / répartition statuts
SQL: SELECT status, COUNT(*) as nb FROM shipments GROUP BY status ORDER BY nb DESC;

Q: stats par client
SQL: SELECT customer, COUNT(*) as nb FROM shipments GROUP BY customer ORDER BY nb DESC LIMIT 10;

Q: stats par transporteur
SQL: SELECT forwarder_name, COUNT(*) as nb FROM shipments WHERE forwarder_name IS NOT NULL GROUP BY forwarder_name ORDER BY nb DESC LIMIT 10;

Q: stats expéditions mois
SQL: SELECT COUNT(*) as total, SUM(CASE WHEN status ILIKE '%DELIVER%' THEN 1 ELSE 0 END) as livrees FROM shipments WHERE created_at >= CURRENT_DATE - INTERVAL '30 days';

--- COMMERCIAL/VENTES ---
Q: prêt facturation / ready billing
SQL: SELECT reference, status, customer, delivery_date FROM shipments WHERE status IN ('FINAL_DELIVERY', 'IMPORT_CLEARANCE') AND delivery_date IS NOT NULL LIMIT 10;

Q: commandes prêtes / production ready
SQL: SELECT reference, status, customer, planned_eta FROM shipments WHERE status = 'PRODUCTION_READY' LIMIT 10;

Q: deadline cut-off maritime
SQL: SELECT reference, planned_etd, planned_etd - CURRENT_DATE as jours_avant_cutoff, status FROM shipments WHERE transport_mode ILIKE '%SEA%' AND planned_etd >= CURRENT_DATE ORDER BY planned_etd LIMIT 10;

--- ACHATS/PROCUREMENT ---
Q: achats urgents
SQL: SELECT reference, supplier, transport_mode, planned_etd FROM shipments WHERE rush_status = true AND supplier IS NOT NULL ORDER BY planned_etd LIMIT 10;

Q: fiabilité fournisseurs
SQL: SELECT supplier, COUNT(*) as total, SUM(CASE WHEN planned_eta >= delivery_date THEN 1 ELSE 0 END) as on_time FROM shipments WHERE supplier IS NOT NULL AND delivery_date IS NOT NULL GROUP BY supplier LIMIT 10;

Q: {question}
SQL:"""

ANSWER_PROMPT = """Tu es un assistant logistique. Réponds en français de manière brève et factuelle.
Base-toi UNIQUEMENT sur les données fournies. N'invente rien.
Si les données sont vides ou contiennent une erreur: réponds "Aucun résultat trouvé pour cette recherche."

Question: {question}
Données: {result}
Réponse:"""

class ChatbotEngine:
    def __init__(self, db, user):
        self.user = user
        self.db = SQLDatabase(db_engine, include_tables=["shipments", "events", "alerts", "documents", "carrier_schedules"])
        
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        self.llm = ChatGroq(
            api_key=groq_api_key,
            model="llama-3.1-8b-instant",  # Fast and capable
            temperature=0,
            max_tokens=200,
        )
        
        self.sql_prompt = PromptTemplate.from_template(SQL_PROMPT)
        self.answer_prompt = PromptTemplate.from_template(ANSWER_PROMPT)

    def process_stream(self, query: str):
        try:
            yield "🔍 "
            
            # Generate SQL
            sql_chain = self.sql_prompt | self.llm | StrOutputParser()
            raw_sql = sql_chain.invoke({"question": query})
            
            # Clean SQL
            sql = raw_sql.strip()
            if "```" in sql:
                sql = sql.split("```")[1].replace("sql", "").strip()
            sql = sql.split(";")[0] + ";"
            
            # Execute SQL
            try:
                result = QuerySQLDataBaseTool(db=self.db).invoke(sql)
            except Exception as e:
                result = f"Erreur SQL: {str(e)}"
            
            # Generate answer
            answer_chain = self.answer_prompt | self.llm | StrOutputParser()
            for chunk in answer_chain.stream({"question": query, "result": result}):
                yield chunk
                
        except Exception as e:
            yield f"❌ Erreur: {str(e)}"
