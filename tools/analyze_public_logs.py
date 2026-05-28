from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.request import urlopen


DEFAULT_LOGS_URL = "https://c3.qwerty.technology/logs?recent=0"
ACTION_LABELS = {0: "R", 1: "P", 2: "S"}

JsonObject = dict[str, Any]


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize public C3 logs.")
    parser.add_argument("--input", type=Path, help="read logs JSON from a local file")
    parser.add_argument("--url", default=DEFAULT_LOGS_URL, help="public logs URL")
    args = parser.parse_args()

    if args.input:
        logs = json.loads(args.input.read_text())
    else:
        with urlopen(args.url, timeout=10) as response:
            logs = json.loads(response.read().decode("utf-8"))

    print(json.dumps(summarize(logs), indent=2, sort_keys=True))
    return 0


def summarize(logs: JsonObject) -> JsonObject:
    rounds = [round_data for round_data in logs.get("rounds", []) if round_data.get("complete")]
    teams: dict[str, JsonObject] = defaultdict(new_team_summary)

    for round_data in rounds:
        matrix = round_data["payoff_matrix"]
        best_average_actions = argmaxes([row_average(row) for row in matrix])

        for bet in round_data.get("bets", []):
            team = teams[bet["team_id"]]
            team["bet_net"] += int(bet.get("payout") or 0)
            if (bet.get("payout") or 0) > 0:
                team["bet_wins"] += 1
            elif (bet.get("payout") or 0) < 0:
                team["bet_losses"] += 1

        for match in round_data.get("matches", []):
            update_match_team(
                teams[match["team_a"]],
                matrix,
                best_average_actions,
                match.get("turns", []),
                "a",
            )
            update_match_team(
                teams[match["team_b"]],
                matrix,
                best_average_actions,
                match.get("turns", []),
                "b",
            )

    return {
        "complete_rounds": [round_data["round_index"] for round_data in rounds],
        "teams": {
            team_id: finalize_team_summary(summary)
            for team_id, summary in sorted(teams.items())
        },
    }


def update_match_team(
    summary: JsonObject,
    matrix: list[list[int]],
    best_average_actions: list[int],
    turns: list[JsonObject],
    side: str,
) -> None:
    previous_self: int | None = None
    previous_opp: int | None = None

    for turn in turns:
        action = int(turn[f"action_{side}"])
        opponent_side = "b" if side == "a" else "a"
        opponent_action = int(turn[f"action_{opponent_side}"])
        payoff = int(turn[f"payoff_{side}"])

        summary["turns"] += 1
        summary["payoff"] += payoff
        summary["action_counts"][ACTION_LABELS[action]] += 1
        if action in best_average_actions:
            summary["best_average_count"] += 1

        if previous_self is not None:
            summary["post_first_turns"] += 1
            if action == previous_self:
                summary["repeat_self_count"] += 1
            if action == previous_opp:
                summary["copy_previous_opp_count"] += 1
            if action in best_responses_to(matrix, previous_opp):
                summary["best_response_previous_opp_count"] += 1

        previous_self = action
        previous_opp = opponent_action


def new_team_summary() -> JsonObject:
    return {
        "turns": 0,
        "payoff": 0,
        "action_counts": {"R": 0, "P": 0, "S": 0},
        "best_average_count": 0,
        "post_first_turns": 0,
        "repeat_self_count": 0,
        "copy_previous_opp_count": 0,
        "best_response_previous_opp_count": 0,
        "bet_net": 0,
        "bet_wins": 0,
        "bet_losses": 0,
    }


def finalize_team_summary(summary: JsonObject) -> JsonObject:
    turns = max(int(summary["turns"]), 1)
    post_first = max(int(summary["post_first_turns"]), 1)
    return {
        "turns": summary["turns"],
        "payoff": summary["payoff"],
        "action_counts": summary["action_counts"],
        "best_average_rate": round(summary["best_average_count"] / turns, 3),
        "repeat_self_rate": round(summary["repeat_self_count"] / post_first, 3),
        "copy_previous_opp_rate": round(summary["copy_previous_opp_count"] / post_first, 3),
        "best_response_previous_opp_rate": round(
            summary["best_response_previous_opp_count"] / post_first,
            3,
        ),
        "bet_net": summary["bet_net"],
        "bet_wins": summary["bet_wins"],
        "bet_losses": summary["bet_losses"],
    }


def row_average(row: list[int]) -> float:
    return sum(row) / len(row)


def best_responses_to(matrix: list[list[int]], opponent_action: int | None) -> list[int]:
    if opponent_action is None:
        return []
    return argmaxes([row[opponent_action] for row in matrix])


def argmaxes(values: list[float | int]) -> list[int]:
    best = max(values)
    return [index for index, value in enumerate(values) if value == best]


if __name__ == "__main__":
    raise SystemExit(main())
