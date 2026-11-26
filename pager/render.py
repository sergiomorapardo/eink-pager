"""Dibuja la pantalla del pager en 1 bit (blanco/negro), lista para e-paper.

Tamaño por defecto: Waveshare 2.9" (296x128). La idea de diseño es que de un
vistazo sepas si algo te necesita; si nada te necesita, la pantalla lo dice y
no tienes que mirar nada más.
"""

from __future__ import annotations

import os
import re
import time
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

from .state import State

WIDTH, HEIGHT = 296, 128

ICON = {"waiting": "!", "done": "✓", "working": "…", "idle": "·"}


# Fuentes con tildes y los íconos (✓ ↻ ▸ ✉). PAGER_FONT permite forzar otra.
FONT_CANDIDATES = [
    os.environ.get("PAGER_FONT", ""),
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def _font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if path and os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def short_message(msg: str) -> str:
    """Acorta los avisos de Claude Code para que quepan en una línea."""
    m = re.match(r"Claude needs your permission to use (.+)", msg)
    if m:
        return f"permiso: {m.group(1)}"
    if msg.startswith("Claude is waiting for your input"):
        return "espera tu respuesta"
    return msg


def _ago(ts: float, now: float) -> str:
    mins = int((now - ts) // 60)
    return f"{mins}m" if mins < 60 else f"{mins // 60}h{mins % 60:02d}"


def _until(iso_or_ts, now: float) -> str:
    """Tiempo hasta el reset; acepta epoch o ISO 8601."""
    if iso_or_ts in (None, ""):
        return ""
    try:
        ts = float(iso_or_ts)
    except (TypeError, ValueError):
        ts = datetime.fromisoformat(str(iso_or_ts).replace("Z", "+00:00")).timestamp()
    mins = max(0, int((ts - now) // 60))
    return f"{mins // 60}h{mins % 60:02d}" if mins >= 60 else f"{mins}m"


def _fit(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> str:
    if draw.textlength(text, font=font) <= max_w:
        return text
    while text and draw.textlength(text + "…", font=font) > max_w:
        text = text[:-1]
    return text + "…"


def _usage_bar(draw, x: int, y: int, w: int, label: str, pct: float, font) -> None:
    draw.text((x, y), label, font=font, fill=0)
    bx = x + 22
    draw.rectangle((bx, y + 2, bx + w, y + 10), outline=0)
    draw.rectangle((bx, y + 2, bx + int(w * min(pct, 100) / 100), y + 10), fill=0)
    draw.text((bx + w + 4, y), f"{pct:.0f}%", font=font, fill=0)


def render(state: State, now: float | None = None, size=(WIDTH, HEIGHT)) -> Image.Image:
    now = now or time.time()
    w, h = size
    img = Image.new("1", size, 1)
    d = ImageDraw.Draw(img)
    small, mid, big = _font(11), _font(13), _font(16)

    # --- Barra superior: consumo del plan ---
    usage = state.data.get("usage") or {}
    five = usage.get("five_hour") or {}
    week = usage.get("seven_day") or {}
    if five:
        _usage_bar(d, 2, 1, 60, "5h", five.get("used_percentage", 0), small)
        reset = _until(five.get("resets_at"), now)
        if reset:
            d.text((118, 1), f"↻{reset}", font=small, fill=0)
    if week:
        _usage_bar(d, 160, 1, 60, "7d", week.get("used_percentage", 0), small)
    if not five and not week:
        d.text((2, 1), "consumo: sin datos", font=small, fill=0)
    d.line((0, 14, w, 14), fill=0)

    # --- Centro: sesiones de Claude Code ---
    sessions = state.active_sessions(now)
    waiting = [s for s in sessions if s["status"] in ("waiting", "done")]
    y = 18
    if not waiting:
        working = sum(1 for s in sessions if s["status"] == "working")
        msg = f"Nada te necesita · {working} trabajando" if working else "Nada te necesita"
        d.text((4, y + 6), msg, font=big, fill=0)
    else:
        for s in waiting[:3]:
            icon = ICON[s["status"]]
            detail = short_message(s.get("message", "")) or ("listo" if s["status"] == "done" else "")
            line = f"{icon} {s['project']}: {detail}" if detail else f"{icon} {s['project']}"
            if s["status"] == "waiting":  # invertido para que salte a la vista
                d.rectangle((0, y - 1, w, y + 16), fill=0)
                d.text((4, y), _fit(d, line, mid, w - 44), font=mid, fill=1)
                d.text((w - 36, y), _ago(s["since"], now), font=mid, fill=1)
            else:
                d.text((4, y), _fit(d, line, mid, w - 44), font=mid, fill=0)
                d.text((w - 36, y), _ago(s["since"], now), font=mid, fill=0)
            y += 19
        if len(waiting) > 3:
            d.text((4, y), f"+{len(waiting) - 3} más", font=small, fill=0)
    d.line((0, 80, w, 80), fill=0)

    # --- Abajo: digest de correo y agenda ---
    digest = state.data.get("digest") or {}
    y = 83
    if not digest:
        d.text((4, y), "correo/agenda: sin digest", font=small, fill=0)
    else:
        nxt = digest.get("next_event")
        if nxt:
            d.text((4, y), _fit(d, f"▸ {nxt}", mid, w - 8), font=mid, fill=0)
            y += 15
        for item in (digest.get("needs_you") or [])[: 2 if nxt else 3]:
            d.text((4, y), _fit(d, f"✉ {item}", small, w - 8), font=small, fill=0)
            y += 13

    # Hora de la última actualización, para notar si el pager se quedó congelado
    stamp = datetime.fromtimestamp(now).strftime("%H:%M")
    d.text((w - d.textlength(stamp, font=small) - 2, h - 13), stamp, font=small, fill=0)
    return img
