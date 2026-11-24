"""Resolving what a route names: a macro (a pack hand, this entry's own
file, or an inline body under its synthesized name), a prompt file, a
landmark. An inline macro is single-use by construction: its name is
synthesized `<playbook>.<move>` or `<playbook>.<name>.<role>`,
dot-joined, a spelling no directory macro can take, so the pack's
dispatch namespace never collides. Under an inline `macro:` the macro
grammar applies (single-name `{x}` templates); outside it, refs stay
dotted.
"""

from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from physiclaw.common import paths
from physiclaw.common.paths import (
    PACK_MACROS_DIRNAME,
    PACK_PROMPTS_DIRNAME,
    PROMPT_SUFFIX,
    entry_of,
)
from physiclaw.conductor.route.scope import Scope, SlotResolve
from physiclaw.conductor.spec.match import page_resolver
from physiclaw.conductor.spec.model import (
    Playbook,
    PlaybookError,
    check_name,
    require_str,
)
from physiclaw.conductor.spec.pack import Pack, Scanned
from physiclaw.macros.model import (
    LANDMARKS_KIND,
    MACROS_KIND,
    PROMPTS_KIND,
    Macro,
    MacroError,
    app_ref,
    app_refs,
    parse_ref,
)
from physiclaw.macros.parse import MacroResolver, parse_inline_macro


def landmark_name(scope: Scope, value: Any, where: str) -> str:
    """An `app.landmarks.<name>` reference resolved to its bare name —
    ONE spelling for a landmark `given:` and a recover hand's
    `tap:`. The name
    half rides the shared name grammar (`check_name`), so a landmark
    reference can never drift from the section's own naming rule."""
    r = parse_ref(value) if isinstance(value, str) else None
    if r is None or not r.is_app(LANDMARKS_KIND):
        raise PlaybookError(
            f"{where}: {value!r} must look like `{app_ref(LANDMARKS_KIND, '<name>')}`"
        )
    name = r.name
    check_name(name, where)
    if name not in scope.pack.landmarks:
        known = ", ".join(sorted(scope.pack.landmarks)) or "(none)"
        raise PlaybookError(
            f"{where}: names landmark {name!r} — not declared under "
            f"`landmarks`. Declared: {known}"
        )
    return name


def _dispatch(*parts: str) -> str:
    """One dot-joined dispatch name, the macro namespace's one speller:
    `<entry>.<file>` for a recorded hand, `<playbook>.<move>[.<role>]`
    for an inline body (a run-only playbook's id carries its entry, so
    its bodies can never claim the entry's name). `check_name` rejects
    dots, so neither can collide with a pack macro."""
    return ".".join(parts)


def local_registry(entry: str, pack: Pack, local: Scanned[Macro]) -> dict[str, Macro]:
    """The route's inline registry, opened with the entry's recorded
    hands — the playbooks it runs share them: each
    `<entry>/macros/<name>.yml` dispatches as `<entry>.<name>` — an
    inline body written down — referenced or not (a stepping tool, an
    agent's `tools:` may name it). A pack hand of the same name is no
    clash: a bare reference is always the file beside this one, the
    pack's is `app.macros.<name>`."""
    return {
        _dispatch(entry, name): replace(spec, name=_dispatch(entry, name))
        for name, spec in local.ok.items()
    }


def route_resolver(
    playbook: str, pack: Pack, inline: dict[str, Macro], local: Scanned[Macro]
) -> SlotResolve:
    """The name-or-inline resolution every macro-carrying slot shares —
    a do's `macro:`, an ask's `resume:`, a page's `recover:`. ONE home
    for the whole idiom: the synthesized-name rule
    (`<playbook>.<name>[.<role>]`, dot-joined so it can never collide
    with a pack macro — `check_name` rejects dots), the MacroError
    framing, the inline registry, and the file validation (a broken
    macro reports its cause, an unknown one lists what exists) — so
    the slots can never drift. Returns the resolved Macro; its `.name`
    is the dispatch name either way. A bare name is the file beside
    this one — the ENTRY's `macros/`, shared by the playbooks it runs
    (already in `inline`, dispatch `app/<entry>.<name>`) — and
    `app.macros.<name>` one of the pack's (dispatch `app/<name>`). An
    inline body is named for the file that writes it
    (`app/<entry>.<playbook>.<move>`), so one can never claim the
    entry's name."""

    entry = entry_of(playbook)
    folder = f"{entry}/{PACK_MACROS_DIRNAME}/"
    page_of = page_resolver(pack.app, pack.pages, pack.prints)
    pack_macro = macro_resolver(pack.macros, pack.macro_errors)

    def macro_of(ref: str) -> Macro:
        """The one lookup a `do:`, a hand, a grant and an inline body's
        `run:` share."""
        r = parse_ref(ref)
        if r is not None and r.shared:
            return pack_macro(ref)  # `app.macros.<name>`, or its own refusal
        if ref in local.errors:
            raise MacroError(
                f"macro {ref!r} ({folder}{ref}.yml) is invalid: {local.errors[ref]}"
            )
        if ref in local.ok:
            return inline[_dispatch(entry, ref)]
        raise MacroError(
            _not_here("macro", ref, folder, local.ok)
            + pack_hint(
                MACROS_KIND, ref, ref in pack.macros or ref in pack.macro_errors
            )
        )

    def resolve(raw: Any, where: str, nid: str, role: str | None = None) -> Macro:
        slot = role or "macro"
        if isinstance(raw, dict):
            mname = _dispatch(playbook, nid, *([role] if role else []))
            if mname in inline:
                raise PlaybookError(
                    f"{where}: inline `{slot}` would be named {mname!r}, which "
                    f"the recorded {folder}{nid}.yml already holds — rename one"
                )
            try:
                spec = parse_inline_macro(raw, mname, page_of, macro_of)
            except MacroError as e:
                raise PlaybookError(f"{where}: inline `{slot}`: {e}") from e
            inline[mname] = spec
            return spec
        if raw is not None and not isinstance(raw, str):
            raise PlaybookError(
                f"{where}: `{slot}` must be a macro name or an inline "
                "mapping with `steps:`"
            )
        mname = require_str(raw, f"{where}: `{slot}`")
        try:
            return macro_of(mname)
        except MacroError as e:
            raise PlaybookError(f"{where}: {slot} {e}") from e

    return resolve


