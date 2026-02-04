import os
import argparse
import subprocess
import json
from datetime import datetime
from src.transcriber import VanaTranscriber
from src.editor import VanaEditor
from src.utils.wp_rest_client import VanaWPClient
from src.utils.supabase_client import VanaSupabase
from internetarchive import upload as ia_upload
from googleapiclient.discovery import build
from google.oauth2 import service_account

class VanaOrchestrator:
    def __init__(self):
        self.db = VanaSupabase()
        self.wp = VanaWPClient()
        self.output_dir = "output"
        os.makedirs(f"{self.output_dir}/frames", exist_ok=True)
        os.makedirs(f"{self.output_dir}/audio", exist_ok=True)

    def stage_0_preservation(self, video_url, folder_name):
        """Baixa o vídeo, extrai áudio HQ e gera Golden Frames."""
        print(f"📥 [STAGE 0] Iniciando preservação de: {video_url}")
        
        video_path = f"{self.output_dir}/video_master.mp4"
        audio_hq = f"{self.output_dir}/audio/audio_hq.mp3"

        # 1. Download Master via yt-dlp
        cmd_dl = [
            'yt-dlp', '-o', video_path,
            '--extract-audio', '--audio-format', 'mp3', '--audio-quality', '0',
            '--keep-video', video_url
        ]
        subprocess.run(cmd_dl, check=True)

        # 2. Extração de Golden Frames via ffmpeg (1 a cada 5 min)
        print("📸 Extraindo Golden Frames para a Batalha de Capas...")
        cmd_frames = [
            'ffmpeg', '-i', video_path, '-vf', 'fps=1/300', 
            f'{self.output_dir}/frames/frame_%03d.jpg'
        ]
        subprocess.run(cmd_frames, check=True)
        
        return video_path, audio_hq

    def stage_1_archive_org(self, audio_path, title):
        """Envia o áudio HQ para o Archive.org (Preservação Eterna)."""
        print("🏛️ [STAGE 1] Fazendo upload para Archive.org...")
        identifier = f"vana-forja-{datetime.now().strftime('%Y%m%d-%H%M')}"
        meta = {'title': title, 'mediatype': 'audio', 'collection': 'opensource_audio'}
        
        # Requer IA_ACCESS_KEY e IA_SECRET_KEY configurados no ambiente
        ia_upload(identifier, files=[audio_path], metadata=meta)
        return f"https://archive.org/details/{identifier}"

    def stage_2_google_drive(self, video_path, folder_name):
        """Envia o Master para o Google Drive da Tour."""
        print("🚀 [STAGE 2] Enviando Vídeo Master para o Google Drive...")
        # Lógica de Service Account
        creds_json = os.getenv('GDRIVE_SERVICE_ACCOUNT_JSON')
        info = json.loads(creds_json)
        creds = service_account.Credentials.from_service_account_info(info)
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {
            'name': f"{folder_name}_MASTER.mp4",
            'parents': [os.getenv('GDRIVE_FOLDER_ID')]
        }
        service.files().create(body=file_metadata, media_body=video_path).execute()

    def run(self, video_url, post_id=None):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        folder_name = f"aula_{timestamp}"

        # --- PRESERVAÇÃO ---
        video_master, audio_hq = self.stage_0_preservation(video_url, folder_name)
        archive_url = self.stage_1_archive_org(audio_hq, folder_name)
        self.stage_2_google_drive(video_master, folder_name)

        # --- INTELIGÊNCIA TEOLÓGICA ---
        # Busca conceitos dinâmicos da Planilha/Supabase para injetar no Editor
        print("🧠 Buscando vocabulário canônico no Supabase...")
        conceitos = self.db.client.table("vana_conceitos").select("*").execute()
        dicionario_sangha = {c['slug']: c['tag_iast'] for c in conceitos.data}

        # --- TRANSCRIÇÃO & EDIÇÃO ---
        print("✍️ Iniciando Transcrição e Refino Editorial V19...")
        transcription = VanaTranscriber().process(audio_hq)
        
        # O Editor agora recebe o dicionário para não 'inventar' tags
        editor = VanaEditor(dicionario=dicionario_sangha)
        content_v19 = editor.refine(transcription, metadata={"archive_url": archive_url})

        # --- FINALIZAÇÃO ---
        if post_id:
            print(f"🆙 Atualizando post existente {post_id} no WordPress...")
            self.wp.update_post(post_id, content_v19)
        else:
            print("🆕 Criando novo rascunho Diamond no WordPress...")
            post_id = self.wp.create_post(content_v19, status="draft")

        # Salva o rastro no Supabase para a Fábrica de Reels
        self.db.save_aula_processada(post_id, archive_url, transcription)
        
        print(f"✅ PROCESSO CONCLUÍDO! Post ID: {post_id}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--post_id", required=False)
    args = parser.parse_args()

    orchestrator = VanaOrchestrator()
    orchestrator.run(args.url, args.post_id)