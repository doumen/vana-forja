# -*- coding: utf-8 -*-
"""
Auditor Reparador v5.9.1 – O Cirurgião de Acabamento
- Reconversão de Blindagem Alquímica (⟦ ⟧ → [ ])
- Normalização de timestamps para o padrão canônico
- Limpeza de resíduos de Markdown (Code Blocks)
- Saneamento de Shortcodes WordPress ([note], [hk_passage])
"""
import re
import json
from pathlib import Path
from src.utils.io import write_json
from src.utils.time import normalize_timestamp

# Caminhos de Entrada e Saída
INP_PATH = Path("work/edited/edited.txt")
OUT_PATH = Path("work/edited/edited_repaired.txt")
REPORT_PATH = Path("work/audit/repair_report.json")

# Regex para detectar timestamps blindados e normais
GUARDED_TS = re.compile(r"⟦(\d{1,2}:\d{2}:\d{2})⟧")
NORMAL_TS = re.compile(r"\[(\d{1,2}:\d{2}:\d{2})\]")

def _restore_timestamps(text: str) -> tuple[str, int]:
    """Converte ⟦H:MM:SS⟧ de volta para [H:MM:SS] normalizado."""
    count = 0

    def replacer(m):
        nonlocal count
        count += 1
        # Normaliza o tempo (ex: 0:5:9 -> 0:05:09) para consistência visual no WP
        ts = normalize_timestamp(m.group(1))
        return f"[{ts}]"

    # Substitui a blindagem por colchetes padrão
    result = GUARDED_TS.sub(replacer, text)
    return result, count

def _sanitize_markdown_and_shortcodes(text: str) -> str:
    """Remove ruídos de formatação e corrige espaçamento de shortcodes."""
    # 1. Remove blocos de código markdown caso a IA tenha incluído (ex: ```text)
    text = re.sub(r"```[a-z]*", "", text)
    text = text.replace("```", "")

    # 2. Normaliza Shortcodes (remove espaços internos que quebram o plugin WP)
    text = re.sub(r"\[\s*note\s*\]", "[note]", text)
    text = re.sub(r"\[\s*/\s*note\s*\]", "[/note]", text)
    text = re.sub(r"\[\s*hk_passage\s*\]", "[hk_passage]", text)
    text = re.sub(r"\[\s*/\s*hk_passage\s*\]", "[/hk_passage]", text)
    
    return text.strip()

def run_repair() -> dict:
    """Executa a rotina de reparo e gera relatório de integridade."""
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not INP_PATH.exists():
        return {"ok": False, "reason": "Ficheiro edited.txt não encontrado para reparo."}

    content = INP_PATH.read_text(encoding="utf-8")

    # 1. Auditoria inicial de tags
    guarded_count = len(GUARDED_TS.findall(content))
    
    # 2. Restauração e Normalização
    text, restored_count = _restore_timestamps(content)
    
    # 3. Limpeza Final
    final_text = _sanitize_markdown_and_shortcodes(text)

    # 4. Auditoria Final
    final_ts_count = len(NORMAL_TS.findall(final_text))

    # Salva o arquivo pronto para o Merger ou para o WordPress
    OUT_PATH.write_text(final_text, encoding="utf-8")

    report = {
        "ok": True,
        "timestamps": {
            "found_guarded": guarded_count,
            "restored_to_brackets": restored_count,
            "final_count": final_ts_count
        },
        "integrity": "EXCELENTE" if guarded_count == restored_count else "DIVERGENTE",
        "output_file": str(OUT_PATH)
    }

    write_json(REPORT_PATH, report)
    return report

if __name__ == "__main__":
    print(json.dumps(run_repair(), indent=2))