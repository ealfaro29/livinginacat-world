"""The manifest's top-level grammar — `APP.yml`'s sections and its meta,
checked as data: the readers (`load.files`, `load.pack`) call in here
after the file is read.
"""

from physiclaw.common import paths
from physiclaw.conductor.spec import specfile
from physiclaw.macros.model import APP_ROOT, REF_KINDS

# The manifest's sections — what the app IS and what its routes share.
# Never a route: each playbook is its own `<name>/PLAYBOOK.yml` beside the
# manifest (`load_playbook_docs`), so `playbooks:` is refused with the
# reason.
_PACK_TOP_KEYS = frozenset(
    {"schema", "kind", "app", "description", "placeholders", "pages", "landmarks"}
)


def check_manifest_keys(data: dict, app: str, error_cls: type[ValueError]) -> None:
    """The manifest's top: only the known sections, the header first,
    never a `playbooks:` list."""
    if "playbooks" in data:
        raise error_cls(
            f"{app}/{paths.PACK_FILENAME}: `playbooks` does not live in the manifest "
            "— write each playbook as its own <name>/PLAYBOOK.yml folder beside "
            "it (the file body is the playbook: name, description, enabled, "
            "inputs, route)"
        )
    gap = paths.header_gap(data, paths.KIND_MANIFEST)
    if gap is not None:
        raise error_cls(f"{app}/{paths.PACK_FILENAME}: {gap}")
    unknown = sorted(set(map(str, data.keys())) - _PACK_TOP_KEYS)
    if unknown:
        raise error_cls(
            f"{app}/{paths.PACK_FILENAME}: unknown key(s): {', '.join(unknown)} "
            f"(sections: {', '.join(sorted(_PACK_TOP_KEYS))})"
        )


def check_manifest_meta(
    doc: dict, app: str, folder: str, error_cls: type[ValueError]
) -> None:
    """The manifest's meta, every field optional: `app` (which app this
    pack automates) must equal the directory it loads from when present
    — the folder IS the app, the field catches a pack copied under the
    wrong name;
    `description` is real prose when present (`install` prints it);
    `placeholders` (install-time constants, validated here so `check`
    catches a malformed map before install prompts read it) is
    name → {description, [example]}."""
    require_str, prose, _, _ = specfile.bind(error_cls)
    if "app" in doc:
        declared = require_str(doc.get("app"), "`app`")
        if declared != folder:
            raise error_cls(
                f"app {declared!r} must equal the pack directory {folder!r}"
            )
    if app == APP_ROOT or app in REF_KINDS:
        raise error_cls(f"a pack cannot be named {app!r} — it is a reference word")
    if "description" in doc:
        prose(doc.get("description"), "`description`")
    ph = doc.get("placeholders")
    if ph is None:
        return
    if not isinstance(ph, dict):
        raise error_cls("`placeholders` must be a mapping of TOKEN → spec")
    for key, spec in ph.items():
        where = f"placeholder {key!r}"
        if not isinstance(spec, dict) or set(spec) - {"description", "example"}:
            raise error_cls(f"{where} must be a {{description, example}} mapping")
        prose(spec.get("description"), f"{where}: `description`")
