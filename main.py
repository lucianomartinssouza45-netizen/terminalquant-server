"""
Servidor de notícias econômicas (TerminalQuant Server).
"""
from datetime import datetime
import logging
from zoneinfo import ZoneInfo
from fastapi import FastAPI, Request
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

app = FastAPI(title="TerminalQuant News Server")

_eventos = []
_updated_at = None
_last_error = None
_raw_count = 0
LOCAL_TZ = ZoneInfo("America/Sao_Paulo")

def processar_dados_brutos(dados):
    global _eventos, _updated_at, _last_error, _raw_count
    try:
        _raw_count = len(dados) if isinstance(dados, list) else 0
        hoje_local = datetime.now(LOCAL_TZ).date()
        eventos_filtrados = []

        for item in dados:
            try:
                data_str = item.get("date")
                if not data_str:
                    continue
                if data_str.endswith("Z"):
                    data_str = data_str.replace("Z", "+00:00")
                
                dt_utc = datetime.fromisoformat(data_str)
                dt_local = dt_utc.astimezone(LOCAL_TZ)

                if dt_local.date() != hoje_local:
                    continue

                eventos_filtrados.append({
                    "date": dt_local.strftime("%Y-%m-%d"),
                    "time": dt_local.strftime("%H:%M"),
                    "event": item.get("title", "").strip(),
                    "impact": "high" if "high" in item.get("impact", "").lower() else ("medium" if "medium" in item.get("impact", "").lower() else "low")
                })
            except Exception:
                continue

        eventos_filtrados.sort(key=lambda x: x["time"])
        _eventos = eventos_filtrados
        _updated_at = datetime.now(LOCAL_TZ).isoformat()
        _last_error = None
    except Exception as e:
        _last_error = str(e)

@app.get("/")
def raiz():
    return {"servico": "TerminalQuant News Server", "status": "online", "updated_at": _updated_at, "total_eventos": len(_eventos)}

@app.get("/api/calendar")
def listar():
    return {"updated_at": _updated_at, "events": _eventos}

@app.post("/api/update")
async def receber_atualizacao(request: Request):
    try:
        dados = await request.json()
        processar_dados_brutos(dados)
        return {"status": "sucesso", "total_recebido": len(dados), "total_filtrados": len(_eventos)}
    except Exception as e:
        return {"status": "erro", "detalhe": str(e)}
