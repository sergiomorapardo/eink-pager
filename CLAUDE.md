# eink-pager

- Python 3.12 con uv. Dependencia única: Pillow. El servidor es stdlib (`http.server`).
- `pager/state.py` estado + persistencia; `pager/render.py` imagen 1 bit 296×128;
  `pager/server.py` HTTP; `pager/digest.py` resumen con `claude -p`.
- Pruebas: `uv run pytest`. Después de tocar el render, regenera `docs/preview.png` y míralo.
- `pager.digest` sin `--dry-run` gasta cuota del plan: pedir aprobación antes de correrlo.
- Los hooks nunca deben bloquear ni fallar una sesión de Claude Code (timeout corto, exit 0).
