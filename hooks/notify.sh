#!/usr/bin/env bash
# Hook de Claude Code: reenvía el JSON del evento al pager.
# Nunca bloquea ni falla la sesión: timeout corto, en segundo plano y salida 0.
payload=$(cat)
curl -s -m 1 -X POST -H 'Content-Type: application/json' \
  --data-binary "$payload" "${PAGER_URL:-http://127.0.0.1:8787}/hook" >/dev/null 2>&1 &
exit 0
