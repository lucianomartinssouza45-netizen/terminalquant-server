"""
Servidor de notícias econômicas (TerminalQuant Server).
Versão unificada e definitiva: Recebe via uploader, persiste em arquivo JSON 
no disco para garantir retenção na nuvem (Render) e serve a API para o aplicativo.
"""
from datetime import datetime
import logging
import json
from pathlib import Path
from zoneinfo import ZoneInfo
from fastapi import FastAPI, Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

app = FastAPI(title="TerminalQuant News Server")

security = HTTPBearer()
TOKEN_ESPERADO = "TQ_SECRET_2026_LUCIANO_XYZ"
LOCAL_TZ = ZoneInfo("America/Sao_Paulo")

ARQUIVO_CACHE = Path("eventos_cache.json")

def carregar_eventos_disco():
    if ARQUIVO_CACHE.exists():
        try:
            with open(ARQUIVO_CACHE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao ler cache em disco: {e}")
    return []

def salvar_eventos_disco(eventos):
    try:
        with open(ARQUIVO_CACHE, "w", encoding="utf-8") as f:
            json.dump(eventos, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Erro ao salvar cache em disco: {e}")

_updated_at = None
_last_error = None

@app.get("/")
def raiz():
    eventos = carregar_eventos_disco()
    return {
        "servico": "TerminalQuant News Server", 
        "status": "online", 
        "updated_at": _updated_at, 
        "total_eventos": len(eventos), 
        "last_error": _last_error
    }

@app.get("/api/calendar")
def listar():
    eventos = carregar_eventos_disco()
    return {
        "updated_at": _updated_at, 
        "events": eventos, 
        "last_error": _last_error
    }

@app.post("/api/update")
async def receber_atualizacao(request: Request, credentials: HTTPAuthorizationCredentials = Security(security)):
    global _updated_at, _last_error
    if credentials.credentials != TOKEN_ESPERADO:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    try:
        payload = await request.json()
        
        if isinstance(payload, dict) and "events" in payload:
            dados = payload["events"]
        elif isinstance(payload, list):
            dados = payload
        else:
            dados = [payload]
            
        salvar_eventos_disco(dados)
        _updated_at = datetime.now(LOCAL_TZ).isoformat()
        _last_error = None
        
        logger.info(f"Recebidos e salvos no disco {len(dados)} eventos.")
        return {"status": "sucesso", "total_recebido": len(dados), "total_filtrados": len(dados)}
    except Exception as e:
        _last_error = str(e)
        logger.error(f"Erro ao atualizar: {e}")
        return {"status": "erro", "detalhe": str(e)}