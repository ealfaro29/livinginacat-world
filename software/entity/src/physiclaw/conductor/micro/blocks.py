"""The blocks a user turn is built from — the screen listing as data
(`act_rows`, `act_block`), the data stamp every untrusted text enters
the prompt through (`data_block`), the return-field list, and the
`- name: body` shape a labelled line takes.
"""

import logging
from collections.abc import Iterable

from physiclaw.common.listing import Element, format_elements
from physiclaw.conductor.micro import prompts
from physiclaw.conductor.spec.limits import MAX_SCREEN_ROWS

log = logging.getLogger(__name__)


def act_rows(rows: Iterable[Element]) -> tuple[Element, ...]:
    """The elements one agent-episode turn presents — every detected
    element, icons included, in screen order (never shuffled: position
    is spatial information a step-by-step operator navigates by),
    capped. What the block shows and what a tap box is matched against
    are this ONE tuple, so they cannot disagree."""
    out = tuple(rows)
    if len(out) > MAX_SCREEN_ROWS:
        log.info("micro: %d elements capped to %d", len(out), MAX_SCREEN_ROWS)
        out = out[:MAX_SCREEN_ROWS]
    return out


def data_block(header: str, body: str) -> str:
    """Untrusted text enters the prompt ONLY through this stamp: OCR'd
    app content (and everything derived from it) can contain anything,
    including instruction-shaped strings — the label keeps the SYSTEM
    contract sovereign over whatever a shop listing happens to say. A
    mechanism, not a convention: new call types get the label by calling
    this, and a test pins its presence."""
    return f"{header} {prompts.DATA_STAMP}:\n{body}"


def act_block(header: str, rows: Iterable[Element]) -> str:
    """One episode turn's listing block — the whole element listing in
    the shared grammar (header, then `id [kind] "label" [box] conf` per
    element), data-fenced. The block is STORED in the episode history
    verbatim, so past turns keep showing exactly what was seen."""
    rows = tuple(rows)
    body = format_elements(rows) if rows else "(no elements detected)"
    return data_block(f"{header} — element listing, top to bottom", body)


def return_fields(fields: str) -> str:
    """The declared `returns:` rendered for the model — one spelling for
    the pure-text call and the episode's opening block."""
    return f"{prompts.RETURN_FIELDS_HEADER}\n{fields}"


def labelled(name: str, body: str) -> str:
    """One `context:` entry for the model: `- name: body`, or the name
    with a body of several lines indented under it — the shape a
    declared `returns:` field already reads in."""
    if "\n" in body:
        rows = "\n".join(f"    {line}" for line in body.split("\n"))
        return f"- {name}:\n{rows}"
    return f"- {name}: {body}"
