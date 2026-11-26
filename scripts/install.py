"""Conecta el pager a Claude Code editando ~/.claude/settings.json.

Agrega los hooks (SessionStart, UserPromptSubmit, Notification, Stop, SessionEnd)
y envuelve el statusline actual con hooks/statusline_tee.sh. Hace copia de
seguridad antes. Por defecto solo muestra el cambio; usa --apply para escribir.
"""

import argparse
import json
import shutil
import time
from pathlib import Path

SETTINGS = Path.home() / ".claude/settings.json"
REPO = Path(__file__).resolve().parent.parent
NOTIFY = f"bash {REPO}/hooks/notify.sh"
TEE = f"bash {REPO}/hooks/statusline_tee.sh"
EVENTS = ["SessionStart", "UserPromptSubmit", "Notification", "Stop", "SessionEnd"]


def patched(settings: dict) -> dict:
    s = json.loads(json.dumps(settings))
    hooks = s.setdefault("hooks", {})
    for ev in EVENTS:
        groups = hooks.setdefault(ev, [])
        if not any(h.get("command") == NOTIFY for g in groups for h in g.get("hooks", [])):
            groups.append({"hooks": [{"type": "command", "command": NOTIFY, "timeout": 5}]})
    sl = s.get("statusLine")
    if sl and sl.get("type") == "command" and not sl["command"].startswith(TEE):
        sl["command"] = f"{TEE} {sl['command']}"
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    current = json.loads(SETTINGS.read_text())
    new = patched(current)
    print(json.dumps({k: new[k] for k in ("hooks", "statusLine") if k in new}, indent=2))
    if args.apply:
        backup = SETTINGS.with_name(f"settings.json.bak-{int(time.time())}")
        shutil.copy2(SETTINGS, backup)
        SETTINGS.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n")
        print(f"Escrito. Copia de seguridad en {backup}")
    else:
        print("\n(solo vista previa; corre con --apply para escribir)")


if __name__ == "__main__":
    main()
