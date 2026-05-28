# Backtest and Logging Runbook

## What the logger captures

`MarketLogger` stores an append-only event stream at:

- `stage2_logs/<run_id>/stage2_events.ndjson`

Each event includes:

- UTC timestamp,
- run id,
- round / turn,
- phase,
- normalized state snapshot,
- compact payload (action count and targets),
- response.

## Stage 2 Data Path

1. Start round 2 driver with logging:

```bash
PYTHONPATH=src C3_GAME_KEY=... \
python -m c3_harness.runner --live --log-market
```

2. During run:

- `/state` is logged each poll,
- `opt_in`, `broadcast`, `action` decisions are logged with payload + response.

3. After a complete round:

```bash
curl -s https://c3.qwerty.technology/logs?recent=0 > stage2_logs/<run_id>/rounds.json
```

4. Replay benchmark on your team:

```bash
PYTHONPATH=src python -m c3_harness.backtest \
  --logs stage2_logs/<run_id>/rounds.json \
  --team-id <team_id>
```

## Evaluation Metrics to Track

- action-match-rate on replay,
- action-predicted payoff delta vs actual,
- simulated bet hit-rate and net,
- observed missed-action penalties,
- per-opponent class stability (switch count by phase).

## Deployment Rule

Promote to live execution only when:

1. replay action-predicted delta is positive over at least the last 2 completed rounds,
2. simulated bet-risk stays inside configured drawdown envelope,
3. broadcast decoupling still prevents phrase-to-action predictability (manual inspection + periodic hash check).
