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


def test_cli_profile_needs_git_email(monkeypatch):
    """
    Tests that running `gg profile` without a configured Git email exits with an error.
    """
    # Arrange: Simulate missing Git identity.
    monkeypatch.setattr('gg_cli.main.get_current_git_email', lambda: None)

    # Act: Invoke the 'profile' command.
    result = runner.invoke(app, ["profile"])

    # Assert: The command should fail with a non-zero exit code and show an error message.
    assert result.exit_code != 0
    assert "Cannot find Git user email" in result.stdout


def test_cli_help_works_without_git_email(monkeypatch):
    """
    Tests that the `gg help` command is accessible even without Git identity.
    """
    # Arrange: Simulate missing Git identity.
    monkeypatch.setattr('gg_cli.main.get_current_git_email', lambda: None)

    # Act: Invoke the 'help' command.
    result = runner.invoke(app, ["help"])

    # Assert: The command should run successfully with a zero exit code.
    assert result.exit_code == 0
    assert "Usage: gg COMMAND" in result.stdout
