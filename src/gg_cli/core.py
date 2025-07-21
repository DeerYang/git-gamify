# src/gg_cli/core.py
"""Core functionalities for data management, user profile handling, and Git repo interactions."""

import json
import subprocess
import hashlib
from datetime import date
from gg_cli.utils import DATA_DIR


def is_in_git_repo() -> bool:
    """Check if the current directory is inside a Git working tree."""
    try:
        # This command returns 'true' if inside a repo, otherwise errors out.
        output = subprocess.check_output(
            ['git', 'rev-parse', '--is-inside-work-tree'],
            text=True,
            stderr=subprocess.DEVNULL
        )
        return output.strip() == 'true'
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_current_git_email() -> str | None:
    """Retrieve the user.email from the local Git configuration."""
    try:
        return subprocess.check_output(
            ['git', 'config', 'user.email'],
            text=True,
            stderr=subprocess.DEVNULL
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def get_profile_filename(email: str) -> str | None:
    """Generate a unique, safe filename for a user profile based on their email."""
    if not email:
        return None
    # Use SHA1 hash to anonymize and create a filesystem-safe name.
    return hashlib.sha1(email.encode('utf-8')).hexdigest() + ".json"


def get_default_user_data(email: str | None = None) -> dict:
    """Return a dictionary containing the default data structure for a new user."""
    return {
        "config": {"language": "en", "user_email": email},
        "user": {"xp": 0, "level": 1},
        "achievements_unlocked": {},
        "stats": {
            "total_commits": 0,
            "total_pushes": 0,
            "last_commit_date": "1970-01-01",
            "last_push_date": "1970-01-01",
            "consecutive_commit_days": 0
        }
    }


def load_user_data() -> dict:
    """
    Load user data from their JSON profile file.

    Identifies the user by their git email, finds the corresponding profile,
    and merges it with the default data structure to ensure forward compatibility
    if new fields are added to the app. Creates a new profile if one doesn't exist.
    """
    email = get_current_git_email()
    if not email:
        return get_default_user_data()

    filename = get_profile_filename(email)
    profile_path = DATA_DIR / filename

    if not profile_path.exists():
        user_data = get_default_user_data(email)
        save_user_data(user_data)
        return user_data

    # Start with default data to ensure all keys exist.
    user_data = get_default_user_data(email)
    try:
        with open(profile_path, 'r', encoding='utf-8') as f:
            disk_data = json.load(f)
        # Merge saved data into the default structure. This makes the data
        # robust against schema changes (e.g., adding new stats).
        for main_key in user_data:
            if main_key in disk_data and isinstance(user_data[main_key], dict):
                user_data[main_key].update(disk_data[main_key])
    except (json.JSONDecodeError, FileNotFoundError):
        # If the file is corrupted or deleted mid-operation, save a clean default state.
        save_user_data(user_data)

    return user_data


def save_user_data(data: dict) -> None:
    """Save the user's data dictionary to their corresponding JSON profile file."""
    email = data.get("config", {}).get("user_email")
    if not email:
        return

    filename = get_profile_filename(email)
    profile_path = DATA_DIR / filename
    with open(profile_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)