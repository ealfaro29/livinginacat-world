"""The `tell` move — a message sent to the user, then the walk moves on."""

from physiclaw.conductor.route.fields import entry_message, on_fail_mode
from physiclaw.conductor.route.scope import Line, Scope
from physiclaw.conductor.spec.model import TellNode


def parse_tell(scope: Scope, line: Line) -> TellNode:
    """A `tell`: its `message:` is the exact text sent (refs filled at
    send time), from any screen — it speaks over the channel."""
    message, _ = entry_message(scope, line.where, line.entry, scope.payloads)
    return TellNode(
        id=line.name, message=message, on_fail=on_fail_mode(line.entry, line.where)
    )
