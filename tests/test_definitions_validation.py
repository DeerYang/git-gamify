"""Tests for static definitions and locale consistency checks."""

import pytest

from gg_cli.definitions_loader import DefinitionsValidationError, validate_definitions


def test_validate_definitions_passes_for_current_files():
    """Repository definitions should be internally consistent."""
    validate_definitions()


def test_validate_definitions_raises_on_missing_locale_key(monkeypatch):
    """Validation should fail if achievement locale keys are missing."""

    def fake_load_achievements_flat():
        return {
            "custom": {
                "name_key": "ach_custom_name",
                "desc_key": "ach_custom_desc",
                "xp_reward": 10,
            }
        }

    def fake_load_locale(locale):
        if locale == "en":
            return {"ach_custom_name": "Name"}
        return {"ach_custom_name": "Name", "ach_custom_desc": "Desc"}

    def fake_load_rewards():
        return {
            "quotes": {"en": ["q"], "zh": ["q"]},
            "jokes": {"en": ["j"], "zh": ["j"]},
        }

    monkeypatch.setattr(
        "gg_cli.definitions_loader.load_achievements_flat", fake_load_achievements_flat
    )
    monkeypatch.setattr("gg_cli.definitions_loader.load_locale", fake_load_locale)
    monkeypatch.setattr("gg_cli.definitions_loader.load_rewards", fake_load_rewards)

    with pytest.raises(DefinitionsValidationError):
        validate_definitions()
