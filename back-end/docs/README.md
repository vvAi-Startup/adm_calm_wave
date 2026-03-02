# 📚 Documentação CalmWave API

Bem-vindo à documentação oficial da API CalmWave! Aqui você encontrará tudo que precisa saber para integrar e usar nossa plataforma de processamento de áudio com IA.

## 📁 Arquivos Disponíveis

### 1. **API.md** - Documentação Completa
O arquivo principal com toda a documentação da API, incluindo:
- Autenticação e autorização
- Endpoints de usuários, áudio, playlists
- Painel administrativo
- Exemplos de uso
- Modelos de dados
- Códigos de erro

**Comece por aqui!**

### 2. **openapi.json** - Especificação OpenAPI 3.0
Arquivo de especificação que pode ser usado com ferramentas como:
- Swagger UI
- Postman
- Insomnia
- E outras ferramentas compatíveis com OpenAPI

**Como usar:**
```bash
# Com Swagger UI local
docker run -p 8080:8080 -e SWAGGER_JSON=/openapi.json -v $(pwd)/openapi.json:/openapi.json swaggerapi/swagger-ui

# Ou importe em Postman
# File > Import > Raw text > Cole o conteúdo do openapi.json
```

## 🚀 Começar Rápido

### 1. Autenticação

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@calmwave.com",
    "password": "admin123"
  }'
```

### 2. Listar Usuários

```bash
curl -X GET http://localhost:5000/api/users \
  -H "Authorization: Bearer SEU_TOKEN_JWT"
```

### 3. Fazer Upload de Áudio

```bash
curl -X POST http://localhost:5000/api/audios/upload \
  -H "Authorization: Bearer SEU_TOKEN_JWT" \
  -F "file=@seu_audio.wav"
```

## 🔑 Credenciais Padrão

| Campo | Valor |
|-------|-------|
| Email | admin@calmwave.com |
| Senha | admin123 |

**⚠️ IMPORTANTE:** Altere as credenciais padrão após o primeiro acesso!

## 📊 Estrutura de Rotas

```
/api
├── /auth              # Autenticação (login, registro, perfil)
├── /users             # Gerenciamento de usuários
├── /audios            # Upload e gerenciamento de áudio
├── /playlists         # Gerenciamento de playlists
├── /notifications     # Sistema de notificações
├── /events            # Logs de eventos
├── /stats             # Estatísticas do sistema
├── /streaming         # WebSocket para streaming em tempo real
└── /admin             # Painel administrativo
```

## 🔐 Autenticação

Todos os endpoints (exceto `/auth/login` e `/auth/register`) requerem um token JWT:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 📝 Principais Features

### 👥 Gerenciamento de Usuários
- Registro e login
- Perfil e configurações
- Múltiplos dispositivos
- Sistema de conquistas
- Controle de conta (admin)

### 🎵 Processamento de Áudio
- Upload de áudio
- Processamento com IA (denoising)
- Transcrição automática
- Reprodução sob demanda
- Marcar como favoritos

### 📂 Playlists
- Criar e organizar playlists
- Adicionar/remover áudios
- Reordenar playlists
- Cores personalizadas

### 📊 Estatísticas
- Dashboard de uso
- Analytics detalhados
- Relatórios administrativos
- Logs de eventos

### 🔔 Notificações
- Notificações em tempo real
- Notificações em broadcast (admin)
- Marcação de leitura

### 👨‍💼 Painel Administrativo
- Gerenciamento de usuários
- Relatórios completos
- Monitoramento de sistema
- Broadcast de notificações

## 🛠️ Ferramentas Recomendadas

### Para Testes
- **Postman** - Collection completa disponível
- **Insomnia** - Alternativa ao Postman
- **cURL** - Linha de comando
- **Thunder Client** - Extensão VS Code

### Para Documentação
- **Swagger UI** - Visualizar e testar endpoints
- **ReDoc** - Documentação responsiva
- **Stoplight** - Gerenciamento de API

## 📈 Fluxo de Uso Típico

```
1. Registrar novo usuário
   POST /auth/register
   
2. Fazer login
   POST /auth/login
   → Recebe JWT token
   
3. Fazer upload de áudio
   POST /audios/upload
   → Áudio é processado automaticamente
   
4. Gerenciar áudios
   - GET /audios (listar)
   - PUT /audios/{id} (atualizar)
   - DELETE /audios/{id} (deletar)
   
5. Criar playlists
   POST /playlists
   POST /playlists/{id}/add-audio/{audio_id}
   
6. Visualizar estatísticas
   GET /stats/dashboard
```

## 🔄 WebSocket - Streaming em Tempo Real

O sistema também suporta streaming de áudio em tempo real via WebSocket.

**Endpoint:** `ws://localhost:5000/socket.io/?token=SEU_TOKEN`

Veja documentação detalhada em `streaming.md` (em breve)

## 📞 Rate Limiting

Atualmente sem limite de taxa, mas isso pode ser implementado no futuro.

## 🐛 Relatório de Bugs

Se encontrar um erro ou comportamento inesperado:

1. Verifique a documentação
2. Tente novamente com os dados corretos
3. Se o problema persistir, relatar com:
   - Endpoint afetado
   - Dados enviados
   - Resposta recebida
   - Logs de erro

## 📚 Referências Rápidas

### Tipos de Conta
- `free` - Limite de 10 áudios/mês
- `premium` - Ilimitado
- `admin` - Acesso administrativo

### Qualidade de Áudio
- `low` - 8kHz
- `normal` - 16kHz
- `high` - 44.1kHz

### Níveis de Evento
- `info` - Informação
- `warning` - Aviso
- `error` - Erro

### Tipos de Notificação
- `info` - Informativa
- `success` - Sucesso
- `warning` - Aviso
- `danger` - Perigo/Erro

## 🎯 Roadmap Futuro

- [ ] Stripe integration para pagamentos
- [ ] Machine learning personalization
- [ ] Mobile SDK oficial
- [ ] Rate limiting
- [ ] API webhooks
- [ ] Mais formatos de áudio
- [ ] Processamento em batch
- [ ] Analytics avançados

## 📄 Licença

Veja LICENSE.md para informações completas.

---

**Versão:** 1.0.0  
**Última atualização:** Março 2024  
**Suporte:** support@calmwave.com
