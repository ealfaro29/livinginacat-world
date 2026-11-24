"""Per-walk outcome log — ``playbooks/runs.jsonl``, the escalation KPI's data.

One machine-written line per walk, appended at its FIRST terminal
moment (`record.py`; wakes and rehearsals alike)::

    {"ts", "session", "app", "playbook", "outcome", "node", "idx",
     "nodes", "reason", "micros", "rescues", ["values", "total"]}

``outcome`` is an `Outcome`; ``rescues`` counts recovery actions;
``node``/``idx`` locate where the walk ended (``node`` null past the
last node); ``values`` and ``total`` ride a completed line. Telemetry
only — read by `playbooks stats` and `propose`, never into a prompt
(the human-readable record is the daily log). Never fatal: a write
failure logs, an unparseable line is skipped. Append-only, no cap.
"""

import json
import logging
from enum import StrEnum
from pathlib import Path

from physiclaw.common import paths
from physiclaw.common.logger import iso_now
from physiclaw.common.text import append_text, clip
from physiclaw.conductor.spec.limits import REASON_CLIP

log = logging.getLogger(__name__)

RUNS_FILENAME = "runs.jsonl"


# The valid outcome spellings — `record` refuses anything else loudly (a
# typo'd outcome at a call site must fail tests, never skew the KPI).
# "abandoned" = the SESSION ended around a mid-flight walk (Ctrl-C,
# wall-clock budget) — recorded from plugin teardown (`Program.abandon`,
# `log_external_stop`'s twin), and deliberately NOT an escalation: the
# next wake starts the route over, no model session was spent.
class Outcome(StrEnum):
    """How a walk ended — the one vocabulary the walk records, the KPI
    counts, and a replay or a stepping driver reports."""

    COMPLETED = "completed"
    SUSPENDED = "suspended"
    HANDOVER = "handover"
    CRASHED = "crashed"
    ABANDONED = "abandoned"


# The KPI's numerator, one home: suspensions are the walk working as
# designed and abandonments spent no model session — neither escalates.
ESCALATION_OUTCOMES = frozenset({Outcome.HANDOVER, Outcome.CRASHED})


def runs_file() -> Path:
    return paths.playbooks_dir() / RUNS_FILENAME


def record(
    *,
    app: str,
    playbook: str,
    outcome: Outcome,
    idx: int,
    nodes: int,
    node: str | None,
    reason: str = "",
    micros: int = 0,
    rescues: int = 0,
    values: dict | None = None,
    total: float | None = None,
) -> None:
    """Append one walk's terminal line. Best-effort: a write failure logs
    and moves on — telemetry must never take down a session. `outcome`
    is coerced through `Outcome`, so a typo'd spelling at a call site
    raises rather than skewing the KPI."""
    try:
        outcome = Outcome(outcome)
    except ValueError:
        raise ValueError(f"unknown walk outcome {outcome!r}") from None
    line = {
        "ts": iso_now(),
        "session": paths.live_session_id(),
        "app": app,
        "playbook": playbook,
        "outcome": outcome,
        "node": node,
        "idx": idx,
        "nodes": nodes,
        "reason": _clip(reason),
        "micros": micros,
        "rescues": rescues,
        "values": {str(k): _clip(str(v)) for k, v in (values or {}).items()},
        "total": total,
    }
    try:
        paths.playbooks_dir().mkdir(parents=True, exist_ok=True)
        append_text(runs_file(), json.dumps(line, ensure_ascii=False) + "\n")
    except Exception:
        log.warning("walk run log write failed", exc_info=True)


def _clip(text: str) -> str:
    return clip(text, REASON_CLIP)
