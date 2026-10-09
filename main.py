"""
Servidor de notícias econômicas (TerminalQuant Server).
Modo de atualização manual via uploader.
"""
from datetime import datetime
import logging
from zoneinfo import ZoneInfo
from fastapi import FastAPI, Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

app = FastAPI(title="TerminalQuant News Server")

security = HTTPBearer()
TOKEN_ESPERADO = "TQ_SECRET_2026_LUCIANO_XYZ"

_eventos = []
_updated_at = None
_last_error = None
_raw_count = 0
LOCAL_TZ = ZoneInfo("America/Sao_Paulo")

def processar_dados_brutos(dados):
    global _eventos, _updated_at, _last_error, _raw_count
    try:
        _raw_count = len(dados) if isinstance(dados, list) else 0
        eventos_filtrados = []

        for item in dados:
            try:
                data_str = item.get("date")
                if not data_str:
                    continue
                
                # Trata formatos com ou sem fuso horário de forma segura
                if data_str.endswith("Z"):
                    dt_utc = datetime.fromisoformat(data_str.replace("Z", "+00:00"))
                    dt_local = dt_utc.astimezone(LOCAL_TZ)
                elif "+" in data_str[10:] or "-" in data_str[10:]:
                    dt_utc = datetime.fromisoformat(data_str)
                    dt_local = dt_utc.astimezone(LOCAL_TZ)
                else:
                    # Se vier sem fuso, assume diretamente o fuso local
                    dt_local = datetime.fromisoformat(data_str).replace(tzinfo=LOCAL_TZ)

                impacto_raw = str(item.get("impact", "")).lower()
                if "high" in impacto_raw:
                    impacto = "high"
                elif "medium" in impacto_raw:
                    impacto = "medium"
                else:
                    impacto = "low"

                eventos_filtrados.append({
                    "date": dt_local.strftime("%Y-%m-%d"),
                    "time": dt_local.strftime("%H:%M"),
                    "event": item.get("event", item.get("title", "")).strip(),
                    "impact": impacto,
                    "country": item.get("country", "USD")
                })
            except Exception as e:
                logger.warning(f"Erro ao parsear item individual ({item}): {e}")
                continue

        eventos_filtrados.sort(key=lambda x: x["time"])
        _eventos = eventos_filtrados
        _updated_at = datetime.now(LOCAL_TZ).isoformat()
        _last_error = None
        logger.info(f"Processamento concluído. Total de eventos aceites: {len(_eventos)}")
    except Exception as e:
        _last_error = str(e)
        logger.error(f"Erro ao processar dados brutos: {e}")

@app.get("/")
def raiz():
    return {
        "servico": "TerminalQuant News Server", 
        "status": "online", 
        "updated_at": _updated_at, 
        "total_eventos": len(_eventos), 
        "last_error": _last_error
    }

@app.get("/api/calendar")
def listar():
    return {
        "updated_at": _updated_at, 
        "events": _eventos, 
        "last_error": _last_error
    }

@app.post("/api/update")
async def receber_atualizacao(request: Request, credentials: HTTPAuthorizationCredentials = Security(security)):
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
            
        processar_dados_brutos(dados)
        return {"status": "sucesso", "total_recebido": len(dados), "total_filtrados": len(_eventos)}
    except Exception as e:
        return {"status": "erro", "detalhe": str(e)}