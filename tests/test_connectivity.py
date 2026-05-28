from __future__ import annotations

import unittest

from c3_harness.api import C3HTTPError
from c3_harness.config import HarnessConfig
from c3_harness.runner import _classify_api_status, connectivity_report


class _StubClient:
    def __init__(self, *, health=None, state=None):
        self._health = health
        self._state = state
        self.config = HarnessConfig()

    def health(self):
        if isinstance(self._health, BaseException):
            raise self._health
        return self._health

    def state(self):
        if isinstance(self._state, BaseException):
            raise self._state
        return self._state


class ConnectivityTests(unittest.TestCase):
    def test_classify_api_status(self) -> None:
        self.assertEqual(_classify_api_status(401), "auth_failed")
        self.assertEqual(_classify_api_status(403), "auth_failed")
        self.assertEqual(_classify_api_status(404), "not_found")
        self.assertEqual(_classify_api_status(429), "server_or_throttle")
        self.assertEqual(_classify_api_status(503), "server_or_throttle")
        self.assertEqual(_classify_api_status(502), "server_or_throttle")
        self.assertEqual(_classify_api_status(500), "server_or_throttle")

    def test_connectivity_reports_success_and_failure(self) -> None:
        client = _StubClient(
            health={"ok": True},
            state={
                "phase": "round_opt_in",
                "round_index": 7,
                "team_id": "team_x",
            },
        )
        report = connectivity_report(client)
        self.assertEqual(len(report["checks"]), 2)
        self.assertEqual(report["checks"][0]["ok"], True)
        self.assertEqual(report["checks"][1]["ok"], True)

    def test_connectivity_reports_http_errors_with_categories(self) -> None:
        client = _StubClient(
            health=C3HTTPError(502, "bad gateway"),
            state=C3HTTPError(401, "unauthorized"),
        )
        report = connectivity_report(client)
        self.assertEqual(report["checks"][0]["ok"], False)
        self.assertEqual(report["checks"][0]["category"], "server_or_throttle")
        self.assertEqual(report["checks"][1]["ok"], False)
        self.assertEqual(report["checks"][1]["category"], "auth_failed")


if __name__ == "__main__":
    unittest.main()
