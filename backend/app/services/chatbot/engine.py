import os
from langchain_community.llms import Ollama
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from ...database import engine as db_engine

# Comprehensive SQL prompt with all tables
SQL_PROMPT = """SQL PostgreSQL expert. Tables disponibles:

=== SHIPMENTS ===
id, reference, order_number, batch_number, sku, customer, status, origin, destination, planned_etd, planned_eta, container_number, seal_number, vessel, quantity, weight_kg, volume_cbm, supplier, forwarder_name, qc_date, mad_date, its_date, delivery_date, transport_mode, compliance_status, rush_status, comments_internal, created_at

=== EVENTS (jalons) ===
id, shipment_id, type, timestamp, note
Types: ORDER_INFO, PRODUCTION_READY, LOADING_IN_PROGRESS, TRANSIT_OCEAN, ARRIVAL_PORT, IMPORT_CLEARANCE, FINAL_DELIVERY, GPS_POSITION, CUSTOMS_STATUS

=== ALERTS (aléas/risques) ===
id, type, severity, message, impact_days, category, shipment_id, linked_route, active, created_at
Types: WEATHER, STRIKE, CUSTOMS, PORT_CONGESTION, PANDEMIC, FINANCIAL
Severity: LOW, MEDIUM, HIGH, CRITICAL

=== DOCUMENTS ===
id, shipment_id, type, filename, url, status, uploaded_at
Types: BL, INVOICE, PACKING_LIST, QC_REPORT, CUSTOMS_DEC

Synonymes: lot→batch_number, commande/PO→reference, aléa/risque→alerts, jalon/étape→events, qualité/QC→qc_date ou documents, retard→planned_eta<CURRENT_DATE

=== TEMPLATES ===
Q: où est ma commande X/position X
SQL: SELECT s.reference,s.status,e.type as dernier_jalon,e.timestamp FROM shipments s LEFT JOIN events e ON s.id=e.shipment_id WHERE s.reference ILIKE'%X%'ORDER BY e.timestamp DESC LIMIT 1;
Q: statut détaillé X/production/QC/transit
SQL: SELECT s.reference,s.status,s.qc_date,s.planned_etd,s.planned_eta,s.transport_mode FROM shipments s WHERE s.reference ILIKE'%X%'LIMIT 5;
Q: retards signalés/articles en retard
SQL: SELECT reference,status,planned_eta,planned_eta-CURRENT_DATE as jours_retard FROM shipments WHERE planned_eta<CURRENT_DATE AND status NOT ILIKE'%DELIVER%'LIMIT 10;
Q: ETD/date départ usine X
SQL: SELECT reference,planned_etd,origin,status FROM shipments WHERE reference ILIKE'%X%'OR container_number ILIKE'%X%'LIMIT 5;
Q: ETA/arrivée prévue X
SQL: SELECT reference,planned_eta,destination,vessel FROM shipments WHERE reference ILIKE'%X%'LIMIT 5;
Q: aléas météo/congestion ports
SQL: SELECT type,severity,message,impact_days,linked_route FROM alerts WHERE type IN('WEATHER','PORT_CONGESTION')AND active=true ORDER BY created_at DESC LIMIT 10;
Q: aléas opérationnels/grèves
SQL: SELECT type,severity,message,impact_days FROM alerts WHERE type IN('STRIKE','CUSTOMS')AND active=true LIMIT 10;
Q: QC validé/contrôle qualité X
SQL: SELECT reference,qc_date,compliance_status FROM shipments WHERE reference ILIKE'%X%'LIMIT 5;
Q: rapport qualité/documents QC X
SQL: SELECT d.type,d.filename,d.status,d.uploaded_at FROM documents d JOIN shipments s ON d.shipment_id=s.id WHERE s.reference ILIKE'%X%'AND d.type='QC_REPORT'LIMIT 5;
Q: date livraison X
SQL: SELECT reference,delivery_date,planned_eta,destination FROM shipments WHERE reference ILIKE'%X%'LIMIT 5;
Q: aléas fournisseur
SQL: SELECT a.type,a.message,a.severity,s.supplier FROM alerts a JOIN shipments s ON a.shipment_id=s.id WHERE a.active=true LIMIT 10;
Q: numéro conteneur/tracking X
SQL: SELECT reference,container_number,seal_number,vessel,bl_number FROM shipments WHERE reference ILIKE'%X%'OR customer ILIKE'%X%'LIMIT 10;
Q: aléas actifs/risques en cours
SQL: SELECT type,severity,message,impact_days,linked_route FROM alerts WHERE active=true ORDER BY severity DESC,created_at DESC LIMIT 15;
Q: historique jalons X
SQL: SELECT e.type,e.timestamp,e.note FROM events e JOIN shipments s ON e.shipment_id=s.id WHERE s.reference ILIKE'%X%'ORDER BY e.timestamp DESC LIMIT 20;
Q: commandes urgentes/rush
SQL: SELECT reference,status,planned_eta,customer FROM shipments WHERE rush_status=true LIMIT 10;
Q: documents X/BL/facture
SQL: SELECT d.type,d.filename,d.status FROM documents d JOIN shipments s ON d.shipment_id=s.id WHERE s.reference ILIKE'%X%'LIMIT 10;
Q: aléas par route/maritime
SQL: SELECT type,message,linked_route,impact_days FROM alerts WHERE linked_route IS NOT NULL AND active=true LIMIT 10;
Q: conformité/compliance X
SQL: SELECT reference,compliance_status,qc_date FROM shipments WHERE reference ILIKE'%X%'LIMIT 5;
Q: poids/volume X
SQL: SELECT reference,weight_kg,volume_cbm,quantity,nb_cartons FROM shipments WHERE reference ILIKE'%X%'LIMIT 5;
Q: mode transport X/aérien/maritime
SQL: SELECT reference,transport_mode,vessel,status FROM shipments WHERE transport_mode ILIKE'%X%'LIMIT 10;
Q: expéditions mois
SQL: SELECT reference,status,customer,planned_eta FROM shipments WHERE created_at>=CURRENT_DATE-INTERVAL'30 days'LIMIT 10;
Q: en transit
SQL: SELECT reference,status,vessel,planned_eta FROM shipments WHERE status ILIKE'%TRANSIT%'LIMIT 10;
Q: livrés/terminés
SQL: SELECT reference,status,delivery_date FROM shipments WHERE status ILIKE'%DELIVER%'OR status ILIKE'%FINAL%'LIMIT 10;
Q: par statut
SQL: SELECT status,COUNT(*)as nb FROM shipments GROUP BY status ORDER BY nb DESC;
Q: par client
SQL: SELECT customer,COUNT(*)as nb FROM shipments GROUP BY customer ORDER BY nb DESC LIMIT 10;
Q: alertes critiques
SQL: SELECT type,message,impact_days FROM alerts WHERE severity='CRITICAL'AND active=true LIMIT 10;
Q: statistiques aléas
SQL: SELECT type,COUNT(*)as nb,AVG(impact_days)as impact_moyen FROM alerts WHERE active=true GROUP BY type;

Q: {question}
SQL:"""

