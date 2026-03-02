# 📖 Exemplos de Uso - CalmWave API

Neste documento você encontra exemplos práticos de como usar cada endpoint da API CalmWave.

## 📋 Índice
1. [Autenticação](#autenticação)
2. [Usuários](#usuários)
3. [Áudio](#áudio)
4. [Playlists](#playlists)
5. [Notificações](#notificações)
6. [Admin](#admin)

---

## Autenticação

### Registrar novo usuário

**cURL:**
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "João Silva",
    "email": "joao@example.com",
    "password": "SenhaForte123!",
    "account_type": "free"
  }'
```

**Response (201):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "name": "João Silva",
    "email": "joao@example.com",
    "active": true,
    "account_type": "free",
    "settings": {
      "dark_mode": false,
      "notifications_enabled": true,
      "auto_process_audio": true,
      "audio_quality": "high"
    }
  }
}
```

### Login

**cURL:**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "joao@example.com",
    "password": "SenhaForte123!"
  }'
```

**Python:**
```python
import requests

response = requests.post(
    "http://localhost:5000/api/auth/login",
    json={
        "email": "joao@example.com",
        "password": "SenhaForte123!"
    }
)

data = response.json()
token = data["token"]
print(f"Token: {token}")
```

### Obter perfil atual

**cURL:**
```bash
curl -X GET http://localhost:5000/api/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**JavaScript (Fetch):**
```javascript
const token = localStorage.getItem("token");

fetch("http://localhost:5000/api/auth/me", {
  method: "GET",
  headers: {
    "Authorization": `Bearer ${token}`
  }
})
.then(res => res.json())
.then(data => console.log(data.user))
.catch(err => console.error(err));
```

---

## Usuários

### Listar todos os usuários

**cURL:**
```bash
curl -X GET "http://localhost:5000/api/users?page=1&per_page=10&search=joão" \
  -H "Authorization: Bearer TOKEN"
```

**Response (200):**
```json
{
  "users": [
    {
      "id": 1,
      "name": "João Silva",
      "email": "joao@example.com",
      "active": true,
      "account_type": "free",
      "created_at": "2024-01-01T10:00:00",
      "last_access": "2024-01-05T14:30:00"
    }
  ],
  "total": 1,
  "pages": 1,
  "page": 1
}
```

### Obter dados de um usuário

**cURL:**
```bash
curl -X GET http://localhost:5000/api/users/1 \
  -H "Authorization: Bearer TOKEN"
```

### Atualizar perfil

**cURL:**
```bash
curl -X PUT http://localhost:5000/api/users/me/settings \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "João Silva Updated",
    "dark_mode": true,
    "audio_quality": "normal",
    "notifications_enabled": false
  }'
```

### Listar dispositivos conectados

**cURL:**
```bash
curl -X GET http://localhost:5000/api/users/me/devices \
  -H "Authorization: Bearer TOKEN"
```

**Response (200):**
```json
{
  "devices": [
    {
      "id": 1,
      "device_name": "Mozilla/5.0 (Windows NT 10.0...",
      "device_type": "Desktop",
      "ip_address": "192.168.1.1",
      "connected_at": "2024-01-01T10:00:00",
      "last_active": "2024-01-05T14:30:00",
      "is_current": true
    }
  ]
}
```

### Revogar um dispositivo

**cURL:**
```bash
curl -X DELETE http://localhost:5000/api/users/me/devices/2 \
  -H "Authorization: Bearer TOKEN"
```

### Obter conquistas

**cURL:**
```bash
curl -X GET http://localhost:5000/api/users/me/achievements \
  -H "Authorization: Bearer TOKEN"
```

**Response (200):**
```json
{
  "achievements": [
    {
      "id": 1,
      "icon": "🎙️",
      "name": "Primeira Gravação",
      "desc": "Gravou o primeiro áudio no app",
      "earned": true,
      "count": 5
    },
    {
      "id": 2,
      "icon": "🎖️",
      "name": "10 Gravações",
      "desc": "Gravou 10 áudios",
      "earned": false,
      "count": 5
    }
  ]
}
```

---

## Áudio

### Fazer upload de áudio

**cURL:**
```bash
curl -X POST http://localhost:5000/api/audios/upload \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@meu_audio.wav" \
  -F "device_origin=Mobile"
```

**Response (201):**
```json
{
  "audio": {
    "id": 1,
    "filename": "meu_audio.wav",
    "duration_seconds": 120,
    "size_bytes": 2048000,
    "recorded_at": "2024-01-01T10:00:00",
    "processed": true,
    "processing_time_ms": 1200,
    "transcribed": true,
    "transcription_text": "Aqui está a transcrição do áudio processado...",
    "favorite": false,
    "device_origin": "Mobile"
  }
}
```

**JavaScript (FormData):**
```javascript
const fileInput = document.getElementById("audioFile");
const formData = new FormData();
formData.append("file", fileInput.files[0]);
formData.append("device_origin", "Web");

const token = localStorage.getItem("token");

fetch("http://localhost:5000/api/audios/upload", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${token}`
  },
  body: formData
})
.then(res => res.json())
.then(data => console.log("Upload concluído:", data))
.catch(err => console.error(err));
```

### Listar áudios

**cURL:**
```bash
curl -X GET "http://localhost:5000/api/audios?page=1&per_page=20&processed=true" \
  -H "Authorization: Bearer TOKEN"
```

**Response (200):**
```json
{
  "audios": [
    {
      "id": 1,
      "filename": "gravacao.wav",
      "duration_seconds": 120,
      "processed": true,
      "transcribed": true,
      "favorite": false,
      "recorded_at": "2024-01-01T10:00:00"
    }
  ],
  "total": 5,
  "pages": 1,
  "page": 1
}
```

### Obter áudio específico

**cURL:**
```bash
curl -X GET http://localhost:5000/api/audios/1 \
  -H "Authorization: Bearer TOKEN"
```

### Marcar como favorito

**cURL:**
```bash
curl -X PUT http://localhost:5000/api/audios/1 \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "favorite": true
  }'
