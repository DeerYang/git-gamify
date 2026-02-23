# src/gg_cli/git_service.py
"""Thin service layer for Git subprocess interactions."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass
class GitCommandResult:
    """Result payload for a Git command execution."""

    returncode: int
    stdout: str
    stderr: str


class GitService:
    """Wrapper around git CLI calls to improve testability."""

    def run(self, args: list[str]) -> GitCommandResult:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=False,
            encoding="utf-8",
        )
        return GitCommandResult(
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    def get_shortstat_last_commit(self) -> str:
        return subprocess.check_output(
            ["git", "diff", "--shortstat", "HEAD~1", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()

    def get_last_commit_message(self) -> str:
        return subprocess.check_output(
            ["git", "log", "-1", "--pretty=%B"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
