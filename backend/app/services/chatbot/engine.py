import os
from langchain_community.llms import Ollama
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from ...database import engine as db_engine

# Custom prompt for SQL generation with logistics domain knowledge
SQL_GENERATION_PROMPT = """Tu es un expert en base de données logistique. Tu dois traduire les questions en français vers des requêtes SQL PostgreSQL.

SCHÉMA DE LA BASE DE DONNÉES:
Table "shipments" (expéditions):
- id: identifiant unique
- reference: numéro de commande (PO Number)
- order_number: numéro de commande
- batch_number: numéro de lot (LOT 1, LOT 2, etc.)
- sku: référence produit
- customer: client
- status: statut actuel (ORDER_INFO, PRODUCTION_READY, LOADING_IN_PROGRESS, TRANSIT_OCEAN, FINAL_DELIVERY, etc.)
- origin: origine
- destination: destination
- planned_etd: date de départ prévue
- planned_eta: date d'arrivée prévue
- container_number: numéro de conteneur
- vessel: nom du navire
- product_description: description du produit
- quantity: quantité
- weight_kg: poids en kg
- supplier: fournisseur
- forwarder_name: transitaire
- comments_internal: commentaires

Table "events" (événements):
- id, shipment_id, type, timestamp, note

VOCABULAIRE LOGISTIQUE:
- "lot" ou "batch" = batch_number
- "commande" ou "PO" = reference ou order_number
- "statut" ou "état" = status
- "conteneur" = container_number
- "navire" ou "bateau" = vessel

RÈGLES:
1. Utilise ILIKE pour les recherches textuelles (insensible à la casse)
2. Pour "lot 1", cherche batch_number ILIKE '%lot%1%' OU batch_number ILIKE '%1%'
3. Retourne toujours les colonnes pertinentes pour répondre à la question
4. Limite les résultats à 10 si pas de critère spécifique

Question: {question}

Requête SQL (SEULEMENT la requête, sans explication):"""

# Custom prompt for natural language synthesis
SYNTHESIS_PROMPT = """Tu es un assistant logistique professionnel. Réponds en français de manière claire et concise.

Question de l'utilisateur: {question}
Requête SQL exécutée: {query}
Résultat de la base de données: {result}

RÈGLES DE RÉPONSE:
1. Si le résultat est vide, dis "Aucune donnée trouvée pour cette recherche."
2. Si le résultat contient des données, résume-les de manière naturelle
3. Utilise le vocabulaire métier (lot, commande, statut, etc.)
4. Sois précis et factuel, base-toi uniquement sur les données

Réponse:"""

class ChatbotEngine:
    def __init__(self, db, user):
        """
        Initialize the deterministic reflection chatbot.
        Args:
            db: SQLAlchemy Session (unused here as we use the engine directly for LangChain)
            user: Current authenticated user
        """
        self.user = user
        # Initialize SQLDatabase from the existing SQLAlchemy engine
        self.db = SQLDatabase(db_engine, include_tables=["shipments", "events"])
        
        # Configure deterministic LLM (Ollama)
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
        self.llm = Ollama(
            base_url=ollama_base_url,
            model="llama3",
            temperature=0  # Force deterministic output
        )
        
        # Initialize prompts
        self.sql_prompt = PromptTemplate.from_template(SQL_GENERATION_PROMPT)
        self.synthesis_prompt = PromptTemplate.from_template(SYNTHESIS_PROMPT)

    def process_stream(self, query: str):
        """
        Process the user query using a 3-phase reflection workflow and stream the response:
        1. Analysis & Translation (NL -> SQL)
        2. Execution (Run SQL)
        3. Synthesis (SQL Result -> NL)
        """
        try:
            # --- Phase 1: Analysis & Translation ---
            yield "🔍 Analyse de votre question...\n"
            
            # Generate SQL using custom prompt
            sql_chain = self.sql_prompt | self.llm | StrOutputParser()
            raw_sql = sql_chain.invoke({"question": query})
            
            # Clean up the SQL (remove markdown code blocks if present)
            sql_query = raw_sql.strip()
            if sql_query.startswith("```"):
                sql_query = sql_query.split("```")[1]
                if sql_query.startswith("sql"):
                    sql_query = sql_query[3:]
            sql_query = sql_query.strip().rstrip(";") + ";"
            
            # --- Phase 2: Execution ---
            yield "💾 Recherche dans la base de données...\n"
            execute_query = QuerySQLDataBaseTool(db=self.db)
            
            try:
                sql_result = execute_query.invoke(sql_query)
            except Exception as sql_error:
                sql_result = f"Erreur SQL: {str(sql_error)}"
            
            # --- Phase 3: Synthesis ---
            yield "✨ Préparation de la réponse...\n\n"
            
            synthesis_chain = self.synthesis_prompt | self.llm | StrOutputParser()
            
            for chunk in synthesis_chain.stream({
                "question": query,
                "query": sql_query,
                "result": sql_result
            }):
                yield chunk
            
        except Exception as e:
            # Fallback for errors
            print(f"Chatbot Error: {str(e)}")
            yield f"\n❌ Désolé, une erreur est survenue: {str(e)}"

