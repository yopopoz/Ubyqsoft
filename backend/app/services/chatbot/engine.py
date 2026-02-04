import os
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from ...database import engine as db_engine

# Optimized SQL prompt for Groq (ultra-fast)
SQL_PROMPT = """Tu es un expert PostgreSQL. Génère UNIQUEMENT le SQL, sans explication.

TABLES:
- shipments: id, reference, batch_number, customer, status, origin, destination, planned_etd, planned_eta, container_number, vessel, supplier, forwarder_name, transport_mode, rush_status, incoterm, qc_date, delivery_date, compliance_status
- events: id, shipment_id, type, timestamp, note
- alerts: id, type, severity, message, impact_days, active, linked_route, shipment_id
- documents: id, shipment_id, type, filename, status
- carrier_schedules: id, carrier, pol, pod, mode, etd, eta, transit_time_days

RÈGLES:
- lot = batch_number, commande/PO = reference
- Chercher: WHERE reference ILIKE '%X%' OR batch_number ILIKE '%X%'
- LIMIT 10 toujours

EXEMPLES:
Q: statut 25LAN034-16
SQL: SELECT reference, batch_number, status, planned_eta FROM shipments WHERE reference ILIKE '%25LAN034-16%' OR batch_number ILIKE '%25LAN034-16%' LIMIT 5;

Q: retards
SQL: SELECT reference, status, planned_eta FROM shipments WHERE planned_eta < CURRENT_DATE AND status NOT ILIKE '%DELIVER%' LIMIT 10;

Q: aléas actifs
SQL: SELECT type, severity, message FROM alerts WHERE active = true ORDER BY severity DESC LIMIT 10;

Q: {question}
SQL:"""

ANSWER_PROMPT = """Réponds en français, court et factuel. Base-toi UNIQUEMENT sur les données.
Si erreur ou vide: "Aucun résultat trouvé."

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
            max_tokens=150,
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
