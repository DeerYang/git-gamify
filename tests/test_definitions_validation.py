"""Tests for static definitions and locale consistency checks."""

from __future__ import annotations

import pytest

from gg_cli.definitions_loader import DefinitionsValidationError, validate_definitions


def test_validate_definitions_passes_for_current_files():
    """Repository definitions should pass validation in normal state."""
    validate_definitions()


def _base_valid_payloads():
    """Construct minimal valid in-memory payloads for mutation-based tests."""
    achievements = {
        "custom": {
            "name_key": "ach_custom_name",
            "desc_key": "ach_custom_desc",
            "xp_reward": 10,
        }
    }
    locales = {
        "en": {"ach_custom_name": "Name", "ach_custom_desc": "Desc"},
        "zh": {"ach_custom_name": "名字", "ach_custom_desc": "描述"},
    }
    rewards = {
        "quotes": {"en": ["q"], "zh": ["q"]},
        "jokes": {"en": ["j"], "zh": ["j"]},
    }
    return achievements, locales, rewards


@pytest.mark.parametrize(
    "mutator",
    [
        lambda ach, loc, rew: loc["en"].pop("ach_custom_desc"),
        lambda ach, loc, rew: ach["custom"].update({"xp_reward": -1}),
        lambda ach, loc, rew: rew["quotes"].update({"zh": []}),
    ],
)
def test_validate_definitions_fails_on_broken_payloads(monkeypatch, mutator):
    """Validation should fail when key locale/achievement/reward invariants are broken."""
    achievements, locales, rewards = _base_valid_payloads()
    mutator(achievements, locales, rewards)

    monkeypatch.setattr("gg_cli.definitions_loader.load_achievements_flat", lambda: achievements)
    monkeypatch.setattr("gg_cli.definitions_loader.load_locale", lambda locale: locales[locale])
    monkeypatch.setattr("gg_cli.definitions_loader.load_rewards", lambda: rewards)

    with pytest.raises(DefinitionsValidationError):
        validate_definitions()
