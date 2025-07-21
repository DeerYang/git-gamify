# tests/test_achievement_system.py
"""Unit tests for the achievement unlocking logic."""

import pytest
from gg_cli.achievements import check_all_achievements
from gg_cli.translator import Translator


@pytest.fixture
def mock_translator() -> Translator:
    """
    Provides a mock Translator instance that avoids file I/O.
    The mock `t` method simply returns the key, which is sufficient for logic testing.
    """
    translator = Translator()
    translator.t = lambda key, **kwargs: key
    return translator


@pytest.fixture
def base_user_data() -> dict:
    """Provides a clean, default user data structure for each test."""
    return {
        "stats": {
            "total_commits": 0,
            "total_pushes": 0,
            "consecutive_commit_days": 0,
        },
        "achievements_unlocked": {}
    }


def test_unlock_first_commit(base_user_data: dict, mock_translator: Translator):
    """Tests that the 'first_commit' achievement unlocks at exactly 1 commit."""
    # Arrange: Set user stats to meet the condition
    base_user_data["stats"]["total_commits"] = 1

    # Act: Run the achievement checker
    xp = check_all_achievements(base_user_data, mock_translator, context={"command": "commit"})

    # Assert: Check that the achievement is unlocked and the correct XP is awarded
    assert "first_commit" in base_user_data["achievements_unlocked"]
    assert xp == 50


def test_unlock_combo_master_only(base_user_data: dict, mock_translator: Translator):
    """
    Tests unlocking a higher-tier achievement ('combo_7') without also getting
    credit for a lower-tier one ('combo_3') that is already unlocked.
    """
    # Arrange: Assume 'combo_3' is already unlocked and the user meets the 'combo_7' condition
    base_user_data["achievements_unlocked"]["combo_3"] = "2025-01-01"
    base_user_data["stats"]["consecutive_commit_days"] = 7

    xp = check_all_achievements(base_user_data, mock_translator, context={"command": "commit"})

    assert "combo_7" in base_user_data["achievements_unlocked"]
    # Assert: The awarded XP should only be from the 'combo_7' achievement.
    assert xp == 300


def test_unlock_firefighter(base_user_data: dict, mock_translator: Translator):
    """Tests that the 'firefighter' achievement unlocks with enough deletions."""
    # Arrange: Provide a context with sufficient deletion stats
    context = {"command": "commit", "deletions": 501}

    xp = check_all_achievements(base_user_data, mock_translator, context)

    assert "firefighter" in base_user_data["achievements_unlocked"]
    assert xp == 200


def test_no_unlock_if_already_unlocked(base_user_data: dict, mock_translator: Translator):
    """Tests that an already unlocked achievement does not grant XP again."""
    # Arrange: Set up a user who has already unlocked 'first_commit'
    base_user_data["stats"]["total_commits"] = 5
    base_user_data["achievements_unlocked"]["first_commit"] = "2025-01-01"

    # Act: Run the checker again
    xp = check_all_achievements(base_user_data, mock_translator, context={"command": "commit"})

    # Assert: No new XP should be awarded.
    assert xp == 0