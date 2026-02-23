"""Tests for git wrapper behavior in CLI entry layer."""

from __future__ import annotations

from types import SimpleNamespace

from gg_cli.main import run_git_wrapper


def test_run_git_wrapper_triggers_gamify_on_success(monkeypatch):
    calls = []

    class StubService:
        def run(self, args):
            assert args == ["commit", "-m", "x"]
            return SimpleNamespace(returncode=0, stdout="ok\n", stderr="")

    monkeypatch.setattr("gg_cli.main.GitService", StubService)
    monkeypatch.setattr(
        "gg_cli.main.process_gamify_logic",
        lambda args, git_service=None: calls.append((args, git_service)),
    )

    run_git_wrapper(["commit", "-m", "x"])
    assert calls
    assert calls[0][0] == ["commit", "-m", "x"]


def test_run_git_wrapper_skips_gamify_on_failure(monkeypatch):
    calls = []

    class StubService:
        def run(self, args):
            return SimpleNamespace(returncode=1, stdout="", stderr="fail\n")

    monkeypatch.setattr("gg_cli.main.GitService", StubService)
    monkeypatch.setattr(
        "gg_cli.main.process_gamify_logic",
        lambda args, git_service=None: calls.append((args, git_service)),
    )

    run_git_wrapper(["commit", "-m", "x"])
    assert calls == []
