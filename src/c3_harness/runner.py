from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, field
from typing import Any

from .api import C3Client, C3HTTPError
from .config import HarnessConfig
from .strategy import BasicStrategy


JsonObject = dict[str, Any]


@dataclass
class HarnessRunner:
    client: C3Client
    strategy: BasicStrategy
    live: bool = False
    submitted_keys: set[tuple[Any, ...]] = field(default_factory=set)

    def step(self) -> JsonObject:
        state = self.client.state()
        phase = state.get("phase")

        if phase == "opt_in":
            return self._handle_opt_in(state)
        if phase == "broadcast":
            return self._handle_broadcast(state)
        if phase == "action":
            return self._handle_action(state)

        return {"phase": phase, "operation": "none", "reason": "phase has no submission"}

    def _handle_opt_in(self, state: JsonObject) -> JsonObject:
        round_index = int(state["round_index"])
        key = ("participate", round_index)
        join = self.strategy.should_join(state)
        agree = self.strategy.choose_bet(state) if join else None
        payload: JsonObject = {"round_index": round_index, "join": join}
        if agree is not None:
            payload["agree"] = agree

        if key in self.submitted_keys:
            return {"operation": "participate", "skipped": "already handled locally"}

        if not self.live:
            self.submitted_keys.add(key)
            return {"operation": "participate", "dry_run": True, "payload": payload}

        response = self.client.participate(round_index=round_index, join=join, agree=agree)
        if response.get("accepted"):
            self.submitted_keys.add(key)
        return {"operation": "participate", "response": response, "payload": payload}

    def _handle_broadcast(self, state: JsonObject) -> JsonObject:
        round_index = int(state["round_index"])
        key = ("broadcast", round_index)

        if state.get("my_broadcast_submitted") or key in self.submitted_keys:
            return {"operation": "broadcast", "skipped": "already submitted"}

        message = self.strategy.choose_broadcast(state)
        payload = {"round_index": round_index, "message": message}

        if not self.live:
            self.submitted_keys.add(key)
            return {"operation": "broadcast", "dry_run": True, "payload": payload}

        response = self.client.broadcast(round_index=round_index, message=message)
        if response.get("accepted"):
            self.submitted_keys.add(key)
        return {"operation": "broadcast", "response": response, "payload": payload}

    def _handle_action(self, state: JsonObject) -> JsonObject:
        round_index = int(state["round_index"])
        turn_index = int(state["turn_index"])
        key = ("action", round_index, turn_index)

        if state.get("my_action_submitted") or key in self.submitted_keys:
            return {"operation": "action", "skipped": "already submitted"}

        actions = self.strategy.choose_actions(state)
        payload = {
            "round_index": round_index,
            "turn_index": turn_index,
            "actions": actions,
        }

        if not self.live:
            self.submitted_keys.add(key)
            return {"operation": "action", "dry_run": True, "payload": payload}

        response = self.client.action(
            round_index=round_index,
            turn_index=turn_index,
            actions=actions,
        )
        if response.get("accepted"):
            self.submitted_keys.add(key)
        return {"operation": "action", "response": response, "payload": payload}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the QRT.C3 agent harness.")
    parser.add_argument("--live", action="store_true", help="submit live POSTs")
    parser.add_argument("--once", action="store_true", help="run one poll/decision step")
    parser.add_argument("--max-loops", type=int, default=None, help="stop after N loops")
    args = parser.parse_args(argv)

    config = HarnessConfig.from_env(live=args.live)
    if not config.game_key:
        print(
            "C3_GAME_KEY is not set; authenticated /state calls will fail. "
            "Set it before running the harness."
        )
        return 2

    runner = HarnessRunner(
        client=C3Client(config),
        strategy=BasicStrategy(),
        live=config.live,
    )

    loops = 0
    while True:
        try:
            result = runner.step()
        except C3HTTPError as exc:
            print(json.dumps({"error": str(exc), "status": exc.status, "body": exc.body}))
            return 1

        print(json.dumps(result, sort_keys=True))
        loops += 1

        if args.once or (args.max_loops is not None and loops >= args.max_loops):
            return 0

        time.sleep(config.poll_interval_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
