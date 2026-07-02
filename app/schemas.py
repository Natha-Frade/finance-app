from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


class DespesaFixaIn(BaseModel):
    descricao: str
    valor: Decimal
    dia_vencimento: Optional[int] = None
    categoria: Optional[str] = None
    parcelado: bool = False
    total_parcelas: Optional[int] = None
    parcela_atual: Optional[int] = None
    valor_total_parcelado: Optional[Decimal] = None
    pago: bool = False
    data_pagamento: Optional[date] = None


class DespesaFixaOut(DespesaFixaIn):
    id: int
    ativo: bool
    class Config:
        from_attributes = True


class DespesaFixaPagoIn(BaseModel):
    pago: bool
    data_pagamento: Optional[date] = None


class GastoVariavelIn(BaseModel):
    descricao: str
    valor: Decimal
    categoria: Optional[str] = None
    data: date
    pago: bool = False


class GastoVariavelOut(GastoVariavelIn):
    id: int
    class Config:
        from_attributes = True


class InvestimentoIn(BaseModel):
    tipo: str
    ativo: str
    ticker: Optional[str] = None


class InvestimentoOut(InvestimentoIn):
    id: int
    quantidade: Decimal
    preco_medio: Decimal
    class Config:
        from_attributes = True


class AporteIn(BaseModel):
    investimento_id: int
    valor_aportado: Decimal
    quantidade_comprada: Decimal
    preco_unitario: Decimal
    data: date


class AporteOut(AporteIn):
    id: int
    class Config:
        from_attributes = True


class ReceitaIn(BaseModel):
    descricao: str
    valor: Decimal
    tipo: str           # fixo | variavel
    data: date
    categoria: Optional[str] = None
    recorrente: bool = False


class ReceitaOut(ReceitaIn):
    id: int
    class Config:
        from_attributes = True


# ===== Autenticação =====
class LoginIn(BaseModel):
    nome: str
    senha: str


class TokenOut(BaseModel):
    token: str
    nome: str


class UsuarioOut(BaseModel):
    id: int
    nome: str
    class Config:
        from_attributes = True
