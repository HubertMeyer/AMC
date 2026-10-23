from __future__ import annotations

import unittest

from amc_wx_lite import menu_model
from amc_wx_lite.command_palette import entries_for_session
from amc_wx_lite.list_model import ListModel, Row
from amc_wx_lite.navigation import (
    LibraryView,
    Navigator,
    OpenPodcastView,
    OpenYouTubeBroadcasts,
    PlayMedia,
    SessionId,
)
from amc_wx_lite.shortcuts import Action, Chord, describe, describe_action, resolve
from amc_wx_lite.youtube_live import (
    YouTubeLivePayloadError,
    broadcast_rows,
    dynamic_live_url,
)


class YouTubeLiveTests(unittest.TestCase):
    def test_dynamic_station_accepts_channel_id_and_handle(self) -> None:
        self.assertEqual(
            dynamic_live_url("https://www.youtube.com/channel/UC_test-123/videos"),
            "https://www.youtube.com/channel/UC_test-123/live",
        )
        self.assertEqual(
            dynamic_live_url("https://youtube.com/%40Parafia/videos"),
            "https://www.youtube.com/@Parafia/live",
        )

    def test_dynamic_station_rejects_video_and_foreign_hosts(self) -> None:
        for address in (
            "https://www.youtube.com/watch?v=abc",
            "https://youtube.com.example.org/channel/UC_test/videos",
        ):
            with self.subTest(address=address):
                with self.assertRaises(YouTubeLivePayloadError):
                    dynamic_live_url(address)

    def test_rows_expose_only_intentional_labels_and_public_addresses(self) -> None:
        rows = broadcast_rows(
            {
                "items": [
                    {
                        "title": "  Msza\r\nna żywo ",
                        "channelTitle": "Parafia",
                        "pageUrl": "https://www.youtube.com/watch?v=PublicznyAdres",
                        "state": "live",
                        "actualStartUtc": "2026-10-23T16:00:00Z",
                        "technicalId": "NIE-WOLNO-MOWIC",
                    },
                    {
                        "title": "Msza wieczorna",
                        "pageUrl": "https://www.youtube.com/watch?v=Zaplanowana",
                        "state": "upcoming",
                        "scheduledStartUtc": "2026-10-25T17:00:00Z",
                    },
                ]
            },
            subscription_id="wewnetrzny-rodzic",
        )
        self.assertEqual([row.title for row in rows], ["Msza na żywo", "Msza wieczorna"])
        self.assertEqual([row.service_kind for row in rows], ["youtubeLive", "youtubeUpcoming"])
        self.assertTrue(rows[0].detail.startswith("na żywo"))
        self.assertTrue(rows[1].detail.startswith("zaplanowana"))
        self.assertEqual(rows[0].path, rows[0].url)
        self.assertEqual(rows[0].parent_id, "wewnetrzny-rodzic")
        spoken = " ".join(ListModel(rows).text_for(0, column) for column in range(3))
        self.assertNotIn("NIE-WOLNO-MOWIC", spoken)

    def test_navigation_opens_refreshes_plays_and_returns_to_channel(self) -> None:
        navigator = Navigator()
        navigator.switch_session(SessionId.PODCASTS)
        navigator.apply_podcast_library([
            Row(
                "subscription-one",
                "Parafia św. Ignacego",
                "podcast",
                url="https://www.youtube.com/channel/UC_test/videos",
                service_kind="youtubeChannel",
            )
        ])

        request = navigator.open_youtube_broadcasts()[0]
        self.assertIsInstance(request, OpenYouTubeBroadcasts)
        self.assertEqual(request.subscription_id, "subscription-one")
        rows = broadcast_rows(
            {"items": [{
                "title": "Msza",
                "pageUrl": "https://www.youtube.com/watch?v=MszaLive",
                "state": "live",
            }]},
            subscription_id="subscription-one",
        )
        announcement = navigator.apply_youtube_broadcasts(
            "subscription-one", "Parafia św. Ignacego", rows
        )[0]
        self.assertEqual(navigator.session.library_view, LibraryView.YOUTUBE_BROADCASTS)
        self.assertIn("na żywo 1", announcement.text)

        refresh = navigator.open_youtube_broadcasts(force_refresh=True)[0]
        self.assertTrue(refresh.force_refresh)
        play = next(
            item for item in navigator.activate_selected() if isinstance(item, PlayMedia)
        )
        self.assertEqual(play.source, "https://www.youtube.com/watch?v=MszaLive")
        navigator.back_to_list()
        back = navigator.go_to_parent()[0]
        self.assertIsInstance(back, OpenPodcastView)
        self.assertEqual(back.preferred_id, "subscription-one")

    def test_f5_and_command_surfaces_share_one_contract(self) -> None:
        self.assertIs(
            resolve(
                Chord("T", ctrl=True),
                player_view=False,
                radio_session=False,
                podcast_session=True,
                youtube_channel=True,
                youtube_account_available=True,
            ),
            Action.YOUTUBE_BROADCASTS,
        )
        self.assertIs(
            resolve(
                Chord("Y", ctrl=True),
                player_view=False,
                radio_session=False,
                podcast_session=True,
                youtube_channel=True,
            ),
            Action.ADD_YOUTUBE_LIVE_STATION,
        )
        self.assertIsNone(
            resolve(
                Chord("T", ctrl=True),
                player_view=False,
                radio_session=False,
                podcast_session=True,
                youtube_channel=True,
                youtube_account_available=False,
            )
        )
        self.assertIsNone(
            resolve(
                Chord("Y", ctrl=True),
                player_view=False,
                radio_session=False,
                podcast_session=True,
                youtube_channel=False,
            )
        )
        self.assertIs(
            resolve(
                Chord("F5"),
                player_view=False,
                radio_session=False,
                podcast_session=True,
                youtube_broadcasts=True,
            ),
            Action.REFRESH_YOUTUBE_BROADCASTS,
        )
        self.assertIs(
            resolve(
                Chord("F5"),
                player_view=False,
                radio_session=False,
                podcast_session=True,
            ),
            Action.REFRESH_PODCAST,
        )
        actions = {
            Action.YOUTUBE_BROADCASTS,
            Action.REFRESH_YOUTUBE_BROADCASTS,
            Action.ADD_YOUTUBE_LIVE_STATION,
        }
        menu_items = {
            item.action: item
            for menu in menu_model.menus_for_session(
                SessionId.PODCASTS,
                youtube_account_available=True,
            )
            for item in menu.items
            if item.action in actions
        }
        palette = {
            entry.action: entry
            for entry in entries_for_session(
                SessionId.PODCASTS,
                youtube_account_available=True,
            )
            if entry.action in actions
        }
        self.assertEqual(set(menu_items), actions)
        self.assertEqual(set(palette), actions)
        self.assertEqual(
            menu_items[Action.REFRESH_YOUTUBE_BROADCASTS].shortcut,
            palette[Action.REFRESH_YOUTUBE_BROADCASTS].shortcut,
        )
        self.assertEqual(
            menu_items[Action.YOUTUBE_BROADCASTS].shortcut,
            palette[Action.YOUTUBE_BROADCASTS].shortcut,
        )
        self.assertEqual(
            menu_items[Action.ADD_YOUTUBE_LIVE_STATION].shortcut,
            palette[Action.ADD_YOUTUBE_LIVE_STATION].shortcut,
        )
        self.assertEqual(menu_items[Action.YOUTUBE_BROADCASTS].shortcut, "Ctrl+T")
        self.assertEqual(menu_items[Action.ADD_YOUTUBE_LIVE_STATION].shortcut, "Ctrl+Y")
        help_entries = dict(describe("Podcasty i YouTube", actions))
        self.assertEqual(
            help_entries["Ctrl+T"],
            "Pokaż transmisje na żywo i zaplanowane kanału YouTube",
        )
        self.assertEqual(
            help_entries["Ctrl+Y"],
            "Dodaj kanał jako dynamiczną stację YouTube na żywo",
        )
        for action in actions:
            self.assertNotIn("Action.", palette[action].label)
            self.assertNotIn("{", palette[action].label)
            self.assertTrue(describe_action(action))


if __name__ == "__main__":
    unittest.main()