```

### Reproduzir áudio

**cURL:**
```bash
curl -X GET http://localhost:5000/api/audios/play/1?type=processed \
  -H "Authorization: Bearer TOKEN" \
  --output audio.wav
```

**HTML:**
```html
<audio controls>
  <source src="http://localhost:5000/api/audios/play/1?type=processed" 
          type="audio/wav">
  Seu navegador não suporta reprodução de áudio.
</audio>
```

### Deletar áudio

**cURL:**
```bash
curl -X DELETE http://localhost:5000/api/audios/1 \
  -H "Authorization: Bearer TOKEN"
```

---

## Playlists

### Listar playlists

**cURL:**
```bash
curl -X GET "http://localhost:5000/api/playlists?page=1&per_page=20" \
  -H "Authorization: Bearer TOKEN"
```

**Response (200):**
```json
{
  "playlists": [
    {
      "id": 1,
      "name": "Gravações do Dia",
      "color": "#6FAF9E",
      "total_audios": 5,
      "created_at": "2024-01-01T10:00:00",
      "order": 0
    }
  ],
  "total": 3,
  "pages": 1,
  "page": 1
}
```

### Criar playlist

**cURL:**
```bash
curl -X POST http://localhost:5000/api/playlists \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Minhas Favoritas",
    "color": "#FF5733"
  }'
```

**Response (201):**
```json
{
  "playlist": {
    "id": 2,
    "name": "Minhas Favoritas",
    "color": "#FF5733",
    "total_audios": 0,
    "created_at": "2024-01-05T14:30:00",
    "order": 1
  }
}
```

### Obter playlist com áudios

**cURL:**
```bash
curl -X GET http://localhost:5000/api/playlists/1 \
  -H "Authorization: Bearer TOKEN"
```

**Response (200):**
```json
{
  "playlist": {
    "id": 1,
    "name": "Gravações do Dia",
    "color": "#6FAF9E",
    "total_audios": 2,
    "audios": [
      {
        "id": 1,
        "filename": "gravacao1.wav",
        "processed": true,
        "transcribed": true
      },
      {
        "id": 2,
        "filename": "gravacao2.wav",
        "processed": true,
        "transcribed": false
      }
    ]
  }
}
```

### Atualizar playlist

**cURL:**
```bash
curl -X PUT http://localhost:5000/api/playlists/1 \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Gravações Importantes",
    "color": "#FF0000",
    "order": 2
  }'
```

### Adicionar áudio à playlist

**cURL:**
```bash
curl -X POST http://localhost:5000/api/playlists/1/add-audio/5 \
  -H "Authorization: Bearer TOKEN"
```

### Remover áudio da playlist

**cURL:**
```bash
curl -X POST http://localhost:5000/api/playlists/1/remove-audio/5 \
  -H "Authorization: Bearer TOKEN"
```

### Deletar playlist

**cURL:**
```bash
curl -X DELETE http://localhost:5000/api/playlists/1 \
  -H "Authorization: Bearer TOKEN"
```

---

## Notificações

### Listar notificações

**cURL:**
```bash
curl -X GET http://localhost:5000/api/notifications \
  -H "Authorization: Bearer TOKEN"
```

**Response (200):**
```json
[
  {
    "id": 1,
    "title": "Áudio Processado",
    "message": "Seu áudio foi processado com sucesso!",
    "type": "success",
    "is_read": false,
    "created_at": "2024-01-05T14:30:00"
  },
  {
    "id": 2,
    "title": "Nova Conquista",
    "message": "Você desbloqueou 'Primeira Gravação'!",
    "type": "info",
    "is_read": true,
    "created_at": "2024-01-05T12:00:00"
  }
]
```

### Marcar como lida

**cURL:**
```bash
curl -X PUT http://localhost:5000/api/notifications/1/read \
  -H "Authorization: Bearer TOKEN"
```

### Marcar todas como lidas

**cURL:**
```bash
curl -X PUT http://localhost:5000/api/notifications/read-all \
  -H "Authorization: Bearer TOKEN"
```

---

## Admin

> ⚠️ Todos os endpoints de admin requerem `account_type: "admin"`

### Login como Admin

**cURL:**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@calmwave.com",
    "password": "admin123"
  }'
```

