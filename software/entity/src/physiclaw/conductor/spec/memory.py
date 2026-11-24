"""What an agent step may read of the agent's OWN memory — the
`context.memory:` vocabulary, declared, never implied. A step names
the parts, one entry per part, and nothing else of that memory
travels to the model:

  - ``<slug>: true``    ONLY the `## <slug>` section of memory.md — a
                        slug matches a heading as a whole whitespace-
                        separated token (`shopping` never bleeds into
                        `## shopping_blacklist`; a heading may carry a
                        translation after its slug), and no match means
                        no text (fail closed)
  - ``all: true``       the whole memory.md
  - ``log: <n>``        the n most recent daily-log entries — the same
                        window the engine preloads into a wake

A part is included because a line says so: there is no default and no
switch, and an absent `memory:` sends nothing. This is the grammar
alone; the agent step reads the parts through `steps.memory`.
"""

from physiclaw.conductor.spec.limits import MAX_MEMORY_LOG
from physiclaw.conductor.spec.specfile import INPUT_NAME_RE

ALL = "all"  # the whole memory.md
LOG = "log"  # the recent daily-log window, `log: <n>`
# The parts the ENGINE names; any other key is a slug — one `## <slug>`
# section of memory.md. `memory_gap` branches on this tuple and
# `lints` reads its exemption off it (a part is the engine's own word, so a
# prompt has no reason to spell it), which is why a new part is one row.
PARTS = (ALL, LOG)


def memory_gap(spec: object) -> str | None:
    """None when `spec` is a legal `memory:` block, else the rule it
    breaks. The one legality reader: the parser calls it, and nothing
    re-derives the vocabulary."""
    if not isinstance(spec, dict):
        return "must be a mapping of `<part>: <how much>`"
    for part, value in spec.items():
        if not isinstance(part, str):
            return f"part {part!r} must be a name"
        if part == LOG:
            if isinstance(value, bool) or not isinstance(value, int):
                return f"`{LOG}: {value!r}` must be how many entries, a number"
            if not 1 <= value <= MAX_MEMORY_LOG:
                return f"`{LOG}: {value}` must be from 1 to {MAX_MEMORY_LOG}"
        elif value is not True:
            return (
                f"`{part}: {value!r}` must be `true` — a part is named to "
                "include it, and left out to leave it behind"
            )
        elif part not in PARTS and not INPUT_NAME_RE.match(part):
            return f"part {part!r} must be a `## <slug>` heading of memory.md"
    return None