def _not_here(kind: str, name: str, folder: str, have: "Mapping[str, Any]") -> str:
    """The one wording of "no such file beside this one", listing what is."""
    listed = ", ".join(sorted(have)) or "(none)"
    return f"no {kind} {name!r} in {folder} ({listed})"


def pack_hint(kind: str, name: str, exists: bool) -> str:
    """The clause that names the pack's spelling when a bare name only
    the pack holds was written — "" otherwise."""
    return f" — the pack's is `{app_ref(kind, name)}`" if exists else ""


def prompt_text(scope: Scope, raw: str, where: str) -> str:
    """An agent's `prompt:` — the prose itself, `prompts.<name>` for this
    route's `prompts/<name>.md`, or `app.prompts.<name>` for the
    pack's. Resolved here, at parse, so the node carries text either
    way and nothing downstream knows which form the author chose."""
    ref = raw.strip()
    r = parse_ref(ref) if not any(c.isspace() for c in ref) else None
    if r is None or r.kind != PROMPTS_KIND:
        return raw
    local = not r.shared
    files = scope.prompts_local if local else scope.prompts_pack
    folder = (
        f"{scope.entry}/{PACK_PROMPTS_DIRNAME}/"
        if local
        else f"{PACK_PROMPTS_DIRNAME}/"
    )
    name = r.name
    check_name(name, f"{where}: `prompt` ({ref})")
    if name in files.errors:
        raise PlaybookError(
            f"{where}: `prompt` names {ref}, and {folder}{name}{PROMPT_SUFFIX} is "
            f"invalid: {files.errors[name]}"
        )
    if name not in files.ok:
        raise PlaybookError(
            f"{where}: `prompt` names {ref}, but "
            + _not_here("file", f"{name}{PROMPT_SUFFIX}", folder, files.ok)
            + pack_hint(PROMPTS_KIND, name, local and name in scope.prompts_pack.ok)
        )
    scope.prompts_used.add(f"{folder}{name}{PROMPT_SUFFIX}")
    return files.ok[name]


def argless_macro(
    raw: Any, key: str, where: str, nid: str, resolve: SlotResolve
) -> Macro:
    """Resolve one argument-less pack macro for a helper-hand slot
    (`resume:`, `recover:`, an agent's `tools:`). The slot may wrap its
    body one level (`{macro: ...}`) — unwrapped HERE, the rule's one
    home, so the resolver sees the same shapes a `do` does. All roles
    dispatch with no arguments, so a required input could only abort at
    run time — right after a confirmed ask, at the worst moment — hence
    the lint. Returns the resolved Macro: its `.name` is the dispatch
    name every slot stores (a playbook-local one reads
    `<playbook>.<name>`), and a grant's guard reads its taps."""
    if isinstance(raw, dict) and set(raw) == {"macro"}:
        raw = raw["macro"]
    spec = resolve(raw, where, nid, key)
    required = sorted(i.name for i in spec.inputs if i.required)
    if required:
        raise PlaybookError(
            f"{where}: `{key}` macro {spec.name!r} requires input(s) "
            f"{', '.join(required)} — the walk dispatches {key} with no "
            "arguments"
        )
    return spec


def macro_resolver(ok: Mapping[str, Macro], errors: Mapping[str, str]) -> MacroResolver:
    """`app.macros.<name>` → one of the pack's hands, or why not — the one
    lookup a playbook's `macro:`, an agent's `tools:`, a manifest hand
    and a macro file's `run:` all end in. One wording for "broken" and
    "not here"."""

    def resolve(ref: str) -> Macro:
        r = parse_ref(ref)
        if r is None or not r.is_app(MACROS_KIND):
            raise MacroError(
                f"{ref!r} is not a pack macro reference — the pack's hands are "
                f"`{app_ref(MACROS_KIND, '<name>')}`"
            )
        if r.name in errors:
            raise MacroError(f"pack macro {r.name!r} is invalid: {errors[r.name]}")
        if r.name not in ok:
            available = app_refs(MACROS_KIND, ok)
            raise MacroError(
                f"{ref!r} not found in this pack's {paths.PACK_MACROS_DIRNAME}/ — "
                f"available: {available}"
            )
        return ok[r.name]

    return resolve


def claim_inline(spec: Playbook, pack: Pack, claimed: dict[str, str]) -> None:
    """Record the dispatch names this FILE writes, raising on one another
    file of the pack already holds — the route compiler's own no-shadow
    rule (`route_resolver`), at pack scope. The entry's recorded
    hands are in every one of its playbooks' registries by design, so
    they are not this file's to claim: only its inline bodies are."""
    entry = paths.entry_of(spec.name)
    recorded = {f"{entry}.{n}" for n in pack.local_for(spec.name).macros.ok}
    for mname in spec.inline_macros:
        if mname in recorded:
            continue
        held = claimed.setdefault(mname, spec.name)
        if held != spec.name:
            raise PlaybookError(
                f"inline macro {mname!r} is already {held!r}'s — one dispatch "
                f"name, one body; rename the move or the page it hangs on"
            )
