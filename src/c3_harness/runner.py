from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, field
from typing import Any

from .api import C3Client, C3HTTPError
from .config import HarnessConfig
from .telemetry import MarketLogger
from .strategy import BasicStrategy


JsonObject = dict[str, Any]


def normalize_phase(raw_phase: Any) -> str:
    if raw_phase is None:
        return ""
    normalized = str(raw_phase).strip().lower()
    if normalized.startswith("round_"):
        normalized = normalized.removeprefix("round_")
    return normalized


def should_retry_api_error(exc: C3HTTPError) -> bool:
    return exc.status in {429} or exc.status >= 500


def _classify_api_status(status: int) -> str:
    if status in {401, 403}:
        return "auth_failed"
    if status == 404:
        return "not_found"
    if status in {429, 500, 502, 503, 504}:
        return "server_or_throttle"
    if status >= 500:
        return "server_error"
    return "unexpected"


def connectivity_report(
    client: C3Client,
    *,
    include_auth_state: bool = True,
    include_health: bool = True,
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "base_url": client.config.base_url,
        "game_key_present": bool(client.config.game_key),
        "checks": [],
    }

    if include_health:
        try:
            health = client.health()
            report["checks"].append(
                {
                    "endpoint": "/health",
                    "ok": True,
                    "status": 200,
                    "body": health,
                }
            )
        except C3HTTPError as exc:
            report["checks"].append(
                {
                    "endpoint": "/health",
                    "ok": False,
                    "status": exc.status,
                    "category": _classify_api_status(exc.status),
                    "body": exc.body,
                }
            )

    if include_auth_state:
        try:
            state = client.state()
            report["checks"].append(
                {
                    "endpoint": "/state",
                    "ok": True,
                    "status": 200,
                    "phase": state.get("phase"),
                    "round_index": state.get("round_index"),
                    "team_id": state.get("team_id"),
                }
            )
        except C3HTTPError as exc:
            report["checks"].append(
                {
                    "endpoint": "/state",
                    "ok": False,
                    "status": exc.status,
                    "category": _classify_api_status(exc.status),
                    "body": exc.body,
                }
            )

    return report


