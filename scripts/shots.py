"""Genera las imágenes del README a partir del render real.

- docs/preview.png: el frame de 1 bit, ampliado 3× sin suavizado.
- docs/images/hero.png: el dispositivo (concepto) mostrando ese frame, capturado
  con Chrome en modo headless a partir de scripts/hero.html.

Usa solo datos de ejemplo (fixtures/digest.json y sesiones ficticias); no llama
a ningún modelo ni servicio externo. Uso: uv run python scripts/shots.py
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pager.render import render  # noqa: E402
from pager.state import State  # noqa: E402

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
]

# Colores de una pantalla e-paper real: el "blanco" es gris cálido y el negro no es puro.
PAPER = (228, 226, 219)
INK = (38, 38, 40)


def sample_frame(tmp: Path) -> Image.Image:
    """Frame con datos ficticios a una hora fija, para que la imagen sea reproducible."""
    now = datetime(2026, 11, 26, 11, 42).timestamp()
    st = State(tmp / "state.json")
    st.set_usage(
        {"five_hour": {"used_percentage": 42, "resets_at": now + 4800},
         "seven_day": {"used_percentage": 18}},
        now=now,
    )
    st.apply_hook({"hook_event_name": "Notification", "session_id": "a", "cwd": "/x/web-app",
                   "message": "Claude needs your permission to use Bash"}, now=now - 180)
    st.apply_hook({"hook_event_name": "Stop", "session_id": "b", "cwd": "/x/api-server"},
                  now=now - 720)
    st.set_digest(json.loads((REPO / "fixtures/digest.json").read_text()), now=now)
    return render(st, now)


def tint(frame: Image.Image, scale: int) -> Image.Image:
    """Pasa el frame de 1 bit a tinta/papel y lo amplía sin suavizado."""
    gray = frame.convert("L")
    colored = Image.merge("RGB", [gray.point(lambda v, a=a, b=b: b if v else a)
                                  for a, b in zip(INK, PAPER)])
    return colored.resize((frame.width * scale, frame.height * scale), Image.NEAREST)


def find_chrome() -> str:
    forced = os.environ.get("CHROME")
    if forced:  # si lo defines, se usa ese o se falla, nunca otro en silencio
        if os.path.exists(forced) or shutil.which(forced):
            return forced
        sys.exit(f"CHROME={forced} no existe.")
    for c in CHROME_CANDIDATES:
        if os.path.exists(c) or shutil.which(c):
            return c
    sys.exit("No encontré Chrome. Define CHROME con la ruta del ejecutable.")


def screenshot(html: Path, out: Path, profile: Path) -> None:
    """Captura html en out con Chrome headless y comprueba que de verdad se escribió."""
    chrome = find_chrome()  # antes de borrar nada: si falla, la imagen anterior se conserva
    out.unlink(missing_ok=True)
    cmd = [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
           f"--user-data-dir={profile}", "--force-device-scale-factor=1",
           "--window-size=1600,1080", f"--screenshot={out}", html.as_uri()]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        sys.exit("Chrome no terminó en 60 s; no se generó el hero.")
    if result.returncode != 0 or not out.exists() or out.stat().st_size == 0:
        sys.exit(f"Chrome no escribió {out.name} (código {result.returncode}):\n{result.stderr[-2000:]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--no-hero", action="store_true", help="solo regenera docs/preview.png")
    args = ap.parse_args()

    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        frame = sample_frame(tmp)
        frame.resize((frame.width * 3, frame.height * 3), Image.NEAREST).save(REPO / "docs/preview.png")
        print("docs/preview.png")
        if args.no_hero:
            return

        tint(frame, 3).save(tmp / "frame.png")  # 3× exacto = tamaño de la pantalla en hero.html
        html = (REPO / "scripts/hero.html").read_text().replace("{{FRAME}}", "frame.png")
        (tmp / "hero.html").write_text(html)
        out = REPO / "docs/images/hero.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        screenshot(tmp / "hero.html", out, tmp / "chrome-profile")
        print(out.relative_to(REPO))


if __name__ == "__main__":
    main()
