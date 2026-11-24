"""Reading the parts of the agent's own memory a step declared
(`spec.memory` is the vocabulary). A slug that matches no heading loads
"" rather than vanishing: the author declared it, so the model reads an
empty slot instead of wondering whether it was told. The conductor may
never import the engine (architecture rule), so memory.md is read off
the shared path constant here.

Nothing here labels what it returns — `load` keys each body by the part
that asked for it, and the step's own `context:` block is where the
label is written.
"""

from collections.abc import Mapping
from typing import Any

from physiclaw.common import daylog, paths
from physiclaw.common.text import read_text
from physiclaw.conductor.spec.memory import ALL, LOG, PARTS


def load(spec: Mapping[str, Any]) -> dict[str, str]:
    """Each named part, read NOW and keyed by its own name — the label
    the model reads, which is why no body carries a heading of its own.
    memory.md is read and carved once however many sections are named,
    and not touched at all when none is."""
    slugs = [p for p in spec if p not in PARTS]
    text = _memory_text() if slugs or ALL in spec else ""
    sections = split_sections(text) if slugs else []
    out = {slug: match_sections(sections, slug) for slug in slugs}
    if ALL in spec:
        out[ALL] = text
    if LOG in spec:
        out[LOG] = daylog.load_recent_entries(spec[LOG])
    return out


def _memory_text() -> str:
    f = paths.memory_file()
    return read_text(f).strip() if f.exists() else ""


# One parsed section: (heading tokens, whole section text).
Sections = list[tuple[frozenset[str], str]]


def split_sections(text: str) -> Sections:
    """The file carved at its `## ` headings — parsed once, matched many
    times."""
    sections: Sections = []
    tokens: frozenset[str] | None = None
    body: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if tokens is not None:
                sections.append((tokens, "\n".join(body).strip()))
            tokens = frozenset(line[3:].casefold().split())
            body = [line]
        elif tokens is not None:
            body.append(line)
    if tokens is not None:
        sections.append((tokens, "\n".join(body).strip()))
    return sections


def match_sections(sections: Sections, slug: str) -> str:
    wanted = slug.casefold()
    return "\n".join(body for tokens, body in sections if wanted in tokens)
