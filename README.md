# ðŸŒŠ CalmWave

O **CalmWave** Ã© uma aplicaÃ§Ã£o completa de Ã¡udio-intelÃªngencia. Ela foca na captaÃ§Ã£o, processo de **remoÃ§Ã£o de ruÃ­dos via inteligÃªncia artificial** (`best_denoiser_model.pth`), transcriÃ§Ã£o automatizada textual e anÃ¡lise de dados das gravaÃ§Ãµes. O sistema possui um robusto banco de dados e um painel analÃ­tico em tempo real.

O projeto inteiro estÃ¡ dividido em dois mÃ³dulos principais:

1. **Back-End API** (`back-end/`): Escrito em Python utilizando Flask, SQLAlchemy (banco de dados), JWT para autenticaÃ§Ã£o, Socket.IO, e Pytorch com manipulaÃ§Ã£o fÃ­sica dos bytes do Ã¡udio (denoiser) e SpeechRecognition (transcriÃ§Ã£o).
2. **Dashboard Web Front-End** (`web/`): Uma aplicaÃ§Ã£o SPA robusta em Next.js para controle do sistema, ouvintes das ondas sonoras virtuais em tempo real (Wavesurfer.js), streaming de mÃ­dia e painel de analÃ­tica visual.

---

## ðŸ“¦ Estrutura de Pastas e Responsabilidades

* `back-end/`: ContÃ©m todo o serviÃ§o lÃ³gico autÃ´nomo da API e Banco de Dados (SQLite).
  * `app/models/`: Modelos de abstraÃ§Ã£o SQLAlchemy para a criaÃ§Ã£o das tabelas `Users`, `Audios`, `Events`, etc.
  * `app/routes/`: Os endpoints (controllers) do servidor. Tais como usuÃ¡rios (`users.py`), streams (`streaming.py`) e arquivos (`audios.py`).
  * `app/services/`: ServiÃ§o interno que isola o carregamento do modelo de ruÃ­do e transcriÃ§Ã£o (Pytorch e processador).
  * `uploads/`: Pasta virtual reservada para o armazenamento dos arquivos locais (WAV e mÃ­dias limpas).
* `web/`: AplicaÃ§Ã£o front-end focada na experiÃªncia do usuÃ¡rio. MÃ³dulos independentes como pÃ¡ginas para dashboard, autenticaÃ§Ã£o (`login`), lista de usuÃ¡rios (`users`) e player web (`audios`).
  * `app/components/`: Componentes especÃ­ficos como cabeÃ§alhos (`Header.tsx`), menus laterais (`Sidebar.tsx`) e middlewares de rotas privadas (`ProtectedRoute.tsx`).
  * Servido via `Next.js 16.1.6`, com React 19 fluido e estilizaÃ§Ã£o ultra minimalista fornecida pelo TailwindCSS.

---

## ðŸš€ Como Executar Localmente

### PrÃ©-requisitos PadrÃ£o
- Python 3.8+ instalado e disponÃ­vel via `python`.
- Node.js 18+ instalado e gerenciador de pacotes `npm`.

### 1ï¸ âƒ£ Iniciando o Back-End (A API Python Flask)

Abra o terminal na pasta root e acesse a pasta `back-end`:

```bash
cd back-end

# 1. Crie seu ambiente virtual (recomendado)
python -m venv venv

# 2. Ative o ambiente virtual recÃ©m-criado
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Instale as milhares dependÃªncias prontas
pip install -r requirements.txt

# 4. Inicie o servidor Socket.io Flask
python run.py
```
> O servidor da API ficarÃ¡ aguardando contatos na porta e roteamento: **http://localhost:5000**
*(O banco de dados SQLite interno e as rotinas base serÃ£o gerados automaticamente no seu primeiro start).*

**ðŸ”‘ UsuÃ¡rio Administrador PadrÃ£o Criado Via "Seed":**
- **Email:** `admin@calmwave.com`
- **Senha:** `admin123`

---

### 2ï¸ âƒ£ Iniciando o Painel de Gerenciamento da Web (Front-End)

Em um outro terminal de trabalho (para nÃ£o derrubar o backend), acesse a pasta `web`:

```bash
cd web

# 1. Instale os mÃ³dulos pesados do Node.js estÃ¡veis:
npm install

# 2. Rode em ambiente de desenvolvimento (porta web 3000):
npm run dev
```
> O front-end carregarÃ¡ sob demanda os componentes em: **http://localhost:3000**

---

## ðŸ“š DocumentaÃ§Ã£o das Rotas da API (Endpoints)

Na raiz de execuÃ§Ã£o, a API trabalha via verbos REST HTTP, respondendo sob a URL base `/api/...`.
Exceto Ã s rotas de login e register, **todas as demais requisiÃ§Ãµes requerem uma sessÃ£o ativa (Login)**. Isso significa fornecer no header HTTP associado a chave: `Authorization: Bearer <seu_token_aqui>`.

