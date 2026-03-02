# 🔧 Guia de Desenvolvimento CalmWave API

## Configuração do Ambiente

### Pré-requisitos
- Python 3.8+
- pip ou conda
- SQLite3 (ou outro banco de dados)
- Git

### Instalação

1. **Clonar o repositório**
```bash
git clone <seu_repo>
cd back-end
```

2. **Criar ambiente virtual**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Instalar dependências**
```bash
pip install -r requirements.txt
```

4. **Variáveis de ambiente**
Crie um arquivo `.env` na raiz do back-end:

```env
# Database
DATABASE_URL=sqlite:///calmwave.db

# JWT
JWT_SECRET_KEY=sua_chave_secreta_aqui

# Flask
FLASK_ENV=development
FLASK_DEBUG=1

# Uploads
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=52428800  # 50MB
```

5. **Executar a aplicação**
```bash
python run.py
```

A API estará disponível em `http://localhost:5000`

---

## 📁 Estrutura do Projeto

```
back-end/
├── app/
│   ├── __init__.py           # Configuração da app
│   ├── models/
│   │   ├── user.py          # Modelo de usuário
│   │   ├── audio.py         # Modelo de áudio
│   │   └── other.py         # Outros modelos
│   ├── routes/
│   │   ├── auth.py          # Autenticação
│   │   ├── users.py         # Gerenciamento de usuários
│   │   ├── audios.py        # Gerenciamento de áudio
│   │   ├── playlists.py     # Gerenciamento de playlists
│   │   ├── notifications.py # Notificações
│   │   ├── events.py        # Logs de eventos
│   │   ├── stats.py         # Estatísticas
│   │   ├── streaming.py     # WebSocket/Streaming
│   │   └── admin.py         # Painel administrativo
│   └── services/
│       └── audio_processor.py # Processamento de áudio
├── docs/
│   ├── README.md            # Este arquivo
│   ├── API.md              # Documentação da API
│   └── openapi.json        # Especificação OpenAPI
├── requirements.txt         # Dependências Python
├── run.py                  # Script de inicialização
└── calmwave.db             # Banco de dados (criado automaticamente)
```

---

## 🏗️ Arquitetura

### Padrão MVC
- **Models** em `app/models/` - Definição de dados
- **Views** em `app/routes/` - Endpoints da API
- **Controllers** integrados nas rotas

### Camadas
```
Cliente (Mobile/Web)
    ↓
Flask API Routes
    ↓
Business Logic (Services)
    ↓
SQLAlchemy Models
    ↓
SQLite Database
```

---

## 🔐 Autenticação e Autorização

### JWT Token
- Gerado em `/auth/login` e `/auth/register`
- Válido indefinidamente (sem expiração)
- Armazenado como `Authorization: Bearer <token>`

### Verificação
```python
from flask_jwt_extended import jwt_required, get_jwt_identity

@route.route("/endpoint", methods=["GET"])
@jwt_required()
def protected_endpoint():
    current_user_id = get_jwt_identity()
    # ...
```

### Admin Check
```python
from app.models.user import User

def is_admin(user_id):
    user = User.query.get(user_id)
    return user and user.account_type == "admin"
```

---

## 📊 Banco de Dados

### Inicializar
```python
from app import create_app, db

app = create_app()
with app.app_context():
    db.create_all()  # Cria todas as tabelas
```

### Migrations (Futuro)
Para migrations futuras, use Alembic:
```bash
pip install flask-migrate
flask db init
flask db migrate -m "Descrição"
flask db upgrade
```

### Seed Data
Admin padrão é criado automaticamente:
- Email: `admin@calmwave.com`
- Senha: `admin123`

---

## 🎯 Adicionando uma Nova Rota

### 1. Criar o modelo (se necessário)
```python
# app/models/novo_modelo.py
from app import db
from datetime import datetime

class NovoModelo(db.Model):
    __tablename__ = "novo_modelo"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    name = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat()
        }
```

### 2. Criar as rotas
```python
# app/routes/novo_modelo.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.novo_modelo import NovoModelo

novo_bp = Blueprint("novo_modelo", __name__)

@novo_bp.route("/", methods=["GET"])
@jwt_required()
def list_items():
    current_user_id = get_jwt_identity()
    items = NovoModelo.query.filter_by(user_id=current_user_id).all()
    return jsonify([i.to_dict() for i in items])

@novo_bp.route("/", methods=["POST"])
@jwt_required()
def create_item():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    item = NovoModelo(
        user_id=current_user_id,
        name=data.get("name")
    )
    db.session.add(item)
    db.session.commit()
    
    return jsonify(item.to_dict()), 201
```

