import json
import re
from datetime import date, datetime
from gg_cli.utils import DEFINITIONS_DIR, console
from gg_cli.translator import Translator
from rich.panel import Panel


# --- 1. 数据加载 ---
def load_achievement_definitions():
    with open(DEFINITIONS_DIR / 'achievements.json', 'r', encoding='utf-8') as f:
        defs = json.load(f)
        return {ach_id: ach_data for category in defs.values() for ach_id, ach_data in category.items()}


ACHIEVEMENTS_DEF = load_achievement_definitions()


# --- 2. 单个成就的检查函数 ---
def _check_simple_stat(user_data, stat_key, target_value, ach_id):
    if user_data["stats"].get(stat_key, 0) >= target_value:
        return {"id": ach_id}
    return None


def _check_midnight_coder(user_data, context, **kwargs):
    if context.get("command") != "commit": return None
    now = datetime.now()
    if 0 <= now.hour < 4:
        return {"id": "midnight_coder"}
    return None


def _check_firefighter(user_data, context, **kwargs):
    if context.get("command") != "commit": return None
    deletions = context.get("deletions", 0)
    if deletions >= 500:
        return {"id": "firefighter"}
    return None


def _check_storyteller(user_data, context, **kwargs):
    if context.get("command") != "commit": return None
    commit_message = context.get("commit_message", "")
    if len(commit_message.split()) >= 50:
        return {"id": "storyteller"}
    return None


# --- 3. 检查函数注册表 (真正已修复) ---
# 核心修复点：修改所有lambda函数，使其能接受关键字参数。
# 我们使用 `*args` 和 `**kwargs` 来接收所有我们不关心的额外参数。
ACHIEVEMENT_CHECKERS = {
    "first_commit": lambda u, **kwargs: _check_simple_stat(u, "total_commits", 1, "first_commit"),
    "commit_10": lambda u, **kwargs: _check_simple_stat(u, "total_commits", 10, "commit_10"),
    "commit_100": lambda u, **kwargs: _check_simple_stat(u, "total_commits", 100, "commit_100"),
    "commit_1000": lambda u, **kwargs: _check_simple_stat(u, "total_commits", 1000, "commit_1000"),
    "first_push": lambda u, **kwargs: _check_simple_stat(u, "total_pushes", 1, "first_push"),
    "push_50": lambda u, **kwargs: _check_simple_stat(u, "total_pushes", 50, "push_50"),
    "combo_3": lambda u, **kwargs: _check_simple_stat(u, "consecutive_commit_days", 3, "combo_3"),
    "combo_7": lambda u, **kwargs: _check_simple_stat(u, "consecutive_commit_days", 7, "combo_7"),
    "combo_30": lambda u, **kwargs: _check_simple_stat(u, "consecutive_commit_days", 30, "combo_30"),
    "midnight_coder": _check_midnight_coder,
    "firefighter": _check_firefighter,
    "storyteller": _check_storyteller,
}


# --- 4. 主检查循环 ---
def check_all_achievements(user_data: dict, translator: Translator, context: dict) -> int:
    xp_from_achievements = 0

    for ach_id, checker_func in ACHIEVEMENT_CHECKERS.items():
        if ach_id not in user_data["achievements_unlocked"]:
            # 这个调用现在对所有已注册的函数都是安全的
            result = checker_func(user_data, context=context)
            if result:
                user_data["achievements_unlocked"][ach_id] = date.today().isoformat()

                reward = ACHIEVEMENTS_DEF[ach_id].get("xp_reward", 0)
                xp_from_achievements += reward

                name = translator.t(ACHIEVEMENTS_DEF[ach_id]["name_key"])
                desc = translator.t(ACHIEVEMENTS_DEF[ach_id]["desc_key"])
                panel_title = translator.t("achievement_unlocked_panel_title")
                console.print(Panel(
                    f"[bold cyan]{name}[/bold cyan]\n[italic]{desc}[/italic]\n\n✨ [bold]Gained +{reward} XP![/bold]",
                    title=panel_title, border_style="yellow", expand=False))

    return xp_from_achievements