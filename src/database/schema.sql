-- 1. EXTENSÕES (Caso queira busca semântica no futuro)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. TABELA: vana_conceitos (O Cérebro Teológico)
-- Alimentada pelo script sync_vocabulary.py via Planilha Google
CREATE TABLE vana_conceitos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug TEXT UNIQUE NOT NULL,           -- Ex: narasimha-lila
    tag_iast TEXT NOT NULL,              -- Ex: Narasiṁha-līlā
    category TEXT DEFAULT 'geral',       -- lila, tattva, biografia, etc.
    description TEXT,                    -- Definição para ajudar a IA
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. TABELA: vana_aulas (O Registro Mestre)
-- Criada pelo vana_orchestrator.py
CREATE TABLE vana_aulas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    wp_post_id INTEGER UNIQUE,           -- ID do post no WordPress
    title TEXT,                          -- Título gerado pela IA
    video_url_original TEXT,             -- Link do Facebook/YouTube original
    archive_url TEXT,                    -- Link de preservação no Archive.org
    gdrive_folder_id TEXT,               -- Pasta no Google Drive com o Master
    status TEXT DEFAULT 'draft',         -- draft, published, archiving
    transcription_raw TEXT,              -- O texto bruto antes da edição
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. TABELA: vana_passagens (A Mina de Ouro / Fábrica de Reels)
-- Alimentada pelo src/parser.py após a edição da IA
CREATE TABLE vana_passagens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    aula_id UUID REFERENCES vana_aulas(id) ON DELETE CASCADE,
    type TEXT NOT NULL,                  -- lila, biografia, tattva, verso, cancao, instrucao, historia
    is_reel BOOLEAN DEFAULT FALSE,       -- Se a IA marcou como potencial para vídeo curto
    hook TEXT,                           -- A frase de impacto para a legenda do Reel
    content TEXT NOT NULL,               -- O conteúdo do fragmento
    timestamp_start TEXT,                -- O tempo exato ⟦HH:MM:SS⟧ no vídeo
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. ÍNDICES PARA PERFORMANCE
CREATE INDEX idx_passagens_reel ON vana_passagens(is_reel) WHERE is_reel = TRUE;
CREATE INDEX idx_passagens_type ON vana_passagens(type);
CREATE INDEX idx_conceitos_slug ON vana_conceitos(slug);

-- 6. TRIGGER PARA ATUALIZAR O updated_at AUTOMATICAMENTE
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_vana_conceitos_updated_at
    BEFORE UPDATE ON vana_conceitos
    FOR EACH ROW
    EXECUTE PROCEDURE update_updated_at_column();

-- 7. POLÍTICAS DE SEGURANÇA (RLS)
-- Como o GitHub Actions e o WordPress usarão a Service Role, 
-- habilitamos acesso total para a nossa API privada.
ALTER TABLE vana_conceitos ENABLE ROW LEVEL SECURITY;
ALTER TABLE vana_aulas ENABLE ROW LEVEL SECURITY;
ALTER TABLE vana_passagens ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Acesso total para API Diamond" ON vana_conceitos FOR ALL USING (true);
CREATE POLICY "Acesso total para API Diamond" ON vana_aulas FOR ALL USING (true);
CREATE POLICY "Acesso total para API Diamond" ON vana_passagens FOR ALL USING (true);