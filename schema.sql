-- ============================================
-- SISTEMA DE CONTROLE FINANCEIRO - SCHEMA
-- ============================================

-- Gastos fixos mensais (aluguel, internet, etc)
CREATE TABLE despesas_fixas (
    id SERIAL PRIMARY KEY,
    descricao VARCHAR(150) NOT NULL,
    valor NUMERIC(12,2) NOT NULL,
    dia_vencimento INTEGER CHECK (dia_vencimento BETWEEN 1 AND 31),
    categoria VARCHAR(50), -- moradia, transporte, lazer, etc
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT NOW()
);

-- Gastos variáveis (lançamento avulso, dia a dia)
CREATE TABLE gastos_variaveis (
    id SERIAL PRIMARY KEY,
    descricao VARCHAR(150) NOT NULL,
    valor NUMERIC(12,2) NOT NULL,
    categoria VARCHAR(50),
    data DATE NOT NULL,
    criado_em TIMESTAMP DEFAULT NOW()
);

-- Cadastro dos investimentos (o que você possui)
CREATE TABLE investimentos (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(30) NOT NULL, -- 'tesouro_selic', 'tesouro_ipca', 'cripto', 'fii', 'acao'
    ativo VARCHAR(50) NOT NULL, -- ex: 'BTC', 'ETH', 'HGLG11', 'Tesouro Selic 2029'
    ticker VARCHAR(20),         -- símbolo pra puxar cotação (ex: 'BTC-USD', 'HGLG11.SA')
    quantidade NUMERIC(18,8) NOT NULL DEFAULT 0,
    preco_medio NUMERIC(18,8) NOT NULL DEFAULT 0,
    criado_em TIMESTAMP DEFAULT NOW()
);

-- Histórico de aportes (toda vez que você compra/investe)
CREATE TABLE aportes (
    id SERIAL PRIMARY KEY,
    investimento_id INTEGER REFERENCES investimentos(id),
    valor_aportado NUMERIC(12,2) NOT NULL,
    quantidade_comprada NUMERIC(18,8) NOT NULL,
    preco_unitario NUMERIC(18,8) NOT NULL,
    data DATE NOT NULL,
    criado_em TIMESTAMP DEFAULT NOW()
);

-- Snapshot mensal de cotações (pra manter histórico, não só valor atual)
CREATE TABLE cotacoes_historico (
    id SERIAL PRIMARY KEY,
    investimento_id INTEGER REFERENCES investimentos(id),
    preco NUMERIC(18,8) NOT NULL,
    valor_total NUMERIC(18,2) NOT NULL, -- quantidade * preco no momento
    data_referencia DATE NOT NULL, -- ex: 2026-06-01 (snapshot do mês)
    criado_em TIMESTAMP DEFAULT NOW(),
    UNIQUE(investimento_id, data_referencia)
);

-- Resumo mensal consolidado (gerado automaticamente, fecha o mês)
CREATE TABLE resumo_mensal (
    id SERIAL PRIMARY KEY,
    mes_referencia DATE NOT NULL UNIQUE, -- ex: 2026-06-01
    total_despesas_fixas NUMERIC(12,2),
    total_gastos_variaveis NUMERIC(12,2),
    total_investido_mes NUMERIC(12,2),
    patrimonio_total_investimentos NUMERIC(14,2),
    saldo_final NUMERIC(12,2),
    criado_em TIMESTAMP DEFAULT NOW()
);

-- Índices úteis
CREATE INDEX idx_gastos_data ON gastos_variaveis(data);
CREATE INDEX idx_cotacoes_data ON cotacoes_historico(data_referencia);
CREATE INDEX idx_aportes_data ON aportes(data);
