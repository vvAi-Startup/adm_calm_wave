# 📚 Índice Completo - Documentação CalmWave API

## Sumário da Documentação

Bem-vindo à documentação oficial da API CalmWave! Este documento serve como índice central para todos os arquivos de documentação.

---

## 📂 Estrutura de Arquivos

### 1. **README.md** ⭐ COMECE AQUI
- Visão geral da API
- Credenciais padrão
- Estrutura de rotas rápida
- Links para outras documentações

**Acesso rápido:** [README.md](README.md)

---

### 2. **API.md** - Documentação Principal
A documentação mais completa com:
- ✅ Guia de autenticação
- ✅ Todos os endpoints documentados
- ✅ Modelos de dados
- ✅ Códigos de erro
- ✅ Exemplos de uso básico

**Acesso rápido:** [API.md](API.md)

**Para quem:** Usuários da API, desenvolvedores frontend, integradores

---

### 3. **EXEMPLOS.md** - Exemplos Práticos
Exemplos reais de como usar cada funcionalidade:
- 🔐 Autenticação
- 👥 Usuários
- 🎵 Áudio
- 📂 Playlists
- 🔔 Notificações
- 👨‍💼 Admin
- 🧪 Scripts de teste completos

**Acesso rápido:** [EXEMPLOS.md](EXEMPLOS.md)

**Para quem:** Desenvolvedores que querem aprender na prática

---

### 4. **DEVELOPMENT.md** - Guia de Desenvolvimento
Tudo para quem vai desenvolver a API:
- 🛠️ Setup do ambiente
- 📁 Estrutura do projeto
- 🏗️ Arquitetura
- 🔐 Padrões de autenticação
- 🎯 Como adicionar novas rotas
- 🧪 Testando
- 🐛 Debugging
- 📦 Deploy

**Acesso rápido:** [DEVELOPMENT.md](DEVELOPMENT.md)

**Para quem:** Desenvolvedores backend, mantedores da API

---

### 5. **openapi.json** - Especificação OpenAPI 3.0
Especificação técnica em formato JSON/YAML:
- Pode ser importada em Swagger UI, Postman, Insomnia
- Documentação automática
- Testes integrados

**Acesso rápido:** [openapi.json](openapi.json)

**Para quem:** Ferramentas, integrações automáticas, geradores de código

---

## 🗺️ Mapa de Rotas

```
/api
├── /auth                          # Autenticação
│   ├── POST /register            # Registrar novo usuário
│   ├── POST /login               # Fazer login
│   └── GET /me                   # Obter perfil atual
│
├── /users                         # Usuários
│   ├── GET /                      # Listar usuários
│   ├── GET /{user_id}            # Obter usuário
│   ├── PUT /{user_id}            # Atualizar usuário
│   ├── DELETE /{user_id}         # Deletar usuário
│   ├── PUT /me/settings          # Atualizar configurações
│   ├── GET /me/devices           # Listar dispositivos
│   ├── DELETE /me/devices/{id}   # Revogar dispositivo
│   └── GET /me/achievements      # Obter conquistas
│
├── /audios                        # Áudio
│   ├── POST /upload              # Fazer upload
│   ├── GET /                      # Listar áudios
│   ├── GET /{audio_id}           # Obter áudio
│   ├── PUT /{audio_id}           # Atualizar áudio
│   ├── DELETE /{audio_id}        # Deletar áudio
│   └── GET /play/{audio_id}      # Reproduzir áudio
│
├── /playlists                     # Playlists
│   ├── GET /                      # Listar playlists
│   ├── POST /                     # Criar playlist
│   ├── GET /{id}                 # Obter playlist
│   ├── PUT /{id}                 # Atualizar playlist
│   ├── DELETE /{id}              # Deletar playlist
│   ├── POST /{id}/add-audio/{a}  # Adicionar áudio
│   └── POST /{id}/remove-audio/  # Remover áudio
│
├── /notifications                 # Notificações
│   ├── GET /                      # Listar notificações
│   ├── PUT /{id}/read            # Marcar como lida
│   └── PUT /read-all             # Marcar todas como lidas
│
├── /events                        # Eventos/Logs
│   ├── GET /                      # Listar eventos
│   └── POST /                     # Criar evento
│
├── /stats                         # Estatísticas
│   ├── GET /dashboard            # Dashboard
│   └── GET /analytics            # Analytics detalhados
│
├── /streaming                     # WebSocket (Streaming)
│   └── GET /sessions             # Sessões ativas
│
└── /admin                         # Painel Administrativo
    ├── GET /users                # Listar usuários
    ├── POST /users               # Criar usuário
    ├── PUT /users/{id}           # Atualizar usuário
    ├── DELETE /users/{id}        # Deletar usuário
    ├── GET /reports/overview     # Relatório geral
    ├── GET /reports/users        # Relatório de usuários
    ├── GET /reports/audios       # Relatório de áudios
    ├── GET /reports/events       # Relatório de eventos
    ├── POST /notifications/broadcast # Enviar broadcast
    └── DELETE /notifications/{id}    # Deletar notificação
```