@dataclass
class HarnessRunner:
    client: C3Client
    strategy: BasicStrategy
    live: bool = False
    logger: MarketLogger | None = None
    public_logs_recent: int = 10
    capture_leaderboard: bool = True
    submitted_keys: set[tuple[Any, ...]] = field(default_factory=set)

    def step(self) -> JsonObject:
        state = self.client.state()
        if self.logger:
            self.logger.log_state(state)
            self._capture_market_context()
        phase = normalize_phase(state.get("phase"))

        if phase == "opt_in":
            return self._handle_opt_in(state)
        if phase == "broadcast":
            return self._handle_broadcast(state)
        if phase == "action":
            return self._handle_action(state)

        return {"phase": phase, "operation": "none", "reason": "phase has no submission"}

    def _capture_market_context(self) -> None:
        if not self.logger:
            return
        try:
            logs = self.client.logs(recent=self.public_logs_recent)
        except C3HTTPError:
            return
        self.logger.log_public_logs(logs)

        if not self.capture_leaderboard:
            return

        try:
            leaderboard = self.client.leaderboard()
        except C3HTTPError:
            return
        self.logger.log_leaderboard(leaderboard)

    def _handle_opt_in(self, state: JsonObject) -> JsonObject:
        round_index = int(state["round_index"])
        key = ("participate", round_index)
        join = self.strategy.should_join(state)
        agree = self.strategy.choose_bet(state) if join else None
        payload: JsonObject = {"round_index": round_index, "join": join}
        if agree is not None:
            payload["agree"] = agree

        if key in self.submitted_keys:
            result = {"operation": "participate", "skipped": "already handled locally"}
            if self.logger:
                self.logger.log_decision("opt_in", payload=payload, response=result, state=state)
            return result

        if not self.live:
            self.submitted_keys.add(key)
            result = {"operation": "participate", "dry_run": True, "payload": payload}
            if self.logger:
                self.logger.log_decision("opt_in", payload=payload, response=result, state=state)
            return result

        response = self.client.participate(round_index=round_index, join=join, agree=agree)
        if response.get("accepted"):
            self.submitted_keys.add(key)
        result = {"operation": "participate", "response": response, "payload": payload}
        if self.logger:
            self.logger.log_decision("opt_in", payload=payload, response=response, state=state)
        return result

    def _handle_broadcast(self, state: JsonObject) -> JsonObject:
        round_index = int(state["round_index"])
        key = ("broadcast", round_index)

        if state.get("my_broadcast_submitted") or key in self.submitted_keys:
            result = {"operation": "broadcast", "skipped": "already submitted"}
            if self.logger:
                self.logger.log_decision("broadcast", payload={}, response=result, state=state)
            return result

        message = self.strategy.choose_broadcast(state)
        payload = {"round_index": round_index, "message": message}

        if not self.live:
            self.submitted_keys.add(key)
            result = {"operation": "broadcast", "dry_run": True, "payload": payload}
            if self.logger:
                self.logger.log_decision("broadcast", payload=payload, response=result, state=state)
            return result

        response = self.client.broadcast(round_index=round_index, message=message)
        if response.get("accepted"):
            self.submitted_keys.add(key)
        result = {"operation": "broadcast", "response": response, "payload": payload}
        if self.logger:
            self.logger.log_decision("broadcast", payload=payload, response=response, state=state)
        return result

    def _handle_action(self, state: JsonObject) -> JsonObject:
        round_index = int(state["round_index"])
        turn_index = int(state["turn_index"])
        key = ("action", round_index, turn_index)

        if state.get("my_action_submitted") or key in self.submitted_keys:
            result = {"operation": "action", "skipped": "already submitted"}
            if self.logger:
                self.logger.log_decision("action", payload={}, response=result, state=state)
            return result

        actions = self.strategy.choose_actions(state)
        payload = {
            "round_index": round_index,
            "turn_index": turn_index,
            "actions": actions,
        }

        if not self.live:
            self.submitted_keys.add(key)
            result = {"operation": "action", "dry_run": True, "payload": payload}
            if self.logger:
                self.logger.log_decision("action", payload=payload, response=result, state=state)
            return result

        response = self.client.action(
            round_index=round_index,
            turn_index=turn_index,
            actions=actions,
        )
        if response.get("accepted"):
            self.submitted_keys.add(key)
        result = {"operation": "action", "response": response, "payload": payload}
        if self.logger:
            self.logger.log_decision("action", payload=payload, response=response, state=state)
        return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the QRT.C3 agent harness.")
    parser.add_argument("--live", action="store_true", help="submit live POSTs")
    parser.add_argument("--check", action="store_true", help="run connectivity checks and exit")
    parser.add_argument("--once", action="store_true", help="run one poll/decision step")
    parser.add_argument("--max-loops", type=int, default=None, help="stop after N loops")
    parser.add_argument("--log-market", action="store_true", help="persist state and decision log")
    args = parser.parse_args(argv)

    config = HarnessConfig.from_env(live=args.live)
    if not config.game_key:
        print(
            "C3_GAME_KEY is not set; authenticated /state calls will fail. "
            "Set it before running the harness."
        )
        if args.check:
            # Keep running connectivity checks for public endpoints in read-only mode.
            config = HarnessConfig.from_env(live=False)
        else:
            return 2

    logger = MarketLogger(
        enabled=args.log_market or config.log_market,
        log_root=config.log_root,
        run_name=config.log_run_name,
    ) if (args.log_market or config.log_market) else None

    runner = HarnessRunner(
        client=C3Client(config, logger=logger),
        strategy=BasicStrategy(),
        live=config.live,
        logger=logger,
        public_logs_recent=config.public_logs_recent,
    )

    if args.check:
        report = connectivity_report(C3Client(config, logger=logger), include_auth_state=True, include_health=True)
        all_ok = all(item.get("ok") for item in report["checks"])
        print(json.dumps(report, sort_keys=True))
        return 0 if all_ok else 1

    loops = 0
    while True:
        try:
            result = runner.step()
        except C3HTTPError as exc:
            if should_retry_api_error(exc) and not args.once:
                print(
                    json.dumps(
                        {
                            "error": "transient_api_error",
                            "status": exc.status,
                            "detail": exc.body,
                            "action": "retry",
                        }
                    )
                )
                time.sleep(config.poll_interval_seconds * 2)
                continue
            print(json.dumps({"error": str(exc), "status": exc.status, "body": exc.body}))
            return 1

        print(json.dumps(result, sort_keys=True))
        loops += 1

        if args.once or (args.max_loops is not None and loops >= args.max_loops):
            return 0

        time.sleep(config.poll_interval_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
