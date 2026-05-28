from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import HarnessConfig
from .telemetry import MarketLogger


JsonObject = dict[str, Any]


class C3HTTPError(RuntimeError):
    def __init__(self, status: int, body: str) -> None:
        super().__init__(f"C3 API returned HTTP {status}: {body}")
        self.status = status
        self.body = body


@dataclass
class C3Client:
    config: HarnessConfig
    timeout_seconds: float = 5.0
    logger: MarketLogger | None = None

    def request(
        self,
        method: str,
        path: str,
        *,
        body: JsonObject | None = None,
        auth: bool = True,
    ) -> JsonObject:
        started_ms = time.time()
        url = f"{self.config.base_url}{path}"
        data = None
        headers = {"Accept": "application/json"}

        if auth:
            headers.update(self.config.auth_headers())

        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = Request(url, data=data, headers=headers, method=method)

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
                status = getattr(response, "status", 200)
        except HTTPError as exc:
            raw_error = exc.read().decode("utf-8")
            status = exc.code
            if self.logger:
                self.logger.log_api_telemetry(path, method, status, (time.time() - started_ms) * 1000)
            raise C3HTTPError(exc.code, raw_error) from exc

        if self.logger:
            self.logger.log_api_telemetry(path, method, status, (time.time() - started_ms) * 1000)

        if not raw:
            return {}
        return json.loads(raw)

    def health(self) -> JsonObject:
        return self.request("GET", "/health", auth=False)

    def server_time(self) -> JsonObject:
        client_sent_ms = int(time.time() * 1000)
        query = urlencode({"client_sent_ms": client_sent_ms})
        return self.request("GET", f"/time?{query}", auth=False)

    def state(self) -> JsonObject:
        return self.request("GET", "/state")

    def leaderboard(self) -> JsonObject:
        return self.request("GET", "/leaderboard", auth=False)

    def logs(self, recent: int = 2) -> JsonObject:
        return self.request("GET", f"/logs?{urlencode({'recent': recent})}", auth=False)

    def participate(
        self,
        *,
        round_index: int,
        join: bool,
        agree: bool | None = None,
    ) -> JsonObject:
        body: JsonObject = {"round_index": round_index, "join": join}
        if agree is not None:
            body["agree"] = agree
        return self.request("POST", "/participate", body=body)

    def broadcast(self, *, round_index: int, message: str) -> JsonObject:
        return self.request(
            "POST",
            "/broadcast",
            body={"round_index": round_index, "message": message[:280]},
        )

    def action(
        self,
        *,
        round_index: int,
        turn_index: int,
        actions: dict[str, int],
    ) -> JsonObject:
        return self.request(
            "POST",
            "/action",
            body={
                "round_index": round_index,
                "turn_index": turn_index,
                "actions": actions,
            },
        )
