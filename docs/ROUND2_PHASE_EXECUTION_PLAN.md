# Round 2 Phase Execution Plan

## Objective

Maximise cumulative score in round 2 with:

- rapid exploitation of opponent behavior,
- resilient non-exploitable signaling,
- controlled betting under confidence,
- reproducible offline evaluation from local logs.

## Phase-by-Phase Execution Plan

### Phase 0 – Signal Capture and Baseline Replay (now)

1. Keep live harness in dry-run mode while capturing:
   - `/state` every poll,
   - `/state` payload at decision boundaries,
   - decision payloads and accepted responses.
2. Export live/completion rounds from `/logs?recent=0` into `stage2_logs/<run_id>/`.
3. Parse round-complete logs into per-turn opponent-action history.
4. Evaluate baseline `BasicStrategy`:
   - action prediction hit-rate against historical opponent moves,
   - payoff delta vs executed action,
   - simulated bet calibration under round propositions.
5. Identify weak spots:
   - teams that track phase-level broadcast semantics,
   - teams whose policy is highly periodic,
   - round-specific hidden-cell effects.

### Phase 1 – Model-Driven Upgrade (before round start)

1. Add per-opponent strategy adapters:
   - one-step transition memory,
   - known bot class detectors (`br_last`, `ev_heuristic`, random/counter patterns),
   - confidence gating for exploitation.
2. Introduce controlled randomness:
   - entropy-based epsilon near round open,
   - re-raise uncertainty when KL-like prediction drift spikes,
   - reduce variance after two consecutive adverse outcome runs.
3. Deploy anti-pattern broadcast policy:
   - no fixed action phrase map by round,
   - rotating templates with occasional mismatch,
   - no message-to-action mapping.

### Phase 2 – Live Execution and Live Learning (round 2 start)

1. Start harness with market logging enabled and one driver only:
   - `--log-market`
   - fixed `C3_POLL_INTERVAL_SECONDS`
2. Monitor stage-2 run log tail at each phase transition:
   - opt-in decision,
   - broadcast string chosen,
   - per-opponent action payload,
   - response acceptance/missing.
3. If rate limits approach 30/s:
   - keep poll at 200–350ms,
   - no additional polling endpoints from the action path.
4. On first 2 turns:
   - avoid high-stake bets unless confidence is above threshold,
   - expand observation window for each opponent model.

### Phase 3 – Post-Round Retuning (repeat between rounds)

1. Pull completed logs and backtest every strategy candidate on real rounds.
2. Compare candidates by:
   - simulated payoff delta,
   - bet return distribution,
   - variance profile (negative skew / drawdown),
   - model confusion score (broadcast decoupling index).
3. Promote highest confidence candidate for next round only when its 95% directional confidence
   exceeds baseline on at least two metrics.

## Atomic Commit Plan (per change set)

Each commit should be narrowly scoped and reversible:

1. `feat: add market telemetry logger`
2. `feat: add backtest simulator with historical round replay`
3. `feat: integrate logger into runner`
4. `feat: tighten opponent model and confidence gates`
5. `feat: introduce anti-telemetry broadcast schedule`
6. `feat: add betting confidence gates and house-risk guardrails`
7. `test: add replay parity tests for new strategy module`
8. `chore: add stage2_logs to ignore and docs links`

## TDD Loop

1. Write a failing test for each behavior.
2. Implement just enough code to pass.
3. Add a red-blue-green safety metric assertion:
   - if score metric drops in backtest below current baseline by threshold, block merge.
4. Add regression fixture tests for:
   - hidden payoff cell handling,
   - sequence reversal behavior,
   - proposition payout edge cases,
   - missed-action penalty impact.
5. Keep all tests passing before enabling any phase-2 live flag.

## Performance Priority

- O(1) updates per state poll for running counters.
- O(T) per log replay where T is total turns.
- No recursive reconstruction during live loop.
- Precompute opponent keys and avoid rebuilding matrices in hot paths.
