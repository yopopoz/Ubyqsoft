import os
from langchain_community.llms import Ollama
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from ...database import engine as db_engine

# Compact SQL prompt with synonyms
SQL_PROMPT = """SQL PostgreSQL. Table: shipments
Colonnes: id, reference, order_number, batch_number, sku, customer, status, origin, destination, planned_etd, planned_eta, container_number, vessel, quantity, supplier, created_at

Synonymes: lot→batch_number, commande/PO→reference, produit/SKU→sku, statut→status, client→customer, conteneur→container_number, navire→vessel, ETA→planned_eta, ETD→planned_etd, transitaire→forwarder_name

Règles: ILIKE pour texte, LIMIT 10

Q: expéditions mois
SQL: SELECT reference,status,planned_eta FROM shipments WHERE created_at>=CURRENT_DATE-INTERVAL'30 days'LIMIT 10;
Q: lot 1
SQL: SELECT reference,batch_number,status FROM shipments WHERE batch_number ILIKE'%1%'LIMIT 5;
Q: statut X
SQL: SELECT reference,status,planned_eta FROM shipments WHERE reference ILIKE'%X%'LIMIT 5;
Q: en transit
SQL: SELECT reference,status,vessel FROM shipments WHERE status ILIKE'%TRANSIT%'LIMIT 10;

Q: {question}
SQL:"""

ANSWER_PROMPT = """Français, bref. Données uniquement.
Q: {question}
D: {result}
R:"""

class ChatbotEngine:
    def __init__(self, db, user):
        self.user = user
        self.db = SQLDatabase(db_engine, include_tables=["shipments"])
        
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
        self.llm = Ollama(
            base_url=ollama_url,
            model="mistral",  # Faster than llama3, smarter than qwen2
            temperature=0,
            num_predict=150,
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
            except:
                result = "Aucun résultat"
            
            yield "\n"
            
            answer_chain = self.answer_prompt | self.llm | StrOutputParser()
            for chunk in answer_chain.stream({"question": query, "result": result}):
                yield chunk
                
        except Exception as e:
            yield f"❌ {str(e)}"




