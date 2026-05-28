from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from c3_harness.telemetry import MarketLogger


class TelemetryTests(unittest.TestCase):
    def test_market_logger_collects_state_and_decision_events(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            logger = MarketLogger(enabled=True, log_root=root, run_id="test-run", run_name="round2")
            logger.log_state({"phase": "broadcast", "round_index": 1})
            logger.log_decision("broadcast", {"round_index": 1, "message": "x"}, {"accepted": True}, {"phase": "broadcast", "round_index": 1})

            events = Path(root) / "test-run" / "round2_events.ndjson"
            self.assertTrue(events.exists())

            raw_lines = events.read_text(encoding="utf-8").strip().splitlines()
            self.assertGreaterEqual(len(raw_lines), 3)
            parsed = [json.loads(line) for line in raw_lines]

            kinds = [entry["kind"] for entry in parsed]
            self.assertIn("run_boot", kinds)
            self.assertIn("state_poll", kinds)
            self.assertIn("decision", kinds)

            decision = next(entry for entry in parsed if entry["kind"] == "decision")
            self.assertEqual(decision["phase"], "broadcast")
            self.assertIn("payload", decision)
            self.assertIn("response", decision)


if __name__ == "__main__":
    unittest.main()