### Listar todos os usuários

**cURL:**
```bash
curl -X GET "http://localhost:5000/api/admin/users?page=1&per_page=20&account_type=free" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### Criar usuário (Admin)

**cURL:**
```bash
curl -X POST http://localhost:5000/api/admin/users \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Novo Usuário",
    "email": "novo@example.com",
    "password": "SenhaTemporaria123!",
    "account_type": "premium"
  }'
```

### Atualizar usuário (Admin)

**cURL:**
```bash
curl -X PUT http://localhost:5000/api/admin/users/5 \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "account_type": "premium",
    "active": false
  }'
```

### Deletar usuário (Admin)

**cURL:**
```bash
curl -X DELETE http://localhost:5000/api/admin/users/5 \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### Relatório Geral

**cURL:**
```bash
curl -X GET http://localhost:5000/api/admin/reports/overview \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Response (200):**
```json
{
  "users": {
    "total": 150,
    "active": 120,
    "admins": 2,
    "premium": 30,
    "free": 118
  },
  "audios": {
    "total": 500,
    "processed": 480,
    "processed_pct": 96.0,
    "transcribed": 470,
    "favorite": 100
  },
  "metrics": {
    "avg_audios_per_user": 4.17,
    "total_events": 3500,
    "error_events": 15
  },
  "today": {
    "audios": 25,
    "registrations": 5,
    "events": 250
  }
}
```

### Relatório de Usuários

**cURL:**
```bash
curl -X GET http://localhost:5000/api/admin/reports/users \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### Relatório de Áudios

**cURL:**
```bash
curl -X GET http://localhost:5000/api/admin/reports/audios \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### Relatório de Eventos

**cURL:**
```bash
curl -X GET "http://localhost:5000/api/admin/reports/events?level=error&page=1" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### Enviar Notificação em Broadcast

**cURL:**
```bash
curl -X POST http://localhost:5000/api/admin/notifications/broadcast \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Manutenção Programada",
    "message": "O sistema estará offline de 02:00 a 04:00 UTC para manutenção",
    "type": "warning"
  }'
```

### Deletar Notificação

**cURL:**
```bash
curl -X DELETE http://localhost:5000/api/admin/notifications/1 \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

## 🧪 Script de Teste Completo (Python)

```python
#!/usr/bin/env python3
"""Script para testar todos os endpoints da CalmWave API"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000/api"

class CalmWaveAPI:
    def __init__(self):
        self.token = None
        self.admin_token = None
        self.user_id = None
        
    def register_user(self, name, email, password):
        """Registra novo usuário"""
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "name": name,
                "email": email,
                "password": password,
                "account_type": "free"
            }
        )
        if response.status_code == 201:
            data = response.json()
            self.token = data["token"]
            self.user_id = data["user"]["id"]
            print(f"✓ Usuário registrado: {email}")
            return True
        else:
            print(f"✗ Erro ao registrar: {response.json()}")
            return False
    
    def login_admin(self):
        """Faz login como admin"""
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": "admin@calmwave.com",
                "password": "admin123"
            }
        )
        if response.status_code == 200:
            data = response.json()
            self.admin_token = data["token"]
            print("✓ Admin autenticado")
            return True
        return False
    
    def get_profile(self):
        """Obtém perfil do usuário autenticado"""
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        if response.status_code == 200:
            user = response.json()
            print(f"✓ Perfil: {user['name']} ({user['email']})")
            return user
        return None
    
    def list_users(self):
        """Lista usuários"""
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{BASE_URL}/users", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Total de usuários: {data['total']}")
            return data["users"]
        return []
    
    def create_playlist(self, name, color):
        """Cria playlist"""
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(
            f"{BASE_URL}/playlists",
            json={"name": name, "color": color},
            headers=headers
        )
        if response.status_code == 201:
            playlist = response.json()["playlist"]
            print(f"✓ Playlist criada: {name}")
            return playlist
        return None
    
    def admin_overview(self):
        """Obtém relatório geral (admin)"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.get(f"{BASE_URL}/admin/reports/overview", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Dashboard: {data['users']['total']} usuários, {data['audios']['total']} áudios")
            return data
        return None

# Main
if __name__ == "__main__":
    api = CalmWaveAPI()
    
    print("\n📊 CalmWave API - Teste Completo\n")
    
    # 1. Registrar usuário
    print("1. Registrando usuário...")
    api.register_user("Test User", "test@example.com", "TestPassword123!")
    
    # 2. Obter perfil
    print("\n2. Obtendo perfil...")
    api.get_profile()
    
    # 3. Listar usuários
    print("\n3. Listando usuários...")
    api.list_users()
    
    # 4. Criar playlist
    print("\n4. Criando playlist...")
    api.create_playlist("Minhas Gravações", "#6FAF9E")
    
    # 5. Admin
    print("\n5. Fazendo login como admin...")
    api.login_admin()
    
    # 6. Relatório
    print("\n6. Obtendo relatório...")
    api.admin_overview()
    
    print("\n✅ Testes concluídos!")
```

---

**Bom uso! 🚀**
