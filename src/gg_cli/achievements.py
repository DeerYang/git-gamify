# src/gg_cli/achievements.py
"""Achievement checking and unlock handling."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable

from rich.panel import Panel

from gg_cli.definitions_loader import load_achievements_flat
from gg_cli.translator import Translator
from gg_cli.utils import console

ACHIEVEMENTS_DEF = load_achievements_flat()


def _check_simple_stat(
    user_data: dict[str, Any], stat_key: str, target_value: int, ach_id: str
) -> dict[str, str] | None:
    if user_data["stats"].get(stat_key, 0) >= target_value:
        return {"id": ach_id}
    return None


def _check_midnight_coder(
    user_data: dict[str, Any], context: dict[str, Any], **kwargs: Any
) -> dict[str, str] | None:
    if context.get("command") != "commit":
        return None
    now = datetime.now()
    if 0 <= now.hour < 4:
        return {"id": "midnight_coder"}
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
    commit_message = context.get("commit_message", "")
    if len(commit_message.split()) >= 50:
        return {"id": "storyteller"}
    return None


Checker = Callable[..., dict[str, str] | None]

ACHIEVEMENT_CHECKERS: dict[str, Checker] = {
    "first_commit": lambda u, **kwargs: _check_simple_stat(
        u, "total_commits", 1, "first_commit"
    ),
    "commit_10": lambda u, **kwargs: _check_simple_stat(u, "total_commits", 10, "commit_10"),
    "commit_100": lambda u, **kwargs: _check_simple_stat(u, "total_commits", 100, "commit_100"),
    "commit_1000": lambda u, **kwargs: _check_simple_stat(
        u, "total_commits", 1000, "commit_1000"
    ),
    "commit_5000": lambda u, **kwargs: _check_simple_stat(
        u, "total_commits", 5000, "commit_5000"
    ),
    "commit_10000": lambda u, **kwargs: _check_simple_stat(
        u, "total_commits", 10000, "commit_10000"
    ),
    "first_push": lambda u, **kwargs: _check_simple_stat(u, "total_pushes", 1, "first_push"),
    "push_10": lambda u, **kwargs: _check_simple_stat(u, "total_pushes", 10, "push_10"),
    "push_50": lambda u, **kwargs: _check_simple_stat(u, "total_pushes", 50, "push_50"),
    "push_100": lambda u, **kwargs: _check_simple_stat(u, "total_pushes", 100, "push_100"),
    "push_500": lambda u, **kwargs: _check_simple_stat(u, "total_pushes", 500, "push_500"),
    "push_1000": lambda u, **kwargs: _check_simple_stat(u, "total_pushes", 1000, "push_1000"),
    "combo_3": lambda u, **kwargs: _check_simple_stat(
        u, "consecutive_commit_days", 3, "combo_3"
    ),
    "combo_7": lambda u, **kwargs: _check_simple_stat(
        u, "consecutive_commit_days", 7, "combo_7"
    ),
    "combo_30": lambda u, **kwargs: _check_simple_stat(
        u, "consecutive_commit_days", 30, "combo_30"
    ),
    "combo_90": lambda u, **kwargs: _check_simple_stat(
        u, "consecutive_commit_days", 90, "combo_90"
    ),
    "combo_180": lambda u, **kwargs: _check_simple_stat(
        u, "consecutive_commit_days", 180, "combo_180"
    ),
    "combo_365": lambda u, **kwargs: _check_simple_stat(
        u, "consecutive_commit_days", 365, "combo_365"
    ),
    "midnight_coder": _check_midnight_coder,
    "firefighter": _check_firefighter,
    "storyteller": _check_storyteller,
}


def check_all_achievements(
    user_data: dict[str, Any], translator: Translator, context: dict[str, Any]
) -> int:
    """Check and unlock achievements; return total gained XP."""
    xp_from_achievements = 0

    for ach_id, checker_func in ACHIEVEMENT_CHECKERS.items():
        if ach_id in user_data["achievements_unlocked"]:
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
