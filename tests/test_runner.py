import unittest

from c3_harness.runner import HarnessRunner, normalize_phase, should_retry_api_error
from c3_harness.strategy import BasicStrategy


class StubClient:
    def __init__(self, state):
        self._state = state
        self.calls = 0

    def state(self):
        self.calls += 1
        return self._state

    def participate(self, **kwargs):
        raise AssertionError("participate should not be called in dry-run")

    def broadcast(self, **kwargs):
        raise AssertionError("broadcast should not be called in dry-run")

    def action(self, **kwargs):
        raise AssertionError("action should not be called in dry-run")

    def logs(self, recent=3):
        return {"logs": []}


class StrategyFixture(BasicStrategy):
    def should_join(self, state):
        return True

    def choose_bet(self, state):
        return False

    def choose_broadcast(self, state):
        return "signal"

    def choose_actions(self, state):
        return {"team_opp": 1}


class RunnerTests(unittest.TestCase):
    def _run_once(self, phase: str):
        client = StubClient(
            {
                "phase": phase,
                "round_index": 7,
                "turn_index": 2,
                "matchups": [{"opponent_id": "team_opp"}],
            }
        )
        runner = HarnessRunner(
            client=client,
            strategy=StrategyFixture(),
            live=False,
        )
        return client, runner.step()

    def test_normalizes_round_phase_prefixes(self) -> None:
        client, result = self._run_once("ROUND_OPT_IN")
        self.assertEqual(result["operation"], "participate")
        self.assertTrue(result.get("dry_run"))
        self.assertIn("payload", result)
        self.assertEqual(client.calls, 1)

    def test_broadcast_handles_round_phase_prefix(self) -> None:
        client, result = self._run_once("ROUND_BROADCAST")
        self.assertEqual(result["operation"], "broadcast")
        self.assertTrue(result["dry_run"])

    def test_action_handles_round_phase_prefix(self) -> None:
        client, result = self._run_once("ROUND_ACTION")
        self.assertEqual(result["operation"], "action")
        self.assertTrue(result["dry_run"])
        self.assertIn("team_opp", result["payload"]["actions"])

    def test_unknown_phase_is_reported(self) -> None:
        _, result = self._run_once("ROUND_WAITING")
        self.assertEqual(result["operation"], "none")

    def test_normalize_phase_handles_lowercase_variants(self) -> None:
        self.assertEqual(normalize_phase("ROUND_BROADCAST"), "broadcast")
        self.assertEqual(normalize_phase("action"), "action")
        self.assertEqual(normalize_phase("Round_Complete"), "complete")

    def test_should_retry_api_error_for_5xx(self) -> None:
        from c3_harness.api import C3HTTPError

        self.assertTrue(should_retry_api_error(C3HTTPError(500, "server error")))
        self.assertTrue(should_retry_api_error(C3HTTPError(502, "bad gateway")))
        self.assertTrue(should_retry_api_error(C3HTTPError(504, "gateway timeout")))

    def test_should_retry_429_rate_limit_as_transient(self) -> None:
        from c3_harness.api import C3HTTPError

        self.assertFalse(should_retry_api_error(C3HTTPError(400, "bad request")))
        self.assertFalse(should_retry_api_error(C3HTTPError(401, "unauthorized")))
        self.assertTrue(should_retry_api_error(C3HTTPError(429, "rate limited")))


if __name__ == "__main__":
    unittest.main()
