from __future__ import annotations

import argparse
import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .betting import ACTION_LABELS, evaluate_proposition
from .strategy import BasicStrategy

JsonObject = dict[str, Any]

STAKE = 15


@dataclass
class BacktestMetrics:
    rounds_evaluated: int = 0
    turns_evaluated: int = 0
    action_matches: int = 0
    action_match_rate: float = 0.0
    payoff_delta_vs_actual: float = 0.0
    total_predicted_payoff: float = 0.0
    total_actual_payoff: float = 0.0
    simulated_bet_net: float = 0.0
    simulated_bet_hits: int = 0
    simulated_bet_attempts: int = 0
    misses_observed: int = 0
    total_predicted_penalty: float = 0.0
    total_actual_penalty: float = 0.0


def _cell_value(value: int | None) -> float:
    return 0.0 if value is None else float(value)


def _safe_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _bet_settlement(
    simulated_bets: dict[str, bool],
    team_id: str,
    proposition_result: bool,
    stake: float = STAKE,
) -> float:
    if team_id not in simulated_bets:
        return 0.0

    participant_count = len(simulated_bets)
    if participant_count <= 0:
        return 0.0

    correct_count = sum(
        1
        for agree_value in simulated_bets.values()
        if agree_value is not None and agree_value == proposition_result
    )

    if correct_count == 0:
        return -stake

    if correct_count == participant_count:
        return 0.0

    if simulated_bets[team_id] == proposition_result:
        return (participant_count - correct_count) * stake / correct_count
    return -stake


def _normalize_counts(values: dict[int, int]) -> dict[str, int]:
    return {label: values.get(index, 0) for index, label in enumerate(ACTION_LABELS)}


def _load_match_turns(match: JsonObject, target: str) -> list[tuple[int, int, int, bool, float]]:
    team_a = str(match["team_a"])
    team_b = str(match["team_b"])
    turns: list[tuple[int, int, int, bool]] = []
    for turn in sorted(match.get("turns", []), key=lambda item: item["turn_index"]):
        turn_index = int(turn["turn_index"])
        action_a = int(turn["action_a"])
        action_b = int(turn["action_b"])
        missed_a = bool(turn.get("missed_a", False))
        missed_b = bool(turn.get("missed_b", False))
        penalty_a = _safe_float(turn.get("penalty_a"))
        penalty_b = _safe_float(turn.get("penalty_b"))
        if team_a == target:
            turns.append((turn_index, action_a, action_b, missed_a, penalty_a))
        elif team_b == target:
            turns.append((turn_index, action_b, action_a, missed_b, penalty_b))
    return turns


def _round_matchups(round_data: JsonObject, target_team_id: str) -> list[JsonObject]:
    target = str(target_team_id)
    return [
        match
        for match in round_data.get("matches", [])
        if target in {str(match.get("team_a")), str(match.get("team_b"))}
    ]


def _opponent_id(match: JsonObject, target_team_id: str) -> str:
    if str(match["team_a"]) == target_team_id:
        return str(match["team_b"])
    return str(match["team_a"])


def _state_for_turn(
    round_data: JsonObject,
    target_team_id: str,
    opponent_id: str,
    history: list[tuple[int, int]],
    turn_index: int,
) -> JsonObject:
    turns = [
        {"my_action": int(my_action), "opponent_action": int(opponent_action)}
        for my_action, opponent_action in history
    ]
    return {
        "round_index": int(round_data["round_index"]),
        "turn_index": int(turn_index),
        "payoff_matrix": round_data["payoff_matrix"],
        "matchups": [{"opponent_id": opponent_id, "history": turns}],
    }


def _round_total_action_counts(matches: list[JsonObject], target_team_id: str) -> dict[int, int]:
    counts: dict[int, int] = {0: 0, 1: 0, 2: 0}
    for match in matches:
        team_a = str(match["team_a"])
        team_b = str(match["team_b"])
        for turn in match.get("turns", []):
            counts[int(turn["action_a"])] += 1
            counts[int(turn["action_b"])] += 1
    return counts


