import sys
import subprocess
import typer
import os
import json
import traceback
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm
from rich.progress_bar import ProgressBar
from rich.text import Text
from rich.console import Group

# --- 导入我们自己的模块 ---
from gg_cli.core import is_in_git_repo, load_user_data, save_user_data, get_current_git_email, get_profile_filename
from gg_cli.gamify import process_gamify_logic, get_level_info, get_total_xp_for_level
from gg_cli.translator import Translator
from gg_cli.utils import console, DATA_DIR, DEFINITIONS_DIR

# --- 1. Typer App 定义 ---
app = typer.Typer(
    help="Run `gg help` for a list of gamify commands.",
    add_help_option=False,  # 我们自己实现 help
    no_args_is_help=True,   # 没有参数时，自动显示帮助信息
)

def get_translator():
    user_data = load_user_data()
    lang_code = user_data.get("config", {}).get("language", "en")
    return Translator(lang_code)

# --- 2. Typer 命令函数 ---

@app.callback()
def main_callback(ctx: typer.Context):
    """
    这是一个在任何命令运行之前都会被调用的回调函数。
    我们在这里进行前置检查。
    """
    # 如果用户运行的不是 help 命令，并且当前不在一个 git 仓库里
    if ctx.invoked_subcommand != 'help' and not is_in_git_repo():
        console.print(f"[bold red]Error:[/bold red] The `gg {ctx.invoked_subcommand}` command must be run inside a Git repository.")
        raise typer.Exit(code=1)

@app.command("help")
def show_help():
    """Show the Git-Gamify command help."""
    # ... (这个函数内容完全不变) ...
    table = Table(box=None, show_header=False, show_edge=False)
    table.add_column(style="cyan", justify="left", width=12)
    table.add_column()
    table.add_row("profile", "Display user profile, stats, or reset progress.")
    table.add_row("config", "Get or set configuration values.")
    table.add_row("help", "Show this help message and exit.")
    console.print(Panel(
        Group(
            Text("Usage: gg COMMAND [OPTIONS]..."),
            Text("Gamify your Git experience. Your aliased `git` commands are tracked automatically.\n"),
            Text("[bold]Internal Commands:[/bold]"),
            table
        ),
        title="[bold]Git-Gamify Help[/bold]", border_style="green", expand=False
    ))

@app.command("profile")
def manage_profile(
        stats: bool = typer.Option(False, "--stats", "-s", help="Display detailed statistics."),
        reset: bool = typer.Option(False, "--reset", help="Reset all progress for the current user.")
):
    """Display user profile, stats, or reset progress."""
    # ... (这个函数内容完全不变) ...
    if reset:
        email = get_current_git_email()
        if not email:
            console.print("[red]Error: Cannot find git user email in this context. Is git configured?[/red]")
            return
        profile_path = DATA_DIR / get_profile_filename(email)
        if Confirm.ask(f"[bold yellow]Are you sure you want to reset all progress for user '{email}'?[/bold yellow]"):
            if profile_path.exists():
                try:
                    os.remove(profile_path)
                    console.print(f"[green]Profile for '{email}' has been successfully reset![/green]")
                except OSError as e:
                    console.print(f"[bold red]Error: Could not delete profile file. Reason: {e}[/bold red]")
            else:
                console.print(f"[yellow]No profile found for '{email}' to reset.[/yellow]")
        else:
            console.print("[cyan]Reset cancelled.[/cyan]")
        return

    if stats:
        user_data = load_user_data()
        s = user_data.get("stats", {})
        console.print(f"Total commits: {s.get('total_commits', 0)}")
        console.print(f"Total pushes: {s.get('total_pushes', 0)}")
        console.print(f"Consecutive commit days: {s.get('consecutive_commit_days', 0)}")
        return

    translator = get_translator()
    user_data = load_user_data()
    user = user_data["user"]
    profile_email = user_data.get("config", {}).get("user_email")

    email_label = translator.t("profile_email_label")
    level_label = translator.t("level_title")
    xp_progress_label = translator.t("xp_progress_title")

    _, xp_per_level, title_key = get_level_info(user['level'])
    translated_level_title = translator.t(title_key)

    xp_current_level_base = get_total_xp_for_level(user['level'])
    xp_next_level_base = xp_current_level_base + xp_per_level

    progress_value = user['xp'] - xp_current_level_base
    progress_total = xp_next_level_base - xp_current_level_base
    if progress_total <= 0: progress_total = 1

    progress_bar = ProgressBar(total=progress_total, completed=progress_value, width=20)
    progress_text = Text(f" {progress_value}/{progress_total} ({progress_value / progress_total:.1%})")

    progress_table = Table.grid(expand=True)
    progress_table.add_column(); progress_table.add_column(justify="right");
    progress_table.add_row(progress_bar, progress_text)

    profile_text_content = Text.from_markup(f"  [bold]{email_label}:[/bold] [cyan]{profile_email}[/cyan]\n" f"  [bold]{level_label}:[/bold] {user['level']} - {translated_level_title}\n\n" f"  [bold]{xp_progress_label}:[/bold]")
    panel_content_group = Group(profile_text_content, progress_table)
    console.print(Panel(panel_content_group, title=translator.t("profile_title"), border_style="magenta", padding=(0, 1), expand=False))

    unlocked_achievements = user_data.get("achievements_unlocked", {})
    if unlocked_achievements:
        from gg_cli.achievements import ACHIEVEMENTS_DEF as achievements_def
        display_achievements = [f"🏆 {translator.t(achievements_def.get(ach_id, {}).get('name_key', ach_id))}" for ach_id in unlocked_achievements.keys()]
        console.print(Panel("\n".join(display_achievements), title=translator.t("achievements_unlocked_title"), border_style="yellow", expand=False))

