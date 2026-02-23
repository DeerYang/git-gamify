"""CLI entrypoint for internal commands and git wrapper dispatch."""

from __future__ import annotations

import os
import sys
import traceback

import typer
from rich.console import Group
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.prompt import Confirm
from rich.table import Table
from rich.text import Text

from gg_cli.core import (
    get_current_git_email,
    get_default_user_data,
    get_profile_filename,
    load_user_data,
    save_user_data,
)
from gg_cli.definitions_loader import DefinitionsValidationError
from gg_cli.gamify import (
    ensure_runtime_definitions_valid,
    get_level_info,
    get_total_xp_for_level,
    process_gamify_logic,
)
from gg_cli.git_service import GitService
from gg_cli.translator import Translator
from gg_cli.utils import DATA_DIR, console

app = typer.Typer(
    help="Run `gg help` for a list of gamify commands.",
    add_help_option=False,
    no_args_is_help=True,
)


def get_translator() -> Translator:
    """Build a translator based on current user language configuration."""
    user_data = load_user_data()
    lang_code = user_data.get("config", {}).get("language", "en")
    return Translator(lang_code)


@app.callback()
def main_callback(ctx: typer.Context) -> None:
    """Run lightweight preflight checks before executing CLI subcommands."""
    command = ctx.invoked_subcommand
    if command == "help":
        return

    try:
        ensure_runtime_definitions_valid()
    except DefinitionsValidationError as exc:
        console.print(f"[bold red]Definitions error:[/bold red] {exc}")
        raise typer.Exit(code=1)

    # Profile/config are user-scope commands and require a git identity.
    if command in ["profile", "config"] and get_current_git_email() is None:
        console.print("[bold red]Error:[/bold red] Cannot find Git user email.")
        console.print("Please run `git config --global user.email 'your@email.com'` to set your identity.")
        raise typer.Exit(code=1)


@app.command("help")
def show_help() -> None:
    """Render custom help output for internal gg commands."""
    table = Table(box=None, show_header=False, show_edge=False)
    table.add_column(style="cyan", justify="left", width=12)
    table.add_column()
    table.add_row("profile", "Display user profile, stats, or reset progress.")
    table.add_row("config", "Get or set configuration values.")
    table.add_row("help", "Show this help message and exit.")
    console.print(
        Panel(
            Group(
                Text("Usage: gg COMMAND [OPTIONS]..."),
                Text("Gamify your Git experience. Your aliased `git` commands are tracked automatically.\n"),
                Text("[bold]Internal Commands:[/bold]"),
                table,
            ),
            title="[bold]Git-Gamify Help[/bold]",
            border_style="green",
            expand=False,
        )
    )


