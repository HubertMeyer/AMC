from __future__ import annotations

import json
import ast
from datetime import date
from pathlib import Path

import pytest

from amc_wx_lite.full_backup import (
    ALL_SECTIONS,
    BACKUP_SCOPES,
    CONFIGURATION,
    RADIO,
    RADIO_SCHEDULES,
    FullBackupError,
    build_imported_ui_state,
    complete_export,
    describe_sections,
    inspect_import,
    staging_path,
)
from amc_wx_lite.state_store import LiteState, Options, StateStore, Station


def _core_backup(path: Path, sections: tuple[str, ...] = ALL_SECTIONS) -> None:
    kind = "fullBackup" if sections == ALL_SECTIONS else "profileBackup"
    payload = {
        "schemaVersion": 1,
        "kind": kind,
        "state": {"radio": {"stations": []}},
    }
    if kind == "profileBackup":
        payload["sections"] = list(sections)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _source_state() -> LiteState:
    return LiteState(
        options=Options(
            volume=61,
            session_order=["files", "radio"],
            timeshift_minutes=47,
        ),
        shortcut_overrides={"settings.general": "Ctrl+Alt+G"},
        stations=[Station("radio-1", "Radio Źródłowe", "https://radio.invalid")],
        search_history={"global": ["Dominikanie Rzeszów"]},
        radio_schedule_overrides=[_schedule("schedule-1", "Poranek")],
        podcast_inbox_sort_mode="Alphabetical",
        tidal_sort_modes={"library": "Alphabetical"},
    )


def _schedule(schedule_id: str, name: str) -> dict:
    return {
        "id": schedule_id,
        "name": name,
        "stationId": "radio-1",
        "stationName": "Radio Źródłowe",
        "streamUrl": "https://radio.invalid/live.mp3",
        "nextStartUtcTicks": 639_271_800_000_000_000,
        "timeZoneId": "Central European Standard Time",
        "durationMinutes": 60,
        "segmentMinutes": 0,
        "recurrence": "Daily",
        "activeDays": [],
        "outputFolder": "",
        "fileNameTemplate": "{stacja} - {data} {czas}",
        "enabled": True,
    }


def test_full_backup_combines_core_and_sanitized_ui_state(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "ui")
    store.save(_source_state())
    target = tmp_path / "moja-kopia.amcbackup.json"
    staged = staging_path(target)
    _core_backup(staged)

    complete_export(
        staged,
        target,
        profile_id="public",
        ui_state_path=store.path,
    )

    raw = json.loads(target.read_text(encoding="utf-8"))
    assert raw["kind"] == "fullBackup"
    assert raw["amcPython"]["releaseProfile"] == "public"
    assert raw["amcPython"]["sections"] == list(ALL_SECTIONS)
    restored_store = StateStore(tmp_path / "restored-ui")
    plan = inspect_import(
        target,
        expected_profile_id="public",
        state_store=restored_store,
    )
    restored = build_imported_ui_state(plan, restored_store)
    assert plan.has_ui_state is True
    assert restored.options.volume == 61
    assert restored.shortcut_overrides == {"settings.general": "Ctrl+Alt+G"}
    assert restored.search_history == {"global": ["Dominikanie Rzeszów"]}
    assert restored.stations[0].name == "Radio Źródłowe"
    assert restored.radio_schedule_overrides is not None


def test_partial_configuration_import_preserves_radio_and_schedules(
    tmp_path: Path,
) -> None:
    source = StateStore(tmp_path / "source")
    source.save(_source_state())
    target = tmp_path / "ustawienia.amcsettings.json"
    staged = staging_path(target)
    _core_backup(staged, (CONFIGURATION,))
    complete_export(
        staged,
        target,
        profile_id="public",
        ui_state_path=source.path,
        sections=(CONFIGURATION,),
    )

    current = StateStore(tmp_path / "current")
    current.save(
        LiteState(
            options=Options(volume=10, timeshift_minutes=12),
            stations=[Station("current", "Radio Bieżące", "https://current.invalid")],
            radio_schedule_overrides=[_schedule("current-schedule", "Noc")],
        )
    )
    plan = inspect_import(
        target,
        expected_profile_id="public",
        state_store=current,
    )
    restored = build_imported_ui_state(plan, current)

    assert plan.included_sections == (CONFIGURATION,)
    assert restored.options.volume == 61
    assert restored.options.timeshift_minutes == 12
    assert restored.shortcut_overrides == {"settings.general": "Ctrl+Alt+G"}
    assert restored.stations[0].name == "Radio Bieżące"
    assert restored.radio_schedule_overrides is not None
    assert restored.radio_schedule_overrides[0]["id"] == "current-schedule"
    assert restored.radio_schedule_overrides[0]["name"] == "Noc"
    raw = json.loads(target.read_text(encoding="utf-8"))
    assert "stations" not in raw["amcPython"]["state"]
    assert "radio_schedule_overrides" not in raw["amcPython"]["state"]


def test_legacy_backup_does_not_restore_last_used_rate_as_general_default(
    tmp_path: Path,
) -> None:
    source = StateStore(tmp_path / "source")
    source.save(_source_state())
    target = tmp_path / "stara-kopia.amcbackup.json"
    staged = staging_path(target)
    _core_backup(staged)
    complete_export(
        staged,
        target,
        profile_id="public",
        ui_state_path=source.path,
    )

    # Format 1 nie miał znacznika migracji. Pole rate było wtedy ostatnio
    # używaną prędkością, a nie świadomym ustawieniem wszystkich sesji.
    raw = json.loads(target.read_text(encoding="utf-8"))
    section = raw["amcPython"]
    section["formatVersion"] = 1
    section.pop("sections", None)
    section.pop("contentSha256", None)
    section["state"].pop("playback_rate_version", None)
    section["state"]["options"]["rate"] = 2.0
    target.write_text(json.dumps(raw), encoding="utf-8")

    current = StateStore(tmp_path / "current")
    current.save(LiteState(options=Options(volume=10, rate=1.25)))
    plan = inspect_import(
        target,
        expected_profile_id="public",
        state_store=current,
    )
    restored = build_imported_ui_state(plan, current)

    assert restored.options.volume == 61
    assert restored.options.rate == 1.25


