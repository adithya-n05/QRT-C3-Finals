from __future__ import annotations

from collections.abc import Mapping


ACTION_LABELS = ("R", "P", "S")
LABEL_TO_ACTION = {label: index for index, label in enumerate(ACTION_LABELS)}
ACTION_TO_LABEL = {index: label for label, index in LABEL_TO_ACTION.items()}


def normalize_counts(counts: Mapping[str | int, int]) -> dict[str, int]:
    normalized = {label: 0 for label in ACTION_LABELS}
    for key, value in counts.items():
        if isinstance(key, int):
            label = ACTION_TO_LABEL[key]
        else:
            label = key
        if label not in normalized:
            raise ValueError(f"Unknown action label: {key!r}")
        normalized[label] = int(value)
    return normalized


def evaluate_proposition(proposition: str, counts: Mapping[str | int, int]) -> bool:
    totals = normalize_counts(counts)
    proposition = proposition.strip().upper()

    if proposition.endswith(">=*"):
        label = proposition[0]
        _ensure_label(label)
        return totals[label] >= max(totals.values())

    if ">=" in proposition:
        left, right = proposition.split(">=", 1)
        _ensure_label(left)
        _ensure_label(right)
        return totals[left] >= totals[right]

    if ">" in proposition:
        left, right = proposition.split(">", 1)
        _ensure_label(left)
        _ensure_label(right)
        return totals[left] > totals[right]

    raise ValueError(f"Unsupported proposition: {proposition!r}")


def proposition_labels(proposition: str) -> tuple[str, str | None, str]:
    proposition = proposition.strip().upper()
    if proposition.endswith(">=*"):
        label = proposition[0]
        _ensure_label(label)
        return label, None, "modal"
    if ">=" in proposition:
        left, right = proposition.split(">=", 1)
        _ensure_label(left)
        _ensure_label(right)
        return left, right, "weak"
    if ">" in proposition:
        left, right = proposition.split(">", 1)
        _ensure_label(left)
        _ensure_label(right)
        return left, right, "strict"
    raise ValueError(f"Unsupported proposition: {proposition!r}")


def _ensure_label(label: str) -> None:
    if label not in LABEL_TO_ACTION:
        raise ValueError(f"Unknown action label: {label!r}")
