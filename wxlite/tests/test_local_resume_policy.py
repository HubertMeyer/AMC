from __future__ import annotations

import json

from amc_wx_lite.local_resume_policy import (
    load_remember_local_playback_positions,
    resolve_remember_local_playback_positions,
)


def test_missing_profile_uses_amc_default_true(tmp_path) -> None:
    assert load_remember_local_playback_positions(tmp_path / "missing.json") is True


def test_profile_boolean_is_inherited_without_writing(tmp_path) -> None:
    state = tmp_path / "state.json"
    state.write_text(
        json.dumps({"settings": {"rememberLocalPlaybackPositions": False}}),
        encoding="utf-8",
    )
    assert load_remember_local_playback_positions(state) is False
    assert resolve_remember_local_playback_positions(None, False) is False
    assert resolve_remember_local_playback_positions(True, False) is True


def test_non_boolean_profile_value_does_not_leak_into_policy(tmp_path) -> None:
    state = tmp_path / "state.json"
    state.write_text(
        json.dumps({"settings": {"rememberLocalPlaybackPositions": "false"}}),
        encoding="utf-8",
    )
    assert load_remember_local_playback_positions(state) is True
