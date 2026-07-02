from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import extract
from .. import models, schemas
from ..database import get_db
from ..auth import get_usuario_atual

router = APIRouter(prefix="/despesas", tags=["Despesas"])


@router.post("/fixas", response_model=schemas.DespesaFixaOut)
def criar_despesa_fixa(despesa: schemas.DespesaFixaIn, db: Session = Depends(get_db),
                       usuario: models.Usuario = Depends(get_usuario_atual)):
    db_despesa = models.DespesaFixa(**despesa.model_dump(), usuario_id=usuario.id)
    db.add(db_despesa)
    db.commit()
    db.refresh(db_despesa)
    return db_despesa


@router.get("/fixas", response_model=list[schemas.DespesaFixaOut])
def listar_despesas_fixas(db: Session = Depends(get_db),
                          usuario: models.Usuario = Depends(get_usuario_atual)):
    return (db.query(models.DespesaFixa)
            .filter(models.DespesaFixa.ativo == True,
                    models.DespesaFixa.usuario_id == usuario.id)
            .all())


def _despesa_do_usuario(despesa_id: int, db: Session, usuario: models.Usuario):
    despesa = (db.query(models.DespesaFixa)
               .filter(models.DespesaFixa.id == despesa_id,
                       models.DespesaFixa.usuario_id == usuario.id)
               .first())
    if not despesa:
        raise HTTPException(404, "Despesa não encontrada")
    return despesa


@router.patch("/fixas/{despesa_id}/pago")
def marcar_pago(despesa_id: int, body: schemas.DespesaFixaPagoIn, db: Session = Depends(get_db),
                usuario: models.Usuario = Depends(get_usuario_atual)):
    despesa = _despesa_do_usuario(despesa_id, db, usuario)
    despesa.pago = body.pago
    despesa.data_pagamento = body.data_pagamento
    db.commit()
    return {"ok": True, "pago": despesa.pago}


@router.patch("/fixas/{despesa_id}/parcela")
def avancar_parcela(despesa_id: int, db: Session = Depends(get_db),
                    usuario: models.Usuario = Depends(get_usuario_atual)):
    despesa = _despesa_do_usuario(despesa_id, db, usuario)
    if not despesa.parcelado:
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
def desativar_despesa_fixa(despesa_id: int, db: Session = Depends(get_db),
                           usuario: models.Usuario = Depends(get_usuario_atual)):
    despesa = _despesa_do_usuario(despesa_id, db, usuario)
    despesa.ativo = False
    db.commit()
    return {"ok": True}


@router.post("/variaveis", response_model=schemas.GastoVariavelOut)
def criar_gasto_variavel(gasto: schemas.GastoVariavelIn, db: Session = Depends(get_db),
                         usuario: models.Usuario = Depends(get_usuario_atual)):
    db_gasto = models.GastoVariavel(**gasto.model_dump(), usuario_id=usuario.id)
    db.add(db_gasto)
    db.commit()
    db.refresh(db_gasto)
    return db_gasto


def _gasto_do_usuario(gasto_id: int, db: Session, usuario: models.Usuario):
    gasto = (db.query(models.GastoVariavel)
             .filter(models.GastoVariavel.id == gasto_id,
                     models.GastoVariavel.usuario_id == usuario.id)
             .first())
    if not gasto:
        raise HTTPException(404, "Gasto não encontrado")
    return gasto


@router.patch("/variaveis/{gasto_id}/pago")
def marcar_variavel_pago(gasto_id: int, body: schemas.DespesaFixaPagoIn, db: Session = Depends(get_db),
                         usuario: models.Usuario = Depends(get_usuario_atual)):
    gasto = _gasto_do_usuario(gasto_id, db, usuario)
    gasto.pago = body.pago
    db.commit()
    return {"ok": True, "pago": gasto.pago}


@router.get("/variaveis", response_model=list[schemas.GastoVariavelOut])
def listar_gastos_variaveis(mes: str | None = None, db: Session = Depends(get_db),
                            usuario: models.Usuario = Depends(get_usuario_atual)):
    query = db.query(models.GastoVariavel).filter(models.GastoVariavel.usuario_id == usuario.id)
    if mes:
        ano, m = mes.split("-")
        query = query.filter(
            extract("year", models.GastoVariavel.data) == int(ano),
            extract("month", models.GastoVariavel.data) == int(m)
        )
    return query.order_by(models.GastoVariavel.data.desc()).all()


@router.delete("/variaveis/{gasto_id}")
def deletar_gasto_variavel(gasto_id: int, db: Session = Depends(get_db),
                           usuario: models.Usuario = Depends(get_usuario_atual)):
    gasto = _gasto_do_usuario(gasto_id, db, usuario)
    db.delete(gasto)
    db.commit()
    return {"ok": True}
