from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    nome = Column(String(50), unique=True, nullable=False)
    senha_hash = Column(String(200), nullable=False)
    criado_em = Column(DateTime, server_default=func.now())


class DespesaFixa(Base):
    __tablename__ = "despesas_fixas"
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    descricao = Column(String(150), nullable=False)
    valor = Column(Numeric(12, 2), nullable=False)
    dia_vencimento = Column(Integer)
    categoria = Column(String(50))
    ativo = Column(Boolean, default=True)
    parcelado = Column(Boolean, default=False)
    total_parcelas = Column(Integer, nullable=True)
    parcela_atual = Column(Integer, nullable=True)
    valor_total_parcelado = Column(Numeric(12, 2), nullable=True)
    pago = Column(Boolean, default=False)
    data_pagamento = Column(Date, nullable=True)
    criado_em = Column(DateTime, server_default=func.now())


class GastoVariavel(Base):
    __tablename__ = "gastos_variaveis"
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    descricao = Column(String(150), nullable=False)
    valor = Column(Numeric(12, 2), nullable=False)
    categoria = Column(String(50))
    data = Column(Date, nullable=False)
    pago = Column(Boolean, default=False)
    criado_em = Column(DateTime, server_default=func.now())


class Investimento(Base):
    __tablename__ = "investimentos"
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    tipo = Column(String(30), nullable=False)
    ativo = Column(String(50), nullable=False)
    ticker = Column(String(20))
    quantidade = Column(Numeric(18, 8), default=0)
    preco_medio = Column(Numeric(18, 8), default=0)
    criado_em = Column(DateTime, server_default=func.now())
    aportes = relationship("Aporte", back_populates="investimento")
    cotacoes = relationship("CotacaoHistorico", back_populates="investimento")


class Aporte(Base):
    __tablename__ = "aportes"
    id = Column(Integer, primary_key=True)
    investimento_id = Column(Integer, ForeignKey("investimentos.id"))
    valor_aportado = Column(Numeric(12, 2), nullable=False)
    quantidade_comprada = Column(Numeric(18, 8), nullable=False)
    preco_unitario = Column(Numeric(18, 8), nullable=False)
    data = Column(Date, nullable=False)
    criado_em = Column(DateTime, server_default=func.now())
    investimento = relationship("Investimento", back_populates="aportes")


class CotacaoHistorico(Base):
    __tablename__ = "cotacoes_historico"
    id = Column(Integer, primary_key=True)
    investimento_id = Column(Integer, ForeignKey("investimentos.id"))
    preco = Column(Numeric(18, 8), nullable=False)
    valor_total = Column(Numeric(18, 2), nullable=False)
    data_referencia = Column(Date, nullable=False)
    criado_em = Column(DateTime, server_default=func.now())
    investimento = relationship("Investimento", back_populates="cotacoes")
    __table_args__ = (UniqueConstraint("investimento_id", "data_referencia"),)


class ResumoMensal(Base):
    __tablename__ = "resumo_mensal"
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    mes_referencia = Column(Date, nullable=False)
    total_despesas_fixas = Column(Numeric(12, 2))
    total_gastos_variaveis = Column(Numeric(12, 2))
    total_investido_mes = Column(Numeric(12, 2))
    patrimonio_total_investimentos = Column(Numeric(14, 2))
    saldo_final = Column(Numeric(12, 2))
    criado_em = Column(DateTime, server_default=func.now())


class Receita(Base):
    __tablename__ = "receitas"
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    descricao = Column(String(150), nullable=False)
    valor = Column(Numeric(12, 2), nullable=False)
    tipo = Column(String(20), nullable=False)
    data = Column(Date, nullable=False)
    categoria = Column(String(50))
    recorrente = Column(Boolean, default=False)
    criado_em = Column(DateTime, server_default=func.now())