---

## 🚀 Guia Rápido por Caso de Uso

### 📱 Sou Desenvolvedor Mobile/Frontend

**Leia na ordem:**
1. [README.md](README.md) - Entender a API
2. [API.md - Autenticação](API.md#-autenticação) - Como se autenticar
3. [EXEMPLOS.md](EXEMPLOS.md) - Ver exemplos práticos
4. [API.md](API.md) - Consultar endpoints específicos

**Endpoints principais:**
- POST `/auth/register` - Registrar
- POST `/auth/login` - Login
- GET `/auth/me` - Meu perfil
- POST `/audios/upload` - Upload de áudio
- GET `/audios` - Listar áudios
- POST `/playlists` - Criar playlist

---

### 🛠️ Sou Desenvolvedor Backend/API

**Leia na ordem:**
1. [README.md](README.md) - Visão geral
2. [DEVELOPMENT.md](DEVELOPMENT.md) - Setup e arquitetura
3. [API.md - Modelos de Dados](API.md#-modelos-de-dados) - Estrutura de dados
4. [DEVELOPMENT.md - Adicionando Rota](DEVELOPMENT.md#-adicionando-uma-nova-rota) - Como adicionar features

**Ferramentas:**
- Python 3.8+
- Flask
- SQLAlchemy
- JWT para autenticação

---

### 👨‍💼 Sou Administrador

**Leia na ordem:**
1. [README.md](README.md) - Visão geral
2. [API.md - Painel Administrativo](API.md#-painel-administrativo) - Funções admin
3. [EXEMPLOS.md - Admin](EXEMPLOS.md#admin) - Exemplos de operações admin

**Funcionalidades principais:**
- Gerenciar usuários
- Ver relatórios
- Enviar notificações broadcast
- Monitorar sistema

---

### 🧪 Estou Testando a API

**Leia na ordem:**
1. [API.md - Códigos de Erro](API.md#️-códigos-de-erro) - Entender respostas
2. [EXEMPLOS.md](EXEMPLOS.md) - Exemplos com cURL
3. [openapi.json](openapi.json) - Importar em Postman

**Ferramentas recomendadas:**
- Postman
- Insomnia
- Thunder Client (VS Code)

---

## 📊 Cheatsheet - Comandos Rápidos

### Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@calmwave.com","password":"admin123"}'
```

### Upload de Áudio
```bash
curl -X POST http://localhost:5000/api/audios/upload \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@audio.wav"
```

### Listar Usuários (Admin)
```bash
curl -X GET http://localhost:5000/api/admin/users \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### Criar Playlist
```bash
curl -X POST http://localhost:5000/api/playlists \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Minha Playlist","color":"#6FAF9E"}'
```

---

## 🔑 Informações Importantes

### Credenciais Padrão
| Campo | Valor |
|-------|-------|
| Email Admin | admin@calmwave.com |
| Senha Admin | admin123 |

**⚠️ ALTERE APÓS PRIMEIRO ACESSO!**

### Base URL
- **Desenvolvimento:** `http://localhost:5000/api`
- **Produção:** Configure conforme necessário

### Autenticação
Todos os endpoints (exceto login e registro) requerem:
```
Authorization: Bearer <seu_token_jwt>
```

---

## 🎓 Glossário

| Termo | Significado |
|-------|-----------|
| **JWT** | JSON Web Token - Autenticação segura |
| **Bearer Token** | Token JWT enviado no header Authorization |
| **OpenAPI** | Especificação padrão para documentar APIs |
| **REST** | Architectural style para APIs |
| **Endpoint** | URL + Método HTTP (ex: GET /api/users) |
| **Payload** | Dados enviados no body da requisição |
| **Response** | Resposta do servidor |

---

## 📞 Suporte e Contato

- **Email:** support@calmwave.com
- **Issues:** Reporte via issues do GitHub
- **Documentação:** Veja este diretório
- **Comunidade:** Discord (em breve)

---

## 🔄 Changelog

### Versão 1.0.0 (Março 2024)
- ✅ API completa funcional
- ✅ Endpoints de usuário
- ✅ Upload e processamento de áudio
- ✅ Sistema de playlists
- ✅ Painel administrativo
- ✅ Estatísticas e relatórios
- ✅ Documentação completa

---

## 🎯 Links Úteis

- [Documentação Flask](https://flask.palletsprojects.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [JWT Auth](https://flask-jwt-extended.readthedocs.io/)
- [OpenAPI Spec](https://spec.openapis.org/oas/v3.0.3)
- [Postman](https://www.postman.com/)
- [Insomnia](https://insomnia.rest/)

---

**Última atualização:** Março 2024  
**Versão:** 1.0.0  
**Status:** ✅ Produção