### 3. Registrar o blueprint
```python
# app/__init__.py
from app.routes.novo_modelo import novo_bp

app.register_blueprint(novo_bp, url_prefix="/api/novo-modelo")
```

---

## 🧪 Testando

### Com cURL
```bash
# Criar conta
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Teste",
    "email": "teste@example.com",
    "password": "senha123"
  }'

# Fazer login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "teste@example.com",
    "password": "senha123"
  }'

# Usar o token
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."
curl -X GET http://localhost:5000/api/users/me \
  -H "Authorization: Bearer $TOKEN"
```

### Com Postman
1. Importe `docs/openapi.json`
2. Configure auth no collection
3. Execute requests

### Com Python
```python
import requests

BASE_URL = "http://localhost:5000/api"

# Login
response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "admin@calmwave.com",
    "password": "admin123"
})
token = response.json()["token"]

# Headers
headers = {"Authorization": f"Bearer {token}"}

# Fazer requisição
response = requests.get(f"{BASE_URL}/users", headers=headers)
print(response.json())
```

---

## 🐛 Debugging

### Logs
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Mensagem de debug")
logger.info("Informação")
logger.warning("Aviso")
logger.error("Erro")
```

### Breakpoints no VSCode
1. Adicione breakpoint
2. Execute: `python -m pdb run.py`
3. Use `c` para continuar, `n` para próxima linha

---

## 📦 Deploy

### Com Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### Com Docker
```dockerfile
FROM python:3.9

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]
```

Build e run:
```bash
docker build -t calmwave-api .
docker run -p 5000:5000 -e DATABASE_URL="sqlite:///calmwave.db" calmwave-api
```

---

## 📋 Checklist para Nova Feature

- [ ] Criar modelo(s) em `app/models/`
- [ ] Criar rotas em `app/routes/`
- [ ] Registrar blueprint em `app/__init__.py`
- [ ] Adicionar logging/eventos quando apropriado
- [ ] Testar endpoints com cURL/Postman
- [ ] Atualizar documentação em `docs/`
- [ ] Adicionar ao OpenAPI spec
- [ ] Code review
- [ ] Deploy

---

## 🚨 Boas Práticas

### Validação
```python
# ❌ Ruim
data = request.get_json()
user = User(email=data["email"])

# ✅ Bom
data = request.get_json()
if not data or "email" not in data:
    return jsonify({"error": "Email é obrigatório"}), 400
if User.query.filter_by(email=data["email"]).first():
    return jsonify({"error": "Email já existe"}), 409
```

### Segurança
```python
# Sempre hash de senha
import bcrypt
pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# Nunca exponha dados sensíveis
user.password_hash = "***"  # Não fazer!

# Use JWT para autenticação
# Sempre valide input
```

### Performance
```python
# ❌ N+1 queries
for user in User.query.all():
    print(user.audios)  # Faz query para cada user!

# ✅ Eager loading
for user in User.query.options(db.joinedload(User.audios)):
    print(user.audios)
```

### Tratamento de Erro
```python
try:
    # Operação de banco
    db.session.commit()
except SQLAlchemyError as e:
    db.session.rollback()
    logger.error(f"Database error: {e}")
    return jsonify({"error": "Database error"}), 500
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return jsonify({"error": "Internal server error"}), 500
```

---

## 🔄 Workflow Git

```bash
# Crie uma branch para sua feature
git checkout -b feature/nova-funcionalidade

# Faça commits pequenos e descritivos
git add .
git commit -m "feat: adiciona nova funcionalidade"

# Push e crie pull request
git push origin feature/nova-funcionalidade
```

---

## 📚 Recursos Úteis

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/14/orm/)
- [Flask-JWT-Extended](https://flask-jwt-extended.readthedocs.io/)
- [OpenAPI 3.0 Spec](https://spec.openapis.org/oas/v3.0.3)

---

## 💡 Dicas

1. **Use Python shell interativo:**
   ```bash
   python
   from app import create_app, db
   from app.models.user import User
   app = create_app()
   app.app_context().push()
   # Agora pode usar db e modelos
   ```

2. **Exporte dados rapidamente:**
   ```python
   import json
   users = User.query.limit(10).all()
   print(json.dumps([u.to_dict() for u in users], indent=2))
   ```

3. **Teste seus endpoints via script:**
   ```bash
   python -m pytest tests/
   ```

---

**Bom desenvolvimento! 🚀**

Se tiver dúvidas, consulte a documentação em `API.md`
