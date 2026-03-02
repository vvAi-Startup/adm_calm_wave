import json

def test_missing_route_returns_404(client):
    """Testa tratamento de erro global para rotas inexistentes"""
    response = client.get('/api/rota-que-nao-existe')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == 'Recurso não encontrado'

def test_login_schema_validation(client):
    """Testa o schema de validação da rota de login"""
    # Payload vazio, deve bater no marshmallow validation
    response = client.post('/api/auth/login', json={})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'messages' in data

def test_register_schema_validation(client):
    """Testa o schema de validação na rota de registro"""
    response = client.post('/api/auth/register', json={"email": "not-an-email", "password": "123"}) # senha muito curta
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'email' in data['messages']
    assert 'password' in data['messages']
