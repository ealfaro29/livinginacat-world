"""A move as `(action, args)` — read off a reply (`reply_args`), off an
outcome (`move_of`), said in words for a log line (`describe_move`), and
keyed for a replay's agreement (`move_key`).
"""

import json
from typing import Any

from physiclaw.common.bbox import format_bbox
from physiclaw.conductor.micro.decision import (
    Macro,
    MicroOutcome,
    Tap,
)
from physiclaw.conductor.spec.calls import (
    ACT_BACK,
    AGENT_DONE,
    ARGS,
    AT,
    DIRECTION,
    LABEL,
    NAME,
    SCROLL_ARMS,
    TOOL_ARGS,
    TOOL_BACK,
    TOOL_RUN,
    TOOL_SCROLL,
    TOOL_TAP,
)


def reply_args(obj: dict) -> dict[str, Any]:
    """A parsed reply's `args`: the tool's arguments as sent, an empty
    dict when the tool takes none (or the reply left them out)."""
    args = obj.get(ARGS)
    return dict(args) if isinstance(args, dict) else {}


def describe_move(action: str, args: dict) -> str:
    """A tool call in words, for a log line or a replay row: the tool,
    then its args the way a person would read them (a tap by the label
    the model gave and the box it sent)."""
    if action == TOOL_TAP:
        at = args.get(AT)
        where = format_bbox(at) if isinstance(at, list) and len(at) == 4 else at
        return f"tap {args.get(LABEL)!r} at {where}"
    if action == TOOL_SCROLL:
        return f"scroll {args.get(DIRECTION)}"
    if action == TOOL_RUN:
        return f"run_macro {args.get(NAME)}"
    if action == AGENT_DONE and args:
        return f"done {json.dumps(args, ensure_ascii=False)}"
    return action


def move_key(action: str, args: dict) -> tuple:
    """What makes two replies the SAME move, for a replay's agreement:
    the tool and the args that locate it — every arg `TOOL_ARGS` lists
    but the label, which is the model's own wording (as are done's
    fields, which `TOOL_ARGS` does not list)."""
    locating = (k for k in TOOL_ARGS.get(action, ()) if k != LABEL)
    return (action, *(_hashable(args.get(k)) for k in locating))


def _hashable(value: Any) -> Any:
    return tuple(value) if isinstance(value, list) else value


def move_of(outcome: MicroOutcome) -> tuple[str, dict[str, Any]]:
    """An agent outcome as the tool call it was: (action, args) — the
    inverse of `_act_outcome`, so a replayed turn and a journal line
    spell the move the model made, not the walk's routing arm."""
    picked = outcome.picked
    if isinstance(picked, Macro):
        return TOOL_RUN, {NAME: picked.name}
    if isinstance(picked, Tap):
        return TOOL_TAP, {LABEL: picked.label, AT: [round(v, 3) for v in picked.bbox]}
    if outcome.out in _ARM_DIRECTION:
        return TOOL_SCROLL, {DIRECTION: _ARM_DIRECTION[outcome.out]}
    if outcome.out == ACT_BACK:
        return TOOL_BACK, {}
    if outcome.out == AGENT_DONE:
        return AGENT_DONE, dict(outcome.payload or {})
    return outcome.out, {}


_ARM_DIRECTION = {arm: direction for direction, arm in SCROLL_ARMS.items()}
