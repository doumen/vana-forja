<?php
/**
 * FORJA DIAMOND v6.3 - Sistema de Integração Vāṇī
 * Este código adiciona botões de comando no painel lateral do Editor (Gutenberg/Clássico)
 * para disparar os GitHub Actions da Forja.
 */

// 1. CONFIGURAÇÕES TÉCNICAS (Defina estas constantes no seu wp-config.php para segurança)
// define('VANA_GH_TOKEN', 'seu_token_aqui');
// define('VANA_GH_REPO', 'seu-usuario/seu-repositorio');

add_action('post_submitbox_misc_actions', 'vana_forja_admin_buttons');
function vana_forja_admin_buttons() {
    global $post;

    // Só exibe se for um post do tipo 'post'
    if ($post->post_type !== 'post') return;

    // Recupera a URL do vídeo (ajuste o nome do campo se usar ACF)
    $video_url = get_post_meta($post->ID, 'video_url', true);
    $tour_name = vana_get_tour_category($post->ID);

    echo '<div class="misc-pub-section vana-forja-panel" style="border-top: 1px solid #ddd; padding-top: 10px; margin-top: 10px;">';
    echo '<strong>🔥 Forja Diamond v6.3</strong><br><br>';

    if (!$video_url) {
        echo '<p style="color: #d63638; font-size: 11px;">⚠️ Preencha a URL do Vídeo para habilitar.</p>';
    } else {
        // Botão Esteira 1: CORE (Transcrição e Edição)
        echo '<button type="button" class="button button-primary" style="width:100%; margin-bottom: 5px;" 
                onclick="triggerVanaAction(\'forja_trigger\', ' . $post->ID . ', \'' . esc_url($video_url) . '\', \'\')">
                🚀 Lançar Core (Texto)
              </button>';

        // Botão Esteira 2: BEAUTIFIER (Fotos e YouTube)
        $yt_url = get_post_meta($post->ID, 'youtube_reels_url', true);
        echo '<button type="button" class="button" style="width:100%;" 
                onclick="triggerVanaAction(\'beautify_trigger\', ' . $post->ID . ', \'\', \'' . esc_url($yt_url) . '\')">
                ✨ Embelezar (Mídia)
              </button>';
              
        echo '<p style="font-size: 10px; color: #666; margin-top: 5px;">📍 Tour detectada: <strong>' . $tour_name . '</strong></p>';
    }
    echo '</div>';

    // Script de Disparo AJAX
    ?>
    <script type="text/javascript">
    function triggerVanaAction(eventType, postId, videoUrl, ytUrl) {
        if(!confirm('Deseja iniciar esta ação na Forja?')) return;
        
        jQuery.ajax({
            url: ajaxurl,
            type: 'POST',
            data: {
                action: 'vana_dispatch_github',
                event_type: eventType,
                post_id: postId,
                video_url: videoUrl,
                youtube_url: ytUrl,
                nonce: '<?php echo wp_create_nonce("vana_forja_nonce"); ?>'
            },
            beforeSend: function() {
                jQuery('#btn-forja').attr('disabled', true).text('Processando...');
            },
            success: function(response) {
                alert('Sinal enviado! Acompanhe a esteira no GitHub Actions.');
            }
        });
    }
    </script>
    <?php
}

// 2. HANDLER SERVER-SIDE (Disparo Seguro para o GitHub)
add_action('wp_ajax_vana_dispatch_github', 'vana_handle_github_dispatch');
function vana_handle_github_dispatch() {
    check_ajax_referer('vana_forja_nonce', 'nonce');

    $event_type  = sanitize_text_field($_POST['event_type']);
    $post_id     = intval($_POST['post_id']);
    $video_url   = esc_url_raw($_POST['video_url']);
    $youtube_url = esc_url_raw($_POST['youtube_url']);
    $tour_id     = vana_get_tour_category($post_id);

    // Endpoint do GitHub Actions
    $url = "https://api.github.com/repos/" . VANA_GH_REPO . "/dispatches";

    $payload = [
        'event_type' => $event_type,
        'client_payload' => [
            'post_id'     => $post_id,
            'video_url'   => $video_url,
            'youtube_url' => $youtube_url,
            'tour_id'     => $tour_id
        ]
    ];

    $response = wp_remote_post($url, [
        'headers' => [
            'Authorization' => 'token ' . VANA_GH_TOKEN,
            'Accept'        => 'application/vnd.github.v3+json',
            'User-Agent'    => 'Vana-Forja-WP'
        ],
        'body' => json_encode($payload)
    ]);

    wp_send_json_success();
}

// 3. AUXILIAR: Detecta a Categoria de "Visita" (Tour)
function vana_get_tour_category($post_id) {
    $categories = get_the_category($post_id);
    foreach($categories as $cat) {
        // Lógica: se a categoria pai for "Visitas" ou tiver um ano no nome
        if ($cat->category_parent > 0 || preg_match('/\d{4}/', $cat->name)) {
            return $cat->slug;
        }
    }
    return 'geral';
}