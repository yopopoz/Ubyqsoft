import os
from langchain_community.llms import Ollama
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from ...database import engine as db_engine

# Optimized SQL prompt for llama3 with 8GB RAM
SQL_PROMPT = """Tu es un expert PostgreSQL. Génère UNIQUEMENT une requête SQL valide, sans explication.

TABLES DISPONIBLES:
- shipments: id, reference, batch_number, customer, status, origin, destination, planned_etd, planned_eta, container_number, vessel, supplier, forwarder_name, transport_mode, rush_status, incoterm, qc_date, delivery_date, compliance_status
- events: id, shipment_id, type, timestamp, note
- alerts: id, type, severity, message, impact_days, active, linked_route, shipment_id
- documents: id, shipment_id, type, filename, status
- carrier_schedules: id, carrier, pol, pod, mode, etd, eta, transit_time_days

RÈGLES IMPORTANTES:
- "lot" ou numéro de lot = chercher dans batch_number
- "commande" ou "PO" = chercher dans reference
- Pour chercher une référence X: WHERE reference ILIKE '%X%' OR batch_number ILIKE '%X%'
- Toujours ajouter LIMIT 10

EXEMPLES:
Q: statut commande 25LAN034-16
SQL: SELECT reference, batch_number, status, planned_eta FROM shipments WHERE reference ILIKE '%25LAN034-16%' OR batch_number ILIKE '%25LAN034-16%' LIMIT 5;

Q: retards
SQL: SELECT reference, status, planned_eta FROM shipments WHERE planned_eta < CURRENT_DATE AND status NOT ILIKE '%DELIVER%' LIMIT 10;

Q: aléas actifs
SQL: SELECT type, severity, message FROM alerts WHERE active = true ORDER BY severity DESC LIMIT 10;

Q: jalons de la commande X
SQL: SELECT e.type, e.timestamp FROM events e JOIN shipments s ON e.shipment_id = s.id WHERE s.reference ILIKE '%X%' ORDER BY e.timestamp;

Q: en transit
SQL: SELECT reference, vessel, planned_eta FROM shipments WHERE status ILIKE '%TRANSIT%' LIMIT 10;

Q: {question}
SQL:"""

ANSWER_PROMPT = """Réponds en français, bref et factuel. Données uniquement. Si vide/erreur: "Aucun résultat trouvé."
Q: {question}
D: {result}
R:"""

class ChatbotEngine:
    def __init__(self, db, user):
        self.user = user
        self.db = SQLDatabase(db_engine, include_tables=["shipments", "events", "alerts", "documents", "carrier_schedules"])
        
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
        self.llm = Ollama(
            base_url=ollama_url,
            model="llama3",  # Better quality than qwen
            temperature=0,
            num_predict=150,
            num_ctx=4096,
            timeout=180,  # 3 min timeout for llama3
        )
        
        self.sql_prompt = PromptTemplate.from_template(SQL_PROMPT)
        self.answer_prompt = PromptTemplate.from_template(ANSWER_PROMPT)

    def process_stream(self, query: str):
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"[CHATBOT] Starting query: {query[:50]}...")
            yield "🔍..."
            
            logger.info("[CHATBOT] Building SQL chain...")
            sql_chain = self.sql_prompt | self.llm | StrOutputParser()
            
            logger.info("[CHATBOT] Invoking LLM for SQL...")
            raw_sql = sql_chain.invoke({"question": query})
            logger.info(f"[CHATBOT] Got SQL: {raw_sql[:100]}...")
            
            sql = raw_sql.strip()
            if "```" in sql:
                sql = sql.split("```")[1].replace("sql", "").strip()
            sql = sql.split(";")[0] + ";"
            
            logger.info(f"[CHATBOT] Executing SQL: {sql[:100]}...")
            try:
                result = QuerySQLDataBaseTool(db=self.db).invoke(sql)
                logger.info(f"[CHATBOT] Query result: {str(result)[:100]}...")
            except Exception as e:
                logger.error(f"[CHATBOT] SQL Error: {str(e)}")
                result = f"Erreur: {str(e)}"
            
            yield "\n"
            
            logger.info("[CHATBOT] Building answer chain...")
            answer_chain = self.answer_prompt | self.llm | StrOutputParser()
            
            logger.info("[CHATBOT] Streaming answer...")
            for chunk in answer_chain.stream({"question": query, "result": result}):
                yield chunk
            
            logger.info("[CHATBOT] Done!")
                
        except Exception as e:
            import traceback
            logger.error(f"[CHATBOT] Exception: {str(e)}")
            logger.error(traceback.format_exc())
            yield f"❌ {str(e)}"







