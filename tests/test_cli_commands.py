# tests/test_cli_commands.py
"""
End-to-end tests for the CLI commands, simulating user interaction.
These tests verify command behavior, error handling, and output.
"""

from typer.testing import CliRunner
from gg_cli.main import app

# A single CliRunner instance can be reused for all tests.
runner = CliRunner()


def test_cli_help_command():
    """Tests that `gg help` runs successfully and contains expected text."""
    result = runner.invoke(app, ["help"])

    assert result.exit_code == 0
    assert "profile" in result.stdout
    assert "config" in result.stdout


def test_cli_profile_needs_git_repo(monkeypatch):
    """
    Tests that running `gg profile` outside a Git repository exits with an error.
    """
    # Arrange: Use monkeypatch to simulate being outside a Git repository.
    # We patch the function at the point of use to ensure the patch takes effect.
    monkeypatch.setattr('gg_cli.main.is_in_git_repo', lambda: False)

    # Act: Invoke the 'profile' command.
    result = runner.invoke(app, ["profile"])

    # Assert: The command should fail with a non-zero exit code and show an error message.
    assert result.exit_code != 0
    assert "must be run inside a Git repository" in result.stdout


def test_cli_help_works_outside_git_repo(monkeypatch):
    """
    Tests that the `gg help` command is accessible even when outside a Git repository.
    """
    # Arrange: Simulate being outside a Git repository.
    monkeypatch.setattr('gg_cli.main.is_in_git_repo', lambda: False)

    # Act: Invoke the 'help' command.
    result = runner.invoke(app, ["help"])

    # Assert: The command should run successfully with a zero exit code.
    assert result.exit_code == 0
    assert "Usage: gg COMMAND" in result.stdout