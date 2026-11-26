"""Resume Gmail y Calendar con Claude Code en modo headless y lo manda al pager.

Usa `claude -p`, que descuenta de la suscripción (no de una API key) y aprovecha
los conectores de Gmail y Calendar de tu cuenta. OJO: cada corrida gasta cuota
del plan; con `--dry-run` usa fixtures/digest.json y no llama al modelo.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import urllib.request
from pathlib import Path

PROMPT = """Revisa mi Gmail (no leídos de las últimas 24 h) y mi Google Calendar (hoy y mañana).
Tu trabajo es protegerme la atención: incluye SOLO lo que requiere una acción mía
o una respuesta hoy. Ignora newsletters, notificaciones automáticas y promociones.
No modifiques nada (no marques como leído, no respondas, no crees eventos).
Responde ÚNICAMENTE con JSON válido, sin texto alrededor, con esta forma:
{"next_event": "HH:MM Título (≤40 caracteres) o null",
 "needs_you": ["remitente: qué necesita (≤50 caracteres)", "... máximo 3"]}"""

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "digest.json"


def build_digest(model: str) -> dict:
    out = subprocess.run(
        ["claude", "-p", PROMPT, "--model", model, "--output-format", "json"],
        capture_output=True, text=True, timeout=300, check=True,
    )
    result = json.loads(out.stdout)  # envoltorio de claude -p
    text = result.get("result", "").strip().removeprefix("```json").removesuffix("```")
    digest = json.loads(text)
    digest["cost_usd"] = result.get("total_cost_usd")  # equivalente API, para vigilar el gasto
    return digest


def post(digest: dict, url: str) -> None:
    req = urllib.request.Request(
        url, data=json.dumps(digest).encode(), headers={"Content-Type": "application/json"}
    )
    urllib.request.urlopen(req, timeout=5).read()


def main():
    ap = argparse.ArgumentParser(description="Digest de correo/agenda para el pager")
    ap.add_argument("--dry-run", action="store_true", help="usa el fixture, no llama a Claude")
    ap.add_argument("--model", default="claude-haiku-5-5", help="modelo barato por defecto")
    ap.add_argument("--url", default="http://127.0.0.1:8787/digest")
    args = ap.parse_args()
    digest = json.loads(FIXTURE.read_text()) if args.dry_run else build_digest(args.model)
    print(json.dumps(digest, ensure_ascii=False, indent=1))
    post(digest, args.url)


if __name__ == "__main__":
    main()
