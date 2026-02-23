# src/gg_cli/gamify.py
"""Gamification engine: event processing, XP rules, levels, and rewards."""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from rich.panel import Panel

from gg_cli.achievements import check_all_achievements
from gg_cli.core import load_user_data, save_user_data
from gg_cli.definitions_loader import (
    DefinitionsValidationError,
    load_rewards,
    validate_definitions,
)
from gg_cli.git_service import GitService
from gg_cli.translator import Translator
from gg_cli.utils import console

# Each tuple: (level_cap, xp_per_level_in_tier, title_translation_key)
LEVEL_TIERS = [
    (10, 100, "level_title_novice"),
    (20, 250, "level_title_apprentice"),
    (30, 500, "level_title_journeyman"),
    (40, 1000, "level_title_adept"),
    (50, 2500, "level_title_master"),
    (60, 5000, "level_title_expert"),
    (70, 7500, "level_title_genius"),
    (80, 10000, "level_title_legendary"),
    (90, 15000, "level_title_marvelous"),
    (100, 25000, "level_title_champion"),
]

DEFAULT_XP_RULES = {
    "commit_base": 10,
    "commit_combo_cap": 15,
    "commit_change_bonus_divisor": 20,
    "commit_change_bonus_cap": 20,
    "push_base": 25,
    "push_daily_bonus": 50,
}

_REWARDS_DEF = load_rewards()
_DEFINITIONS_VALIDATED = False


@dataclass
class GamifyEvent:
    """Normalized command event used by gamification processors."""

    command: str
    args: list[str]
    today: date = field(default_factory=date.today)
    context: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.context.setdefault("command", self.command)


def ensure_runtime_definitions_valid() -> None:
    """Run definitions integrity checks once per process."""
    global _DEFINITIONS_VALIDATED
    if _DEFINITIONS_VALIDATED:
        return
    validate_definitions()
    _DEFINITIONS_VALIDATED = True


def get_level_info(level: int) -> tuple[int, int, str]:
    """Retrieve tier information for a given level."""
    if not isinstance(level, int) or level < 1:
        level = 1
    for max_level, xp_per_level, title_key in LEVEL_TIERS:
        if level <= max_level:
            return max_level, xp_per_level, title_key
    return LEVEL_TIERS[-1]


def get_total_xp_for_level(target_level: int) -> int:
    """Calculate cumulative XP required to reach the beginning of target level."""
    total_xp = 0
    current_level = 1
    while current_level < target_level:
        _, xp_per_level, _ = get_level_info(current_level)
        total_xp += xp_per_level
        current_level += 1
    return total_xp


def get_level_from_xp(xp: int) -> int:
    """Calculate user level from total XP."""
    if not isinstance(xp, int) or xp < 0:
        xp = 0
    level = 1
    xp_needed_for_next_level = 0
    while True:
        _, xp_per_level, _ = get_level_info(level)
        xp_needed_for_next_level += xp_per_level
        if xp < xp_needed_for_next_level:
            return level
        level += 1


def _process_commit_event(
    user_data: dict[str, Any],
    event: GamifyEvent,
    git_service: GitService,
    xp_rules: dict[str, int],
) -> int:
    stats = user_data["stats"]
    stats["total_commits"] += 1
    last_commit_date_str = stats.get("last_commit_date", "1970-01-01")

    if last_commit_date_str != "1970-01-01":
        last_commit_date = date.fromisoformat(last_commit_date_str)
        day_delta = (event.today - last_commit_date).days
        if day_delta == 1:
            stats["consecutive_commit_days"] += 1
        elif day_delta > 1:
            stats["consecutive_commit_days"] = 1
    else:
        stats["consecutive_commit_days"] = 1

    if last_commit_date_str != event.today.isoformat():
        stats["last_commit_date"] = event.today.isoformat()

    xp_to_add = xp_rules["commit_base"]
    xp_to_add += min(stats["consecutive_commit_days"], xp_rules["commit_combo_cap"])

    try:
        diff_stats = git_service.get_shortstat_last_commit()
        changes = sum(int(token) for token in diff_stats.split() if token.isdigit())
        change_xp = int(changes / xp_rules["commit_change_bonus_divisor"])
        xp_to_add += min(change_xp, xp_rules["commit_change_bonus_cap"])

        deletions_match = re.search(r"(\d+)\s+deletions", diff_stats)
        event.context["deletions"] = int(deletions_match.group(1)) if deletions_match else 0
        event.context["commit_message"] = git_service.get_last_commit_message()
    except Exception:
        # First commit or detached states can fail diff retrieval; keep flow resilient.
        pass

    return xp_to_add


