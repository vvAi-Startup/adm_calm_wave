# Pipeline de Deploy

```mermaid
flowchart TD
    DEV([👨‍💻 Developer\npush / PR])

    DEV --> GHA[GitHub Actions\ntests.yml]

    GHA --> TB[Testes Backend\npytest – ./back-end]
    TB -->|falhou| FAIL([❌ Pipeline bloqueado])

    TB -->|passou| SPLIT{ }

    SPLIT --> RENDER[Deploy → Render\n./back-end]
    SPLIT --> VERCEL[Deploy → Vercel\n./web]

    RENDER --> RENDER_OK([✅ API online])
    VERCEL --> VERCEL_OK([✅ Frontend online])
```

## Resumo

| Etapa | Ferramenta | Pasta |
|---|---|---|
| Testes | GitHub Actions (`tests.yml`) | `./back-end` |
| Backend | Render | `./back-end` |
| Frontend | Vercel | `./web` |
