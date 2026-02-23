"""Tests for profile persistence behavior in UserRepository."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gg_cli.core import UserRepository, get_default_user_data


def test_user_repository_round_trip(tmp_path: Path):
    repo = UserRepository(tmp_path)
    data = get_default_user_data("test@example.com")
    data["stats"]["total_commits"] = 3
    repo.save(data)

    loaded = repo.load("test@example.com")
    assert loaded["stats"]["total_commits"] == 3
    assert loaded["config"]["user_email"] == "test@example.com"


def test_user_repository_merges_partial_schema_from_disk(tmp_path: Path):
    repo = UserRepository(tmp_path)
    profile_path = repo.get_profile_path("test@example.com")
    profile_path.write_text(
        json.dumps(
            {"stats": {"total_commits": 9}, "config": {"language": "zh"}},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    loaded = repo.load("test@example.com")
    assert loaded["stats"]["total_commits"] == 9
    assert loaded["stats"]["total_pushes"] == 0
    assert loaded["config"]["language"] == "zh"
    assert loaded["config"]["user_email"] == "test@example.com"


def test_user_repository_recovers_from_corrupt_file(tmp_path: Path):
    repo = UserRepository(tmp_path)
    profile_path = repo.get_profile_path("test@example.com")
    profile_path.write_text("{bad-json", encoding="utf-8")

    loaded = repo.load("test@example.com")
    assert loaded["stats"]["total_commits"] == 0
    assert loaded["config"]["user_email"] == "test@example.com"


def test_user_repository_cleans_temp_file_when_replace_fails(tmp_path: Path, monkeypatch):
    repo = UserRepository(tmp_path)
    data = get_default_user_data("test@example.com")

    def fake_replace(src: str, dst: str):
        raise OSError("replace failed")

    monkeypatch.setattr("gg_cli.core.os.replace", fake_replace)

    with pytest.raises(OSError):
        repo.save(data)

    leftovers = list(tmp_path.glob("*.tmp"))
    assert leftovers == []