def _process_push_event(
    user_data: dict[str, Any], event: GamifyEvent, xp_rules: dict[str, int]
) -> int:
    stats = user_data["stats"]
    stats["total_pushes"] += 1
    last_push_date = date.fromisoformat(stats["last_push_date"])

    xp_to_add = xp_rules["push_base"]
    if event.today != last_push_date:
        xp_to_add += xp_rules["push_daily_bonus"]
        stats["last_push_date"] = event.today.isoformat()

    return xp_to_add


def _apply_level_progression(
    user_data: dict[str, Any],
    translator: Translator,
    xp_to_add: int,
    reward_rng: random.Random | None = None,
) -> None:
    if xp_to_add <= 0:
        return

    current_level = user_data.get("user", {}).get("level", 1)
    current_xp = user_data.get("user", {}).get("xp", 0)

    new_xp = current_xp + xp_to_add
    new_level = get_level_from_xp(new_xp)
    user_data["user"] = {"xp": new_xp, "level": new_level}

    _, xp_per_level_current, _ = get_level_info(new_level)
    xp_base_for_current_level = get_total_xp_for_level(new_level)
    next_level_xp_target = xp_base_for_current_level + xp_per_level_current

    console.print(
        translator.t(
            "xp_gain_message",
            xp=xp_to_add,
            level=new_level,
            current_xp=new_xp,
            next_level_xp=next_level_xp_target,
        )
    )

    if new_level <= current_level:
        return

    _, _, title_key = get_level_info(new_level)
    console.print(
        translator.t("level_up_message", level=new_level, title=translator.t(title_key)),
        style="bold magenta",
    )

    language = user_data.get("config", {}).get("language", "en")
    rng = reward_rng or random
    reward_type = rng.choice(["quotes", "jokes"])
    reward = rng.choice(_REWARDS_DEF[reward_type][language])
    console.print(
        Panel(
            f"[italic cyan]{reward}[/italic cyan]",
            title=translator.t("random_reward_title"),
            border_style="green",
            expand=False,
        )
    )


def process_event(
    user_data: dict[str, Any],
    event: GamifyEvent,
    translator: Translator,
    git_service: GitService | None = None,
    xp_rules: dict[str, int] | None = None,
) -> int:
    """Process a normalized Git event and return total awarded XP."""
    rules = xp_rules or DEFAULT_XP_RULES
    git = git_service or GitService()

    xp_to_add = 0
    if event.command == "commit":
        xp_to_add += _process_commit_event(user_data, event, git, rules)
    elif event.command == "push":
        xp_to_add += _process_push_event(user_data, event, rules)

    xp_to_add += check_all_achievements(user_data, translator, event.context)
    _apply_level_progression(user_data, translator, xp_to_add)
    return xp_to_add


def process_gamify_logic(
    git_command_args: list[str], git_service: GitService | None = None
) -> None:
    """
    Entry point called after successful git command.

    Loads user state, processes one event, and persists updated profile.
    """
    try:
        ensure_runtime_definitions_valid()
    except DefinitionsValidationError as exc:
        console.print(f"[bold red]Definitions error:[/bold red] {exc}")
        return

    user_data = load_user_data()
    if not user_data or not user_data.get("config", {}).get("user_email"):
        return

    command = git_command_args[0] if git_command_args else ""
    event = GamifyEvent(command=command, args=git_command_args)
    translator = Translator(user_data.get("config", {}).get("language", "en"))
    process_event(user_data, event, translator, git_service=git_service)
    save_user_data(user_data)
