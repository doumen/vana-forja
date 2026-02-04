# -*- coding: utf-8 -*-
import argparse
import sys
from src.transcriber import run_transcription, get_video_duration
from src.editor import run_editor
from src.parser import parse_shortcodes  # ✨ NOVO: O Minerador
from src.wp_rest_client import publish_wp
from src.utils.supabase_client import VanaSupabase
from src.utils.time import parse_timestamp
from src.notifier import notify_budget_block, notify_success

# CONFIGURAÇÕES DE CUSTO (FINOPS)
COST_PER_HOUR = 0.85 
MONTHLY_LIMIT = 50.0 

def pre_flight_budget_check(args, db):
    """Calcula o pedágio antes de iniciar a decolagem."""
    print("⚖️ [PRE-FLIGHT] Verificando viabilidade financeira...")
    
    if args.start and args.end:
        duration_sec = parse_timestamp(args.end) - parse_timestamp(args.start)
    else:
        duration_sec = get_video_duration(args.source_url)
    
    estimated_cost = (duration_sec / 3600) * COST_PER_HOUR
    current_spend = db.get_monthly_spend()
    
    print(f"   💰 Custo estimado: ${estimated_cost:.2f} | Gasto mensal: ${current_spend:.2f}")

    if (current_spend + estimated_cost) > MONTHLY_LIMIT:
        return False, estimated_cost, current_spend
    return True, estimated_cost, current_spend

def main():
    parser = argparse.ArgumentParser(description="Forja HariKatha v6.3 Diamond")
    parser.add_argument("--source_url", required=True)
    parser.add_argument("--post_id", type=int, required=True)
    parser.add_argument("--target_lang", default="pt")
    parser.add_argument("--start", default=None)
    parser.add_argument("--end", default=None)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()

    db = VanaSupabase()
    
    # --- PASSO 0: FINOPS ---
    allowed, est_cost, total_spent = pre_flight_budget_check(args, db)
    if not allowed:
        msg = f"🛑 LIMITE ATINGIDO: ${total_spent:.2f}. Esta aula custaria +${est_cost:.2f}."
        print(msg)
        notify_budget_block(msg, total_spent)
        sys.exit(0)

    try:
        # --- PASSO 1: IDENTIDADE ---
        source_id = db.get_source_id(args.source_url)
        aula = db.upsert_aula(source_id)
        aula_id = aula['id']

        # --- PASSO 2: TRANSCRIÇÃO ---
        raw_content = db.buscar_raw_existente(aula_id)
        if not raw_content:
            t_stats = run_transcription(args.source_url, args.start, args.end)
            raw_content = t_stats['content']
            db.salvar_raw(aula_id, raw_content, t_stats['sha256'])
        
        # --- PASSO 3: REFINO ---
        # Verificamos se já existe a versão final para evitar re-gasto de API
        versao = db.buscar_versao_final(aula_id, args.target_lang)
        
        if not versao:
            e_stats = run_editor(target_lang=args.target_lang)
            # Salvamos e capturamos o ID da versão criada
            versao_final_id = db.salvar_versao_final(
                aula_id, 
                args.target_lang, 
                e_stats['text'], 
                custo=e_stats['cost_usd'],
                status=e_stats['status']
            )
            final_text = e_stats['text']
            status_final = e_stats['status']

            # --- PASSO 3.5: MINERAÇÃO (ESTUDO CRUZADO) ✨ ---
            print("💎 [MINING] Extraindo pérolas para o estudo cruzado...")
            fragmentos = parse_shortcodes(final_text, versao_final_id)
            db.salvar_segmentos(fragmentos)
        else:
            final_text = versao['texto_editado']
            status_final = versao['status']

        # --- PASSO 4: PUBLICAÇÃO ---
        if args.publish:
            publish_wp(args.post_id, final_text, status=status_final)
            db.atualizar_post_id(aula_id, args.target_lang, args.post_id)

        print(f"✅ [SUCESSO] Processo concluído. Status: {status_final}")
        notify_success(aula_id, status_final)

    except Exception as e:
        print(f"❌ [ERRO] Falha no pipeline: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()