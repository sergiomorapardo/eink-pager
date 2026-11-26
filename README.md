# eink-pager

Un pager de tinta electrónica que te ahorra atención: en vez de vigilar terminales,
correo y el consumo del plan de Claude, miras una pantallita que solo te dice
**qué te necesita ahora**.

![preview](docs/preview.png)

| Zona | Qué muestra | De dónde sale |
|---|---|---|
| Arriba | % usado de la ventana de 5 h y de 7 días, y cuánto falta para el reset | `rate_limits` que Claude Code le pasa al statusline |
| Centro | Sesiones de Claude Code que piden permiso (invertido) o terminaron (✓) | Hooks de Claude Code |
| Abajo | Próximo evento y hasta 3 correos que piden acción | `claude -p` + conectores de Gmail/Calendar |

Si nada te necesita, la pantalla dice "Nada te necesita" y ya.

## Arquitectura

```
Claude Code ── hooks ──────────┐
statusline ── rate_limits ─────┼──► servidor local :8787 ──► /frame.bmp ──► ESP32 + e-paper
claude -p (Gmail/Calendar) ────┘         (estado + render)    /           ──► simulador web
```

El dispositivo es "tonto": baja una imagen de 1 bit y la pinta. Todo se decide en la Mac.

## Uso

```bash
uv sync
uv run python -m pager.server          # simulador en http://127.0.0.1:8787
uv run python scripts/install.py        # vista previa del cambio a ~/.claude/settings.json
uv run python scripts/install.py --apply
uv run python -m pager.digest --dry-run # digest de ejemplo, sin llamar a Claude
uv run pytest
```

`pager.digest` sin `--dry-run` corre `claude -p` con Haiku y **gasta cuota del plan**.
La idea es programarlo cada 30–60 min con launchd o `/schedule` una vez calibrado el costo.

## Pendiente

- [ ] Calibrar costo real de una corrida de `pager.digest` y elegir frecuencia.
- [ ] launchd para el servidor y el digest.
- [ ] Hardware y firmware (ver `firmware/README.md`).
- [ ] Botón físico: "visto" para descartar avisos.
