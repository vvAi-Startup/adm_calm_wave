# CalmWave API - Documentação Completa

## 📋 Visão Geral

A API CalmWave é uma plataforma completa de processamento de áudio com IA, desenvolvida em Flask. Ela fornece endpoints para autenticação, gerenciamento de usuários, processamento de áudio, playlists, estatísticas e administrativos.

**Versão:** 1.0.0  
**Base URL:** `http://localhost:5000/api`

---

## 🔐 Autenticação

Todos os endpoints (exceto registro e login) requerem um token JWT no header:

```
Authorization: Bearer <seu_token_jwt>
```

### Login

**POST** `/auth/login`

Autentica um usuário e retorna um token JWT.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (200):**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "name": "João Silva",
    "email": "user@example.com",
    "active": true,
    "account_type": "free",
    "settings": { ... }
  }
}
```

### Registro

**POST** `/auth/register`

Cria uma nova conta de usuário.

**Request:**
```json
{
  "name": "João Silva",
  "email": "user@example.com",
  "password": "password123",
  "account_type": "free"
}
```

**Response (201):**
Mesma resposta do login

### Perfil Atual

**GET** `/auth/me`

Retorna os dados do usuário autenticado.

**Response (200):**
```json
{
  "id": 1,
  "name": "João Silva",
  "email": "user@example.com",
  ...
}
```

---

## 👥 Gerenciamento de Usuários

### Listar Usuários

**GET** `/users?page=1&per_page=20&search=termo`

Retorna uma lista paginada de usuários.

**Parameters:**
- `page` (int): Página (padrão: 1)
- `per_page` (int): Itens por página (padrão: 20)
- `search` (string): Buscar por nome ou email

**Response (200):**
```json
{
  "users": [...],
  "total": 100,
  "pages": 5,
  "page": 1
}
```

### Obter Usuário

**GET** `/users/{user_id}`

Retorna dados de um usuário específico.

### Atualizar Usuário

**PUT** `/users/{user_id}`

Atualiza informações do usuário.

**Request:**
```json
{
  "name": "Novo Nome",
  "active": true,
  "profile_photo_url": "https://..."
}
```

### Deletar Usuário

**DELETE** `/users/{user_id}`

Desativa um usuário (soft delete).

### Configurações do Usuário

**PUT** `/users/me/settings`

Atualiza configurações pessoais.

**Request:**
```json
{
  "dark_mode": true,
  "notifications_enabled": true,
  "auto_process_audio": true,
  "audio_quality": "high",
  "name": "Novo Nome"
}
```

### Dispositivos

**GET** `/users/me/devices`

Lista todos os dispositivos conectados.

**DELETE** `/users/me/devices/{device_id}`

Remove um dispositivo.

**POST** `/users/me/devices/revoke_all`

Desconecta todos os outros dispositivos.

### Conquistas

**GET** `/users/me/achievements`

Retorna as conquistas do usuário.

**Response (200):**
```json
{
  "achievements": [
    {
      "id": 1,
      "icon": "🎙️",
      "name": "Primeira Gravação",
      "desc": "Gravou o primeiro áudio",
      "earned": true,
      "count": 5
    }
  ]
}
```

---

## 🎵 Gerenciamento de Áudio

### Fazer Upload

**POST** `/audios/upload`

Envia um arquivo de áudio para processamento.

**Request (multipart/form-data):**
- `file`: Arquivo de áudio (WAV, MP3, etc)
- `device_origin` (opcional): Origem do dispositivo (padrão: "Web")

**Response (201):**
```json
{
  "audio": {
    "id": 1,
    "filename": "gravacao.wav",
    "processed": true,
    "processing_time_ms": 1200,
    "transcribed": true,
    "transcription_text": "Transcrição do áudio...",
    ...
  }
}
```

### Listar Áudios

**GET** `/audios?page=1&per_page=20&processed=true&favorite=false`

Lista áudios do usuário autenticado.

**Parameters:**
- `page` (int): Página
- `per_page` (int): Itens por página
- `processed` (bool): Filtrar por processado
- `favorite` (bool): Filtrar por favoritos

### Obter Áudio

**GET** `/audios/{audio_id}`

Retorna informações do áudio.

### Atualizar Áudio

**PUT** `/audios/{audio_id}`

Atualiza informações do áudio.

**Request:**
```json
{
  "favorite": true,
  "playlist_id": 5,
  "transcription_text": "Transcrição editada"
}
```

### Deletar Áudio

**DELETE** `/audios/{audio_id}`

Remove um áudio.

### Reproduzir Áudio

**GET** `/audios/play/{audio_id}?type=processed`

Transmite o arquivo de áudio.

**Parameters:**
- `type` (string): "original" ou "processed" (padrão: "processed")

---

## 📂 Playlists

### Listar Playlists

**GET** `/playlists?page=1&per_page=20`

Lista todas as playlists do usuário.

### Criar Playlist

**POST** `/playlists`

Cria uma nova playlist.

**Request:**
```json
{
  "name": "Minha Playlist",
  "color": "#6FAF9E"
}
```

**Response (201):**
```json
{
  "playlist": {
    "id": 1,
    "name": "Minha Playlist",
    "color": "#6FAF9E",
    "total_audios": 0,
    "created_at": "2024-01-01T00:00:00",
    "order": 0
  }
}
```

### Obter Playlist

**GET** `/playlists/{playlist_id}`

Retorna a playlist com todos os áudios.

**Response (200):**
```json
{
  "playlist": {
    "id": 1,
    "name": "Minha Playlist",
    "audios": [...]
  }
}
```

### Atualizar Playlist

**PUT** `/playlists/{playlist_id}`

Atualiza informações da playlist.

**Request:**
```json
{
  "name": "Nome Atualizado",
  "color": "#FF5733",
  "order": 1
}
```

### Deletar Playlist

**DELETE** `/playlists/{playlist_id}`

Remove a playlist (áudios não são deletados).

### Adicionar Áudio à Playlist

**POST** `/playlists/{playlist_id}/add-audio/{audio_id}`

Adiciona um áudio à playlist.

### Remover Áudio da Playlist

**POST** `/playlists/{playlist_id}/remove-audio/{audio_id}`

Remove um áudio da playlist.

---

## 🔔 Notificações

### Listar Notificações

**GET** `/notifications`

Lista as últimas 20 notificações do usuário.

**Response (200):**
```json
[
  {
    "id": 1,
    "title": "Áudio Processado",
    "message": "Seu áudio foi processado com sucesso",
    "type": "success",
    "is_read": false,
    "created_at": "2024-01-01T00:00:00"
  }
]
```

### Marcar Como Lida

**PUT** `/notifications/{notification_id}/read`

Marca uma notificação como lida.

### Marcar Todas Como Lidas

**PUT** `/notifications/read-all`

Marca todas as notificações do usuário como lidas.

---

## 📊 Estatísticas

### Dashboard

**GET** `/stats/dashboard`

Retorna estatísticas gerais do sistema.

**Response (200):**
```json
{
  "total_audios": 150,
  "total_users": 45,
  "processed_audios": 140,
  "processed_pct": 93.3,
  "recent_audios_week": 12,
  "streaming_sessions": 3,
  "system_status": "Operacional",
  "daily_counts": [
    { "day": "Mon", "count": 5 },
    ...
  ],
  "last_uploads": [...]
}
```

### Analytics

**GET** `/stats/analytics`

Análise detalhada com dados de crescimento.

---

## 👨‍💼 Painel Administrativo

### Credenciais Padrão

**Email:** `admin@calmwave.com`  
**Senha:** `admin123`

> ⚠️ **IMPORTANTE:** Altere essas credenciais após o primeiro acesso!

### Listar Usuários (Admin)

**GET** `/admin/users?page=1&per_page=20&search=termo&account_type=free`

Lista todos os usuários do sistema (apenas admin).

**Parameters:**
- `page` (int): Página
- `per_page` (int): Itens por página
- `search` (string): Buscar por nome ou email
- `account_type` (string): Filtrar por tipo (free, premium, admin)

### Criar Usuário (Admin)

**POST** `/admin/users`

Cria um novo usuário (apenas admin).

**Request:**
```json
{
  "name": "Novo Usuário",
  "email": "novo@example.com",
  "password": "senha123",
  "account_type": "premium"
}
```

### Atualizar Usuário (Admin)

**PUT** `/admin/users/{user_id}`

Atualiza um usuário (apenas admin).

**Request:**
```json
{
  "name": "Novo Nome",
  "account_type": "premium",
  "active": true
}
```

### Deletar Usuário (Admin)

**DELETE** `/admin/users/{user_id}`

Desativa um usuário (apenas admin).

### Relatório Geral

**GET** `/admin/reports/overview`

Retorna um relatório geral do sistema.

**Response (200):**
```json
{
  "users": {
    "total": 100,
    "active": 95,
    "admins": 2,
    "premium": 20,
    "free": 78
  },
  "audios": {
    "total": 500,
    "processed": 480,
    "processed_pct": 96.0,
    "transcribed": 470,
    "favorite": 120
  },
  "metrics": {
    "avg_audios_per_user": 5.26,
    "total_events": 2000,
    "error_events": 10
  },
  "today": {
    "audios": 15,
    "registrations": 3,
    "events": 120
  }
}
```

### Relatório de Usuários

**GET** `/admin/reports/users`

Relatório detalhado sobre usuários.

**Response (200):**
```json
{
  "daily_registrations": [
    { "day": "Mon", "count": 5 },
    ...
  ],
  "top_users": [
    {
      "id": 1,
      "name": "João Silva",
      "email": "joao@example.com",
      "audio_count": 45
    }
  ]
}
```

### Relatório de Áudios

**GET** `/admin/reports/audios`

Relatório detalhado sobre áudios.

**Response (200):**
```json
{
  "daily_uploads": [...],
  "processing": {
    "total_processed": 480,
    "total_processing_time_ms": 576000,
    "avg_processing_time_ms": 1200.0
  },
  "storage": {
    "total_bytes": 1073741824,
    "total_mb": 1024.0,
    "total_gb": 1.0
  }
}
```

### Relatório de Eventos

**GET** `/admin/reports/events?page=1&per_page=50&level=error&event_type=AUDIO_PROCESSING_FAILED`

Logs detalhados de eventos.

**Parameters:**
- `page` (int): Página
- `per_page` (int): Itens por página
- `level` (string): Filtrar por nível (info, warning, error)
- `event_type` (string): Filtrar por tipo de evento

### Enviar Notificação em Broadcast

**POST** `/admin/notifications/broadcast`

Envia uma notificação para todos os usuários.

**Request:**
```json
{
  "title": "Manutenção Programada",
  "message": "O serviço estará indisponível de 02:00 a 04:00",
  "type": "warning"
}
```

### Deletar Notificação

**DELETE** `/admin/notifications/{notification_id}`

Remove uma notificação.

---

## 🔌 WebSocket (Streaming em Tempo Real)

O sistema suporta streaming de áudio em tempo real via WebSocket. Veja `streaming.md` para documentação detalhada.

---

## 📝 Modelos de Dados

### User
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "João Silva",
  "profile_photo_url": "https://...",
  "created_at": "2024-01-01T00:00:00",
  "last_access": "2024-01-05T14:30:00",
  "active": true,
  "account_type": "free",
  "settings": {
    "dark_mode": false,
    "notifications_enabled": true,
    "auto_process_audio": true,
    "audio_quality": "high"
  }
}
```

