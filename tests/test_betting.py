import unittest

from c3_harness.betting import evaluate_proposition, normalize_counts


class BettingTests(unittest.TestCase):
    def test_modal_proposition_allows_ties(self):
        self.assertTrue(evaluate_proposition("R>=*", {"R": 4, "P": 4, "S": 1}))
        self.assertFalse(evaluate_proposition("S>=*", {"R": 4, "P": 4, "S": 1}))

    def test_pairwise_propositions(self):
        counts = {"R": 3, "P": 3, "S": 2}
        self.assertFalse(evaluate_proposition("R>P", counts))
        self.assertTrue(evaluate_proposition("R>=P", counts))
        self.assertTrue(evaluate_proposition("P>S", counts))

    def test_integer_count_keys_are_supported(self):
        self.assertEqual(normalize_counts({0: 2, 1: 1, 2: 0}), {"R": 2, "P": 1, "S": 0})


if __name__ == "__main__":
    unittest.main()
