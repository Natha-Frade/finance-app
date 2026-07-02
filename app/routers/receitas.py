from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import extract
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/receitas", tags=["Receitas"])


def filtro_mes(query, coluna, mes: str):
    ano, mes_num = mes.split("-")
    return query.filter(
        extract("year", coluna) == int(ano),
        extract("month", coluna) == int(mes_num),
    )


@router.post("", response_model=schemas.ReceitaOut)
def criar_receita(receita: schemas.ReceitaIn, db: Session = Depends(get_db)):
    db_rec = models.Receita(**receita.model_dump())
    db.add(db_rec)
    db.commit()
    db.refresh(db_rec)
    return db_rec


@router.get("", response_model=list[schemas.ReceitaOut])
def listar_receitas(mes: str | None = None, db: Session = Depends(get_db)):
    query = db.query(models.Receita)
    if mes:
        query = filtro_mes(query, models.Receita.data, mes)
    return query.order_by(models.Receita.data.desc()).all()


@router.delete("/{receita_id}")
def deletar_receita(receita_id: int, db: Session = Depends(get_db)):
    rec = db.query(models.Receita).get(receita_id)
    if not rec:
        raise HTTPException(404, "Receita não encontrada")
    db.delete(rec)
    db.commit()
    return {"ok": True}
