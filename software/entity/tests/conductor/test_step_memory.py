"""Tests for `spec.memory` and `steps.memory` — what an agent step loads
beside its prompt, exactly as declared and nothing more."""

from __future__ import annotations

import pytest

from physiclaw.common import daylog, paths
from physiclaw.common.text import write_text
from physiclaw.conductor.spec import memory as memory_spec
from physiclaw.conductor.steps import memory

MEMORY = "## shopping_prefs 购物偏好\n- 只买伊利\n\n## shopping_blacklist\n- 三无\n"


def _write_memory(text: str = MEMORY) -> None:
    f = paths.memory_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    write_text(f, text)


@pytest.mark.parametrize(
    "spec, ok",
    [
        ({"shopping_prefs": True}, True),
        ({"all": True}, True),
        ({"log": 12}, True),
        ({"shopping_prefs": True, "log": 3}, True),
        ({"log": True}, False),  # a count, not a switch
        ({"log": 0}, False),
        ({"log": 999}, False),
        ({"shopping_prefs": "yes"}, False),  # named to include, or left out
        ({"Bad-Slug": True}, False),
        ([], False),
    ],
)
def test_memory_gap_owns_the_vocabulary(spec, ok: bool) -> None:
    assert (memory_spec.memory_gap(spec) is None) is ok


def test_memory_slice_is_token_matched_and_fail_closed() -> None:
    # Least-privilege: only the named section travels — token-exact
    # heading match (no substring bleed), and NO match means NO text.
    _write_memory()

    loaded = memory.load({"shopping_prefs": True})
    assert (
        "只买伊利" in loaded["shopping_prefs"]
        and "三无" not in loaded["shopping_prefs"]
    )
    # `shopping` is a substring of both headings but a token of neither.
    assert memory.load({"shopping": True}) == {"shopping": ""}
    assert memory.load({"nothing": True}) == {"nothing": ""}


def test_the_whole_file_and_the_log_load_when_named() -> None:
    _write_memory()
    daylog.append_log("[11:02] demo: bought milk ¥45")

    loaded = memory.load({"all": True, "log": 5})

    assert "只买伊利" in loaded["all"] and "三无" in loaded["all"]
    assert "bought milk ¥45" in loaded["log"]


def test_naming_no_part_reads_nothing() -> None:
    _write_memory()
    daylog.append_log("[11:02] demo: bought milk ¥45")

    assert memory.load({}) == {}
