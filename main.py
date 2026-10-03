"""
Servidor de notícias econômicas.

Recebe eventos do uploader (POST) e serve pros clientes (GET).
"""
import os
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

app = FastAPI(title="TerminalQuant News Server")

# Token de autenticação (lido da variável de ambiente TOKEN_UPLOAD)
TOKEN_UPLOAD = os.getenv("TOKEN_UPLOAD", "TROQUE_ESSE_TOKEN_123")

# Guarda os eventos em memória
_eventos = []
_updated_at = None


class EventosPayload(BaseModel):
    events: list


@app.get("/")
def raiz():
    return {
        "servico": "TerminalQuant News Server",
        "status": "online",
        "updated_at": _updated_at,
        "total_eventos": len(_eventos),
    }


@app.post("/api/calendar/update")
def atualizar(payload: EventosPayload, authorization: Optional[str] = Header(None)):
    global _eventos, _updated_at

    # Valida token
    if authorization != f"Bearer {TOKEN_UPLOAD}":
        raise HTTPException(status_code=401, detail="Token inválido")

    _eventos = payload.events
    _updated_at = datetime.utcnow().isoformat()

    return {
        "status": "ok",
        "recebidos": len(_eventos),
        "updated_at": _updated_at,
    }


@app.get("/api/calendar")
def listar():
    return {
        "updated_at": _updated_at,
        "events": _eventos,
    }