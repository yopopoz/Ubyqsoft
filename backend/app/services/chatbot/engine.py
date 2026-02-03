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

    def process(self, query: str) -> str:
        """
        Process the user query using a 3-phase reflection workflow:
        1. Analysis & Translation (NL -> SQL)
        2. Execution (Run SQL)
        3. Synthesis (SQL Result -> NL)
        """
        try:
            # --- Phase 1: Analysis & Translation ---
            # Create a chain that converts the user question into a SQL query
            write_query = create_sql_query_chain(self.llm, self.db)
            
            # --- Phase 2: Execution ---
            # Tool to execute the generated query
            execute_query = QuerySQLDataBaseTool(db=self.db)
            
            # --- Phase 3: Synthesis ---
            # defined strictly to base the answer ONLY on the context (SQL results)
            answer_prompt = PromptTemplate.from_template(
                """Given the following user question, corresponding SQL query, and SQL result, answer the user question.
                
                Question: {question}
                SQL Query: {query}
                SQL Result: {result}
                
                Answer (in French, strictly based on the SQL Result):"""
            )

            # Build the full chain
            # 1. Generate SQL query
            # 2. Execute SQL query
            # 3. Generate final answer
            chain = (
                RunnablePassthrough.assign(query=write_query).assign(
                    result=itemgetter("query") | execute_query
                )
                | answer_prompt
                | self.llm
                | StrOutputParser()
            )

            # Invoke the chain
            response = chain.invoke({"question": query})
            
            # Additional safety/fallback check could go here
            return response

        except Exception as e:
            # Fallback for errors (e.g., LLM offline, bad query)
            print(f"Chatbot Error: {str(e)}")
            return f"Désolé, je ne peux pas traiter votre demande pour le moment. Erreur technique: {str(e)}"
