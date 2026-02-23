"""Shared pytest fixtures for deterministic and maintainable tests."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from typing import Any

import pytest
from typer.testing import CliRunner

from gg_cli.core import get_default_user_data


@dataclass
class StubTranslator:
    """Simple translator stub that returns keys directly."""

    def t(self, key: str, **kwargs: Any) -> str:
        return key.format(**kwargs) if kwargs else key


@dataclass
class StubGitService:
    """Git service stub used by event processing tests."""

    shortstat: str = " 2 files changed, 100 insertions(+), 40 deletions(-)"
    commit_message: str = "Add feature and tests"

    def get_shortstat_last_commit(self) -> str:
        return self.shortstat

    def get_last_commit_message(self) -> str:
        return self.commit_message


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def translator() -> StubTranslator:
    return StubTranslator()


@pytest.fixture
def user_data() -> dict[str, Any]:
    return get_default_user_data("test@example.com")


@pytest.fixture
def git_service() -> StubGitService:
    return StubGitService()


@pytest.fixture
def today() -> date:
    return date(2026, 2, 2)


@pytest.fixture
def user_data_factory() -> Any:
    """Return a factory for isolated mutable user data payloads."""

    template = get_default_user_data("test@example.com")

    def _factory() -> dict[str, Any]:
        return deepcopy(template)

    return _factory


@pytest.fixture(autouse=True)
def suppress_console_output(request, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep tests quiet by default while allowing opt-out per test/module."""
    if request.node.get_closest_marker("allow_console_output"):
        return
    monkeypatch.setattr("gg_cli.utils.console.print", lambda *args, **kwargs: None)
