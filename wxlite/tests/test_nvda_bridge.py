"""Zgodność istniejącego dodatku NVDA z mapą poleceń AMC Python."""

from __future__ import annotations

import ast
from pathlib import Path

from amc_wx_lite import nvda_bridge
from amc_wx_lite.shortcuts import Action


ROOT = Path(__file__).resolve().parents[2]


def _addon_commands() -> set[str]:
    source = (
        ROOT
        / "nvda-addon"
        / "addon"
        / "globalPlugins"
        / "amcController"
        / "transport.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "COMMANDS" for target in node.targets):
            continue
        call = node.value
        assert isinstance(call, ast.Call) and call.args
        sequence = call.args[0]
        assert isinstance(sequence, (ast.Tuple, ast.List, ast.Set))
        return {ast.literal_eval(item) for item in sequence.elts}
    raise AssertionError("Nie znaleziono listy COMMANDS istniejącego dodatku NVDA")


def test_every_existing_addon_command_is_explicitly_accounted_for() -> None:
    assert nvda_bridge.ALLOWED_COMMANDS == _addon_commands()


def test_actions_are_existing_actions_not_arbitrary_router_identifiers() -> None:
    assert nvda_bridge.ACTION_BY_COMMAND
    assert all(isinstance(action, Action) for action in nvda_bridge.ACTION_BY_COMMAND.values())
    assert nvda_bridge.action_for("playPause") is Action.PLAY_PAUSE
    assert nvda_bridge.action_for("recordToggle") is Action.RECORD_TOGGLE
    assert nvda_bridge.action_for("showSchedules") is Action.MANAGE_RADIO_SCHEDULES
    assert nvda_bridge.action_for("preset12") is Action.PRESET_12
    assert nvda_bridge.action_for("dowolne.polecenie") is None


def test_missing_features_are_refused_in_user_language_not_mapped_to_wrong_action() -> None:
    assert nvda_bridge.KNOWN_NOT_IMPLEMENTED == frozenset({"muteAll"})
    assert nvda_bridge.action_for("previousChapter") is Action.PREVIOUS_CHAPTER
    assert nvda_bridge.action_for("nextChapter") is Action.NEXT_CHAPTER
    assert nvda_bridge.action_for("showChapters") is Action.VIEW_CHAPTERS
    for command in nvda_bridge.KNOWN_NOT_IMPLEMENTED:
        message = nvda_bridge.unavailable_message(command)
        assert command not in message
        assert "AMC Test" in message


def test_previous_and_next_preset_are_special_supported_commands() -> None:
    assert {"presetPrevious", "presetNext"} <= nvda_bridge.SPECIAL_COMMANDS
    assert "presetPrevious" not in nvda_bridge.KNOWN_NOT_IMPLEMENTED
    assert "presetNext" not in nvda_bridge.KNOWN_NOT_IMPLEMENTED
    assert {"presetPrevious", "presetNext"} <= nvda_bridge.ALLOWED_COMMANDS


def test_session_list_is_supported_by_the_existing_addon() -> None:
    assert nvda_bridge.action_for("showSessions") is Action.SESSION_LIST
    assert "showSessions" not in nvda_bridge.KNOWN_NOT_IMPLEMENTED
    assert "showSessions" in nvda_bridge.OPEN_WINDOW_COMMANDS


def test_command_palette_is_supported_by_the_existing_addon() -> None:
    assert nvda_bridge.action_for("showCommands") is Action.COMMAND_PALETTE
    assert "showCommands" not in nvda_bridge.KNOWN_NOT_IMPLEMENTED
    assert "showCommands" in nvda_bridge.OPEN_WINDOW_COMMANDS


def test_only_explicit_view_commands_request_foreground() -> None:
    assert "showSearch" in nvda_bridge.OPEN_WINDOW_COMMANDS
    assert "showSchedules" in nvda_bridge.OPEN_WINDOW_COMMANDS
    for background in ("status", "playPause", "recordToggle", "refreshPodcastLibrary"):
        assert background not in nvda_bridge.OPEN_WINDOW_COMMANDS