### Audio
```json
{
  "id": 1,
  "user_id": 1,
  "filename": "gravacao.wav",
  "file_path": "/uploads/gravacao.wav",
  "duration_seconds": 120,
  "size_bytes": 2048000,
  "recorded_at": "2024-01-01T10:00:00",
  "processed": true,
  "processed_path": "/uploads/processed_gravacao.wav",
  "processing_time_ms": 1200,
  "transcribed": true,
  "transcription_text": "Texto da transcrição...",
  "favorite": false,
  "playlist_id": null,
  "device_origin": "Mobile"
}
```

### Playlist
```json
{
  "id": 1,
  "user_id": 1,
  "name": "Minhas Gravações",
  "color": "#6FAF9E",
  "created_at": "2024-01-01T00:00:00",
  "total_audios": 5,
  "order": 0
}
```

### Notification
```json
{
  "id": 1,
  "user_id": 1,
  "title": "Áudio Processado",
  "message": "Seu áudio foi processado com sucesso!",
  "type": "success",
  "is_read": false,
  "created_at": "2024-01-01T12:00:00"
}
```

### Event
```json
{
  "id": 1,
  "user_id": 1,
  "event_type": "AUDIO_UPLOADED",
  "created_at": "2024-01-01T10:00:00",
  "details_json": "{\"filename\": \"gravacao.wav\", \"size\": 2048000}",
  "screen": "audio",
  "level": "info"
}
```

