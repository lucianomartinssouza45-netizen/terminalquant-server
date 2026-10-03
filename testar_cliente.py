"""
Simula o app cliente: faz GET no servidor e mostra os eventos.
"""
import requests

SERVIDOR_URL = "http://127.0.0.1:8000/api/calendar"

print(f"Buscando de: {SERVIDOR_URL}\n")

try:
    r = requests.get(SERVIDOR_URL, timeout=10)

    if r.status_code != 200:
        print(f"Erro: HTTP {r.status_code}")
        exit()

    dados = r.json()
    eventos = dados.get("events", [])
    updated_at = dados.get("updated_at")

    print(f"Atualizado em: {updated_at}")
    print(f"Total: {len(eventos)} eventos\n")
    print("-" * 70)

    for ev in eventos[:20]:
        bolinha = {"high": "[R]", "medium": "[L]", "low": "[V]"}.get(ev["impact"], "?")
        print(f"{ev['time']}  {bolinha}  {ev['event']}")

    print("-" * 70)
    print(f"Mostrando 20 de {len(eventos)}")

except Exception as e:
    print(f"Erro: {e}")