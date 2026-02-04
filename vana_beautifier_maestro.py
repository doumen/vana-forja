# vana_beautifier_maestro.py
import argparse
import os
from src.beautifier import VanaBeautifier

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--post_id", required=True)
    parser.add_argument("--yt_url", required=False)
    parser.add_argument("--tour_id", required=False)
    args = parser.parse_args()

    # Inicia o Estilista
    beautifier = VanaBeautifier()

    # Define o caminho das fotos (Ex: baixando do Drive usando o tour_id)
    # Por enquanto, passamos o caminho local se as fotos estiverem no runner
    local_path = f"output/frames/{args.tour_id}" if args.tour_id else None

    # Executa o embelezamento
    beautifier.process_post(
        post_id=args.post_id,
        local_photos_path=local_path,
        yt_url=args.yt_url
    )

if __name__ == "__main__":
    main()