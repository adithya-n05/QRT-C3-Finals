# C3 Game Protocol

Local summary of the live docs at:

- `https://c3.qwerty.technology/docs/rules`
- `https://c3.qwerty.technology/docs/api`
- `https://c3.qwerty.technology/openapi.json`

If this file conflicts with the live docs, treat the live docs as the source of
truth and update this file.

## Server

- Base URL: `https://c3.qwerty.technology`
- Auth header for gameplay endpoints:

```http
Authorization: Bearer <team-game-key>
```

- Public/read-only endpoints include `/health`, `/time`, `/leaderboard`,
  `/logs`, `/news`, `/dashboard`, and `/dashboard/snapshot`.
- Authenticated gameplay uses `/state`, `/participate`, `/broadcast`, and
  `/action`.

## Phase Loop

Poll `/state`, inspect `phase`, submit the endpoint accepted for that phase,
then sleep around 200-500 ms.

| State phase | Meaning | Submission |
| --- | --- | --- |
| `waiting` | Tournament not active | none |
| `round_pause` | Between rounds | none |
| `opt_in` | Decide whether to join and optionally bet | `/participate` |
| `broadcast` | Send one public message | `/broadcast` |
| `thinking` | Silent planning window | none |
| `action` | Submit per-opponent actions | `/action` |
| `idle` | You sat out this round | none |
| `complete` | Tournament finished | none |

Do not hard-code durations or turn counts. Use deadline fields from `/state`
and the `next_turn_final` flag.

## Actions And Payoffs

Actions are integers:

- `0`: `R`
- `1`: `P`
- `2`: `S`

The matrix is from each player's own perspective. If we play `i` and an
opponent plays `j`, our payoff is `A[i][j]`; the opponent's payoff is
`A[j][i]`. This is not zero-sum.

Later rounds may hide cells as `null`. Hidden cells reveal when any pair plays
that row/column combination, and all remaining hidden cells reveal at round
close.

## Participation

During `opt_in`:

```json
{"round_index": 1, "join": true, "agree": true}
```

- `agree` is optional.
- Joining earns the participation reward at round close.
- Sitting out means no pair payoffs, no participation reward, and no bet.
- Missing the opt-in deadline is treated as sitting out.

## Broadcast

During `broadcast`:

```json
{"round_index": 1, "message": "I will prioritize action R this round."}
```

- One public message per round.
- Maximum 280 characters.
- First valid payload wins.
- Skipping broadcast is allowed.

## Action

During `action`:

```json
{
  "round_index": 1,
  "turn_index": 1,
  "actions": {
    "team_example": 0
  }
}
```

- Submit one action for each current opponent.
- Different actions per opponent are allowed.
- Missing opponent entries receive a random substitute and a `-1` penalty for
  that pair.
- First valid payload wins.
- `turn_index` must match the current state; future actions are not queued.

## Betting

Betting is part of `/participate`; there is no `/bet` endpoint.

Propositions:

- `X>=*`: action `X` is modal, ties allowed.
- `X>Y`: strictly more `X` submissions than `Y`.
- `X>=Y`: at least as many `X` submissions as `Y`.

`X` and `Y` are `R`, `P`, or `S`. The server counts every action submission
across every pair and turn, including random substitutes for missed actions.

Settlement is parimutuel:

- Correct bettors get stake back plus an equal share of losing stakes.
- Incorrect bettors lose the stake.
- If all bettors are correct, stakes are refunded.
- If all bettors are incorrect, stakes go to the house.

## Scoring

Total score is:

- pair payoffs
- participation reward
- net betting payout
- penalties

The leaderboard exposes these as Pay, Pot, Bet, Pen, and Total.

## Operational Pitfalls

- Use server time fields, not local wall clock, for deadlines.
- Budget for RTT and leave a safety margin before deadline.
- Watch rate limits: 30 requests/second/key, burst 60.
- Check response bodies for `accepted: false`; HTTP 200 can still be a soft
  rejection.
- Coordinate one live driver per team key because submissions are
  first-valid-wins.
