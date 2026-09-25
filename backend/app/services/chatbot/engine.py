import os
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from ...database import engine as db_engine

# ========================================
# COMPREHENSIVE SQL PROMPT - ALL TEMPLATES
# ========================================

SQL_PROMPT = """Tu es un expert SQL PostgreSQL pour une application de suivi logistique. Génère UNIQUEMENT une requête SQL SELECT valide, sans texte ni explication autour.

=== TABLES DISPONIBLES ===
1. shipments (id, reference, batch_number, order_number, sku, customer, status, origin, destination, planned_etd, planned_eta, container_number, seal_number, vessel, quantity, weight_kg, volume_cbm, supplier, forwarder_name, qc_date, mad_date, its_date, delivery_date, transport_mode, compliance_status, rush_status, incoterm, comments_internal, created_at, carrier_scac, last_sync_at, sync_status, next_poll_at)
2. events (id, shipment_id, type, timestamp, note, source, external_id)
   - type: ORDER_INFO, PRODUCTION_READY, LOADING_IN_PROGRESS, TRANSIT_OCEAN, ARRIVAL_PORT, IMPORT_CLEARANCE, FINAL_DELIVERY, GPS_POSITION, CUSTOMS_STATUS
   - source: MANUAL, API_CMA, API_MAERSK, API_VESSELFINDER
3. alerts (id, type, severity, message, impact_days, category, shipment_id, linked_route, active, created_at)
   - type: WEATHER, STRIKE, CUSTOMS, PORT_CONGESTION, PANDEMIC, FINANCIAL | severity: LOW, MEDIUM, HIGH, CRITICAL
4. documents (id, shipment_id, type, filename, url, status, uploaded_at)
   - type: BL, INVOICE, PACKING_LIST, QC_REPORT, CUSTOMS_DEC
5. carrier_schedules (id, carrier, pol, pod, mode, etd, eta, transit_time_days, vessel_name, voyage_ref)
6. api_logs (id, provider, endpoint, method, status_code, request_payload, response_body, error_message, duration_ms, created_at)

=== SYNONYMES & MAPPING ===
- Commande/PO/ref → reference | Lot/batch → batch_number | Article/produit/SKU → sku | Client → customer | Fournisseur → supplier | Transitaire → forwarder_name
- Départ/ETD → planned_etd | Arrivée/ETA → planned_eta | Livraison → delivery_date | Mise à dispo/MAD → mad_date | Instruction/ITS → its_date | Qualité/QC → qc_date
- Conteneur/boîte → container_number | Navire/bateau → vessel | Scellé/plomb → seal_number
- Maritime/mer → transport_mode ILIKE '%SEA%' | Aérien/avion → transport_mode ILIKE '%AIR%' | Routier/camion → transport_mode ILIKE '%ROAD%'
- En retard → planned_eta < CURRENT_DATE AND status NOT ILIKE '%DELIVER%' AND status NOT ILIKE '%FINAL%'
- Urgent/prioritaire/rush → rush_status = true | Aléas/risques → alerts WHERE active = true

=== RÈGLES SQL ===
- Si la recherche ressemble à un code article/SKU (ex: LG791800), chercher dans (sku ILIKE '%X%' OR reference ILIKE '%X%' OR batch_number ILIKE '%X%').
- Toujours inclure LIMIT 15 (sauf pour COUNT/GROUP BY).
- Utiliser CURRENT_DATE pour la date du jour.

=== EXEMPLES DE REQUÊTES ===
Q: Où est ma commande X / statut SKU X
SQL: SELECT reference, batch_number, sku, status, customer, origin, destination, planned_etd, planned_eta, vessel, container_number, transport_mode FROM shipments WHERE reference ILIKE '%X%' OR sku ILIKE '%X%' OR batch_number ILIKE '%X%' LIMIT 10;

Q: Commandes en retard
SQL: SELECT reference, batch_number, sku, status, planned_eta, CURRENT_DATE - planned_eta as jours_retard, customer FROM shipments WHERE planned_eta < CURRENT_DATE AND status NOT ILIKE '%DELIVER%' AND status NOT ILIKE '%FINAL%' ORDER BY jours_retard DESC LIMIT 15;

Q: Aléas actifs / risques météo
SQL: SELECT type, severity, message, impact_days, linked_route FROM alerts WHERE active = true ORDER BY created_at DESC LIMIT 15;

Q: Historique jalons / suivi événements de X
SQL: SELECT e.type, e.timestamp, e.note, s.reference FROM events e JOIN shipments s ON e.shipment_id = s.id WHERE s.reference ILIKE '%X%' OR s.batch_number ILIKE '%X%' ORDER BY e.timestamp DESC LIMIT 20;

Q: Documents / BL / facture pour X
SQL: SELECT d.type, d.filename, d.status, d.uploaded_at, s.reference FROM documents d JOIN shipments s ON d.shipment_id = s.id WHERE s.reference ILIKE '%X%' OR s.batch_number ILIKE '%X%' ORDER BY d.uploaded_at DESC LIMIT 10;

Q: Prochains horaires / schedules transporteurs
SQL: SELECT carrier, pol, pod, mode, etd, eta, transit_time_days, vessel_name FROM carrier_schedules WHERE etd >= CURRENT_DATE ORDER BY etd LIMIT 15;

Q: Statistiques par statut / client
SQL: SELECT status, COUNT(*) as nb, SUM(quantity) as total_qty FROM shipments GROUP BY status ORDER BY nb DESC;

Q: Erreurs API récentes
SQL: SELECT provider, endpoint, status_code, error_message, created_at FROM api_logs WHERE status_code >= 400 OR error_message IS NOT NULL ORDER BY created_at DESC LIMIT 15;
"""

