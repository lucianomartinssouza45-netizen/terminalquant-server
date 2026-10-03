"""
Uploader: monitora o CSV do MT5 e envia pro servidor quando há mudança.
"""
import csv
import os
import time
import logging
from pathlib import Path

import requests

# ============================================================
# CONFIGURAÇÃO
# ============================================================

SERVIDOR_URL = "https://terminalquant-server.onrender.com/api/calendar/update"
TOKEN = "TQ_SECRET_2026_LUCIANO_XYZ"
INTERVALO_VERIFICACAO = 60  # verifica a cada 60 segundos
ARQUIVO_TIMESTAMP = ".ultimo_timestamp"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("uploader")


def encontrar_csv_mt5():
    """Varre as pastas do MT5 e acha o calendar.csv mais recente."""
    base = Path(os.getenv("APPDATA", "")) / "MetaQuotes" / "Terminal"
    if not base.exists():
        return None

    candidatos = []
    for terminal_dir in base.iterdir():
        if not terminal_dir.is_dir():
            continue
        csv_path = terminal_dir / "MQL5" / "Files" / "calendar.csv"
        if csv_path.exists():
            candidatos.append(csv_path)

    if not candidatos:
        return None

    candidatos.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidatos[0]


def ler_csv(caminho):
    """Lê o CSV e devolve lista de eventos."""
    eventos = []
    with open(caminho, "r", encoding="latin-1") as f:
        reader = csv.DictReader(f, delimiter=";")
        for linha in reader:
            time_str = (linha.get("time") or "").strip()
            event_str = (linha.get("event") or "").strip()
            impact_str = (linha.get("impact") or "").strip().lower()

            if not time_str or not event_str:
                continue
            if impact_str not in ("low", "medium", "high"):
                continue

            eventos.append({
                "time": time_str,
                "event": event_str,
                "impact": impact_str,
            })

    eventos.sort(key=lambda e: e["time"])
    return eventos


def enviar_pro_servidor(eventos):
    """Faz POST pro servidor."""
    try:
        r = requests.post(
            SERVIDOR_URL,
            json={"events": eventos},
            headers={"Authorization": f"Bearer {TOKEN}"},
            timeout=10,
        )
        if r.status_code == 200:
            logger.info(f"OK — {len(eventos)} eventos enviados.")
            return True
        else:
            logger.warning(f"Falha — HTTP {r.status_code}: {r.text}")
            return False
    except Exception as e:
        logger.warning(f"Erro de rede: {e}")
        return False


def ler_timestamp_anterior():
    """Lê o último timestamp salvo."""
    if not os.path.exists(ARQUIVO_TIMESTAMP):
        return 0.0
    try:
        with open(ARQUIVO_TIMESTAMP, "r") as f:
            return float(f.read().strip())
    except Exception:
        return 0.0


def salvar_timestamp(ts):
    """Salva o timestamp atual."""
    try:
        with open(ARQUIVO_TIMESTAMP, "w") as f:
            f.write(str(ts))
    except Exception as e:
        logger.warning(f"Erro ao salvar timestamp: {e}")


def verificar_e_enviar():
    """Verifica se o CSV mudou. Se sim, lê e envia."""
    csv_path = encontrar_csv_mt5()
    if not csv_path:
        return

    ts_atual = csv_path.stat().st_mtime
    ts_anterior = ler_timestamp_anterior()

    if ts_atual <= ts_anterior:
        return

    logger.info(f"CSV modificado! Lendo {csv_path.name}")
    eventos = ler_csv(csv_path)
    logger.info(f"Lidos: {len(eventos)} eventos")

    if eventos:
        if enviar_pro_servidor(eventos):
            salvar_timestamp(ts_atual)
    else:
        logger.warning("CSV vazio. Não enviando.")


def main():
    logger.info("=" * 50)
    logger.info("Uploader iniciado (modo monitoramento)")
    logger.info(f"Servidor: {SERVIDOR_URL}")
    logger.info(f"Verificando a cada {INTERVALO_VERIFICACAO}s")
    logger.info("=" * 50)

    verificar_e_enviar()

    while True:
        time.sleep(INTERVALO_VERIFICACAO)
        try:
            verificar_e_enviar()
        except Exception as e:
            logger.exception(f"Erro: {e}")


if __name__ == "__main__":
    main()