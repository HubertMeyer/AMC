"""End-to-end witness for F2/Delete profile mutations through the C# host."""

from __future__ import annotations

import json
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

from amc_wx_lite.host_client import LiteHostClient


ROOT = Path(__file__).resolve().parents[2]
HOST = (
    ROOT
    / "src"
    / "AccessibleMediaController.LiteHost"
    / "bin"
    / "Release"
    / "net8.0-windows10.0.19041.0"
    / "amc_lite_host.exe"
)


def _library(path: Path, media: Path) -> None:
    with closing(sqlite3.connect(path)) as db:
        db.create_collation(
            "AMC_PL",
            lambda left, right: (left.casefold() > right.casefold())
            - (left.casefold() < right.casefold()),
        )
        db.executescript(
            """
            CREATE TABLE local_items(
                id TEXT PRIMARY KEY, title TEXT NOT NULL,
                has_custom_title INTEGER NOT NULL, path TEXT NOT NULL,
                is_favorite INTEGER NOT NULL DEFAULT 0,
                is_in_library INTEGER NOT NULL DEFAULT 1,
                is_in_queue INTEGER NOT NULL DEFAULT 0,
                is_play_next INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE INDEX ix_local_items_title ON local_items(title COLLATE AMC_PL);
            CREATE TABLE bookmarks(
                id TEXT PRIMARY KEY, session_id TEXT, item_id TEXT,
                item_title TEXT);
            CREATE TABLE excluded_paths(ordinal INTEGER PRIMARY KEY, path TEXT NOT NULL);
            CREATE TABLE playback_history(session_id TEXT, ordinal INTEGER, item_id TEXT);
            CREATE TABLE custom_order(ordinal INTEGER, item_id TEXT);
            CREATE TABLE favorite_order(session_id TEXT, ordinal INTEGER, item_id TEXT);
            CREATE TABLE favorite_added_order(session_id TEXT, ordinal INTEGER, item_id TEXT);
            CREATE TABLE library_added_order(session_id TEXT, ordinal INTEGER, item_id TEXT);
            CREATE TABLE library_custom_order(session_id TEXT, ordinal INTEGER, item_id TEXT);
            CREATE TABLE queue_order(session_id TEXT, ordinal INTEGER, item_id TEXT);
            CREATE TABLE queue_play_next_order(session_id TEXT, ordinal INTEGER, item_id TEXT);
            CREATE TABLE queue_regular_order(session_id TEXT, ordinal INTEGER, item_id TEXT);
            CREATE TABLE playlists(
                id TEXT PRIMARY KEY, session_id TEXT NOT NULL,
                ordinal INTEGER NOT NULL, name TEXT NOT NULL COLLATE AMC_PL,
                created_utc_ticks INTEGER NOT NULL);
            CREATE UNIQUE INDEX ix_playlists_session_name
                ON playlists(session_id, name COLLATE AMC_PL);
            CREATE TABLE playlist_items(
                playlist_id TEXT NOT NULL, ordinal INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                PRIMARY KEY(playlist_id, ordinal),
                UNIQUE(playlist_id, item_id),
                FOREIGN KEY(playlist_id) REFERENCES playlists(id) ON DELETE CASCADE);
            """
        )
        db.execute(
            "INSERT INTO local_items(id,title,has_custom_title,path) VALUES(?,?,0,?)",
            ("local-1", "Stara nazwa", str(media)),
        )
        db.execute(
            "INSERT INTO local_items(id,title,has_custom_title,path) VALUES(?,?,0,?)",
            ("local-2", "Drugi plik", str(media)),
        )
        db.execute(
            "INSERT INTO bookmarks(id,session_id,item_id,item_title) VALUES('b','local','local-1','Stara nazwa')"
        )
        db.execute(
            "INSERT INTO playback_history VALUES('podcasts',0,'episode-1')"
        )
        db.execute(
            "INSERT INTO playback_history VALUES('podcasts',1,'episode-kept')"
        )
        for table in (
            "queue_order", "queue_regular_order", "queue_play_next_order"
        ):
            db.execute(
                f"INSERT INTO {table} VALUES('podcasts',0,'episode-queue')"
            )
        db.execute(
            "INSERT INTO playlists VALUES('p-local','local',0,'Stara lista',638000000000000000)"
        )
        db.execute("INSERT INTO playlist_items VALUES('p-local',0,'local-1')")
        db.execute(
            "INSERT INTO playlists VALUES('p-radio','radio',0,'Stacje',638000000000000001)"
        )
        db.execute("INSERT INTO playlist_items VALUES('p-radio',0,'radio-1')")
        db.commit()


