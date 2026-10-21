"""Pierwszy zapis publicznego AMC przez rzeczywisty proces LiteHost."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from amc_wx_lite.host_client import LiteHostClient


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
    playlist = tmp_path / "stacje.m3u"
    playlist.write_text(
        "#EXTM3U\n#EXTINF:-1,Stacja z playlisty\n"
        "https://example.invalid/imported-radio\n",
        encoding="utf-8",
    )

    client = LiteHostClient(
        host,
        library_db=library,
        podcasts_db=podcasts,
        state_json=state,
        release_profile="public",
    )
    try:
        client.start()
        added = client.add_radio_station(
            "Stacja z wyszukiwania",
            "https://example.invalid/search-radio",
        )
        assert added["addedCount"] == 1

        imported = client.import_playlist_to_library(str(playlist))
        assert imported["addedCount"] == 1
        assert imported["skippedCount"] == 0
    finally:
        client.close()

    assert library.is_file()
    assert podcasts.is_file()
    assert state.is_file()
    payload = json.loads(state.read_text(encoding="utf-8"))
    names = {str(item.get("name") or "") for item in payload["radio"]["stations"]}
    assert names == {"Stacja z wyszukiwania", "Stacja z playlisty"}
