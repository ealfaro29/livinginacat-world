"""The suspension file — the one thing a walk leaves behind.

``playbooks/suspended.json`` holds a walk that asked the user something
and stepped out of the way rather than burning a session waiting: an
ask ran out of patience polling for a reply. It carries the walk's
whole position — cursor, agent outputs, the gate's consent numbers —
so the next wake picks up mid-purchase instead of starting over.

One-shot: consumed on load, whatever the outcome. A crash mid-resume
loses the suspension and the wake runs plain, never a loop.

This is the ONLY cross-wake state the conductor writes: a playbook on
disk is the grant, so nothing else needs pre-declaring.
"""

import json
from pathlib import Path

from physiclaw.common import paths
from physiclaw.common.logger import write_json_atomic
from physiclaw.common.text import read_text

SUSPENDED_FILENAME = "suspended.json"
SUSPENDED_SCHEMA = 1


def suspended_path() -> Path:
    return paths.playbooks_dir() / SUSPENDED_FILENAME


def clear_suspended() -> bool:
    p = suspended_path()
    if not p.exists():
        return False
    p.unlink()
    return True


def read_position(path: Path) -> dict | None:
    """One stored walk position (`Program.state`'s shape) off `path` —
    the suspension file, or a stepping tool's checkpoint, which share the
    shape and the schema. None when missing, unreadable, or written by a
    build with another schema."""
    try:
        data = json.loads(read_text(path))
    except Exception:
        return None
    if not isinstance(data, dict) or data.get("schema") != SUSPENDED_SCHEMA:
        return None
    return data


def suspended_ref() -> tuple[str, str] | None:
    """The suspended walk's ``(app, playbook)`` per the file, without
    validating anything else. None when nothing is suspended /
    unreadable."""
    try:
        data = json.loads(read_text(suspended_path()))
        return str(data["app"]), str(data["playbook"])
    except Exception:
        return None


def write_suspended(state: dict) -> None:
    """The one write of the suspension file — the walk's projection."""
    write_json_atomic(suspended_path(), state)


def read_suspended() -> dict:
    """The suspension file, schema-checked — raises when it is missing,
    unreadable, or of a schema this build does not know."""
    data = read_position(suspended_path())
    if data is None:
        raise ValueError("no suspension this build can read")
    return data
