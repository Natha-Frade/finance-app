from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/investimentos", tags=["Investimentos"])


@router.post("", response_model=schemas.InvestimentoOut)
def criar_investimento(inv: schemas.InvestimentoIn, db: Session = Depends(get_db)):
    db_inv = models.Investimento(**inv.model_dump())
    db.add(db_inv)
    db.commit()
    db.refresh(db_inv)
    return db_inv


@router.get("", response_model=list[schemas.InvestimentoOut])
def listar_investimentos(db: Session = Depends(get_db)):
    return db.query(models.Investimento).all()


@router.post("/aportes", response_model=schemas.AporteOut)
def registrar_aporte(aporte: schemas.AporteIn, db: Session = Depends(get_db)):
    """Registra um novo aporte e atualiza quantidade/preço médio do investimento."""
    inv = db.query(models.Investimento).get(aporte.investimento_id)
    if not inv:
        raise HTTPException(404, "Investimento não encontrado")

    db_aporte = models.Aporte(**aporte.model_dump())
    db.add(db_aporte)

    # recalcula preço médio ponderado
    qtd_total = inv.quantidade + aporte.quantidade_comprada
    valor_total_anterior = inv.quantidade * inv.preco_medio
    novo_preco_medio = (valor_total_anterior + aporte.valor_aportado) / qtd_total if qtd_total else 0

    inv.quantidade = qtd_total
    inv.preco_medio = novo_preco_medio

    db.commit()
    db.refresh(db_aporte)
    return db_aporte


@router.get("/{investimento_id}/aportes", response_model=list[schemas.AporteOut])
def listar_aportes(investimento_id: int, db: Session = Depends(get_db)):
    return db.query(models.Aporte).filter(models.Aporte.investimento_id == investimento_id).all()
