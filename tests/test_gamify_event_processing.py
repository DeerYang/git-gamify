"""Tests for event-based gamification processing and orchestration paths."""

from __future__ import annotations

from datetime import date

import pytest

from gg_cli.definitions_loader import DefinitionsValidationError
from gg_cli.gamify import GamifyEvent, process_event, process_gamify_logic


def test_process_commit_event_updates_stats_and_context(user_data_factory, translator, git_service):
    data = user_data_factory()
    event = GamifyEvent(command="commit", args=["commit", "-m", "x"], today=date(2026, 2, 1))

    gained_xp = process_event(data, event, translator=translator, git_service=git_service)

    assert gained_xp > 0
    assert data["stats"]["total_commits"] == 1
    assert data["stats"]["consecutive_commit_days"] == 1
    assert event.context["deletions"] == 40
    assert event.context["commit_message"] == "Add feature and tests"


def test_process_commit_event_streak_increments_and_resets(user_data_factory, translator, git_service):
    data = user_data_factory()
    data["stats"]["last_commit_date"] = "2026-02-01"
    data["stats"]["consecutive_commit_days"] = 2

    next_day = GamifyEvent(command="commit", args=["commit"], today=date(2026, 2, 2))
    process_event(data, next_day, translator=translator, git_service=git_service)
    assert data["stats"]["consecutive_commit_days"] == 3

    after_gap = GamifyEvent(command="commit", args=["commit"], today=date(2026, 2, 10))
    process_event(data, after_gap, translator=translator, git_service=git_service)
    assert data["stats"]["consecutive_commit_days"] == 1


def test_process_push_event_applies_daily_bonus_once(user_data_factory, translator):
    data = user_data_factory()
    today = date(2026, 2, 2)

    first_push = GamifyEvent(command="push", args=["push"], today=today)
    second_push = GamifyEvent(command="push", args=["push"], today=today)

    xp_first = process_event(data, first_push, translator=translator)
    xp_second = process_event(data, second_push, translator=translator)

    assert xp_first >= 75
    assert xp_second >= 25
    assert xp_first > xp_second


def test_process_event_tolerates_commit_diff_failures(user_data_factory, translator, monkeypatch):
    data = user_data_factory()
    event = GamifyEvent(command="commit", args=["commit"], today=date(2026, 2, 2))

    class FailingGitService:
        def get_shortstat_last_commit(self):
            raise RuntimeError("git diff unavailable")

        def get_last_commit_message(self):
            raise RuntimeError("git log unavailable")

    gained_xp = process_event(data, event, translator=translator, git_service=FailingGitService())
    assert gained_xp > 0
    assert "deletions" not in event.context


def test_process_gamify_logic_handles_invalid_definitions(monkeypatch):
    monkeypatch.setattr(
        "gg_cli.gamify.ensure_runtime_definitions_valid",
        lambda: (_ for _ in ()).throw(DefinitionsValidationError("bad defs")),
    )
    process_gamify_logic(["commit", "-m", "x"])


def test_process_gamify_logic_exits_when_user_email_missing(monkeypatch, user_data_factory):
    data = user_data_factory()
    data["config"]["user_email"] = None
    saves = []

    monkeypatch.setattr("gg_cli.gamify.ensure_runtime_definitions_valid", lambda: None)
    monkeypatch.setattr("gg_cli.gamify.load_user_data", lambda: data)
    monkeypatch.setattr("gg_cli.gamify.save_user_data", lambda payload: saves.append(payload))

    process_gamify_logic(["commit", "-m", "x"])
    assert saves == []
