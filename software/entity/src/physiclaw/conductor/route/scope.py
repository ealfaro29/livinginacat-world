"""What one route's compile threads through every move parser: the
`Scope` (the pack, the inputs, what the pass has compiled so far, the
macro and playbook resolvers), the `Line` each parser reads (the move
and the waypoints around it), and the resolver's shape.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from physiclaw.common.paths import (
    entry_of,
)
from physiclaw.conductor.spec.model import Node, Playbook
from physiclaw.conductor.spec.pack import Pack, Scanned
from physiclaw.macros.model import (
    Macro,
)


class SlotResolve(Protocol):
    """The name-or-inline resolution every macro-carrying slot shares
    (`resolve.route_resolver` builds the route's, `recover.manifest_recovers`
    the manifest's): `raw` is the slot's value (a name, or an inline
    body), `where` and `nid` frame the error and the synthesized name,
    `role` names the slot when it is not `macro:`. Distinct from
    `macros.parse.MacroResolver`, the name-only lookup it wraps."""

    def __call__(
        self, raw: Any, where: str, nid: str, role: str | None = None
    ) -> Macro: ...


@dataclass(frozen=True)
class Waypoint:
    """One `page:` line of the route, its id resolved (`compile._shape`)
    — the contract the moves around it are framed by, and where a page
    declares its recovery hand."""

    pos: int  # the route line, 1-based
    id: str
    entry: dict

    @property
    def where(self) -> str:
        return f"route line {self.pos}"


@dataclass(frozen=True)
class Line:
    """One move of the route, as its parser reads it: the kind and the
    name (the entry's leading key and its value), the entry's fields,
    and the waypoints around it — `before`, the page the walk stands on
    when the move opens (the nearest page above; None above the first),
    and `after`, the page written right after it (None when a move
    follows, or the route ends). What a move makes of them is its own
    rule: a `do` is framed by both, an `ask` reads only `before`."""

    pos: int  # the route line, 1-based
    kind: str
    name: str
    entry: dict
    before: str | None
    after: str | None

    @property
    def where(self) -> str:
        """How this move is named in a refusal."""
        return f"move {self.name!r}"


@dataclass
class Scope:
    """What every move parser reads: the pack, the inputs, the
    resolvers, and what the pass has done so far. `payloads` and
    `compiled` grow as the pass advances (an agent's return fields, the
    moves so far, in route order), so a `{move.field}` ref and a run's
    `each:`/`revise:` are defined-before-use by construction."""

    playbook: str
    pack: Pack
    input_names: set[str]
    resolve: SlotResolve
    # Seeded with the ONE slot every text may quote, `{ask.replies}`;
    # a payment ask's messages add `{ask.total}` (`payloads_with_total`).
    payloads: dict[str, tuple[str, ...]] = field(
        default_factory=lambda: {"ask": ("replies",)}
    )
    # The moves compiled so far, in route order.
    compiled: list[Node] = field(default_factory=list)
    # The sub-playbooks this route's `run` lines name, resolved before
    # the pass (their returns are quotable above the run), by move name.
    subs: dict[str, Playbook] = field(default_factory=dict)
    # The prompt files an agent step may name — this route's own
    # (`prompts.<name>`) and the pack's (`app.prompts.<name>`) — and
    # the files it did read, pack-relative (`buy/prompts/pick.md`).
    prompts_local: Scanned[str] = field(default_factory=Scanned)
    prompts_pack: Scanned[str] = field(default_factory=Scanned)
    prompts_used: set[str] = field(default_factory=set)
    # The playbooks this entry runs, parsed on demand for a `run` line
    # (by id, `<entry>.<name>`) — None where the caller has no pack of
    # playbooks to offer (a playbook parsed from bare text).
    resolve_playbook: Callable[[str], Playbook] | None = None

    @property
    def entry(self) -> str:
        """The folder this file sits in — the playbook itself for an
        entry, its entry for a playbook that entry runs. The leaf files
        beside this one are the entry's (`macros/`, `prompts/`)."""
        return entry_of(self.playbook)

    def payloads_with_total(self) -> dict[str, tuple[str, ...]]:
        """The refs a payment step may quote: every recorded return
        field plus the ONE gate slot, `{ask.total}` — the consented
        amount its ask binds (`lints.check_money` keeps the two adjacent)."""
        return {**self.payloads, "ask": ("replies", "total")}
