from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import extract
from .. import models, schemas
from ..database import get_db
from ..auth import get_usuario_atual

router = APIRouter(prefix="/receitas", tags=["Receitas"])


def filtro_mes(query, coluna, mes: str):
    ano, mes_num = mes.split("-")
    return query.filter(
        extract("year", coluna) == int(ano),
        extract("month", coluna) == int(mes_num),
    )


@router.post("", response_model=schemas.ReceitaOut)
def criar_receita(receita: schemas.ReceitaIn, db: Session = Depends(get_db),
                  usuario: models.Usuario = Depends(get_usuario_atual)):
    db_rec = models.Receita(**receita.model_dump(), usuario_id=usuario.id)
    db.add(db_rec)
    db.commit()
    db.refresh(db_rec)
    return db_rec


@router.get("", response_model=list[schemas.ReceitaOut])
def listar_receitas(mes: str | None = None, db: Session = Depends(get_db),
                    usuario: models.Usuario = Depends(get_usuario_atual)):
    query = db.query(models.Receita).filter(models.Receita.usuario_id == usuario.id)
    if mes:
        query = filtro_mes(query, models.Receita.data, mes)
    return query.order_by(models.Receita.data.desc()).all()


@router.delete("/{receita_id}")
def deletar_receita(receita_id: int, db: Session = Depends(get_db),
                    usuario: models.Usuario = Depends(get_usuario_atual)):
    rec = (db.query(models.Receita)
           .filter(models.Receita.id == receita_id,
                   models.Receita.usuario_id == usuario.id)
           .first())
    if not rec:
        raise HTTPException(404, "Receita não encontrada")
    db.delete(rec)
    db.commit()
    return {"ok": True}
