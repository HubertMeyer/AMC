from __future__ import annotations

from dataclasses import replace

from amc_wx_lite.list_model import Row
from amc_wx_lite.navigation import (
    Announce,
    LibraryView,
    Navigator,
    OpenSpotifyCollectionView,
    OpenSpotifyContainer,
    PlaySpotifyItem,
    SessionId,
    ShowSpotifyRelations,
    View,
)
from amc_wx_lite.search_catalog import SESSION_LABELS
from amc_wx_lite.shortcuts import (
    Action,
    Chord,
    SPOTIFY_SUPPORTED_ACTIONS,
    resolve,
)


def _artist() -> Row:
    return Row(
        "private-artist-row", "Wykonawca", "artist",
        service_id="spotify:artist:secret", service_kind="artist",
    )


def _album(number: int = 1) -> Row:
    return Row(
        f"private-album-row-{number}", f"Album {number}", "album",
        service_id=f"spotify:album:secret-{number}", service_kind="album",
        artist_name="Wykonawca",
        related_artist_service_id="spotify:artist:secret",
        related_artist_name="Wykonawca",
    )


def _track(number: int = 1) -> Row:
    return Row(
        f"private-track-row-{number}", f"Utwór {number}", "track",
        service_id=f"spotify:track:secret-{number}", service_kind="track",
        artist_name="Wykonawca",
        related_album_service_id="spotify:album:secret",
        related_album_title="Album użytkowy",
        related_artist_service_id="spotify:artist:secret",
        related_artist_name="Wykonawca",
    )


def test_one_spotify_session_has_user_labels_and_contextual_arrow_shortcuts() -> None:
    assert SESSION_LABELS[SessionId.SPOTIFY] == "Spotify"
    assert resolve(
        Chord("7", ctrl=True), player_view=False, radio_session=False
    ) is Action.SESSION_SPOTIFY
    assert resolve(
        Chord("Right"), player_view=False, radio_session=False,
        spotify_session=True,
    ) is Action.SPOTIFY_RELATIONS
    assert resolve(
        Chord("Left"), player_view=False, radio_session=False,
        spotify_session=True,
    ) is Action.QUICK_INFORMATION
    assert {
        Action.VIEW_LIBRARY,
        Action.VIEW_HISTORY,
        Action.SEARCH_CURRENT,
        Action.SPOTIFY_RELATIONS,
    } <= SPOTIFY_SUPPORTED_ACTIONS


def test_enter_on_artist_opens_overview_then_backspace_restores_exact_focus() -> None:
    nav = Navigator()
    nav.active = SessionId.SPOTIFY
    rows = [_album(), _artist(), _album(2)]
    nav.apply_spotify_view("Biblioteka Spotify", rows)
    nav.session.model.select_id("private-artist-row")

    events = nav.activate_selected()

    assert events == [Announce("Wykonawca, Wykonawca, 2 pozycje")]
    assert [row.title for row in nav.session.model.rows] == ["Albumy", "Utwory"]
    section = nav.activate_selected()[0]
    assert isinstance(section, OpenSpotifyContainer)
    assert section.kind == "artist"
    assert section.section == "albums"

    assert nav.go_to_parent() == []
    assert nav.session.model.selected_id == "private-artist-row"
    assert nav.session.model.selected_row == rows[1]


def test_album_playlist_and_podcast_enter_request_their_real_container() -> None:
    for kind, title in (
        ("album", "Album"),
        ("playlist", "Playlista"),
        ("podcast", "Podcast"),
    ):
        nav = Navigator()
        nav.active = SessionId.SPOTIFY
        row = Row(
            f"private-{kind}", title, kind,
            service_id=f"spotify:{kind}:secret", service_kind=kind,
        )
        nav.apply_spotify_view("Biblioteka Spotify", [row])

        events = nav.activate_selected()

        assert events == [OpenSpotifyContainer(
            item_id=f"private-{kind}",
            service_id=f"spotify:{kind}:secret",
            title=title,
            kind=kind,
        )]


def test_track_enter_keeps_read_only_list_and_container_back_restores_rows() -> None:
    nav = Navigator()
    nav.active = SessionId.SPOTIFY
    albums = [_album(), _album(2)]
    nav.apply_spotify_view("Biblioteka Spotify", albums)
    nav.session.model.select_id(albums[1].item_id)
    target = nav.activate_selected()[0]
    tracks = [_track(), _track(2)]
    nav.apply_spotify_container(target, "Album 2", tracks)
    nav.session.model.select_id(tracks[1].item_id)

    events = nav.activate_selected()

    assert events == [PlaySpotifyItem(
        tracks[1].item_id, tracks[1].title, tracks[1].service_id or "", "track"
    )]
    assert nav.session.view is View.LIST
    assert nav.session.model.selected_row == tracks[1]

    assert nav.close_spotify_preview() == []
    assert nav.session.library_view is LibraryView.SPOTIFY_LIBRARY
    assert nav.session.model.selected_row == albums[1]


