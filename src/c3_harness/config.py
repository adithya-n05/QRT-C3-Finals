from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_BASE_URL = "https://c3.qwerty.technology"


@dataclass(frozen=True)
class HarnessConfig:
    base_url: str = DEFAULT_BASE_URL
    game_key: str | None = None
    poll_interval_seconds: float = 0.35
    safety_margin_ms: int = 100
    live: bool = False
    log_market: bool = False
    log_root: str = "stage2_logs"
    log_run_name: str | None = None
    public_logs_recent: int = 10

    @classmethod
    def from_env(cls, *, live: bool = False) -> "HarnessConfig":
        return cls(
            base_url=os.getenv("C3_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
            game_key=os.getenv("C3_GAME_KEY"),
            poll_interval_seconds=float(os.getenv("C3_POLL_INTERVAL_SECONDS", "0.35")),
            safety_margin_ms=int(os.getenv("C3_SAFETY_MARGIN_MS", "100")),
            live=live,
            log_market=os.getenv("C3_LOG_MARKET", "0") not in {"0", "false", "False", "FALSE"},
            log_root=os.getenv("C3_LOG_ROOT", "stage2_logs"),
            log_run_name=os.getenv("C3_LOG_RUN_NAME"),
            public_logs_recent=int(os.getenv("C3_PUBLIC_LOGS_RECENT", "10")),
        )

    def auth_headers(self) -> dict[str, str]:
        if not self.game_key:
            return {}
        return {"Authorization": f"Bearer {self.game_key}"}
