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

# --- 1. 定义数值系统核心 ---
LEVEL_TIERS = [
    (10, 100, "level_title_novice"), (20, 250, "level_title_apprentice"),
    (30, 500, "level_title_journeyman"), (40, 1000, "level_title_adept"),
    (50, 2500, "level_title_master"),
]


def get_level_info(level):
    if not isinstance(level, int) or level < 1: level = 1
    for max_level, xp_per_level, title_key in LEVEL_TIERS:
        if level <= max_level: return max_level, xp_per_level, title_key
    return LEVEL_TIERS[-1]


def get_total_xp_for_level(target_level):
    total_xp = 0
    current_level = 1
    while current_level < target_level:
        _, xp_per_level, _ = get_level_info(current_level)
        total_xp += xp_per_level
        current_level += 1
    return total_xp


def get_level_from_xp(xp):
    if not isinstance(xp, int) or xp < 0: xp = 0
    level = 1
    xp_needed = 0
    while True:
        _, xp_per_level, _ = get_level_info(level)
        if xp < xp_needed + xp_per_level: return level
        xp_needed += xp_per_level
        level += 1


# --- 2. 加载奖励文件 ---
def load_rewards():
    with open(DEFINITIONS_DIR / 'rewards.json', 'r', encoding='utf-8') as f:
        return json.load(f)


rewards_def = load_rewards()


# --- 3. 核心游戏化逻辑 ---
def process_gamify_logic(git_command_args):
    user_data = load_user_data()
    if not user_data or not user_data.get("config", {}).get("user_email"): return

    translator = Translator(user_data.get("config", {}).get("language", "en"))
    command = git_command_args[0] if git_command_args else ""
    today = date.today()
    xp_to_add = 0
    context = {"command": command}

    if command == "commit":
        user_data["stats"]["total_commits"] += 1
        last_commit_date_str = user_data["stats"]["last_commit_date"]

        if last_commit_date_str != "1970-01-01":
            last_commit_date = date.fromisoformat(last_commit_date_str)
            if (today - last_commit_date).days == 1:
                user_data["stats"]["consecutive_commit_days"] += 1
            elif (today - last_commit_date).days > 1:
                user_data["stats"]["consecutive_commit_days"] = 1
        else:  # First commit ever
            user_data["stats"]["consecutive_commit_days"] = 1

        if last_commit_date_str != today.isoformat():
            user_data["stats"]["last_commit_date"] = today.isoformat()

        xp_to_add += 10  # Base XP for commit
        xp_to_add += min(user_data["stats"]["consecutive_commit_days"], 15)  # Combo XP

        try:
            diff_stats = subprocess.check_output(["git", "diff", "--shortstat", "HEAD~1", "HEAD"], text=True,
                                                 stderr=subprocess.DEVNULL).strip()
            changes = sum(int(s) for s in diff_stats.split() if s.isdigit())
            xp_to_add += min(int(changes / 20), 20)

            # For Firefighter achievement
            deletions_match = re.search(r'(\d+)\s+deletions', diff_stats)
            context["deletions"] = int(deletions_match.group(1)) if deletions_match else 0

            # For Storyteller achievement
            context["commit_message"] = subprocess.check_output(["git", "log", "-1", "--pretty=%B"], text=True).strip()
        except Exception:
            pass  # Ignore errors if not in a state to diff

    elif command == "push":
        user_data["stats"]["total_pushes"] += 1
        last_push_date = date.fromisoformat(user_data["stats"]["last_push_date"])
        xp_to_add += 25  # Base XP for push
        if today != last_push_date:
            xp_to_add += 50  # Daily bonus
            user_data["stats"]["last_push_date"] = today.isoformat()

    # --- 调用成就系统 ---
    xp_from_achievements = check_all_achievements(user_data, translator, context)
    xp_to_add += xp_from_achievements

    if xp_to_add > 0:
        current_level = user_data.get("user", {}).get("level", 1)
        current_xp = user_data.get("user", {}).get("xp", 0)

        new_xp = current_xp + xp_to_add
        new_level = get_level_from_xp(new_xp)
        user_data["user"] = {"xp": new_xp, "level": new_level}

        _, xp_per_level_current, _ = get_level_info(new_level)
        xp_base_for_current_level = get_total_xp_for_level(new_level)
        next_level_xp_target = xp_base_for_current_level + xp_per_level_current
        console.print(translator.t("xp_gain_message", xp=xp_to_add, level=new_level, current_xp=new_xp,
                                   next_level_xp=next_level_xp_target))

        if new_level > current_level:
            _, _, title_key = get_level_info(new_level)
            console.print(translator.t("level_up_message", level=new_level, title=translator.t(title_key)),
                          style="bold magenta")
            lang = user_data.get("config", {}).get("language", "en")
            reward = random.choice(rewards_def[random.choice(["quotes", "jokes"])][lang])
            console.print(Panel(f"[italic cyan]{reward}[/italic cyan]", title=translator.t("random_reward_title"),
                                border_style="green", expand=False))

            _, xp_per_level, _ = get_level_info(new_level)
            xp_from_bonus = int(xp_per_level * 0.20)
            user_data["user"]["xp"] += xp_from_bonus

            bonus_final_xp = user_data["user"]["xp"]
            bonus_final_level = get_level_from_xp(bonus_final_xp)
            _, xp_per_level_bonus, _ = get_level_info(bonus_final_level)
            xp_base_for_bonus_level = get_total_xp_for_level(bonus_final_level)
            bonus_next_level_xp_target = xp_base_for_bonus_level + xp_per_level_bonus
            console.print(
                translator.t("xp_gain_message", xp=xp_from_bonus, level=bonus_final_level, current_xp=bonus_final_xp,
                             next_level_xp=bonus_next_level_xp_target))
            user_data["user"]["level"] = bonus_final_level

    save_user_data(user_data)