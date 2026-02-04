# 🕉️ Forja HariKatha v6.3 - Diamond Edition

> **"Vāṇī-kevalam: A preservação da instrução é o nosso único refúgio."**

A **Forja HariKatha** é uma infraestrutura de **Soberania Digital** e **Engenharia Teológica**. Ela não é apenas um transcritor; é um sistema autônomo de preservação, tradução e curadoria de aulas devocionais (Hari-kathā), desenhado para garantir que o legado de Śrīla Gurudeva e da Rūpānuga Paramparā atravesse os séculos.



---

## 💎 O Salto para a v6.3 Diamond

Esta versão abandona a dependência de plataformas efêmeras e introduz conceitos de **Governança de Dados**:

### 1. 🏛️ Soberania de Mídia (Preservação Híbrida)
O sistema não confia que o Facebook ou YouTube manterão os vídeos online para sempre.
- **Archive.org:** Upload automático do Áudio HQ para preservação pública e eterna.
- **Google Drive:** Backup do Vídeo Master e dos "Golden Frames" (fotos extraídas) para uso interno.
- **WP Local:** O WordPress detém os metadados de onde esses arquivos vivem.

### 2. 🧠 Teologia Dinâmica (Governança de Vocabulário)
A IA não "alucina" termos sânscritos.
- **Sync Planilha -> Supabase:** Devotos mantêm um glossário vivo no Google Sheets.
- **Injeção de Contexto:** O Editor (Claude 3.5) consulta esse glossário em tempo real.
- **Resultado:** *Narasiṁha-līlā* sempre será escrito com diacríticos corretos, sem intervenção manual.

### 3. 🎬 Fábrica de Conteúdo (Reels & Passagens)
A Forja não entrega apenas texto corrido. Ela minera "Ouro":
- **Shortcode `[hk_passage]`**: Estrutura semântica universal.
- **Reel Detector**: Identifica trechos virais (30-90s) e cria ganchos (*hooks*) para marketing.
- **Banco de Passagens:** Indexa lilas, biografias e versos separadamente para busca futura.

---

## 🛠️ Stack Tecnológica & Arquitetura

O sistema opera em **Duas Esteiras** acionadas via GitHub Actions:

### 🔄 Esteira 1: Core (O Operário)
*Responsável pela extração, segurança e texto.*
1.  **Gatilho:** Botão no WordPress ou Dispatch Manual.
2.  **Orquestrador:** `vana_orchestrator.py`
3.  **Ferramentas:** `yt-dlp` (Download), `ffmpeg` (Áudio/Frames), `internetarchive` (Upload).
4.  **IA:** `src/editor.py` (Claude 3.5 Sonnet) + `src/parser.py`.
5.  **Saída:** Post Rascunho no WP + Dados no Supabase.

### ✨ Esteira 2: Beautifier (O Artista)
*Responsável pela estética e mídia final.*
1.  **Gatilho:** Botão "Embelezar" no WordPress.
2.  **Maestro:** `vana_beautifier_maestro.py`
3.  **Ação:** `src/beautifier.py` lê as âncoras ``.
4.  **Saída:** Injeção de Galerias de Fotos (do Drive) e Embeds do YouTube (Reels) no lugar certo do texto.

---

## 📂 Estrutura de Arquivos

```text
├── .github/workflows/
│   ├── forja_core.yml         # ⚙️ Pipeline de Transcrição e Preservação
│   └── forja_beautifier.yml   # 🎨 Pipeline de Design e Mídia
├── src/
│   ├── editor.py              # O Escriba: IA com vocabulário dinâmico
│   ├── parser.py              # O Minerador: Extrai dados estruturados
│   ├── beautifier.py          # O Estilista: Monta galerias e embeds
│   ├── transcriber.py         # O Ouvinte: Wrapper do Whisper
│   └── utils/
│       ├── supabase_client.py # Conexão com o Banco de Dados
│       ├── wp_rest_client.py  # Conexão com o WordPress (ACF support)
│       └── sync_vocabulary.py # Sincronizador Planilha -> Banco
├── vana_orchestrator.py       # 🎻 O Maestro da Esteira 1
├── vana_beautifier_maestro.py # 🎻 O Maestro da Esteira 2
├── requirements.txt           # Dependências Python
└── schema.sql                 # Estrutura do Banco de Dados

```