def evaluate_round_for_team(round_data: JsonObject, team_id: str, strategy: BasicStrategy) -> BacktestMetrics:
    matrix = round_data["payoff_matrix"]
    proposition = round_data.get("bet_proposition")
    matches = _round_matchups(round_data, team_id)
    if not matches:
        return BacktestMetrics()

    metrics = BacktestMetrics(rounds_evaluated=1)
    total_actions = 0
    action_matches = 0
    predicted_payoff = 0.0
    actual_payoff = 0.0
    misses = 0

    observed_target_turns: list[tuple[str, int, int, int]] = []
    # (opponent_id, turn_index, actual_action, predicted_action)
    for match in matches:
        opp_id = _opponent_id(match, team_id)
        turns = _load_match_turns(match, team_id)
        for idx, (turn_index, actual_action, opponent_action, missed, observed_penalty) in enumerate(turns):
            history = [
                (my_action, opp_action)
                for _turn_index, my_action, opp_action, _missed, _penalty in turns[:idx]
            ]
            strategy_state = _state_for_turn(
                round_data=round_data,
                target_team_id=team_id,
                opponent_id=opp_id,
                history=history,
                turn_index=turn_index,
            )
            predicted_action = int(strategy.choose_actions(strategy_state).get(opp_id, 0))
            observed_target_turns.append((opp_id, turn_index, actual_action, predicted_action))

            total_actions += 1
            if predicted_action == actual_action:
                action_matches += 1
            predicted_payoff += _cell_value(matrix[predicted_action][opponent_action])
            actual_penalty = observed_penalty
            predicted_penalty = 0.0
            actual_payoff += _cell_value(matrix[actual_action][opponent_action]) + actual_penalty
            predicted_payoff += predicted_penalty
            metrics.total_actual_penalty += actual_penalty
            metrics.total_predicted_penalty += predicted_penalty
            if missed:
                misses += 1

    metrics.turns_evaluated = total_actions
    metrics.action_matches = action_matches
    metrics.total_predicted_payoff = predicted_payoff
    metrics.total_actual_payoff = actual_payoff
    metrics.payoff_delta_vs_actual = round(predicted_payoff - actual_payoff, 3)
    metrics.misses_observed = misses
    if total_actions:
        metrics.action_match_rate = action_matches / total_actions

    # Counterfactual betting: evaluate this strategy's agree decision using synthetic action totals.
    if proposition:
        total_counts = _round_total_action_counts(matches, team_id)
        predicted_counts = deepcopy(total_counts)
        for opp_id, turn_index, actual_action, predicted_action in observed_target_turns:
            if actual_action == predicted_action:
                continue
            predicted_counts[actual_action] -= 1
            predicted_counts[predicted_action] += 1
            if predicted_counts[actual_action] < 0:
                predicted_counts[actual_action] = 0

        opt_in_state = {
            "round_index": int(round_data["round_index"]),
            "payoff_matrix": matrix,
            "bet_proposition": proposition,
            "matchups": [
                {"opponent_id": _opponent_id(match, team_id)} for match in matches
            ],
        }
        agree = strategy.choose_bet(opt_in_state)
        if agree is not None:
            proposition_result = evaluate_proposition(
                proposition,
                _normalize_counts(predicted_counts),
            )
            metrics.simulated_bet_attempts += 1
            if agree == proposition_result:
                metrics.simulated_bet_hits += 1

            historical_bets = {
                str(bet["team_id"]): bet.get("agree")
                for bet in round_data.get("bets", [])
                if bet.get("team_id")
            }

            simulated_bets = dict(historical_bets)
            if team_id in round_data.get("joiners", []):
                if agree is None:
                    simulated_bets.pop(team_id, None)
                else:
                    simulated_bets[team_id] = bool(agree)

            participant_count = len(simulated_bets)
            if participant_count:
                metrics.simulated_bet_net += _bet_settlement(
                    simulated_bets=simulated_bets,
                    team_id=team_id,
                    proposition_result=proposition_result,
                    stake=STAKE,
                )

    return metrics


def run_backtest(logs_path: Path, team_id: str, strategy: BasicStrategy | None = None) -> BacktestMetrics:
    strategy = strategy or BasicStrategy()
    logs_data: JsonObject = json.loads(logs_path.read_text(encoding="utf-8"))

    aggregate = BacktestMetrics()
    total_actions = 0
    total_matches = 0

    for round_data in logs_data.get("rounds", []):
        if not round_data.get("complete"):
            continue
        round_metrics = evaluate_round_for_team(round_data, team_id, strategy)
        aggregate.rounds_evaluated += round_metrics.rounds_evaluated
        aggregate.turns_evaluated += round_metrics.turns_evaluated
        aggregate.action_matches += round_metrics.action_matches
        aggregate.total_predicted_payoff += round_metrics.total_predicted_payoff
        aggregate.total_actual_payoff += round_metrics.total_actual_payoff
        aggregate.total_predicted_penalty += round_metrics.total_predicted_penalty
        aggregate.total_actual_penalty += round_metrics.total_actual_penalty
        aggregate.payoff_delta_vs_actual += round_metrics.payoff_delta_vs_actual
        aggregate.simulated_bet_net += round_metrics.simulated_bet_net
        aggregate.simulated_bet_attempts += round_metrics.simulated_bet_attempts
        aggregate.simulated_bet_hits += round_metrics.simulated_bet_hits
        aggregate.misses_observed += round_metrics.misses_observed
        total_actions += round_metrics.turns_evaluated
        total_matches += 1

    if total_actions:
        aggregate.action_match_rate = aggregate.action_matches / total_actions
    aggregate.action_match_rate = round(aggregate.action_match_rate, 4)
    aggregate.payoff_delta_vs_actual = round(aggregate.payoff_delta_vs_actual, 3)
    aggregate.simulated_bet_net = round(aggregate.simulated_bet_net, 3)
    aggregate.total_actual_penalty = round(aggregate.total_actual_penalty, 3)
    aggregate.total_predicted_penalty = round(aggregate.total_predicted_penalty, 3)
    return aggregate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backtest a strategy against C3 logs.")
    parser.add_argument("--logs", type=Path, required=True, help="Path to logs JSON")
    parser.add_argument("--team-id", required=True, help="Target team_id in logs")
    args = parser.parse_args(argv)

    result = run_backtest(args.logs, args.team_id)
    print(json.dumps(result.__dict__, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