def test_collection_root_enter_opens_named_view_and_back_restores_focus() -> None:
    nav = Navigator()
    nav.active = SessionId.SPOTIFY
    rows = [
        Row(
            "spotify-collection:liked",
            "Polubione utwory",
            "folder",
            service_id="liked",
            service_kind="spotifyCollection",
        ),
        Row(
            "spotify-collection:artists",
            "Wykonawcy",
            "folder",
            service_id="artists",
            service_kind="spotifyCollection",
        ),
    ]
    nav.apply_spotify_view("Biblioteka Spotify", rows)
    nav.session.model.select_id(rows[1].item_id)

    intent = nav.activate_selected()[0]

    assert intent == OpenSpotifyCollectionView(
        rows[1].item_id, "artists", "Wykonawcy"
    )
    nav.apply_spotify_collection_view(intent, "Wykonawcy Spotify", [_artist()])
    assert nav.go_to_parent() == []
    assert nav.session.model.selected_row == rows[1]


def test_episode_enter_and_right_arrow_return_to_its_podcast() -> None:
    nav = Navigator()
    nav.active = SessionId.SPOTIFY
    episode = Row(
        "private-episode", "Odcinek", "episode",
        service_id="spotify:episode:secret", service_kind="episode",
        related_podcast_service_id="spotify:show:secret",
        related_podcast_title="Podcast użytkowy",
    )
    nav.apply_spotify_view("Biblioteka Spotify", [episode])

    menu = nav.spotify_relations()[0]
    assert isinstance(menu, ShowSpotifyRelations)
    assert [choice.label for choice in menu.choices] == ["Przejdź do podcastu"]
    assert nav.activate_spotify_relation(menu.choices[0]) == [OpenSpotifyContainer(
        item_id="private-episode:related-podcast",
        service_id="spotify:show:secret",
        title="Podcast użytkowy",
        kind="podcast",
    )]
    assert isinstance(nav.activate_selected()[0], PlaySpotifyItem)


def test_left_and_right_arrow_speak_only_labels_and_keep_focus() -> None:
    nav = Navigator()
    nav.active = SessionId.SPOTIFY
    track = _track()
    nav.apply_spotify_view("Biblioteka Spotify", [track])
    before = nav.session.model.selected_id

    information = nav.spotify_information()[0]
    relations = nav.spotify_relations()[0]

    assert isinstance(information, Announce)
    assert isinstance(relations, ShowSpotifyRelations)
    spoken = " ".join((
        information.text,
        relations.title,
        *(choice.label for choice in relations.choices),
    ))
    assert nav.session.model.selected_id == before
    assert "secret" not in spoken
    assert "spotify:" not in spoken
    assert "SessionId" not in spoken
    assert "Row(" not in spoken


def test_visible_source_order_drives_next_item_and_confirmation() -> None:
    nav = Navigator()
    nav.active = SessionId.SPOTIFY
    tracks = [_track(), _track(2)]
    nav.apply_spotify_view("Biblioteka Spotify", tracks)
    nav.activate_selected()
    nav.note_spotify_playback_started(tracks[0].item_id, tracks[0].title)

    events = nav.step_playback_source(True)

    assert events == [PlaySpotifyItem(
        tracks[1].item_id,
        tracks[1].title,
        tracks[1].service_id or "",
        "track",
        previous_item_id=tracks[0].item_id,
        previous_title=tracks[0].title,
    )]
    assert nav.session.now_playing_id == tracks[0].item_id
    nav.note_spotify_playback_started(tracks[1].item_id, tracks[1].title)
    assert nav.session.now_playing_id == tracks[1].item_id


def test_session_switch_preserves_nested_list_and_focus() -> None:
    nav = Navigator()
    nav.active = SessionId.SPOTIFY
    album = _album()
    nav.apply_spotify_view("Biblioteka Spotify", [album])
    target = nav.activate_selected()[0]
    tracks = [_track(), _track(2)]
    nav.apply_spotify_container(target, "Album", tracks, preferred_id=tracks[1].item_id)

    nav.switch_session(SessionId.FILES)
    event = nav.switch_session(SessionId.SPOTIFY)[0]

    assert event == Announce("Spotify, lista, Utwór 2")
    assert nav.session.library_view is LibraryView.SPOTIFY_CONTAINER
    assert nav.session.model.selected_row == tracks[1]


def test_search_result_opens_without_adding_it_to_the_saved_library() -> None:
    nav = Navigator()
    nav.active = SessionId.SPOTIFY
    saved = _album()
    nav.apply_spotify_view("Biblioteka Spotify", [saved])
    online = Row(
        "private-online", "Nowa playlista", "playlist",
        service_id="spotify:playlist:online-secret", service_kind="playlist",
    )

    events = nav.open_spotify_search_result(online)

    assert events == [OpenSpotifyContainer(
        "private-online", "spotify:playlist:online-secret", "Nowa playlista", "playlist"
    )]
    assert nav.session.model.rows == [saved]
    assert nav.session.spotify_history == []


def test_unplayable_row_refuses_once_without_exposing_private_identity() -> None:
    nav = Navigator()
    nav.active = SessionId.SPOTIFY
    row = replace(
        _track(),
        activation_message="Ten materiał nie jest obecnie dostępny do odtworzenia",
    )
    nav.apply_spotify_view("Biblioteka Spotify", [row])

    events = nav.activate_selected()

    assert events == [Announce("Ten materiał nie jest obecnie dostępny do odtworzenia")]
    assert "secret" not in events[0].text
    assert nav.session.view is View.LIST
