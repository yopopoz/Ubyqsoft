
import sys
import os
# Add the parent directory to sys.path to allow importing app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.chatbot.engine import ChatbotEngine
from app.database import SessionLocal
from app.models import User

# Mock user for testing
mock_user = User(email="test@example.com", is_active=True)

def test_chatbot():
    print("--- Starting Chatbot Test ---")
    db = SessionLocal()
    try:
        engine = ChatbotEngine(db, mock_user)
        
        # Test 1: Simple Count Query
        query1 = "Combien de shipments y a-t-il au total ?"
        print(f"\nQuery: {query1}")
        print("Response: ", end="", flush=True)
        for chunk in engine.process_stream(query1):
            print(chunk, end="", flush=True)
        print()
        
        # Test 2: Specific Data Query
        query2 = "Listez les références des 5 derniers shipments."
        print(f"\nQuery: {query2}")
        print("Response: ", end="", flush=True)
        for chunk in engine.process_stream(query2):
            print(chunk, end="", flush=True)
        print()
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()
        print("\n--- Test Finished ---")

if __name__ == "__main__":
    test_chatbot()
