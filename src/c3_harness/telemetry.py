from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

JsonObject = dict[str, Any]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _safe_int(value: Any, default: int | None = None) -> int | None:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_state(state: JsonObject) -> JsonObject:
    keys = (
        "phase",
        "round_index",
        "turn_index",
        "next_turn_final",
        "payoff_matrix",
        "bet_proposition",
        "turn_deadline_utc",
        "round_deadline_utc",
        "matchups",
        "leaderboard",
        "team_id",
        "team_name",
    )
    normalized: JsonObject = {}
    for key in keys:
        if key in state:
            normalized[key] = state[key]
    return normalized


def _compact_payload(payload: JsonObject | None) -> JsonObject | None:
    if payload is None:
        return None
    compact = dict(payload)
    actions = compact.get("actions")
    if isinstance(actions, dict):
        compact["actions_count"] = len(actions)
        compact["action_targets"] = sorted(actions.keys())
    return compact


@dataclass
class MarketEvent:
    kind: str
    run_id: str
    round_index: int | None = None
    turn_index: int | None = None
    phase: str | None = None
    state: JsonObject | None = None
    payload: JsonObject | None = None
    response: JsonObject | None = None
    metadata: JsonObject | None = None

    def to_dict(self) -> JsonObject:
        return {
            "ts": _now_utc(),
            "kind": self.kind,
            "run_id": self.run_id,
            "round_index": self.round_index,
            "turn_index": self.turn_index,
            "phase": self.phase,
            "state": self.state,
            "payload": self.payload,
            "response": self.response,
            "metadata": self.metadata or {},
        }


class MarketLogger:
    """Append-only logger for live-state and decision artifacts."""

    def __init__(
        self,
        enabled: bool = False,
        log_root: str = "stage2_logs",
        run_id: str | None = None,
        run_name: str | None = None,
    ) -> None:
        self.enabled = enabled
        self.log_root = Path(log_root)
        self.run_id = run_id or _now_utc().replace(":", "-").replace("+00:00", "Z")
        self.run_name = run_name
        self.events_path = self.log_root / self.run_id / f"{self.run_name or 'stage2'}_events.ndjson"
        if self.enabled:
            self.events_path.parent.mkdir(parents=True, exist_ok=True)
            self._append_raw_line(
                self.events_path,
                MarketEvent(
                    kind="run_boot",
                    run_id=self.run_id,
                    metadata=self._run_boot_payload(),
                ).to_dict(),
            )

    def _run_boot_payload(self) -> JsonObject:
        return {
            "ts": _now_utc(),
            "run_id": self.run_id,
            "run_name": self.run_name,
            "schema_version": 1,
            "source": "c3_harness",
        }

    def _append_raw_line(self, path: Path, payload: JsonObject) -> None:
        if not self.enabled:
            return
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True))
            handle.write("\n")

    def log_state(self, state: JsonObject) -> None:
        if not self.enabled:
            return
        normalized = _normalize_state(state)
        event = MarketEvent(
            kind="state_poll",
            run_id=self.run_id,
            round_index=_safe_int(state.get("round_index")),
            turn_index=_safe_int(state.get("turn_index")),
            phase=str(state.get("phase")),
            state=normalized,
            payload={"full_state": state},
        )
        self._append_raw_line(self.events_path, event.to_dict())

    def log_decision(
        self,
        phase: str,
        payload: JsonObject | None,
        response: JsonObject | None,
        state: JsonObject | None = None,
    ) -> None:
        if not self.enabled:
            return
        normalized_state = _normalize_state(state or {})
        compact_payload = _compact_payload(payload or {})
        event = MarketEvent(
            kind="decision",
            run_id=self.run_id,
            round_index=_safe_int((state or {}).get("round_index")),
            turn_index=_safe_int((state or {}).get("turn_index")),
            phase=phase,
            state=normalized_state,
            payload=compact_payload,
            response=response,
        )
        self._append_raw_line(self.events_path, event.to_dict())

    def log_public_logs(self, logs: JsonObject | list[JsonObject]) -> None:
        if not self.enabled:
            return
        event = MarketEvent(
            kind="public_logs",
            run_id=self.run_id,
            metadata={"source": "public_logs_endpoint"},
            payload={"logs": logs},
        )
        self._append_raw_line(self.events_path, event.to_dict())

    def log_leaderboard(self, leaderboard: JsonObject) -> None:
        if not self.enabled:
            return
        event = MarketEvent(
            kind="leaderboard",
            run_id=self.run_id,
            metadata={"source": "leaderboard_endpoint"},
            payload={"leaderboard": leaderboard},
        )
        self._append_raw_line(self.events_path, event.to_dict())

    def log_api_telemetry(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        rtt_ms: float | None = None,
    ) -> None:
        if not self.enabled:
            return
        event = MarketEvent(
            kind="api_telemetry",
            run_id=self.run_id,
            metadata={
                "endpoint": endpoint,
                "method": method.upper(),
                "status_code": status_code,
                "rtt_ms": rtt_ms,
            },
        )
        self._append_raw_line(self.events_path, event.to_dict())
