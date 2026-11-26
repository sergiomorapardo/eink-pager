# TODO

## Needs a decision (explicit approval)

- [ ] **Connect to Claude Code**: `uv run python scripts/install.py --apply`.
  Adds 5 hooks to `~/.claude/settings.json` and wraps the statusline (backs it up first).
  Without it the pager receives no sessions or usage.
- [ ] **First real digest run**: `uv run python -m pager.digest` (no `--dry-run`).
  Spends plan quota. Goals: measure cost (tokens/USD) and confirm the Gmail/Calendar
  connectors work inside `claude -p`.
- [ ] **Private GitHub repo**, push the code, and set up the Claude review workflow
  so the PR rules in `AGENTS.md` can apply.

## Software

- [ ] Pick the digest frequency from the measured cost (every 30 or 60 min? work hours only?).
- [ ] launchd job to keep the server running.
- [ ] launchd job or `/schedule` for the digest.
- [ ] Dismiss alerts ("seen"): `POST /ack` endpoint, later a physical button.
- [ ] Hide `done` sessions after a while (they currently last up to 6 h).
- [ ] Visual alert when 5-hour usage crosses a threshold (e.g. 80%).
- [ ] Show when the digest is stale (e.g. more than 2 h without updates).
- [ ] Port `merge_pr.py` / `cleanup_merged.py` from AgenticDebtCollection, with a confirmation step before deleting anything.

## Hardware

- [ ] Buy: ESP32 + Waveshare 2.9" e-Paper (296×128 B/W) or LILYGO T5, plus a LiPo battery.
- [ ] PlatformIO + GxEPD2 firmware (plan in `firmware/README.md`).
- [ ] Start the server with `--host 0.0.0.0` so the ESP32 can reach it.

## Ideas

- [ ] 3D-printed case.
- [ ] More sources: GitHub PRs awaiting your review, broken CI.
