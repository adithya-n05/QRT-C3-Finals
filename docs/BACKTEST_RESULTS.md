# Backtest Results

This records replay checks against locally stored public log snapshots. Raw
capture files are intentionally not committed; this document keeps the usable
summary.

## 2026-05-28 Stored Public Logs

Source snapshot:

```text
computation_logs/20260528T141505Z/raw/live_capture_active/logs_100.json
```

The snapshot contains two completed rounds and 39 target-team turns per bot.
Command shape:

```bash
PYTHONPATH=src python -m c3_harness.backtest \
  --logs computation_logs/20260528T141505Z/raw/live_capture_active/logs_100.json \
  --team-id <team_id>
```

| Team replayed | Action match rate | Actual payoff | Strategy payoff | Delta |
| --- | ---: | ---: | ---: | ---: |
| `team_bot_br_last` | 0.4872 | -6 | 3 | +9 |
| `team_bot_ev_heuristic` | 0.8462 | 11 | 13 | +2 |
| `team_bot_gpt_nano` | 0.2821 | -20 | -3 | +17 |
| `team_bot_random_action` | 0.3333 | -38 | 6 | +44 |

No misses were observed. The strategy made no simulated betting attempts on
these two completed rounds, which is acceptable for now because the current
betting policy is intentionally conservative.

## Takeaways

- The current policy improves counterfactual payoff against all four practice
  bots on this stored sample.
- The smallest margin is against `bot_ev_heuristic`, which is expected because
  the strategy intentionally models that bot similarly to its actual row-average
  behavior.
- The largest gains come from not copying weak/noisy play against `bot_gpt_nano`
  and `bot_random_action`.
- Next tuning target: betting forecast. We need more completed logged rounds
  before raising bet frequency.
