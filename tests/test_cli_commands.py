"""CLI behavior tests for help/profile/config command paths."""

from __future__ import annotations

import pytest

from gg_cli.main import app

pytestmark = pytest.mark.allow_console_output


def test_cli_help_command(runner):
    result = runner.invoke(app, ["help"])
    assert result.exit_code == 0
    assert "profile" in result.stdout
    assert "config" in result.stdout


def test_cli_profile_requires_git_email(monkeypatch, runner):
    monkeypatch.setattr("gg_cli.main.get_current_git_email", lambda: None)
    result = runner.invoke(app, ["profile"])
    assert result.exit_code != 0
    assert "Cannot find Git user email" in result.stdout


def test_cli_help_works_without_git_email(monkeypatch, runner):
    monkeypatch.setattr("gg_cli.main.get_current_git_email", lambda: None)
    result = runner.invoke(app, ["help"])
    assert result.exit_code == 0
    assert "Usage: gg COMMAND" in result.stdout


def test_cli_config_get_language(monkeypatch, runner, user_data_factory):
    data = user_data_factory()
    data["config"]["language"] = "zh"
    monkeypatch.setattr("gg_cli.main.load_user_data", lambda: data)
    monkeypatch.setattr("gg_cli.main.get_current_git_email", lambda: "test@example.com")
    result = runner.invoke(app, ["config", "--get", "language"])
    assert result.exit_code == 0
    assert "zh" in result.stdout


def test_cli_config_set_language_persists(monkeypatch, runner, user_data_factory):
    data = user_data_factory()
    saves = []

    def fake_save(payload):
        saves.append(payload.copy())

    monkeypatch.setattr("gg_cli.main.load_user_data", lambda: data)
    monkeypatch.setattr("gg_cli.main.save_user_data", fake_save)
    monkeypatch.setattr("gg_cli.main.get_current_git_email", lambda: "test@example.com")
    result = runner.invoke(app, ["config", "--set", "language=zh"])
    assert result.exit_code == 0
    assert data["config"]["language"] == "zh"
    assert saves


def test_cli_config_set_invalid_format(monkeypatch, runner):
    monkeypatch.setattr("gg_cli.main.get_current_git_email", lambda: "test@example.com")
    monkeypatch.setattr("gg_cli.main.load_user_data", lambda: {"config": {}})
    result = runner.invoke(app, ["config", "--set", "language"])
    assert result.exit_code == 0
    assert "Invalid format" in result.stdout
