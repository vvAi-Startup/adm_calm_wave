# 🚀 Início Rápido - CalmWave API

## ⚡ 5 Minutos para Começar

### 1️⃣ Instalar Dependências
```bash
cd back-end
pip install -r requirements.txt
```

### 2️⃣ Executar o Servidor
```bash
python run.py
```

Você verá:
```
 * Running on http://localhost:5000
```

### 3️⃣ Fazer Login (Admin Padrão)
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@calmwave.com",
    "password": "admin123"
  }'
```

### 4️⃣ Copiar o Token Retornado
O comando acima retornará:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": { ... }
}
```

### 5️⃣ Fazer Sua Primeira Requisição
```bash
TOKEN="seu_token_aqui"

curl -X GET http://localhost:5000/api/users \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📚 Documentação Rápida

| Documento | Propósito | Para Quem |
|-----------|----------|----------|
| **[docs/README.md](docs/README.md)** | Visão geral da API | Todos |
| **[docs/API.md](docs/API.md)** | Documentação completa | Desenvolvedores |
| **[docs/EXEMPLOS.md](docs/EXEMPLOS.md)** | Exemplos práticos | Aprendizado |
| **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)** | Guia de desenvolvimento | Contribuidores |
| **[docs/INDEX.md](docs/INDEX.md)** | Índice da documentação | Navegação |

---

## 🔑 Credenciais Padrão

```
Email: admin@calmwave.com
Senha: admin123
```

**⚠️ Altere após o primeiro acesso!**

---

## 📍 Principais Endpoints

### Autenticação
```
POST   /api/auth/register         # Registrar novo usuário
POST   /api/auth/login            # Fazer login
GET    /api/auth/me               # Perfil atual
```

### Usuários
```
GET    /api/users                 # Listar usuários
PUT    /api/users/me/settings     # Atualizar configurações
GET    /api/users/me/devices      # Meus dispositivos
GET    /api/users/me/achievements # Minhas conquistas
```

### Áudio
```
POST   /api/audios/upload         # Upload de áudio
GET    /api/audios                # Listar meus áudios
GET    /api/audios/play/{id}      # Reproduzir áudio
```

### Playlists
```
POST   /api/playlists             # Criar playlist
GET    /api/playlists             # Listar playlists
POST   /api/playlists/{id}/add-audio/{audio_id}  # Adicionar áudio
```

### Admin
```
GET    /api/admin/users                      # Listar todos os usuários
POST   /api/admin/users                      # Criar usuário
GET    /api/admin/reports/overview           # Relatório geral
GET    /api/admin/reports/users              # Relatório de usuários
GET    /api/admin/reports/audios             # Relatório de áudios
GET    /api/admin/reports/events             # Logs de eventos
```

---

## 💡 Exemplos Rápidos

### Criar um Novo Usuário
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "João Silva",
    "email": "joao@example.com",
    "password": "Senha123!",
    "account_type": "free"
  }'
```

### Fazer Upload de Áudio
```bash
TOKEN="seu_token_aqui"

curl -X POST http://localhost:5000/api/audios/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@meu_audio.wav"
```

### Criar Playlist
```bash
TOKEN="seu_token_aqui"

curl -X POST http://localhost:5000/api/playlists \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Minha Playlist",
    "color": "#6FAF9E"
  }'
```

### Obter Relatório (Admin)
```bash
ADMIN_TOKEN="seu_token_admin_aqui"

curl -X GET http://localhost:5000/api/admin/reports/overview \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## 📊 Visão Geral da API

- **Total de Endpoints:** 46
- **Categorias:** 9 (auth, users, audios, playlists, notifications, events, stats, streaming, admin)
- **Autenticação:** JWT Bearer Token
- **Banco de Dados:** SQLite
- **Framework:** Flask + SQLAlchemy

---

## 🛠️ Troubleshooting

### Erro: `ModuleNotFoundError: No module named 'flask'`
```bash
pip install -r requirements.txt
```

### Erro: `Address already in use`
A porta 5000 está em uso. Use outra porta:
```bash
python -c "from app import create_app, socketio; app = create_app(); socketio.run(app, port=8000)"
```

### Erro: `JWT token is invalid`
Certifique-se de que:
- O token está no header: `Authorization: Bearer TOKEN`
- O token não expirou
- A chave secreta JWT está correta

---

## 🔄 Próximas Etapas

1. **Explorar a documentação**
   - Leia `docs/API.md` para entender todos os endpoints
   - Confira `docs/EXEMPLOS.md` para ver mais exemplos

2. **Testar com Ferramentas**
   - Postman: Importe `docs/openapi.json`
   - Insomnia: Importe `docs/openapi.json`
   - cURL: Use exemplos acima

3. **Começar a Desenvolver**
   - Se for contribuir, leia `docs/DEVELOPMENT.md`
   - Entenda a estrutura em `app/`
   - Adicione suas features

4. **Deploy**
   - Configure `.env` com variáveis de produção
   - Use Gunicorn em produção
   - Configure banco de dados real (PostgreSQL)

---

## 📞 Suporte

- **Documentação:** Veja pasta `docs/`
- **Exemplos:** `docs/EXEMPLOS.md`
- **Desenvolvimento:** `docs/DEVELOPMENT.md`
- **Email:** support@calmwave.com

---

## ✅ Checklist de Configuração

- [ ] Python 3.8+ instalado
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Servidor rodando (`python run.py`)
- [ ] Conseguiu fazer login com admin padrão
- [ ] Conseguiu fazer uma requisição com o token

Se todos os itens acima estão marcados, você está pronto para usar a API! 🎉

---

**Bem-vindo ao CalmWave! 🚀**
