# -*- coding: utf-8 -*-
"""
Transcriber v5.9.2 – O Músculo STT (Edição Corte Cirúrgico)
- Download inteligente via yt-dlp com --download-sections
- Sincronia de Offset: Timestamps casam com o tempo real da live
- Transcrição ultra-rápida via Groq Whisper-v3
- Cache persistente via SHA-256
"""
import os
import subprocess
import math
import shutil
from pathlib import Path
from groq import Groq

from src.utils.io import sha256_file, write, write_json
from src.utils.time import format_timestamp, parse_timestamp
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

def _download_audio(url: str, start: str = None, end: str = None) -> Path:
    """Download seguro com suporte a corte cirúrgico opcional."""
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    dst_base = AUDIO_DIR / "source"
    output_template = f"{dst_base}.%(ext)s"

    cmd = [
        "yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", "0",
        "-o", output_template, "--no-playlist", url
    ]

    # Aplica o Corte Cirúrgico se ambos os parâmetros existirem
    if start and end and len(start.strip()) > 0 and len(end.strip()) > 0:
        # Formato yt-dlp: "*00:10:00-00:20:00"
        cmd.extend(["--download-sections", f"*{start.strip()}-{end.strip()}"])

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        write("work/audit/download_error.txt", f"URL: {url}\nErro: {e.stderr}")
        raise RuntimeError("Falha no download. Verifique se a URL e os tempos de corte são válidos.")

    for f in AUDIO_DIR.glob("source.*"):
        if f.suffix == ".mp3": return f
    raise FileNotFoundError("O arquivo mp3 não foi gerado.")

def _split_audio(src: Path, chunk_minutes: int = 10) -> list[Path]:
    """Divide o áudio em chunks de 10 minutos para respeitar limites da API."""
    chunks_dir = AUDIO_DIR / "chunks"
    if chunks_dir.exists(): shutil.rmtree(chunks_dir)
    chunks_dir.mkdir(parents=True)

    total_duration = _get_duration(src)
    chunk_seconds = chunk_minutes * 60
    num_parts = math.ceil(total_duration / chunk_seconds)

    parts = []
    for i in range(num_parts):
        start_chunk = i * chunk_seconds
        dst = chunks_dir / f"part_{i:03d}.mp3"
        cmd = [
            "ffmpeg", "-y", "-i", str(src), "-ss", str(start_chunk), "-t", str(chunk_seconds),
            "-vn", "-acodec", "libmp3lame", "-q:a", "2", str(dst)
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        parts.append(dst)
    return parts

def _transcribe_chunk(client: Groq, chunk_path: Path, lang: str) -> list[dict]:
    """Chama Groq Whisper-v3."""
    with open(chunk_path, "rb") as f:
        response = client.audio.transcriptions.create(
            file=f,
            model=os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3"),
            response_format="verbose_json",
            language=lang,
            temperature=0.0
        )
    return getattr(response, "segments", []) or []

def run_transcription(source_url: str, lang_hint: str = "pt", start: str = None, end: str = None) -> dict:
    """Pipeline principal com lógica de Offset Temporal para cortes cirúrgicos."""
    cache = PersistentCache("transcriptions", ttl_seconds=30 * 86400)
    
    # 1. Download (Com ou sem corte)
    src = _download_audio(source_url, start, end)
    audio_sha = sha256_file(src)

    # 2. Cache Check
    if cache.has(f"sha:{audio_sha}"):
        return {"cached": True, **cache.get(f"sha:{audio_sha}")}

    # 3. Cálculo do Offset Inicial (Importante para manter sincronia da Live)
    # Se o corte começou em 00:10:00, o primeiro segundo do arquivo deve ser 600s
    initial_offset = parse_timestamp(start) if start else 0
    
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    parts = _split_audio(src, CHUNK_MINUTES)
    
    all_lines = []
    total_words = 0
    current_offset = float(initial_offset)

    for part in parts:
        segments = _transcribe_chunk(client, part, lang_hint)
        part_duration = _get_duration(part)

        for seg in segments:
            # O tempo absoluto = Offset da Live + Offset do Chunk + Início no Segmento
            abs_start = current_offset + float(seg.get("start", 0))
            text = (seg.get("text") or "").strip()
            if not text: continue

            ts = format_timestamp(int(abs_start))
            all_lines.append(f"[{ts}] {text}")
            total_words += len(text.split())

        current_offset += part_duration

    # 4. Finalização
    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = TEXT_DIR / "raw_transcript.txt"
    out_path.write_text("\n".join(all_lines), encoding="utf-8")

    shutil.rmtree(AUDIO_DIR / "chunks", ignore_errors=True)

    stats = {
        "audio_sha256": audio_sha,
        "total_words": total_words,
        "coverage_seconds": int(current_offset - initial_offset),
        "initial_offset": initial_offset,
        "out_file": str(out_path),
    }
    cache.set(f"sha:{audio_sha}", stats)
    return stats