# src/gg_cli/definitions_loader.py
"""Load and validate game definitions (achievements, rewards, locales)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gg_cli.utils import DEFINITIONS_DIR, LOCALES_DIR

REQUIRED_LOCALES = ("en", "zh")


class DefinitionsValidationError(RuntimeError):
    """Raised when static JSON definitions are invalid or inconsistent."""


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def load_achievements_flat() -> dict[str, dict[str, Any]]:
    raw = _load_json(DEFINITIONS_DIR / "achievements.json")
    return {
        achievement_id: achievement
        for category in raw.values()
        for achievement_id, achievement in category.items()
    }


def load_rewards() -> dict[str, Any]:
    return _load_json(DEFINITIONS_DIR / "rewards.json")


def load_locale(locale: str) -> dict[str, str]:
    data = _load_json(LOCALES_DIR / f"{locale}.json")
    return {k: str(v) for k, v in data.items()}


def validate_definitions() -> None:
    """Validate static definitions and locale keys for runtime safety."""
    errors: list[str] = []

    achievements = load_achievements_flat()
    locales = {locale: load_locale(locale) for locale in REQUIRED_LOCALES}

    for achievement_id, achievement in achievements.items():
        for key in ("name_key", "desc_key", "xp_reward"):
            if key not in achievement:
                errors.append(f"Achievement '{achievement_id}' missing key '{key}'.")

        xp_reward = achievement.get("xp_reward")
        if not isinstance(xp_reward, int) or xp_reward < 0:
            errors.append(
                f"Achievement '{achievement_id}' has invalid xp_reward '{xp_reward}'."
            )

        name_key = achievement.get("name_key")
        desc_key = achievement.get("desc_key")
        for locale, locale_map in locales.items():
            if name_key not in locale_map:
                errors.append(
                    f"Locale '{locale}' missing achievement key '{name_key}'."
                )
            if desc_key not in locale_map:
                errors.append(
                    f"Locale '{locale}' missing achievement key '{desc_key}'."
                )

    rewards = load_rewards()
    required_reward_types = ("quotes", "jokes")
    optional_reward_types = ("tips", "challenges")

    for reward_type in required_reward_types:
        if reward_type not in rewards or not isinstance(rewards[reward_type], dict):
            errors.append(f"Rewards missing '{reward_type}' section.")
            continue

    for reward_type in list(required_reward_types) + list(optional_reward_types):
        if reward_type not in rewards:
            continue
        if not isinstance(rewards[reward_type], dict):
            errors.append(f"Rewards '{reward_type}' must be a locale dictionary.")
            continue
        for locale in REQUIRED_LOCALES:
            values = rewards[reward_type].get(locale)
            if not isinstance(values, list) or not values:
                errors.append(
                    f"Rewards '{reward_type}' has no non-empty list for locale '{locale}'."
                )

    if errors:
        formatted = "\n".join(f"- {error}" for error in errors)
        raise DefinitionsValidationError(
            "Game definitions validation failed:\n" + formatted
        )
