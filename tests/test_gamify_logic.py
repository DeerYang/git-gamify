# tests/test_gamify_logic.py
"""
Unit tests for the core gamification numerical logic, such as level and XP calculations.
These tests ensure the mathematical correctness of the leveling system.
"""

import pytest
from gg_cli.gamify import get_level_from_xp, get_total_xp_for_level, get_level_info

@pytest.mark.parametrize("xp, expected_level", [
    (0, 1),      # Initial state
    (99, 1),     # Just before leveling up
    (100, 2),    # Exactly at the threshold for level 2
    (199, 2),    # In the middle of level 2
    (999, 10),   # Just before leaving the first tier
    (1000, 11),  # Exactly at the threshold for level 11 (10 * 100 XP)
    (1249, 11),  # In the middle of level 11
    (3499, 20),  # Just before leaving the second tier
    (3500, 21),  # Exactly at the threshold for level 21 (10*100 + 10*250 XP)
])
def test_get_level_from_xp_scenarios(xp, expected_level):
    """
    Tests that get_level_from_xp returns the correct level for various XP values,
    covering initial, intermediate, and boundary conditions.
    """
    assert get_level_from_xp(xp) == expected_level

@pytest.mark.parametrize("target_level, expected_total_xp", [
    (1, 0),       # No XP required to reach level 1
    (2, 100),     # 100 XP required to reach level 2
    (3, 200),     # 100 (for L2) + 100 (for L3) = 200 XP
    (11, 1000),   # 10 levels * 100 XP/level = 1000 XP
    (12, 1250),   # 1000 (for L1-10) + 250 (for L11) = 1250 XP
    (21, 3500),   # 1000 (for L1-10) + 2500 (for L11-20) = 3500 XP
])
def test_get_total_xp_for_level_scenarios(target_level, expected_total_xp):
    """
    Tests that get_total_xp_for_level correctly calculates the cumulative XP
    needed to reach a specific target level.
    """
    assert get_total_xp_for_level(target_level) == expected_total_xp

def test_get_level_info_boundaries():
    """
    Tests that get_level_info returns the correct tier information
    at the boundaries between level tiers.
    """
    # Level 10 should be in the first tier (100 XP/level)
    _, xp_per_level_10, title_key_10 = get_level_info(10)
    assert xp_per_level_10 == 100
    assert title_key_10 == "level_title_novice"

    # Level 11 should be in the second tier (250 XP/level)
    _, xp_per_level_11, title_key_11 = get_level_info(11)
    assert xp_per_level_11 == 250
    assert title_key_11 == "level_title_apprentice"