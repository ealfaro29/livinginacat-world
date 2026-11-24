"""The live rule — what a real wake needs of a playbook: enabled, and
every macro it can dispatch enabled. `require_live` raises off it, the
wake roster prints `live_gap`, `playbooks check` warns off
`disabled_macros`; all three read one rule.
"""

from physiclaw.conductor.spec.model import (
    AgentNode,
    AskNode,
    DoNode,
    Playbook,
    PlaybookError,
)
from physiclaw.conductor.spec.pack import Pack
from physiclaw.macros.model import Macro


def require_live(spec: Playbook, pack: Pack) -> None:
    """The live rule, spelled once: what a real wake needs of a playbook
    — enabled, with every referenced pack macro enabled. A resuming
    suspension and the boot must satisfy it; a rehearsal deliberately
    need not (you rehearse BEFORE you enable). Raises PlaybookError
    naming the gap."""
    if not spec.offered:
        raise PlaybookError(
            f"{spec.app}/{spec.name}: walked by {spec.run_by}'s `run:`, "
            "never launched on its own"
        )
    gap = live_gap(spec, pack)
    if gap is not None:
        raise PlaybookError(f"{spec.app}/{spec.name}: {gap} — rehearse, then enable")


def live_gap(spec: Playbook, pack: Pack) -> str | None:
    """The one thing that keeps a valid playbook from a wake, in a word
    or two — None when it is live. `require_live` raises off it; the
    wake roster prints it; both read one rule."""
    if not spec.enabled:
        return "disabled"
    if not spec.offered:
        # Walked by its entry only — never launched alone, so the roster
        # owes this reason for it (`offered` is the rule itself).
        return f"run by {spec.run_by}"
    for r in spec.runs:
        if not r.sub.enabled:
            return f"runs disabled playbook {r.sub.name!r}"
    disabled = disabled_macros(spec, pack)
    if disabled:
        return (
            f"disabled macro{'s' if len(disabled) > 1 else ''}: {', '.join(disabled)}"
        )
    return None


def disabled_macros(spec: Playbook, pack: Pack) -> list[str]:
    """Referenced pack macros still disabled — the live-readiness rule:
    `playbooks check` warns about it and the boot will not offer such
    a playbook at all. Covers every dispatching role: do moves, an ask's
    `resume:`, a page's `recover:` hands, and an agent's granted macros.
    Safe unguarded access: parse
    validated every directory name against `pack.macros`."""
    named: set[str] = set()
    inline: dict[str, Macro] = {}
    for pb in spec.with_subs:
        inline.update(pb.inline_macros)
        for recovery in pb.recovers.values():
            named.update(h.macro for h in recovery.hands if h.macro is not None)
        for n in pb.nodes:
            if isinstance(n, DoNode):
                named.add(n.macro)
            elif isinstance(n, AskNode) and n.resume is not None:
                named.add(n.resume)
            elif isinstance(n, AgentNode):
                named.update(n.macros)
    # One rule, no special case: each name resolves through the merged
    # view. An inline body is enabled by construction (its gate is the
    # playbook's own `enabled:`); a pack macro or a playbook's recorded
    # file carries its own flag, and both are read here — as `live`, so
    # a hand that runs a disabled macro counts as disabled itself.
    return sorted(m for m in named if not (inline.get(m) or pack.macros[m]).live)
