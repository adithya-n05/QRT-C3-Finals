from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .betting import ACTION_LABELS, ACTION_TO_LABEL, LABEL_TO_ACTION, evaluate_proposition, proposition_labels


Matrix = list[list[int | None]]
JsonObject = dict[str, Any]


@dataclass
class BasicStrategy:
    """Deterministic competition policy.

    The policy stays fast enough for two-second turns, submits complete action
    payloads, and uses only information allowed by the public game protocol.
    """

    hidden_cell_value: float = 0.0
    bet_confidence_margin: float = 1.0
    bet_count_margin: float = 2.0
    steering_future_weight: float = 0.65
    expected_turns: float = 8.0
    default_opponent_count: int = 3

    def should_join(self, state: JsonObject) -> bool:
        if state.get("phase") != "opt_in":
            return False

        matrix = state.get("payoff_matrix")
        if not matrix:
            return True

        return self.expected_round_value(state, matrix) >= 0.0

    def choose_bet(self, state: JsonObject) -> bool | None:
        proposition = state.get("bet_proposition")
        matrix = state.get("payoff_matrix")
        if not proposition or not matrix:
            return None

        forecast_counts = self.forecast_action_counts(state, matrix)
        if forecast_counts:
            count_margin = proposition_count_margin(proposition, forecast_counts)
            if count_margin < self.bet_count_margin:
                return None
            return evaluate_proposition(proposition, forecast_counts)

        best_action, margin = self.best_average_action(matrix)
        if margin < self.bet_confidence_margin:
            return None

        left, right, kind = proposition_labels(proposition)
        best_label = ACTION_TO_LABEL[best_action]

        if kind == "modal":
            return best_label == left
        if right is None:
            return None

        if best_label == left:
            return True
        if best_label == right:
            return False
        return None

    def choose_broadcast(self, state: JsonObject) -> str:
        matrix = state.get("payoff_matrix")
        if not matrix:
            return "Online. Broadcasts are noisy; actions are per-opponent."

        best_action, _ = self.best_average_action(matrix)
        decoy = self.decoy_action(best_action, int(state.get("round_index", 0)))
        other = self.decoy_action(decoy, int(state.get("round_index", 1)))
        decoy_label = ACTION_TO_LABEL[decoy]
        other_label = ACTION_TO_LABEL[other]
        templates = [
            "Reading every broadcast. My public signal is intentionally noisy.",
            f"Testing a {decoy_label}/{other_label} mix; final-turn logic may invert.",
            f"Leaning {decoy_label} if the table stays stable. Per-opponent overrides apply.",
            "Bet signal and action signal are split this round.",
            "I am using different actions per opponent, so aggregate tells are weak.",
        ]
        return templates[int(state.get("round_index", 0)) % len(templates)]

    def choose_actions(self, state: JsonObject) -> dict[str, int]:
        matrix = state.get("payoff_matrix")
        if not matrix:
            default_action = 0
        else:
            default_action, _ = self.best_average_action(matrix)

        actions: dict[str, int] = {}
        for opponent_id in opponent_ids(state):
            if matrix and is_br_last_bot(opponent_id):
                actions[opponent_id] = self.choose_against_br_last(state, opponent_id, matrix)
            elif matrix:
                distribution = self.predict_opponent_distribution(state, opponent_id, matrix)
                actions[opponent_id] = self.best_against_distribution(matrix, distribution)
            else:
                actions[opponent_id] = default_action
        return actions

    def expected_round_value(self, state: JsonObject, matrix: Matrix) -> float:
        best_action, _ = self.best_average_action(matrix)
        expected_turn_payoff = sum(
            self.cell_value(cell)
            for cell in matrix[best_action]
        ) / len(matrix[best_action])
        opponent_count = len(opponent_ids(state)) or self.default_opponent_count
        participation_reward = float(state.get("pot") or 5)
        return participation_reward + expected_turn_payoff * self.expected_turns * opponent_count

    def forecast_action_counts(self, state: JsonObject, matrix: Matrix) -> dict[str, int] | None:
        ids = opponent_ids(state)
        if not ids:
            return None

        counts = {label: 0 for label in ACTION_LABELS}
        for opponent_id in ids:
            if is_br_last_bot(opponent_id):
                our_action = self.choose_against_br_last(state, opponent_id, matrix)
            else:
                distribution = self.predict_opponent_distribution(state, opponent_id, matrix)
                our_action = self.best_against_distribution(matrix, distribution)

            opponent_distribution = self.predict_opponent_distribution(state, opponent_id, matrix)
            opponent_action = max(
                opponent_distribution,
                key=lambda action: opponent_distribution[action],
            )

            counts[ACTION_TO_LABEL[our_action]] += 1
            counts[ACTION_TO_LABEL[opponent_action]] += 1
        return counts

    def best_average_action(self, matrix: Matrix) -> tuple[int, float]:
        row_scores = [sum(self.cell_value(cell) for cell in row) / len(row) for row in matrix]
        ranked = sorted(enumerate(row_scores), key=lambda item: item[1], reverse=True)
        best_action, best_score = ranked[0]
        runner_up = ranked[1][1] if len(ranked) > 1 else best_score
        return best_action, best_score - runner_up

    def best_response_to(self, matrix: Matrix, opponent_action: int) -> int:
        column_scores = [
            self.cell_value(matrix[action][opponent_action])
            for action in range(len(matrix))
        ]
        return max(range(len(column_scores)), key=lambda action: column_scores[action])

    def best_against_distribution(self, matrix: Matrix, distribution: dict[int, float]) -> int:
        values = self.expected_values_against(matrix, distribution)
        return max(range(len(values)), key=lambda action: values[action])

    def expected_values_against(self, matrix: Matrix, distribution: dict[int, float]) -> list[float]:
        return [
            sum(
                self.cell_value(matrix[action][opponent_action]) * probability
                for opponent_action, probability in distribution.items()
            )
            for action in range(len(matrix))
        ]

    def choose_against_br_last(
        self,
        state: JsonObject,
        opponent_id: str,
        matrix: Matrix,
    ) -> int:
        distribution = self.predict_opponent_distribution(state, opponent_id, matrix)
        current_values = self.expected_values_against(matrix, distribution)
        if state.get("next_turn_final"):
            return max(range(len(current_values)), key=lambda action: current_values[action])

        # bot_br_last responds to the previous opponent action. Our action now
        # can therefore steer its next action, so include a one-turn lookahead.
        total_values: list[float] = []
        for action, current_value in enumerate(current_values):
            induced_next = self.best_response_to(matrix, action)
            future_value = max(
                self.cell_value(matrix[future_action][induced_next])
                for future_action in range(len(matrix))
            )
            total_values.append(current_value + self.steering_future_weight * future_value)
        return max(range(len(total_values)), key=lambda action: total_values[action])

    def predict_opponent_distribution(
        self,
        state: JsonObject,
        opponent_id: str,
        matrix: Matrix,
    ) -> dict[int, float]:
        if is_br_last_bot(opponent_id):
            previous_my_action = last_observed_my_action(state, opponent_id)
            if previous_my_action is not None:
                return peaked_distribution(self.best_response_to(matrix, previous_my_action), 0.9)

        if is_ev_heuristic_bot(opponent_id):
            best_action, _ = self.best_average_action(matrix)
            return peaked_distribution(best_action, 0.8)

        history_distribution = observed_opponent_distribution(state, opponent_id)
        if history_distribution:
            return history_distribution

        best_action, _ = self.best_average_action(matrix)
        return peaked_distribution(best_action, 0.55)

    def decoy_action(self, best_action: int, round_index: int) -> int:
        return (best_action + 1 + (round_index % 2)) % 3

    def cell_value(self, value: int | None) -> float:
        if value is None:
            return self.hidden_cell_value
        return float(value)


