"""Unit tests for achievement unlock behavior."""

from __future__ import annotations

from datetime import date

import pytest

from gg_cli.achievements import ACHIEVEMENTS_DEF, check_all_achievements


def test_unlock_first_commit(user_data_factory, translator):
    """First commit achievement should unlock and grant its configured XP."""
    data = user_data_factory()
    data["stats"]["total_commits"] = 1

    gained_xp = check_all_achievements(data, translator, context={"command": "commit"})

    assert "first_commit" in data["achievements_unlocked"]
    assert gained_xp == ACHIEVEMENTS_DEF["first_commit"]["xp_reward"]
    assert data["achievements_unlocked"]["first_commit"] == date.today().isoformat()


def test_unlock_higher_combo_only_when_lower_is_already_unlocked(user_data_factory, translator):
    """Higher streak tiers should unlock when prerequisite progression exists."""
    data = user_data_factory()
    data["achievements_unlocked"]["combo_3"] = "2025-01-01"
    data["stats"]["consecutive_commit_days"] = 7

    gained_xp = check_all_achievements(data, translator, context={"command": "commit"})

    assert "combo_5" in data["achievements_unlocked"]
    assert "combo_7" in data["achievements_unlocked"]
    assert gained_xp >= ACHIEVEMENTS_DEF["combo_7"]["xp_reward"]


@pytest.mark.parametrize(
    "context, achievement_id",
    [
        ({"command": "commit", "deletions": 501}, "firefighter"),
        ({"command": "commit", "commit_message": "word " * 50}, "storyteller"),
        ({"command": "commit", "commit_message": "fix: close bug #12"}, "bug_hunter"),
        ({"command": "commit", "commit_message": "refactor: extract helper"}, "refactor_artist"),
        ({"command": "commit", "deletions": 120}, "cleanup_crew"),
        ({"command": "commit", "changes": 220}, "big_wave"),
    ],
)
def test_special_achievement_unlocks(user_data_factory, translator, context, achievement_id):
    """Context-driven achievements should unlock for their matching event payloads."""
    data = user_data_factory()

    gained_xp = check_all_achievements(data, translator, context=context)

    assert achievement_id in data["achievements_unlocked"]
    assert gained_xp >= ACHIEVEMENTS_DEF[achievement_id]["xp_reward"]


def test_daily_commit_achievements(user_data_factory, translator):
    """Daily commit milestones should unlock based on same-day commit count."""
    data = user_data_factory()
    data["stats"]["daily_commit_count"] = 6

    gained_xp = check_all_achievements(data, translator, context={"command": "commit"})

    assert "daily_commit_3" in data["achievements_unlocked"]
    assert "daily_commit_6" in data["achievements_unlocked"]
    assert gained_xp >= (
        ACHIEVEMENTS_DEF["daily_commit_3"]["xp_reward"]
        + ACHIEVEMENTS_DEF["daily_commit_6"]["xp_reward"]
    )


def test_balanced_day_unlocks_on_push(user_data_factory, translator):
    """Balanced-day achievement should unlock when commit and push happen today."""
    data = user_data_factory()
    today = date.today().isoformat()
    data["stats"]["last_commit_date"] = today
    data["stats"]["last_push_date"] = today

    gained_xp = check_all_achievements(data, translator, context={"command": "push"})

    assert "balanced_day" in data["achievements_unlocked"]
    assert gained_xp >= ACHIEVEMENTS_DEF["balanced_day"]["xp_reward"]


def test_already_unlocked_achievement_grants_no_xp(user_data_factory, translator):
    """Unlocked achievements must not re-award XP on later checks."""
    data = user_data_factory()
    data["stats"]["total_commits"] = 5
    data["achievements_unlocked"]["first_commit"] = "2025-01-01"

    gained_xp = check_all_achievements(data, translator, context={"command": "commit"})

    assert gained_xp == 0
