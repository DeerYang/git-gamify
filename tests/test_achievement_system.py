"""Unit tests for achievement unlock behavior."""

from __future__ import annotations

from datetime import date

import pytest

from gg_cli.achievements import ACHIEVEMENTS_DEF, check_all_achievements


def test_unlock_first_commit(user_data_factory, translator):
    data = user_data_factory()
    data["stats"]["total_commits"] = 1

    gained_xp = check_all_achievements(data, translator, context={"command": "commit"})

    assert "first_commit" in data["achievements_unlocked"]
    assert gained_xp == ACHIEVEMENTS_DEF["first_commit"]["xp_reward"]
    assert data["achievements_unlocked"]["first_commit"] == date.today().isoformat()


def test_unlock_higher_combo_only_when_lower_is_already_unlocked(user_data_factory, translator):
    data = user_data_factory()
    data["achievements_unlocked"]["combo_3"] = "2025-01-01"
    data["stats"]["consecutive_commit_days"] = 7

    gained_xp = check_all_achievements(data, translator, context={"command": "commit"})

    assert "combo_7" in data["achievements_unlocked"]
    assert gained_xp == ACHIEVEMENTS_DEF["combo_7"]["xp_reward"]


@pytest.mark.parametrize(
    "context, achievement_id",
    [
        ({"command": "commit", "deletions": 501}, "firefighter"),
        ({"command": "commit", "commit_message": "word " * 50}, "storyteller"),
    ],
)
def test_special_achievement_unlocks(user_data_factory, translator, context, achievement_id):
    data = user_data_factory()

    gained_xp = check_all_achievements(data, translator, context=context)

    assert achievement_id in data["achievements_unlocked"]
    assert gained_xp >= ACHIEVEMENTS_DEF[achievement_id]["xp_reward"]


def test_already_unlocked_achievement_grants_no_xp(user_data_factory, translator):
    data = user_data_factory()
    data["stats"]["total_commits"] = 5
    data["achievements_unlocked"]["first_commit"] = "2025-01-01"

    gained_xp = check_all_achievements(data, translator, context={"command": "commit"})

    assert gained_xp == 0
