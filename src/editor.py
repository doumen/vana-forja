# -*- coding: utf-8 -*-
"""
Editor Vaishnava v6.3 Diamond – O Escriba de Shortcodes
- Desacoplamento Total: Modelos e Idiomas via Ambiente/Config.
- Vocabulário Dinâmico: Sincronizado via Supabase.
- Fábrica de Reels: Identificação de trechos virais.
- Taxonomia Universal: Uso do container [hk_passage].
"""

import os
import re
import json
from pathlib import Path
from typing import Optional, Dict
import anthropic

class VanaEditor:
    def __init__(self, dicionario: Optional[Dict] = None):
        """
        Inicia o Editor com configurações externas.
        """
        # 1. Configurações de IA (Fora do Código)
        self.model = os.getenv("VANA_MODEL_EDITOR", "claude-3-5-sonnet-20241022")
        self.temperature = float(os.getenv("VANA_EDITOR_TEMP", "0.2"))
        
        # 2. Inicialização do Cliente
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("❌ ANTHROPIC_API_KEY não configurada no ambiente.")
        self.client = anthropic.Anthropic(api_key=api_key)

        # 3. Vocabulário da Sangha (Vindo do Supabase)
        self.dicionario = dicionario or {}

    def _get_idioma_legivel(self, lang_code: str) -> str:
        """Busca o nome do idioma em um config externo ou env."""
        # Podemos carregar de um languages.json ou de uma env string
        lang_config = os.getenv("VANA_LANG_MAP", '{"pt":"Português","en":"English","es":"Español"}')
        try:
            mapping = json.loads(lang_config)
            return mapping.get(lang_code, "Português")
        except json.JSONDecodeError:
            return "Português"

    def _build_system_prompt(self, target_lang: str) -> str:
        """Constrói o cérebro teológico da IA."""
        idioma = self._get_idioma_legivel(target_lang)
        
        # Injeção do Vocabulário IAST Dinâmico
        vocab_str = "\n".join([f"- {slug}: Usar termo '{iast}'" for slug, iast in self.dicionario.items()])

        return f"""
Você é o Editor-Chefe do Projeto Vana, especialista na preservação da Hari-kathā.
Sua missão é refinar a transcrição para {idioma}, garantindo a pureza (Vāṇī-Śuddha).

### 🛡️ 1. CLÁUSULA DE AUTORIDADE E IAST
Use estritamente estes termos oficiais da nossa Sangha:
{vocab_str}

### 💎 2. TAXONOMIA DIAMOND [hk_passage]
Encapsule "pérolas" no shortcode universal. Não use shortcodes antigos.
Format: [hk_passage type="..." reel="true|false" hook="..."]

Tipos Permitidos:
- `lila`: Passatempos de Kṛṣṇa e Suas expansões.
- `biografia`: Vidas e glórias dos Ācāryas e Vaishnavas.
- `tattva`: Filosofia profunda e conclusões teológicas.
- `verso`: Slokas citados (use [original] e [explicacao] internamente).
- `cancao`: Letras de Kirtans e Bhajans.
- `instrucao`: Ordens de Sādhana e conselhos de Gurudeva.
- `historia`: Parábolas, anedotas e histórias didáticas.

### 🎥 3. FÁBRICA DE REELS
- Marque reel="true" em até 3 trechos de alto impacto (30-90s).
- Defina o `hook` com uma frase curta e viral para o título do vídeo.

### 📸 4. ESTRUTURA E DESIGN
- Insira após o primeiro parágrafo e ao final.
- Mantenha os timestamps protegidos ⟦HH:MM:SS⟧ no início dos parágrafos.
"""

    def _apply_timestamp_guard(self, text: str) -> str:
        """Protege os timestamps [HH:MM:SS] convertendo-os em ⟦HH:MM:SS⟧."""
        pattern = r"\[(\d{1,2}:\d{2}:\d{2})\]"
        return re.sub(pattern, r"⟦\1⟧", text)

    def refine(self, raw_text: str, target_lang: str = "pt", metadata: Optional[Dict] = None) -> Dict:
        """Executa o refino editorial completo."""
        print(f"✨ [VanaEditor] Processando em {target_lang} com o modelo {self.model}...")
        
        # 1. Blindagem de Dados
        guarded_text = self._apply_timestamp_guard(raw_text)
        archive_url = metadata.get("archive_url", "#") if metadata else "#"

        # 2. Preparação do Prompt
        sys_prompt = self._build_system_prompt(target_lang)
        user_input = f"Edite a transcrição abaixo para o Padrão V19.\nLink de Preservação: {archive_url}\n\n{guarded_text}"

        # 3. Chamada à IA
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=self.temperature,
                system=sys_prompt,
                messages=[{"role": "user", "content": user_input}]
            )
            
            final_text = response.content[0].text
            return self._audit_and_package(final_text, guarded_text)
            
        except Exception as e:
            print(f"❌ Erro crítico no Editor: {e}")
            return {"text": raw_text, "status": "erro", "error": str(e)}

    def _audit_and_package(self, final_text: str, original_guarded: str) -> Dict:
        """Audita a integridade do post gerado."""
        ts_original = len(re.findall(r"⟦\d{1,2}:\d{2}:\d{2}⟧", original_guarded))
        ts_final = len(re.findall(r"⟦\d{1,2}:\d{2}:\d{2}⟧", final_text))
        flags = final_text.count("🚩")
        
        # Garante a âncora de mídia
        if "" not in final_text:
            final_text += "\n\n"

        return {
            "text": final_text.strip(),
            "status": "verificado" if (flags == 0 and ts_final == ts_original) else "revisao_pendente",
            "ts_integrity": ts_final == ts_original,
            "flags_count": flags,
            "model_used": self.model
        }