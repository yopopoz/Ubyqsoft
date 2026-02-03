import os
from langchain_community.llms import Ollama
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter
from ...database import engine as db_engine

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
        self.db = SQLDatabase(db_engine)
        
        # Configure deterministic LLM (Ollama)
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
        self.llm = Ollama(
            base_url=ollama_base_url,
            model="llama3",
            temperature=0  # Force deterministic output
        )

    def process_stream(self, query: str):
        """
        Process the user query using a 3-phase reflection workflow and stream the response:
        1. Analysis & Translation (NL -> SQL)
        2. Execution (Run SQL)
        3. Synthesis (SQL Result -> NL)
        """
        try:
            # --- Phase 1: Analysis & Translation ---
            yield "🔍 Analyse en cours...\n"
            write_query = create_sql_query_chain(self.llm, self.db)
            sql_query = write_query.invoke({"question": query})
            
            # --- Phase 2: Execution ---
            yield "💾 Recherche des données...\n"
            execute_query = QuerySQLDataBaseTool(db=self.db)
            sql_result = execute_query.invoke(sql_query)
            
            # --- Phase 3: Synthesis ---
            answer_prompt = PromptTemplate.from_template(
                """Given the following user question, corresponding SQL query, and SQL result, answer the user question.
                
                Question: {question}
                SQL Query: {query}
                SQL Result: {result}
                
                Answer (in French, strictly based on the SQL Result):"""
            )

            chain = answer_prompt | self.llm | StrOutputParser()
            
            for chunk in chain.stream({
                "question": query,
                "query": sql_query,
                "result": sql_result
            }):
                yield chunk
            
        except Exception as e:
            # Fallback for errors
            print(f"Chatbot Error: {str(e)}")
            yield f"\nDésolé, une erreur est survenue: {str(e)}"
