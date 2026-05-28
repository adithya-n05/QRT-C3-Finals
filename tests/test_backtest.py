from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from c3_harness.backtest import run_backtest
from c3_harness.strategy import BasicStrategy


class BacktestTests(unittest.TestCase):
    def _build_round(self, me_agree: bool, opp_agree: bool) -> dict:
        proposition = "R>=*"
        bets = [
            {"team_id": "team_me", "agree": me_agree},
            {"team_id": "team_opp", "agree": opp_agree},
        ]
        return {
            "round_index": 1,
            "complete": True,
            "payoff_matrix": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            "bet_proposition": proposition,
            "joiners": ["team_me", "team_opp"],
            "bets": bets,
            "matches": [
                {
                    "match_id": "r1__team_me__team_opp",
                    "team_a": "team_me",
                    "team_b": "team_opp",
                    "turns": [
                        {
                            "turn_index": 1,
                            "action_a": 1,
                            "action_b": 2,
                            "payoff_a": 0,
                            "payoff_b": 0,
                            "penalty_a": 0,
                            "penalty_b": 0,
                            "missed_a": False,
                            "missed_b": False,
                        }
                    ],
                }
            ],
        }

    def test_all_wrong_bets_pay_negative(self) -> None:
        # proposition R>=* is FALSE with these counts, so True is incorrect.
        payload = {"rounds": [self._build_round(me_agree=True, opp_agree=True)]}

        class AlwaysAgreeStrategy(BasicStrategy):
            def choose_actions(self, state):  # type: ignore[override]
                return {"team_opp": 1}

            def choose_bet(self, state):  # type: ignore[override]
                return True

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "logs.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = run_backtest(path, "team_me", strategy=AlwaysAgreeStrategy())

        self.assertEqual(result.simulated_bet_net, -15.0)

    def test_all_correct_bets_refund_only(self) -> None:
        # proposition R>=* is FALSE with these counts, so False is correct.
        payload = {"rounds": [self._build_round(me_agree=False, opp_agree=False)]}

        class AlwaysDisagreeStrategy(BasicStrategy):
            def choose_actions(self, state):  # type: ignore[override]
                return {"team_opp": 1}

            def choose_bet(self, state):  # type: ignore[override]
                return False

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "logs.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = run_backtest(path, "team_me", strategy=AlwaysDisagreeStrategy())

        self.assertEqual(result.simulated_bet_net, 0.0)

    def test_actual_penalties_are_counted(self) -> None:
        payload = {
            "rounds": [
                {
                    "round_index": 1,
                    "complete": True,
                    "payoff_matrix": [[3, 0, 0], [0, 1, 0], [0, 0, 1]],
                    "joiners": ["team_me", "team_opp"],
                    "matches": [
                        {
                            "match_id": "r1__team_me__team_opp",
                            "team_a": "team_me",
                            "team_b": "team_opp",
                            "turns": [
                                {
                                    "turn_index": 1,
                                    "action_a": 0,
                                    "action_b": 0,
                                    "payoff_a": 3,
                                    "payoff_b": 1,
                                    "penalty_a": -1,
                                    "penalty_b": 0,
                                    "missed_a": False,
                                    "missed_b": False,
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        class ForcedPredictionStrategy(BasicStrategy):
            def choose_actions(self, state):  # type: ignore[override]
                return {"team_opp": 0}

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "logs.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = run_backtest(path, "team_me", strategy=ForcedPredictionStrategy())

        self.assertEqual(result.total_actual_payoff, 2.0)
        self.assertEqual(result.total_predicted_payoff, 3.0)
        self.assertEqual(result.total_actual_penalty, -1.0)
        self.assertEqual(result.action_match_rate, 1.0)

    def test_run_backtest_reads_complete_rounds_and_scores(self) -> None:
        payload = {
            "rounds": [
                {
                    "round_index": 1,
                    "complete": True,
                    "payoff_matrix": [[3, 1, -1], [0, 2, -2], [1, -1, 0]],
                    "bet_proposition": "R>P",
                    "joiners": ["team_me", "team_opponent"],
                    "bets": [
                        {"team_id": "team_me", "agree": True, "payout": 10},
                        {"team_id": "team_opponent", "agree": False, "payout": -10},
                    ],
                    "matches": [
                        {
                            "match_id": "r1__team_me__team_opponent",
                            "team_a": "team_me",
                            "team_b": "team_opponent",
                            "turns": [
                                {
                                    "turn_index": 1,
                                    "action_a": 0,
                                    "action_b": 1,
                                    "payoff_a": 1,
                                    "payoff_b": 0,
                                    "penalty_a": 0,
                                    "penalty_b": 0,
                                    "missed_a": False,
                                    "missed_b": False,
                                },
                                {
                                    "turn_index": 2,
                                    "action_a": 2,
                                    "action_b": 0,
                                    "payoff_a": -1,
                                    "payoff_b": 1,
                                    "penalty_a": 0,
                                    "penalty_b": 0,
                                    "missed_a": False,
                                    "missed_b": False,
                                },
                            ],
                        }
                    ],
                },
            ]
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "logs.json"
            path.write_text(json.dumps(payload), encoding="utf-8")

            result = run_backtest(path, "team_me")

            self.assertEqual(result.rounds_evaluated, 1)
            self.assertEqual(result.turns_evaluated, 2)
            self.assertGreaterEqual(result.action_match_rate, 0.0)
            self.assertIsInstance(result.simulated_bet_net, float)
            self.assertGreaterEqual(result.simulated_bet_attempts, 0)

    def test_run_backtest_counts_skipped_rounds_when_strategy_abstains(self) -> None:
        payload = {
            "rounds": [
                {
                    "round_index": 7,
                    "complete": True,
                    "payoff_matrix": [[-3, -3, -3], [-2, -2, -2], [-1, -1, -1]],
                    "bet_proposition": "R>=*",
                    "joiners": ["team_me", "team_opp"],
                    "matches": [
                        {
                            "match_id": "r7__team_me__team_opp",
                            "team_a": "team_me",
                            "team_b": "team_opp",
                            "turns": [
                                {
                                    "turn_index": 1,
                                    "action_a": 0,
                                    "action_b": 1,
                                    "payoff_a": -3,
                                    "payoff_b": -3,
                                    "penalty_a": 0,
                                    "penalty_b": 0,
                                    "missed_a": False,
                                    "missed_b": False,
                                }
                            ],
                        }
                    ],
                    "bets": [
                        {"team_id": "team_me", "agree": True},
                        {"team_id": "team_opp", "agree": True},
                    ],
                }
            ]
        }

        class AbstainStrategy(BasicStrategy):
            def should_join(self, state):  # type: ignore[override]
                return False

            def choose_actions(self, state):  # type: ignore[override]
                return {"team_opp": 0}

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "logs.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = run_backtest(path, "team_me", strategy=AbstainStrategy())

        self.assertEqual(result.rounds_evaluated, 1)
        self.assertEqual(result.rounds_skipped, 1)
        self.assertEqual(result.turns_evaluated, 0)
        self.assertEqual(result.simulated_bet_attempts, 0)


if __name__ == "__main__":
    unittest.main()
