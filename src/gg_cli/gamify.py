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
    (10, 220, "level_title_novice"),
    (20, 320, "level_title_apprentice"),
    (30, 460, "level_title_journeyman"),
    (40, 650, "level_title_adept"),
    (50, 900, "level_title_master"),
    (60, 1200, "level_title_expert"),
    (70, 1600, "level_title_genius"),
    (80, 2100, "level_title_legendary"),
    (90, 2700, "level_title_marvelous"),
    (100, 3500, "level_title_champion"),
]

DEFAULT_XP_RULES = {
    "commit_base": 8,
    "commit_full_reward_count": 6,
    "commit_half_reward_count": 12,
    "commit_change_tier1": 20,
    "commit_change_tier2": 80,
    "commit_change_tier3": 200,
    "commit_change_bonus_tier1": 2,
    "commit_change_bonus_tier2": 4,
    "commit_change_bonus_tier3": 6,
    "push_base": 4,
    "push_first_of_day_bonus": 8,
    "push_daily_xp_cap": 12,
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
    _reset_daily_trackers_if_needed(stats, event.today)
    stats["total_commits"] += 1
    last_commit_date_str = stats.get("last_commit_date", "1970-01-01")
    is_new_commit_day = last_commit_date_str != event.today.isoformat()

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

    stats["daily_commit_count"] += 1
    commit_count_today = stats["daily_commit_count"]
    reward_multiplier = _get_commit_reward_multiplier(commit_count_today, xp_rules)
    xp_to_add = 0

    try:
        diff_stats = git_service.get_shortstat_last_commit()
        changes = sum(int(token) for token in diff_stats.split() if token.isdigit())
        event.context["changes"] = changes
        change_xp = _get_change_bonus(changes, xp_rules)

        deletions_match = re.search(r"(\d+)\s+deletions", diff_stats)
        event.context["deletions"] = int(deletions_match.group(1)) if deletions_match else 0
        event.context["commit_message"] = git_service.get_last_commit_message()
    except Exception:
        # First commit or detached states can fail diff retrieval; keep flow resilient.
        change_xp = 0

    streak_bonus = _get_streak_bonus(stats["consecutive_commit_days"]) if is_new_commit_day else 0
    raw_xp = xp_rules["commit_base"] + change_xp + streak_bonus
    xp_to_add += int(raw_xp * reward_multiplier)

    return xp_to_add


def _process_push_event(
    user_data: dict[str, Any], event: GamifyEvent, xp_rules: dict[str, int]
) -> int:
    stats = user_data["stats"]
    _reset_daily_trackers_if_needed(stats, event.today)
    stats["total_pushes"] += 1
    is_first_push_today = stats["last_push_date"] != event.today.isoformat()

    raw_xp = xp_rules["push_base"]
    if is_first_push_today:
        raw_xp += xp_rules["push_first_of_day_bonus"]
        stats["last_push_date"] = event.today.isoformat()

    remaining_xp_quota = max(0, xp_rules["push_daily_xp_cap"] - stats["daily_push_xp_earned"])
    earned_xp = min(raw_xp, remaining_xp_quota)
    stats["daily_push_xp_earned"] += earned_xp
    return earned_xp


def _reset_daily_trackers_if_needed(stats: dict[str, Any], today: date) -> None:
    today_str = today.isoformat()
    if stats.get("daily_xp_date") == today_str:
        return
    stats["daily_xp_date"] = today_str
    stats["daily_commit_count"] = 0
    stats["daily_push_xp_earned"] = 0


def _get_commit_reward_multiplier(commit_count_today: int, xp_rules: dict[str, int]) -> float:
    if commit_count_today <= xp_rules["commit_full_reward_count"]:
        return 1.0
    if commit_count_today <= xp_rules["commit_half_reward_count"]:
        return 0.5
    return 0.0


def _get_streak_bonus(consecutive_days: int) -> int:
    if consecutive_days >= 31:
        return 5
    if consecutive_days >= 15:
        return 4
    if consecutive_days >= 8:
        return 3
    if consecutive_days >= 4:
        return 2
    return 1


def _get_change_bonus(changes: int, xp_rules: dict[str, int]) -> int:
    if changes >= xp_rules["commit_change_tier3"]:
        return xp_rules["commit_change_bonus_tier3"]
    if changes >= xp_rules["commit_change_tier2"]:
        return xp_rules["commit_change_bonus_tier2"]
    if changes >= xp_rules["commit_change_tier1"]:
        return xp_rules["commit_change_bonus_tier1"]
    return 0


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
    reward_pools = ["tips", "quotes", "jokes", "challenges"]
    available_reward_pools = [
        pool
        for pool in reward_pools
        if pool in _REWARDS_DEF and language in _REWARDS_DEF[pool] and _REWARDS_DEF[pool][language]
    ]
    if not available_reward_pools:
        available_reward_pools = ["quotes"]
    reward_type = rng.choice(available_reward_pools)
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
