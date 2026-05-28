# Competition Strategy

This is the current tactical read from the live docs, public dashboard, public
logs, and presentation images. Treat the live API and `/logs` as fresher than
this file if they diverge.

## Objective

Win by combining reliability, matrix EV, opponent modeling, and betting
discipline. The game is short-phase and first-valid-wins, so a fast complete
payload beats a clever action that arrives late.

## Current Information

- The repo contains a Python harness under `src/c3_harness/` with dry-run by
  default, live mode behind `--live`, tests under `tests/`, and local protocol
  docs under `docs/`.
- The live game is a repeated 3x3 matrix game. Payoffs are symmetric
  perspective, not zero-sum: our payoff is `A[our_action][their_action]`.
- Each round has opt-in, broadcast, thinking, action, complete, and pause
  phases. Use server deadlines from `/state`; do not hard-code timing.
- Actions are per opponent. Broadcast is one public message. Bets are placed
  only during opt-in and settle on aggregate action counts.
- Public `/logs?recent=0` exposes completed matrices, actions, broadcasts,
  bets, and outcomes. Use it for read-only opponent modeling.

## Opponent Findings From Practice Bots

These observations came from public logs during the bot practice stage.

- `bot_br_last`: after turn 1, it best-responds to the opponent's previous
  action with near-perfect reliability. This is steerable: our current action
  can induce its next action.
- `bot_ev_heuristic`: mostly plays the row with the highest average payoff
  against a uniform opponent. Counter it by best-responding to that likely row.
- `bot_gpt_nano`: mixed and less predictable; use recent observed actions with
  smoothing instead of trusting broadcasts.
- `bot_random_action`: noisy tactically, but has profited from betting
  variance. Do not assume leaderboard rank equals strategic strength.

## Action Policy

1. Join only when expected round value is non-negative. Participation reward is
   material, but it can be overwhelmed by 6-12 turns against multiple opponents
   on a badly negative matrix.
2. Always submit one action per opponent. A missing entry creates avoidable
   random action and penalty risk.
3. For known `bot_br_last`, use one-turn lookahead except on final turn:
   current payoff plus a weighted future value from the action it will be
   induced to play next.
4. For known `bot_ev_heuristic`, predict the highest row-average action and
   best-respond to it.
5. For unknown opponents and humans, start from row-average priors, then switch
   to smoothed recent action frequencies as soon as history exists.
6. On `next_turn_final`, stop investing in future steering and maximize current
   expected payoff.

## Broadcast Policy

Broadcast should reduce opponents' ability to infer our actual action plan.
Use legal cheap talk, but avoid precise commitments that humans can exploit.

- Do not broadcast the true best action.
- Prefer plausible, low-information messages: noisy public signal, per-opponent
  overrides, final-turn inversion, split bet/action signal.
- Make the message compatible with multiple future actions. A good broadcast
  should still look defensible after any action we play.
- If a human tries to coordinate through broadcasts, only cooperate when the
  matrix makes mutual cooperation strictly valuable and their observed actions
  support it. Otherwise treat the message as non-binding.
- Keep broadcasts under 280 chars and deterministic by round so dry-runs are
  reproducible.

Current harness behavior follows this policy in `BasicStrategy.choose_broadcast`.

## Betting Policy

Betting is high variance because the stake is 15 and settlement is parimutuel.

- Bet only when the proposition aligns strongly with our aggregate action
  forecast. The harness now forecasts counts from our planned actions and the
  predicted modal opponent actions when matchups are known.
- Abstain when the matrix is close, masked, or likely human behavior dominates
  the action count.
- Remember one-sided correct markets refund only; the upside comes from being
  right when others are wrong.
- Public dashboard bet counts are useful for humans, but the live agent should
  rely on authenticated `/state` for submissions.

## Operational Plan

- Run exactly one live driver for the team key.
- Keep the driver printing one JSON decision per step; this satisfies the need
  to state what is happening at every turn and gives a live audit trail.
- Before live mode, run:

```bash
PYTHONPATH=src python -m unittest discover -s tests
PYTHONPATH=src python -m c3_harness.runner --once
```

- Live mode only after `C3_GAME_KEY` is set:

```bash
PYTHONPATH=src python -m c3_harness.runner --live
```

## Next Improvements

- Persist `/logs` snapshots and compute per-team action models automatically.
- Add a replay evaluator that scores candidate strategies against historical
  rounds.
- Improve betting by expanding count forecasts from our local matchups to the
  full active field when public logs reveal stable participant behavior.
- Add a round-2 stage logger and runbook for quick iteration on proposition
  assumptions.

## Round 2 Execution Anchors

- `--log-market` is the default for stage-two experiments.
- Replay all complete rounds before each strategy promotion.
- Promotion criteria:
  - positive counterfactual payoff delta vs existing policy,
  - no collapse in action-match confidence across the first two turns,
  - improved or neutral expected bet NPV under recorded market totals.

See:

- `src/c3_harness/backtest.py`
- `src/c3_harness/telemetry.py`
