from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .betting import ACTION_TO_LABEL, LABEL_TO_ACTION, proposition_labels


Matrix = list[list[int | None]]
JsonObject = dict[str, Any]


@dataclass
class BasicStrategy:
    """Small deterministic baseline policy.

    The goal is not to be optimal. It is to provide a clear, testable harness
    that always submits complete payloads and can be improved safely.
    """

    hidden_cell_value: float = 0.0
    bet_confidence_margin: float = 1.0

    def should_join(self, state: JsonObject) -> bool:
        return state.get("phase") == "opt_in"

    def choose_bet(self, state: JsonObject) -> bool | None:
        proposition = state.get("bet_proposition")
        matrix = state.get("payoff_matrix")
        if not proposition or not matrix:
            return None

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
            return "I am online and will submit complete actions."

        best_action, _ = self.best_average_action(matrix)
        label = ACTION_TO_LABEL[best_action]
        return f"I am prioritizing action {label} when the matrix supports it."

    def choose_actions(self, state: JsonObject) -> dict[str, int]:
        matrix = state.get("payoff_matrix")
        if not matrix:
            default_action = 0
        else:
            default_action, _ = self.best_average_action(matrix)

        actions: dict[str, int] = {}
        for opponent_id in opponent_ids(state):
            last_action = last_observed_opponent_action(state, opponent_id)
            if matrix and last_action is not None:
                actions[opponent_id] = self.best_response_to(matrix, last_action)
            else:
                actions[opponent_id] = default_action
        return actions

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
    for matchup in state.get("matchups", []):
        if matchup.get("opponent_id") != opponent_id:
            continue
        history = matchup.get("turns") or matchup.get("history") or []
        for turn in reversed(history):
            action = turn.get("opponent_action")
            if action in LABEL_TO_ACTION.values():
                return int(action)
    return None
