# src/gg_cli/achievements.py
"""Achievement checking and unlock handling."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Callable

from rich.panel import Panel

from gg_cli.definitions_loader import load_achievements_flat
from gg_cli.translator import Translator
from gg_cli.utils import console

ACHIEVEMENTS_DEF = load_achievements_flat()

COMMIT_THRESHOLDS = {
    "commit_10": 10,
    "commit_20": 20,
    "commit_35": 35,
    "commit_50": 50,
    "commit_75": 75,
    "commit_100": 100,
    "commit_150": 150,
    "commit_200": 200,
    "commit_300": 300,
    "commit_400": 400,
    "commit_600": 600,
    "commit_800": 800,
    "commit_1000": 1000,
    "commit_1500": 1500,
    "commit_2000": 2000,
    "commit_3000": 3000,
    "commit_5000": 5000,
    "commit_8000": 8000,
    "commit_10000": 10000,
    "commit_12000": 12000,
    "commit_15000": 15000,
}

PUSH_THRESHOLDS = {
    "push_10": 10,
    "push_20": 20,
    "push_35": 35,
    "push_50": 50,
    "push_75": 75,
    "push_100": 100,
    "push_150": 150,
    "push_200": 200,
    "push_300": 300,
    "push_400": 400,
    "push_600": 600,
    "push_800": 800,
    "push_1000": 1000,
    "push_1500": 1500,
    "push_2000": 2000,
    "push_3000": 3000,
    "push_5000": 5000,
    "push_8000": 8000,
}

STREAK_THRESHOLDS = {
    "combo_3": 3,
    "combo_5": 5,
    "combo_7": 7,
    "combo_10": 10,
    "combo_14": 14,
    "combo_21": 21,
    "combo_30": 30,
    "combo_45": 45,
    "combo_60": 60,
    "combo_90": 90,
    "combo_120": 120,
    "combo_180": 180,
    "combo_240": 240,
    "combo_365": 365,
    "combo_500": 500,
    "combo_730": 730,
    "combo_1000": 1000,
}

DAILY_COMMIT_THRESHOLDS = {
    "daily_commit_3": 3,
    "daily_commit_4": 4,
    "daily_commit_6": 6,
    "daily_commit_8": 8,
    "daily_commit_10": 10,
    "daily_commit_12": 12,
}

KEYWORD_PATTERNS = {
    "bug_hunter": r"\b(fix|bug|hotfix)\b",
    "refactor_artist": r"\brefactor\b",
    "docs_keeper": r"\bdocs?\b",
    "test_guardian": r"\btests?\b",
    "chore_keeper": r"\bchore\b",
    "perf_tuner": r"\bperf(ormance)?\b",
    "security_guard": r"\bsecurity\b",
    "release_captain": r"\brelease\b",
}


def _check_simple_stat(
    user_data: dict[str, Any], stat_key: str, target_value: int, ach_id: str
) -> dict[str, str] | None:
    if user_data["stats"].get(stat_key, 0) >= target_value:
        return {"id": ach_id}
    return None


def _check_keyword_commit(
    user_data: dict[str, Any], context: dict[str, Any], pattern: str, ach_id: str
) -> dict[str, str] | None:
    if context.get("command") != "commit":
        return None
    message = context.get("commit_message", "")
    if re.search(pattern, message, flags=re.IGNORECASE):
        return {"id": ach_id}
    return None


def _check_daily_commit_target(
    user_data: dict[str, Any], context: dict[str, Any], target: int, ach_id: str
) -> dict[str, str] | None:
    if context.get("command") != "commit":
        return None
    if user_data["stats"].get("daily_commit_count", 0) >= target:
        return {"id": ach_id}
    return None


def _check_midnight_coder(
    user_data: dict[str, Any], context: dict[str, Any], **kwargs: Any
) -> dict[str, str] | None:
    if context.get("command") != "commit":
        return None
    hour = datetime.now().hour
    if 0 <= hour < 4:
        return {"id": "midnight_coder"}
    return None


def _check_dawn_coder(
    user_data: dict[str, Any], context: dict[str, Any], **kwargs: Any
) -> dict[str, str] | None:
    if context.get("command") != "commit":
        return None
    hour = datetime.now().hour
    if 4 <= hour < 8:
        return {"id": "dawn_coder"}
    return None


def _check_weekend_warrior(
    user_data: dict[str, Any], context: dict[str, Any], **kwargs: Any
) -> dict[str, str] | None:
    if context.get("command") != "commit":
        return None
    if date.today().weekday() >= 5:
        return {"id": "weekend_warrior"}
    return None


def _check_friday_ship(
    user_data: dict[str, Any], context: dict[str, Any], **kwargs: Any
) -> dict[str, str] | None:
    if context.get("command") != "push":
        return None
    if date.today().weekday() == 4:
        return {"id": "friday_ship"}
    return None


def _check_firefighter(
    user_data: dict[str, Any], context: dict[str, Any], **kwargs: Any
) -> dict[str, str] | None:
    if context.get("command") != "commit":
        return None
    if context.get("deletions", 0) >= 500:
        return {"id": "firefighter"}
    return None


def _check_storyteller(
    user_data: dict[str, Any], context: dict[str, Any], **kwargs: Any
) -> dict[str, str] | None:
    if context.get("command") != "commit":
        return None
    if len(context.get("commit_message", "").split()) >= 50:
        return {"id": "storyteller"}
    return None


def _check_message_master(
    user_data: dict[str, Any], context: dict[str, Any], **kwargs: Any
) -> dict[str, str] | None:
    if context.get("command") != "commit":
        return None
    if len(context.get("commit_message", "").split()) >= 100:
        return {"id": "message_master"}
    return None


def _check_cleanup_crew(
    user_data: dict[str, Any], context: dict[str, Any], **kwargs: Any
) -> dict[str, str] | None:
    if context.get("command") != "commit":
        return None
    if context.get("deletions", 0) >= 100:
        return {"id": "cleanup_crew"}
    return None


def _check_big_wave(
    user_data: dict[str, Any], context: dict[str, Any], **kwargs: Any
) -> dict[str, str] | None:
    if context.get("command") != "commit":
        return None
    if context.get("changes", 0) >= 200:
        return {"id": "big_wave"}
    return None


def _check_tsunami(
    user_data: dict[str, Any], context: dict[str, Any], **kwargs: Any
) -> dict[str, str] | None:
    if context.get("command") != "commit":
        return None
    if context.get("changes", 0) >= 500:
        return {"id": "tsunami"}
    return None


def _check_tiny_commit(
    user_data: dict[str, Any], context: dict[str, Any], **kwargs: Any
) -> dict[str, str] | None:
    if context.get("command") != "commit":
        return None
    changes = context.get("changes", 0)
    if 0 < changes <= 10:
        return {"id": "tiny_commit"}
    return None


def _check_balanced_day(
    user_data: dict[str, Any], context: dict[str, Any], **kwargs: Any
) -> dict[str, str] | None:
    if context.get("command") != "push":
        return None
    today_str = date.today().isoformat()
    stats = user_data.get("stats", {})
    if stats.get("last_commit_date") == today_str and stats.get("last_push_date") == today_str:
        return {"id": "balanced_day"}
    return None


Checker = Callable[..., dict[str, str] | None]


def _build_simple_stat_checkers(
    stat_key: str, thresholds: dict[str, int]
) -> dict[str, Checker]:
    result: dict[str, Checker] = {}
    for ach_id, target in thresholds.items():
        result[ach_id] = (
            lambda u, _target=target, _id=ach_id, **kwargs: _check_simple_stat(
                u, stat_key, _target, _id
            )
        )
    return result


ACHIEVEMENT_CHECKERS: dict[str, Checker] = {
    "first_commit": lambda u, **kwargs: _check_simple_stat(u, "total_commits", 1, "first_commit"),
    "first_push": lambda u, **kwargs: _check_simple_stat(u, "total_pushes", 1, "first_push"),
    **_build_simple_stat_checkers("total_commits", COMMIT_THRESHOLDS),
    **_build_simple_stat_checkers("total_pushes", PUSH_THRESHOLDS),
    **_build_simple_stat_checkers("consecutive_commit_days", STREAK_THRESHOLDS),
    **{
        ach_id: (
            lambda u, _target=target, _id=ach_id, **kwargs: _check_daily_commit_target(
                u, kwargs["context"], _target, _id
            )
        )
        for ach_id, target in DAILY_COMMIT_THRESHOLDS.items()
    },
    **{
        ach_id: (
            lambda u, _pattern=pattern, _id=ach_id, **kwargs: _check_keyword_commit(
                u, kwargs["context"], _pattern, _id
            )
        )
        for ach_id, pattern in KEYWORD_PATTERNS.items()
    },
    "midnight_coder": _check_midnight_coder,
    "dawn_coder": _check_dawn_coder,
    "weekend_warrior": _check_weekend_warrior,
    "friday_ship": _check_friday_ship,
    "firefighter": _check_firefighter,
    "storyteller": _check_storyteller,
    "message_master": _check_message_master,
    "cleanup_crew": _check_cleanup_crew,
    "big_wave": _check_big_wave,
    "tsunami": _check_tsunami,
    "tiny_commit": _check_tiny_commit,
    "balanced_day": _check_balanced_day,
}


def check_all_achievements(
    user_data: dict[str, Any], translator: Translator, context: dict[str, Any]
) -> int:
    """Check and unlock achievements; return total gained XP."""
    xp_from_achievements = 0

    for ach_id, checker_func in ACHIEVEMENT_CHECKERS.items():
        if ach_id in user_data["achievements_unlocked"]:
            continue
        if ach_id not in ACHIEVEMENTS_DEF:
            continue

        result = checker_func(user_data, context=context)
        if not result:
            continue

        user_data["achievements_unlocked"][ach_id] = date.today().isoformat()
        reward = int(ACHIEVEMENTS_DEF[ach_id].get("xp_reward", 0))
        xp_from_achievements += reward

        name = translator.t(ACHIEVEMENTS_DEF[ach_id]["name_key"])
        desc = translator.t(ACHIEVEMENTS_DEF[ach_id]["desc_key"])
        panel_title = translator.t("achievement_unlocked_panel_title")
        console.print(
            Panel(
                f"[bold cyan]{name}[/bold cyan]\n[italic]{desc}[/italic]\n\n[bold]Gained +{reward} XP![/bold]",
                title=panel_title,
                border_style="yellow",
                expand=False,
            )
        )

    return xp_from_achievements
