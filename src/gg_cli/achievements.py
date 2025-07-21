# src/gg_cli/achievements.py
"""Handles the logic for checking and unlocking all achievements."""

import json
import re
from datetime import date, datetime
from gg_cli.utils import DEFINITIONS_DIR, console
from gg_cli.translator import Translator
from rich.panel import Panel


def load_achievement_definitions() -> dict:
    """
    Loads achievement definitions from JSON and flattens them into a single dict.

    Returns:
        A dictionary mapping achievement IDs to their definition data.
    """
    with open(DEFINITIONS_DIR / 'achievements.json', 'r', encoding='utf-8') as f:
        defs = json.load(f)
        # Flatten the structure from categories into a single ID-based dictionary.
        return {ach_id: ach_data for category in defs.values() for ach_id, ach_data in category.items()}


ACHIEVEMENTS_DEF = load_achievement_definitions()


# Helper functions for checking specific achievement conditions.
# These are kept internal to this module.

def _check_simple_stat(user_data: dict, stat_key: str, target_value: int, ach_id: str) -> dict | None:
    """Generic checker for achievements based on a simple statistic count."""
    if user_data["stats"].get(stat_key, 0) >= target_value:
        return {"id": ach_id}
    return None


def _check_midnight_coder(user_data: dict, context: dict, **kwargs) -> dict | None:
    """Checker for the 'Midnight Coder' achievement."""
    if context.get("command") != "commit":
        return None
    now = datetime.now()
    if 0 <= now.hour < 4:  # Check if the time is between 00:00 and 04:00
        return {"id": "midnight_coder"}
    return None


def _check_firefighter(user_data: dict, context: dict, **kwargs) -> dict | None:
    """Checker for the 'Firefighter' achievement."""
    if context.get("command") != "commit":
        return None
    deletions = context.get("deletions", 0)
    if deletions >= 500:
        return {"id": "firefighter"}
    return None


def _check_storyteller(user_data: dict, context: dict, **kwargs) -> dict | None:
    """Checker for the 'Storyteller' achievement."""
    if context.get("command") != "commit":
        return None
    commit_message = context.get("commit_message", "")
    if len(commit_message.split()) >= 50:
        return {"id": "storyteller"}
    return None


# Maps achievement IDs to their corresponding checker functions for easy iteration.
ACHIEVEMENT_CHECKERS = {
    "first_commit": lambda u, **kwargs: _check_simple_stat(u, "total_commits", 1, "first_commit"),
    "commit_10":    lambda u, **kwargs: _check_simple_stat(u, "total_commits", 10, "commit_10"),
    "commit_100":   lambda u, **kwargs: _check_simple_stat(u, "total_commits", 100, "commit_100"),
    "commit_1000":  lambda u, **kwargs: _check_simple_stat(u, "total_commits", 1000, "commit_1000"),
    "first_push":   lambda u, **kwargs: _check_simple_stat(u, "total_pushes", 1, "first_push"),
    "push_50":      lambda u, **kwargs: _check_simple_stat(u, "total_pushes", 50, "push_50"),
    "combo_3":      lambda u, **kwargs: _check_simple_stat(u, "consecutive_commit_days", 3, "combo_3"),
    "combo_7":      lambda u, **kwargs: _check_simple_stat(u, "consecutive_commit_days", 7, "combo_7"),
    "combo_30":     lambda u, **kwargs: _check_simple_stat(u, "consecutive_commit_days", 30, "combo_30"),
    "midnight_coder": _check_midnight_coder,
    "firefighter": _check_firefighter,
    "storyteller": _check_storyteller,
}


def check_all_achievements(user_data: dict, translator: Translator, context: dict) -> int:
    """
    Iterates through all defined achievements and checks if they should be unlocked.

    If an achievement is unlocked, it updates user_data, prints a notification,
    and contributes to the total XP gained in this session.

    Args:
        user_data: The user's current data dictionary.
        translator: An instance of the Translator class for notifications.
        context: A dictionary containing contextual info about the command (e.g., command name).

    Returns:
        The total XP awarded from all newly unlocked achievements.
    """
    xp_from_achievements = 0

    for ach_id, checker_func in ACHIEVEMENT_CHECKERS.items():
        if ach_id not in user_data["achievements_unlocked"]:
            result = checker_func(user_data, context=context)
            if result:
                user_data["achievements_unlocked"][ach_id] = date.today().isoformat()

                reward = ACHIEVEMENTS_DEF[ach_id].get("xp_reward", 0)
                xp_from_achievements += reward

                # Display a notification to the user.
                name = translator.t(ACHIEVEMENTS_DEF[ach_id]["name_key"])
                desc = translator.t(ACHIEVEMENTS_DEF[ach_id]["desc_key"])
                panel_title = translator.t("achievement_unlocked_panel_title")
                console.print(Panel(
                    f"[bold cyan]{name}[/bold cyan]\n[italic]{desc}[/italic]\n\n✨ [bold]Gained +{reward} XP![/bold]",
                    title=panel_title, border_style="yellow", expand=False))

    return xp_from_achievements