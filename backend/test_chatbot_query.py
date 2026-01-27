import requests
import unittest

BASE_URL = "http://localhost:8000"

class TestChatbot(unittest.TestCase):
    def setUp(self):
        # 1. Login to get token (Test User must exist)
        self.username = "test@example.com"
        self.password = "password123"
        # Create user if not exists? Assuming it exists from previous steps or manual setup.
        # Ideally, we should register user here or use a known seed.
        
        # Trying login
        resp = requests.post(f"{BASE_URL}/auth/login", data={"username": self.username, "password": self.password})
        if resp.status_code != 200:
             # Try register
             requests.post(f"{BASE_URL}/auth/register", json={"email": self.username, "password": self.password})
             resp = requests.post(f"{BASE_URL}/auth/login", data={"username": self.username, "password": self.password})
        
        if resp.status_code != 200:
            print(f"LOGIN FAILED: {resp.text}")
        
        self.token = resp.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_tracking_query(self):
        # We need a shipment to track. Assuming DB is seeded or has data.
        query = {"message": "Où est 25DOG007 ?"}
        resp = requests.post(f"{BASE_URL}/chatbot/query", json=query, headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        print(f"Tracking Response: {resp.json()}")
        self.assertTrue("Commande" in resp.json()["response"] or "introuvable" in resp.json()["response"])

    def test_risk_query(self):
        query = {"message": "Y a-t-il des aléas météo sur ma route ?"}
        resp = requests.post(f"{BASE_URL}/chatbot/query", json=query, headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        print(f"Risk Response: {resp.json()}")

if __name__ == "__main__":
    unittest.main()