---

## ⚠️ Códigos de Erro

| Código | Descrição |
|--------|-----------|
| 400 | Requisição inválida |
| 401 | Não autorizado / Token inválido |
| 403 | Acesso negado (permissions) |
| 404 | Recurso não encontrado |
| 409 | Conflito (ex: email duplicado) |
| 500 | Erro interno do servidor |

---

## 🚀 Exemplos de Uso

### Exemplo 1: Login e Fazer Upload

```bash
# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'

# Response
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": { ... }
}

# Fazer upload de áudio
curl -X POST http://localhost:5000/api/audios/upload \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -F "file=@audio.wav" \
  -F "device_origin=Mobile"
```

### Exemplo 2: Criar e Gerenciar Playlist

```bash
# Criar playlist
curl -X POST http://localhost:5000/api/playlists \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Gravações do Dia",
    "color": "#FF5733"
  }'

# Adicionar áudio à playlist
curl -X POST http://localhost:5000/api/playlists/1/add-audio/5 \
  -H "Authorization: Bearer TOKEN"

# Obter playlist com áudios
curl -X GET http://localhost:5000/api/playlists/1 \
  -H "Authorization: Bearer TOKEN"
```

### Exemplo 3: Acesso Admin

```bash
# Listar todos os usuários
curl -X GET "http://localhost:5000/api/admin/users?page=1&per_page=50" \
  -H "Authorization: Bearer ADMIN_TOKEN"

# Obter relatório geral
curl -X GET http://localhost:5000/api/admin/reports/overview \
  -H "Authorization: Bearer ADMIN_TOKEN"

# Enviar notificação broadcast
curl -X POST http://localhost:5000/api/admin/notifications/broadcast \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Manutenção Programada",
    "message": "Sistema estará offline",
    "type": "warning"
  }'
```

---

## 📖 Recursos Adicionais

- **Swagger UI:** Acesse `http://localhost:5000/swagger` para visualizar a API interativamente
- **OpenAPI Spec:** Arquivo em `docs/openapi.json`
- **WebSocket:** Veja `streaming.md` para documentação de streaming

---

## 🔄 Tipos de Conta

| Tipo | Limite | Características |
|------|--------|-----------------|
| **Free** | 10 áudios/mês | Upload básico, processamento com IA |
| **Premium** | Ilimitado | Prioridade na fila, armazenamento expandido |
| **Admin** | N/A | Acesso total a relatórios e gerenciamento |

---

## 📞 Suporte

Para dúvidas ou problemas, entre em contato com o time CalmWave.

**Email:** support@calmwave.com

---

**Última atualização:** Março 2024
