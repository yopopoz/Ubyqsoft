import requests
import json

# Login
try:
    r = requests.post('http://localhost:8000/auth/login', data={'username': 'test@example.com', 'password': 'password123'})
    token = r.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    print("Login successful")
except Exception as e:
    print(f"Login failed: {e}")
    exit(1)

# Test queries
queries = [
    'Où est 25DOG007 ?',
    'Commandes première quinzaine janvier',
    'Commandes en retard ce mois-ci', # This one triggered the error before
    'Arrivées port sous 7 jours',
    'Séquence douanes DDP maritime',
]

for q in queries:
    try:
        resp = requests.post('http://localhost:8000/chatbot/query', json={'message': q}, headers=headers)
        if resp.status_code == 200:
            print(f"[{q}] -> OK")
            # print(resp.json()['response'])
        else:
            print(f"[{q}] -> ERROR {resp.status_code}")
            print(resp.text)
    except Exception as e:
        print(f"[{q}] -> EXCEPTION {e}")
