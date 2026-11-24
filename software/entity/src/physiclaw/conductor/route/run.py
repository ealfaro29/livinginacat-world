"""The `run` move — a playbook of this entry walked as one move, once or
once per item (`each:`), with its `revise:` and its rounds budget.
"""

from physiclaw.common.paths import (
    playbook_file,
    run_by,
)
from physiclaw.conductor.route.fields import (
    check_with,
    closed_word,
    limit_int,
    limit_mapping,
    on_fail_mode,
    with_args,
)
from physiclaw.conductor.route.scope import Line, Scope
from physiclaw.conductor.spec.limits import (
    DEFAULT_REVISIONS,
    DEFAULT_RUN_ROUNDS,
    MAX_REVISIONS,
    MAX_RUN_ROUNDS,
)
from physiclaw.conductor.spec.model import (
    MISS_MODES,
    AgentNode,
    AskNode,
    Playbook,
    PlaybookError,
    RunNode,
    TellNode,
    check_name,
    require_str,
)
from physiclaw.conductor.spec.refs import (
    check_refs,
)

_RUN_LIMIT_KEYS = {"rounds", "revisions"}


def sub_playbook(scope: Scope, where: str, name: str) -> Playbook:
    """The playbook a `run` names — `<name>.yml` beside this entry's
    PLAYBOOK.yml, parsed against the same pack by the resolver the pack
    loader wired (a playbook parsed from bare text has none to offer).
    Only an ENTRY runs: what it runs is a file, with no folder for
    playbooks of its own, so a run goes one level deep by shape."""
    if scope.resolve_playbook is None:
        raise PlaybookError(f"{where}: `run` names a playbook, but none are loaded")
    if run_by(scope.playbook) is not None:
        raise PlaybookError(
            f"{where}: only an entry runs a playbook — this file is one that "
            f"{playbook_file(scope.entry)} runs"
        )
    check_name(name, f"{where}: `run`")
    return scope.resolve_playbook(f"{scope.playbook}.{name}")


def parse_run(scope: Scope, line: Line) -> RunNode:
    """A `run` move: a playbook beside this entry walked as one move.
    Its frame is derived like a `do`'s — it starts where that playbook
    starts (cold, or on the page before it) and lands on its last page,
    which the route must name next."""
    where, nid, entry = line.where, line.name, line.entry
    before, after = line.before, line.after
    sub = scope.subs[nid]
    args = with_args(scope, line)
    if not sub.end:
        raise PlaybookError(
            f"{where}: playbook {sub.name!r} ends on a move — a playbook run "
            "as a move must end on a page, the landing the run checks"
        )
    if not sub.self_starting:
        if before is None:
            raise PlaybookError(
                f"{where}: playbook {sub.name!r} starts on page {sub.start!r} — "
                "put that page before the run, or give the playbook its own "
                "`start`"
            )
        if before != sub.start:
            raise PlaybookError(
                f"{where}: the page before it is {before!r}, but playbook "
                f"{sub.name!r} starts on {sub.start!r}"
            )
    if after is None:
        raise PlaybookError(
            f"{where}: a `run` must be followed by the page it lands on — "
            f"playbook {sub.name!r} ends on {sub.end!r}"
        )
    if after != sub.end:
        raise PlaybookError(
            f"{where}: playbook {sub.name!r} lands on {sub.end!r}, but the "
            f"route continues with page {after!r}"
        )
    declared = {inp.name for inp in sub.inputs}
    agents = {n.id for n in scope.compiled if isinstance(n, AgentNode)}
    each: tuple[str, str] | None = None
    raw_each = entry.get("each")
    if raw_each is not None:
        if not (isinstance(raw_each, dict) and len(raw_each) == 1):
            raise PlaybookError(
                f"{where}: `each` is one mapping, `{{<input>: <move>.<field>}}` — "
                "the input each round fills, from a list an earlier agent returned"
            )
        ((inp, ref),) = raw_each.items()
        inp, ref = str(inp), require_str(ref, f"{where}: `each` value")
        if inp not in declared:
            raise PlaybookError(
                f"{where}: `each` fills {inp!r}, which is not an input of "
                f"playbook {sub.name!r}"
            )
        if inp in args:
            raise PlaybookError(f"{where}: {inp!r} is filled by both `with` and `each`")
        check_refs({ref}, scope.input_names, scope.payloads, f"{where}: `each`")
        if ref.split(".")[0] not in agents:
            raise PlaybookError(
                f"{where}: `each` iterates a list an EARLIER agent returned "
                f"({{{ref}}} is not one)"
            )
        each = (inp, ref)
        if not sub.self_starting and sub.end != sub.start:
            # Round two enters where round one LANDED. Without a `start`
            # of its own the sub has no way back, so every round after
            # the first fails its enter check — recorded "missed" with
            # nothing ever attempted.
            raise PlaybookError(
                f"{where}: `each` walks {sub.name!r} once per item, and each "
                f"round starts where the last one landed — but it ends on "
                f"{sub.end!r} and starts on {sub.start!r}. Give it a `start`."
            )
    check_with(
        where,
        args,
        sub.inputs,
        f"playbook {sub.name!r}",
        filled=frozenset({each[0]}) if each else frozenset(),
    )
    miss = closed_word(entry, "miss", MISS_MODES, where)
    if miss is not None:
        if each is None:
            raise PlaybookError(f"{where}: `miss: skip` goes with `each`")
        if any(
            isinstance(n, (AskNode, TellNode)) or getattr(n, "irreversible", None)
            for n in sub.nodes
        ):
            raise PlaybookError(
                f"{where}: `miss: skip` needs a playbook that never asks, tells or pays "
                f"— {sub.name!r} does; a skipped round must leave nothing owed"
            )
    revise = entry.get("revise")
    if revise is not None:
        revise = require_str(revise, f"{where}: `revise`")
        if revise not in agents:
            raise PlaybookError(
                f"{where}: `revise` names {revise!r}, which is not an EARLIER "
                "agent of this route — a revision re-runs the walk from there"
            )
        if not any(isinstance(n, AskNode) for n in sub.nodes):
            raise PlaybookError(
                f"{where}: `revise` needs an ask inside playbook {sub.name!r} "
                "— it is that ask's uncovered reply that revises"
            )
    raw_limit = limit_mapping(entry, where, _RUN_LIMIT_KEYS)
    if "rounds" in raw_limit and each is None:
        raise PlaybookError(f"{where}: `limit.rounds` goes with `each`")
    if "revisions" in raw_limit and revise is None:
        raise PlaybookError(f"{where}: `limit.revisions` goes with `revise`")
    max_rounds = limit_int(
        raw_limit.get("rounds", DEFAULT_RUN_ROUNDS),
        f"{where}: `limit.rounds`",
        1,
        MAX_RUN_ROUNDS,
    )
    revise_limit = limit_int(
        raw_limit.get("revisions", DEFAULT_REVISIONS),
        f"{where}: `limit.revisions`",
        1,
        MAX_REVISIONS,
    )
    return RunNode(
        id=nid,
        args=args,
        sub=sub,
        enter="" if sub.self_starting else (before or ""),
        verify=sub.end,
        each=each,
        miss=miss,
        revise=revise,
        revise_limit=revise_limit,
        max_rounds=max_rounds,
        on_fail=on_fail_mode(entry, where),
    )