@app.command("profile")
def manage_profile(
    stats: bool = typer.Option(False, "--stats", "-s", help="Display detailed statistics."),
    reset: bool = typer.Option(False, "--reset", help="Reset all progress for the current user."),
) -> None:
    """Display profile info, stats, or reset the current profile."""
    if reset:
        email = get_current_git_email()
        if not email:
            console.print("[red]Error: Cannot find git user email. Is git configured?[/red]")
            raise typer.Exit(code=1)

        profile_path = DATA_DIR / get_profile_filename(email)
        if Confirm.ask(f"[bold yellow]Are you sure you want to reset all progress for '{email}'?[/bold yellow]"):
            if profile_path.exists():
                try:
                    os.remove(profile_path)
                    console.print(f"[green]Profile for '{email}' has been successfully reset![/green]")
                except OSError as exc:
                    console.print(f"[bold red]Error: Could not delete profile file. Reason: {exc}[/bold red]")
            else:
                console.print(f"[yellow]No profile found for '{email}' to reset.[/yellow]")
        else:
            console.print("[cyan]Reset cancelled.[/cyan]")
        return

    if stats:
        user_data = load_user_data()
        stats_payload = user_data.get("stats", {})
        console.print(f"Total commits: {stats_payload.get('total_commits', 0)}")
        console.print(f"Total pushes: {stats_payload.get('total_pushes', 0)}")
        console.print(f"Consecutive commit days: {stats_payload.get('consecutive_commit_days', 0)}")
        return

    translator = get_translator()
    user_data = load_user_data()
    user = user_data.get("user", get_default_user_data()["user"])
    profile_email = user_data.get("config", {}).get("user_email")

    # Build level progress values for the profile view.
    level = user.get("level", 1)
    xp = user.get("xp", 0)
    _, xp_per_level, title_key = get_level_info(level)
    translated_level_title = translator.t(title_key)
    xp_current_level_base = get_total_xp_for_level(level)
    xp_next_level_base = xp_current_level_base + xp_per_level
    progress_value = xp - xp_current_level_base
    progress_total = xp_next_level_base - xp_current_level_base
    if progress_total <= 0:
        progress_total = 1

    progress_bar = ProgressBar(total=progress_total, completed=progress_value, width=20)
    progress_text = Text(f" {progress_value}/{progress_total} ({progress_value / progress_total:.1%})")
    progress_table = Table.grid(expand=True)
    progress_table.add_column()
    progress_table.add_column(justify="right")
    progress_table.add_row(progress_bar, progress_text)

    profile_text = Text.from_markup(
        f"  [bold]{translator.t('profile_email_label')}:[/bold] [cyan]{profile_email}[/cyan]\n"
        f"  [bold]{translator.t('level_title')}:[/bold] {level} - {translated_level_title}\n\n"
        f"  [bold]{translator.t('xp_progress_title')}:[/bold]"
    )
    panel_group = Group(profile_text, progress_table)
    console.print(
        Panel(
            panel_group,
            title=translator.t("profile_title"),
            border_style="magenta",
            padding=(0, 1),
            expand=False,
        )
    )

    unlocked_achievements = user_data.get("achievements_unlocked", {})
    if unlocked_achievements:
        # Import lazily to avoid definition loading cost when achievements are not displayed.
        from gg_cli.achievements import ACHIEVEMENTS_DEF as achievements_def

        display_items = [
            f"* {translator.t(achievements_def.get(ach_id, {}).get('name_key', ach_id))}"
            for ach_id in unlocked_achievements
        ]
        console.print(
            Panel(
                "\n".join(display_items),
                title=translator.t("achievements_unlocked_title"),
                border_style="yellow",
                expand=False,
            )
        )


@app.command("config")
def manage_config(
    set_value: str = typer.Option(None, "--set", help="Set a value (e.g., 'language=zh')."),
    get_value: str = typer.Option(None, "--get", help="Get a value (e.g., 'language')."),
) -> None:
    """Read or update user configuration values."""
    if not set_value and not get_value:
        console.print("[yellow]Please provide an option: --set or --get. Run 'gg help' for more info.[/yellow]")
        return

    user_data = load_user_data()
    if set_value:
        try:
            key, value = set_value.split("=", 1)
            if key.lower() == "language":
                user_data["config"]["language"] = value
                save_user_data(user_data)
                confirm_translator = Translator(value)
                console.print(
                    Panel(confirm_translator.t("config_language_set"), border_style="green", expand=False)
                )
            else:
                console.print(
                    f"[red]Error: Unknown config key '[cyan]{key}[/cyan]'. Only 'language' is supported.[/red]"
                )
        except ValueError:
            console.print("[red]Error: Invalid format. Please use '--set key=value'.[/red]")

    if get_value:
        if get_value.lower() == "language":
            console.print(user_data.get("config", {}).get("language", "en"))
        else:
            console.print(
                f"[red]Error: Unknown config key '[cyan]{get_value}[/cyan]'. Only 'language' is supported.[/red]"
            )


def run_git_wrapper(git_args: list[str]) -> None:
    """Run real git command and trigger gamification on successful commit/push."""
    git_service = GitService()
    try:
        result = git_service.run(git_args)
        if result.stdout:
            sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)

        if result.returncode == 0:
            command = git_args[0] if git_args else ""
            if command in ["commit", "push"]:
                console.print("-" * 20)
                process_gamify_logic(git_args, git_service=git_service)
    except FileNotFoundError:
        console.print("[bold red]Error: 'git' command not found. Is Git installed and in your PATH?[/bold red]")
    except Exception:
        console.print("[bold red]An unexpected error occurred. Full traceback below:[/bold red]")
        traceback.print_exc()


def cli_entry() -> None:
    """Dispatch either git-wrapper mode or regular Typer command mode."""
    if len(sys.argv) > 1 and sys.argv[1] == "git":
        run_git_wrapper(sys.argv[2:])
    else:
        app()


if __name__ == "__main__":
    cli_entry()

