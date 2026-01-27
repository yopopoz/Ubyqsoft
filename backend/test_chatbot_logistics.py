import requests
import unittest

BASE_URL = "http://localhost:8000"

class TestChatbotLogistics(unittest.TestCase):
    def setUp(self):
        self.username = "test@example.com"
        self.password = "password123"
        
        resp = requests.post(f"{BASE_URL}/auth/login", data={"username": self.username, "password": self.password})
        if resp.status_code != 200:
            print(f"LOGIN FAILED: {resp.text}")
            self.token = None
        else:
            self.token = resp.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def _query(self, msg):
        resp = requests.post(f"{BASE_URL}/chatbot/query", json={"message": msg}, headers=self.headers)
        print(f"Q: {msg}")
        print(f"A: {resp.json().get('response', resp.text)[:200]}")
        print("-" * 50)
        return resp

    def test_tracking(self):
        resp = self._query("Où est 25DOG007 ?")
        self.assertEqual(resp.status_code, 200)

    def test_first_fortnight(self):
        resp = self._query("Commandes première quinzaine janvier")
        self.assertEqual(resp.status_code, 200)

    def test_delays(self):
        resp = self._query("Commandes en retard ce mois-ci")
        self.assertEqual(resp.status_code, 200)

    def test_port_arrivals(self):
        resp = self._query("Arrivées port sous 7 jours")
        self.assertEqual(resp.status_code, 200)

    def test_pickup_planning(self):
        resp = self._query("Planning pick-up EXW")
        self.assertEqual(resp.status_code, 200)

    def test_ddp_milestones(self):
        resp = self._query("Étapes DDP standard")
        self.assertEqual(resp.status_code, 200)

    def test_customs(self):
        resp = self._query("Séquence douanes DDP maritime")
        self.assertEqual(resp.status_code, 200)

    def test_alerts(self):
        resp = self._query("Aléas météo actuels")
        self.assertEqual(resp.status_code, 200)

    def test_exw_ddp_status(self):
        resp = self._query("Statut EXW DDP pour 25DOG007")
        self.assertEqual(resp.status_code, 200)

    def test_schedules(self):
        resp = self._query("Schedules maritimes janvier")
        self.assertEqual(resp.status_code, 200)

    def test_air_urgent(self):
        resp = self._query("Commandes urgentes aérien")
        self.assertEqual(resp.status_code, 200)

    def test_in_transit(self):
        resp = self._query("DDP en transit")
        self.assertEqual(resp.status_code, 200)

if __name__ == "__main__":
    unittest.main(verbosity=2)
