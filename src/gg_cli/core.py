import json
import subprocess
import hashlib
from gg_cli.utils import DATA_DIR
from datetime import date


def is_in_git_repo():
    try:
        return subprocess.check_output(['git', 'rev-parse', '--is-inside-work-tree'], text=True,
                                       stderr=subprocess.DEVNULL).strip() == 'true'
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_current_git_email():
    try:
        return subprocess.check_output(['git', 'config', 'user.email'], text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def get_profile_filename(email):
    if not email: return None
    return hashlib.sha1(email.encode('utf-8')).hexdigest() + ".json"


def get_default_user_data(email=None):
    return {
        "config": {"language": "en", "user_email": email},
        "user": {"xp": 0, "level": 1},
        "achievements_unlocked": {},
        "stats": {
            "total_commits": 0, "total_pushes": 0,
            "last_commit_date": "1970-01-01",
            "last_push_date": "1970-01-01",
            "consecutive_commit_days": 0
        }
    }


def load_user_data():
    email = get_current_git_email()
    if not email: return get_default_user_data()

    filename = get_profile_filename(email)
    profile_path = DATA_DIR / filename

    if not profile_path.exists():
        user_data = get_default_user_data(email)
        save_user_data(user_data)
        return user_data

    user_data = get_default_user_data(email)
    try:
        with open(profile_path, 'r', encoding='utf-8') as f:
            disk_data = json.load(f)
        for main_key in user_data:
            if main_key in disk_data and isinstance(user_data[main_key], dict):
                user_data[main_key].update(disk_data[main_key])
    except (json.JSONDecodeError, FileNotFoundError):
        save_user_data(user_data)

    return user_data


def save_user_data(data):
    email = data.get("config", {}).get("user_email")
    if not email: return

    filename = get_profile_filename(email)
    profile_path = DATA_DIR / filename
    with open(profile_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)