def _podcasts(path: Path) -> None:
    payload = {
        "Id": "podcast-1",
        "Title": "Stary podcast",
        "HasCustomTitle": False,
        "FeedUrl": "https://example.invalid/feed",
        "IsInLibrary": True,
    }
    with closing(sqlite3.connect(path)) as db:
        db.executescript(
            """
            CREATE TABLE podcast_subscriptions(
                id TEXT PRIMARY KEY, title TEXT, is_in_library INTEGER,
                payload_json TEXT);
            CREATE TABLE podcast_episodes(
                id TEXT PRIMARY KEY, subscription_id TEXT,
                is_in_queue INTEGER, is_play_next INTEGER,
                payload_json TEXT);
            CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            """
        )
        db.execute(
            "INSERT INTO podcast_subscriptions VALUES(?,?,1,?)",
            ("podcast-1", "Stary podcast", json.dumps(payload)),
        )
        db.execute(
            "INSERT INTO podcast_episodes VALUES(?,?,1,1,?)",
            (
                "episode-queue",
                "podcast-1",
                json.dumps({"IsInQueue": True, "IsPlayNext": True}),
            ),
        )
        db.commit()


def test_profile_edits_go_through_the_real_host() -> None:
    assert HOST.exists(), "Najpierw zbuduj LiteHost w konfiguracji Release"
    temporary_root = ROOT / ".tmp-tests"
    temporary_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="amc-profile-mutations-", dir=temporary_root
    ) as raw:
        root = Path(raw)
        media = root / "nagranie.mp3"
        media.write_bytes(b"test")
        library = root / "library.db"
        podcasts = root / "podcasts.db"
        state = root / "state.json"
        _library(library, media)
        _podcasts(podcasts)
        state.write_text(
            json.dumps(
                {
                    "radio": {
                        "stations": [
                            {
                                "id": "radio-1",
                                "name": "Stare radio",
                                "streamUrl": "https://example.invalid/old",
                                "isInLibrary": True,
                                "isFavorite": True,
                            }
                        ],
                        "recordingSchedules": [],
                    }
                }
            ),
            encoding="utf-8",
        )

        client = LiteHostClient(
            HOST, library_db=library, podcasts_db=podcasts, state_json=state
        )
        try:
            client.start()
            client.rename_library_item("local-1", "Nazwa biblioteczna")
            renamed = client.rename_local_file("local-1", "nowy plik")
            assert Path(renamed["path"]).name == "nowy plik.mp3"
            assert Path(renamed["path"]).exists()
            client.rename_podcast_subscription("podcast-1", "Nowy podcast")
            removed_library = client.toggle_podcast_library(["podcast-1"])
            assert removed_library == {"added": False, "requested": 1, "changed": 1}
            restored_library = client.toggle_podcast_library(["podcast-1"])
            assert restored_library == {"added": True, "requested": 1, "changed": 1}
            removed_queue = client.toggle_podcast_queue(["episode-queue"])
            assert removed_queue["added"] is False
            assert removed_queue["changed"] == 1
            restored_queue = client.toggle_podcast_queue(["episode-queue"])
            assert restored_queue["added"] is True
            assert restored_queue["changed"] == 1
            made_next = client.toggle_podcast_queue(
                ["episode-queue"], play_next=True
            )
            assert made_next["added"] is True
            assert made_next["changed"] == 1
            radio_edit = client.edit_radio_station(
                "radio-1", "Nowe radio", "https://example.invalid/new"
            )
            assert radio_edit["streamChanged"] is True
            local_favorite = client.toggle_profile_favorites(
                "files", ["local-1", "local-2"]
            )
            assert local_favorite == {
                "favorite": True,
                "requested": 2,
                "changed": 2,
                "titles": ["Nazwa biblioteczna", "Drugi plik"],
            }
            radio_favorite = client.toggle_profile_favorites("radio", ["radio-1"])
            assert radio_favorite["favorite"] is False
            assert radio_favorite["changed"] == 1
            radio_favorite = client.toggle_profile_favorites("radio", ["radio-1"])
            assert radio_favorite["favorite"] is True
            assert radio_favorite["changed"] == 1
            playlist_snapshot = client.profile_playlists("files")
            assert playlist_snapshot == {
                "sessionId": "local",
                "playlists": [
                    {
                        "playlistId": "p-local",
                        "name": "Stara lista",
                        "createdUtcTicks": 638000000000000000,
                        "itemIds": ["local-1"],
                    }
                ],
            }
            saved_playlists = client.replace_profile_playlists(
                "files",
                [
                    {
                        "playlistId": "p-local",
                        "name": "Nowa nazwa listy",
                        "createdUtcTicks": 638000000000000000,
                        "itemIds": ["local-2"],
                    },
                    {
                        "playlistId": "p-new",
                        "name": "Druga lista",
                        "createdUtcTicks": 638000000000000002,
                        "itemIds": ["local-1", "local-2"],
                    },
                ],
            )
            assert saved_playlists == {
                "sessionId": "local",
                "saved": 2,
                "items": 3,
            }
            client.remove_profile_items("files", "library", ["local-1"])
            client.remove_profile_items(
                "podcasts", "podcastLibrary", ["podcast-1"]
            )
            client.remove_profile_items(
                "podcasts", "podcastHistory", ["episode-1"]
            )
            client.remove_profile_items(
                "podcasts", "podcastQueue", ["episode-queue"]
            )
            client.remove_profile_items("radio", "library", ["radio-1"])
        finally:
            client.close()

        with closing(sqlite3.connect(library)) as db:
            row = db.execute(
                "SELECT title,path,is_favorite,is_in_library FROM local_items WHERE id='local-1'"
            ).fetchone()
            assert row == (
                "Nazwa biblioteczna",
                str(root / "nowy plik.mp3"),
                1,
                0,
            )
            assert db.execute(
                "SELECT item_id FROM favorite_order WHERE session_id='local' ORDER BY ordinal"
            ).fetchall() == [("local-1",), ("local-2",)]
            assert db.execute(
                "SELECT item_id FROM favorite_added_order WHERE session_id='local' ORDER BY ordinal"
            ).fetchall() == [("local-1",), ("local-2",)]
            assert (root / "nowy plik.mp3").exists(), (
                "Delete ma usunąć rekord z Biblioteki, ale zostawić plik na dysku"
            )
            excluded = db.execute(
                "SELECT path FROM excluded_paths"
            ).fetchone()
            assert excluded == (str(root / "nowy plik.mp3"),)
            bookmark = db.execute(
                "SELECT item_title FROM bookmarks WHERE id='b'"
            ).fetchone()
            assert bookmark == ("Nazwa biblioteczna",)
            podcast_history = db.execute(
                "SELECT item_id FROM playback_history "
                "WHERE session_id='podcasts' ORDER BY ordinal"
            ).fetchall()
            assert podcast_history == [("episode-kept",)]
            for table in (
                "queue_order", "queue_regular_order", "queue_play_next_order"
            ):
                assert db.execute(
                    f"SELECT item_id FROM {table} WHERE session_id='podcasts'"
                ).fetchall() == []
            assert db.execute(
                "SELECT id,name FROM playlists WHERE session_id='local' ORDER BY ordinal"
            ).fetchall() == [
                ("p-local", "Nowa nazwa listy"),
                ("p-new", "Druga lista"),
            ]
            assert db.execute(
                "SELECT playlist_id,item_id FROM playlist_items "
                "WHERE playlist_id IN ('p-local','p-new') ORDER BY playlist_id,ordinal"
            ).fetchall() == [
                ("p-local", "local-2"),
                ("p-new", "local-1"),
                ("p-new", "local-2"),
            ]
            assert db.execute(
                "SELECT name FROM playlists WHERE id='p-radio'"
            ).fetchone() == ("Stacje",), "Zapis sesji lokalnej nie może ruszyć Radia"
        with closing(sqlite3.connect(podcasts)) as db:
            title, in_library, payload = db.execute(
                "SELECT title,is_in_library,payload_json FROM podcast_subscriptions WHERE id='podcast-1'"
            ).fetchone()
            assert title == "Nowy podcast"
            assert in_library == 0
            assert json.loads(payload)["HasCustomTitle"] is True
            assert json.loads(payload)["IsInLibrary"] is False
            queue_row = db.execute(
                "SELECT is_in_queue,is_play_next,payload_json "
                "FROM podcast_episodes WHERE id='episode-queue'"
            ).fetchone()
            assert queue_row[:2] == (0, 0)
            queue_payload = json.loads(queue_row[2])
            assert queue_payload["IsInQueue"] is False
            assert queue_payload["IsPlayNext"] is False
        radio = json.loads(state.read_text(encoding="utf-8"))["radio"]["stations"][0]
        assert radio["name"] == "Nowe radio"
        assert radio["streamUrl"] == "https://example.invalid/new"
        assert radio["isInLibrary"] is False
        assert radio["isFavorite"] is False