### ðŸ” Auth & SeguranÃ§a (`/api/auth`)
- `POST /api/auth/login` â†’ Autentica um usuÃ¡rio com `email` e `password`. Se o preenchimento for vÃ¡lido devolve um payload assinado `token` via JWT. Ele faz tracking de dispositivo e registro de IP da sessÃ£o pelo Socket.
- `POST /api/auth/register` â†’ Cria um novo cadastro comum em app, onde se exige as chaves `name`, `email` e `password` no JSON. O backend realiza um hash da senha atravÃ©s da biblioteca *Bcrypt*!
- `GET /api/auth/me` â†’ Verificador RÃ¡pido. Se a requisiÃ§Ã£o possuir um token JWT de usuÃ¡rio legÃ­timo ativado, retorna todos os dados do BD dele (sem senhas e caches visÃ­veis).

### ðŸŽ§ TransaÃ§Ãµes de Ãudio (`/api/audios`)
- `GET /api/audios` â†’ Retorna de forma assÃ­ncrona o seu catÃ¡logo prÃ³prio. Suporta os parÃ¢metros *query* (paginado) como: `?page=X`, `?per_page=Y`, `?processed=true` e `?favorite=true`.
- `GET /api/audios/<id>` â†’ Traz os detalhes, tamanho do arquivo e rastreamento de tempo de limpeza (`processing_time_ms`) de uma mÃ­dia Ãºnica gravada.
- `POST /api/audios/upload` â†’ *A Rota Core:* Envia via `multipart/form-data` fisicamente um Ã¡udio pelo campo `file`. O servidor assimila este Ã¡udio, o passa pela engrenagem de **Modelos de IA denoiser** (removendo barulhos extras por tensÃµes) e, por focar na acessibilidade, dispara logo a rotina subjacente text-to-speech `transcribe_audio`.
- `GET /api/audios/play/<id>?type=processed` â†’ Rota exclusiva para reprodutor do painel HTML5 `Wavesurfer.js`! Ela extrai os buffers sob demanda. Use `type=original` caso vocÃª vÃ¡ consumir o som sujo ou cru na pÃ¡gina web.
- `PUT /api/audios/<id>` â†’ Trata pequenas ediÃ§Ãµes pontuais sobre a sessÃ£o de uma gravaÃ§Ã£o (ex. marcar como favorito, trocar tÃ­tulo ou setar ID de uma playlist).
- `DELETE /api/audios/<id>` â†’ Elimina definitivamente do banco SQLite e da pasta de *uploads* todo o trajeto do arquivo fÃ­sico do banco de sessoes.

### ðŸ‘¥ AdministraÃ§Ã£o de Painel & UsuÃ¡rios (`/api/users`)
Rotas desenhadas para atualizar nomes, perfis ou atÃ© administradores ativarem/desativarem contas para suspensÃµes dentro da plataforma analÃ­tica.

### ðŸ“Š Logs e MÃ©tricas em Tempo Real (`/api/events`, `/api/stats`, `/api/streaming`...)
Para o nÃºcleo Dashboard ter painÃ©is atualizÃ¡veis, hÃ¡ endpoints que cruzam dados com Python: Eles observam de usuÃ¡rios ativados na plataforma (MAU / WAU) no intervalo, a tempo total engajado processando mÃ­dia, por regiÃ£o ou em grÃ¡ficos de Pizza (charts em web interface). A aplicaÃ§Ã£o gera rastros contÃ­nuos por mÃ³dulo via log/logs screen com as classes modeladoras de `Events`.

---

## ðŸ’» Tecnologias em AÃ§Ã£o (Stack)

**No Backend (Python 3.8+)**
- API Core: `Flask`, `Flask-RESTless`, e gerenciamento `Flask-SQLAlchemy` (ORM) com BD `SQLite`.
- Tempo Real & CORS: `Flask-SocketIO`, integrador `eventlet`, com suporte estendido Ã  requisiÃ§Ãµes Cross-Origin.
- Engenharia FÃ­sica Som & Machine Learning Ia: Biblioteca neural `PyTorch`, extensÃ£o `torchaudio`. Recortes de trilhas baseados em `pydub`, `soundfile` e transcriÃ§Ãµes atravÃ©s da framework `SpeechRecognition`.
- Algoritmos Base Hashing: `Bcrypt` em pares combinatoriais e `PyJWT` autÃªntico seguro por Token.

**No Frontend Web (`Node` / `Next.js`)**
- Core Roteador Otimizado: `Next.js v16` operando sob um `React v19`.
- GrÃ¡fico e Design Components UI: Baseado totalmente no robusto `Tailwind CSS 4.0` (por pacotes `postcss` na compilaÃ§Ã£o dos layouts).
- Processo de Som/Players Customizado Web: `wavesurfer.js 7.12` para pintura no Canvas das variaÃ§Ãµes de tom, sem dependÃªncia estÃ¡tica.
- ComunicaÃ§Ã£o Servidor InstantÃ¢nea: Interface Websockets com `socket.io-client`.