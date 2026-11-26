"""Estado del pager: sesiones de Claude Code, consumo del plan y digest de correo/agenda.

Se guarda en un JSON local para sobrevivir reinicios del servidor.
"""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

DEFAULT_PATH = Path(os.environ.get("PAGER_STATE", Path.home() / ".local/state/eink-pager/state.json"))

# Sesiones sin eventos en este tiempo se consideran abandonadas y se ocultan.
STALE_SECONDS = 6 * 3600

# Evento de hook -> estado de la sesión
EVENT_STATUS = {
    "SessionStart": "idle",
    "UserPromptSubmit": "working",
    "Notification": "waiting",  # pide permiso o lleva rato esperando input
    "Stop": "done",
}


class State:
    def __init__(self, path: Path = DEFAULT_PATH):
        self.path = path
        self._lock = threading.Lock()
        self.data = {"sessions": {}, "usage": None, "digest": None}
        if path.exists():
            try:
                self.data.update(json.loads(path.read_text()))
            except json.JSONDecodeError:
                pass

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=1))
        tmp.replace(self.path)

    def apply_hook(self, payload: dict, now: float | None = None) -> None:
        """Aplica el JSON que Claude Code manda a un hook."""
        now = now or time.time()
        event = payload.get("hook_event_name", "")
        sid = payload.get("session_id")
        if not sid:
            return
        with self._lock:
            sessions = self.data["sessions"]
            if event == "SessionEnd":
                sessions.pop(sid, None)
            elif event in EVENT_STATUS:
                s = sessions.setdefault(sid, {})
                s["project"] = Path(payload.get("cwd") or "?").name
                s["status"] = EVENT_STATUS[event]
                s["message"] = payload.get("message", "") if event == "Notification" else ""
                s["since"] = now
            self._save()

    def set_usage(self, rate_limits: dict, now: float | None = None) -> None:
        """Guarda `rate_limits` tal como llega al statusline."""
        with self._lock:
            self.data["usage"] = {**rate_limits, "updated": now or time.time()}
            self._save()

    def set_digest(self, digest: dict, now: float | None = None) -> None:
        with self._lock:
            self.data["digest"] = {**digest, "updated": now or time.time()}
            self._save()

    def active_sessions(self, now: float | None = None) -> list[dict]:
        """Sesiones vigentes, primero las que piden atención."""
        now = now or time.time()
        order = {"waiting": 0, "done": 1, "working": 2, "idle": 3}
        live = [
            {"id": sid, **s}
            for sid, s in self.data["sessions"].items()
            if now - s.get("since", 0) < STALE_SECONDS
        ]
        return sorted(live, key=lambda s: (order.get(s["status"], 9), -s["since"]))
