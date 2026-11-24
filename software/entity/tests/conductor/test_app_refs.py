"""The `app.` root: everything a pack declares in APP.yml or ships
beside it is referenced as `app.<kind>.<name>`; a bare name is beside
the referring file. Pages: a route's own page is declared beside a
waypoint and written bare in that route only."""

from __future__ import annotations

import pytest
from conductor_fakes import PAGES, write_pack

from physiclaw.conductor.load import pack as pb
from physiclaw.conductor.spec.model import PlaybookError

ROUTE = """\
description: one move
inputs:
  keyword:
    description: k
route:
  - page: app.pages.home
  - do: open
    macro: app.macros.open-app
    with: {message: "{inputs.keyword}"}
  - page: app.pages.home
"""


def _entry(app: str, name: str):
    pack = pb.load_pack(app)
    return next(e for e in pb.scan_playbooks(app, pack) if e.name == name)


def test_a_manifest_page_is_app_pages_and_a_bare_name_is_refused_with_the_hint() -> (
    None
):
    write_pack(
        "demo",
        playbooks={
            "buy": ROUTE.replace("- page: app.pages.home\n", "- page: home\n", 1)
        },
    )

    err = _entry("demo", "buy").error or ""
    assert "page 'home' is not declared in this route" in err
    assert "the pack's is `app.pages.home`" in err


def test_a_route_declared_page_is_bare_and_its_own() -> None:
    own = ROUTE.replace(
        "  - page: app.pages.home\n  - do: open",
        "  - page: mine\n    description: this route's own\n"
        '    anchors: ["Mine"]\n  - do: open',
        1,
    ).replace("  - page: app.pages.home\n", "  - page: mine\n")
    other = ROUTE.replace("app.pages.home", "app.pages.mine")
    write_pack("demo", playbooks={"buy": own, "track": other})

    assert _entry("demo", "buy").error is None
    err = _entry("demo", "track").error or ""
    assert "declared in buy/PLAYBOOK.yml" in err and "move it to APP.yml" in err


def test_a_declaration_under_an_app_pages_waypoint_is_refused() -> None:
    text = ROUTE.replace(
        "  - page: app.pages.home\n  - do: open",
        '  - page: app.pages.home\n    anchors: ["X"]\n  - do: open',
        1,
    )
    write_pack("demo", playbooks={"buy": text})

    assert "written bare: `page: home`" in (_entry("demo", "buy").error or "")


def test_a_manifest_hand_and_a_landmark_use_the_app_root_too() -> None:
    from conductor_fakes import PAGES

    write_pack(
        "demo",
        playbooks={"buy": ROUTE},
        pages=PAGES.rstrip("\n")
        + '\nextra:\n  description: one more\n  anchors: ["Extra"]\n'
        + "  recover: {macro: open-app}\n",
    )
    with pytest.raises(PlaybookError, match=r"app\.macros\.<name>"):
        pb.load_pack("demo")

    text = ROUTE.replace(
        "  - page: app.pages.home\n",
        "  - page: app.pages.home\n    recover: {tap: landmarks.back}\n",
        1,
    )
    write_pack(
        "demo",
        playbooks={"buy": text},
        landmarks='back:\n  label: "b"\n  at: [0.1, 0.1, 0.2, 0.2]\n',
    )
    assert "app.landmarks.<name>" in (_entry("demo", "buy").error or "")


def test_a_pack_cannot_be_named_app() -> None:
    write_pack("app", playbooks={})
    with pytest.raises(PlaybookError, match="reference word"):
        pb.load_pack("app")


# ---------- a page says what it is ----------


def test_a_page_says_what_it_is_and_the_refusal_reads_as_a_menu() -> None:
    described = PAGES.replace("description: the home page", "description: the feed")
    write_pack(
        "demo",
        pages=described,
        playbooks={"buy": ROUTE.replace("app.pages.home", "app.pages.homme", 1)},
    )

    assert pb.load_pack("demo").pages["home"].description == "the feed"
    # Misname one and the pack hands back its pages with what each IS,
    # one per line, instead of a wall of names.
    assert "\n  app.pages.home — the feed" in (_entry("demo", "buy").error or "")


def test_a_page_that_says_nothing_is_no_page() -> None:
    # Required, as a macro's and a playbook's description is: a page
    # nobody can say in prose is one nobody can tell from its neighbour.
    write_pack("demo", pages='home:\n  anchors: ["Files"]\n')

    with pytest.raises(PlaybookError, match=r"`description` is required"):
        pb.load_pack("demo")


def test_a_description_beside_a_waypoint_that_declares_nothing_is_refused() -> None:
    # It would say what an already-declared page is, from a file that
    # does not declare it — inert, so it is refused where it is written.
    write_pack(
        "demo",
        playbooks={
            "buy": ROUTE.replace(
                "  - page: app.pages.home\n",
                "  - page: app.pages.home\n    description: a note\n",
                1,
            )
        },
    )

    assert "belongs where the page is declared" in (_entry("demo", "buy").error or "")


# ---------- a route's own `pages:` block ----------

BLOCK = """\
description: one move
inputs:
  keyword:
    description: k
pages:
  mine:
    description: the mine page
    anchors: ["Mine"]
    recover: go_back
    tries: 3
route:
  - page: mine
  - do: open
    macro: app.macros.open-app
    with: {message: "{inputs.keyword}"}
  - page: mine
"""


def test_a_pages_block_declares_the_routes_own_pages_bare() -> None:
    write_pack("demo", playbooks={"buy": BLOCK})

    pack = pb.load_pack("demo")
    assert pack.route_pages == {"mine": "buy"} and "mine" in pack.pages
    entry = _entry("demo", "buy")
    assert entry.error is None, entry.error
    assert entry.spec is not None and entry.spec.start == "mine"
    # The block's hand is the page's default on the route.
    r = entry.spec.recovers["mine"]
    assert r.tries == 3 and r.elsewhere is not None and r.elsewhere.tool == "go_back"


def test_a_waypoint_overrides_the_blocks_hand() -> None:
    text = BLOCK.replace(
        "  - page: mine\n  - do: open",
        "  - page: mine\n    recover: home_screen\n  - do: open",
    )
    write_pack("demo", playbooks={"buy": text})

    r = _entry("demo", "buy").spec.recovers["mine"]
    assert r.elsewhere is not None and r.elsewhere.tool == "home_screen"


def test_a_block_page_is_private_and_declared_once() -> None:
    write_pack(
        "demo",
        playbooks={
            "buy": BLOCK,
            "track": ROUTE.replace("app.pages.home", "app.pages.mine"),
        },
    )
    err = _entry("demo", "track").error or ""
    assert "declared in buy/PLAYBOOK.yml" in err and "move it to APP.yml" in err

    twice = BLOCK.replace(
        "  - page: mine\n  - do: open",
        '  - page: mine\n    anchors: ["Again"]\n  - do: open',
    )
    write_pack("demo", playbooks={"buy": twice})
    with pytest.raises(PlaybookError, match="declared twice"):
        pb.load_pack("demo")

    write_pack("demo", playbooks={"buy": BLOCK.replace("mine", "home")})
    with pytest.raises(PlaybookError, match="declared twice"):
        pb.load_pack("demo")


def test_a_block_is_validated_like_the_manifests_pages() -> None:
    # The pack door parses every declaration site, the block included.
    write_pack(
        "demo", playbooks={"buy": BLOCK.replace('anchors: ["Mine"]', "anchors: []")}
    )
    with pytest.raises(PlaybookError, match="non-empty"):
        pb.load_pack("demo")
