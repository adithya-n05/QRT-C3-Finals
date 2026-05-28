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

    def test_opponent_ids_ignores_dashboard_style_matchups(self):
        state = {
            "matchups": [
                {"match_id": "r1__a__b", "team_a": "a", "team_b": "b"},
                {"opponent_id": "team_c"},
            ]
        }

        self.assertEqual(opponent_ids(state), ["team_c"])


if __name__ == "__main__":
    unittest.main()
