-- ==========================================================
-- 🕉️ FORJA HARIKATHA v6.3 - SCHEMA GLOBAL
-- ==========================================================

-- 1. EXTENSÕES (Para buscas inteligentes e UUIDs)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. TIPOS CUSTOMIZADOS (Enums para integridade)
CREATE TYPE status_revisao AS ENUM ('verificado', 'revisao_pendente', 'erro');
CREATE TYPE tipo_segmento AS ENUM ('verso', 'instrucao', 'lila', 'historia', 'biografia', 'cancao', 'tattva');
CREATE TYPE plataforma_origem AS ENUM ('youtube', 'facebook', 'outro');

-- 3. TABELA: FONTES (Identidade Única do Áudio)
CREATE TABLE fontes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url_original TEXT UNIQUE NOT NULL,
    plataforma plataforma_origem NOT NULL,
    fingerprint_sha256 TEXT UNIQUE, -- Impede reprocessar o mesmo áudio
    duracao_segundos INTEGER,
    criado_em TIMESTAMPTZ DEFAULT NOW()
);

-- 4. TABELA: AULAS (A Entidade Mestre)
CREATE TABLE aulas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fonte_id UUID REFERENCES fontes(id) ON DELETE CASCADE,
    titulo TEXT,
    data_original DATE,
    raw_transcript TEXT, -- DNA Bruto gerado pelo Whisper
    criado_em TIMESTAMPTZ DEFAULT NOW()
);

-- 5. TABELA: VERSOES_FINAIS (O Escriba e o Financeiro)
CREATE TABLE versoes_finais (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    aula_id UUID REFERENCES aulas(id) ON DELETE CASCADE,
    idioma VARCHAR(5) NOT NULL, -- pt, en, es
    texto_editado TEXT NOT NULL, -- Texto com Shortcodes
    custo_usd DECIMAL(10, 4) DEFAULT 0.0000,
    status status_revisao DEFAULT 'revisao_pendente',
    post_id_wp INTEGER, -- ID do post no WordPress
    flags_count INTEGER DEFAULT 0,
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(aula_id, idioma)
);

-- 6. TABELA: SEGMENTOS_TEOLOGICOS (A Mineração para Estudo Cruzado)
CREATE TABLE segmentos_teologicos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    versao_id UUID REFERENCES versoes_finais(id) ON DELETE CASCADE,
    tipo tipo_segmento NOT NULL,
    titulo_segmento TEXT,
    conteudo TEXT NOT NULL,
    timestamp_inicio INTERVAL, -- Tempo exato no vídeo
    metadata JSONB, -- Para referências extras como (BG 4.9)
    criado_em TIMESTAMPTZ DEFAULT NOW()
);

-- 7. ÍNDICES ESTRATÉGICOS (Performance e FinOps)
-- Para o cálculo rápido de gasto mensal (Pre-flight)
CREATE INDEX idx_custo_mensal ON versoes_finais (criado_em, custo_usd);

-- Para busca rápida por temas no Estudo Cruzado
CREATE INDEX idx_tipo_segmento ON segmentos_teologicos (tipo);
CREATE INDEX idx_segmento_metadata ON segmentos_teologicos USING GIN (metadata);

-- 8. VIEW PARA DASHBOARD FINANCEIRO (Opcional)
CREATE OR REPLACE VIEW resumo_financeiro_mensal AS
SELECT 
    DATE_TRUNC('month', criado_em) as mes,
    SUM(custo_usd) as gasto_total,
    COUNT(id) as total_aulas
FROM versoes_finais
GROUP BY 1;