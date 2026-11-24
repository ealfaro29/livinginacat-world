"""The `do` move — a recorded macro with its `with:` values, framed by
the pages around it — and the `start`, the same macro run cold."""

from physiclaw.conductor.route.fields import (
    check_with,
    irreversible_class,
    on_fail_mode,
    with_args,
)
from physiclaw.conductor.route.scope import Line, Scope
from physiclaw.conductor.spec.model import (
    DoNode,
    PlaybookError,
)


def parse_do(scope: Scope, line: Line) -> DoNode:
    """A `do` move: the `macro:` it runs (a pack macro by name, or an
    inline body), with `with:` as that macro's inputs. Its frame is the
    waypoints around it: it enters on the page before it and must land
    on the page after."""
    where, nid, entry = line.where, line.name, line.entry
    args = with_args(scope, line)
    if line.after is None:
        raise PlaybookError(
            f"{where}: a `do` must be followed by the page it lands "
            "on — the landing check is what proves the move ran"
        )
    assert line.before is not None  # `_shape`: no `do` above the first page
    before, after = line.before, line.after
    if "." in before or "." in after:
        raise PlaybookError(
            f"{where}: a `do` runs on this pack's own pages — a reserved "
            "built-in cannot frame it"
        )
    if "macro" not in entry:
        raise PlaybookError(
            f"{where}: a `do` names its `macro:` — a pack macro by name, or an "
            "inline body with `steps:`"
        )
    spec = scope.resolve(entry["macro"], where, nid)
    macro = spec.name
    check_with(where, args, spec.inputs, f"macro {macro!r}")
    return DoNode(
        id=nid,
        macro=macro,
        args=dict(args),
        enter=before,
        verify=after,
        irreversible=irreversible_class(entry, where),
        on_fail=on_fail_mode(entry, where),
    )


def parse_start(scope: Scope, line: Line) -> DoNode:
    """The `start`: the cold launch, a macro run from anywhere that must
    land on the first page — the one it sits right before (`_shape`)."""
    where = line.where
    assert line.after is not None  # `_shape`: a `start` sits before a page
    if "macro" not in line.entry:
        raise PlaybookError(
            f"{where}: a `start` names its `macro:` — the cold launch it runs"
        )
    spec = scope.resolve(line.entry["macro"], where, line.name)
    return DoNode(
        id=line.name,
        macro=spec.name,
        args={},
        enter="",  # unconditional: the start runs from anywhere
        verify=line.after,
        on_fail=on_fail_mode(line.entry, where),
    )
