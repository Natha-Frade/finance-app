import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from . import models, schemas
from .database import get_db

SECRET_KEY = os.getenv("SECRET_KEY", "mude-esta-chave-nas-variaveis-do-railway")
ALGORITMO = "HS256"
VALIDADE_DIAS = 30
MAX_USUARIOS = 5

router = APIRouter(prefix="/auth", tags=["Autenticação"])
security = HTTPBearer(auto_error=False)


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        return bcrypt.checkpw(senha.encode(), senha_hash.encode())
    except Exception:
        return False


def criar_token(usuario_id: int) -> str:
    payload = {
        "sub": str(usuario_id),
        "exp": datetime.now(timezone.utc) + timedelta(days=VALIDADE_DIAS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITMO)


def get_usuario_atual(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> models.Usuario:
    if not credentials:
        raise HTTPException(401, "Não autenticado")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITMO])
        usuario_id = int(payload["sub"])
    except Exception:
        raise HTTPException(401, "Sessão inválida ou expirada")
    usuario = db.query(models.Usuario).get(usuario_id)
    if not usuario:
        raise HTTPException(401, "Usuário não encontrado")
    return usuario


@router.post("/registro", response_model=schemas.TokenOut)
def registrar(dados: schemas.LoginIn, db: Session = Depends(get_db)):
    nome = dados.nome.strip()
    if len(nome) < 2:
        raise HTTPException(400, "Nome muito curto")
    if len(dados.senha) < 4:
        raise HTTPException(400, "Senha deve ter pelo menos 4 caracteres")
    if db.query(models.Usuario).count() >= MAX_USUARIOS:
        raise HTTPException(403, f"Limite de {MAX_USUARIOS} perfis atingido")
    if db.query(models.Usuario).filter(models.Usuario.nome.ilike(nome)).first():
        raise HTTPException(400, "Já existe um perfil com esse nome")
    usuario = models.Usuario(nome=nome, senha_hash=hash_senha(dados.senha))
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return {"token": criar_token(usuario.id), "nome": usuario.nome}


@router.post("/login", response_model=schemas.TokenOut)
def login(dados: schemas.LoginIn, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.nome.ilike(dados.nome.strip())).first()
    if not usuario or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(401, "Nome ou senha incorretos")
    return {"token": criar_token(usuario.id), "nome": usuario.nome}


@router.get("/me", response_model=schemas.UsuarioOut)
def perfil(usuario: models.Usuario = Depends(get_usuario_atual)):
    return usuario
