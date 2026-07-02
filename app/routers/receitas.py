from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import text
import os

from .database import engine, Base, SessionLocal
from .routers import despesas, investimentos, resumo, receitas
from .services import cotacoes
from . import models, auth

# Cria as tabelas que ainda não existem
Base.metadata.create_all(bind=engine)

# Migrations simples: adiciona colunas novas em tabelas já existentes.
# Cada comando roda isolado e falhas são ignoradas (coluna já existe, etc).
MIGRACOES = [
    "ALTER TABLE despesas_fixas ADD COLUMN IF NOT EXISTS parcelado BOOLEAN DEFAULT FALSE",
    "ALTER TABLE despesas_fixas ADD COLUMN IF NOT EXISTS total_parcelas INTEGER",
    "ALTER TABLE despesas_fixas ADD COLUMN IF NOT EXISTS parcela_atual INTEGER",
    "ALTER TABLE despesas_fixas ADD COLUMN IF NOT EXISTS valor_total_parcelado NUMERIC(12,2)",
    "ALTER TABLE despesas_fixas ADD COLUMN IF NOT EXISTS pago BOOLEAN DEFAULT FALSE",
    "ALTER TABLE despesas_fixas ADD COLUMN IF NOT EXISTS data_pagamento DATE",
    "ALTER TABLE gastos_variaveis ADD COLUMN IF NOT EXISTS pago BOOLEAN DEFAULT FALSE",
    "ALTER TABLE despesas_fixas ADD COLUMN IF NOT EXISTS usuario_id INTEGER",
    "ALTER TABLE gastos_variaveis ADD COLUMN IF NOT EXISTS usuario_id INTEGER",
    "ALTER TABLE receitas ADD COLUMN IF NOT EXISTS usuario_id INTEGER",
    "ALTER TABLE investimentos ADD COLUMN IF NOT EXISTS usuario_id INTEGER",
    "ALTER TABLE resumo_mensal ADD COLUMN IF NOT EXISTS usuario_id INTEGER",
    "ALTER TABLE resumo_mensal DROP CONSTRAINT IF EXISTS resumo_mensal_mes_referencia_key",
]
for comando in MIGRACOES:
    try:
        with engine.begin() as conn:
            conn.execute(text(comando))
    except Exception:
        pass

app = FastAPI(title="Controle Financeiro - Nathã")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrinja em produção
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(despesas.router)
app.include_router(investimentos.router)
app.include_router(resumo.router)
app.include_router(receitas.router)


@app.get("/")
def root():
    f = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "index.html"))
    return FileResponse(f)


# --------- Job automático: atualiza cotações 1x por dia ---------
def job_atualizar_cotacoes():
    from datetime import date
    db = SessionLocal()
    try:
        investimentos_db = db.query(models.Investimento).all()
        hoje = date.today()
        for inv in investimentos_db:
            if not inv.ticker:
                continue
            try:
                preco = cotacoes.buscar_preco(inv.tipo, inv.ticker)
            except Exception:
                continue
            valor_total = float(inv.quantidade) * preco
            existente = (
                db.query(models.CotacaoHistorico)
                .filter_by(investimento_id=inv.id, data_referencia=hoje)
                .first()
            )
            if existente:
                existente.preco = preco
                existente.valor_total = valor_total
            else:
                db.add(models.CotacaoHistorico(
                    investimento_id=inv.id, preco=preco,
                    valor_total=valor_total, data_referencia=hoje,
                ))
        db.commit()
    finally:
        db.close()


scheduler = BackgroundScheduler()
scheduler.add_job(job_atualizar_cotacoes, "cron", hour=18, minute=0)  # roda todo dia às 18h
scheduler.start()
