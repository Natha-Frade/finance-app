from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import extract
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/despesas", tags=["Despesas"])


@router.post("/fixas", response_model=schemas.DespesaFixaOut)
def criar_despesa_fixa(despesa: schemas.DespesaFixaIn, db: Session = Depends(get_db)):
    db_despesa = models.DespesaFixa(**despesa.model_dump())
    db.add(db_despesa)
    db.commit()
    db.refresh(db_despesa)
    return db_despesa


@router.get("/fixas", response_model=list[schemas.DespesaFixaOut])
def listar_despesas_fixas(db: Session = Depends(get_db)):
    return db.query(models.DespesaFixa).filter(models.DespesaFixa.ativo == True).all()


@router.patch("/fixas/{despesa_id}/pago")
def marcar_pago(despesa_id: int, body: schemas.DespesaFixaPagoIn, db: Session = Depends(get_db)):
    despesa = db.query(models.DespesaFixa).get(despesa_id)
    if not despesa:
        raise HTTPException(404, "Despesa não encontrada")
    despesa.pago = body.pago
    despesa.data_pagamento = body.data_pagamento
    db.commit()
    return {"ok": True, "pago": despesa.pago}


@router.patch("/fixas/{despesa_id}/parcela")
def avancar_parcela(despesa_id: int, db: Session = Depends(get_db)):
    despesa = db.query(models.DespesaFixa).get(despesa_id)
    if not despesa or not despesa.parcelado:
        raise HTTPException(404, "Despesa parcelada não encontrada")
    if despesa.parcela_atual < despesa.total_parcelas:
        despesa.parcela_atual += 1
        despesa.pago = False
        despesa.data_pagamento = None
    else:
        despesa.ativo = False
    db.commit()
    return {"ok": True, "parcela_atual": despesa.parcela_atual, "ativo": despesa.ativo}


@router.delete("/fixas/{despesa_id}")
def desativar_despesa_fixa(despesa_id: int, db: Session = Depends(get_db)):
    despesa = db.query(models.DespesaFixa).get(despesa_id)
    if not despesa:
        raise HTTPException(404, "Despesa não encontrada")
    despesa.ativo = False
    db.commit()
    return {"ok": True}


@router.post("/variaveis", response_model=schemas.GastoVariavelOut)
def criar_gasto_variavel(gasto: schemas.GastoVariavelIn, db: Session = Depends(get_db)):
    db_gasto = models.GastoVariavel(**gasto.model_dump())
    db.add(db_gasto)
    db.commit()
    db.refresh(db_gasto)
    return db_gasto


@router.patch("/variaveis/{gasto_id}/pago")
def marcar_variavel_pago(gasto_id: int, body: schemas.DespesaFixaPagoIn, db: Session = Depends(get_db)):
    gasto = db.query(models.GastoVariavel).get(gasto_id)
    if not gasto:
        raise HTTPException(404, "Gasto não encontrado")
    gasto.pago = body.pago
    db.commit()
    return {"ok": True, "pago": gasto.pago}


@router.get("/variaveis", response_model=list[schemas.GastoVariavelOut])
def listar_gastos_variaveis(mes: str | None = None, db: Session = Depends(get_db)):
    query = db.query(models.GastoVariavel)
    if mes:
        ano, m = mes.split("-")
        query = query.filter(
            extract("year", models.GastoVariavel.data) == int(ano),
            extract("month", models.GastoVariavel.data) == int(m)
        )
    return query.order_by(models.GastoVariavel.data.desc()).all()


@router.delete("/variaveis/{gasto_id}")
def deletar_gasto_variavel(gasto_id: int, db: Session = Depends(get_db)):
    gasto = db.query(models.GastoVariavel).get(gasto_id)
    if not gasto:
        raise HTTPException(404, "Gasto não encontrado")
    db.delete(gasto)
    db.commit()
    return {"ok": True}
