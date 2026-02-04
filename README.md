### `README.md` (v6.1 Diamond)

```markdown
# 🕉️ Forja HariKatha v6.1 - Diamond Edition

**Preservação Digital da Vāṇī Vaishnava com Inteligência Artificial.**

A Forja HariKatha é um ecossistema de preservação de alto nível desenhado para transcrever, traduzir e publicar aulas devocionais (Hari-kathā) extraídas de diversas plataformas (YouTube, Facebook, Lives).



---

## 💎 Diferenciais da Versão v6.1 Diamond

### 🧠 Cláusula de Autoridade (Vāṇī-Śuddha)
Diferente de tradutores comuns, a Forja aplica arbitragem semântica. Se o tradutor humano durante a aula cometer um erro, a IA identifica a fala original de Gurudeva (em Hindi, Bengali ou Inglês) e prioriza a fonte original no texto final.

### 💾 Memória Perpétua e Idempotência
Integrada ao **Supabase**, a Forja "lembra" de cada aula processada.
- **Fingerprint SHA-256**: Identifica o DNA do áudio para evitar custos duplicados entre Facebook e YouTube.
- **Fuzzy Match**: Reconhece aulas similares por título e duração.
- **Retomada de Falhas**: Se o processo cair, ele retoma exatamente de onde parou sem gastar tokens extras.

### 🌍 Ecossistema Multilíngue
Gera o "DNA" (texto bruto) uma única vez e ramifica em versões refinadas para **Português, Inglês e Espanhol**, mantendo a transliteração Sânscrita perfeita (IAST).

---

## 🛠️ Stack Tecnológica

* **STT:** Groq (Whisper-v3) - Transcrição ultra-veloz.
* **LLM:** Anthropic (Claude 3.5 Sonnet) - Refino teológico e tradução.
* **Banco de Dados:** Supabase (PostgreSQL) - Persistência e auditoria.
* **Mídia:** yt-dlp & FFmpeg - Ingestão e corte cirúrgico.
* **CMS:** WordPress (REST API) - Entrega final.
* **Automação:** GitHub Actions - Orquestração em nuvem.

---

## 📂 Estrutura de Arquivos

```text
├── vana_orchestrator.py      # Maestro e Gerenciador de Estados
├── src/
│   ├── transcriber.py        # Motor de STT e Fingerprinting
│   ├── editor.py             # Escriba Vaishnava (Refino Teológico)
│   ├── wp_rest_client.py     # Ponte de Entrega WordPress
│   ├── utils/
│   │   └── supabase_client.py # Cliente de Persistência e Idempotência
│   └── database/
│       └── schema.sql        # Definição das tabelas do Banco
├── .github/workflows/
│   └── vana_forja.yml        # Automação CI/CD no GitHub
├── requirements.txt          # Dependências do Sistema
└── .env.example              # Modelo de Configuração

```

---

## 🚀 Como Iniciar

### 1. Preparação do Banco de Dados

Execute o script em `src/database/schema.sql` no SQL Editor do seu **Supabase**.

### 2. Configuração de Variáveis

Renomeie o `.env.example` para `.env` e preencha com suas chaves de API:

* `GROQ_API_KEY`
* `ANTHROPIC_API_KEY`
* `SUPABASE_URL` & `SUPABASE_SERVICE_KEY`
* `WP_URL`, `WP_USER` & `WP_APP_PASS`

### 3. Uso via GitHub Actions

Vá na aba **Actions** do seu repositório, selecione **"🚀 Forja HariKatha"** e preencha:

1. **Source URL**: Link do YouTube ou Facebook.
2. **Post ID**: ID do post que receberá o texto.
3. **Target Lang**: Idioma (pt, en ou es).
4. **Corte Cirúrgico**: Opcional (HH:MM:SS).

---

## ⚖️ Licença e Uso

Este projeto foi desenvolvido para a preservação das glórias de Śrīla Gurudeva. O uso deve ser estritamente devocional e focado na pureza da Vāṇī.

---

**"Gaurāṅga! Tudo o que Gurudeva disse deve ser preservado em sua forma mais pura."**

```

---

### 🏁 Conclusão do Projeto (v6.1 Diamond)

**Marcel, a arquitetura está completa.** Você tem agora:
1.  **Persistência** (Supabase).
2.  **Idempotência** (Proteção contra custos duplicados).
3.  **Multilíngue** (DNA Único).
4.  **Multi-Source** (YT/FB).
5.  **Automação** (GitHub Actions).


```