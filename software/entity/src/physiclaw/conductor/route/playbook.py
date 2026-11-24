"""A playbook file → its `Playbook`: the document's own keys (name,
description, enabled, inputs, returns) around its route, which
`compile.py` compiles; an entry's `run` line reaches the playbook it
names through `playbook_by_id`, the scan's memo, so every document
compiles once. Pure over `(document, Pack)`: `load.pack` reads the
files and calls in here.
"""

from typing import Any

from physiclaw.common import paths
from physiclaw.conductor.route.compile import compile_route
from physiclaw.conductor.spec import specfile
from physiclaw.conductor.spec.conventions import ROUND_MARKS
from physiclaw.conductor.spec.model import (
    Playbook,
    PlaybookError,
    PlaybookInput,
    check_name,
    prose,
    require_str,
)
from physiclaw.conductor.spec.pack import Pack
from physiclaw.conductor.spec.refs import check_refs, field_name, refs_in
from physiclaw.macros import parse as macro_parse
from physiclaw.macros.model import MacroError


def parse_playbook(text: str, name: str, pack: Pack) -> Playbook:
    """One playbook given as YAML text — the text-shaped door tests and
    tooling use; the live path is `scan_playbooks` over the pack's
    playbook files. Raises PlaybookError naming the offending field;
    never a partial spec."""
    data = specfile.load_yaml(text, PlaybookError)
    return parse_playbook_data(data, name, pack)


_PLAY_KEYS = {
    "schema",
    "kind",
    "name",
    "description",
    "enabled",
    "inputs",
    "pages",
    "route",
    "returns",
}


def parse_playbook_data(
    data: Any, name: str, pack: Pack, parsed: dict[str, Playbook] | None = None
) -> Playbook:
    """One playbook's document → a validated Playbook. `name` is the id
    — the folder's name for an entry, `<entry>.<name>` for a playbook
    it runs — and the `name:` inside must be its own name (the folder's,
    or the file's stem), under the `kind:` its position requires. An
    entry's `run` line names one of the playbooks beside it, parsed on
    demand against the same pack (`playbook_by_id`); `parsed` is the
    scan's memo, so every document compiles once and the entry and the
    scan hold one object."""
    if not isinstance(data, dict):
        raise PlaybookError("a playbook must be a YAML mapping (key: value pairs)")
    # A playbook names itself, like a macro and a skill do — and the
    # name must be the file's, so a copied folder cannot lie about
    # what it is (the same rule `app` keeps with the pack folder).
    runs_under = paths.run_by(name)
    own, file = paths.own_name(name), paths.playbook_file(name)
    # The header before any other key, so a file in the wrong folder or
    # the wrong grammar is named for what it IS rather than refused for
    # a key the other grammar happens not to know.
    gap = paths.header_gap(data, paths.kind_of(name))
    if gap is not None:
        raise PlaybookError(f"{file}: {gap}")
    unknown = sorted(set(map(str, data.keys())) - _PLAY_KEYS)
    if unknown:
        raise PlaybookError(f"unknown key(s): {', '.join(unknown)}")
    if "name" not in data:
        raise PlaybookError(f"a playbook has no `name:` — {file} starts `name: {own}`")
    check_name(paths.entry_of(name), "playbook name")
    if runs_under is not None:
        check_name(own, "playbook name")
    declared = require_str(data.get("name"), "`name`")
    if declared != own:
        raise PlaybookError(
            f"name {declared!r} must equal the "
            f"{'file' if runs_under else 'folder'} name {own!r} ({file})"
        )
    description = prose(data.get("description"), "`description`")
    enabled = data.get("enabled", True)
    if not isinstance(enabled, bool):
        raise PlaybookError("`enabled` must be true or false")
    inputs = _parse_inputs(data.get("inputs", {}))
    input_names = {i.name for i in inputs}
    memo = {} if parsed is None else parsed  # ONE memo for every `run` of this route
    route = compile_route(
        data.get("route"),
        pages=data.get("pages"),
        playbook=name,
        input_names=input_names,
        pack=pack,
        resolve_playbook=lambda other: playbook_by_id(other, pack, memo, run_by=name),
    )
    returns = _parse_returns(data.get("returns"), input_names, route.payloads)
    return Playbook(
        app=pack.app,
        name=name,
        description=description,
        enabled=enabled,
        inputs=inputs,
        nodes=tuple(route.nodes),
        start=route.start,
        inline_macros=route.inline,
        recovers=route.recovers,
        prompts_used=route.prompts_used,
        returns=returns,
        end=route.end,
    )


def playbook_by_id(
    name: str,
    pack: Pack,
    parsed: dict[str, Playbook],
    *,
    run_by: str | None = None,
) -> Playbook:
    """A playbook of the pack by id — for an entry's `run` line (`run_by`
    the entry, so the error names the file at fault; the id is then
    `<entry>.<name>`) and for the scan alike, so a run and a walk of it
    read the same file, once (`parsed` memoises). Only an entry runs, so
    a parse can never reach itself."""
    if name in parsed:
        return parsed[name]
    if name in pack.playbook_errors:
        raise PlaybookError(
            f"playbook {name!r} is invalid: {pack.playbook_errors[name]}"
        )
    if name not in pack.playbook_docs:
        # Always run by an entry: the scan only asks for ids it read off
        # disk, and a route's `run` asks for `<this entry>.<name>`.
        entry = paths.entry_of(name)
        siblings = sorted(
            paths.own_name(n) for n in pack.playbook_docs if paths.run_by(n) == entry
        )
        raise PlaybookError(
            f"no playbook {paths.own_name(name)!r} of {entry!r} — it would be "
            f"{paths.playbook_file(name)} (has: {', '.join(siblings) or '(none)'})"
        )
    try:
        spec = parse_playbook_data(pack.playbook_docs[name], name, pack, parsed)
    except PlaybookError as e:
        if run_by is not None:
            raise PlaybookError(f"playbook {name!r} (run by {run_by!r}): {e}") from e
        raise
    parsed[name] = spec
    return spec


def _parse_returns(
    raw: Any, input_names: set[str], payloads: dict[str, tuple[str, ...]]
) -> dict[str, str]:
    """`returns:` — field → template over the playbook's own refs, what
    a `run` of it yields (`{<run>.<field>}`) once its round ends."""
    if raw is None:
        return {}
    if not isinstance(raw, dict) or not raw:
        raise PlaybookError("`returns` must be a mapping of field → template")
    out: dict[str, str] = {}
    for fname, template in raw.items():
        field_name(str(fname), "`returns` field")
        if str(fname) in ROUND_MARKS:
            raise PlaybookError(
                f"`returns` field {fname!r} is how a round records whether it "
                f"ran ({', '.join(sorted(ROUND_MARKS))}) — rename it"
            )
        text = prose(template, f"`returns.{fname}`")
        check_refs(
            refs_in(text, f"`returns.{fname}`"),
            input_names,
            payloads,
            f"`returns.{fname}`",
        )
        out[str(fname)] = text
    return out


def _parse_inputs(raw: Any) -> tuple[PlaybookInput, ...]:
    """`inputs:` through the macro grammar's parser, the error class
    translated at this one seam."""
    try:
        return macro_parse.parse_inputs(raw)
    except MacroError as e:
        raise PlaybookError(str(e)) from e
