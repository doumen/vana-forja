# -*- coding: utf-8 -*-
"""
WordPress REST Client v6.3 Diamond
- Publicação inteligente baseada em status (Draft vs Publish).
- Autenticação segura via Application Passwords.
- Atualização de posts existentes com suporte a Shortcodes.
"""

import os
import requests
import base64
from typing import Optional

class WordPressClient:
    def __init__(self):
        self.url = os.getenv("WP_URL") # Ex: https://site.com/wp-json/wp/v2/posts
        self.user = os.getenv("WP_USER")
        self.app_pass = os.getenv("WP_APP_PASS")
        
        if not all([self.url, self.user, self.app_pass]):
            print("⚠️ AVISO: Credenciais WordPress incompletas. Publicação desativada.")
            self.active = False
        else:
            self.active = True
            # Prepara o Header de Autenticação (Basic Auth)
            auth_str = f"{self.user}:{self.app_pass}"
            self.auth_header = {
                "Authorization": "Basic " + base64.b64encode(auth_str.encode()).decode()
            }

    def publish_content(self, post_id: int, content: str, status: str = "verificado") -> Optional[int]:
        """
        Publica ou atualiza o conteúdo no WordPress.
        status: 'verificado' -> 'publish'
        status: 'revisao_pendente' -> 'draft'
        """
        if not self.active:
            return None

        # Mapeamento de Status para o WordPress
        wp_status = "publish" if status == "verificado" else "draft"
        
        # Endpoint específico do post
        post_url = f"{self.url}/{post_id}"
        
        data = {
            "content": content,
            "status": wp_status
        }

        print(f"   📡 Enviando para WordPress (Post ID: {post_id}, Status: {wp_status})...")
        
        try:
            response = requests.post(post_url, headers=self.auth_header, json=data)
            
            if response.status_code in [200, 201]:
                print(f"   ✅ Sucesso! Conteúdo entregue como {wp_status}.")
                return post_id
            else:
                print(f"   ❌ Erro WP ({response.status_code}): {response.text}")
                return None
                
        except Exception as e:
            print(f"   ❌ Falha na conexão com WordPress: {e}")
            return None

def publish_wp(post_id: int, content: str, status: str = "verificado"):
    """Função facilitadora para o Orchestrator."""
    client = WordPressClient()
    return client.publish_content(post_id, content, status)