import unittest

from c3_harness.strategy import BasicStrategy, opponent_ids


class StrategyTests(unittest.TestCase):
    def test_action_payload_includes_every_opponent(self):
        state = {
            "phase": "action",
            "round_index": 1,
            "turn_index": 1,
            "payoff_matrix": [
                [1, 1, 1],
                [3, 0, 0],
                [0, 0, 0],
            ],
            "matchups": [
                {"opponent_id": "team_a"},
                {"opponent_id": "team_b"},
            ],
        }

        actions = BasicStrategy().choose_actions(state)

        self.assertEqual(set(actions), {"team_a", "team_b"})
        self.assertTrue(all(action in {0, 1, 2} for action in actions.values()))

    def test_hidden_cells_are_treated_as_zero(self):
        strategy = BasicStrategy()
        matrix = [
            [None, None, None],
            [1, 1, 1],
            [-1, -1, -1],
        ]

        best_action, margin = strategy.best_average_action(matrix)

        self.assertEqual(best_action, 1)
        self.assertGreater(margin, 0)

    def test_bet_abstains_when_matrix_is_not_clear(self):
        state = {
            "phase": "opt_in",
            "bet_proposition": "R>=*",
            "payoff_matrix": [
                [1, 0, 0],
                [0, 1, 0],
                [0, 0, 1],
            ],
        }

        self.assertIsNone(BasicStrategy().choose_bet(state))

    def test_bet_uses_forecast_counts_when_matchups_are_known(self):
        state = {
            "phase": "opt_in",
            "bet_proposition": "R>=*",
            "payoff_matrix": [
                [3, 3, 3],
                [0, 0, 0],
                [-1, -1, -1],
            ],
            "matchups": [
                {"opponent_id": "team_bot_ev_heuristic"},
                {"opponent_id": "team_other"},
            ],
        }

        self.assertTrue(BasicStrategy().choose_bet(state))

    def test_bet_abstains_when_forecast_counts_are_close(self):
        state = {
            "phase": "opt_in",
            "bet_proposition": "R>P",
            "payoff_matrix": [
                [3, 0, 3],
                [0, 3, 0],
                [-1, -1, -1],
            ],
            "matchups": [
                {"opponent_id": "team_bot_ev_heuristic"},
                {
                    "opponent_id": "team_other",
                    "history": [
                        {"opponent_action": 1},
                        {"opponent_action": 1},
                        {"opponent_action": 1},
                    ],
                },
            ],
        }

        self.assertIsNone(BasicStrategy().choose_bet(state))

    def test_join_skips_catastrophically_negative_rounds(self):
        state = {
            "phase": "opt_in",
            "pot": 5,
            "payoff_matrix": [
                [-3, -3, -3],
                [-2, -2, -2],
                [-1, -1, -1],
            ],
            "matchups": [
                {"opponent_id": "team_a"},
                {"opponent_id": "team_b"},
            ],
        }

        self.assertFalse(BasicStrategy().should_join(state))

    def test_join_accepts_positive_expected_rounds(self):
        state = {
            "phase": "opt_in",
            "pot": 5,
            "payoff_matrix": [
                [1, 1, 1],
                [0, 0, 0],
                [-1, -1, -1],
            ],
            "matchups": [{"opponent_id": "team_a"}],
        }

        self.assertTrue(BasicStrategy().should_join(state))

    def test_opponent_ids_ignores_dashboard_style_matchups(self):
        state = {
            "matchups": [
                {"match_id": "r1__a__b", "team_a": "a", "team_b": "b"},
                {"opponent_id": "team_c"},
            ]
        }

        self.assertEqual(opponent_ids(state), ["team_c"])

    def test_broadcast_is_noisy_and_short(self):
        state = {
            "round_index": 3,
            "payoff_matrix": [
                [3, 3, 3],
                [0, 0, 0],
                [-1, -1, -1],
            ],
        }

        message = BasicStrategy().choose_broadcast(state)

        self.assertLessEqual(len(message), 280)
        self.assertNotIn("prioritizing action R", message)

    def test_bot_br_last_can_be_steered_before_final_turn(self):
        state = {
            "next_turn_final": False,
            "payoff_matrix": [
                [0, 0, 5],
                [0, 4, 0],
                [0, 0, 1],
            ],
            "matchups": [
                {
                    "opponent_id": "team_bot_br_last",
                    "history": [{"my_action": 0, "opponent_action": 0}],
                }
            ],
        }

        actions = BasicStrategy().choose_actions(state)

        self.assertEqual(actions["team_bot_br_last"], 1)

    def test_bot_br_last_uses_current_payoff_on_final_turn(self):
        state = {
            "next_turn_final": True,
            "payoff_matrix": [
                [0, 0, 5],
                [0, 4, 0],
                [0, 0, 1],
            ],
            "matchups": [
                {
                    "opponent_id": "team_bot_br_last",
                    "history": [{"my_action": 0, "opponent_action": 0}],
                }
            ],
        }

        actions = BasicStrategy().choose_actions(state)

        self.assertEqual(actions["team_bot_br_last"], 0)

    def test_ev_heuristic_bot_is_treated_as_row_average_player(self):
        state = {
            "payoff_matrix": [
                [0, 0, 0],
                [0, 0, 3],
                [3, 3, -1],
            ],
            "matchups": [{"opponent_id": "team_bot_ev_heuristic"}],
        }

        actions = BasicStrategy().choose_actions(state)

        self.assertEqual(actions["team_bot_ev_heuristic"], 1)


if __name__ == "__main__":
    unittest.main()
