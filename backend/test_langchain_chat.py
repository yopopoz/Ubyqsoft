
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
        response1 = engine.process(query1)
        print(f"Response: {response1}")
        
        # Test 2: Specific Data Query
        query2 = "Listez les références des 5 derniers shipments."
        print(f"\nQuery: {query2}")
        response2 = engine.process(query2)
        print(f"Response: {response2}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()
        print("\n--- Test Finished ---")

if __name__ == "__main__":
    test_chatbot()
