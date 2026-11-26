#!/usr/bin/env bash
# Envoltorio del statusline: manda `rate_limits` al pager y luego pinta el
# statusline de siempre. Uso en settings.json:
#   "command": "bash ~/Developer/eink-pager/hooks/statusline_tee.sh bash ~/.claude/statusline.sh"
# Se limita a un envío cada 30 s porque el statusline se refresca cada 2 s.
input=$(cat)
stamp="${TMPDIR:-/tmp}/eink-pager-usage.stamp"
if [ ! -f "$stamp" ] || [ $(( $(date +%s) - $(stat -f %m "$stamp" 2>/dev/null || echo 0) )) -ge 30 ]; then
  touch "$stamp"
  limits=$(printf '%s' "$input" | jq -c '.rate_limits // empty' 2>/dev/null)
  if [ -n "$limits" ]; then
    curl -s -m 1 -X POST -H 'Content-Type: application/json' \
      --data-binary "$limits" "${PAGER_URL:-http://127.0.0.1:8787}/usage" >/dev/null 2>&1 &
  fi
fi
printf '%s' "$input" | "$@"