SQL_PROMPT_SUFFIX = """
Q: {question}
SQL:"""

ANSWER_PROMPT = """Tu es un assistant logistique expert. Réponds dans la même langue que la question de l'utilisateur de manière précise et contextuelle.
Base-toi UNIQUEMENT sur les données fournies par la requête SQL.

ANALYSE DU RÉSULTAT "Données":
1. Si le résultat est VIDE ("[]" ou "None") :
   - Question technique (Logs, API, Erreurs système) : Réponds qu'aucune erreur technique n'a été relevée.
   - Question sur des aléas spécifiques (Météo, Grèves, Douane) : Réponds qu'aucun aléa de ce type n'est actif.
   - Question sur les retards : Réponds qu'aucun retard n'est détecté.
   - Question sur une information manquante (MAD, ETA, Navire) : Réponds que cette donnée n'est pas encore renseignée.
   - Recherche spécifique introuvable (Commande, Lot) : Réponds qu'aucune expédition correspondante n'a été trouvée.

2. Si le résultat contient des données :
   - Résume les informations de manière factuelle.
   - Formate les dates en format lisible (ex: 15 janvier 2026).
   - Pour les retards, précise le nombre de jours.

Question: {question}
Données: {result}
Réponse:"""

# Simple in-memory cache for responses (TTL 5 minutes)
import hashlib
import time
from functools import lru_cache

_response_cache = {}
_cache_ttl = 300  # 5 minutes

def _get_cache_key(query: str) -> str:
    """Generate cache key from normalized query"""
    normalized = query.lower().strip()
    return hashlib.md5(normalized.encode()).hexdigest()

def _get_cached_response(query: str):
    """Get cached response if valid"""
    key = _get_cache_key(query)
    if key in _response_cache:
        cached_time, response = _response_cache[key]
        if time.time() - cached_time < _cache_ttl:
            return response
        del _response_cache[key]
    return None

def _set_cached_response(query: str, response: str):
    """Cache a response"""
    key = _get_cache_key(query)
    _response_cache[key] = (time.time(), response)
    # Limit cache size to 100 entries
    if len(_response_cache) > 100:
        oldest_key = min(_response_cache.keys(), key=lambda k: _response_cache[k][0])
        del _response_cache[oldest_key]


