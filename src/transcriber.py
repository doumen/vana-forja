# -*- coding: utf-8 -*-
"""
Transcriber v5.9.1 – O Músculo STT
- Download robusto via yt-dlp (com tratamento de erro silenciados)
- Divisão inteligente em chunks de 10 min (ffmpeg)
- Transcrição ultra-rápida via Groq Whisper-v3
- Sincronia temporal absoluta entre chunks
"""
import os
import subprocess
import math
import shutil
from pathlib import Path
from groq import Groq

from src.utils.io import sha256_file, write, write_json
from src.utils.time import format_timestamp
from src.utils.cache import PersistentCache

# Configurações de Diretórios
WORK_DIR = Path("work")
AUDIO_DIR = WORK_DIR / "audio"
TEXT_DIR = WORK_DIR / "transcripts"
CHUNK_MINUTES = int(os.getenv("CHUNK_MINUTES", "10"))

def _get_duration(path: Path) -> float:
    """Obtém a duração exata do áudio via ffprobe."""
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())

def _download_audio(url: str) -> Path:
    """Download seguro via yt-dlp encapsulado para evitar vazamento de logs."""
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    dst_base = AUDIO_DIR / "source"
    output_template = f"{dst_base}.%(ext)s"

    cmd = [
        "yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", "0",
        "-o", output_template, "--no-playlist", url
    ]

    try:
        # capture_output=True garante que erros do yt-dlp não poluam o log do GHA
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        write("work/audit/download_error.txt", f"URL: {url}\nErro: {e.stderr}")
        raise RuntimeError(f"Falha no download da aula. Verifique a URL ou conexão.")

    # Localiza o arquivo convertido (independente da extensão original)
    for f in AUDIO_DIR.glob("source.*"):
        if f.suffix == ".mp3":
            return f
    raise FileNotFoundError("O arquivo mp3 não foi localizado após o download.")

def _split_audio(src: Path, chunk_minutes: int = 10) -> list[Path]:
    """Divide o áudio original em pedaços menores para respeitar os limites da API Groq (25MB)."""
    chunks_dir = AUDIO_DIR / "chunks"
    if chunks_dir.exists():
        shutil.rmtree(chunks_dir)
    chunks_dir.mkdir(parents=True)

    total_duration = _get_duration(src)
    chunk_seconds = chunk_minutes * 60
    num_parts = math.ceil(total_duration / chunk_seconds)

    parts = []
    for i in range(num_parts):
        start = i * chunk_seconds
        dst = chunks_dir / f"part_{i:03d}.mp3"
        # ffmpeg faz o corte cirúrgico sem re-encodar pesado, preservando qualidade
        cmd = [
            "ffmpeg", "-y", "-i", str(src), "-ss", str(start), "-t", str(chunk_seconds),
            "-vn", "-acodec", "libmp3lame", "-q:a", "2", str(dst)
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        parts.append(dst)

    return parts

def _transcribe_chunk(client: Groq, chunk_path: Path, lang: str) -> list[dict]:
    """Chama a API do Groq para transcrever um segmento específico."""
    with open(chunk_path, "rb") as f:
        response = client.audio.transcriptions.create(
            file=f,
            model=os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3"),
            response_format="verbose_json",
            language=lang,
            temperature=0.0, # Zero alucinação, máxima fidelidade
            timeout=60 # Watchdog de rede
        )
    return getattr(response, "segments", []) or []

def run_transcription(source_url: str, lang_hint: str = "pt") -> dict:
    """Pipeline principal de STT com suporte a Cache por SHA-256."""
    cache = PersistentCache("transcriptions", ttl_seconds=30 * 86400)
    
    # 1. Download
    src = _download_audio(source_url)
    audio_sha = sha256_file(src)

    # 2. Verificação de Cache (Idempotência)
    if cache.has(f"sha:{audio_sha}"):
        stats = cache.get(f"sha:{audio_sha}")
        print(f"   ↩️ Áudio já processado anteriormente (Cache Hit).")
        return {"cached": True, **stats}

    # 3. Preparação Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    # 4. Split e Transcrição
    parts = _split_audio(src, CHUNK_MINUTES)
    all_lines = []
    total_words = 0
    current_offset = 0.0

    for part in parts:
        segments = _transcribe_chunk(client, part, lang_hint)
        part_duration = _get_duration(part)

        for seg in segments:
            # Ajusta o tempo do segmento somando o offset do chunk anterior
            start_sec = current_offset + float(seg.get("start", 0))
            text = (seg.get("text") or "").strip()
            if not text: continue

            ts = format_timestamp(int(start_sec))
            all_lines.append(f"[{ts}] {text}")
            total_words += len(text.split())

        current_offset += part_duration

    # 5. Persistência dos Brutos
    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = TEXT_DIR / "raw_transcript.txt"
    out_path.write_text("\n".join(all_lines), encoding="utf-8")

    # 6. Cleanup de mídia (Stateless)
    shutil.rmtree(AUDIO_DIR / "chunks", ignore_errors=True)

    # 7. Estatísticas e Cache
    stats = {
        "audio_sha256": audio_sha,
        "source_url": source_url,
        "chunks": len(parts),
        "total_words": total_words,
        "wpm_est": round(total_words / max(1, current_offset / 60), 2),
        "coverage_seconds": int(current_offset),
        "out_file": str(out_path),
    }
    
    write_json(TEXT_DIR / ".meta" / "transcription_stats.json", stats)
    cache.set(f"sha:{audio_sha}", stats)

    return stats