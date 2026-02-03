import os
from langchain_community.llms import Ollama
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from ...database import engine as db_engine

# SQL prompt with examples to prevent hallucination
SQL_PROMPT = """Table shipments colonnes EXACTES: id, reference, order_number, batch_number, sku, customer, status, origin, destination, planned_etd, planned_eta, container_number, vessel, quantity, created_at.

Exemples:
Q: expeditions du mois
SQL: SELECT reference, status, planned_eta FROM shipments WHERE created_at >= CURRENT_DATE - INTERVAL '30 days' LIMIT 5;

Q: lot 1
SQL: SELECT reference, batch_number, status FROM shipments WHERE batch_number ILIKE '%1%' LIMIT 5;

Q: statut commande X
SQL: SELECT reference, status, planned_eta FROM shipments WHERE reference ILIKE '%X%' LIMIT 5;

Question: {question}
SQL:"""

# Shorter synthesis prompt - STRICT: no hallucination
ANSWER_PROMPT = """RÈGLE: Réponds UNIQUEMENT avec les données ci-dessous. N'invente rien.
Question: {question}
Données: {result}
Si données vides: "Aucun résultat trouvé."
Réponse (1-2 phrases max):"""

class ChatbotEngine:
    def __init__(self, db, user):
        self.user = user
        self.db = SQLDatabase(db_engine, include_tables=["shipments"])
        
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
        # Use faster model with optimized settings
        self.llm = Ollama(
            base_url=ollama_url,
            model="qwen2:1.5b",  # Much faster than llama3
            temperature=0,
            num_predict=150,  # Limit response length
            num_ctx=1024,  # Smaller context window
        )
        
        self.sql_prompt = PromptTemplate.from_template(SQL_PROMPT)
        self.answer_prompt = PromptTemplate.from_template(ANSWER_PROMPT)

    def process_stream(self, query: str):
        try:
            yield "🔍 Recherche...\n"
            
            # Generate SQL
            sql_chain = self.sql_prompt | self.llm | StrOutputParser()
            raw_sql = sql_chain.invoke({"question": query})
            
            # Clean SQL
            sql = raw_sql.strip()
            if "```" in sql:
                sql = sql.split("```")[1].replace("sql", "").strip()
            sql = sql.split(";")[0] + ";"
            
            # Execute
            try:
                result = QuerySQLDataBaseTool(db=self.db).invoke(sql)
            except:
                result = "Aucun résultat"
            
            yield "\n"
            
            # Answer
            answer_chain = self.answer_prompt | self.llm | StrOutputParser()
            for chunk in answer_chain.stream({"question": query, "result": result}):
                yield chunk
                
        except Exception as e:
            yield f"❌ Erreur: {str(e)}"


