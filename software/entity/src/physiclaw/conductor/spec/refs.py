"""The ref grammar — `{inputs.name}` and `{move.field}`, validated at
parse (`refs_in`, `check_refs`) and filled at run (`fill_refs`).

Every ref is dotted: `inputs.<name>` reads a declared input, `<move>.<field>`
an EARLIER agent step's declared return field (or the quoting step's
own: its last answer, empty the first time), `ask.total` a payment
ask's quoted total. A bare `{name}` is a load error everywhere but an
agent's prompt, where it names one of that step's `given:` values
(`names_in`, `fill_names`). Refs are playbook-level — resolved to plain strings before any macro sees them,
so pack macros keep the stock single-name template grammar.
"""

import re
from collections.abc import Iterator
from typing import Any

from physiclaw.conductor.spec import specfile
from physiclaw.conductor.spec.model import INPUTS_ROOT, AgentNode, Node, PlaybookError

# The playbook's brace grammar, one tokenizer for its two spellings:
# `{root.name}` — a ref, always dotted (`inputs.` / an earlier agent
# step's id; the root follows the move-name grammar, hyphens included —
# `{pick-into-cart.message}`; the field stays input-shaped) — and
# `{name}` — a prompt's reference to one of its step's `given:` keys,
# input-shaped like the key. A name has no dot and a ref must, so the
# two never collide; each reader accepts one group and refuses the
# other. Dotted refs are deliberately NOT part of the macro template
# layer (its tokenizer rejects them); same `{{`/`}}` escapes, same
# fail-at-load-on-stray-brace rule.
_REF = r"[a-z0-9][a-z0-9_-]*\.[a-z][a-z0-9_]*"
_NAME = r"[a-z][a-z0-9_]*"
TOKEN_RE = re.compile(r"\{\{|\}\}|\{(" + _REF + r")\}|\{(" + _NAME + r")\}|[{}]")
REF, NAME = 1, 2  # TOKEN_RE's groups: which spelling a brace pair holds
# The dotted spelling with no braces — how a `given:` value may name
# its ref when it is nothing but the ref (`said: inputs.user_said`).
BARE_REF_RE = re.compile(_REF)


def field_name(name: Any, what: str) -> str:
    """The one naming rule for the values `{x.y}` refs read — an agent's
    return fields, spelled like the inputs they sit beside."""
    if not isinstance(name, str) or not specfile.INPUT_NAME_RE.match(name):
        raise PlaybookError(
            f"{what} {name!r} must be lowercase, start with a "
            "letter, and contain only letters/digits/underscores"
        )
    return name


def _braces(text: str) -> Iterator[re.Match[str]]:
    """Every brace token of `text` but the escapes."""
    return (m for m in TOKEN_RE.finditer(text) if m.group(0) not in ("{{", "}}"))


def refs_in(text: str, where: str) -> set[str]:
    """Every dotted ref a template names; anything else in braces is a
    load error."""
    refs: set[str] = set()
    for m in _braces(text):
        if m.group(REF) is None:
            raise PlaybookError(
                f"{where}: stray {m.group(0)!r} — every ref is dotted: "
                "{inputs.name} for an input, {node.field} for an earlier "
                "agent step's output, {{ / }} for a literal brace"
            )
        refs.add(m.group(REF))
    return refs


def names_in(text: str, where: str) -> set[str]:
    """Every `{name}` a prompt refers to. A dotted ref is refused with
    the way to write it; any other stray brace as `refs_in` does."""
    names: set[str] = set()
    for m in _braces(text):
        if m.group(NAME) is not None:
            names.add(m.group(NAME))
        elif m.group(REF) is not None:
            raise PlaybookError(
                f"{where}: {m.group(0)} — a prompt refers to a value by the "
                "name its `given:` gives it: declare "
                f"`<name>: {m.group(REF)}` there and write {{<name>}}"
            )
        else:
            raise PlaybookError(
                f"{where}: stray {m.group(0)!r} — a prompt writes {{name}} for "
                "a `given:` value, {{ / }} for a literal brace"
            )
    return names


