# 🌊 CalmWave

O **CalmWave** é uma aplicação completa de inteligência de áudio. Ela foca na captação, processo de **remoção de ruídos via inteligência artificial** (`best_denoiser_model.pth`), transcrição automatizada textual e análise de dados das gravações. O sistema possui um robusto banco de dados (Supabase/PostgreSQL) e um painel analítico em tempo real.

O projeto está dividido em dois módulos principais:

1. **Back-End API** (`back-end/`): Escrito em Python utilizando Flask, Supabase (banco de dados PostgreSQL), JWT para autenticação e dependências de áudio (Pytorch com manipulação de bytes de áudio para denoise e SpeechRecognition para transcrição).
2. **Dashboard Web Front-End** (`web/`): Uma aplicação SPA robusta em Next.js para controle do sistema, ouvir ondas sonoras virtuais em tempo real (Wavesurfer.js), streaming de mídia e painel de analítica visual.

---

## 📦 Estrutura de Pastas e Responsabilidades

* `back-end/`: Contém todo o serviço lógico da API e conexão com o Banco de Dados (Supabase).
  * `app/routes/`: Os endpoints (controllers) do servidor. Tais como usuários (`users.py`), transcrição/áudio (`audios.py`), saúde da API (`health.py`).
  * `app/services/`: Serviço interno que isola o processamento dos áudios e integrações (ex: `audio_processor.py`).
  * `uploads/`: Pasta reservada para o armazenamento temporário de uploads.
* `web/`: Aplicação front-end focada na experiência do usuário. Módulos como páginas para dashboard, autenticação, lista de usuários e player web (`audios`).
  * `app/components/`: Componentes específicos como cabeçalhos (`Header.tsx`), menus laterais (`Sidebar.tsx`) e controle de estado.
  * Servido via Next.js com React e estilização provida pelo TailwindCSS.

---

## 🚀 Como Executar Localmente

### Pré-requisitos
- Python 3.8+ instalado.
- Node.js 18+ instalado (com `npm`).
- Conta e Projeto configurado no [Supabase](https://supabase.com).

### 1️⃣ Iniciando o Back-End (API Flask)

Abra o terminal na raiz e acesse a pasta `back-end`:

```bash
cd back-end

# 1. Crie seu ambiente virtual
python -m venv venv

# 2. Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure o arquivo .env (crie se não existir) com as credenciais dadas pelo Supabase.

# 5. Inicie o servidor Flask
python run.py
```
> O servidor aguardará requisições na porta **http://localhost:5000**

---

### 2️⃣ Iniciando o Painel Web (Front-End)

Em um outro terminal, acesse a pasta `web`:

```bash
cd web

# 1. Instale as dependências:
npm install

# 2. Configure o arquivo .env.local com a URL da API:
# Ex: NEXT_PUBLIC_API_URL=http://localhost:5000

# 3. Rode o servidor de dev:
npm run dev
```
> A aplicação carregará em **http://localhost:3000**

---

## 📚 Documentação das Rotas da API

A API trabalha via requisições REST, rotas protegidas (na maioria) via token JWT inserido no cabeçalho `Authorization: Bearer <token>`.

### 🔑 Auth & Segurança (`/auth`)
- `POST /auth/login` → Autentica com `email` e `password`. Devolve token JWT.
- `POST /auth/register` → Cria um novo usuário.
- `GET /auth/me` → Valida o token e retorna o usuário atual.

### 🎧 Áudio (`/audios`)
- `GET /audios` → Retorna o catálogo de áudios.
- `GET /audios/sync` → Sincronização mobile, acesso `Guest` habilitado sem necessitar de token.
- `POST /audios/upload` → Upload de arquivo, aciona engrenagens de remoção de ruído (denoiser) e transcrição.
- `PUT /audios/<id>` → Atualiza informações do áudio.
- `DELETE /audios/<id>` → Remove o áudio.

### 👥 Usuários (`/users`)
- Atualizar perfil, gerenciar permissões administrativas e listagens.

### 🚑 Healthcheck
- `GET /health` → Rota monitorada externamente que responde pelo uptime, versão do endpoint, e validação de comunicação direta com o Supabase.

---

## 💻 Stack Tecnológica

**Backend**
- Framework: `Flask`
- Banco de Dados: `Supabase` (PostgreSQL)
- Processamento: `PyTorch`, `torchaudio`, `SpeechRecognition`
- Segurança: `Bcrypt`, `PyJWT`

**Frontend**
- Framework React: `Next.js`
- Design e UI: `Tailwind CSS`
- Player Customizado: `wavesurfer.js`