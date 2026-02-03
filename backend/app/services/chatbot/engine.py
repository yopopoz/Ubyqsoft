import os
from langchain_community.llms import Ollama
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from ...database import engine as db_engine

# Comprehensive SQL prompt with synonyms and diverse examples
SQL_PROMPT = """Tu es un expert SQL pour une base logistique. Génère UNIQUEMENT du SQL PostgreSQL valide.

=== COLONNES DISPONIBLES (table: shipments) ===
id, reference, order_number, batch_number, sku, customer, status, origin, destination, 
planned_etd, planned_eta, container_number, vessel, quantity, supplier, forwarder_name, created_at

=== DICTIONNAIRE SYNONYMES → COLONNE ===
lot/batch/numéro de lot → batch_number
commande/PO/order/numéro commande → reference OU order_number  
produit/article/SKU/référence produit → sku
statut/état/situation → status
client/customer → customer
fournisseur/supplier → supplier
origine/départ/from → origin
destination/arrivée/to → destination
date départ/ETD/départ prévu → planned_etd
date arrivée/ETA/arrivée prévue → planned_eta
conteneur/container → container_number
navire/bateau/vessel → vessel
quantité/qty/nombre → quantity
transitaire/forwarder → forwarder_name

=== EXEMPLES ===
Q: expéditions du mois / envois récents / shipments this month
SQL: SELECT reference, status, customer, planned_eta FROM shipments WHERE created_at >= CURRENT_DATE - INTERVAL '30 days' LIMIT 10;

Q: lot 1 / batch 1 / numéro de lot 1
SQL: SELECT reference, batch_number, status, customer FROM shipments WHERE batch_number ILIKE '%1%' LIMIT 5;

Q: statut commande ABC / état de ABC / où en est ABC
SQL: SELECT reference, status, planned_eta, destination FROM shipments WHERE reference ILIKE '%ABC%' OR order_number ILIKE '%ABC%' LIMIT 5;

Q: combien d'expéditions / nombre total / count
SQL: SELECT COUNT(*) as total FROM shipments;

Q: expéditions en transit / en cours / in progress
SQL: SELECT reference, status, vessel, planned_eta FROM shipments WHERE status ILIKE '%TRANSIT%' OR status ILIKE '%PROGRESS%' LIMIT 10;

Q: client X / expéditions pour X / commandes client X  
SQL: SELECT reference, status, planned_eta FROM shipments WHERE customer ILIKE '%X%' LIMIT 10;

Q: conteneur ABCD / container ABCD
SQL: SELECT reference, container_number, status, vessel FROM shipments WHERE container_number ILIKE '%ABCD%' LIMIT 5;

Q: produit SKU123 / article SKU123
SQL: SELECT reference, sku, quantity, status FROM shipments WHERE sku ILIKE '%SKU123%' LIMIT 10;

Q: arrivées prévues / ETA cette semaine
SQL: SELECT reference, planned_eta, status, destination FROM shipments WHERE planned_eta >= CURRENT_DATE AND planned_eta <= CURRENT_DATE + INTERVAL '7 days' ORDER BY planned_eta LIMIT 10;

Q: retards / en retard / delayed
SQL: SELECT reference, status, planned_eta FROM shipments WHERE planned_eta < CURRENT_DATE AND status NOT ILIKE '%DELIVER%' LIMIT 10;

=== RÈGLES ===
1. Utilise TOUJOURS ILIKE pour les recherches texte (insensible à la casse)
2. LIMIT 10 par défaut sauf si COUNT demandé
3. N'invente JAMAIS de colonnes - utilise UNIQUEMENT celles listées ci-dessus

Question: {question}
SQL:"""

# Strict answer prompt
ANSWER_PROMPT = """Réponds en français, bref et factuel. Base-toi UNIQUEMENT sur les données.
Question: {question}
Données: {result}
Si vide ou erreur: "Aucun résultat trouvé pour cette recherche."
Réponse:"""

class ChatbotEngine:
    def __init__(self, db, user):
        self.user = user
        self.db = SQLDatabase(db_engine, include_tables=["shipments"])
        
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
        # Use llama3 for better understanding (accepts slower for accuracy)
        self.llm = Ollama(
            base_url=ollama_url,
            model="llama3",
            temperature=0,
            num_predict=200,
        )
        
        self.sql_prompt = PromptTemplate.from_template(SQL_PROMPT)
        self.answer_prompt = PromptTemplate.from_template(ANSWER_PROMPT)

    def process_stream(self, query: str):
        try:
            yield "🔍 Analyse...\n"
            
            # Generate SQL
            sql_chain = self.sql_prompt | self.llm | StrOutputParser()
            raw_sql = sql_chain.invoke({"question": query})
            
            # Clean SQL
            sql = raw_sql.strip()
            if "```" in sql:
                sql = sql.split("```")[1].replace("sql", "").strip()
            sql = sql.split(";")[0] + ";"
            
            # Execute
            yield "💾 Recherche...\n"
            try:
                result = QuerySQLDataBaseTool(db=self.db).invoke(sql)
            except Exception as e:
                result = f"Erreur: {str(e)}"
            
            yield "\n"
            
            # Answer
            answer_chain = self.answer_prompt | self.llm | StrOutputParser()
            for chunk in answer_chain.stream({"question": query, "result": result}):
                yield chunk
                
        except Exception as e:
            yield f"❌ Erreur: {str(e)}"



