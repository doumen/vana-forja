**Dandavat Pranams, Marcel.** Aqui está o arquivo **`README.md`** formatado em Markdown puro dentro do bloco de código, para que possas copiar e colar diretamente no teu repositório.

Este documento foi desenhado para servir como o **Manual de Operações** definitivo para qualquer desenvolvedor que assuma o projeto.

---

```markdown
# 🔥 Forja HariKatha v5.9.1

A **Forja HariKatha** é um ecossistema de processamento *stateless* (sem estado) de alta performance, desenhado para converter aulas e palestras teológicas (YouTube/Facebook) em rascunhos editoriais prontos para publicação no WordPress.

O sistema foca em três pilares: **Fidelidade Teológica (IAST)**, **Custo Operacional Zero de Infra** e **Resiliência em Hospedagem Compartilhada (Hostinger)**.

---

## 🏛️ Arquitetura do Sistema

A Forja utiliza o **GitHub Actions (GHA)** como motor de processamento, delegando tarefas pesadas para APIs de última geração.



### Fluxo de Transmutação:
1.  **Ingestão:** Extração de áudio via `yt-dlp`.
2.  **Transcrição (STT):** Motor **Groq Whisper-v3** (processa 1h em ~60s).
3.  **Auditoria Raw:** Validação de densidade de fala e cronologia.
4.  **Refino Editorial:** Aplicação de **IAST** e parágrafos via **Claude 3.5/4.5**.
5.  **Fusão Śāstrica:** Injeção de notas do **Glossário Mestre** (Google Sheets API).
6.  **Entrega Incremental:** Publicação via **PATCH Incremental** para evitar erros 413/504 na Hostinger.

---

## 🛠️ Estrutura de Pastas

```text
vana-forja/
├── src/
│   ├── utils/            # Cache persistente, I/O atômico e Tempo
│   ├── smart_ai_wrapper  # Inteligência multi-provedor e travas de FinOps
│   ├── transcriber       # Músculo de extração e STT
│   ├── editor            # Refino literário com Blindagem Alquímica
│   ├── auditor_raw       # Controle de qualidade de áudio/texto
│   ├── auditor_reparador # Saneamento de tags e normalização
│   ├── merger            # Conexão com Glossário Mestre
│   ├── wp_rest_client    # Entrega resiliente para Hostinger
│   └── notifier          # Alertas via Telegram
├── vana_orchestrator.py  # O Maestro (Entry point do pipeline)
└── .github/workflows/    # Automação do GitHub Actions

```

---

## 🚀 Configuração e Deploy

### 1. Secrets do GitHub (Settings > Secrets > Actions)

Devem ser configuradas as seguintes chaves para o funcionamento do motor:

| Secret | Descrição |
| --- | --- |
| `GROQ_API_KEY` | Chave para transcrição Whisper |
| `ANTHROPIC_API_KEY` | Chave para o Claude (Edição) |
| `WP_BASE_URL` | URL do site (ex: https://www.google.com/search?q=https://site.com) |
| `WP_USER` | Usuário editor do WordPress |
| `WP_APP_PASS` | Senha de Aplicação (Application Password) |
| `GOOGLE_CREDS_JSON` | JSON da Service Account (Google Cloud) |
| `TELEGRAM_BOT_TOKEN` | Token do Bot de Alertas |

### 2. Variáveis de Ambiente (Variables > Actions)

| Variable | Valor Sugerido |
| --- | --- |
| `AI_PROVIDER` | `claude` |
| `BUDGET_DAY_USD` | `5.0` |
| `WP_CPT` | `vana_aula` |
| `GLOSSARIO_SHEET_ID` | ID da Planilha do Google |

---

## ⚡ Operação Manual

A Forja é disparada manualmente através da aba **Actions** no GitHub:

1. Selecione o workflow **🔥 Forja HariKatha v5.9.1**.
2. Clique em **Run workflow**.
3. Preencha os campos obrigatórios:
* **URL:** Link da live ou vídeo.
* **Post ID:** ID do rascunho já criado no WordPress.
* **Publish:** Se `true`, o post será publicado automaticamente ao fim.



---

## 🛡️ Resiliência e FinOps

* **Deduplicação:** O sistema gera um hash SHA-256 do áudio. Se o áudio já foi processado, ele usa o cache e não gasta tokens de IA.
* **Blindagem Alquímica:** Timestamps são protegidos por caracteres `⟦ ⟧` para evitar que a IA os delete ou altere.
* **Throttling WP:** O envio para a Hostinger respeita um tempo de espera (`WP_TPS`) para não ser bloqueado pelo firewall do servidor.

---

### 🙏🏽 Jaya Gurudeva!

*Este projeto visa a preservação eterna das instruções transcendentais através da tecnologia.*

```

---

Marcel, este `README` é a peça final que faltava para o teu repositório estar **pronto para ser entregue**. Ele explica não apenas o "como", mas o "porquê" de cada decisão técnica (como a blindagem e o envio incremental).

**Deseja que eu faça uma última revisão em algum dos módulos Python ou podemos celebrar a conclusão desta arquitetura?** 🚀🔥🙏🏽

```