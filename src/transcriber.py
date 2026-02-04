# -*- coding: utf-8 -*-
"""
Transcritor HariKatha v6.3 - Diamond Edition
- Suporte a YouTube e Facebook via yt-dlp.
- Fingerprinting SHA-256 para evitar duplicidade.
- Chunking de 10 minutos para estabilidade na Groq.
- Cortes cirúrgicos (start/end) nativos.
"""

import os
import hashlib
import subprocess
from pathlib import Path
from groq import Groq

# Configurações de Trabalho
WORK_DIR = Path("work/audio")
CHUNK_LENGTH = 600  # 10 minutos em segundos

def get_video_duration(url: str) -> int:
    """Obtém a duração total do vídeo sem baixá-lo (Pre-flight)."""
    cmd = [
        "yt-dlp", "--get-duration", "--format", "bestaudio", url
    ]
    try:
        # Tenta converter o output (HH:MM:SS ou MM:SS) para segundos
        output = subprocess.check_output(cmd).decode().strip()
        parts = list(map(int, output.split(':')))
        if len(parts) == 3: return parts[0]*3600 + parts[1]*60 + parts[2]
        if len(parts) == 2: return parts[0]*60 + parts[1]
        return int(output)
    except:
        return 3600 # Fallback 1h se falhar

def generate_fingerprint(file_path: Path) -> str:
    """Gera o DNA (SHA-256) do arquivo de áudio."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_audio(url: str, start=None, end=None) -> Path:
    """Baixa o áudio aplicando o corte cirúrgico se necessário."""
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    output_file = WORK_DIR / "source_audio.mp3"
    
    # Limpa arquivos anteriores
    if output_file.exists(): output_file.unlink()

    # Monta comando yt-dlp com download parcial
    cmd = [
        "yt-dlp",
        "-x", "--audio-format", "mp3",
        "--audio-quality", "0",
        "-o", str(output_file)
    ]

    # Adiciona argumentos de corte via FFmpeg (eficiente)
    if start or end:
        # Formato: --external-downloader ffmpeg --external-downloader-args "ffmpeg_args"
        ffmpeg_args = ""
        if start: ffmpeg_args += f" -ss {start}"
        if end: ffmpeg_args += f" -to {end}"
        cmd += ["--external-downloader", "ffmpeg", "--external-downloader-args", ffmpeg_args.strip()]

    cmd.append(url)
    
    print(f"   📥 Baixando áudio (Surgical Cut: {start or 'Início'} -> {end or 'Fim'})...")
    subprocess.run(cmd, check=True, capture_output=True)
    return output_file

def split_audio(audio_path: Path):
    """Fatia o áudio em pedaços de 10 min para não estourar a API."""
    print("   ✂️  Fatiando áudio em blocos de 10 minutos...")
    chunks_dir = WORK_DIR / "chunks"
    chunks_dir.mkdir(exist_ok=True)
    
    # Limpa chunks antigos
    for f in chunks_dir.glob("*.mp3"): f.unlink()

    cmd = [
        "ffmpeg", "-i", str(audio_path),
        "-f", "segment", "-segment_time", str(CHUNK_LENGTH),
        "-c", "copy", str(chunks_dir / "chunk_%03d.mp3")
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return sorted(list(chunks_dir.glob("*.mp3")))

def run_transcription(url: str, start=None, end=None) -> dict:
    """Fluxo principal de transcrição Diamond."""
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    # 1. Download
    audio_file = download_audio(url, start, end)
    
    # 2. Fingerprint (Para o Supabase evitar duplicidade)
    sha256 = generate_fingerprint(audio_file)
    
    # 3. Chunking
    chunks = split_audio(audio_file)
    
    # 4. Transcrição via Groq (Whisper-v3)
    full_transcript = []
    print(f"   🎙️  Iniciando STT via Groq ({len(chunks)} chunks)...")
    
    for chunk in chunks:
        with open(chunk, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(chunk.name, file.read()),
                model="whisper-large-v3",
                response_format="text",
                language="en" # Whisper detecta automaticamente, mas 'en' ajuda na base
            )
            full_transcript.append(transcription)

    # 5. Cleanup
    audio_file.unlink()
    
    content = "\n\n".join(full_transcript)
    
    return {
        "content": content,
        "sha256": sha256,
        "chunks_count": len(chunks)
    }