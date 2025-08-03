# src/gg_cli/gamify.py
"""The core gamification engine. Calculates XP, manages levels, and processes game logic after Git commands."""

import json
import random
import subprocess
import re
from datetime import date
from gg_cli.core import load_user_data, save_user_data
from gg_cli.translator import Translator
from gg_cli.utils import console, DEFINITIONS_DIR
from gg_cli.achievements import check_all_achievements
from rich.panel import Panel

# Defines the level progression system.
# Each tuple represents: (level_cap, xp_per_level_in_tier, title_translation_key)
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


def get_level_info(level: int) -> tuple[int, int, str]:
    """Retrieves tier information for a given level."""
    if not isinstance(level, int) or level < 1:
        level = 1
    for max_level, xp_per_level, title_key in LEVEL_TIERS:
        if level <= max_level:
            return max_level, xp_per_level, title_key
    # Default to the last tier for levels beyond the defined caps.
    return LEVEL_TIERS[-1]


def get_total_xp_for_level(target_level: int) -> int:
    """Calculates the total XP required to reach the beginning of a target level."""
    total_xp = 0
    current_level = 1
    while current_level < target_level:
        _, xp_per_level, _ = get_level_info(current_level)
        total_xp += xp_per_level
        current_level += 1
    return total_xp


def get_level_from_xp(xp: int) -> int:
    """Calculates a user's level based on their total XP."""
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


def load_rewards() -> dict:
    """Loads random rewards (quotes, jokes) from the JSON definition file."""
    with open(DEFINITIONS_DIR / 'rewards.json', 'r', encoding='utf-8') as f:
        return json.load(f)


rewards_def = load_rewards()


def process_gamify_logic(git_command_args: list[str]) -> None:
    """
    The main entry point for all gamification logic.

    This function is called after a successful git command and handles
    XP calculation, stats updates, and achievement checks.
    """
    user_data = load_user_data()
    if not user_data or not user_data.get("config", {}).get("user_email"):
        return

    translator = Translator(user_data.get("config", {}).get("language", "en"))
    command = git_command_args[0] if git_command_args else ""
    today = date.today()
    xp_to_add = 0
    context = {"command": command}

    if command == "commit":
        # Update commit stats
        user_data["stats"]["total_commits"] += 1
        last_commit_date_str = user_data["stats"].get("last_commit_date", "1970-01-01")

        if last_commit_date_str != "1970-01-01":
            last_commit_date = date.fromisoformat(last_commit_date_str)
            if (today - last_commit_date).days == 1:
                user_data["stats"]["consecutive_commit_days"] += 1
            elif (today - last_commit_date).days > 1:
                user_data["stats"]["consecutive_commit_days"] = 1
        else:  # First commit ever for this user.
            user_data["stats"]["consecutive_commit_days"] = 1

        if last_commit_date_str != today.isoformat():
            user_data["stats"]["last_commit_date"] = today.isoformat()

        # Calculate XP for the commit
        xp_to_add += 10  # Base XP
        xp_to_add += min(user_data["stats"]["consecutive_commit_days"], 15)  # Combo bonus

        # Bonus XP based on code volume
        try:
            diff_stats = subprocess.check_output(
                ["git", "diff", "--shortstat", "HEAD~1", "HEAD"],
                text=True, stderr=subprocess.DEVNULL
            ).strip()
            changes = sum(int(s) for s in diff_stats.split() if s.isdigit())
            xp_to_add += min(int(changes / 20), 20)

            # Gather context for achievements
            deletions_match = re.search(r'(\d+)\s+deletions', diff_stats)
            context["deletions"] = int(deletions_match.group(1)) if deletions_match else 0
            context["commit_message"] = subprocess.check_output(["git", "log", "-1", "--pretty=%B"], text=True).strip()
        except Exception:
            # Ignore errors if not in a state to diff (e.g., first commit).
            pass

    elif command == "push":
        # Update push stats
        user_data["stats"]["total_pushes"] += 1
        last_push_date = date.fromisoformat(user_data["stats"]["last_push_date"])

        # Calculate XP for the push
        xp_to_add += 25  # Base XP
        if today != last_push_date:
            xp_to_add += 50  # Daily bonus
            user_data["stats"]["last_push_date"] = today.isoformat()

    # Check for any newly unlocked achievements and add their XP.
    xp_from_achievements = check_all_achievements(user_data, translator, context)
    xp_to_add += xp_from_achievements

    if xp_to_add > 0:
        current_level = user_data.get("user", {}).get("level", 1)
        current_xp = user_data.get("user", {}).get("xp", 0)

        new_xp = current_xp + xp_to_add
        new_level = get_level_from_xp(new_xp)
        user_data["user"] = {"xp": new_xp, "level": new_level}

        # Display XP gain message
        _, xp_per_level_current, _ = get_level_info(new_level)
        xp_base_for_current_level = get_total_xp_for_level(new_level)
        next_level_xp_target = xp_base_for_current_level + xp_per_level_current
        console.print(translator.t(
            "xp_gain_message",
            xp=xp_to_add,
            level=new_level,
            current_xp=new_xp,
            next_level_xp=next_level_xp_target
        ))

        # Handle level up event
        if new_level > current_level:
            _, _, title_key = get_level_info(new_level)
            console.print(
                translator.t("level_up_message", level=new_level, title=translator.t(title_key)),
                style="bold magenta"
            )
            # Give a random reward
            lang = user_data.get("config", {}).get("language", "en")
            reward_type = random.choice(["quotes", "jokes"])
            reward = random.choice(rewards_def[reward_type][lang])
            console.print(Panel(
                f"[italic cyan]{reward}[/italic cyan]",
                title=translator.t("random_reward_title"),
                border_style="green", expand=False
            ))

    save_user_data(user_data)
