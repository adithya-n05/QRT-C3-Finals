#!/usr/bin/env bash
set -euo pipefail

: "${C3_BASE_URL:=https://c3.qwerty.technology}"
: "${C3_GAME_KEY:?Set C3_GAME_KEY before starting capture}"
: "${C3_LOG_MARKET:=1}"
: "${C3_LOG_ROOT:=stage2_logs}"
: "${C3_LOG_RUN_NAME:=stage2_capture_$(date -u +%Y%m%dT%H%M%SZ)}"
: "${C3_POLL_INTERVAL_SECONDS:=0.35}"

export C3_BASE_URL
export C3_GAME_KEY
export C3_LOG_MARKET
export C3_LOG_ROOT
export C3_LOG_RUN_NAME
export C3_POLL_INTERVAL_SECONDS

mkdir -p "${C3_LOG_ROOT}"

PYTHONPATH=src python -m c3_harness.runner --live --log-market "$@"