@app.command("config")
def manage_config(
        set_value: str = typer.Option(None, "--set", help="Set a value (e.g., --set language=zh)."),
        get_value: str = typer.Option(None, "--get", help="Get a value (e.g., --get language).")
):
    """Get or set configuration values."""
    # ... (这个函数内容完全不变) ...
    if not set_value and not get_value:
        console.print("[yellow]Please provide an option. Use --set or --get. Run 'gg help' for more info.[/yellow]")
        return
    user_data = load_user_data()
    if set_value:
        try:
            key, value = set_value.split('=', 1)
            if key.lower() == 'language':
                user_data['config']['language'] = value
                save_user_data(user_data)
                confirm_translator = Translator(value)
                console.print(Panel(confirm_translator.t("config_language_set"), border_style="green", expand=False))
            else:
                console.print(f"[red]Error: Unknown config key '[cyan]{key}[/cyan]'. Only 'language' is supported.[/red]")
        except ValueError:
            console.print("[red]Error: Invalid format. Please use '--set key=value'.[/red]")
    if get_value:
        if get_value.lower() == 'language':
            console.print(user_data.get('config', {}).get('language', 'en'))
        else:
            console.print(f"[red]Error: Unknown config key '[cyan]{get_value}[/cyan]'. Only 'language' is supported.[/red]")

# --- 3. Git Wrapper & Main Entry Point ---

def run_git_wrapper(git_args):
    """Executes the real git command and handles gamification."""
    try:
        result = subprocess.run(['git'] + git_args, capture_output=True, text=True, check=False, encoding='utf-8')
        if result.stdout: sys.stdout.write(result.stdout)
        if result.stderr: sys.stderr.write(result.stderr)
        if result.returncode == 0:
            command = git_args[0] if git_args else ""
            if command in ["commit", "push"]:
                console.print("-" * 20)
                process_gamify_logic(git_args)
    except FileNotFoundError:
        console.print("[bold red]Error: 'git' command not found. Is Git installed in your PATH?[/bold red]")
    except Exception:
        console.print("[bold red]An unexpected error occurred. Full traceback below:[/bold red]")
        traceback.print_exc()

def cli_entry():
    """The main entry point for the CLI tool."""
    # 检查是否是特殊的 'git' 包装命令
    if len(sys.argv) > 1 and sys.argv[1] == 'git':
        run_git_wrapper(sys.argv[2:])
    else:
        # 否则，将所有事情都交给 Typer 处理
        app()

if __name__ == "__main__":
    cli_entry()