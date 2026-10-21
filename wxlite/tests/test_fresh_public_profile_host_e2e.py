"""Pierwszy zapis publicznego AMC przez rzeczywisty proces LiteHost."""

from __future__ import annotations

import json
import sqlite3
import unittest
from pathlib import Path

from amc_wx_lite.host_client import LiteHostClient
from amc_wx_lite.full_backup import ALL_SECTIONS


def test_fresh_public_profile_accepts_search_add_and_playlist_import(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[2]
    host = (
        root
        / "src"
        / "AccessibleMediaController.LiteHost"
        / "bin"
        / "Release"
        / "net8.0-windows10.0.19041.0"
        / "amc_lite_host.exe"
    )
    if not host.is_file():
        raise unittest.SkipTest("najpierw zbuduj host AMC-wx-Lite w konfiguracji Release")

    local = tmp_path / "local" / "AMC" / "profile"
    roaming = tmp_path / "roaming" / "AMC" / "profile"
    library = local / "library.db"
    podcasts = local / "podcasts.db"
    state = roaming / "state.json"
    shared_snapshot = tmp_path / "shared" / "common-data-v1.json"
    full_backup = tmp_path / "pelna-kopia.amcbackup.json"
    playlist = tmp_path / "stacje.m3u"
    forward_playlist = (
        "#EXTM3U\n"
        "#EXTINF:-1,Jedynka\nhttps://example.invalid/jedynka\n"
        "#EXTINF:-1,Radio Środek\nhttps://example.invalid/srodek\n"
        "#EXTINF:-1,Dominikanie Rzeszów\nhttps://example.invalid/dominikanie\n"
    )
    playlist.write_text(forward_playlist, encoding="utf-8")

    client = LiteHostClient(
        host,
        library_db=library,
        podcasts_db=podcasts,
        state_json=state,
        release_profile="public",
        common_data_snapshot=shared_snapshot,
    )
    try:
        client.start()
        added = client.add_radio_station(
            "Stacja z wyszukiwania",
            "https://example.invalid/search-radio",
        )
        assert added["addedCount"] == 1

        imported = client.import_playlist_to_library(str(playlist))
        assert imported["addedCount"] == 3
        assert imported["skippedCount"] == 0
        assert imported["preferredStationName"] == "Jedynka"
        station_id = imported["preferredStationId"]

        # Ponowny import musi zmienić porządek także wtedy, gdy wszystkie
        # stacje już istnieją. Dzięki temu aktualizacja naprawia playlistę,
        # która w starszej wersji została ułożona od końca.
        playlist.write_text(
            "#EXTM3U\n"
            "#EXTINF:-1,Dominikanie Rzeszów\nhttps://example.invalid/dominikanie\n"
            "#EXTINF:-1,Radio Środek\nhttps://example.invalid/srodek\n"
            "#EXTINF:-1,Jedynka\nhttps://example.invalid/jedynka\n",
            encoding="utf-8",
        )
        reversed_again = client.import_playlist_to_library(str(playlist))
        assert reversed_again["addedCount"] == 0
        assert reversed_again["preferredStationName"] == "Dominikanie Rzeszów"
        playlist.write_text(forward_playlist, encoding="utf-8")
        repaired = client.import_playlist_to_library(str(playlist))
        assert repaired["addedCount"] == 0
        assert repaired["preferredStationName"] == "Jedynka"

        sorted_result = client.set_radio_collection_sort(
            "library", "Alphabetical"
        )
        assert sorted_result["sortMode"] == "Alphabetical"

        removed = client.toggle_radio_library([station_id])
        assert removed["inLibrary"] is False and removed["changed"] == 1
        restored = client.toggle_radio_library([station_id])
        assert restored["inLibrary"] is True and restored["changed"] == 1
        favorite = client.toggle_profile_favorites("radio", [station_id])
        assert favorite["favorite"] is True and favorite["changed"] == 1
        exported = client.export_backup(full_backup, list(ALL_SECTIONS))
        assert exported["state"] == "exported"
        assert exported["radioStations"] == 4
    finally:
        client.close()

    restored_local = tmp_path / "restored-local" / "AMC" / "profile"
    restored_roaming = tmp_path / "restored-roaming" / "AMC" / "profile"
    restored_client = LiteHostClient(
        host,
        library_db=restored_local / "library.db",
        podcasts_db=restored_local / "podcasts.db",
        state_json=restored_roaming / "state.json",
        release_profile="public",
        common_data_snapshot=shared_snapshot,
    )
    try:
        restored_client.start()
        restored = restored_client.import_backup(full_backup, list(ALL_SECTIONS))
        assert restored["state"] == "imported"
        assert restored["radioStations"] == 4
        assert restored["bookmarks"] >= 0
    finally:
        restored_client.close()

    restored_payload = json.loads(
        (restored_roaming / "state.json").read_text(encoding="utf-8")
    )
    assert {
        str(item.get("name") or "")
        for item in restored_payload["radio"]["stations"]
    } == {
        "Stacja z wyszukiwania",
        "Jedynka",
        "Radio Środek",
        "Dominikanie Rzeszów",
    }

    assert library.is_file()
    assert podcasts.is_file()
    assert state.is_file()
    payload = json.loads(state.read_text(encoding="utf-8"))
    names = {str(item.get("name") or "") for item in payload["radio"]["stations"]}
    assert names == {
        "Stacja z wyszukiwania",
        "Jedynka",
        "Radio Środek",
        "Dominikanie Rzeszów",
    }
    jedynka = next(item for item in payload["radio"]["stations"] if item["name"] == "Jedynka")
    assert jedynka["isInLibrary"] is True
    assert jedynka["isFavorite"] is True
    assert (
        payload["sessionNavigation"]["sessions"]["radio"]
        ["collectionSortModes"]["Biblioteka"]
        == "Alphabetical"
    )

    names_by_id = {item["id"]: item["name"] for item in payload["radio"]["stations"]}
    connection = sqlite3.connect(library)
    try:
        stored = [
            row[0]
            for row in connection.execute(
                "SELECT item_id FROM library_added_order "
                "WHERE session_id = 'radio' ORDER BY ordinal"
            )
        ]
    finally:
        connection.close()
    visible_import = [names_by_id[item_id] for item_id in reversed(stored)][:3]
    assert visible_import == ["Jedynka", "Radio Środek", "Dominikanie Rzeszów"]