def opponent_ids(state: JsonObject) -> list[str]:
    ids: list[str] = []
    for matchup in state.get("matchups", []):
        opponent_id = matchup.get("opponent_id")
        if opponent_id:
            ids.append(opponent_id)
    return ids


def last_observed_opponent_action(state: JsonObject, opponent_id: str) -> int | None:
    for turn in reversed(matchup_history(state, opponent_id)):
        action = first_int(turn, ("opponent_action", "their_action", "action"))
        if action in LABEL_TO_ACTION.values():
            return int(action)
    return None


def last_observed_my_action(state: JsonObject, opponent_id: str) -> int | None:
    for turn in reversed(matchup_history(state, opponent_id)):
        action = first_int(turn, ("my_action", "our_action"))
        if action in LABEL_TO_ACTION.values():
            return int(action)
    return None


def observed_opponent_distribution(state: JsonObject, opponent_id: str) -> dict[int, float] | None:
    counts = {0: 1.0, 1: 1.0, 2: 1.0}
    observations = 0
    for turn in matchup_history(state, opponent_id):
        action = first_int(turn, ("opponent_action", "their_action", "action"))
        if action in LABEL_TO_ACTION.values():
            counts[int(action)] += 1.0
            observations += 1
    if observations == 0:
        return None
    total = sum(counts.values())
    return {action: count / total for action, count in counts.items()}


def matchup_history(state: JsonObject, opponent_id: str) -> list[JsonObject]:
    for matchup in state.get("matchups", []):
        if matchup.get("opponent_id") != opponent_id:
            continue
        return list(matchup.get("turns") or matchup.get("history") or [])
    return []


def first_int(source: JsonObject, keys: tuple[str, ...]) -> int | None:
    for key in keys:
        value = source.get(key)
        if value in LABEL_TO_ACTION.values():
            return int(value)
    return None


def peaked_distribution(action: int, probability: float) -> dict[int, float]:
    spillover = (1.0 - probability) / 2.0
    return {
        candidate: probability if candidate == action else spillover
        for candidate in LABEL_TO_ACTION.values()
    }


def is_br_last_bot(opponent_id: str) -> bool:
    return "bot_br_last" in opponent_id


def is_ev_heuristic_bot(opponent_id: str) -> bool:
    return "bot_ev_heuristic" in opponent_id


def proposition_count_margin(proposition: str, counts: dict[str, int]) -> int:
    left, right, kind = proposition_labels(proposition)
    if kind == "modal":
        competitors = [count for label, count in counts.items() if label != left]
        return counts[left] - max(competitors)
    if right is None:
        return 0
    return abs(counts[left] - counts[right])