class ChatbotEngine:
    def __init__(self, db, user):
        self.user = user
        self.db = SQLDatabase(db_engine, include_tables=["shipments", "events", "alerts", "documents", "carrier_schedules", "api_logs"])
        
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        self.groq_api_key = groq_api_key
        groq_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        self.groq_max_tokens = int(os.getenv("GROQ_MAX_TOKENS", "500"))
        self.fallback_models = [groq_model] + [
            m for m in ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
            if m != groq_model
        ]

        self.llm = self._create_llm(groq_model)
        
        # Customer filtering logic
        # 1. Use allowed_customer if set (highest priority, applies to all roles)
        # 2. Use user.name if role is client (backward compatibility)
        filter_customer = self.user.allowed_customer
        if not filter_customer and self.user.role == "client":
            filter_customer = self.user.name
            
        # Default is_demo to False for production safety
        is_demo = False

        filter_instruction = ""
        if filter_customer and not is_demo:
            # Escape single quotes for SQL safety (e.g. L'Oreal -> L''Oreal)
            safe_customer = filter_customer.replace("'", "''")
            
            # Inject strict filtering instruction with smarter SQL handling
            # TEMP: Force allow L'Oreal and Lancome as requested by user
            filter_instruction = f"""

IMPORTANT: L'utilisateur est restreint au client '{safe_customer}', MAIS autorisé aussi à voir 'L''Oreal' et 'Lancôme'.
Tu DOIS filtrer les résultats pour inclure ces clients.

RÈGLES DE RECHERCHE PRIORITAIRES :
1. Si la recherche contient des chiffres et des lettres (ex: LG791800), c'est probablement un SKU -> cherche d'abord dans la colonne 'sku'.

RÈGLES DE FILTRAGE :
1. Si la requête a déjà une clause WHERE, ajoute "AND (customer ILIKE '%{safe_customer}%' OR customer ILIKE '%L''Oreal%' OR customer ILIKE '%Lancôme%')".
2. Si la requête n'a PAS de clause WHERE, ajoute "WHERE (customer ILIKE '%{safe_customer}%' OR customer ILIKE '%L''Oreal%' OR customer ILIKE '%Lancôme%')".
"""
            
        self.base_sql_prompt = SQL_PROMPT + filter_instruction
        final_prompt = self.base_sql_prompt + SQL_PROMPT_SUFFIX
        
        self.sql_prompt = PromptTemplate.from_template(final_prompt)
        self.answer_prompt = PromptTemplate.from_template(ANSWER_PROMPT)

    def _create_llm(self, model_name: str) -> ChatGroq:
        return ChatGroq(
            api_key=self.groq_api_key,
            model=model_name,
            temperature=0,
            max_tokens=self.groq_max_tokens,
        )
    
    def _validate_sql(self, sql: str) -> tuple[bool, str]:
        """Validate SQL syntax using sqlparse"""
        import sqlparse
        import re
        try:
            parsed = sqlparse.parse(sql)
            if not parsed or not parsed[0].tokens:
                return False, "SQL vide ou invalide"
            
            # Check it's a SELECT statement (security)
            first_token = str(parsed[0].tokens[0]).upper().strip()
            if first_token not in ('SELECT', 'WITH'):
                return False, "Seules les requêtes SELECT sont autorisées"
            
            # Check for dangerous keywords using Regex (whole word only)
            # This prevents False Positives like "created_at" triggering "CREATE"
            sql_upper = sql.upper()
            dangerous = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'TRUNCATE', 'ALTER', 'CREATE']
            
            for keyword in dangerous:
                # \b matches word boundary
                if re.search(r'\b' + keyword + r'\b', sql_upper):
                    return False, f"Mot-clé interdit: {keyword}"
            
            return True, ""
        except Exception as e:
            return False, str(e)
    
    def _clean_sql(self, raw_sql: str) -> str:
        """Clean and extract SQL from LLM response"""
        sql = raw_sql.strip()
        if "```" in sql:
            parts = sql.split("```")
            if len(parts) >= 2:
                sql = parts[1].replace("sql", "").strip()
        sql = sql.split(";")[0] + ";"
        return sql
    
    def _generate_sql(self, query: str, error_context: str = None) -> str:
        """Generate SQL, with optional error context for retry and model fallback"""
        print(f"DEBUG: Generating SQL for query: {query} (context: {error_context})", flush=True)
        if error_context:
            retry_suffix = f"""
La requête précédente a échoué avec l'erreur: {error_context}
Corrige la requête SQL pour la question suivante.

Question: {{question}}
SQL corrigé:"""
            prompt_template = PromptTemplate.from_template(self.base_sql_prompt + retry_suffix)
        else:
            prompt_template = self.sql_prompt
        
        last_exception = None
        for model_name in self.fallback_models:
            try:
                llm = self._create_llm(model_name)
                sql_chain = prompt_template | llm | StrOutputParser()
                raw_sql = sql_chain.invoke({"question": query})
                self.llm = llm  # Remember working model for answer streaming
                print(f"DEBUG: Raw SQL generated ({model_name}): {raw_sql}", flush=True)
                return self._clean_sql(raw_sql)
            except Exception as e:
                print(f"DEBUG: Error in _generate_sql with model {model_name}: {e}", flush=True)
                last_exception = e
        raise last_exception

    def process_stream(self, query: str):
        print(f"DEBUG: Starting process_stream for query: {query}", flush=True)
        try:
            # Check cache first
            cached = _get_cached_response(query)
            if cached:
                print("DEBUG: Returning cached response", flush=True)
                yield cached
                return
            
            # Generate SQL (first attempt)
            print("DEBUG: Attempting to generate SQL...", flush=True)
            sql = self._generate_sql(query)
            print(f"DEBUG: SQL to validate: {sql}", flush=True)
            
            # Validate SQL
            is_valid, validation_error = self._validate_sql(sql)
            if not is_valid:
                print(f"DEBUG: SQL Invalid: {validation_error}. Retrying...", flush=True)
                # Fallback: retry with error context
                sql = self._generate_sql(query, error_context=validation_error)
                is_valid, validation_error = self._validate_sql(sql)
                if not is_valid:
                    msg = f"Impossible de générer une requête valide: {validation_error}"
                    print(f"DEBUG: Failure: {msg}", flush=True)
                    yield msg
                    return
            
            print(f"DEBUG: SQL Validated. Executing: {sql}", flush=True)
            
            # Execute SQL with fallback
            max_retries = 2
            result = None
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    result = QuerySQLDataBaseTool(db=self.db).invoke(sql)
                    print(f"DEBUG: SQL Execution Result (Attempt {attempt+1}): {str(result)[:200]}...", flush=True)
                    break  # Success
                except Exception as e:
                    last_error = str(e)
                    print(f"DEBUG: SQL Exec Error (Attempt {attempt+1}): {last_error}", flush=True)
                    if attempt < max_retries - 1:
                        # Retry with error context
                        sql = self._generate_sql(query, error_context=last_error)
                        is_valid, _ = self._validate_sql(sql)
                        if not is_valid:
                            break
            
            if result is None:
                msg = f"Erreur après {max_retries} tentatives: {last_error}"
                print(f"DEBUG: Final Failure: {msg}", flush=True)
                result = msg
            
            # Generate answer with streaming and model fallback
            print("DEBUG: Generating answer stream...", flush=True)
            full_response = ""
            stream_success = False
            last_stream_err = None
            for model_name in self.fallback_models:
                try:
                    llm = self._create_llm(model_name)
                    answer_chain = self.answer_prompt | llm | StrOutputParser()
                    for chunk in answer_chain.stream({"question": query, "result": result}):
                        yield chunk
                        full_response += chunk
                    stream_success = True
                    print(f"DEBUG: Stream complete ({model_name}). Full response length: {len(full_response)}", flush=True)
                    break
                except Exception as e:
                    print(f"DEBUG: Error during answer streaming with {model_name}: {e}", flush=True)
                    last_stream_err = e
                    if full_response:
                        # Already yielded partial chunks, don't duplicate
                        stream_success = True
                        break
            if not stream_success:
                yield f"Erreur de génération de réponse: {last_stream_err}"
            
            # Cache the full response (only if successful)
            if "Erreur" not in str(result) and full_response:
                _set_cached_response(query, full_response)
                
        except Exception as e:
            print(f"DEBUG: Global process_stream exception: {e}", flush=True)
            import traceback
            traceback.print_exc()
            yield f"Erreur: {str(e)}"
