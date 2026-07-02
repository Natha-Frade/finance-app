from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import extract
from .. import models
from ..database import get_db
from ..services import cotacoes
from ..auth import get_usuario_atual

router = APIRouter(tags=["Cotações e Resumo"])


def filtro_mes(query, coluna, mes: str):
    ano, mes_num = mes.split("-")
    return query.filter(
        extract("year", coluna) == int(ano),
        extract("month", coluna) == int(mes_num),
    )


@router.post("/cotacoes/atualizar")
def atualizar_cotacoes(db: Session = Depends(get_db),
                       usuario: models.Usuario = Depends(get_usuario_atual)):
    investimentos = db.query(models.Investimento).filter(models.Investimento.usuario_id == usuario.id).all()
    atualizados, erros = [], []
    hoje = date.today()
    for inv in investimentos:
        if not inv.ticker:
            continue
        try:
            preco = cotacoes.buscar_preco(inv.tipo, inv.ticker)
        except NotImplementedError:
            continue
        except Exception as e:
            erros.append({"investimento": inv.ativo, "erro": str(e)})
            continue
        valor_total = float(inv.quantidade) * preco
        existente = db.query(models.CotacaoHistorico).filter_by(investimento_id=inv.id, data_referencia=hoje).first()
        if existente:
            existente.preco = preco
            existente.valor_total = valor_total
        else:
            db.add(models.CotacaoHistorico(investimento_id=inv.id, preco=preco, valor_total=valor_total, data_referencia=hoje))
        atualizados.append({"investimento": inv.ativo, "preco": preco, "valor_total": valor_total})
    db.commit()
    return {"atualizados": atualizados, "erros": erros}


@router.get("/resumo/{mes}")
def gerar_resumo_mensal(mes: str, db: Session = Depends(get_db),
                        usuario: models.Usuario = Depends(get_usuario_atual)):
    try:
        mes_ref = date.fromisoformat(f"{mes}-01")
    except ValueError:
        raise HTTPException(400, "Formato de mês inválido. Use YYYY-MM")

    uid = usuario.id

    # Receitas do mês
    receitas_mes = filtro_mes(
        db.query(models.Receita).filter(models.Receita.usuario_id == uid),
        models.Receita.data, mes
    ).all()
    total_receitas = sum(float(r.valor) for r in receitas_mes)
    total_receitas_fixas = sum(float(r.valor) for r in receitas_mes if r.tipo == 'fixo')
    total_receitas_variaveis = sum(float(r.valor) for r in receitas_mes if r.tipo == 'variavel')

    # Despesas
    total_fixas = sum(float(d.valor) for d in db.query(models.DespesaFixa).filter_by(ativo=True, usuario_id=uid))
    total_variaveis = sum(float(g.valor) for g in filtro_mes(
        db.query(models.GastoVariavel).filter(models.GastoVariavel.usuario_id == uid),
        models.GastoVariavel.data, mes))

    # Aportes do mês (só de investimentos do usuário)
    ids_inv = [i.id for i in db.query(models.Investimento.id).filter(models.Investimento.usuario_id == uid)]
    total_investido = sum(float(a.valor_aportado) for a in filtro_mes(
        db.query(models.Aporte).filter(models.Aporte.investimento_id.in_(ids_inv)),
        models.Aporte.data, mes)) if ids_inv else 0.0

    # Patrimônio total
    patrimonio = 0.0
    for inv in db.query(models.Investimento).filter(models.Investimento.usuario_id == uid).all():
        ultima = db.query(models.CotacaoHistorico).filter_by(investimento_id=inv.id).order_by(models.CotacaoHistorico.data_referencia.desc()).first()
        patrimonio += float(ultima.valor_total) if ultima else float(inv.quantidade) * float(inv.preco_medio)

    # Saldo real = receitas - despesas fixas - despesas variáveis - aportes
    total_gastos = total_fixas + total_variaveis
    saldo_final = total_receitas - total_gastos - total_investido

    resumo = db.query(models.ResumoMensal).filter_by(mes_referencia=mes_ref, usuario_id=uid).first()
    if not resumo:
        resumo = models.ResumoMensal(mes_referencia=mes_ref, usuario_id=uid)
        db.add(resumo)

    resumo.total_despesas_fixas = total_fixas
    resumo.total_gastos_variaveis = total_variaveis
    resumo.total_investido_mes = total_investido
    resumo.patrimonio_total_investimentos = patrimonio
    resumo.saldo_final = saldo_final
    db.commit()

    return {
        "mes": mes,
        "total_receitas": total_receitas,
        "total_receitas_fixas": total_receitas_fixas,
        "total_receitas_variaveis": total_receitas_variaveis,
        "total_despesas_fixas": total_fixas,
        "total_gastos_variaveis": total_variaveis,
        "total_gastos": total_gastos,
        "total_investido_mes": total_investido,
        "patrimonio_total_investimentos": patrimonio,
        "saldo_final": saldo_final,
    }
