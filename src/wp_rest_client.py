# -*- coding: utf-8 -*-
"""
WordPress REST Client v6.3 Diamond
- Autenticação Segura: Application Passwords.
- Gerenciamento de Posts: Criação e Atualização (v19).
- Suporte a ACF: Persistência de metadados de preservação.
- Upload de Mídia: Integração com a Biblioteca do WP.
"""

import os
import requests
from requests.auth import HTTPBasicAuth
from typing import Dict, List, Optional, Any

class VanaWPClient:
    def __init__(self):
        # Configurações de ambiente
        self.wp_url = os.getenv("WP_URL", "").rstrip('/')
        self.username = os.getenv("WP_USERNAME")
        self.password = os.getenv("WP_APPLICATION_PASSWORD")
        
        if not all([self.wp_url, self.username, self.password]):
            raise EnvironmentError("❌ Credenciais do WordPress não encontradas nas variáveis de ambiente!")

        self.auth = HTTPBasicAuth(self.username, self.password)
        self.api_base = f"{self.wp_url}/wp-json/wp/v2"

    def create_post(self, title: str, content: str, status: str = "draft", 
                    categories: List[int] = None, tags: List[int] = None, 
                    meta: Dict[str, Any] = None) -> Optional[int]:
        """
        Cria um novo post no WordPress.
        """
        print(f"📝 Criando rascunho: {title}...")
        
        payload = {
            "title": title,
            "content": content,
            "status": status,
            "categories": categories or [],
            "tags": tags or [],
            "acf": meta or {}  # Suporte para campos ACF
        }

        try:
            response = requests.post(
                f"{self.api_base}/posts",
                auth=self.auth,
                json=payload
            )
            response.raise_for_status()
            post_id = response.json().get("id")
            print(f"✅ Post criado com ID: {post_id}")
            return post_id
        except Exception as e:
            print(f"❌ Erro ao criar post: {e}")
            return None

    def update_post(self, post_id: int, data: Dict[str, Any]) -> bool:
        """
        Atualiza um post existente. Útil para o Beautifier e para o Orchestrator.
        """
        print(f"🆙 Atualizando post ID: {post_id}...")
        
        try:
            response = requests.post(
                f"{self.api_base}/posts/{post_id}",
                auth=self.auth,
                json=data
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"❌ Erro ao atualizar post {post_id}: {e}")
            return False

    def get_post(self, post_id: int) -> Optional[Dict]:
        """Busca os dados de um post (contexto de edição)."""
        try:
            response = requests.get(
                f"{self.api_base}/posts/{post_id}?context=edit",
                auth=self.auth
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Erro ao buscar post {post_id}: {e}")
            return None

    def upload_media(self, file_path: str, post_id: int = None) -> Optional[int]:
        """
        Sobe um arquivo para a biblioteca de mídia.
        """
        if not os.path.exists(file_path):
            print(f"⚠️ Arquivo não encontrado: {file_path}")
            return None

        filename = os.path.basename(file_path)
        print(f"📸 Subindo mídia: {filename}...")

        headers = {
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "image/jpeg" # Ajuste se for outro tipo
        }

        with open(file_path, "rb") as img:
            try:
                response = requests.post(
                    f"{self.api_base}/media",
                    auth=self.auth,
                    headers=headers,
                    data=img
                )
                response.raise_for_status()
                media_id = response.json().get("id")
                
                # Se um post_id for fornecido, vincula a imagem a ele
                if post_id and media_id:
                    self.update_media_parent(media_id, post_id)
                
                return media_id
            except Exception as e:
                print(f"❌ Erro no upload de mídia: {e}")
                return None

    def update_media_parent(self, media_id: int, post_id: int):
        """Vincula uma mídia a um post específico."""
        requests.post(
            f"{self.api_base}/media/{media_id}",
            auth=self.auth,
            json={"post": post_id}
        )