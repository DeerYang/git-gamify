"""Tests for event-based gamification processing."""

from datetime import date

from gg_cli.gamify import (
    GamifyEvent,
    process_event,
    process_gamify_logic,
)
from gg_cli.definitions_loader import DefinitionsValidationError


class StubTranslator:
    def t(self, key, **kwargs):
        return key.format(**kwargs) if kwargs else key


class StubGitService:
    def get_shortstat_last_commit(self):
        return " 2 files changed, 100 insertions(+), 40 deletions(-)"

    def get_last_commit_message(self):
        return "Add feature and tests"


def make_user_data():
    return {
        "config": {"language": "en", "user_email": "test@example.com"},
        "user": {"xp": 0, "level": 1},
        "achievements_unlocked": {},
        "stats": {
            "total_commits": 0,
            "total_pushes": 0,
            "last_commit_date": "1970-01-01",
            "last_push_date": "1970-01-01",
            "consecutive_commit_days": 0,
        },
    }


def test_process_commit_event_updates_stats_and_context():
    user_data = make_user_data()
    event = GamifyEvent(command="commit", args=["commit", "-m", "x"], today=date(2026, 2, 1))

    gained_xp = process_event(
        user_data,
        event,
        translator=StubTranslator(),
        git_service=StubGitService(),
    )

    assert gained_xp > 0
    assert user_data["stats"]["total_commits"] == 1
    assert user_data["stats"]["consecutive_commit_days"] == 1
    assert event.context["deletions"] == 40
    assert event.context["commit_message"] == "Add feature and tests"


def test_process_push_event_applies_daily_bonus_once():
    user_data = make_user_data()
    translator = StubTranslator()
    today = date(2026, 2, 2)

    first_push = GamifyEvent(command="push", args=["push"], today=today)
    second_push = GamifyEvent(command="push", args=["push"], today=today)

    xp_first = process_event(user_data, first_push, translator=translator)
    xp_second = process_event(user_data, second_push, translator=translator)

    assert xp_first >= 75
    assert xp_second >= 25
    assert xp_first > xp_second


def test_process_gamify_logic_handles_invalid_definitions(monkeypatch):
    monkeypatch.setattr(
        "gg_cli.gamify.ensure_runtime_definitions_valid",
        lambda: (_ for _ in ()).throw(DefinitionsValidationError("bad defs")),
    )
    # Should not bubble exceptions to caller.
    process_gamify_logic(["commit", "-m", "x"])
