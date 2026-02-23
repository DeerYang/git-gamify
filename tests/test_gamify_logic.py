"""Unit tests for level tier math and XP progression invariants."""

from __future__ import annotations

import pytest

from gg_cli.gamify import (
    LEVEL_TIERS,
    get_level_from_xp,
    get_level_info,
    get_total_xp_for_level,
)


@pytest.mark.parametrize(
    "xp, expected_level",
    [
        (0, 1),
        (99, 1),
        (100, 2),
        (999, 10),
        (1000, 11),
        (3499, 20),
        (3500, 21),
    ],
)
def test_get_level_from_xp_scenarios(xp, expected_level):
    assert get_level_from_xp(xp) == expected_level


@pytest.mark.parametrize(
    "target_level, expected_total_xp",
    [
        (1, 0),
        (2, 100),
        (3, 200),
        (11, 1000),
        (12, 1250),
        (21, 3500),
    ],
)
def test_get_total_xp_for_level_scenarios(target_level, expected_total_xp):
    assert get_total_xp_for_level(target_level) == expected_total_xp


def test_get_level_info_boundaries():
    _, xp_per_level_10, title_key_10 = get_level_info(10)
    assert xp_per_level_10 == 100
    assert title_key_10 == "level_title_novice"

    _, xp_per_level_11, title_key_11 = get_level_info(11)
    assert xp_per_level_11 == 250
    assert title_key_11 == "level_title_apprentice"


def test_level_from_xp_is_monotonic():
    previous_level = 1
    for xp in range(0, 20000, 37):
        level = get_level_from_xp(xp)
        assert level >= previous_level
        previous_level = level


def test_get_level_info_handles_invalid_level_inputs():
    assert get_level_info(0) == LEVEL_TIERS[0]
    assert get_level_info(-5) == LEVEL_TIERS[0]
    assert get_level_info("bad") == LEVEL_TIERS[0]


def test_get_level_from_xp_handles_invalid_inputs():
    assert get_level_from_xp(-1) == 1
    assert get_level_from_xp("bad") == 1