ANSWER_PROMPT = """Réponds en français, bref et factuel. Données uniquement. Si vide/erreur: "Aucun résultat trouvé."
Q: {question}
D: {result}
R:"""

class ChatbotEngine:
    def __init__(self, db, user):
        self.user = user
        self.db = SQLDatabase(db_engine, include_tables=["shipments", "events", "alerts", "documents"])
        
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
        self.llm = Ollama(
            base_url=ollama_url,
            model="mistral",
            temperature=0,
            num_predict=200,
        )
        
        self.sql_prompt = PromptTemplate.from_template(SQL_PROMPT)
        self.answer_prompt = PromptTemplate.from_template(ANSWER_PROMPT)

    def process_stream(self, query: str):
        try:
            yield "🔍..."
            
            sql_chain = self.sql_prompt | self.llm | StrOutputParser()
            raw_sql = sql_chain.invoke({"question": query})
            
            sql = raw_sql.strip()
            if "```" in sql:
                sql = sql.split("```")[1].replace("sql", "").strip()
            sql = sql.split(";")[0] + ";"
            
            try:
                result = QuerySQLDataBaseTool(db=self.db).invoke(sql)
            except Exception as e:
                result = f"Erreur: {str(e)}"
            
            yield "\n"
            
            answer_chain = self.answer_prompt | self.llm | StrOutputParser()
            for chunk in answer_chain.stream({"question": query, "result": result}):
                yield chunk
                
        except Exception as e:
            yield f"❌ {str(e)}"





