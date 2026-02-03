import os
from langchain_community.llms import Ollama
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from ...database import engine as db_engine

# Condensed SQL prompt for fast LLM processing (8GB RAM constraint)
SQL_PROMPT = """PostgreSQL. Tables: shipments(id,reference,batch_number,customer,status,origin,destination,planned_etd,planned_eta,container_number,vessel,supplier,forwarder_name,transport_mode,rush_status,incoterm,qc_date,delivery_date), events(id,shipment_id,type,timestamp,note), alerts(id,type,severity,message,impact_days,active,linked_route), documents(id,shipment_id,type,filename,status), carrier_schedules(id,carrier,pol,pod,mode,etd,eta,transit_time_days)

Synonymes: lot=batch_number, commande/PO=reference, aléa=alerts, jalon=events

Exemples:
Q: statut/où est X → SELECT reference,batch_number,status,planned_eta FROM shipments WHERE reference ILIKE'%X%'OR batch_number ILIKE'%X%'LIMIT 5;
Q: retards → SELECT reference,status,planned_eta FROM shipments WHERE planned_eta<CURRENT_DATE AND status NOT ILIKE'%DELIVER%'LIMIT 10;
Q: ETD/ETA X → SELECT reference,planned_etd,planned_eta,vessel FROM shipments WHERE reference ILIKE'%X%'OR batch_number ILIKE'%X%'LIMIT 5;
Q: aléas actifs → SELECT type,severity,message,impact_days FROM alerts WHERE active=true ORDER BY severity DESC LIMIT 10;
Q: jalons X → SELECT e.type,e.timestamp FROM events e JOIN shipments s ON e.shipment_id=s.id WHERE s.reference ILIKE'%X%'ORDER BY e.timestamp;
Q: documents X → SELECT type,filename,status FROM documents d JOIN shipments s ON d.shipment_id=s.id WHERE s.reference ILIKE'%X%';
Q: urgents/rush → SELECT reference,status,planned_eta,customer FROM shipments WHERE rush_status=true LIMIT 10;
Q: en transit → SELECT reference,vessel,planned_eta FROM shipments WHERE status ILIKE'%TRANSIT%'LIMIT 10;
Q: schedules/horaires → SELECT carrier,pol,pod,etd,eta,transit_time_days FROM carrier_schedules WHERE etd>=CURRENT_DATE ORDER BY etd LIMIT 10;
Q: client X → SELECT reference,status,planned_eta FROM shipments WHERE customer ILIKE'%X%'LIMIT 10;
Q: fournisseur X → SELECT reference,status,supplier FROM shipments WHERE supplier ILIKE'%X%'LIMIT 10;
Q: conteneur X → SELECT reference,container_number,vessel,status FROM shipments WHERE container_number ILIKE'%X%'OR reference ILIKE'%X%'LIMIT 5;
Q: DDP → SELECT reference,status,incoterm,planned_eta FROM shipments WHERE incoterm='DDP'LIMIT 10;
Q: maritime/aérien → SELECT reference,transport_mode,status FROM shipments WHERE transport_mode ILIKE'%X%'LIMIT 10;
Q: arrivées 7j → SELECT reference,planned_eta,destination FROM shipments WHERE planned_eta BETWEEN CURRENT_DATE AND CURRENT_DATE+7 LIMIT 10;
Q: stats statut → SELECT status,COUNT(*)as nb FROM shipments GROUP BY status;
Q: QC/qualité X → SELECT reference,qc_date,compliance_status FROM shipments WHERE reference ILIKE'%X%'LIMIT 5;
Q: météo/congestion → SELECT type,message,linked_route FROM alerts WHERE type IN('WEATHER','PORT_CONGESTION')AND active=true LIMIT 10;

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
            model="qwen2:1.5b",  # Fast model, installed on server
            temperature=0,
            num_predict=150,
            num_ctx=8192,  # Large context for long prompt
            timeout=120,   # 2 min timeout
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







