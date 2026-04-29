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

def test_health_check(client):
    """Testa se a rota health retorna 200 (se config banco OK) ou gracefully degrada (503/etc)"""
    response = client.get('/api/health')
    assert response.status_code in [200, 503]
    data = json.loads(response.data)
    assert 'status' in data
    assert 'uptime_seconds' in data

def test_protected_route_without_token(client):
    """Testa se rota protegida (ex: users list admin) bloqueia requisições sem JWT"""
    response = client.get('/api/admin/users') 
    # flask_jwt_extended retorna 401 quando o header Authorization não existe
    assert response.status_code == 401
    
    # Valida payload de erro retornado pela lib de JWT
    data = json.loads(response.data)
    assert "msg" in data or "error" in data

def test_audios_public_endpoint(client):
    """Verifica comportamento do endpoint de audios (sem auth)"""
    response = client.get('/api/audios/')
    # Como não envia token, e se a rota exigir auth, recusa. Senão mostra lista.
    assert response.status_code in [200, 401]

def test_malformed_json_returns_400(client):
    """Testa se envio de corpo não JSON para aplicação de rotas JSON devolve Bad Request em login"""
    response = client.post('/api/auth/login', data="isso não é json", content_type='application/json')
    assert response.status_code == 400

def test_unknown_method_on_endpoint(client):
    """Testa method not allowed para Health, que aceita só GET"""
    response = client.post('/api/health')
    assert response.status_code == 405