def test_radio_and_schedules_are_independent_ui_sections(tmp_path: Path) -> None:
    source = StateStore(tmp_path / "source")
    source.save(_source_state())
    current = StateStore(tmp_path / "current")
    current.save(
        LiteState(
            stations=[Station("old", "Stare Radio", "https://old.invalid")],
            radio_schedule_overrides=[_schedule("old-schedule", "Stary plan")],
        )
    )

    radio_path = tmp_path / "radio.amcradio.json"
    radio_stage = staging_path(radio_path)
    _core_backup(radio_stage, (RADIO,))
    complete_export(
        radio_stage,
        radio_path,
        profile_id="public",
        ui_state_path=source.path,
        sections=(RADIO,),
    )
    radio_plan = inspect_import(
        radio_path, expected_profile_id="public", state_store=current
    )
    radio_state = build_imported_ui_state(radio_plan, current)
    assert radio_state.stations[0].name == "Radio Źródłowe"
    assert radio_state.radio_schedule_overrides is not None
    assert radio_state.radio_schedule_overrides[0]["id"] == "old-schedule"
    assert radio_state.radio_schedule_overrides[0]["name"] == "Stary plan"

    schedule_path = tmp_path / "plany.amcschedules.json"
    schedule_stage = staging_path(schedule_path)
    _core_backup(schedule_stage, (RADIO_SCHEDULES,))
    complete_export(
        schedule_stage,
        schedule_path,
        profile_id="public",
        ui_state_path=source.path,
        sections=(RADIO_SCHEDULES,),
    )
    schedule_plan = inspect_import(
        schedule_path, expected_profile_id="public", state_store=current
    )
    schedule_state = build_imported_ui_state(schedule_plan, current)
    assert schedule_state.stations[0].name == "Stare Radio"
    assert schedule_state.radio_schedule_overrides is not None
    assert schedule_state.radio_schedule_overrides[0]["name"] == "Poranek"


def test_backup_rejects_other_release_profile_before_import(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "ui")
    store.save(LiteState())
    target = tmp_path / "test.amcbackup.json"
    staged = staging_path(target)
    _core_backup(staged)
    complete_export(
        staged,
        target,
        profile_id="test",
        ui_state_path=store.path,
    )

    with pytest.raises(FullBackupError, match="innego profilu"):
        inspect_import(
            target,
            expected_profile_id="public",
            state_store=StateStore(tmp_path / "public-ui"),
        )


def test_backup_rejects_tampered_python_section(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "ui")
    store.save(_source_state())
    target = tmp_path / "kopia.amcbackup.json"
    staged = staging_path(target)
    _core_backup(staged)
    complete_export(
        staged,
        target,
        profile_id="public",
        ui_state_path=store.path,
    )
    raw = json.loads(target.read_text(encoding="utf-8"))
    raw["amcPython"]["state"]["options"]["volume"] = 99
    target.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(FullBackupError, match="integralności"):
        inspect_import(
            target,
            expected_profile_id="public",
            state_store=StateStore(tmp_path / "current"),
        )


def test_legacy_core_backup_preserves_current_ui_state(tmp_path: Path) -> None:
    path = tmp_path / "legacy.amcbackup.json"
    _core_backup(path)
    store = StateStore(tmp_path / "ui")
    store.save(LiteState(options=Options(volume=73)))
    plan = inspect_import(
        path,
        expected_profile_id="public",
        state_store=store,
    )
    restored = build_imported_ui_state(plan, store)
    assert plan.has_ui_state is False
    assert plan.ui_payload is None
    assert restored.options.volume == 73


def test_backup_rejects_unrelated_json(tmp_path: Path) -> None:
    path = tmp_path / "not-a-backup.amcbackup.json"
    path.write_text(
        '{"kind":"playlist","schemaVersion":1,"state":{}}',
        encoding="utf-8",
    )
    with pytest.raises(FullBackupError, match="nie jest kopią danych AMC"):
        inspect_import(
            path,
            expected_profile_id="public",
            state_store=StateStore(tmp_path / "ui"),
        )


def test_export_scopes_have_stable_accessible_labels_and_extensions() -> None:
    assert [scope.key for scope in BACKUP_SCOPES] == [
        "all",
        "configuration",
        "library",
        "playlists",
        "radio",
        "radioSchedules",
        "podcasts",
        "services",
    ]
    labels = [scope.label for scope in BACKUP_SCOPES]
    assert len(labels) == len(set(labels))
    assert all(label.strip() and "{" not in label for label in labels)
    assert BACKUP_SCOPES[0].default_file_name(date(2026, 10, 21)) == (
        "AMC-pelna-kopia-2026-10-21.amcbackup.json"
    )
    assert describe_sections((RADIO_SCHEDULES,)) == (
        "harmonogramy nagrywania Radia"
    )


def test_backup_commands_have_execution_and_accessible_scope_dialog() -> None:
    source = (
        Path(__file__).resolve().parents[1] / "amc_wx_lite" / "gui.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    used_actions = {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "Action"
    }
    assert {"EXPORT_BACKUP", "IMPORT_BACKUP"} <= used_actions
    assert 'dialog.SetSelection(0)' in source
    assert 'dialog.SetName("Wybierz zakres eksportu danych AMC")' in source
    assert 'child.SetName("Zakres eksportu danych AMC")' in source