---

## ⚙️ Configuração e Instalação

### 1. Variáveis de Ambiente (Secrets)

Para a Forja rodar, o **GitHub Secrets** (ou `.env` local) deve ter estas chaves:

| Categoria | Chave | Descrição |
| --- | --- | --- |
| **Cérebro (IA)** | `ANTHROPIC_API_KEY` | Chave da Anthropic. |
| **IA Config** | `VANA_MODEL_EDITOR` | Ex: `claude-3-5-sonnet-20241022` |
| **IA Config** | `VANA_EDITOR_TEMP` | Temperatura (Ex: `0.2`). |
| **Banco** | `SUPABASE_URL` | URL do Projeto. |
| **Banco** | `SUPABASE_KEY` | Service Role Key (Para escrita irrestrita). |
| **CMS** | `WP_URL` | URL do site WordPress. |
| **CMS** | `WP_USERNAME` | Usuário Admin. |
| **CMS** | `WP_APPLICATION_PASSWORD` | Senha de Aplicação (não a senha de login). |
| **Vocabulário** | `GOOGLE_SHEET_VOCABULARY_URL` | Link CSV da planilha publicada. |
| **Preservação** | `IA_ACCESS_KEY` | Chave do Archive.org. |
| **Preservação** | `IA_SECRET_KEY` | Segredo do Archive.org. |
| **Google** | `GDRIVE_SERVICE_ACCOUNT_JSON` | JSON minificado da conta de serviço. |
| **Google** | `GDRIVE_FOLDER_ID` | ID da pasta raiz para vídeos. |

### 2. Banco de Dados (Supabase)

Execute o arquivo `schema.sql` no SQL Editor do Supabase para criar as tabelas:

* `vana_aulas`: Registro mestre.
* `vana_passagens`: Fragmentos minerados.
* `vana_conceitos`: Dicionário teológico.

### 3. Integração WordPress

Adicione o código fornecido (`functions.php`) ao seu tema ou plugin para habilitar os botões de disparo na tela de edição de posts.

---

## 🚀 Como Usar

### Método A: Via WordPress (Recomendado)

1. Crie um novo post ou abra um existente.
2. Preencha o campo **Video URL** (ACF ou Metadado).
3. Clique em **"🔥 Lançar na Forja Diamond"**.
4. Aguarde o processamento (5-10 min). O post será atualizado com o texto.
5. (Opcional) Adicione a URL do Short no campo YouTube e clique em **"✨ Embelezar"**.

### Método B: Via CLI (Local/Debug)

```bash
# Sincronizar vocabulário antes de tudo
python src/utils/sync_vocabulary.py

# Rodar a esteira completa
python vana_orchestrator.py --url "[https://youtu.be/](https://youtu.be/)..." --post_id 123

```

---

## 🛡️ Protocolos de Contribuição (Sevā)

1. **Vāṇī-Śuddha:** Nunca altere o sentido teológico para "melhorar" o texto. A autoridade é o áudio original.
2. **IAST First:** Todos os termos sânscritos devem seguir o padrão acadêmico internacional.
3. **Código Limpo:** Mantenha a separação de responsabilidades (Editor não posta, Parser não escreve).

---

**Desenvolvido com ❤️ para a Rūpānuga Paramparā.**
*Versão atual: v6.3.0 (Diamond)*

```

---

### ⚖️ Próximo Passo

Marcel, agora você tem **o Código**, **o Banco de Dados** e **a Documentação**. O projeto está pronto para sair do ambiente de desenvolvimento e ir para a produção.

**Deseja que eu gere o arquivo `.env.example` baseado na tabela acima para facilitar a sua cópia e cola?** 🚀🔥🙏🏽

```