def _fill(text: str, values: dict[str, str], group: int, where: str) -> str:
    """`text` with every brace pair of one spelling replaced by its
    value, the escapes by their brace. The parse-time reader of the
    same group has already refused the other spelling and any stray."""

    def repl(m: re.Match[str]) -> str:
        token = m.group(0)
        if token == "{{":
            return "{"
        if token == "}}":
            return "}"
        key = m.group(group)
        if key is None:
            raise PlaybookError(f"{where}: stray {token!r} in {text!r}")
        if key not in values:
            raise PlaybookError(f"{where}: no value for {token}")
        return values[key]

    return TOKEN_RE.sub(repl, text)


def fill_names(text: str, values: dict[str, str], where: str) -> str:
    """A prompt with each `{name}` replaced by its `given:` value — the
    runtime half of `names_in`, filled ONCE when the step opens."""
    return _fill(text, values, NAME, where)


def check_refs(
    refs: set[str],
    input_names: set[str],
    payloads: dict[str, tuple[str, ...]],
    where: str,
) -> None:
    """Every ref resolves: an `inputs.*` to a declared input, anything
    else to an EARLIER move's declared output field — or the quoting
    agent's own, declared before its prompt is read."""
    for ref in sorted(refs):
        root, _, fld = ref.partition(".")
        if root == INPUTS_ROOT:
            if fld not in input_names:
                raise PlaybookError(f"{where}: {{{ref}}} not declared under `inputs`")
        elif root not in payloads:
            raise PlaybookError(
                f"{where}: {{{ref}}} references move {root!r}, which "
                "is not an EARLIER agent step (or this one) — outputs wire "
                "forward only, in route order"
            )
        elif fld not in payloads[root]:
            raise PlaybookError(
                f"{where}: {{{ref}}}: move {root!r} has no output "
                f"{fld!r} (has: {', '.join(payloads[root]) or '(none)'})"
            )


def check_arg_refs(
    value: Any,
    input_names: set[str],
    payloads: dict[str, tuple[str, ...]],
    where: str,
) -> None:
    """`check_refs` over a `with:` value — recursing into lists and
    mappings exactly as `fill_refs` fills them."""
    if isinstance(value, str):
        check_refs(refs_in(value, where), input_names, payloads, where)
    elif isinstance(value, list):
        for v in value:
            check_arg_refs(v, input_names, payloads, where)
    elif isinstance(value, dict):
        for v in value.values():
            check_arg_refs(v, input_names, payloads, where)


def fill_args(args: dict, values: dict[str, str], where: str) -> dict[str, Any]:
    """A move's `with:` block filled — each value through `fill_refs`,
    named "<where> `with.<key>`" in any error."""
    return {
        k: fill_refs(v, values, where=f"{where} `with.{k}`") for k, v in args.items()
    }


def fill_refs(value: Any, values: dict[str, str], where: str) -> Any:
    """A `with:` value with its refs resolved from `values` — the runtime
    half of the ref grammar, beside TOKEN_RE so no consumer re-derives
    the braces. `values` is keyed by the dotted ref spellings themselves
    (`inputs.name`, `node.field`). Recurses into lists/dicts exactly as
    `check_arg_refs` validates them. Raises PlaybookError on a ref with
    no value (e.g. an agent output not yet recorded)."""
    if isinstance(value, list):
        return [fill_refs(v, values, where) for v in value]
    if isinstance(value, dict):
        return {k: fill_refs(v, values, where) for k, v in value.items()}
    if not isinstance(value, str):
        return value
    return _fill(value, values, REF, where)


def own_fields(node: "Node | None") -> dict[str, str]:
    """The CURSOR step's own return fields, empty — what it reads of its
    own last answer before it has given one (the parser lets a prompt
    quote earlier steps' fields and its own).

    Its own only. Blanking every step's fields would make `fill_refs`
    unable to fail: a ref to a step that has not answered is the
    fail-closed guard behind a stepping jump and behind a suspension
    that outlived an edit to an agent's `returns:`, and the message it
    raises is what a handover reports."""
    if not isinstance(node, AgentNode):
        return {}
    return {f"{node.id}.{f}": "" for f in node.return_fields}
