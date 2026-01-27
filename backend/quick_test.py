import requests

# Login
r = requests.post('http://localhost:8000/auth/login', data={'username': 'test@example.com', 'password': 'password123'})
token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Test queries
queries = [
    'Où est 25DOG007 ?',
    'Commandes première quinzaine janvier',
    'Arrivées port sous 7 jours',
    'Étapes DDP standard',
    'Commandes en retard ce mois-ci',
    'Planning pick-up EXW',
    'Aléas météo actuels',
    'Statut EXW DDP pour 25DOG007',
    'DDP en transit'
]
for q in queries:
    resp = requests.post('http://localhost:8000/chatbot/query', json={'message': q}, headers=headers)
    print(f'Q: {q}')
    answer = resp.json().get('response', resp.text)
    print(f'A: {answer[:200]}...' if len(answer) > 200 else f'A: {answer}')
    print('-'*50)
