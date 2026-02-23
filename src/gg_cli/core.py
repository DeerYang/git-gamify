# src/gg_cli/core.py
"""Core functionality for Git identity detection and user profile persistence."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from gg_cli.utils import DATA_DIR


def is_in_git_repo() -> bool:
    """Check if the current directory is inside a Git working tree."""
    try:
        output = subprocess.check_output(
            ["git", "rev-parse", "--is-inside-work-tree"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return output.strip() == "true"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_current_git_email() -> str | None:
    """Retrieve `user.email` from local Git configuration."""
    try:
        email = subprocess.check_output(
            ["git", "config", "user.email"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        return email or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def get_profile_filename(email: str) -> str | None:
    """Generate a safe profile filename for a user email."""
    if not email:
        return None
    return hashlib.sha1(email.encode("utf-8")).hexdigest() + ".json"


def get_default_user_data(email: str | None = None) -> dict[str, Any]:
    """Return the default user profile structure."""
    return {
        "config": {"language": "en", "user_email": email},
        "user": {"xp": 0, "level": 1},
        "achievements_unlocked": {},
        "stats": {
            "total_commits": 0,
            "total_pushes": 0,
            "last_commit_date": "1970-01-01",
            "last_push_date": "1970-01-01",
            "consecutive_commit_days": 0,
            "daily_xp_date": "1970-01-01",
            "daily_commit_count": 0,
            "daily_push_xp_earned": 0,
        },
    }


class UserRepository:
    """Persistence layer for user profile JSON files."""

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or DATA_DIR
        self.data_dir.mkdir(exist_ok=True)

    def get_profile_path(self, email: str) -> Path:
        filename = get_profile_filename(email)
        if not filename:
            raise ValueError("Email is required to resolve profile path.")
        return self.data_dir / filename

    def load(self, email: str | None) -> dict[str, Any]:
        """Load profile by email and merge with current default schema."""
        if not email:
            return get_default_user_data()

        profile_path = self.get_profile_path(email)
        user_data = get_default_user_data(email)
        if not profile_path.exists():
            self.save(user_data)
            return user_data

        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                disk_data = json.load(f)
            for main_key in user_data:
                if main_key in disk_data and isinstance(user_data[main_key], dict):
                    user_data[main_key].update(disk_data[main_key])
        except (json.JSONDecodeError, OSError):
            # Recover from corruption by replacing with clean schema.
            self.save(user_data)

        return user_data

    def save(self, data: dict[str, Any]) -> None:
        """Persist profile data using an atomic replace operation."""
        email = data.get("config", {}).get("user_email")
        if not email:
            return

        profile_path = self.get_profile_path(email)
        # Atomic write: write tmp file in same directory and replace destination.
        fd, tmp_path = tempfile.mkstemp(
            prefix=profile_path.stem + ".",
            suffix=".tmp",
            dir=str(profile_path.parent),
            text=True,
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, profile_path)
        except OSError:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            finally:
                raise


_USER_REPOSITORY = UserRepository()


def load_user_data() -> dict[str, Any]:
    """Load user data for current Git identity."""
    return _USER_REPOSITORY.load(get_current_git_email())


def save_user_data(data: dict[str, Any]) -> None:
    """Save user data for current Git identity."""
    _USER_REPOSITORY.save(data)
