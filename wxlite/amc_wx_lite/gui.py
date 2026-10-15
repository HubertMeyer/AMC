"""Okno AMC-wx-Lite: NATYWNE kontrolki wxPython.

Zasady dostepnosci przyjete tutaj (i dlaczego):

* ``wx.ListCtrl`` w trybie ``LC_REPORT`` -- ZWYKLA natywna lista Windows, tak
  jak w SARA i WinZappie. Teksty siedza w kontrolce, a przy zmianie danych
  aktualizujemy TYLKO faktycznie zmienione wiersze i pola (``list_sync``).
  Czytnik ekranu dostaje zwykla, natywna liste z rolami i nazwami -- dziala
  bez dodatku NVDA i z Narratorem. Wirtualizacja (``LC_VIRTUAL`` +
  ``OnGetItemText``) ZOSTALA USUNIETA: jej cache tekstu dawal czytnikowi
  stara nazwe z nowym licznikiem, a ``SetItemCount`` przestawial cala liste
  nawet wtedy, gdy dane sie nie zmienily.
* Strzalki, Home/End, Tab i pisanie-po-pierwszej-literze naleza do KONTROLKI.
  Nie przejmujemy ich. Przejmujemy tylko to, co ma wlasne znaczenie w AMC
  (Enter, Backspace, F6, Escape, Spacja, Ctrl+cyfra...).
* Fokusu NIE ustawiamy co tick. ``SetFocus`` wola sie wylacznie przy ZMIANIE
  widoku - inaczej czytnik przerywalby sobie mowe w kolko.
* Odswiezamy TYLKO zmienione wiersze/etykiety, nigdy calej listy bez potrzeby.
* Jedna brama komunikatow: ``Announcer``. Zadnego sleepMode, zadnego zapisu
  do appModules NVDA.

Czego tu nie ma swiadomie: WebView2, Sonos ani uslug startowych. Plany sa
edytowane w natywnym oknie wxPython i wykonywane przez host C#. Pelny AMC
zostaje nietkniety: wxPython zapisuje wlasne, kompletne nadpisanie planow.
"""

from __future__ import annotations

import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Callable

import wx

from .async_gate import BackgroundRunner, StaleResultGate
from .audio_clip import (
    AudioEditSettingsReadError,
    AudioClipContext,
    AudioClipFormatChoice,
    AudioClipSelection,
    AudioClipTrackEndIntent,
    append_clip_confirmation_text,
    clip_context_from_status,
    describe_backup_outcome,
    format_choices_from_payload,
    format_clip_time,
    resolve_keep_audio_edit_backups,
    remove_clip_confirmation_text,
    resolve_clip_end_position,
    restore_clip_selection,
    suggested_clip_file_name,
    update_clip_selections,
)
from .audio_output import (
    AudioOutputChoice,
    adjacent_available_choice,
    audio_output_selection_message,
    choices_from_payload,
    effective_output_device_id,
    read_profile_outputs,
)
from .collation import HostCollation
from .command_palette import (
    CommandPaletteEntry,
    count_label as command_count_label,
    entries_for_session as command_entries_for_session,
    filter_entries as filter_command_entries,
)
from .host_client import HostError, HostUnavailable, LiteHostClient, default_host_path
from . import nvda_bridge
from .library_source import LibrarySnapshot, LibrarySource, degradation_notice
from . import list_sync
from . import list_filter
from .list_model import (
    ListModel,
    Row,
    rows_from_folder_payload,
    rows_from_queue_status,
    rows_from_stations,
)
from . import menu_model
from .playlist_dialog import (
    PlaylistMembershipDialog,
    PlaylistPayloadError,
    choices_from_payload as playlist_choices_from_payload,
)
from . import profile_presets
from .navigation import (
    ActivateWiiMDevice,
    ActivateSonosGroup,
    Announce,
    LIBRARY_VIEW_FOLDERS,
    LibraryView,
    Navigator,
    OpenFolder,
    OpenLibraryView,
    OpenPodcastAggregateView,
    OpenWiiMDevicePresets,
    OpenWiiMNetworkStreams,
    OpenPodcastPlaylistView,
    OpenPodcastView,
    OpenQueueView,
    OpenSpotifyCollectionView,
    OpenSpotifyContainer,
    OpenSpotifyView,
    OpenTidalContainer,
    OpenTidalView,
    OpenSonosView,
    PlayFromQueue,
    PlayQueueAt,
    PlayStation,
    PlayMedia,
    PlaySpotifyItem,
    PlayTidalContainer,
    PlayTidalTrack,
    PlayTrack,
    PlayWiiMNetworkStream,
    PlaySonosMaterial,
    SessionId,
    ShowSpotifyRelations,
    ShowTidalRelations,
    TransientNavigationSnapshot,
    View,
    view_context,
)
from .shortcuts import (
    Action,
    Chord,
    GLOBAL_VIEW_SHORTCUTS,
    PRESET_SHORTCUTS,
    SPOTIFY_SUPPORTED_ACTIONS,
    TIDAL_SUPPORTED_ACTIONS,
    SONOS_SUPPORTED_ACTIONS,
    WIIM_SUPPORTED_ACTIONS,
    describe,
    keyboard_help_announcement,
    preset_slot,
    resolve,
)
from .wiim_source import (
    WiiMOptionChoice,
    WiiMPresetChoice,
    WiiMPayloadError,
    device_rows as wiim_device_rows,
    network_stream_edit_info as wiim_network_stream_edit_info,
    network_stream_rows as wiim_network_stream_rows,
    now_playing_label as wiim_now_playing_label,
    option_choices as wiim_option_choices,
    preset_choices as wiim_preset_choices,
    snapshot as wiim_snapshot,
)
from .sonos_source import (
    SonosPayloadError,
    library_rows as sonos_library_rows,
    material_rows as sonos_material_rows,
    own_stream_edit_info as sonos_own_stream_edit_info,
    response_message as sonos_response_message,
    target_rows as sonos_target_rows,
    now_playing_label as sonos_now_playing_label,
    snapshot as sonos_snapshot,
)
from .profile_layout import resolve_layout
from .podcast_source import (
    PAGE_SIZE as PODCAST_PAGE_SIZE,
    PodcastDescription,
    PodcastGlobalSettings,
    PodcastProfileError,
    PodcastSource,
    SORT_ADDED_NEWEST,
    SORT_ALPHABETICAL,
    SORT_CUSTOM,
    subscription_rows,
)
from .paging import load_more_row, requested_count
from .quick_info import (
    HOST_ERROR_MESSAGE,
    QUICK_INFO_OP,
    QUICK_INFO_STREAM,
    quick_info_failure,
    quick_info_plan,
    quick_info_reply,
    read_cached_information,
)
from .search_catalog import (
    SESSION_LABELS,
    SearchEntry,
    SearchResultAction,
    record_query as add_search_history,
    search as search_entries,
)
from .search_sources import SearchCollection, SearchSources
from .speaker_content import (
    SPEAKER_SESSIONS,
    speaker_information_failure,
    speaker_information_plan,
    speaker_information_reply,
    speaker_information_text,
    speaker_search_entries,
    speaker_search_scope_label,
)
from .remote_search import (
    entries_from_payload,
    merge_saved_and_remote,
    radio_entries_from_payload,
)
from .radio_activity import (
    STATE_POSITION_LABELS,
    activity_cue_wav,
    state_position_index,
    state_position_value,
)
from . import radio_recognition
from .transport_parity import (
    DEFAULT_TEMPLATES,
    PLAYBACK_RATES,
    SUGGESTED_CUSTOM_SEEK_SECONDS,
    TEMPLATE_KEYS,
    TEMPLATE_LABELS,
    TRACK_END_MARGIN_SECONDS,
    MessagePolicy,
    PercentAnnouncement,
    apply_message_overrides,
    clamp_playback_rate,
    describe_custom_seek_length,
    format_clock,
    format_playback_rate,
    load_message_policy,
    next_playback_rate,
    parse_custom_seek_length,
    playback_rate_choice_label,
    resolve_custom_seek_seconds,
    resolve_detailed_hints,
    seek_percent_value,
    seek_step_seconds,
    time_announcement,
)
from .transient_preview_policy import (
    TRANSIENT_PREVIEW_ACTIONS,
    is_transient_preview_available,
    load_global_transient_previews,
    resolve_global_transient_previews,
    transient_preview_unavailable_message,
)
from .local_resume_policy import (
    load_remember_local_playback_positions,
    resolve_remember_local_playback_positions,
)
from . import session_options
from . import session_order
from .radio_source import RadioSource
from .radio_schedule_dialogs import RadioScheduleEditorDialog, RadioSchedulesDialog
from . import radio_schedule_settings
from .radio_recording import (
    active_recording_rows,
    current_station_recording_label,
    format_duration,
    preferences_with_overrides,
    recording_history_from_amc_state,
    recording_history_payload_from_event,
    recording_history_rows,
    recent_recording_history,
    station_activity_rows,
)
from .state_store import LiteState, Station, StationList, StateStore
from .spotify_source import (
    SpotifyContainerPayloadError,
    account_summary_from_payload as spotify_account_summary_from_payload,
    container_result_from_payload as spotify_container_result_from_payload,
    history_rows as spotify_history_rows,
    record_history_row as record_spotify_history_row,
    root_result_from_payload as spotify_root_result_from_payload,
)
from .tidal_source import (
    TidalContainerPayloadError,
    TidalProfileError,
    TidalSource,
    VIEW_FAVORITES as TIDAL_VIEW_FAVORITES,
    VIEW_LIBRARY as TIDAL_VIEW_LIBRARY,
    VIEW_PLAYLISTS as TIDAL_VIEW_PLAYLISTS,
    container_result_from_host,
    queue_payload as tidal_queue_payload,
    queue_rows as tidal_queue_rows,
)
from .version_info import is_main_window_title, window_title

APP_NAME = "AMC Python"
TEMPO_LABELS = {1: "Mowa – Speedy", 2: "Muzyka – Signalsmith", 0: "Dotychczasowy – SoundTouch"}
RADIO_FORMAT_CHOICES = (
    ("MP3", "Mp3"),
    ("M4A, dźwięk AAC", "Aac"),
    ("FLAC, bezstratny", "Flac"),
    ("Oryginalny strumień, bez konwersji", "Original"),
    ("WAV, bez kompresji", "Wav"),
)
RADIO_BITRATE_CHOICES = (96, 128, 160, 192, 256, 320)
RADIO_TIMESHIFT_CHOICES = (10, 20, 30, 60, 120, 180, 360, 720)


def _append_frontend_log(store: StateStore, message: str) -> None:
    """Zapisz techniczny blad startu bez pokazywania go jako nazwy kontrolki.

    ``pythonw.exe`` nie ma konsoli, dlatego sam komunikat na pasku stanu nie
    wystarcza do rozpoznania regresji po ponownym uruchomieniu. Dziennik jest
    prywatny dla AMC Python i nigdy nie trafia do etykiet ani list NVDA.
    """

    try:
        log_dir = store.directory / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
        with (log_dir / "frontend.log").open("a", encoding="utf-8") as stream:
            stream.write(f"{timestamp} {message.strip()}\n")
    except OSError:
        # Dziennik diagnostyczny nie moze sam zablokowac startu interfejsu.
        pass


def radio_timeshift_label(minutes: int) -> str:
    """Pelna, jednoznaczna etykieta bufora dla kontrolki i NVDA."""
    storage = "w pamięci" if minutes <= 24 else "na dysku"
    if minutes == 60:
        duration = "1 godzina"
    elif minutes > 60 and minutes % 60 == 0:
        hours = minutes // 60
        unit = "godziny" if hours in (2, 3, 4) else "godzin"
        duration = f"{hours} {unit}"
    else:
        duration = f"{minutes} minut"
    return f"{duration}, {storage}"


def _windows_main_window() -> int:
    """Uchwyt poprzedniego głównego okna, bez szukania po procesach Pythona."""
    if os.name != "nt":
        return 0
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32  # type: ignore[attr-defined]
        matches: list[int] = []
        callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

        @callback_type
        def visit(handle, _parameter):
            length = int(user32.GetWindowTextLengthW(handle))
            if length <= 0:
                return True
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(handle, buffer, len(buffer))
            if is_main_window_title(buffer.value):
                matches.append(int(handle))
                return False
            return True

        user32.EnumWindows(visit, 0)
        return matches[0] if matches else 0
    except Exception:
        return 0


def _activate_window_handle(handle: int) -> bool:
    """Przywróć, zmaksymalizuj i wysuń wskazane okno na pierwszy plan."""
    if os.name != "nt" or not handle:
        return False
    try:
        import ctypes

        user32 = ctypes.windll.user32  # type: ignore[attr-defined]
        user32.ShowWindow(handle, 3)  # SW_MAXIMIZE
        user32.SetForegroundWindow(handle)
        return True
    except Exception:
        return False


def _request_previous_instance_close() -> bool:
    """Wyślij poprzedniej wersji zwykłe WM_CLOSE; nigdy nie zabijaj procesu."""
    handle = _windows_main_window()
    if not handle or os.name != "nt":
        return False
    try:
        import ctypes

        return bool(ctypes.windll.user32.PostMessageW(handle, 0x0010, 0, 0))  # type: ignore[attr-defined]
    except Exception:
        return False


def _wait_for_previous_instance(checker, *, timeout_seconds: float = 8.0) -> bool:
    """True oznacza, że poprzednia instancja zwolniła blokadę."""
    deadline = time.monotonic() + max(0.0, timeout_seconds)
    while checker.IsAnotherRunning() and time.monotonic() < deadline:
        time.sleep(0.1)
    return not checker.IsAnotherRunning()


def _present_main_window(frame: wx.Frame) -> None:
    """Jedna droga startu i ponownego przywołania głównego okna."""
    frame.Maximize(True)
    frame.Show(True)
    frame.Raise()
    frame.SetFocus()
    try:
        _activate_window_handle(int(frame.GetHandle()))
    except Exception:
        pass

YOUTUBE_EXPORT_CSV_FILTER = 0
YOUTUBE_EXPORT_OPML_FILTER = 1
YOUTUBE_EXPORT_WILDCARD = (
    "CSV kanałów, zgodny z Google Takeout, NewPipe i FreeTube (*.csv)|*.csv|"
    "OPML dla kanałów i playlist, do czytników RSS (*.opml)|*.opml"
)

RADIO_EXPORT_M3U_FILTER = 0
RADIO_EXPORT_JSON_FILTER = 1
RADIO_EXPORT_WILDCARD = (
    "Playlisty M3U (*.m3u)|*.m3u|"
    "Ulubione VRadio (*.json)|*.json|"
    "Wszystkie pliki (*.*)|*.*"
)


def youtube_export_path_for_filter(path: str, filter_index: int) -> str:
    """Nadaj rozszerzenie odpowiadające formatowi wybranemu w dialogu.

    Natywny dialog Windows potrafi zachować poprzednie ``.csv`` w nazwie,
    mimo że użytkownik przeszedł na filtr OPML. Format wybiera jawnie pole
    „Typ pliku”, więc to jego wybór ma pierwszeństwo przed starym rozszerzeniem.
    """
    suffix = ".opml" if filter_index == YOUTUBE_EXPORT_OPML_FILTER else ".csv"
    return str(Path(path).with_suffix(suffix))


def radio_export_path_for_filter(path: str, filter_index: int) -> str:
    """Uzgodnij rozszerzenie z formatem wybranym w natywnym dialogu."""
    candidate = Path(path)
    if filter_index == RADIO_EXPORT_JSON_FILTER:
        return str(candidate.with_suffix(".json"))
    if filter_index == RADIO_EXPORT_M3U_FILTER:
        return str(candidate.with_suffix(".m3u"))
    return str(candidate if candidate.suffix else candidate.with_suffix(".m3u"))

# Mapowanie klawiszy wx -> wlasne nazwy z shortcuts.py. Trzymamy to w JEDNYM
# miejscu, zeby tablica skrotow nie zalezala od wx (da sie ja testowac w WSL).
_SPECIAL_KEYS = {
    wx.WXK_RETURN: "Return",
    wx.WXK_NUMPAD_ENTER: "Return",
    wx.WXK_BACK: "Back",
    wx.WXK_ESCAPE: "Escape",
    wx.WXK_SPACE: "Space",
    wx.WXK_DELETE: "Delete",
    wx.WXK_F1: "F1",
    wx.WXK_F2: "F2",
    wx.WXK_F6: "F6",
    wx.WXK_LEFT: "Left",
    wx.WXK_RIGHT: "Right",
    wx.WXK_UP: "Up",
    wx.WXK_DOWN: "Down",
    wx.WXK_TAB: "Tab",
    wx.WXK_HOME: "Home",
    wx.WXK_END: "End",
    wx.WXK_PAGEUP: "Prior",
    wx.WXK_PAGEDOWN: "Next",
}

# Pelne wx udostepnia te stale, ale lekki zastepnik testowy nie musi. Budujemy
# rozszerzenie warunkowo, zeby test dostepnosci GUI nie musial udawac calej
# klawiatury numerycznej tylko dlatego, ze presety obsluguja ja produkcyjnie.
for _wx_name, _key_name in (
    *((f"WXK_NUMPAD{digit}", str(digit)) for digit in range(10)),
    ("WXK_NUMPAD_SUBTRACT", "-"),
    ("WXK_NUMPAD_ADD", "+"),
):
    if hasattr(wx, _wx_name):
        _SPECIAL_KEYS[getattr(wx, _wx_name)] = _key_name


def chord_from_event(event: wx.KeyEvent) -> Chord:
    code = event.GetKeyCode()
    name = _SPECIAL_KEYS.get(code)
    if name is None:
        if 32 < code < 127:
            name = chr(code).upper()
        else:
            name = f"#{code}"
    return Chord(key=name, ctrl=event.ControlDown(), shift=event.ShiftDown(), alt=event.AltDown())


def format_time(seconds: float | None) -> str:
    """Czas po polsku, krotko - tak go czyta czytnik ekranu."""
    if seconds is None or seconds < 0:
        return "nieznany"
    total = int(seconds)
    minutes, secs = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours} godz {minutes} min {secs} s"
    if minutes:
        return f"{minutes} min {secs} s"
    return f"{secs} s"


def player_time_label(position: float | None, duration: float | None) -> str:
    """Etykieta czasu w oknie odtwarzacza, dokladnie jak w oryginale.

    ``MainWindow.xaml.cs:2643-2647``: gdy czas trwania jest znany, tekst to
    ``{pozycja} z {calosc}`` w formacie ``FormatTime`` (czyli ``m:ss``); gdy
    nie jest -- sama pozycja; a bez odtwarzania zdanie "Stan czasu nieznany".
    Wariant wx mial tu wlasny format ("30 s / 3 min 51 s"), wiec ten sam ekran
    wygladal inaczej niz w AMC.
    """
    if position is None:
        return "Stan czasu nieznany"
    if duration:
        return f"{format_clock(position)} z {format_clock(duration)}"
    return format_clock(position)


#: Komunikat Ctrl+C. ``MainWindow.xaml.cs:24372``. Byl zmierzony jako
#: poprawny (dokladnie jeden na gest, takze przy powtorzeniu) -- nie ruszamy go.
COPIED_NAME_MESSAGE = "Skopiowano nazwę"


def format_item_count(count: int) -> str:
    """Polska odmiana licznika elementow zgodna z pelnym AMC."""
    if count == 1:
        return "1 element"
    last_two_digits = count % 100
    last_digit = count % 10
    suffix = (
        "elementy"
        if 2 <= last_digit <= 4 and not 12 <= last_two_digits <= 14
        else "elementów"
    )
    return f"{count} {suffix}"


def format_file_count(count: int) -> str:
    """Polska odmiana licznika plikow zgodna z pelnym AMC."""
    if count == 1:
        return "1 plik"
    last_two_digits = count % 100
    last_digit = count % 10
    suffix = (
        "pliki"
        if 2 <= last_digit <= 4 and not 12 <= last_two_digits <= 14
        else "plików"
    )
    return f"{count} {suffix}"


def is_local_path(source: str | None) -> bool:
    """``TryGetLocalPath`` -- MainWindow.xaml.cs:5378-5390, regula za regula.

    Oryginal:

        if (string.IsNullOrWhiteSpace(source)
            || Uri.TryCreate(source, UriKind.Absolute, out var uri) && !uri.IsFile)
            return false;
        if (!Path.IsPathFullyQualified(source)) return false;

    czyli trzy odrzucenia: pusty tekst; absolutny URI, ktory NIE jest ``file:``
    (np. ``http://``); sciezka niepelna (wzgledna). Co wazne, oryginal TUTAJ
    NIE sprawdza istnienia pliku -- to osobna regula, patrz ``_file_drop_path``.

    Nie dodajemy nic poza tym -- z JEDNYM jawnym wyjatkiem: ``file:`` URI.
    Oryginal przepuszcza go przez pierwszy warunek (``uri.IsFile`` jest prawda),
    ale zaraz potem odrzuca na ``Path.IsPathFullyQualified("file:///D:/a.mp3")``
    == ``false``, czyli de facto NIE uznaje go za lokalny. My uznajemy i
    sprowadzamy do sciezki (``local_path_from_source``). To nasze rozszerzenie,
    nie przepisana linia oryginalu.
    """
    if not source or not source.strip():
        return False
    source = source.strip()
    scheme = source.split(":", 1)[0].lower() if ":" in source else ""
    # Jednoliterowy "schemat" to litera dysku Windows (``D:\...``), nie URI.
    if len(scheme) > 1 and scheme.isalpha():
        if scheme != "file":
            return False
        return True
    # ``IsPathFullyQualified``: UNC, dysk z separatorem albo korzen POSIX
    # (testy chodza w WSL, wiec sciezka POSIX tez jest w pelni kwalifikowana).
    if source.startswith("\\\\") or source.startswith("//"):
        return True
    if len(source) >= 3 and source[1] == ":" and source[2] in "\\/":
        return True
    return source.startswith("/")


#: ``Preferred DropEffect`` -- liczby shella Windows, nie nasze wymysly.
#: ``DROPEFFECT_COPY = 1``, ``DROPEFFECT_MOVE = 2``. Oryginal wola
#: ``SetData("Preferred DropEffect", BitConverter.GetBytes(2))`` TYLKO przy
#: wycinaniu (``MainWindow.xaml.cs:25303``); strona kopiowania (:24781-24783)
#: nie ustawia tego formatu wcale, a jego BRAK znaczy dla shella kopiowanie.
DROPEFFECT_COPY = 1
DROPEFFECT_MOVE = 2


def file_copy_clipboard_payload(path: str) -> dict:
    """Co ma trafic do schowka przy KOPIOWANIU pliku.

    Odpowiada ``CopyItemLocations`` (``MainWindow.xaml.cs:24778-24787``):
    tekst sciezki ORAZ ``CF_HDROP``, bez ``Preferred DropEffect``.
    """
    return {"text": path, "file_path": path, "preferred_drop_effect": None}


def file_cut_clipboard_payload(path: str) -> dict:
    """Co ma trafic do schowka przy WYCINANIU pliku.

    Odpowiada ``CutLocalFilesForExternalMove``
    (``MainWindow.xaml.cs:25300-25303``): to samo co przy kopiowaniu PLUS
    ``Preferred DropEffect`` = MOVE. Bez tego trzeciego formatu Explorer
    zrobilby KOPIE, a uzytkownik uslyszalby "gotowy do przeniesienia".
    """
    return {"text": path, "file_path": path, "preferred_drop_effect": DROPEFFECT_MOVE}


def local_path_from_source(source: str) -> str:
    """Sprowadza ``file:`` URI do zwyklej sciezki; reszte oddaje bez zmian.

    UWAGA na granice tej funkcji wobec oryginalu. ``TryGetLocalPath``
    (``MainWindow.xaml.cs:5378``) NIE konwertuje ``file:`` URI -- oddaje
    ``localPath = source`` i poleca go dalej ``Path.IsPathFullyQualified``,
    ktory dla ``file:///D:/a.mp3`` zwraca ``false``. Czyli oryginal takiego
    zrodla w ogole nie uznaje za lokalne. Ta konwersja to NASZE rozszerzenie,
    nie doslowne 1:1; opisujemy ja tak wprost, zeby nikt nie przypisal jej
    oryginalowi.

    Istotne jest, zeby nie zgubic nazwy serwera. ``urlparse`` wklada ja do
    ``netloc``, nie do ``path``, wiec ``file://serwer/udzial/a.mp3`` bez tego
    dawalo ``/udzial/a.mp3`` -- sciezke na BIEZACYM dysku, nie na udziale.
    """
    source = (source or "").strip()
    if source.lower().startswith("file:"):
        from urllib.parse import unquote, urlparse

        parsed = urlparse(source)
        path = unquote(parsed.path)
        host = unquote(parsed.netloc)
        # ``file://serwer/udzial/a.mp3`` -> ``\\serwer\udzial\a.mp3``.
        # ``localhost`` to umowna nazwa maszyny biezacej, nie udzial sieciowy.
        if host and host.lower() != "localhost":
            return "\\\\" + host + path.replace("/", "\\")
        # ``file:///D:/a.mp3`` -> ``D:/a.mp3``
        if len(path) >= 3 and path[0] == "/" and path[2] == ":":
            path = path[1:]
        return path
    return source


def copied_address_message(row: Row, *, file_copied: bool = False) -> str:
    """Komunikat Ctrl+Shift+C opisujacy to, co NAPRAWDE trafia do schowka.

    Dla stacji zostaje "Skopiowano bezpośredni adres"
    (``MainWindow.xaml.cs:24400``): adres strumienia to tekst i komunikat
    niczego wiecej nie obiecuje.

    Dla pliku slowa zaleza od DANYCH, nie od zamiaru:

    ``file_copied=True``
        schowek dostal ``wx.FileDataObject`` (``CF_HDROP``) obok tekstu, czyli
        wklejenie w menedzerze plikow utworzy kopie. Dopiero wtedy wolno
        powiedziec "Skopiowano plik i pełną ścieżkę"
        (``MainWindow.xaml.cs:24785``).

    ``file_copied=False``
        sciezki nie ma na dysku (albo nie jest lokalna), wiec file drop
        wskazywalby w pustke -- idzie SAM tekst i komunikat mowi tylko o nim.
        Tak samo jak przed ta zmiana: komunikat nigdy nie obiecuje czynnosci,
        ktorej program nie wykonal.
    """
    if row.kind in {"station", "wiimNetworkStream", "sonosOwnStream"}:
        return "Skopiowano bezpośredni adres"
    return "Skopiowano plik i pełną ścieżkę" if file_copied else "Skopiowano pełną ścieżkę"


#: ``winUser.EVENT_SYSTEM_ALERT`` (``source/winUser.py:355``). NIE uzywamy go
#: na polu statusu -- patrz komentarz w ``Announcer``.
EVENT_SYSTEM_ALERT = 0x0002

#: ``winUser.EVENT_OBJECT_LIVEREGIONCHANGED`` (``source/winUser.py:396``).
EVENT_OBJECT_LIVEREGIONCHANGED = 0x8019

#: ``winUser.OBJID_CLIENT`` i ``CHILDID_SELF`` (``source/winUser.py:416, 410``).
#: Trzymamy je TUTAJ, a nie bierzemy z ``wx``: to stale MSAA, a dzieki temu
#: brak atrybutu w ``wx`` nie moze sie przebrac za "czytnik milczy".
OBJID_CLIENT = -4
CHILDID_SELF = 0


def _notify_win_event(event: int, hwnd: int, object_id: int, child_id: int) -> None:
    """``user32.NotifyWinEvent`` -- zwykle API MSAA, bez dodatku do czytnika.

    Na nie-Windows (testy w WSL) nie ma czego wolac; ``Announcer`` dostaje
    wtedy wlasna funkcje powiadamiania i tu nie zaglada.
    """
    import ctypes

    ctypes.windll.user32.NotifyWinEvent(event, hwnd, object_id, child_id)


def transport_button_label(*, playing: bool, preparing: bool = False) -> str:
    """Nazwa przycisku transportu: CZYNNOSC, ktora wykona nacisniecie.

    Dawne "Pauza/wznow" wymienialo oba warianty naraz, wiec czytnik mowil
    zawsze to samo i nie bylo wiadomo, co sie stanie. Slownictwo i warunek
    bierzemy ze zwyklego AMC, bez nowej rodziny nazw:

        ``MainWindow.xaml.cs:2560``
        ``PlayerPlayPauseButton.Content =``
        ``    preparing ? "Anuluj" : session.IsPlaying ? "Wstrzymaj" : "Odtwórz";``

    ``&`` to klawisz dostepu wx (odpowiednik ``_`` w XAML).
    """
    if preparing:
        return "&Anuluj"
    return "&Wstrzymaj" if playing else "&Odtwórz"


def transport_confirmation(*, paused: bool) -> str:
    """Krotkie potwierdzenie po Spacji: stan, ktory JUZ nastapil.

    Etykieta mowi o przyszlosci ("Wstrzymaj"), potwierdzenie o terazniejszosci
    ("Wstrzymano") -- inaczej czytnik dwa razy powtarza to samo slowo i nie
    wiadomo, czy czynnosc sie udala. Jedno slowo, bo to potwierdzenie gestu,
    nie opis stanu odtwarzacza.
    """
    return "Wstrzymano" if paused else "Odtwarzanie"


class Announcer:
    """JEDNA brama krotkich komunikatow. Widoczny status + mowa czytnika.

    DLACZEGO NIE ``EVENT_SYSTEM_ALERT`` (tak bylo i bylo CICHO):

    NVDA tlumaczy ``EVENT_SYSTEM_ALERT`` na zdarzenie ``"alert"``
    (``source/IAccessibleHandler/internalWinEventHandler.py:37``), a jego
    obsluga ODRZUCA obiekt, ktory nie ma roli alertu:

        ``source/NVDAObjects/IAccessible/__init__.py:2025-2028``
        ``def event_alert(self):``
        ``    if self.role != controlTypes.Role.ALERT:``
        ``        # Ignore alert events on objects that aren't alerts.``
        ``        return``

    Pole statusu to ``wx.StaticText``, czyli okno klasy ``Static`` z rola
    ``ROLE_SYSTEM_STATICTEXT`` -> nakladka ``StaticText``
    (tamze:2842), a nie ``Role.ALERT`` (``IAccessibleHandler/__init__.py:119``
    daje ALERT tylko dla ``ROLE_SYSTEM_ALERT``). Wywolanie bylo poprawne,
    obiekt byl zly -- NVDA wracal w pierwszej linii i milczal. Stad
    "schowek poprawny, a mowy nie bylo".

    DLACZEGO LIVE REGION DZIALA:

        ``source/NVDAObjects/__init__.py:1238-1254``
        ``def event_liveRegionChange(self):``
        ``    name = self.name``
        ``    if name: ... ui.message(name, ...)``

    Zdarzenie ``EVENT_OBJECT_LIVEREGIONCHANGED`` nie sprawdza ROLI -- wymaga
    tylko NIEPUSTEJ nazwy, a nazwa ``wx.StaticText`` to jego tekst, ktory
    ustawiamy ponizej. ``ui.message`` wymawia DOKLADNIE ten tekst: bez slowa
    "alert" i bez nazwy regionu, czyli krotko.

    To ta sama intencja, co w zwyklym AMC: ``AccessibleStatusTextBlock``
    wysyla notyfikacje z TRESCIA, a peer bierze nazwe z tekstu
    (``Controls/AccessibleStatusTextBlock.cs:26-37, 44-48``).

    Pozostale zasady bez zmian: jawnie powtorzone pytanie (Ctrl+E dwa razy)
    dostaje odpowiedz dwa razy, ale tekstu nie przepisujemy bez potrzeby;
    JEDEN komunikat to JEDNO zdarzenie (dwa to podwojna zapowiedz); okno w
    tle aktualizuje status, lecz nie wchodzi w slowo obcej aplikacji.
    """

    def __init__(
        self,
        status_field: wx.StaticText,
        *,
        notify=_notify_win_event,
        status_bar: "NativeStatusBar | None" = None,
    ) -> None:
        self._status = status_field
        self._notify = notify
        # Pasek stanu jest OPCJONALNY: stare wywolania i atrapy w testach nadal
        # maja dzialac, a sama zapowiedz nie moze zalezec od dodatku.
        self._status_bar = status_bar
        self._capture_active = False
        self._captured_message = ""

    def begin_capture(self) -> None:
        """Przechwyć natychmiastową odpowiedź dla dodatku NVDA.

        Dodatek sam wypowie odpowiedź. Lokalny live region nie może w tym
        samym czasie mówić drugi raz tego samego tekstu.
        """
        self._capture_active = True
        self._captured_message = ""

    def end_capture(self) -> str:
        message = self._captured_message
        self._capture_active = False
        self._captured_message = ""
        return message

    def show(self, text: str) -> str:
        """Zaktualizuj dostepny tekst bez wymuszania wypowiedzi NVDA."""
        text = (text or "").strip()
        if not text:
            return ""
        if self._status.GetLabel() != text:
            self._status.SetLabel(text)
        self._status.SetName(text)
        return text

    def say(self, text: str) -> None:
        text = self.show(text)
        if not text:
            return
        if self._capture_active:
            self._captured_message = text
            return
        # Kanal zapowiedzi i natywny pasek odtwarzania sa rozdzielne, tak jak
        # w glownym AMC. Kopiowanie tutaj ostatniego komunikatu nadpisywalo
        # wiarygodny status i dlatego NVDA+End czytal np. tylko
        # "Odtwarzacz, Radio Poznan" zamiast stacji, parametrow i utworu.
        # Nazwe ustawiamy ZAWSZE, nawet gdy tekst sie nie zmienil: wlasnie ja
        # czyta ``event_liveRegionChange``, a powtorzone pytanie ma odpowiedziec.
        owner = wx.GetTopLevelParent(self._status)
        if owner is not None and not owner.IsActive():
            return
        try:
            self._notify(
                EVENT_OBJECT_LIVEREGIONCHANGED,
                int(self._status.GetHandle()),
                OBJID_CLIENT,
                CHILDID_SELF,
            )
        except OSError:
            # Zapowiedz jest DODATKIEM do czynnosci: gdy samo MSAA padnie,
            # kopiowanie albo pauza i tak sie wykonaly, a tekst statusu zostaje
            # do odczytania na zadanie. Zadnego ``sleep`` ani ponowien.
            #
            # Lapiemy WYLACZNIE ``OSError`` (tyle potrafi zglosic
            # ``NotifyWinEvent``). Szerokie ``except Exception`` ukrywalo tu
            # wlasna literowke w nazwie stalej -- czyli dokladnie te ciche
            # milczenie czytnika, ktore naprawiamy.
            pass


class NativeStatusBar:
    """Trzyma aktualny status w NATYWNYM pasku stanu okna -- dla ``NVDA+End``.

    PO CO, skoro ``Announcer`` juz mowi
    -----------------------------------
    ``Announcer`` to kanal ZDARZENIA: mowi w chwili zmiany. ``NVDA+End`` to
    kanal NA ZADANIE: czyta PASEK STANU. NVDA szuka go natywnie i gdy nie
    znajdzie kontrolki paska stanu, sieka tytul okna -- stad zgloszone
    "wieczorne" z "Uspokojenie wieczorne". ``wx.StaticText`` z nazwa
    "Komunikaty" nie jest paskiem stanu (rola ``STATICTEXT``), wiec nie da
    sie go odczytac na zadanie. Zostaje wiec oba kanaly obok siebie.

    Zwykle AMC trzyma je dokladnie tak samo rozdzielnie:
    ``Controls/AccessibleStatusTextBlock.cs`` to kanal mowy, a
    ``Controls/AccessiblePlaybackStatusStrip.cs`` + ``MainWindow.xaml:20-22``
    to natywny ``StatusStrip`` do odczytu na zadanie, jawnie poza fokusem
    (``Focusable="False"``, ``IsTabStop="False"``, ``Selectable, false``):
    "It must remain available to NVDA+End, but it must never become the
    keyboard target".

    ZADNEGO zdarzenia czytnika -- to regula oryginalu
    ------------------------------------------------
    ``AccessiblePlaybackStatusStrip.SpokenText`` celowo nie wysyla
    notyfikacji o zmianie nazwy: "Do not emit a NameChange event every
    second: ... that event can move NVDA's navigator away from the player".
    Dlatego ta klasa tylko PRZECHOWUJE tekst -- nie wola
    ``_notify_win_event`` i nie udaje live regionu. Mowa zostaje tam, gdzie
    byla zmierzona jako dzialajaca: w ``Announcer``.

    Dodatkowo nie piszemy tego samego tekstu dwa razy. Status aktualizuje sie
    takze z zegara transportu, a ``SetStatusText`` przemalowuje pasek --
    powtorzony tekst to czysty koszt bez zmiany tresci.
    """

    def __init__(self, bar) -> None:
        self._bar = bar
        self._text = ""

    def show(self, text: str) -> None:
        text = (text or "").strip()
        if not text or text == self._text:
            return
        self._text = text
        self._bar.SetStatusText(text, 0)

    @property
    def text(self) -> str:
        return self._text


#: Sentinel "kontekst jeszcze nieznany". ``None`` nie nadaje sie na te role:
#: widok Folderow ma ``library_view=None`` i to POPRAWNY kontrakt, wiec
#: ``None`` jest zwyklym, legalnym kontekstem widoku.
_BRAK_KONTEKSTU = object()


class MediaListCtrl(wx.ListCtrl):
    """ZWYKLA natywna lista Windows z aktualizacja tylko tego, co sie zmienilo.

    DLACZEGO NIE JEST JUZ WIRTUALNA. Kontrolka byla ``LC_VIRTUAL`` i oddawala
    tekst na zadanie przez ``OnGetItemText``. Kazde odswiezenie widoku szlo
    wtedy jedna droga: ``SetItemCount`` + ``RefreshItems(0, n-1)`` -- rowniez
    gdy dane sie nie zmienily, bo ``_sync_views`` konczy KAZDY przebieg
    ``_run`` (takze po samym komunikacie, Ctrl+C czy ticku statusu). Na 2476
    wierszach bylo to odswiezenie calej listy na kazde nacisniecie klawisza.

    Zatwierdzony kierunek: zwykle natywne listy (jak w SARA i WinZapp, ktore
    uzytkownik wskazal jako dzialajace dobrze) plus aktualizacje przyrostowe.
    Kontrolka trzyma teksty u siebie, a ``sync_rows`` dopisuje, usuwa, przenosi
    i nadpisuje WYLACZNIE to, co sie rozni.

    Co ZOSTAJE bez zmian: te same trzy kolumny, te same ``item_id`` z
    ``ListModel`` i ta sama trwala kontrolka (bez ``Destroy``/rekreacji HWND --
    ta droga zostala zmierzona i wycofana). Drzewo dostepnosci wierszy nalezy
    do natywnego SysListView32; nie instalujemy na nim ``wx.Accessible``.
    Strzalki, Home/End i pisanie-po-pierwszej-literze naleza do kontrolki;
    na zwyklej liscie dziala to natywnie, bez naszego udzialu.

    Czego ten kod NIE robi: nie dotyka czytnika ekranu. Mniej operacji na
    kontrolce to mniej zdarzen a11y, ale dowodem mowy jest zywy NVDA.
    """

    def __init__(self, parent: wx.Window, model: ListModel, label: str,
                 state: object | None = None) -> None:
        super().__init__(
            parent,
            # Bez ``LC_SINGLE_SEL``: pelne AMC pozwala zaznaczyc Shift/Ctrl
            # kilka wierszy, a polecenia schowka dzialaja na calym wyborze.
            # SysListView32 zachowuje przy tym zwykla obsluge klawiatury i
            # role dostepnosci -- nie budujemy wlasnego mechanizmu wyboru.
            style=wx.LC_REPORT | wx.BORDER_SUNKEN,
        )
        self.model = model
        #: STAN SESJI, ktorej liste pokazujemy (``navigation.SessionState``).
        #: Sluzy WYLACZNIE do odczytu tozsamosci widoku w ``_view_context``;
        #: kontrolka nic w nim nie zmienia. ``None`` = brak wiedzy o widoku, co
        #: wylacza pelna podmiane (bezpieczny domysl: przyrostowo).
        self.state = state
        self.InsertColumn(0, "Nazwa", width=420)
        self.InsertColumn(1, "Rodzaj", width=120)
        self.InsertColumn(2, "Szczegoly", width=260)
        #: Stan POKAZANY w kontrolce. Jedyne zrodlo prawdy do porownania --
        #: odczytywanie tekstow z ``GetItemText`` przy kazdym odswiezeniu
        #: oznaczaloby 7428 wywolan API na liste 2476 wierszy.
        self._shown: list[list_sync.RowText] = []
        #: KONTEKST WIDOKU, ktory ``_shown`` naprawde przedstawia (sentinel, bo
        #: ``None`` jest LEGALNYM kontekstem -- widok Folderow ma
        #: ``library_view=None``). Pelna podmiana listy bramkuje sie o roznice
        #: miedzy tym polem a kontekstem liczonym w ``sync_rows``.
        self._shown_context: object = _BRAK_KONTEKSTU
        # ListModel.replace zawsze tworzy nowa liste, takze dla identycznych danych.
        self._shown_rows_source = self.model.rows
        #: Czy trwa NASZA aktualizacja. Wstawianie wierszy i ``SetItemState``
        #: powoduja, ze kontrolka wysyla ``EVT_LIST_ITEM_SELECTED`` tak samo jak
        #: przy ruchu uzytkownika. Bez tej bramki przejsciowy indeks (np. 0 po
        #: wstawieniu pierwszego wiersza) wszedlby do modelu JAKO NOWY WYBOR i
        #: skasowal wybor uzytkownika. Czytane przez ``MediaListFrame``.
        self.updating = False
        #: TEKST FILTRA obowiazujacy dla tej listy. Ustawia go okno przed
        #: ``sync_rows`` (jedno pole dla wszystkich list, jak ``FilterBox``).
        #: Pusty = zachowanie dokladnie takie jak przed dodaniem filtra.
        self.filter_query: str = ""
        # Natywne SysListView32 MUSI pozostac wlascicielem calego drzewa
        # dostepnosci. Wczesniejsza nakladka ``wx.Accessible`` podawala nazwe
        # samej listy, ale na rzeczywistym NVDA zaslaniala jej dzieci: strzalki
        # przesuwaly fokus i Enter dzialal, a czytnik nie dostawal nazw wierszy.
        # ``SetLabel`` ustawia tekst natywnego okna, ``SetName`` zachowuje
        # jawna nazwe po stronie wx; nie podmieniamy providera MSAA/UIA.
        self.SetLabel(label)
        self.SetName(label)
        self._base_accessible_label = label
        self._accessible_label = label

    def set_accessible_label(self, label: str) -> None:
        """Ustaw nazwę bieżącego widoku bez wymiany natywnej listy.

        Nazwa opisuje to, co użytkownik rzeczywiście ogląda (np. „Playlista”
        albo „Nagrywane”), a nie tylko sesję „Stacje radiowe”.  Nie dokładamy
        własnego providera dostępności: dzieci i pozycję „1 z N” nadal podaje
        natywny SysListView32.
        """
        label = (label or "").strip()
        if not label or label == self._accessible_label:
            return
        self.SetLabel(label)
        self.SetName(label)
        self._accessible_label = label

    # ------------------------------------------------------------ aktualizacja

    def sync_rows(self) -> None:
        """Dociagnij kontrolke do modelu. Brak zmian = ZERO operacji.

        To jest cala zatwierdzona zasada w jednym miejscu: plan wylicza
        ``list_sync``, my go tylko nakladamy. Gdy plan jest pusty i kursor jest
        na miejscu, nie wolamy nawet ``Freeze`` -- bo zamrozenie kontrolki tez
        jest operacja na kontrolce.
        """
        desired = list_sync.model_row_texts(self.model, self.filter_query)
        if self.filter_query and desired and not any(
            row.item_id == self.model.selected_id for row in desired
        ):
            # Enter must activate a visible result, not the now-hidden old row.
            # Match the original list policy's fallback to the first result.
            self.model.select_id(desired[0].item_id)
        ops = list_sync.plan_row_updates(self._shown, desired)
        # TOZSAMOSC WIDOKU, ktory wlasnie mamy pokazac. Potrzebna, bo pelna
        # podmiana listy nalezy do ZMIANY WIDOKU, a nie do zmiany danych w nim.
        context = self._view_context()
        cursor = self._cursor_target()
        if not ops:
            # Nowa lista oznacza zakonczone zastosowanie danych przez model.
            # Sam zamiar zmiany widoku zostawia dotychczasowy obiekt rows.
            if self.model.rows is not getattr(self, "_shown_rows_source", None):
                self._shown_context = context
                self._shown_rows_source = self.model.rows
            if cursor is None:
                # Nic sie nie zmienilo i kursor jest na miejscu: ZERO operacji.
                # To jest cel calej zmiany -- sam komunikat, Ctrl+C czy tick
                # statusu nie dotykaja listy.
                # Brak operacji kontrolki nie wyklucza nowego, identycznego
                # wyniku loadera. Kontekst takiego wyniku zapisano wyzej.
                return
            # Sam kursor: jedno przejscie stanu, bez przemalowania listy.
            self.updating = True
            try:
                self._move_cursor(cursor)
            finally:
                self.updating = False
            # Samo przesuniecie kursora nie zmienia obiektu model.rows.
            return
        # Zmiana struktury/tekstu to JEDNO przemalowanie, nie seria krokow.
        # ``Freeze``/``Thaw`` to standardowy mechanizm wx, nie usypianie i nie
        # wyciszanie czytnika. ``Thaw`` w ``finally``, bo zamrozona kontrolka
        # po wyjatku bylaby niewidoczna. ``Freeze`` NIE wstrzymuje zdarzen
        # a11y ani ``EVT_LIST_ITEM_SELECTED`` -- od tego jest ``updating``.
        self.updating = True
        self.Freeze()
        try:
            self._apply_ops(ops, desired, context)
            self._shown = desired
            # Kontekst ZAAPLIKOWANY, razem z danymi. Nie wczesniej: gdyby lecial
            # przed nalozeniem planu, przerwana aktualizacja zostawilaby liste z
            # danymi starego widoku, a bramke z kontekstem nowego.
            self._shown_context = context
            self._shown_rows_source = self.model.rows
            # Kursor liczymy PONOWNIE: po usunieciu wiersza kontrolka sama
            # przesuwa fokus, wiec stan sprzed podmiany nie jest wiarygodny.
            target = self._cursor_target()
            if target is not None:
                self._move_cursor(target)
        finally:
            self.Thaw()
            self.updating = False
    def _view_context(self) -> tuple | None:
        """Tozsamosc widoku z sesji, albo ``None`` gdy sesji nie znamy.

        Jedno zrodlo prawdy: ``navigation.view_context`` na ``SessionState``,
        ktory kontrolka dostala przy budowie. Zadnej wlasnej kopii stanu.
        """
        state = getattr(self, "state", None)
        if state is None:
            return None
        return view_context(state)

    def _plan_usuwa_fokus_i_wstawia(self, ops: list) -> bool:
        """Czy plan usuwa wiersz Z FOKUSEM i jednoczesnie cos wstawia.

        Tylko taki uklad daje przejsciowy fokus na usuwane dziecko (zmierzone:
        ``DeleteItem`` na sfokusowanym wierszu emituje ``EVENT_OBJECT_FOCUS`` na
        dziecko, ktorego juz nie bedzie). To jest warunek KONIECZNY pelnej
        podmiany, ale NIE wystarczajacy -- patrz ``_wymienia_caly_widok``.
        """
        focused = self.GetFocusedItem()
        if focused < 0:
            return False
        usuwa_fokus = any(
            isinstance(op, list_sync.DeleteRow) and op.index == focused
            for op in ops
        )
        if not usuwa_fokus:
            return False
        return any(isinstance(op, list_sync.InsertRow) for op in ops)

    def _wymienia_caly_widok(self, ops: list, context: tuple | None) -> bool:
        """Czy wolno siegnac po pelna podmiane ``DeleteAllItems`` + wstawienie.

        DWA warunki, OBA konieczne:

        1. ``context`` MUSI sie roznic od kontekstu, ktory lista NAPRAWDE
           pokazuje (``_shown_context``). To jest bramka ZAKRESU: pelna podmiana
           nalezy do RZECZYWISTEJ zmiany widoku (Foldery -> Wszystkie pliki,
           wejscie w folder, zawartosc playlisty). Zwykle usuniecie jednego
           elementu i wstawienie w TYM SAMYM widoku zostaje przyrostowe -- diff,
           punktowe zmiany, zero operacji bez zmian, wybor po ID.
           ``context is None`` (np. atrapa testowa bez sesji) NIGDY nie wlacza
           podmiany: brak wiedzy o widoku to nie dowod jego zmiany.

           Kontekst porownujemy z ZAAPLIKOWANYM, nie z zamiarem: ``_shown_context``
           zapisujemy razem z ``_shown`` dopiero po nalozeniu planu, wiec
           asynchroniczny loader, ktory jeszcze nie oddal danych, nie przestawia
           bramki przed czasem.

        2. Plan MUSI usuwac wiersz z fokusem i wstawiac (``_plan_usuwa_fokus_i_wstawia``).
           Bez tego nie ma przejsciowego zdarzenia fokusu, wiec pelna podmiana
           nie naprawialaby niczego, a kosztowalaby przebudowe 2476 wierszy.
        """
        if context is None or context == self._shown_context:
            return False
        return self._plan_usuwa_fokus_i_wstawia(ops)

    def _apply_ops(self, ops: list, desired: list | None = None,
                   context: tuple | None = None) -> None:
        """Wykonaj plan w podanej kolejnosci. Indeksy sa juz uzgodnione.

        Przy RZECZYWISTEJ zmianie calego widoku (``_wymienia_caly_widok``)
        czyscimy liste jednym ``DeleteAllItems`` i wstawiamy caly ``desired``.
        Powod jest zmierzony: ``DeleteItem`` na sfokusowanym wierszu emituje
        przejsciowy ``EVENT_OBJECT_FOCUS`` na dziecko, ktorego juz nie bedzie
        (NVDA czytal wtedy wiersz dwa razy), a ``DeleteAllItems`` nie emituje
        nic. Wstawiamy WSZYSTKIE wiersze i wszystkie kolumny -- bez paginacji,
        obcinania i bez LC_VIRTUAL.

        W obrebie TEGO SAMEGO widoku droga zostaje nietknieta: usuniecie
        wiersza pod kursorem BEZ zmiany widoku to nadal jedno ``DeleteItem``,
        a zmiana tekstu to jedno ``SetItem``.
        """
        # PUSTY WYNIK: jedno natywne ``DeleteAllItems`` zamiast kasowania
        # sfokusowanego dziecka przez ``DeleteItem``. To drugie generuje w
        # Windows przejściowy obiekt bez nazwy, który NVDA czyta jako
        # „nieznane”. ``DeleteAllItems`` zachowuje zwykłą kontrolkę i jej
        # obsługę klawiatury, ale nie wystawia nieistniejącego wiersza.
        if desired == [] and self._shown:
            self.DeleteAllItems()
            return
        if desired is not None and self._wymienia_caly_widok(ops, context):
            self.DeleteAllItems()
            for index, row in enumerate(desired):
                self.InsertItem(index, row.texts[0])
                for column in range(1, len(row.texts)):
                    if row.texts[column]:
                        self.SetItem(index, column, row.texts[column])
            return
        for op in ops:
            if isinstance(op, list_sync.DeleteRow):
                self.DeleteItem(op.index)
            elif isinstance(op, list_sync.InsertRow):
                self.InsertItem(op.index, op.texts[0])
                for column in range(1, len(op.texts)):
                    if op.texts[column]:
                        self.SetItem(op.index, column, op.texts[column])
            else:
                self.SetItem(op.index, op.column, op.text)

    def fill_initial(self) -> None:
        """Pierwsze wypelnienie. Ta sama droga co kazda pozniejsza zmiana."""
        self.sync_rows()

    # ------------------------------------------------------- kursor (2 rzeczy)

    def _cursor_target(self) -> int | None:
        """Gdzie ma stac kursor, albo ``None`` gdy nie ma co ruszac.

        ZAZNACZENIE i SKUPIONY WIERSZ to osobne wlasciwosci: pytamy o oba.
        Dawna ``sync_selection`` patrzyla tylko na ``GetFirstSelected``, wiec
        rozjazd fokusu po usunieciu wiersza zostawal nienaprawiony.

        PRZY AKTYWNYM FILTRZE indeks z modelu NIE jest indeksem w kontrolce:
        lista pokazuje tylko wiersze dopasowane. Pozycje liczymy wiec z
        ``_shown`` (czyli ze stanu, ktory kontrolka NAPRAWDE ma) po
        ``item_id`` wybranego wiersza -- ta sama zasada "wybor po ID, nie po
        pozycji", ktora rzadzi calym mechanizmem list i ktorej uzywa oryginal
        (``ResolveListSelectionIndex``, ``MainWindowNavigationPolicy.cs:101``).
        Przy niepustym wyniku ``sync_rows`` wybiera pierwszy widoczny wiersz,
        jeżeli poprzedni wybór wypadł z filtra. Tutaj mapujemy już jego ID.
        """
        wanted = self._wanted_visible_index()
        first_selected = self.GetFirstSelected()
        focused = self.GetFocusedItem()
        # W wielokrotnym wyborze Ctrl+strzalka legalnie przesuwa SAM fokus na
        # niezaznaczony wiersz, aby Ctrl+Spacja mogla go potem dolaczyc albo
        # odlaczyc. Jezeli model juz wskazuje ten fokus i jakies zaznaczenie
        # istnieje, stan natywnej listy jest spojny -- brak bitu SELECTED na
        # fokusie jest zamierzony, a nie usterka do naprawienia. Dawna droga
        # ponownie zaznaczala wiersz przy najblizszym ticku i psula wybor
        # nieprzylegajacy.
        if focused == wanted and first_selected != -1:
            return None
        # W liscie wielokrotnego wyboru ``GetFirstSelected`` zwraca PIERWSZY
        # z zaznaczonych wierszy, a niekoniecznie wiersz z fokusem. Jezeli
        # chciany wiersz juz nalezy do zaznaczenia, podajemy go planerowi jako
        # zaznaczony. Inaczej kazdy tick uznawalby poprawny zakres Shift za
        # rozjazd i ponownie dotykal kontrolki (oraz NVDA).
        selected = wanted if self._is_index_selected(wanted) else first_selected
        return list_sync.plan_cursor(
            wanted=wanted,
            selected=selected,
            focused=focused,
        )

    def _is_index_selected(self, index: int) -> bool:
        """Czy konkretny widoczny wiersz nalezy do natywnego zaznaczenia."""
        # Model moze juz wskazywac pierwszy wiersz, gdy natywna kontrolka jest
        # jeszcze pusta (pierwsze ladowanie albo zmiana widoku). Na prawdziwym
        # wxMSW ``GetItemState(0)`` przy ``GetItemCount()==0`` nie zwraca po
        # prostu zera: podnosi ``wxAssertionError: invalid list control item
        # index``. Wyjatek przerywal ``sync_rows`` PRZED ``InsertItem``. Model
        # mial wtedy stacje/plik (wiec Enter go uruchamial), ale SysListView32
        # nie mial zadnych dzieci, dlatego strzalki nie dawaly NVDA tekstu.
        if index < 0 or index >= self.GetItemCount():
            return False
        try:
            return bool(
                self.GetItemState(index, wx.LIST_STATE_SELECTED)
                & wx.LIST_STATE_SELECTED
            )
        except (AttributeError, TypeError):
            # Minimalne atrapy testowe sprzed obslugi wielokrotnego wyboru
            # znaja tylko pierwszy zaznaczony wiersz.
            return self.GetFirstSelected() == index

    def _wanted_visible_index(self) -> int:
        """Indeks wybranego wiersza W WIDOCZNEJ liscie albo -1.

        Bez filtra jest to po prostu ``model.selected_index`` -- te same
        liczby co przed ta zmiana, wiec zadna istniejaca droga sie nie rusza.
        """
        wanted = self.model.selected_index
        if not self.filter_query:
            return wanted
        if wanted < 0:
            return -1
        selected_id = self.model.selected_id
        for index, shown in enumerate(self._shown):
            if shown.item_id == selected_id:
                return index
        return -1

    def _move_cursor(self, index: int) -> None:
        """Przestaw zaznaczenie i fokus, ustawiajac TYLKO brakujace bity.

        ``Select`` + ``Focus`` to dwa wywolania API, dwa zdarzenia MSAA i dwa
        odczyty tego samego wiersza (zmierzone: "Emu ... 1 z 9" dwukrotnie).
        ``SetItemState`` z maska ``SELECTED|FOCUSED`` przestawia oba bity razem
        -- tak samo jak natywne chodzenie strzalkami, ktore nie dubluje odczytu.

        ALE maska musi pokrywac wylacznie to, czego NAPRAWDE brakuje. Po
        wstawieniu wierszy SysListView32 SAM ustawia fokus na wiersz 0; gdy
        potem ustawialismy bit FOCUSED na JUZ skupionym wierszu, kontrolka
        dostawala kolejne przejscie stanu bez potrzeby. Ustawiamy wiec tylko
        bity brakujace -- mniej zdarzen a11y na kazda synchronizacje.

        UCZCIWIE O SKUTKU: ta zmiana NIE usunela podwojnego odczytu pierwszego
        wiersza przy wejsciu do "Wszystkich plikow" (gest W02). Po niej objaw
        wystepuje nadal, powtarzalnie 3/3 (kwit ``odbior-powt-w02-*.json``),
        wiec hipoteza "to powtorny bit FOCUSED" jest FALSYFIKOWANA. Zostaje to
        jako redukcja zbednych operacji, a nie jako naprawa W02; przyczyna
        podwojnego odczytu pozostaje otwarta i jest opisana w raporcie.

        Czego tu NIE MA: opozniania mowy, ``cancelSpeech`` ani usypiania
        czytnika. Nie dublujemy zdarzenia, zamiast tlumic jego skutek.
        """
        wanted = wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED
        # Pytamy kontrolke, co JUZ ma -- bity, ktore sa na miejscu, pomijamy.
        mask = 0
        if not self._is_index_selected(index):
            mask |= wx.LIST_STATE_SELECTED
        if self.GetFocusedItem() != index:
            mask |= wx.LIST_STATE_FOCUSED
        if mask:
            self.SetItemState(index, wanted & mask, mask)
        # Przewijanie MUSI zostac: na 2476 wierszach kursor poza widokiem byl by
        # regresja. ``EnsureVisible`` samo nie oglasza wiersza.
        self.EnsureVisible(index)

    def sync_cursor(self) -> None:
        """Sam kursor, bez dotykania zawartosci (np. po powrocie z odtwarzacza)."""
        target = self._cursor_target()
        if target is not None:
            self._move_cursor(target)

    def shown_item_id(self, index: int) -> str | None:
        """``item_id`` wiersza, ktory kontrolka POKAZUJE pod tym indeksem.

        Jedyne poprawne tlumaczenie pozycji z kontrolki na tozsamosc danej,
        gdy filtr zweza liste. ``None`` dla indeksu poza zakresem -- wx potrafi
        zapytac o wiersz w trakcie zmiany dlugosci listy.
        """
        if 0 <= index < len(self._shown):
            return self._shown[index].item_id
        return None

    def selected_rows(self) -> list[Row]:
        """Wszystkie zaznaczone wiersze w kolejnosci widocznej na liscie.

        Model zachowuje jedno ID jako kursor/zakotwiczenie nawigacji. Pelny
        zakres Shift/Ctrl jest natomiast stanem natywnej kontrolki Windows i
        trzeba go odczytac przez ``GetFirstSelected``/``GetNextSelected``.
        Mapowanie idzie przez ``_shown``, zeby filtr nie pomylil indeksu
        widocznego z indeksem pelnego modelu.
        """
        item_ids: list[str] = []
        seen: set[str] = set()
        index = self.GetFirstSelected()
        while index != -1:
            item_id = self.shown_item_id(index)
            if item_id is not None and item_id not in seen:
                seen.add(item_id)
                item_ids.append(item_id)
            next_index = self.GetNextSelected(index)
            # Prawdziwy ListCtrl zwraca indeks wiekszy albo -1. Wadliwa
            # atrapa nie moze zawiesic aplikacji ani testu w petli bez konca.
            if next_index != -1 and next_index <= index:
                break
            index = next_index

        rows_by_id = {row.item_id: row for row in self.model.rows}
        return [rows_by_id[item_id] for item_id in item_ids if item_id in rows_by_id]

    def select_item_ids(self, item_ids: list[str]) -> None:
        """Przywróć wielokrotne zaznaczenie po zmianie kolejności według ID.

        Nie wolno zachować samych indeksów: po przeniesieniu wskazywałyby inne
        pliki. Fokus pozostaje na ``model.selected_id`` ustawionym przez
        zwykły ``sync_rows``; tutaj zmieniamy wyłącznie bity zaznaczenia.
        """
        wanted = set(item_ids)
        self.updating = True
        try:
            for index, shown in enumerate(self._shown):
                selected = self._is_index_selected(index)
                should_select = shown.item_id in wanted
                if selected == should_select:
                    continue
                self.SetItemState(
                    index,
                    wx.LIST_STATE_SELECTED if should_select else 0,
                    wx.LIST_STATE_SELECTED,
                )
        finally:
            self.updating = False

    def visible_count(self) -> int:
        """Liczba wierszy POKAZANYCH teraz. Zrodlo liczby do statusu filtra."""
        return len(self._shown)


class CommandPaletteDialog(wx.Dialog):
    """Natywna paleta: jawne etykiety, filtr i jedna istniejąca akcja."""

    def __init__(
        self,
        parent: wx.Window,
        entries: tuple[CommandPaletteEntry, ...],
    ) -> None:
        super().__init__(parent, title="Paleta poleceń — AMC", size=(700, 520))
        self._all_entries = entries
        self._shown_entries = entries

        panel = wx.Panel(self)
        layout = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(panel, label="&Filtruj polecenia:")
        self.query = wx.TextCtrl(panel)
        self.query.SetName("Filtr poleceń")
        self.query.SetHelpText(
            "Wpisuj fragmenty nazwy. Strzałka w dół przechodzi do listy, "
            "Enter wykonuje wybrane polecenie, Escape zamyka paletę."
        )
        self.status = wx.StaticText(panel, label=command_count_label(len(entries)))
        self.status.SetName(command_count_label(len(entries)))
        self.commands = wx.ListBox(
            panel,
            choices=[entry.label for entry in entries],
            style=wx.LB_SINGLE,
        )
        self.commands.SetName("Polecenia")
        self.commands.SetHelpText(
            "Strzałki wybierają polecenie. Enter wykonuje, Escape zamyka paletę."
        )
        if entries:
            self.commands.SetSelection(0)

        layout.Add(label, 0, wx.ALL | wx.EXPAND, 12)
        layout.Add(self.query, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 12)
        layout.Add(self.status, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 12)
        layout.Add(self.commands, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 12)
        panel.SetSizer(layout)

        buttons = wx.StdDialogButtonSizer()
        execute = wx.Button(self, wx.ID_OK, label="&Wykonaj")
        execute.SetName("Wykonaj polecenie")
        execute.SetDefault()
        cancel = wx.Button(self, wx.ID_CANCEL, label="&Anuluj")
        cancel.SetName("Anuluj paletę poleceń")
        buttons.AddButton(execute)
        buttons.AddButton(cancel)
        buttons.Realize()
        shell = wx.BoxSizer(wx.VERTICAL)
        shell.Add(panel, 1, wx.EXPAND)
        shell.Add(buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 12)
        self.SetSizer(shell)
        self.SetEscapeId(wx.ID_CANCEL)

        self.query.Bind(wx.EVT_TEXT, self._on_query_changed)
        self.query.Bind(wx.EVT_KEY_DOWN, self._on_query_key)
        self.commands.Bind(wx.EVT_KEY_DOWN, self._on_list_key)
        self.commands.Bind(wx.EVT_LISTBOX_DCLICK, self._accept)
        execute.Bind(wx.EVT_BUTTON, self._accept)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key_hook)
        self.query.SetFocus()

    @property
    def selected_entry(self) -> CommandPaletteEntry | None:
        index = self.commands.GetSelection()
        return self._shown_entries[index] if 0 <= index < len(self._shown_entries) else None

    def _refresh(self) -> None:
        self._shown_entries = filter_command_entries(
            self._all_entries, self.query.GetValue()
        )
        self.commands.Set([entry.label for entry in self._shown_entries])
        if self._shown_entries:
            self.commands.SetSelection(0)
        label = command_count_label(len(self._shown_entries))
        self.status.SetLabel(label)
        self.status.SetName(label)

    def _on_query_changed(self, event: wx.CommandEvent) -> None:
        self._refresh()
        event.Skip()

    def _on_query_key(self, event: wx.KeyEvent) -> None:
        code = event.GetKeyCode()
        if code in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
            self._accept(event)
            return
        if code == wx.WXK_DOWN and self._shown_entries:
            self.commands.SetFocus()
            return
        if code == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
            return
        event.Skip()

    def _on_list_key(self, event: wx.KeyEvent) -> None:
        code = event.GetKeyCode()
        if code in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
            self._accept(event)
            return
        if code == wx.WXK_UP and self.commands.GetSelection() == 0:
            self.query.SetFocus()
            self.query.SetInsertionPointEnd()
            return
        if code == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
            return
        event.Skip()

    def _on_key_hook(self, event: wx.KeyEvent) -> None:
        focus = wx.Window.FindFocus()
        if focus is self.query:
            self._on_query_key(event)
            return
        if focus is self.commands:
            self._on_list_key(event)
            return
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
            return
        event.Skip()

    def _accept(self, _event) -> None:
        if self.selected_entry is None:
            label = "Brak polecenia do wykonania"
            self.status.SetLabel(label)
            self.status.SetName(label)
            self.query.SetFocus()
            return
        self.EndModal(wx.ID_OK)


class SearchDialog(wx.Dialog):
    """Native, screen-reader-friendly search window.

    It is deliberately a separate window, as in full AMC.  ``Ctrl+K`` keeps
    filtering the already visible list; ``Ctrl+F`` searches the complete
    cached catalogue, the public directories supported by a service, or the
    explicitly labelled loaded-list scope of WiiM and Sonos. Results are
    placed in this ordinary SysListView32.
    """

    def __init__(
        self,
        parent: wx.Window,
        *,
        all_services: bool,
        current_session_label: str,
        run_search: Callable[[str, "SearchDialog"], None],
        copy_text: Callable[[str], bool],
        history: list[str],
        record_query: Callable[[str], list[str]],
        detailed_hints: bool = False,
    ) -> None:
        mode = (
            "Szukaj we wszystkich usługach"
            if all_services
            else f"Szukaj w {current_session_label}"
        )
        super().__init__(parent, title=f"{mode} — AMC", size=(840, 570))
        self.SetName(f"{mode} — AMC")
        self._all_services = all_services
        self._run_search = run_search
        self._copy_text = copy_text
        self._history = list(history)
        self._record_query = record_query
        self._history_index = -1
        self._browsing_history = False
        self._applying_history = False
        self._entries: list[SearchEntry] = []
        self.catalog: SearchCollection | None = None
        self.selected_result: SearchEntry | None = None
        self.selected_results: list[SearchEntry] = []
        self.selected_action = SearchResultAction.OPEN

        heading = wx.StaticText(self, label=mode)
        heading.SetName(mode)
        query_label = wx.StaticText(self, label="&Tekst do wyszukania:")
        self.query = wx.TextCtrl(self)
        self.query.SetName(mode)
        self.query.SetHelpText(
            "Wpisz tekst i naciśnij Enter, aby rozpocząć wyszukiwanie. "
            "Przy pustym polu strzałka w dół wybiera historię. "
            "Escape zamyka okno."
            if detailed_hints
            else ""
        )
        self.search_button = wx.Button(self, label="&Szukaj")
        self.search_button.SetName("Szukaj")
        self.results = wx.ListCtrl(
            self,
            style=wx.LC_REPORT | wx.BORDER_SUNKEN,
        )
        self.results.InsertColumn(0, "Nazwa", width=390)
        self.results.InsertColumn(1, "Rodzaj", width=130)
        self.results.InsertColumn(2, "Szczegóły", width=270)
        self.results.SetLabel("Wyniki wyszukiwania")
        self.results.SetName("Wyniki wyszukiwania")
        self.results.SetHelpText(
            "Strzałki wybierają wynik. Enter przechodzi do wyniku na "
            "właściwej liście. W TIDAL prawa strzałka otwiera dostępne "
            "albumy, utwory i podobnych wykonawców. Escape zamyka okno."
            if detailed_hints
            else ""
        )
        self.status = wx.StaticText(self, label="Wpisz tekst do wyszukania")
        self.status.SetName("Stan wyszukiwania")
        self.announcer = Announcer(self.status)
        self.open_button = wx.Button(self, wx.ID_OK, "&Otwórz")
        self.close_button = wx.Button(self, wx.ID_CANCEL, "&Zamknij")

        query_row = wx.BoxSizer(wx.HORIZONTAL)
        query_row.Add(self.query, 1, wx.RIGHT | wx.EXPAND, 8)
        query_row.Add(self.search_button, 0)
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.AddStretchSpacer()
        buttons.Add(self.open_button, 0, wx.RIGHT, 8)
        buttons.Add(self.close_button, 0)
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(heading, 0, wx.ALL, 10)
        layout.Add(query_label, 0, wx.LEFT | wx.RIGHT, 10)
        layout.Add(query_row, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        layout.Add(self.results, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        layout.Add(self.status, 0, wx.ALL | wx.EXPAND, 10)
        layout.Add(buttons, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        self.SetSizer(layout)
        self.SetEscapeId(wx.ID_CANCEL)

        self.query.Bind(wx.EVT_KEY_DOWN, self._on_query_key)
        self.query.Bind(wx.EVT_TEXT, self._on_query_text)
        self.results.Bind(wx.EVT_KEY_DOWN, self._on_results_key)
        self.results.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_result_activated)
        self.search_button.Bind(wx.EVT_BUTTON, lambda _event: self.start_search())
        self.open_button.Bind(wx.EVT_BUTTON, lambda _event: self._open_selected())
        self.close_button.Bind(wx.EVT_BUTTON, lambda _event: self.EndModal(wx.ID_CANCEL))
        # Standardowa obsluga dialogu wx potrafi potraktowac Enter jako
        # aktywacje domyslnego ID_OK ZANIM TextCtrl dostanie EVT_KEY_DOWN.
        # Przechwyt na poziomie okna przekazuje gest do kontrolki z fokusem:
        # Enter uruchamia wyszukiwanie, a strzalki przegladaja historie.
        self.Bind(wx.EVT_CHAR_HOOK, self._on_dialog_shortcut_hook)
        self.Bind(wx.EVT_SHOW, self._on_show)
        self.Bind(wx.EVT_CLOSE, lambda event: event.Skip())
        self.CentreOnParent()
        self.query.SetFocus()

    def _on_show(self, event: wx.ShowEvent) -> None:
        event.Skip()
        if event.IsShown():
            wx.CallAfter(self.query.SetFocus)

    def _on_dialog_shortcut_hook(self, event: wx.KeyEvent) -> None:
        """Oddaj klawisz wlasciwej kontrolce przed domyslami dialogu wx."""

        focus = wx.Window.FindFocus()
        if focus is self.query:
            self._on_query_key(event)
            return
        if focus is self.results:
            self._on_results_key(event)
            return
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
            return
        event.Skip()

    def start_search(self) -> None:
        if not self.search_button.IsEnabled():
            return
        query = self.query.GetValue().strip()
        if not query:
            self.announcer.say("Wpisz tekst do wyszukania")
            self.query.SetFocus()
            return
        self.search_button.Enable(False)
        self.announcer.say("Wyszukiwanie")
        self._history = self._record_query(query)
        self._reset_history_browsing()
        self._run_search(query, self)

    def show_results(
        self,
        entries: list[SearchEntry],
        warnings: tuple[str, ...] = (),
    ) -> None:
        self.search_button.Enable(True)
        self._entries = entries
        self.results.Freeze()
        try:
            self.results.DeleteAllItems()
            for index, entry in enumerate(entries):
                row = entry.row
                self.results.InsertItem(index, row.title)
                if entry.kind_label:
                    self.results.SetItem(index, 1, entry.kind_label)
                details = [row.artist_name] if row.artist_name else []
                if row.detail:
                    details.append(row.detail)
                if self._all_services:
                    details.append(entry.session_label)
                if details:
                    self.results.SetItem(index, 2, ", ".join(dict.fromkeys(details)))
        finally:
            self.results.Thaw()

        if not entries:
            message = "Brak wyników. Zmień wyszukiwany tekst"
            if warnings:
                message = f"{message}. {'; '.join(warnings)}"
            self.announcer.say(message)
            self.query.SetFocus()
            self.query.SelectAll()
            return

        count = len(entries)
        message = "1 wynik" if count == 1 else f"{count} wyników"
        if warnings:
            message = f"{message}. {'; '.join(warnings)}"
        # The focused native row already speaks its label and position.  Keep
        # the count as readable status without a second live announcement,
        # exactly like the full AMC search window.
        self.status.SetLabel(message)
        self.status.SetName(message)
        self.results.SetItemState(
            0,
            wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED,
            wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED,
        )
        self.results.EnsureVisible(0)
        self.results.SetFocus()

    def search_failed(self) -> None:
        self.search_button.Enable(True)
        self.announcer.say("Nie udało się wykonać wyszukiwania")
        self.query.SetFocus()

    def _selected_entries(self) -> list[SearchEntry]:
        result: list[SearchEntry] = []
        index = self.results.GetFirstSelected()
        while index != -1:
            if 0 <= index < len(self._entries):
                result.append(self._entries[index])
            next_index = self.results.GetNextSelected(index)
            if next_index != -1 and next_index <= index:
                break
            index = next_index
        if result:
            return result
        focused = self.results.GetFocusedItem()
        return [self._entries[focused]] if 0 <= focused < len(self._entries) else []

    def _lead_entry(self) -> SearchEntry | None:
        focused = self.results.GetFocusedItem()
        if 0 <= focused < len(self._entries):
            return self._entries[focused]
        selected = self._selected_entries()
        return selected[0] if selected else None

    def _complete_selected(self, action: SearchResultAction) -> None:
        entry = self._lead_entry()
        if entry is None:
            self.announcer.say("Najpierw wykonaj wyszukiwanie i wybierz wynik")
            self.query.SetFocus()
            return
        selected = self._selected_entries()
        if action in (
            SearchResultAction.QUEUE,
            SearchResultAction.PLAY_NEXT,
            SearchResultAction.FAVORITE,
            SearchResultAction.LIBRARY,
            SearchResultAction.PLAYLIST,
        ):
            sessions = {candidate.session_id for candidate in selected}
            locations = {
                (candidate.source_view, candidate.parent_id)
                for candidate in selected
            }
            if len(sessions) > 1:
                self.announcer.say(
                    "Dla jednego działania wybierz wyniki z tej samej usługi"
                )
                return
            if len(locations) > 1:
                self.announcer.say(
                    "Dla jednego działania wybierz wyniki z tej samej listy"
                )
                return
        self.selected_result = entry
        self.selected_results = selected or [entry]
        self.selected_action = action
        self.EndModal(wx.ID_OK)

    def _open_selected(self) -> None:
        self._complete_selected(SearchResultAction.OPEN)

    def _copy(self, *, addresses: bool) -> None:
        values = []
        for entry in self._selected_entries():
            value = entry.row.address if addresses else entry.row.title
            if value:
                values.append(value)
        if not values:
            self.announcer.say(
                "Wybrane wyniki nie mają adresu" if addresses else "Nie ma czego skopiować"
            )
            return
        if self._copy_text(os.linesep.join(values)):
            if addresses:
                self.announcer.say(
                    "Skopiowano adres" if len(values) == 1
                    else f"Skopiowano adresy: {len(values)} elementów"
                )
            else:
                self.announcer.say(
                    COPIED_NAME_MESSAGE if len(values) == 1
                    else f"Skopiowano nazwy: {len(values)} elementów"
                )

    def _announce_quick_information(self) -> None:
        entry = self._lead_entry()
        if entry is None:
            self.announcer.say("Brak wybranego wyniku")
            return
        row = entry.row
        parts = [row.title, row.artist_name, entry.kind_label, row.detail]
        if self._all_services:
            parts.append(entry.session_label)
        self.announcer.say(", ".join(dict.fromkeys(part for part in parts if part)))

    def _on_query_key(self, event: wx.KeyEvent) -> None:
        code = event.GetKeyCode()
        if code in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
            self.start_search()
            return
        if (
            code == wx.WXK_DOWN
            and (not self.query.GetValue() or self._browsing_history)
            and self._browse_history(1)
        ):
            return
        if code == wx.WXK_UP and self._browsing_history and self._browse_history(-1):
            return
        if code == wx.WXK_DOWN and self._entries:
            self.results.SetFocus()
            return
        if code == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
            return
        event.Skip()

    def _on_query_text(self, event: wx.CommandEvent) -> None:
        event.Skip()
        if not self._applying_history:
            self._reset_history_browsing()

    def _reset_history_browsing(self) -> None:
        self._browsing_history = False
        self._history_index = -1

    def _apply_history_text(self, value: str) -> None:
        self._applying_history = True
        try:
            self.query.SetValue(value)
            self.query.SetInsertionPointEnd()
            self.query.SelectAll()
        finally:
            self._applying_history = False

    def _browse_history(self, direction: int) -> bool:
        if not self._history:
            if not self.query.GetValue():
                self.announcer.say("Historia wyszukiwania jest pusta")
                return True
            return False
        if not self._browsing_history:
            if self.query.GetValue() or direction < 0:
                return False
            self._browsing_history = True
            self._history_index = 0
        else:
            self._history_index += direction
            if self._history_index < 0:
                self._apply_history_text("")
                self._reset_history_browsing()
                self.status.SetLabel("Puste pole wyszukiwania")
                self.status.SetName("Puste pole wyszukiwania")
                return True
            self._history_index = min(self._history_index, len(self._history) - 1)
        self._apply_history_text(self._history[self._history_index])
        text = f"{self._history_index + 1} z {len(self._history)} w historii"
        self.status.SetLabel(text)
        self.status.SetName(text)
        return True

    def _on_results_key(self, event: wx.KeyEvent) -> None:
        code = event.GetKeyCode()
        ctrl = event.ControlDown()
        shift = event.ShiftDown()
        alt = event.AltDown()
        if code == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
            return
        if code in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) and not (ctrl or shift or alt):
            self._open_selected()
            return
        if code in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) and ctrl and not (shift or alt):
            self._complete_selected(SearchResultAction.TOGGLE_PLAYBACK)
            return
        if code in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) and shift and not (ctrl or alt):
            self._complete_selected(SearchResultAction.QUEUE)
            return
        if code in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) and ctrl and shift and not alt:
            self._complete_selected(SearchResultAction.PLAY_NEXT)
            return
        if ctrl and shift and code in (ord("U"), ord("u")):
            self._complete_selected(SearchResultAction.FAVORITE)
            return
        if ctrl and shift and code in (ord("L"), ord("l")):
            self._complete_selected(SearchResultAction.LIBRARY)
            return
        if ctrl and shift and code in (ord("P"), ord("p")) and not alt:
            self._complete_selected(SearchResultAction.PLAYLIST)
            return
        if ctrl and shift and alt and code in (ord("P"), ord("p")):
            self._complete_selected(SearchResultAction.PRESET)
            return
        if alt and code in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) and not (ctrl or shift):
            self._complete_selected(SearchResultAction.INFORMATION)
            return
        if ctrl and code in (ord("D"), ord("d")) and not (shift or alt):
            self._complete_selected(SearchResultAction.DOWNLOAD)
            return
        if ctrl and code in (ord("S"), ord("s")) and not (shift or alt):
            self._complete_selected(SearchResultAction.SAVE_AS)
            return
        if code == wx.WXK_LEFT and not (ctrl or shift or alt):
            self._announce_quick_information()
            return
        if code == wx.WXK_RIGHT and not (ctrl or shift or alt):
            self._complete_selected(SearchResultAction.RELATIONS)
            return
        if ctrl and code in (ord("C"), ord("c")):
            self._copy(addresses=shift)
            return
        event.Skip()

    def _on_result_activated(self, _event: wx.ListEvent) -> None:
        self._open_selected()


class StationDialog(wx.Dialog):
    """Dodanie/zmiana stacji. Zwykle pola z etykietami - czytnik je nazwie."""

    def __init__(
        self,
        parent: wx.Window,
        title: str,
        name: str = "",
        url: str = "",
        *,
        network_stream: bool = False,
    ) -> None:
        super().__init__(parent, title=title)
        panel = wx.Panel(self)
        grid = wx.FlexGridSizer(2, 2, 8, 8)

        item_name = "strumienia" if network_stream else "stacji"
        name_label = wx.StaticText(panel, label=f"&Nazwa {item_name}:")
        self.name_field = wx.TextCtrl(panel, value=name, size=(320, -1))
        self.name_field.SetName(f"Nazwa {item_name}")
        url_label = wx.StaticText(panel, label="&Adres (http/https):")
        self.url_field = wx.TextCtrl(panel, value=url, size=(320, -1))
        self.url_field.SetName(f"Adres {item_name}")

        grid.AddMany(
            [
                (name_label, 0, wx.ALIGN_CENTER_VERTICAL),
                (self.name_field, 1, wx.EXPAND),
                (url_label, 0, wx.ALIGN_CENTER_VERTICAL),
                (self.url_field, 1, wx.EXPAND),
            ]
        )
        grid.AddGrowableCol(1, 1)

        buttons = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        # WAZNE: przyciski OK/Anuluj sa dziecmi DIALOGU, nie panelu. Gdy ich
        # sizer wlozymy w sizer PANELU, wxWidgets przerywa asercja
        # CheckExpectedParentIs i modalna petla nigdy nie wraca - okno zostaje
        # niewidoczne, ale wciaz trzyma fokus. Dlatego panel trzyma TYLKO pola,
        # a sizer zewnetrzny nalezy do dialogu.
        inner = wx.BoxSizer(wx.VERTICAL)
        inner.Add(grid, 1, wx.ALL | wx.EXPAND, 12)
        panel.SetSizer(inner)

        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(panel, 1, wx.EXPAND)
        outer.Add(buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 12)
        self.SetSizer(outer)
        self.Fit()
        self.name_field.SetFocus()

    @property
    def values(self) -> tuple[str, str]:
        return self.name_field.GetValue().strip(), self.url_field.GetValue().strip()


class RenameItemDialog(wx.Dialog):
    """Jednoznacznie nazwane pole zmiany nazwy, bez technicznych wartości."""

    def __init__(
        self,
        parent: wx.Window,
        *,
        title: str,
        prompt: str,
        field_name: str,
        value: str,
        help_text: str = "",
    ) -> None:
        super().__init__(parent, title=title)
        panel = wx.Panel(self)
        inner = wx.BoxSizer(wx.VERTICAL)
        if help_text:
            help_label = wx.StaticText(panel, label=help_text)
            help_label.Wrap(460)
            inner.Add(help_label, 0, wx.ALL | wx.EXPAND, 10)
        label = wx.StaticText(panel, label=prompt)
        self.field = wx.TextCtrl(panel, value=value, size=(420, -1))
        self.field.SetName(field_name)
        inner.Add(label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        inner.Add(self.field, 0, wx.ALL | wx.EXPAND, 10)
        panel.SetSizer(inner)

        buttons = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(panel, 1, wx.EXPAND)
        outer.Add(buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 10)
        self.SetSizer(outer)
        self.Fit()
        self.field.SetFocus()
        self.field.SelectAll()

    @property
    def value(self) -> str:
        return self.field.GetValue().strip()


class PodcastSourceDialog(wx.Dialog):
    """Natywny formularz dodawania źródła Podcastów i YouTube."""

    def __init__(self, parent: wx.Window) -> None:
        super().__init__(
            parent,
            title="Nowy podcast, kanał YouTube lub medium internetowe",
        )
        panel = wx.Panel(self)
        layout = wx.BoxSizer(wx.VERTICAL)

        help_text = (
            "Wpisz adres kanału RSS lub Atom, kanału albo playlisty YouTube, "
            "lub pojedynczego publicznego materiału YouTube. Po zatwierdzeniu "
            "AMC sprawdzi adres i doda źródło do Biblioteki."
        )
        help_label = wx.StaticText(panel, label=help_text)
        help_label.SetName(help_text)
        help_label.Wrap(520)
        layout.Add(help_label, 0, wx.ALL | wx.EXPAND, 10)

        address_label = wx.StaticText(panel, label="&Adres źródła:")
        self.address_field = wx.TextCtrl(panel, value="", size=(500, -1))
        self.address_field.SetName("Adres źródła")
        layout.Add(address_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        layout.Add(self.address_field, 0, wx.ALL | wx.EXPAND, 10)

        title_label = wx.StaticText(panel, label="Własna &nazwa, opcjonalnie:")
        self.title_field = wx.TextCtrl(panel, value="", size=(500, -1))
        self.title_field.SetName("Własna nazwa, opcjonalnie")
        layout.Add(title_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        layout.Add(self.title_field, 0, wx.ALL | wx.EXPAND, 10)
        panel.SetSizer(layout)

        buttons = wx.StdDialogButtonSizer()
        add_button = wx.Button(self, wx.ID_OK, label="&Sprawdź i dodaj")
        add_button.SetName("Sprawdź i dodaj źródło")
        add_button.SetDefault()
        cancel = wx.Button(self, wx.ID_CANCEL, label="&Anuluj")
        cancel.SetName("Anuluj dodawanie źródła")
        buttons.AddButton(add_button)
        buttons.AddButton(cancel)
        buttons.Realize()

        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(panel, 1, wx.EXPAND)
        outer.Add(buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 10)
        self.SetSizer(outer)
        self.SetMinSize((620, 360))
        self.Fit()
        self.address_field.SetFocus()

    @property
    def values(self) -> tuple[str, str]:
        return self.address_field.GetValue().strip(), self.title_field.GetValue().strip()


class PodcastOpmlImportDialog(wx.Dialog):
    """Wybór źródeł bez ujawniania obiektów ani identyfikatorów NVDA."""

    def __init__(self, parent: wx.Window, entries: list[dict]) -> None:
        super().__init__(parent, title="Importuj podcasty z OPML")
        self._entries = [
            {
                "label": str(entry.get("label") or "Podcast").strip() or "Podcast",
                "feedUrl": str(entry.get("feedUrl") or "").strip(),
            }
            for entry in entries
            if str(entry.get("feedUrl") or "").strip()
        ]
        self._included = [True] * len(self._entries)

        panel = wx.Panel(self)
        layout = wx.BoxSizer(wx.VERTICAL)
        help_text = (
            "Wszystkie podcasty są początkowo zaznaczone. "
            "Spacja zmienia stan bieżącej pozycji, Ctrl+A zaznacza wszystkie."
        )
        help_label = wx.StaticText(panel, label=help_text)
        help_label.SetName(help_text)
        help_label.Wrap(620)
        layout.Add(help_label, 0, wx.ALL | wx.EXPAND, 10)

        self.sources = wx.ListBox(panel, style=wx.LB_SINGLE)
        self.sources.SetName("Podcasty do importu")
        self.sources.SetToolTip(help_text)
        layout.Add(self.sources, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        panel.SetSizer(layout)

        buttons = wx.StdDialogButtonSizer()
        import_button = wx.Button(self, wx.ID_OK, label="&Importuj zaznaczone")
        import_button.SetName("Importuj zaznaczone podcasty")
        import_button.SetDefault()
        cancel = wx.Button(self, wx.ID_CANCEL, label="&Anuluj")
        cancel.SetName("Anuluj import podcastów")
        buttons.AddButton(import_button)
        buttons.AddButton(cancel)
        buttons.Realize()

        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(panel, 1, wx.EXPAND)
        outer.Add(buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 10)
        self.SetSizer(outer)
        self.SetMinSize((700, 480))
        self._refresh_labels(selected=0)
        self.sources.Bind(wx.EVT_KEY_DOWN, self._on_key)
        self.Bind(wx.EVT_BUTTON, self._on_accept, id=wx.ID_OK)
        self.sources.SetFocus()

    def _label(self, index: int) -> str:
        state = "zaznaczony" if self._included[index] else "niezaznaczony"
        return f"{self._entries[index]['label']}, {state}"

    def _refresh_labels(self, *, selected: int) -> None:
        labels = [self._label(index) for index in range(len(self._entries))]
        if self.sources.GetCount() != len(labels):
            self.sources.Set(labels)
        else:
            for index, label in enumerate(labels):
                if self.sources.GetString(index) != label:
                    self.sources.SetString(index, label)
        if self._entries:
            self.sources.SetSelection(max(0, min(selected, len(self._entries) - 1)))

    def _on_key(self, event: wx.KeyEvent) -> None:
        chord = chord_from_event(event)
        selected = self.sources.GetSelection()
        if chord.canonical == "Space" and 0 <= selected < len(self._included):
            self._included[selected] = not self._included[selected]
            self._refresh_labels(selected=selected)
            return
        if chord.canonical == "Ctrl+A":
            self._included = [True] * len(self._included)
            self._refresh_labels(selected=max(0, selected))
            return
        event.Skip()

    def _on_accept(self, _event: wx.CommandEvent) -> None:
        if not self.selected_feed_urls:
            wx.MessageBox(
                "Zaznacz co najmniej jeden podcast do importu.",
                "Import OPML",
                wx.OK | wx.ICON_INFORMATION,
                self,
            )
            self.sources.SetFocus()
            return
        self.EndModal(wx.ID_OK)

    @property
    def selected_feed_urls(self) -> list[str]:
        return [
            entry["feedUrl"]
            for entry, included in zip(self._entries, self._included)
            if included
        ]


class PodcastDescriptionDialog(wx.Dialog):
    """Native read-only long-form text, with no embedded browser surface."""

    def __init__(
        self,
        parent: wx.Window,
        information: PodcastDescription,
        copy_text: Callable[[str], bool],
    ) -> None:
        # Windows/MSAA ogłasza tytuł nowego okna przed kontrolką z treścią.
        # Dlatego tytułem dostępnym jest początek prawdziwego opisu, a nie
        # ogólne „Opis odcinka”, po którym NVDA dopowiadał rolę „dialog”.
        accessible_title = (
            information.initial_focus_name or information.window_title
        )
        super().__init__(parent, title=accessible_title)
        self._information = information.text
        self._copy_text = copy_text

        # NVDA najpierw ogłasza nazwę nowo otwartego okna. Nazwą dostępną
        # jest więc początek właściwego opisu, a nie powtórzone techniczne
        # „Opis odcinka, dialog”. Tytuł wizualny okna pozostaje bez zmian.
        self.SetName(accessible_title)

        panel = wx.Panel(self)
        layout = wx.BoxSizer(wx.VERTICAL)
        self.content = wx.TextCtrl(
            panel,
            value=information.text,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2,
        )
        # To jest świadomie przygotowany tekst użytkowy, nigdy repr obiektu,
        # identyfikator ani nazwa klasy. Tak samo pełny AMC rozpoczyna fokus od
        # początku właściwego opisu, zamiast od technicznej roli kontrolki.
        self.content.SetName(accessible_title)
        self.content.SetInsertionPoint(0)
        layout.Add(self.content, 1, wx.EXPAND)

        self.copy_status = wx.StaticText(panel, label="")
        self.copy_status.SetName("Stan kopiowania")
        layout.Add(self.copy_status, 0, wx.TOP | wx.EXPAND, 8)
        panel.SetSizer(layout)

        buttons = wx.StdDialogButtonSizer()
        copy_button = wx.Button(self, wx.ID_COPY, label="&Kopiuj wszystko")
        copy_button.SetName("Kopiuj całą treść")
        close_button = wx.Button(self, wx.ID_CANCEL, label="&Zamknij")
        close_button.SetName("Zamknij opis")
        buttons.AddButton(copy_button)
        buttons.AddButton(close_button)
        buttons.Realize()

        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(panel, 1, wx.ALL | wx.EXPAND, 12)
        outer.Add(buttons, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.ALIGN_RIGHT, 12)
        self.SetSizer(outer)
        self.SetMinSize((700, 520))
        self.Bind(wx.EVT_BUTTON, self._on_copy, id=wx.ID_COPY)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key)
        self.content.SetFocus()

    def _on_copy(self, _event: wx.CommandEvent) -> None:
        if self._copy_text(self._information):
            self.copy_status.SetLabel("Skopiowano całą treść")

    def _on_key(self, event: wx.KeyEvent) -> None:
        if chord_from_event(event).canonical == "Escape":
            self.EndModal(wx.ID_CANCEL)
            return
        event.Skip()


def _preset_slot_from_event(event: wx.KeyEvent) -> int | None:
    """Cyfra/minus/rownosc w dialogach presetow, bez nazw technicznych wx."""
    if event.ControlDown() or event.AltDown() or event.ShiftDown():
        return None
    key = chord_from_event(event).key
    if key in {str(value) for value in range(1, 10)}:
        return int(key)
    return {"0": 10, "-": 11, "=": 12, "+": 12}.get(key)


class PresetListDialog(wx.Dialog):
    """Dostepna lista 12 miejsc. Do kontrolek trafiaja tylko jawne etykiety."""

    def __init__(
        self,
        parent: wx.Window,
        *,
        choices: tuple[profile_presets.PresetChoice, ...],
        session_name: str,
        current_target: profile_presets.PresetTarget | None,
    ) -> None:
        super().__init__(parent, title=f"Presety — {session_name}")
        self._choices = choices
        panel = wx.Panel(self)
        layout = wx.BoxSizer(wx.VERTICAL)

        description_text = (
            f"Presety sesji {session_name}. Cyfry wybierają miejsce. "
            "Enter lub Spacja uruchamia zajętą pozycję. "
            "Ctrl+Alt+Shift+P przypisuje bieżący element."
        )
        description = wx.StaticText(panel, label=description_text)
        description.SetName(description_text)
        layout.Add(description, 0, wx.ALL | wx.EXPAND, 12)

        self.preset_list = wx.ListBox(
            panel,
            choices=[choice.label for choice in choices],
            style=wx.LB_SINGLE,
        )
        self.preset_list.SetName(f"Presety, {session_name}")
        self.preset_list.SetToolTip(
            "Cyfra, minus lub znak równości wybiera miejsce. Enter albo Spacja uruchamia."
        )
        selected = next(
            (index for index, choice in enumerate(choices)
             if current_target is not None
             and profile_presets.choice_matches_target(choice, current_target)),
            -1,
        )
        if selected < 0:
            selected = next(
                (index for index, choice in enumerate(choices) if choice.target_id is not None),
                0,
            )
        self.preset_list.SetSelection(selected)
        layout.Add(self.preset_list, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 12)

        self.status = wx.StaticText(panel, label="Gotowe")
        self.status.SetName("Gotowe")
        self._announcer = Announcer(self.status)
        layout.Add(self.status, 0, wx.ALL | wx.EXPAND, 12)
        panel.SetSizer(layout)

        buttons = wx.StdDialogButtonSizer()
        self.activate_button = wx.Button(self, wx.ID_OK, label="&Uruchom")
        self.activate_button.SetName("Uruchom preset")
        self.activate_button.SetDefault()
        close = wx.Button(self, wx.ID_CANCEL, label="&Zamknij")
        close.SetName("Zamknij listę presetów")
        buttons.AddButton(self.activate_button)
        buttons.AddButton(close)
        buttons.Realize()

        shell = wx.BoxSizer(wx.VERTICAL)
        shell.Add(panel, 1, wx.EXPAND)
        shell.Add(buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 12)
        self.SetSizer(shell)
        self.SetMinSize((620, 430))
        self.Fit()
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key)
        self.activate_button.Bind(wx.EVT_BUTTON, self._activate)
        self.preset_list.Bind(wx.EVT_LISTBOX_DCLICK, self._activate)
        self.preset_list.SetFocus()

    @property
    def selected_choice(self) -> profile_presets.PresetChoice | None:
        index = self.preset_list.GetSelection()
        return self._choices[index] if 0 <= index < len(self._choices) else None

    def _on_key(self, event: wx.KeyEvent) -> None:
        slot = _preset_slot_from_event(event)
        if slot is not None:
            self.preset_list.SetSelection(slot - 1)
            return
        code = event.GetKeyCode()
        if not event.ControlDown() and not event.AltDown() and not event.ShiftDown():
            if code in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER, wx.WXK_SPACE):
                self._activate(event)
                return
        event.Skip()

    def _activate(self, _event) -> None:
        choice = self.selected_choice
        if choice is None:
            return
        if choice.target_id is None:
            self._announcer.say(
                f"Preset {choice.spoken_shortcut_label} pusty. "
                "Ctrl+Alt+Shift+P przypisuje bieżący element"
            )
            return
        self.EndModal(wx.ID_OK)


class WiiMOptionDialog(wx.Dialog):
    """Jedna opcja urządzenia; lista dostaje wyłącznie jawne etykiety."""

    def __init__(
        self,
        parent: wx.Window,
        *,
        title: str,
        description: str,
        choices: tuple[WiiMOptionChoice, ...],
        selected_index: int,
    ) -> None:
        super().__init__(parent, title=title)
        self._choices = choices
        panel = wx.Panel(self)
        layout = wx.BoxSizer(wx.VERTICAL)

        hint = wx.StaticText(panel, label=description)
        hint.SetName(description)
        layout.Add(hint, 0, wx.ALL | wx.EXPAND, 12)

        self.choice_list = wx.ListBox(
            panel,
            choices=[choice.label for choice in choices],
            style=wx.LB_SINGLE,
        )
        self.choice_list.SetName(title)
        self.choice_list.SetSelection(
            selected_index if 0 <= selected_index < len(choices) else 0
        )
        layout.Add(self.choice_list, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 12)
        panel.SetSizer(layout)

        buttons = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        shell = wx.BoxSizer(wx.VERTICAL)
        shell.Add(panel, 1, wx.EXPAND)
        shell.Add(buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 12)
        self.SetSizer(shell)
        self.SetMinSize((620, 390))
        self.Fit()
        self.choice_list.Bind(wx.EVT_LISTBOX_DCLICK, self._accept)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key)
        self.choice_list.SetFocus()

    @property
    def selected_choice(self) -> WiiMOptionChoice | None:
        index = self.choice_list.GetSelection()
        return self._choices[index] if 0 <= index < len(self._choices) else None

    def _on_key(self, event: wx.KeyEvent) -> None:
        if not event.ControlDown() and not event.AltDown() and not event.ShiftDown():
            if event.GetKeyCode() in (
                wx.WXK_RETURN,
                wx.WXK_NUMPAD_ENTER,
                wx.WXK_SPACE,
            ):
                self._accept(event)
                return
        event.Skip()

    def _accept(self, _event) -> None:
        if self.selected_choice is not None:
            self.EndModal(wx.ID_OK)


class WiiMPresetListDialog(wx.Dialog):
    """Natywne presety urządzenia, z tymi samymi 12 miejscami co pełne AMC."""

    def __init__(
        self,
        parent: wx.Window,
        *,
        choices: tuple[WiiMPresetChoice, ...],
        device_title: str,
        shortcut_slots_by_preset: dict[int, int] | None = None,
        select_for_shortcut: bool = False,
    ) -> None:
        super().__init__(
            parent,
            title=(
                f"Wybierz gotowy preset — {device_title}"
                if select_for_shortcut
                else f"Presety urządzenia — {device_title}"
            ),
        )
        self._choices = choices
        self.shortcut_assignment_requested = bool(select_for_shortcut)
        shortcut_slots_by_preset = shortcut_slots_by_preset or {}
        panel = wx.Panel(self)
        layout = wx.BoxSizer(wx.VERTICAL)

        description_text = (
            f"Wybierz istniejący preset urządzenia {device_title}, który "
            "chcesz przypisać do skrótu AMC. Cyfra wybiera preset. "
            "Enter lub Spacja przechodzi do wyboru skrótu. Escape anuluje."
            if select_for_shortcut else
            f"Presety zapisane w urządzeniu {device_title}. Cyfra wybiera "
            "miejsce. Page Up i Page Down przechodzą po zajętych miejscach. "
            "Enter lub Spacja uruchamia zajęty preset. Ctrl+Alt+Shift+P "
            "przypisuje zaznaczony preset do skrótu AMC."
        )
        description = wx.StaticText(panel, label=description_text)
        description.SetName(description_text)
        layout.Add(description, 0, wx.ALL | wx.EXPAND, 12)

        self.preset_list = wx.ListBox(
            panel,
            choices=[
                (
                    f"{choice.label}, skrót Ctrl+Shift+"
                    f"{profile_presets.shortcut_label(shortcut_slots_by_preset[choice.number], spoken=True)}"
                    if choice.number in shortcut_slots_by_preset
                    else choice.label
                )
                for choice in choices
            ],
            style=wx.LB_SINGLE,
        )
        self.preset_list.SetName(f"Presety urządzenia, {device_title}")
        self.preset_list.SetToolTip(
            "Cyfra wybiera miejsce. Page Up i Page Down przechodzą po "
            "zajętych presetach. Enter albo Spacja uruchamia."
        )
        selected = next(
            (index for index, choice in enumerate(choices) if choice.current),
            -1,
        )
        if selected < 0:
            selected = next(
                (index for index, choice in enumerate(choices) if choice.occupied),
                0,
            )
        self.preset_list.SetSelection(selected)
        layout.Add(self.preset_list, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 12)

        self.status = wx.StaticText(panel, label="Gotowe")
        self.status.SetName("Gotowe")
        self._announcer = Announcer(self.status)
        layout.Add(self.status, 0, wx.ALL | wx.EXPAND, 12)
        panel.SetSizer(layout)

        buttons = wx.StdDialogButtonSizer()
        self.activate_button = wx.Button(
            self,
            wx.ID_OK,
            label="&Wybierz" if select_for_shortcut else "&Uruchom",
        )
        self.activate_button.SetName(
            "Wybierz preset do przypisania"
            if select_for_shortcut else "Uruchom preset urządzenia"
        )
        self.activate_button.SetDefault()
        self.assign_button: wx.Button | None = None
        if not select_for_shortcut:
            self.assign_button = wx.Button(self, label="&Przypisz skrót…")
            self.assign_button.SetName("Przypisz skrót do zaznaczonego presetu")
        close = wx.Button(self, wx.ID_CANCEL, label="&Zamknij")
        close.SetName("Zamknij listę presetów urządzenia")
        buttons.AddButton(self.activate_button)
        if self.assign_button is not None:
            buttons.AddButton(self.assign_button)
        buttons.AddButton(close)
        buttons.Realize()

        shell = wx.BoxSizer(wx.VERTICAL)
        shell.Add(panel, 1, wx.EXPAND)
        shell.Add(buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 12)
        self.SetSizer(shell)
        self.SetMinSize((620, 430))
        self.Fit()
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key)
        self.activate_button.Bind(wx.EVT_BUTTON, self._activate)
        if self.assign_button is not None:
            self.assign_button.Bind(wx.EVT_BUTTON, self._assign)
        self.preset_list.Bind(wx.EVT_LISTBOX_DCLICK, self._activate)
        self.preset_list.SetFocus()

    @property
    def selected_choice(self) -> WiiMPresetChoice | None:
        index = self.preset_list.GetSelection()
        return self._choices[index] if 0 <= index < len(self._choices) else None

    def _on_key(self, event: wx.KeyEvent) -> None:
        if (
            not self.shortcut_assignment_requested
            and event.ControlDown()
            and event.AltDown()
            and event.ShiftDown()
            and chord_from_event(event).key == "P"
        ):
            self._assign(event)
            return
        slot = _preset_slot_from_event(event)
        if slot is not None:
            self.preset_list.SetSelection(slot - 1)
            return
        code = event.GetKeyCode()
        if not event.ControlDown() and not event.AltDown() and not event.ShiftDown():
            if code in (wx.WXK_PAGEUP, wx.WXK_PAGEDOWN):
                self._move_to_occupied(1 if code == wx.WXK_PAGEDOWN else -1)
                return
            if code in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER, wx.WXK_SPACE):
                self._activate(event)
                return
        event.Skip()

    def _move_to_occupied(self, direction: int) -> None:
        if not any(choice.occupied for choice in self._choices):
            self._announcer.say("Brak zajętych presetów urządzenia")
            return
        current = max(0, self.preset_list.GetSelection())
        for offset in range(1, len(self._choices) + 1):
            index = (current + direction * offset) % len(self._choices)
            if self._choices[index].occupied:
                self.preset_list.SetSelection(index)
                return

    def _activate(self, _event) -> None:
        choice = self.selected_choice
        if choice is None:
            return
        if not choice.occupied:
            self._announcer.say(f"Preset {choice.number} jest pusty")
            return
        if choice.activation_error and not self.shortcut_assignment_requested:
            self._announcer.say(choice.activation_error)
            return
        self.EndModal(wx.ID_OK)

    def _assign(self, _event) -> None:
        choice = self.selected_choice
        if choice is None:
            return
        if not choice.occupied:
            self._announcer.say(f"Preset {choice.number} jest pusty")
            return
        self.shortcut_assignment_requested = True
        self.EndModal(wx.ID_OK)


class PresetAssignmentDialog(wx.Dialog):
    """Przypisanie z ochrona zajetego miejsca i osobnym trybem usuwania."""

    def __init__(
        self,
        parent: wx.Window,
        *,
        target: profile_presets.PresetTarget,
        choices: tuple[profile_presets.PresetChoice, ...],
        first_free_slot: int | None,
        initial_slot: int,
        session_name: str,
        fixed_target_title: str = "",
        fixed_target_available: bool = False,
        fixed_target_initially_selected: bool = False,
    ) -> None:
        super().__init__(parent, title=f"Przypisz preset — {session_name}")
        self._target = target
        self._choices = choices
        self.selected_slot = 0
        self.selected_action = ""
        self._remove_pending = False
        self._last_requested_slot: int | None = None
        self._replacement_armed_slot: int | None = None
        self.fixed_target_checkbox: wx.CheckBox | None = None

        panel = wx.Panel(self)
        layout = wx.BoxSizer(wx.VERTICAL)
        if first_free_slot is not None:
            free = profile_presets.shortcut_label(first_free_slot, spoken=True)
            description_text = (
                f"Dodaj preset: {target.title}. Pierwsze wolne miejsce: "
                f"preset {profile_presets.shortcut_label(first_free_slot)}, "
                f"skrót Ctrl+Shift+{free}. Naciśnij cyfrę, minus albo znak "
                "równości, a następnie Enter. Escape anuluje."
            )
        else:
            description_text = (
                f"Dodaj preset: {target.title}. Nie ma wolnego miejsca. "
                "Aby zastąpić zajęty preset, wskaż dwukrotnie to samo miejsce "
                "i naciśnij Enter. Escape anuluje."
            )
        description = wx.StaticText(panel, label=description_text)
        description.SetName(description_text)
        layout.Add(description, 0, wx.ALL | wx.EXPAND, 12)

        self.preset_list = wx.ListBox(
            panel,
            choices=[choice.label for choice in choices],
            style=wx.LB_SINGLE,
        )
        self.preset_list.SetName("Miejsca presetów")
        self.preset_list.SetToolTip(
            "Cyfra, minus lub znak równości wybiera miejsce. "
            "Enter zapisuje lub zastępuje. Delete przygotowuje usunięcie."
        )
        self.preset_list.SetSelection(max(0, min(len(choices) - 1, initial_slot - 1)))
        layout.Add(self.preset_list, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 12)

        if fixed_target_available and fixed_target_title.strip():
            fixed_label = (
                "Zawsze na tym zestawie głośników: "
                f"{fixed_target_title.strip()}"
            )
            self.fixed_target_checkbox = wx.CheckBox(panel, label=fixed_label)
            self.fixed_target_checkbox.SetName(fixed_label)
            self.fixed_target_checkbox.SetValue(
                bool(fixed_target_initially_selected)
            )
            layout.Add(
                self.fixed_target_checkbox,
                0,
                wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND,
                12,
            )

        self.status = wx.StaticText(panel, label="Gotowe")
        self.status.SetName("Gotowe")
        self._announcer = Announcer(self.status)
        layout.Add(self.status, 0, wx.ALL | wx.EXPAND, 12)
        panel.SetSizer(layout)

        buttons = wx.StdDialogButtonSizer()
        self.save_button = wx.Button(self, wx.ID_OK, label="&Zapisz")
        self.save_button.SetName("Zapisz preset")
        self.save_button.SetDefault()
        cancel = wx.Button(self, wx.ID_CANCEL, label="&Anuluj")
        cancel.SetName("Anuluj przypisanie presetu")
        buttons.AddButton(self.save_button)
        buttons.AddButton(cancel)
        buttons.Realize()

        shell = wx.BoxSizer(wx.VERTICAL)
        shell.Add(panel, 1, wx.EXPAND)
        shell.Add(buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 12)
        self.SetSizer(shell)
        self.SetMinSize((650, 460))
        self.Fit()
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key)
        self.preset_list.Bind(wx.EVT_LISTBOX, self._on_list_selection)
        self.save_button.Bind(wx.EVT_BUTTON, self._confirm)
        self.preset_list.SetFocus()

    @property
    def selected_choice(self) -> profile_presets.PresetChoice | None:
        index = self.preset_list.GetSelection()
        return self._choices[index] if 0 <= index < len(self._choices) else None

    @property
    def fixed_target_selected(self) -> bool:
        return bool(
            self.fixed_target_checkbox is not None
            and self.fixed_target_checkbox.GetValue()
        )

    def _on_key(self, event: wx.KeyEvent) -> None:
        slot = _preset_slot_from_event(event)
        if slot is not None:
            self._select_slot(slot, announce=True)
            return
        if not event.ControlDown() and not event.AltDown() and not event.ShiftDown():
            code = event.GetKeyCode()
            if code == wx.WXK_DELETE:
                self._prepare_removal()
                return
            if code in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
                self._confirm(event)
                return
        event.Skip()

    def _on_list_selection(self, event) -> None:
        self._remove_pending = False
        self._last_requested_slot = None
        self._replacement_armed_slot = None
        event.Skip()

    def _select_slot(self, slot: int, *, announce: bool) -> None:
        self._remove_pending = False
        previous = self.selected_choice
        repeated = (
            self._last_requested_slot == slot
            and previous is not None
            and previous.slot == slot
        )
        self._last_requested_slot = slot
        self.preset_list.SetSelection(slot - 1)
        choice = self.selected_choice
        if choice is None:
            return
        replaces_other = (
            choice.target_id is not None
            and not profile_presets.choice_matches_target(choice, self._target)
        )
        self._replacement_armed_slot = slot if replaces_other and repeated else None
        if not announce:
            return
        slot_name = f"Preset {choice.slot_label}"
        if choice.target_id is None:
            text = f"{slot_name} pusty. {self._target.title}. Enter zapisuje, Escape anuluje"
        elif not replaces_other:
            text = f"{slot_name} już zawiera ten element. Enter zatwierdza, Escape anuluje"
        elif self._replacement_armed_slot == slot:
            text = (
                f"Potwierdzono {slot_name}. Enter zastępuje element "
                f"{choice.target_title} elementem {self._target.title}, Escape anuluje"
            )
        else:
            text = (
                f"{slot_name} zajęty: {choice.target_title}. Naciśnij ponownie "
                f"{choice.spoken_shortcut_label}, a następnie Enter, aby zastąpić; "
                "inny klawisz wybiera inne miejsce; Escape anuluje"
            )
        self._announcer.say(text)

    def _prepare_removal(self) -> None:
        choice = self.selected_choice
        if choice is None:
            return
        if choice.target_id is None:
            self._announcer.say(f"Preset {choice.slot_label} jest już pusty")
            return
        self._remove_pending = True
        self._announcer.say(
            f"Usunąć preset {choice.slot_label}: {choice.target_title}? "
            "Enter potwierdza, Escape anuluje"
        )

    def _confirm(self, _event) -> None:
        choice = self.selected_choice
        if choice is None:
            return
        replaces_other = (
            choice.target_id is not None
            and not profile_presets.choice_matches_target(choice, self._target)
        )
        if (
            not self._remove_pending
            and replaces_other
            and self._replacement_armed_slot != choice.slot
        ):
            self._announcer.say(
                f"Preset {choice.slot_label} jest zajęty przez {choice.target_title}. "
                f"Naciśnij dwa razy {choice.spoken_shortcut_label}, a następnie "
                "Enter, aby zastąpić, albo Escape, aby anulować"
            )
            return
        self.selected_slot = choice.slot
        self.selected_action = "remove" if self._remove_pending else "save"
        self.EndModal(wx.ID_OK)


class PodcastPlaybackOptionsDialog(wx.Dialog):
    """Natywne opcje jednego podcastu albo odcinka.

    Kontrolki dostają wyłącznie jawne polskie napisy. Wartości protokołu są
    przechowywane obok listy etykiet, więc NVDA nie może przeczytać numeru
    enuma, identyfikatora ani reprezentacji obiektu.
    """

    _RATES: tuple[float, ...] = (0.50, 0.75, 1.00, 1.25, 1.50, 1.75, 2.00)
    _SILENCES: tuple[int, ...] = (0, 500, 1000, 2000, 3000, 5000)
    _REFRESH: tuple[tuple[str, int], ...] = (
        ("Tylko ręcznie", 0),
        ("Co 15 minut", 15),
        ("Co 30 minut", 30),
        ("Co godzinę", 60),
        ("Co 3 godziny", 180),
        ("Co 6 godzin", 360),
        ("Co 12 godzin", 720),
        ("Raz dziennie", 1440),
    )

    def __init__(self, parent: wx.Window, options: dict) -> None:
        self._target = "podcast" if options.get("target") == "podcast" else "episode"
        podcast = self._target == "podcast"
        super().__init__(
            parent,
            title="Opcje podcastu" if podcast else "Opcje odcinka podcastu",
        )
        panel = wx.ScrolledWindow(self, style=wx.VSCROLL)
        panel.SetScrollRate(0, 12)
        form = wx.FlexGridSizer(0, 2, 8, 8)
        form.AddGrowableCol(1, 1)
        self._first: wx.Choice | None = None

        title = str(options.get("title") or (
            "Podcast bez nazwy" if podcast else "Odcinek bez nazwy"
        )).strip()
        heading = wx.StaticText(panel, label=title)
        heading.SetName(title)
        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(heading, 0, wx.ALL | wx.EXPAND, 12)

        resume_inherited = (
            "Domyślnie dla Podcastów — pamiętaj pozycję"
            if podcast
            else "Według podcastu; bez ustawienia — pamiętaj pozycję"
        )
        self.resume = self._add_choice(
            panel,
            form,
            "&Pozycja odtwarzania odcinków:" if podcast else "&Pozycja odtwarzania odcinka:",
            "Pozycja odtwarzania odcinków podcastu" if podcast else "Pozycja odtwarzania tego odcinka",
            (
                ("Pamiętaj pozycję odtwarzania", 1),
                ("Zawsze od początku", 2),
                (resume_inherited, 0),
            ),
            self._integer(options.get("resumePositionMode"), 0),
        )

        inherited_rate = (
            "Według prędkości sesji"
            if podcast
            else "Według podcastu lub prędkości sesji"
        )
        rate_choices: tuple[tuple[str, float | None], ...] = (
            (inherited_rate, None),
        ) + tuple((self._rate_label(rate), rate) for rate in self._RATES)
        self.rate = self._add_choice(
            panel,
            form,
            "P&rędkość odcinków podcastu:" if podcast else "P&rędkość tego odcinka:",
            "Prędkość odcinków podcastu" if podcast else "Prędkość tego odcinka",
            rate_choices,
            self._number_or_none(options.get("playbackRate")),
        )

        inherited = (
            "Według ustawienia globalnego"
            if podcast
            else "Według podcastu, sesji lub ustawienia globalnego"
        )
        tristate: tuple[tuple[str, bool | None], ...] = (
            (inherited, None),
            ("Włączone", True),
            ("Wyłączone", False),
        )
        self.loudness = self._add_choice(
            panel, form, "&Normalizacja głośności:", "Normalizacja głośności",
            tristate, self._bool_or_none(options.get("loudnessNormalization")),
        )
        self.transitions = self._add_choice(
            panel, form, "Łagodne p&rzejścia:", "Łagodne przejścia",
            tristate, self._bool_or_none(options.get("smoothTrackTransitions")),
        )

        silence_choices: tuple[tuple[str, int | None], ...] = (
            (inherited, None),
        ) + tuple(
            (
                "Bez dodatkowej ciszy"
                if value == 0
                else f"Cisza: {session_options.inter_track_silence_label(value)}",
                value,
            )
            for value in self._SILENCES
        )
        self.silence = self._add_choice(
            panel,
            form,
            "&Cisza po odcinkach podcastu:" if podcast else "&Cisza po tym odcinku:",
            "Cisza po odcinkach podcastu" if podcast else "Cisza po tym odcinku",
            silence_choices,
            self._integer_or_none(options.get("interTrackSilenceMs")),
        )

        tempo_choices: tuple[tuple[str, int | None], ...] = (
            (inherited, None),
            ("Mowa — Speedy", 1),
            ("Muzyka — Signalsmith", 2),
            ("Dotychczasowy — SoundTouch", 0),
        )
        self.tempo = self._add_choice(
            panel, form, "Spo&sób przeliczania tempa:", "Sposób przeliczania tempa",
            tempo_choices, self._integer_or_none(options.get("tempoAlgorithm")),
        )

        self.refresh: wx.Choice | None = None
        self.folder_mode: wx.Choice | None = None
        self.folder_text: wx.TextCtrl | None = None
        self.folder_button: wx.Button | None = None
        if podcast:
            self.refresh = self._add_choice(
                panel, form, "Automatyczne &odświeżanie podcastu:",
                "Automatyczne odświeżanie podcastu", self._REFRESH,
                self._integer(options.get("refreshIntervalMinutes"), 0),
            )
            folder = str(options.get("downloadsFolder") or "").strip()
            folder_modes: tuple[tuple[str, bool], ...] = (
                ("Zgodnie z ustawieniem Podcastów", False),
                ("Własny folder dla tego podcastu", True),
            )
            self.folder_mode = self._add_choice(
                panel, form, "&Folder pobierania odcinków:",
                "Folder pobierania odcinków tego podcastu", folder_modes,
                bool(folder),
            )
            label = wx.StaticText(panel, label="Własny f&older pobierania:")
            folder_row = wx.BoxSizer(wx.HORIZONTAL)
            self.folder_text = wx.TextCtrl(panel, value=folder, style=wx.TE_READONLY)
            self.folder_text.SetName("Własny folder pobierania tego podcastu")
            self.folder_button = wx.Button(panel, label="&Wybierz…")
            self.folder_button.SetName("Wybierz własny folder pobierania tego podcastu")
            self.folder_button.Bind(wx.EVT_BUTTON, self._choose_folder)
            self.folder_mode.Bind(wx.EVT_CHOICE, self._update_folder_controls)
            folder_row.Add(self.folder_text, 1, wx.RIGHT | wx.EXPAND, 8)
            folder_row.Add(self.folder_button, 0)
            form.AddMany(((label, 0, wx.ALIGN_CENTER_VERTICAL), (folder_row, 1, wx.EXPAND)))
            self._update_folder_controls(None)

        outer.Add(form, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 12)
        panel.SetSizer(outer)

        self.save_button = wx.Button(self, wx.ID_OK, label="&Zapisz")
        self.save_button.SetName("Zapisz opcje odtwarzania")
        self.save_button.SetDefault()
        self.save_button.Bind(wx.EVT_BUTTON, self._save)
        cancel = wx.Button(self, wx.ID_CANCEL, label="&Anuluj")
        cancel.SetName("Anuluj opcje odtwarzania")
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.Add(self.save_button, 0, wx.RIGHT, 8)
        buttons.Add(cancel, 0)

        shell = wx.BoxSizer(wx.VERTICAL)
        shell.Add(panel, 1, wx.EXPAND)
        shell.Add(buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 12)
        self.SetSizer(shell)
        self.SetMinSize((680, 620))
        self.SetSize((760, 780))
        if self._first is not None:
            self._first.SetFocus()

    @staticmethod
    def _integer(value, fallback: int) -> int:
        return value if type(value) is int else fallback

    @staticmethod
    def _integer_or_none(value) -> int | None:
        return value if type(value) is int else None

    @staticmethod
    def _number_or_none(value) -> float | None:
        return float(value) if type(value) in (int, float) else None

    @staticmethod
    def _bool_or_none(value) -> bool | None:
        return value if type(value) is bool else None

    @staticmethod
    def _rate_label(rate: float) -> str:
        value = f"{rate:.2f}".replace(".", ",")
        if rate < 1.0:
            return f"{value} razy — wolniej"
        if rate > 1.0:
            return f"{value} razy — szybciej"
        return f"{value} razy — normalna prędkość"

    def _add_choice(self, panel, grid, label, name, choices, current) -> wx.Choice:
        static = wx.StaticText(panel, label=label)
        control = wx.Choice(panel, choices=[text for text, _ in choices])
        control.SetName(name)
        control._amc_values = [value for _, value in choices]  # type: ignore[attr-defined]
        index = next(
            (
                i for i, (_, value) in enumerate(choices)
                if value == current and type(value) is type(current)
            ),
            0,
        )
        control.SetSelection(index)
        grid.AddMany(((static, 0, wx.ALIGN_CENTER_VERTICAL), (control, 1, wx.EXPAND)))
        if self._first is None:
            self._first = control
        return control

    @staticmethod
    def _choice_value(control: wx.Choice | None):
        if control is None or control.GetSelection() < 0:
            return None
        return control._amc_values[control.GetSelection()]  # type: ignore[attr-defined]

    def _update_folder_controls(self, _event) -> None:
        custom = self._choice_value(self.folder_mode) is True
        if self.folder_text is not None:
            self.folder_text.Enable(custom)
        if self.folder_button is not None:
            self.folder_button.Enable(custom)

    def _choose_folder(self, _event) -> None:
        initial = self.folder_text.GetValue() if self.folder_text is not None else ""
        with wx.DirDialog(
            self,
            "Wybierz folder pobierania odcinków tego podcastu",
            defaultPath=initial,
            style=wx.DD_DIR_MUST_EXIST,
        ) as dialog:
            if dialog.ShowModal() == wx.ID_OK and self.folder_text is not None:
                self.folder_text.SetValue(dialog.GetPath())
        if self.folder_button is not None:
            self.folder_button.SetFocus()

    def _save(self, _event) -> None:
        if self._choice_value(self.folder_mode) is True:
            folder = self.folder_text.GetValue().strip() if self.folder_text else ""
            if not folder or not Path(folder).is_absolute():
                dialog = wx.MessageDialog(
                    self,
                    "Wybierz pełną ścieżkę własnego folderu albo użyj folderu ogólnego Podcastów.",
                    "Folder pobierania podcastu",
                    wx.OK | wx.ICON_INFORMATION,
                )
                try:
                    dialog.SetName("Folder pobierania podcastu")
                    dialog.ShowModal()
                finally:
                    dialog.Destroy()
                if self.folder_button is not None:
                    self.folder_button.SetFocus()
                return
        self.EndModal(wx.ID_OK)

    @property
    def values(self) -> dict[str, object]:
        podcast = self._target == "podcast"
        custom_folder = podcast and self._choice_value(self.folder_mode) is True
        return {
            "resumePositionMode": self._choice_value(self.resume),
            "playbackRate": self._choice_value(self.rate),
            "loudnessNormalization": self._choice_value(self.loudness),
            "smoothTrackTransitions": self._choice_value(self.transitions),
            "interTrackSilenceMs": self._choice_value(self.silence),
            "tempoAlgorithm": self._choice_value(self.tempo),
            **(
                {
                    "refreshIntervalMinutes": self._choice_value(self.refresh),
                    "downloadsFolder": (
                        self.folder_text.GetValue().strip()
                        if custom_folder and self.folder_text is not None
                        else None
                    ),
                }
                if podcast
                else {}
            ),
        }


def session_selection_labels(order: object = None) -> tuple[str, ...]:
    """Jawne teksty listy sesji; wartości modelu nigdy nie trafiają do UI."""
    return session_order.selection_labels(order)


class RelationDestinationDialog(wx.Dialog):
    """Krótka, natywna lista miejsc dostępnych pod prawą strzałką.

    Zwykłe ``wx.Menu`` jest przez NVDA przedstawiane jako „menu kontekstowe”,
    a jego tytuł staje się dodatkowym, pozornym wierszem. Ten dialog ma tylko
    prawdziwe działania użytkowe i jawnie nazwaną listę.
    """

    def __init__(
        self,
        parent: wx.Window,
        *,
        title: str,
        labels: tuple[str, ...],
    ) -> None:
        super().__init__(parent, title=title)
        self._labels = labels
        panel = wx.Panel(self)
        layout = wx.BoxSizer(wx.VERTICAL)

        hint_text = "Wybierz, dokąd przejść. Enter otwiera, Escape wraca."
        hint = wx.StaticText(panel, label=hint_text)
        hint.SetName(hint_text)
        layout.Add(hint, 0, wx.ALL | wx.EXPAND, 12)

        self.destinations = wx.ListBox(
            panel,
            choices=list(labels),
            style=wx.LB_SINGLE,
        )
        self.destinations.SetName("Dokąd przejść")
        if labels:
            self.destinations.SetSelection(0)
        layout.Add(self.destinations, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 12)
        panel.SetSizer(layout)

        buttons = wx.StdDialogButtonSizer()
        open_button = wx.Button(self, wx.ID_OK, label="&Otwórz")
        open_button.SetName("Otwórz wybrane miejsce")
        open_button.SetDefault()
        cancel_button = wx.Button(self, wx.ID_CANCEL, label="&Anuluj")
        cancel_button.SetName("Wróć bez przechodzenia")
        buttons.AddButton(open_button)
        buttons.AddButton(cancel_button)
        buttons.Realize()

        shell = wx.BoxSizer(wx.VERTICAL)
        shell.Add(panel, 1, wx.EXPAND)
        shell.Add(buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 12)
        self.SetSizer(shell)
        self.SetMinSize((520, 300))
        self.Fit()
        self.SetEscapeId(wx.ID_CANCEL)
        self.destinations.Bind(wx.EVT_LISTBOX_DCLICK, self._accept)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key)
        self.destinations.SetFocus()

    @property
    def selected_index(self) -> int | None:
        index = self.destinations.GetSelection()
        return index if 0 <= index < len(self._labels) else None

    def _accept(self, _event) -> None:
        if self.selected_index is not None:
            self.EndModal(wx.ID_OK)

    def _on_key(self, event: wx.KeyEvent) -> None:
        if not event.ControlDown() and not event.AltDown() and not event.ShiftDown():
            if event.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
                self._accept(event)
                return
        event.Skip()


class SessionSelectionDialog(wx.Dialog):
    """Natywna lista sesji z jawnymi etykietami dla czytnika ekranu."""

    SESSIONS: tuple[SessionId, ...] = tuple(SessionId)

    def __init__(
        self,
        parent: wx.Window,
        current: SessionId,
        order: object = None,
    ) -> None:
        super().__init__(parent, title="Wybór sesji")
        self.sessions = session_order.normalize(order)
        panel = wx.Panel(self)
        layout = wx.BoxSizer(wx.VERTICAL)

        hint_text = "Wybierz sesję. Enter przełącza, Escape anuluje."
        hint = wx.StaticText(panel, label=hint_text)
        hint.SetName(hint_text)
        layout.Add(hint, 0, wx.ALL | wx.EXPAND, 12)

        self.session_list = wx.ListBox(
            panel,
            choices=list(session_selection_labels(self.sessions)),
            style=wx.LB_SINGLE,
        )
        self.session_list.SetName("Sesje")
        selected = self.sessions.index(current) if current in self.sessions else 0
        self.session_list.SetSelection(selected)
        layout.Add(self.session_list, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 12)
        panel.SetSizer(layout)

        buttons = wx.StdDialogButtonSizer()
        select_button = wx.Button(self, wx.ID_OK, label="&Wybierz")
        select_button.SetName("Wybierz sesję")
        select_button.SetDefault()
        cancel_button = wx.Button(self, wx.ID_CANCEL, label="&Anuluj")
        cancel_button.SetName("Anuluj wybór sesji")
        buttons.AddButton(select_button)
        buttons.AddButton(cancel_button)
        buttons.Realize()

        shell = wx.BoxSizer(wx.VERTICAL)
        shell.Add(panel, 1, wx.EXPAND)
        shell.Add(buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 12)
        self.SetSizer(shell)
        self.SetMinSize((520, 360))
        self.Fit()
        self.session_list.Bind(wx.EVT_LISTBOX_DCLICK, self._accept)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key)
        self.session_list.SetFocus()

    @property
    def selected_session(self) -> SessionId | None:
        index = self.session_list.GetSelection()
        return self.sessions[index] if 0 <= index < len(self.sessions) else None

    def _accept(self, _event) -> None:
        if self.selected_session is not None:
            self.EndModal(wx.ID_OK)

    def _on_key(self, event: wx.KeyEvent) -> None:
        if not event.ControlDown() and not event.AltDown() and not event.ShiftDown():
            if event.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
                self._accept(event)
                return
        event.Skip()


class SessionOptionsDialog(wx.Dialog):
    """Opcje sesji. Pokazuje WYLACZNIE opcje, ktore ta sesja umie wykonac.

    Port ``SessionPlaybackOptionsEditor.CreateDialog`` (cs:33-70). Dwie
    rzeczy przeniesione z oryginalu swiadomie:

    * O tym, ktore kontrolki powstaja, decyduja ZDOLNOSCI sesji
      (``session_options.capabilities_for``), a nie to, czy pole istnieje w
      C#. Oryginal ukrywa niewykonalne pola (cs:59-66); my ich nie tworzymy
      wcale -- ukryta kontrolka nadal siedzi w kolejnosci Tab u czytnika.
    * Kazde pole ma wariant "Jak ustawienie ogólne", bo brak wyboru to w
      modelu ``None``, a nie falsz. Bez tego nie dalo by sie WROCIC do
      dziedziczenia po jednorazowym wyborze.

    Wszystkie kontrolki sa ZWYKLE natywne wx (``wx.Choice``) -- czytnik
    nazywa je sam, bez naszych komunikatow.
    """

    #: Kolejnosc wariantow trojstanowych. Dziedziczenie jest PIERWSZE, bo to
    #: stan domyslny; uzytkownik slyszy je przy otwarciu bez wlasnego wyboru.
    _TRISTATE: tuple[tuple[str, bool | None], ...] = (
        ("Jak ustawienie ogólne", None),
        ("Włączone", True),
        ("Wyłączone", False),
    )

    def __init__(self, parent: wx.Window, session, options, overrides, *, drafts=None) -> None:
        super().__init__(parent, title=session_options.dialog_title(session))
        self._options = options
        # Drafty WSZYSTKICH sesji: przelaczenie konfigurowanej sesji nie moze
        # zgubic tego, co uzytkownik juz wybral dla poprzedniej. Kontrakt:
        # Zapisz utrwala kazdy zmieniony draft, Anuluj zaden.
        self._drafts: dict = {
            SessionId.FILES: session_options.SessionPlaybackOverrides(),
            SessionId.RADIO: session_options.SessionPlaybackOverrides(),
            SessionId.PODCASTS: session_options.SessionPlaybackOverrides(),
        }
        if drafts:
            self._drafts.update(drafts)
        self._drafts[session] = overrides
        self._session = session
        self._caps = session_options.capabilities_for(session)
        panel = wx.Panel(self)
        self._panel = panel
        outer = wx.BoxSizer(wx.VERTICAL)
        self._outer = outer

        # WYBOR KONFIGUROWANEJ SESJI. Sam tytul okna nie jest wyborem: bez tej
        # kontrolki dialog konfigurowal WYLACZNIE sesje, ktora wlasnie gra, a
        # wymaganie jest odwrotne -- skonfigurowac druga sesje BEZ przelaczenia
        # odsluchu. Dialog nie dotyka ani ``_switch_session``, ani transportu.
        sessions = [SessionId.FILES, SessionId.RADIO, SessionId.PODCASTS]
        self._sessions = sessions
        row = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(panel, label="Konfigurowana &sesja:")
        self.session_choice = wx.Choice(
            panel,
            choices=[session_options.session_display_name(item) for item in sessions],
        )
        self.session_choice.SetName("Konfigurowana sesja")
        self.session_choice.SetSelection(sessions.index(session))
        self.session_choice.Bind(wx.EVT_CHOICE, self._on_session_changed)
        row.Add(label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        row.Add(self.session_choice, 1, wx.EXPAND)
        outer.Add(row, 0, wx.ALL | wx.EXPAND, 12)

        # Pola opcji siedza w WYMIENIANYM kontenerze: zdolnosci sesji decyduja
        # o tym, ktore kontrolki istnieja, wiec przelaczenie sesji buduje je od
        # nowa (ukryta kontrolka nadal siedzi w kolejnosci Tab u czytnika).
        self._fields_panel: wx.Panel | None = None
        self._fields_slot = wx.BoxSizer(wx.VERTICAL)
        outer.Add(self._fields_slot, 1, wx.EXPAND)

        # Przyciski sa dziecmi DIALOGU, nie panelu -- patrz uwaga w
        # ``StationDialog``: inaczej wxWidgets przerywa asercja i modalna
        # petla nie wraca, a okno trzyma fokus bez obrazu.
        buttons = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        shell = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(outer)
        shell.Add(panel, 1, wx.EXPAND)
        shell.Add(buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 12)
        self.SetSizer(shell)
        self._build_fields()

    @property
    def session(self):
        """Sesja AKTUALNIE konfigurowana w dialogu."""
        return self._session

    def _on_session_changed(self, _event) -> None:
        """Przelaczenie konfigurowanej sesji. NIE zmienia odsluchu.

        Wybory biezacej sesji ida do draftu, zeby wrocily po powrocie.
        """
        index = self.session_choice.GetSelection()
        if index < 0:
            return
        wanted = self._sessions[index]
        if wanted is self._session:
            return
        self._drafts[self._session] = self._collect()
        self._session = wanted
        self._caps = session_options.capabilities_for(wanted)
        self._build_fields()

    def _build_fields(self) -> None:
        """Zbuduj pola opcji dla BIEZACEJ sesji z jej draftu."""
        overrides = self._drafts[self._session]
        options = self._options
        if self._fields_panel is not None:
            self._fields_slot.Clear(True)
        panel = wx.Panel(self._panel)
        self._fields_panel = panel
        self._fields_slot.Add(panel, 1, wx.EXPAND)
        grid = wx.FlexGridSizer(0, 2, 8, 8)
        self._first = None

        self.loudness = None
        self.transitions = None
        self.silence = None
        self.pause = None

        if self._caps.supports_audio_processing:
            self.loudness = self._add_choice(
                panel, grid, "&Normalizacja głośności:", "Normalizacja głośności",
                self._TRISTATE, overrides.loudness_normalization,
            )
            self.transitions = self._add_choice(
                panel, grid, "Łagodne &przejścia między utworami:",
                "Łagodne przejścia między utworami",
                self._TRISTATE, overrides.smooth_track_transitions,
            )
            # Tylko dlugosci, ktore silnik przyjmuje (LiteAudioSettings.cs:15).
            silence_choices: tuple[tuple[str, int | None], ...] = (
                ("Jak ustawienie ogólne", None),
            ) + tuple(
                (session_options.inter_track_silence_label(value), value)
                for value in session_options.INTER_TRACK_SILENCE_CHOICES
            )
            self.silence = self._add_choice(
                panel, grid, "&Cisza między utworami:", "Cisza między utworami",
                silence_choices, overrides.inter_track_silence_ms,
            )

        if self._caps.supports_player_exit_pause:
            # Etykieta wariantu dziedziczonego mowi WPROST, co z niego wynika
            # (jak ``PlayerExitPausePolicy.DescribeSessionMode``) -- inaczej
            # uzytkownik musialby sprawdzac ustawienia ogolne osobnym gestem.
            inherited = (
                "Jak ustawienie ogólne: wstrzymuj"
                if options.pause_on_player_exit
                else "Jak ustawienie ogólne: odtwarzaj dalej"
            )
            self.pause = self._add_choice(
                panel, grid, "Po &wyjściu z odtwarzacza:", "Po wyjściu z odtwarzacza",
                (
                    (inherited, None),
                    ("Wstrzymuj odtwarzanie", True),
                    ("Odtwarzaj dalej", False),
                ),
                overrides.pause_on_player_exit,
            )

        grid.AddGrowableCol(1, 1)
        inner = wx.BoxSizer(wx.VERTICAL)
        inner.Add(grid, 1, wx.ALL | wx.EXPAND, 12)
        panel.SetSizer(inner)
        self.Fit()
        self.Layout()
        if self._first is not None:
            self._first.SetFocus()

    def _add_choice(self, panel, grid, label, name, choices, current) -> wx.Choice:
        """Jedna zwykla lista wyboru z etykieta. Etykieta ma skrot literowy."""
        static = wx.StaticText(panel, label=label)
        control = wx.Choice(panel, choices=[text for text, _ in choices])
        # Nazwa dostepnosciowa BEZ znaku ``&`` i bez dwukropka: czytnik czyta
        # nazwe kontrolki, a nie tekst etykiety graficznej.
        control.SetName(name)
        control._amc_values = [value for _, value in choices]  # type: ignore[attr-defined]
        index = next(
            (i for i, (_, value) in enumerate(choices) if value == current and type(value) is type(current)),
            0,
        )
        control.SetSelection(index)
        grid.AddMany(
            [(static, 0, wx.ALIGN_CENTER_VERTICAL), (control, 1, wx.EXPAND)]
        )
        if self._first is None:
            self._first = control
        return control

    @staticmethod
    def _value(control: wx.Choice | None):
        if control is None:
            return None
        index = control.GetSelection()
        if index < 0:
            return None
        return control._amc_values[index]  # type: ignore[attr-defined]

    def _collect(self):
        """Wybory UZYTKOWNIKA dla BIEZACEJ sesji. Bez skutku ubocznego."""
        return session_options.SessionPlaybackOverrides(
            loudness_normalization=self._value(self.loudness),
            smooth_track_transitions=self._value(self.transitions),
            inter_track_silence_ms=self._value(self.silence),
            pause_on_player_exit=self._value(self.pause),
        )

    @property
    def overrides(self):
        """Wybory dla sesji aktualnie pokazanej w dialogu."""
        return self._collect()

    @property
    def drafts(self) -> dict:
        """Wybory KAZDEJ edytowanej sesji. Zapisz utrwala wszystkie.

        Bez tego skonfigurowanie drugiej sesji i zatwierdzenie przepadlo by:
        handler widzialby tylko sesje pokazana na koniec.
        """
        result = dict(self._drafts)
        result[self._session] = self._collect()
        return result


class AudioClipExportDialog(wx.Dialog):
    """Dostepny wybor SPOSOBU zapisu, oddzielony od wartosci protokolu.

    ``wx.Choice`` dostaje wylacznie jawne polskie etykiety. Wartosci
    ``original/flac/wav`` sa przechowywane osobno, wiec nazwa enumu ani repr
    obiektu nie moze trafic do UI Automation i mowy NVDA.
    """

    def __init__(
        self,
        parent: wx.Window,
        *,
        context: AudioClipContext,
        selection: AudioClipSelection,
        choices: list[AudioClipFormatChoice],
        notice: str,
    ) -> None:
        super().__init__(parent, title="Zapisz fragment audio")
        panel = wx.Panel(self)
        outer = wx.BoxSizer(wx.VERTICAL)

        start = format_clip_time(selection.start_seconds or 0.0)
        end = format_clip_time(selection.end_seconds or 0.0)
        duration = format_clip_time(
            (selection.end_seconds or 0.0) - (selection.start_seconds or 0.0)
        )
        summary = wx.StaticText(
            panel,
            label=(
                f"{context.title}. Od {start} do {end}. "
                f"Długość fragmentu: {duration}."
            ),
        )
        summary.SetName(summary.GetLabel())
        outer.Add(summary, 0, wx.ALL | wx.EXPAND, 12)

        label = wx.StaticText(panel, label="&Sposób zapisu:")
        self.format_choice = wx.Choice(panel, choices=[choice.label for choice in choices])
        self.format_choice.SetName("Sposób zapisu fragmentu")
        self._choices = choices
        self.format_choice.SetSelection(0)
        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        row.Add(self.format_choice, 1, wx.EXPAND)
        outer.Add(row, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 12)

        notice_text = wx.StaticText(panel, label=notice)
        notice_text.SetName(notice)
        outer.Add(notice_text, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 12)
        safety = wx.StaticText(
            panel,
            label=(
                "Plik źródłowy nigdy nie jest zmieniany. "
                "Wynik zostanie zapisany jako nowy plik."
            ),
        )
        safety.SetName(safety.GetLabel())
        outer.Add(safety, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 12)

        buttons = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        ok = self.FindWindowById(wx.ID_OK)
        if ok is not None:
            ok.SetLabel("&Wybierz plik…")
            ok.SetName("Wybierz plik")
        shell = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(outer)
        shell.Add(panel, 1, wx.EXPAND)
        shell.Add(buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 12)
        self.SetSizerAndFit(shell)

    @property
    def selected_format(self) -> AudioClipFormatChoice | None:
        index = self.format_choice.GetSelection()
        return self._choices[index] if 0 <= index < len(self._choices) else None


class AudioOutputDeviceDialog(wx.Dialog):
    """Natywny wybor wyjscia; do wx trafiaja tylko jawne etykiety."""

    def __init__(
        self,
        parent: wx.Window,
        session_name: str,
        choices: tuple[AudioOutputChoice, ...],
        selected_device_id: str | None,
    ) -> None:
        super().__init__(parent, title=f"Urządzenie audio — {session_name}")
        self._choices = choices
        panel = wx.Panel(self)
        label = wx.StaticText(panel, label="&Urządzenie audio:")
        self.device_choice = wx.Choice(
            panel,
            choices=[choice.label for choice in choices],
        )
        self.device_choice.SetName("Urządzenie audio")
        selected = next(
            (
                index
                for index, choice in enumerate(choices)
                if choice.device_id == selected_device_id
            ),
            0,
        )
        if choices:
            self.device_choice.SetSelection(selected)

        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        row.Add(self.device_choice, 1, wx.EXPAND)
        panel.SetSizer(row)
        buttons = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(panel, 1, wx.ALL | wx.EXPAND, 12)
        outer.Add(buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 12)
        self.SetSizerAndFit(outer)
        self.device_choice.SetFocus()

    @property
    def selected_choice(self) -> AudioOutputChoice | None:
        index = self.device_choice.GetSelection()
        return self._choices[index] if 0 <= index < len(self._choices) else None


class RadioRecognitionHistoryDialog(wx.Dialog):
    """Natywna, trwala historia wynikow rozpoznawania Radia."""

    def __init__(
        self,
        parent: wx.Window,
        entries: list[dict],
        *,
        copy_to_clipboard: Callable[[str], bool],
        announce: Callable[[str], None],
    ) -> None:
        super().__init__(parent, title="Rozpoznane utwory", size=(760, 540))
        self._entries = entries
        self._copy_to_clipboard = copy_to_clipboard
        self._announce = announce
        self._visible: list[dict] = []
        self._filter_keys: list[str | None] = []
        self.changed = False

        panel = wx.Panel(self)
        layout = wx.BoxSizer(wx.VERTICAL)
        help_text = (
            "Rozpoznane utwory, od najnowszego. Ctrl+C kopiuje opis, "
            "Ctrl+Shift+C kopiuje opis i łącza. Enter otwiera wynik "
            "dostawcy, Delete usuwa wybrane wpisy."
        )
        help_label = wx.StaticText(panel, label=help_text)
        help_label.SetName(help_text)
        help_label.Wrap(700)
        layout.Add(help_label, 0, wx.ALL | wx.EXPAND, 10)

        filter_label = wx.StaticText(panel, label="&Pokaż wpisy:")
        self.station_filter = wx.Choice(panel)
        self.station_filter.SetName("Filtr historii według stacji")
        layout.Add(filter_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        layout.Add(self.station_filter, 0, wx.ALL | wx.EXPAND, 10)

        self.history = wx.ListBox(panel, style=wx.LB_EXTENDED)
        self.history.SetName("Rozpoznane utwory")
        self.history.SetToolTip(help_text)
        layout.Add(self.history, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        self.status = wx.StaticText(panel, label="")
        self.status.SetName("Stan historii rozpoznawania")
        layout.Add(self.status, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        panel.SetSizer(layout)

        buttons = wx.StdDialogButtonSizer()
        copy_button = wx.Button(self, label="&Kopiuj")
        copy_button.SetName("Kopiuj opis")
        export_button = wx.Button(self, label="&Eksportuj…")
        export_button.SetName("Eksportuj historię")
        delete_button = wx.Button(self, label="&Usuń")
        delete_button.SetName("Usuń z historii")
        close_button = wx.Button(self, wx.ID_CANCEL, label="&Zamknij")
        close_button.SetName("Zamknij historię")
        for button in (copy_button, export_button, delete_button, close_button):
            buttons.AddButton(button)
        buttons.Realize()

        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(panel, 1, wx.EXPAND)
        outer.Add(buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 10)
        self.SetSizer(outer)
        self.SetMinSize((620, 420))

        self.station_filter.Bind(wx.EVT_CHOICE, self._on_filter)
        self.history.Bind(wx.EVT_CHAR_HOOK, self._on_key)
        self.history.Bind(wx.EVT_LISTBOX_DCLICK, self._on_open)
        copy_button.Bind(wx.EVT_BUTTON, self._on_copy)
        export_button.Bind(wx.EVT_BUTTON, self._on_export)
        delete_button.Bind(wx.EVT_BUTTON, self._on_delete)
        self._refresh_filters()
        self._refresh_rows()
        wx.CallAfter(self.history.SetFocus)

    @staticmethod
    def _station_key(entry: dict) -> str:
        station_id = str(entry.get("stationId") or "").strip()
        if station_id:
            return "id:" + station_id
        return "name:" + str(entry.get("stationName") or "").strip().casefold()

    def _refresh_filters(self, preferred: str | None = None) -> None:
        if preferred is None and self._filter_keys:
            index = self.station_filter.GetSelection()
            if 0 <= index < len(self._filter_keys):
                preferred = self._filter_keys[index]
        stations: dict[str, tuple[str, int]] = {}
        for entry in self._entries:
            key = self._station_key(entry)
            label = str(entry.get("stationName") or "Nieznana stacja").strip()
            ticks = int(entry.get("recognizedUtcTicks") or 0)
            previous = stations.get(key)
            if previous is None or ticks > previous[1]:
                stations[key] = (label or "Nieznana stacja", ticks)
        ordered = sorted(stations.items(), key=lambda item: item[1][0].casefold())
        self._filter_keys = [None, *(key for key, _value in ordered)]
        labels = ["Wszystkie stacje", *(value[0] for _key, value in ordered)]
        self.station_filter.Set(labels)
        try:
            selection = self._filter_keys.index(preferred)
        except ValueError:
            selection = 0
        self.station_filter.SetSelection(selection)

    def _refresh_rows(self, fallback_index: int = 0) -> None:
        filter_index = self.station_filter.GetSelection()
        filter_key = (
            self._filter_keys[filter_index]
            if 0 <= filter_index < len(self._filter_keys)
            else None
        )
        self._visible = [
            entry for entry in sorted(
                self._entries,
                key=lambda item: int(item.get("recognizedUtcTicks") or 0),
                reverse=True,
            )
            if filter_key is None or self._station_key(entry) == filter_key
        ]
        self.history.Set([
            radio_recognition.track_label(entry) for entry in self._visible
        ])
        if self._visible:
            self.history.SetSelection(
                max(0, min(fallback_index, len(self._visible) - 1))
            )
            filter_label = self.station_filter.GetStringSelection()
            text = f"Wpisów: {len(self._visible)}, {filter_label}"
        else:
            text = (
                "Historia jest pusta"
                if filter_key is None
                else "Brak wpisów dla wybranej stacji"
            )
        self.status.SetLabel(text)
        self.status.SetName(text)

    def _selected_entries(self) -> list[dict]:
        return [
            self._visible[index]
            for index in self.history.GetSelections()
            if 0 <= index < len(self._visible)
        ]

    def _set_status(self, text: str) -> None:
        self.status.SetLabel(text)
        self.status.SetName(text)
        self._announce(text)

    def _copy(self, *, links: bool) -> None:
        selected = self._selected_entries()
        if not selected:
            self._set_status("Brak wybranego wpisu")
            return
        formatter = radio_recognition.rich_text if links else radio_recognition.copy_text
        if not self._copy_to_clipboard(
            "\n\n".join(formatter(entry) for entry in selected)
        ):
            return
        if len(selected) == 1:
            self._set_status("Skopiowano opis i łącza" if links else "Skopiowano opis")
        else:
            subject = "opisy i łącza" if links else "opisy"
            self._set_status(f"Skopiowano {subject}: {len(selected)}")

    def _delete(self) -> None:
        selected = self._selected_entries()
        if not selected:
            self._set_status("Brak wpisu do usunięcia")
            return
        fallback = self.history.GetSelection()
        ids = {str(entry.get("id") or "") for entry in selected}
        self._entries[:] = [
            entry for entry in self._entries
            if str(entry.get("id") or "") not in ids
        ]
        self.changed = True
        self._refresh_filters()
        self._refresh_rows(max(0, fallback))
        self.history.SetFocus()
        self._set_status(
            "Usunięto wpis z historii rozpoznawania"
            if len(selected) == 1
            else f"Usunięto wpisy z historii rozpoznawania: {len(selected)}"
        )

    def _open_provider(self) -> None:
        selected = self._selected_entries()
        uri = str(selected[0].get("providerUri") or "") if selected else ""
        if not uri:
            self._set_status("Ten wynik nie zawiera łącza dostawcy rozpoznawania")
            return
        if not wx.LaunchDefaultBrowser(uri):
            self._set_status("Nie udało się otworzyć łącza")

    def _on_filter(self, _event: wx.CommandEvent) -> None:
        self._refresh_rows()
        self.history.SetFocus()

    def _on_key(self, event: wx.KeyEvent) -> None:
        chord = chord_from_event(event).canonical
        if chord == "Ctrl+Shift+C":
            self._copy(links=True)
            return
        if chord == "Ctrl+C":
            self._copy(links=False)
            return
        if chord == "Delete":
            self._delete()
            return
        if chord == "Return":
            self._open_provider()
            return
        if chord == "Escape":
            self.EndModal(wx.ID_CANCEL)
            return
        event.Skip()

    def _on_open(self, _event: wx.CommandEvent) -> None:
        self._open_provider()

    def _on_copy(self, _event: wx.CommandEvent) -> None:
        self._copy(links=False)

    def _on_delete(self, _event: wx.CommandEvent) -> None:
        self._delete()

    def _on_export(self, _event: wx.CommandEvent) -> None:
        if not self._entries:
            self._set_status("Historia jest pusta")
            return
        default_name = f"AMC - rozpoznane utwory - {time.strftime('%Y-%m-%d')}.json"
        with wx.FileDialog(
            self,
            "Eksportuj rozpoznane utwory",
            defaultFile=default_name,
            wildcard="Plik JSON (*.json)|*.json|Plik CSV (*.csv)|*.csv",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as dialog:
            if dialog.ShowModal() != wx.ID_OK:
                self.history.SetFocus()
                return
            path = dialog.GetPath()
        try:
            radio_recognition.export_history(path, self._entries)
        except OSError as error:
            self._set_status(f"Nie udało się zapisać pliku: {error}")
        else:
            self._set_status(f"Wyeksportowano historię: {Path(path).name}")
        self.history.SetFocus()


class GeneralPlaybackOptionsDialog(wx.Dialog):
    """Functional settings pages; every exposed value has a real effect."""

    def __init__(
        self,
        parent: wx.Window,
        options,
        recording,
        wake_scheduled_recordings: bool,
        podcast_settings: PodcastGlobalSettings,
        keep_audio_edit_backups: bool,
        custom_seek_seconds: int,
        global_transient_previews: bool,
        remember_local_playback_positions: bool,
        detailed_hints: bool,
        message_policy: MessagePolicy,
    ) -> None:
        super().__init__(parent, title="Ustawienia", size=(720, 620))
        self.notebook = wx.Notebook(self)
        self.notebook.SetName("Kategorie ustawień")

        general = wx.ScrolledWindow(self.notebook)
        general.SetScrollRate(0, 12)
        general_layout = wx.BoxSizer(wx.VERTICAL)

        startup_target_label = wx.StaticText(
            general, label="&Wyświetlaj po uruchomieniu:"
        )
        self._startup_target_values = ["MediaList", "SessionList"]
        self.startup_target = wx.Choice(
            general,
            choices=["Ostatnia używana sesja", "Lista sesji"],
        )
        self.startup_target.SetName("Wyświetlaj po uruchomieniu")
        try:
            startup_target_index = self._startup_target_values.index(
                options.startup_target
            )
        except ValueError:
            startup_target_index = 0
        self.startup_target.SetSelection(startup_target_index)
        general_layout.Add(startup_target_label, 0, wx.BOTTOM, 4)
        general_layout.Add(
            self.startup_target, 0, wx.BOTTOM | wx.EXPAND, 12
        )

        self.pause = wx.CheckBox(
            general, label="&Wstrzymuj odtwarzanie po wyjściu z odtwarzacza"
        )
        self.pause.SetName("Wstrzymuj odtwarzanie po wyjściu z odtwarzacza")
        self.pause.SetValue(options.pause_on_player_exit)

        self.follow = wx.CheckBox(
            general,
            label="Po wyjściu ustaw &fokus na aktualnie odtwarzanym elemencie",
        )
        self.follow.SetName(
            "Po wyjściu ustaw fokus na aktualnie odtwarzanym elemencie"
        )
        self.follow.SetValue(options.follow_playback_on_player_exit)

        self.open_preset = wx.CheckBox(
            general, label="Po uruchomieniu presetu &otwieraj odtwarzacz"
        )
        self.open_preset.SetName("Po uruchomieniu presetu otwieraj odtwarzacz")
        self.open_preset.SetValue(options.open_player_when_activating_preset)

        self.radio_enter = wx.CheckBox(
            general,
            label=(
                "Pozostawaj na li&ście po uruchomieniu stacji lub materiału "
                "Enterem"
            ),
        )
        self.radio_enter.SetName(
            "Pozostawaj na liście po uruchomieniu stacji lub materiału Enterem"
        )
        self.radio_enter.SetValue(options.stay_on_list_after_radio_enter)

        self.pause_output_fallback = wx.CheckBox(
            general,
            label=(
                "Po odłączeniu wybranego urządzenia przejdź na domyślne, "
                "ale &wstrzymaj dźwięk"
            ),
        )
        self.pause_output_fallback.SetName(
            "Po odłączeniu wybranego urządzenia przejdź na domyślne, ale wstrzymaj dźwięk"
        )
        self.pause_output_fallback.SetValue(
            options.pause_on_audio_output_fallback
        )

        self.keep_audio_edit_backups = wx.CheckBox(
            general, label="Zachowuj &kopie po edycji"
        )
        self.keep_audio_edit_backups.SetName("Zachowuj kopie po edycji")
        self.keep_audio_edit_backups.SetValue(keep_audio_edit_backups)

        self.global_transient_previews = wx.CheckBox(
            general,
            label=(
                "Wspólne podglądy &nagrywania i nowych odcinków "
                "we wszystkich sesjach"
            ),
        )
        self.global_transient_previews.SetName(
            "Wspólne podglądy nagrywania i nowych odcinków we wszystkich sesjach"
        )
        self.global_transient_previews.SetValue(global_transient_previews)

        self.remember_local_playback_positions = wx.CheckBox(
            general,
            label="Pamiętaj pozycję odtwarzania lokalnych &plików",
        )
        self.remember_local_playback_positions.SetName(
            "Pamiętaj pozycję odtwarzania lokalnych plików"
        )
        self.remember_local_playback_positions.SetValue(
            remember_local_playback_positions
        )

        for control in (
            self.pause,
            self.follow,
            self.open_preset,
            self.radio_enter,
            self.pause_output_fallback,
            self.keep_audio_edit_backups,
            self.global_transient_previews,
            self.remember_local_playback_positions,
        ):
            general_layout.Add(control, 0, wx.BOTTOM | wx.EXPAND, 10)

        session_order_label = wx.StaticText(
            general, label="Kolejność sesji i skrótów &Ctrl+1–9:"
        )
        self._session_order = list(session_order.normalize(options.session_order))
        self.session_order_list = wx.ListBox(
            general,
            choices=list(session_order.selection_labels(self._session_order)),
            style=wx.LB_SINGLE,
        )
        self.session_order_list.SetName(
            "Sesje: kolejność i skróty Control od 1 do 9"
        )
        self.session_order_list.SetHelpText(
            "Alt+strzałka w górę lub w dół zmienia położenie zaznaczonej sesji"
        )
        if self._session_order:
            self.session_order_list.SetSelection(0)
        self.session_order_list.Bind(wx.EVT_CHAR_HOOK, self._on_session_order_key)

        session_order_buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.session_up = wx.Button(general, label="Przenieś &wyżej")
        self.session_up.SetName("Przenieś zaznaczoną sesję wyżej")
        self.session_down = wx.Button(general, label="Przenieś &niżej")
        self.session_down.SetName("Przenieś zaznaczoną sesję niżej")
        self.session_default = wx.Button(
            general, label="Przywróć &domyślną kolejność"
        )
        self.session_default.SetName("Przywróć domyślną kolejność sesji")
        self.session_up.Bind(
            wx.EVT_BUTTON, lambda _event: self._move_session_order(-1)
        )
        self.session_down.Bind(
            wx.EVT_BUTTON, lambda _event: self._move_session_order(1)
        )
        self.session_default.Bind(
            wx.EVT_BUTTON, self._restore_default_session_order
        )
        session_order_buttons.Add(self.session_up, 0, wx.RIGHT, 8)
        session_order_buttons.Add(self.session_down, 0, wx.RIGHT, 8)
        session_order_buttons.Add(self.session_default, 0)
        general_layout.Add(session_order_label, 0, wx.TOP | wx.BOTTOM, 4)
        general_layout.Add(
            self.session_order_list, 0, wx.BOTTOM | wx.EXPAND, 8
        )
        general_layout.Add(
            session_order_buttons, 0, wx.BOTTOM | wx.EXPAND, 12
        )

        custom_seek_label = wx.StaticText(
            general,
            label="Dłuższy przeskok pod Ctrl+Alt+strzałką w &lewo i w prawo:",
        )
        self._custom_seek_seconds = custom_seek_seconds
        self.custom_seek = wx.ComboBox(
            general,
            choices=[
                describe_custom_seek_length(value)
                for value in SUGGESTED_CUSTOM_SEEK_SECONDS
            ],
            style=wx.CB_DROPDOWN,
        )
        self.custom_seek.SetName(
            "Długość przeskoku pod Ctrl+Alt+strzałką w lewo i w prawo"
        )
        if custom_seek_seconds in SUGGESTED_CUSTOM_SEEK_SECONDS:
            self.custom_seek.SetSelection(
                SUGGESTED_CUSTOM_SEEK_SECONDS.index(custom_seek_seconds)
            )
        else:
            self.custom_seek.SetValue(
                describe_custom_seek_length(custom_seek_seconds)
            )
        general_layout.Add(custom_seek_label, 0, wx.BOTTOM, 4)
        general_layout.Add(self.custom_seek, 0, wx.BOTTOM | wx.EXPAND, 10)

        audio_heading = wx.StaticText(
            general, label="Przetwarzanie dźwięku"
        )
        audio_heading.SetName("Przetwarzanie dźwięku")
        general_layout.Add(audio_heading, 0, wx.TOP | wx.BOTTOM | wx.EXPAND, 8)

        self.loudness = wx.CheckBox(
            general, label="&Normalizuj odczuwaną głośność utworów"
        )
        self.loudness.SetName("Normalizuj odczuwaną głośność utworów")
        self.loudness.SetValue(options.loudness_normalization)
        self.smooth = wx.CheckBox(
            general, label="&Łagodnie przechodź między utworami"
        )
        self.smooth.SetName("Łagodnie przechodź między utworami")
        self.smooth.SetValue(options.smooth_track_transitions)
        general_layout.Add(self.loudness, 0, wx.BOTTOM | wx.EXPAND, 10)
        general_layout.Add(self.smooth, 0, wx.BOTTOM | wx.EXPAND, 10)

        silence_label = wx.StaticText(
            general, label="Dodatkowa &cisza po naturalnym końcu utworu:"
        )
        self._silence_values = list(session_options.INTER_TRACK_SILENCE_CHOICES)
        self.silence = wx.Choice(
            general,
            choices=[
                session_options.inter_track_silence_label(value)
                for value in self._silence_values
            ],
        )
        self.silence.SetName("Dodatkowa cisza po naturalnym końcu utworu")
        try:
            silence_index = self._silence_values.index(options.inter_track_silence_ms)
        except ValueError:
            silence_index = 0
        self.silence.SetSelection(silence_index)
        general_layout.Add(silence_label, 0, wx.BOTTOM, 4)
        general_layout.Add(self.silence, 0, wx.BOTTOM | wx.EXPAND, 10)

        tempo_label = wx.StaticText(
            general, label="Sposób przeliczania zmienionego &tempa:"
        )
        self._tempo_values = [0, 1, 2]
        self.tempo = wx.Choice(
            general,
            choices=[TEMPO_LABELS[value] for value in self._tempo_values],
        )
        self.tempo.SetName("Sposób przeliczania zmienionego tempa")
        self.tempo.SetSelection(
            self._tempo_values.index(options.tempo_algorithm)
            if options.tempo_algorithm in self._tempo_values
            else 1
        )
        general_layout.Add(tempo_label, 0, wx.BOTTOM, 4)
        general_layout.Add(self.tempo, 0, wx.BOTTOM | wx.EXPAND, 10)
        general.SetSizer(general_layout)

        radio = wx.ScrolledWindow(self.notebook)
        radio.SetScrollRate(0, 12)
        radio_layout = wx.BoxSizer(wx.VERTICAL)

        timeshift_label = wx.StaticText(
            radio, label="&Długość bufora transmisji:"
        )
        self._timeshift_values = list(RADIO_TIMESHIFT_CHOICES)
        if options.timeshift_minutes not in self._timeshift_values:
            self._timeshift_values.append(options.timeshift_minutes)
            self._timeshift_values.sort()
        self.timeshift = wx.Choice(
            radio,
            choices=[
                radio_timeshift_label(value)
                for value in self._timeshift_values
            ],
        )
        self.timeshift.SetName("Długość bufora transmisji")
        self.timeshift.SetSelection(
            self._timeshift_values.index(options.timeshift_minutes)
        )
        radio_layout.Add(timeshift_label, 0, wx.BOTTOM, 4)
        radio_layout.Add(self.timeshift, 0, wx.BOTTOM | wx.EXPAND, 10)

        self.recognition_monitoring = wx.CheckBox(
            radio, label="&Obserwuj i automatycznie rozpoznawaj utwory"
        )
        self.recognition_monitoring.SetName(
            "Obserwuj i automatycznie rozpoznawaj utwory"
        )
        self.recognition_monitoring.SetValue(
            options.radio_recognition_monitoring
        )
        recognition_scope_label = wx.StaticText(
            radio, label="&Zakres automatycznego rozpoznawania:"
        )
        self._recognition_scope_values = list(radio_recognition.SCOPES)
        self.recognition_scope = wx.Choice(
            radio,
            choices=[
                radio_recognition.scope_label(value)
                for value in self._recognition_scope_values
            ],
        )
        self.recognition_scope.SetName(
            "Zakres automatycznego rozpoznawania utworów"
        )
        self.recognition_scope.SetSelection(
            self._recognition_scope_values.index(
                radio_recognition.normalize_scope(
                    options.radio_recognition_scope
                )
            )
        )
        radio_layout.Add(
            self.recognition_monitoring, 0, wx.BOTTOM | wx.EXPAND, 10
        )
        radio_layout.Add(recognition_scope_label, 0, wx.BOTTOM, 4)
        radio_layout.Add(
            self.recognition_scope, 0, wx.BOTTOM | wx.EXPAND, 10
        )

        folder_mode_label = wx.StaticText(
            radio, label="&Położenie nagrań Radia:"
        )
        self._recording_folder_mode_values = ["radio", "podcasts"]
        self.recording_folder_mode = wx.Choice(
            radio,
            choices=[
                "Osobny folder nagrywania Radia",
                "Ten sam folder co pobieranie Podcastów",
            ],
        )
        self.recording_folder_mode.SetName("Położenie nagrań Radia")
        use_podcast_folder = options.radio_use_podcast_downloads_folder
        if use_podcast_folder is None:
            use_podcast_folder = recording.folder_preset == "podcasts"
        self.recording_folder_mode.SetSelection(1 if use_podcast_folder else 0)
        self.recording_folder_mode.Bind(
            wx.EVT_CHOICE, self._on_recording_folder_mode
        )
        radio_layout.Add(folder_mode_label, 0, wx.BOTTOM, 4)
        radio_layout.Add(
            self.recording_folder_mode, 0, wx.BOTTOM | wx.EXPAND, 10
        )

        folder_label = wx.StaticText(
            radio, label="Osobny &folder nagrywania radia:"
        )
        configured_folder = options.radio_recordings_folder
        if configured_folder is None:
            configured_folder = recording.radio_default_folder
        if configured_folder is None and recording.folder_preset == "radio":
            configured_folder = recording.default_folder
        configured_folder = configured_folder or ""
        self._recording_folder_value = str(configured_folder).strip()
        self.recording_folder = wx.TextCtrl(
            radio,
            value=(
                self._recording_folder_value
                or "Domyślny folder nagrywania AMC"
            ),
            style=wx.TE_READONLY,
        )
        self.recording_folder.SetName("Domyślny folder nagrywania radia")
        folder_buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.browse_recording_folder = wx.Button(radio, label="&Wybierz…")
        self.browse_recording_folder.SetName(
            "Wybierz domyślny folder nagrywania radia"
        )
        self.default_recording_folder = wx.Button(
            radio, label="Użyj folderu &domyślnego AMC"
        )
        self.default_recording_folder.SetName(
            "Użyj domyślnego folderu nagrywania AMC"
        )
        self.browse_recording_folder.Bind(
            wx.EVT_BUTTON, self._on_browse_recording_folder
        )
        self.default_recording_folder.Bind(
            wx.EVT_BUTTON, self._on_default_recording_folder
        )
        folder_buttons.Add(self.browse_recording_folder, 0, wx.RIGHT, 8)
        folder_buttons.Add(self.default_recording_folder, 0)
        radio_layout.Add(folder_label, 0, wx.BOTTOM, 4)
        radio_layout.Add(self.recording_folder, 0, wx.BOTTOM | wx.EXPAND, 8)
        radio_layout.Add(folder_buttons, 0, wx.BOTTOM | wx.EXPAND, 12)

        format_label = wx.StaticText(radio, label="&Format pliku:")
        self._recording_format_values = [
            value for _label, value in RADIO_FORMAT_CHOICES
        ]
        self.recording_format = wx.Choice(
            radio, choices=[label for label, _value in RADIO_FORMAT_CHOICES]
        )
        self.recording_format.SetName("Format nagrania radia")
        self.recording_format.SetSelection(
            self._recording_format_values.index(recording.format)
            if recording.format in self._recording_format_values
            else 0
        )
        bitrate_label = wx.StaticText(
            radio, label="&Bitrate nagrania MP3 lub AAC:"
        )
        self.recording_bitrate = wx.Choice(
            radio,
            choices=[f"{value} kilobitów na sekundę" for value in RADIO_BITRATE_CHOICES],
        )
        self.recording_bitrate.SetName("Bitrate nagrania MP3 lub AAC")
        self.recording_bitrate.SetSelection(
            min(
                range(len(RADIO_BITRATE_CHOICES)),
                key=lambda index: abs(
                    RADIO_BITRATE_CHOICES[index] - recording.bitrate_kbps
                ),
            )
        )
        self.recording_format.Bind(wx.EVT_CHOICE, self._on_recording_format)
        radio_layout.Add(format_label, 0, wx.BOTTOM, 4)
        radio_layout.Add(self.recording_format, 0, wx.BOTTOM | wx.EXPAND, 10)
        radio_layout.Add(bitrate_label, 0, wx.BOTTOM, 4)
        radio_layout.Add(self.recording_bitrate, 0, wx.BOTTOM | wx.EXPAND, 10)

        self.prefer_station_folder = wx.CheckBox(
            radio,
            label=(
                "W nowym harmonogramie podpowiadaj &folder stacji, "
                "gdy stacja go ma"
            ),
        )
        self.prefer_station_folder.SetName(
            "W nowym harmonogramie podpowiadaj folder stacji, gdy stacja go ma"
        )
        self.prefer_station_folder.SetValue(
            recording.prefer_station_folder_in_new_schedules
        )
        self.wake_scheduled_recordings = wx.CheckBox(
            radio,
            label=(
                "Domyślnie &wybudzaj komputer przed zaplanowanym nagraniem"
            ),
        )
        self.wake_scheduled_recordings.SetName(
            "Domyślnie wybudzaj komputer przed zaplanowanym nagraniem"
        )
        self.wake_scheduled_recordings.SetValue(wake_scheduled_recordings)
        radio_layout.Add(
            self.prefer_station_folder, 0, wx.BOTTOM | wx.EXPAND, 10
        )
        radio_layout.Add(
            self.wake_scheduled_recordings, 0, wx.BOTTOM | wx.EXPAND, 10
        )
        radio.SetSizer(radio_layout)
        self._update_recording_bitrate_state()
        self._update_recording_folder_state()

        podcasts = wx.ScrolledWindow(self.notebook)
        podcasts.SetScrollRate(0, 12)
        podcasts_layout = wx.BoxSizer(wx.VERTICAL)

        podcast_folder_label = wx.StaticText(
            podcasts, label="Domyślny &folder pobierania podcastów:"
        )
        configured_podcast_folder = options.podcast_downloads_folder
        if configured_podcast_folder is None:
            configured_podcast_folder = podcast_settings.downloads_folder
        self._podcast_folder_value = str(configured_podcast_folder).strip()
        self.podcast_folder = wx.TextCtrl(
            podcasts,
            value=(
                self._podcast_folder_value
                or "Domyślny folder pobierania AMC"
            ),
            style=wx.TE_READONLY,
        )
        self.podcast_folder.SetName(
            "Domyślny folder pobierania podcastów"
        )
        podcast_folder_buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.browse_podcast_folder = wx.Button(podcasts, label="&Wybierz…")
        self.browse_podcast_folder.SetName(
            "Wybierz domyślny folder pobierania podcastów"
        )
        self.default_podcast_folder = wx.Button(
            podcasts, label="Użyj folderu &domyślnego AMC"
        )
        self.default_podcast_folder.SetName(
            "Użyj domyślnego folderu pobierania AMC"
        )
        self.browse_podcast_folder.Bind(
            wx.EVT_BUTTON, self._on_browse_podcast_folder
        )
        self.default_podcast_folder.Bind(
            wx.EVT_BUTTON, self._on_default_podcast_folder
        )
        podcast_folder_buttons.Add(self.browse_podcast_folder, 0, wx.RIGHT, 8)
        podcast_folder_buttons.Add(self.default_podcast_folder, 0)
        podcasts_layout.Add(podcast_folder_label, 0, wx.BOTTOM, 4)
        podcasts_layout.Add(self.podcast_folder, 0, wx.BOTTOM | wx.EXPAND, 8)
        podcasts_layout.Add(
            podcast_folder_buttons, 0, wx.BOTTOM | wx.EXPAND, 12
        )

        rss_label = wx.StaticText(
            podcasts, label="Odstęp dla &podcastów w minutach:"
        )
        self.podcast_rss_interval = wx.SpinCtrl(
            podcasts, min=0, max=10_080,
            initial=(
                options.podcast_rss_refresh_interval_minutes
                if options.podcast_rss_refresh_interval_minutes is not None
                else podcast_settings.rss_refresh_interval_minutes
            ),
        )
        self.podcast_rss_interval.SetName(
            "Odstęp automatycznego sprawdzania podcastów w minutach; zero wyłącza"
        )
        youtube_label = wx.StaticText(
            podcasts, label="Odstęp dla kanałów &YouTube w minutach:"
        )
        self.podcast_youtube_interval = wx.SpinCtrl(
            podcasts, min=0, max=10_080,
            initial=(
                options.podcast_youtube_refresh_interval_minutes
                if options.podcast_youtube_refresh_interval_minutes is not None
                else podcast_settings.youtube_refresh_interval_minutes
            ),
        )
        self.podcast_youtube_interval.SetName(
            "Odstęp automatycznego sprawdzania kanałów YouTube w minutach; zero wyłącza"
        )
        batch_label = wx.StaticText(
            podcasts, label="Liczba źródeł sprawdzanych &jednocześnie:"
        )
        self.podcast_refresh_batch = wx.SpinCtrl(
            podcasts, min=1, max=50,
            initial=(
                options.podcast_automatic_refresh_batch_size
                if options.podcast_automatic_refresh_batch_size is not None
                else podcast_settings.automatic_refresh_batch_size
            ),
        )
        self.podcast_refresh_batch.SetName(
            "Liczba źródeł sprawdzanych w jednym przebiegu"
        )
        for label, control in (
            (rss_label, self.podcast_rss_interval),
            (youtube_label, self.podcast_youtube_interval),
            (batch_label, self.podcast_refresh_batch),
        ):
            podcasts_layout.Add(label, 0, wx.BOTTOM, 4)
            podcasts_layout.Add(control, 0, wx.BOTTOM | wx.EXPAND, 10)
        podcasts.SetSizer(podcasts_layout)

        messages = wx.ScrolledWindow(self.notebook)
        messages.SetScrollRate(0, 12)
        messages_layout = wx.BoxSizer(wx.VERTICAL)

        self.message_enabled = wx.CheckBox(
            messages, label="&Włącz komunikaty dostępności"
        )
        self.message_enabled.SetName("Włącz komunikaty dostępności")
        self.message_enabled.SetHelpText(
            "Wyłączenie zatrzymuje rutynową mowę AMC, ale nadal pozostawia "
            "tekst w pasku stanu i nie ukrywa komunikatów o błędach."
        )
        self.message_enabled.SetValue(message_policy.enabled)
        messages_layout.Add(
            self.message_enabled, 0, wx.BOTTOM | wx.EXPAND, 10
        )

        self.message_seek_messages = wx.CheckBox(
            messages, label="Włącz automatyczne komunikaty &odtwarzacza"
        )
        self.message_seek_messages.SetName(
            "Włącz automatyczne komunikaty odtwarzacza"
        )
        self.message_seek_messages.SetValue(message_policy.seek_messages)

        self.message_arrow_seek_messages = wx.CheckBox(
            messages,
            label="Oznajmiaj przewijanie &strzałkami oraz klawiszami Home i End",
        )
        self.message_arrow_seek_messages.SetName(
            "Oznajmiaj przewijanie strzałkami oraz klawiszami Home i End"
        )
        self.message_arrow_seek_messages.SetValue(
            message_policy.arrow_seek_messages
        )

        self.message_percentage_seek_messages = wx.CheckBox(
            messages, label="Oznajmiaj skoki klawiszami &cyfr"
        )
        self.message_percentage_seek_messages.SetName(
            "Oznajmiaj skoki klawiszami cyfr"
        )
        self.message_percentage_seek_messages.SetValue(
            message_policy.percentage_seek_messages
        )

        percentage_label = wx.StaticText(
            messages, label="Przy skoku cyfrą &podawaj:"
        )
        self._message_percent_values = [
            PercentAnnouncement.PERCENT,
            PercentAnnouncement.TIME,
            PercentAnnouncement.PERCENT_AND_TIME,
        ]
        self.message_percent_announcement = wx.Choice(
            messages,
            choices=["Tylko procent", "Tylko czas", "Procent i czas"],
        )
        self.message_percent_announcement.SetName(
            "Treść komunikatu po skoku klawiszem cyfry"
        )
        self.message_percent_announcement.SetSelection(
            self._message_percent_values.index(
                message_policy.percent_announcement
            )
        )

        self.message_volume_messages = wx.CheckBox(
            messages, label="Oznajmiaj zmiany &głośności"
        )
        self.message_volume_messages.SetName("Oznajmiaj zmiany głośności")
        self.message_volume_messages.SetValue(message_policy.volume_messages)

        self.message_playback_messages = wx.CheckBox(
            messages, label="Oznajmiaj odtwarzanie i pau&zę"
        )
        self.message_playback_messages.SetName(
            "Oznajmiaj odtwarzanie i pauzę"
        )
        self.message_playback_messages.SetValue(
            message_policy.playback_messages
        )

        self.message_bookmark_navigation_messages = wx.CheckBox(
            messages, label="Oznajmiaj nawigację po &zakładkach"
        )
        self.message_bookmark_navigation_messages.SetName(
            "Oznajmiaj nawigację po zakładkach"
        )
        self.message_bookmark_navigation_messages.SetValue(
            message_policy.bookmark_navigation_messages
        )

        for control in (
            self.message_seek_messages,
            self.message_arrow_seek_messages,
            self.message_percentage_seek_messages,
        ):
            messages_layout.Add(control, 0, wx.BOTTOM | wx.EXPAND, 10)
        messages_layout.Add(percentage_label, 0, wx.BOTTOM, 4)
        messages_layout.Add(
            self.message_percent_announcement,
            0,
            wx.BOTTOM | wx.EXPAND,
            10,
        )
        for control in (
            self.message_volume_messages,
            self.message_playback_messages,
            self.message_bookmark_navigation_messages,
        ):
            messages_layout.Add(control, 0, wx.BOTTOM | wx.EXPAND, 10)

        self.detailed_hints = wx.CheckBox(
            messages,
            label=(
                "Pokazuj &szczegółowe podpowiedzi klawiatury przy polach "
                "i listach"
            ),
        )
        self.detailed_hints.SetName(
            "Pokazuj szczegółowe podpowiedzi klawiatury przy polach i listach"
        )
        self.detailed_hints.SetValue(detailed_hints)
        messages_layout.Add(
            self.detailed_hints, 0, wx.TOP | wx.BOTTOM | wx.EXPAND, 10
        )

        templates_explanation = wx.StaticText(
            messages,
            label=(
                "Wybierz zdarzenie, a następnie zmień jego tekst. "
                "Pusty tekst wyłącza dany komunikat."
            ),
        )
        templates_explanation.SetName(
            "Szablony komunikatów dostępności"
        )
        templates_label = wx.StaticText(messages, label="&Zdarzenie:")
        self._message_template_keys = list(TEMPLATE_KEYS)
        self._message_template_values = {
            key: (
                message_policy.templates[key]
                if key in message_policy.templates
                else DEFAULT_TEMPLATES[key]
            )
            for key in self._message_template_keys
        }
        self.message_templates = wx.ListBox(
            messages,
            choices=[TEMPLATE_LABELS[key] for key in self._message_template_keys],
            style=wx.LB_SINGLE,
        )
        self.message_templates.SetName("Zdarzenia komunikatów")
        self.message_templates.SetSelection(0)
        self._message_template_index = 0
        template_text_label = wx.StaticText(
            messages, label="&Tekst wybranego komunikatu:"
        )
        self.message_template_text = wx.TextCtrl(
            messages,
            value=self._message_template_values[self._message_template_keys[0]],
            style=wx.TE_MULTILINE,
            size=(-1, 64),
        )
        self.message_template_text.SetName(
            "Tekst szablonu wybranego komunikatu"
        )
        self.message_templates.Bind(
            wx.EVT_LISTBOX, self._on_message_template_choice
        )
        messages_layout.Add(
            templates_explanation, 0, wx.TOP | wx.BOTTOM | wx.EXPAND, 8
        )
        messages_layout.Add(templates_label, 0, wx.BOTTOM, 4)
        messages_layout.Add(
            self.message_templates, 0, wx.BOTTOM | wx.EXPAND, 8
        )
        messages_layout.Add(template_text_label, 0, wx.BOTTOM, 4)
        messages_layout.Add(
            self.message_template_text, 0, wx.BOTTOM | wx.EXPAND, 12
        )

        activity_heading = wx.StaticText(
            messages, label="Komunikaty stanu stacji radiowej"
        )
        activity_heading.SetName("Komunikaty stanu stacji radiowej")
        messages_layout.Add(activity_heading, 0, wx.TOP | wx.BOTTOM | wx.EXPAND, 8)

        playback_label = wx.StaticText(
            messages, label="Stan &odtwarzania przy nazwie stacji:"
        )
        self.playback_position = wx.Choice(
            messages, choices=list(STATE_POSITION_LABELS)
        )
        self.playback_position.SetName("Stan odtwarzania przy nazwie stacji")
        self.playback_position.SetSelection(
            state_position_index(options.radio_playback_state_position)
        )
        messages_layout.Add(playback_label, 0, wx.BOTTOM, 4)
        messages_layout.Add(self.playback_position, 0, wx.BOTTOM | wx.EXPAND, 10)

        recording_label = wx.StaticText(
            messages, label="Stan &nagrywania przy nazwie stacji:"
        )
        self.recording_position = wx.Choice(
            messages, choices=list(STATE_POSITION_LABELS)
        )
        self.recording_position.SetName("Stan nagrywania przy nazwie stacji")
        self.recording_position.SetSelection(
            state_position_index(options.radio_recording_state_position)
        )
        messages_layout.Add(recording_label, 0, wx.BOTTOM, 4)
        messages_layout.Add(self.recording_position, 0, wx.BOTTOM | wx.EXPAND, 10)

        self.playback_sound = wx.CheckBox(
            messages, label="Krótki &dźwięk dla odtwarzanej stacji"
        )
        self.playback_sound.SetName("Krótki dźwięk dla odtwarzanej stacji")
        self.playback_sound.SetValue(options.radio_playback_state_sound)
        self.recording_sound = wx.CheckBox(
            messages, label="Krótki dźwięk dla nagrywanej stacji"
        )
        self.recording_sound.SetName("Krótki dźwięk dla nagrywanej stacji")
        self.recording_sound.SetValue(options.radio_recording_state_sound)
        messages_layout.Add(self.playback_sound, 0, wx.BOTTOM | wx.EXPAND, 10)
        messages_layout.Add(self.recording_sound, 0, wx.BOTTOM | wx.EXPAND, 10)
        self.recognition_announcements = wx.CheckBox(
            messages, label="&Oznajmiaj automatycznie rozpoznane utwory"
        )
        self.recognition_announcements.SetName(
            "Oznajmiaj automatycznie rozpoznane utwory"
        )
        self.recognition_announcements.SetValue(
            options.radio_recognition_announcements
        )
        messages_layout.Add(
            self.recognition_announcements, 0, wx.BOTTOM | wx.EXPAND, 10
        )
        messages.SetSizer(messages_layout)

        self.notebook.AddPage(general, "Ogólne", select=True)
        self.notebook.AddPage(radio, "Radio i nagrywanie")
        self.notebook.AddPage(podcasts, "Podcasty i YouTube")
        self.notebook.AddPage(messages, "Komunikaty")

        buttons = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        save = self.FindWindowById(wx.ID_OK)
        if save is not None:
            save.SetLabel("&Zapisz")
            save.SetName("Zapisz ustawienia")
            save.SetDefault()
        self.Bind(wx.EVT_BUTTON, self._on_save, id=wx.ID_OK)
        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(self.notebook, 1, wx.ALL | wx.EXPAND, 12)
        outer.Add(buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 12)
        self.SetSizer(outer)
        self.SetMinSize((560, 450))
        self.CentreOnParent()
        self.pause.SetFocus()

    def _on_browse_recording_folder(self, _event: wx.CommandEvent) -> None:
        dialog = wx.DirDialog(
            self,
            message="Wybierz domyślny folder nagrywania radia",
            defaultPath=self._recording_folder_value,
        )
        try:
            if dialog.ShowModal() != wx.ID_OK:
                return
            self._recording_folder_value = dialog.GetPath().strip()
            self.recording_folder.SetValue(self._recording_folder_value)
        finally:
            dialog.Destroy()
        self.recording_folder.SetFocus()

    def _refresh_session_order_list(self, selected: int) -> None:
        self.session_order_list.Set(
            list(session_order.selection_labels(self._session_order))
        )
        if self._session_order:
            self.session_order_list.SetSelection(
                max(0, min(selected, len(self._session_order) - 1))
            )
        self.session_order_list.SetFocus()

    def _move_session_order(self, direction: int) -> None:
        index = self.session_order_list.GetSelection()
        target = index + (-1 if direction < 0 else 1)
        if index < 0 or target < 0 or target >= len(self._session_order):
            self.session_order_list.SetFocus()
            return
        self._session_order[index], self._session_order[target] = (
            self._session_order[target],
            self._session_order[index],
        )
        self._refresh_session_order_list(target)

    def _restore_default_session_order(self, _event: wx.CommandEvent) -> None:
        self._session_order = list(session_order.DEFAULT_SESSION_ORDER)
        self._refresh_session_order_list(0)

    def _on_session_order_key(self, event: wx.KeyEvent) -> None:
        if event.AltDown() and not event.ControlDown() and not event.ShiftDown():
            code = event.GetKeyCode()
            if code == wx.WXK_UP:
                self._move_session_order(-1)
                return
            if code == wx.WXK_DOWN:
                self._move_session_order(1)
                return
        event.Skip()

    def _on_save(self, event: wx.CommandEvent) -> None:
        parsed = parse_custom_seek_length(self.custom_seek.GetValue())
        if parsed is None:
            wx.MessageBox(
                "Długość przeskoku musi być podana w minutach albo sekundach, "
                "na przykład: 5 minut, 90 sekund lub 1:30. "
                "Dopuszczalny zakres to od 5 sekund do 30 minut.",
                "Nie zapisano ustawień",
                wx.OK | wx.ICON_WARNING,
                parent=self,
            )
            self.custom_seek.SetFocus()
            self.custom_seek.SetSelection(-1, -1)
            return
        self._custom_seek_seconds = parsed
        event.Skip()

    def _on_default_recording_folder(self, _event: wx.CommandEvent) -> None:
        self._recording_folder_value = ""
        self.recording_folder.SetValue("Domyślny folder nagrywania AMC")
        self.recording_folder.SetFocus()

    def _on_recording_folder_mode(self, _event: wx.CommandEvent) -> None:
        self._update_recording_folder_state()

    def _update_recording_folder_state(self) -> None:
        own_folder = self.recording_folder_mode.GetSelection() == 0
        self.recording_folder.Enable(own_folder)
        self.browse_recording_folder.Enable(own_folder)
        self.default_recording_folder.Enable(own_folder)

    def _on_recording_format(self, _event: wx.CommandEvent) -> None:
        self._update_recording_bitrate_state()

    def _update_recording_bitrate_state(self) -> None:
        index = max(0, self.recording_format.GetSelection())
        selected = self._recording_format_values[index]
        self.recording_bitrate.Enable(selected in ("Mp3", "Aac"))

    def _on_browse_podcast_folder(self, _event: wx.CommandEvent) -> None:
        dialog = wx.DirDialog(
            self,
            message="Wybierz domyślny folder pobierania podcastów",
            defaultPath=self._podcast_folder_value,
        )
        try:
            if dialog.ShowModal() != wx.ID_OK:
                return
            self._podcast_folder_value = dialog.GetPath().strip()
            self.podcast_folder.SetValue(self._podcast_folder_value)
        finally:
            dialog.Destroy()
        self.podcast_folder.SetFocus()

    def _on_default_podcast_folder(self, _event: wx.CommandEvent) -> None:
        self._podcast_folder_value = ""
        self.podcast_folder.SetValue("Domyślny folder pobierania AMC")
        self.podcast_folder.SetFocus()

    def _store_message_template_text(self) -> None:
        index = self._message_template_index
        if 0 <= index < len(self._message_template_keys):
            self._message_template_values[
                self._message_template_keys[index]
            ] = self.message_template_text.GetValue()

    def _on_message_template_choice(self, event: wx.CommandEvent) -> None:
        self._store_message_template_text()
        selected = self.message_templates.GetSelection()
        if 0 <= selected < len(self._message_template_keys):
            self._message_template_index = selected
            self.message_template_text.ChangeValue(
                self._message_template_values[
                    self._message_template_keys[selected]
                ]
            )
        event.Skip()

    @property
    def values(self) -> dict[str, object]:
        self._store_message_template_text()
        return {
            "startup_target": self._startup_target_values[
                max(0, self.startup_target.GetSelection())
            ],
            "pause_on_player_exit": self.pause.GetValue(),
            "session_order": [session.value for session in self._session_order],
            "follow_playback_on_player_exit": self.follow.GetValue(),
            "open_player_when_activating_preset": self.open_preset.GetValue(),
            "stay_on_list_after_radio_enter": self.radio_enter.GetValue(),
            "pause_on_audio_output_fallback": (
                self.pause_output_fallback.GetValue()
            ),
            "keep_audio_edit_backups": self.keep_audio_edit_backups.GetValue(),
            "custom_seek_seconds": self._custom_seek_seconds,
            "global_transient_previews": self.global_transient_previews.GetValue(),
            "remember_local_playback_positions": (
                self.remember_local_playback_positions.GetValue()
            ),
            "detailed_hints": self.detailed_hints.GetValue(),
            "message_enabled": self.message_enabled.GetValue(),
            "message_seek_messages": self.message_seek_messages.GetValue(),
            "message_arrow_seek_messages": (
                self.message_arrow_seek_messages.GetValue()
            ),
            "message_percentage_seek_messages": (
                self.message_percentage_seek_messages.GetValue()
            ),
            "message_volume_messages": self.message_volume_messages.GetValue(),
            "message_playback_messages": (
                self.message_playback_messages.GetValue()
            ),
            "message_bookmark_navigation_messages": (
                self.message_bookmark_navigation_messages.GetValue()
            ),
            "message_percent_announcement": self._message_percent_values[
                max(0, self.message_percent_announcement.GetSelection())
            ].value,
            "message_templates": dict(self._message_template_values),
            "loudness_normalization": self.loudness.GetValue(),
            "smooth_track_transitions": self.smooth.GetValue(),
            "inter_track_silence_ms": self._silence_values[
                max(0, self.silence.GetSelection())
            ],
            "tempo_algorithm": self._tempo_values[
                max(0, self.tempo.GetSelection())
            ],
            "radio_playback_state_position": state_position_value(
                self.playback_position.GetSelection()
            ),
            "radio_recording_state_position": state_position_value(
                self.recording_position.GetSelection()
            ),
            "radio_playback_state_sound": self.playback_sound.GetValue(),
            "radio_recording_state_sound": self.recording_sound.GetValue(),
            "radio_recognition_monitoring": (
                self.recognition_monitoring.GetValue()
            ),
            "radio_recognition_scope": self._recognition_scope_values[
                max(0, self.recognition_scope.GetSelection())
            ],
            "radio_recognition_announcements": (
                self.recognition_announcements.GetValue()
            ),
            "timeshift_minutes": self._timeshift_values[
                max(0, self.timeshift.GetSelection())
            ],
            "radio_recordings_folder": self._recording_folder_value,
            "radio_use_podcast_downloads_folder": (
                self.recording_folder_mode.GetSelection() == 1
            ),
            "radio_recording_format": self._recording_format_values[
                max(0, self.recording_format.GetSelection())
            ],
            "radio_recording_bitrate_kbps": RADIO_BITRATE_CHOICES[
                max(0, self.recording_bitrate.GetSelection())
            ],
            "radio_prefer_station_folder_in_new_schedules": (
                self.prefer_station_folder.GetValue()
            ),
            "radio_schedule_wake_override": (
                self.wake_scheduled_recordings.GetValue()
            ),
            "podcast_downloads_folder": self._podcast_folder_value,
            "podcast_rss_refresh_interval_minutes": (
                self.podcast_rss_interval.GetValue()
            ),
            "podcast_youtube_refresh_interval_minutes": (
                self.podcast_youtube_interval.GetValue()
            ),
            "podcast_automatic_refresh_batch_size": (
                self.podcast_refresh_batch.GetValue()
            ),
        }


class LiteFrame(wx.Frame):
    """Okno glowne: panel listy i panel odtwarzacza, przelaczane jak w AMC."""

    def __init__(self, store: StateStore, state: LiteState) -> None:
        super().__init__(None, title=window_title(), size=(900, 600))

        self.store = store
        self.state = state
        self.options = state.options
        # Stacje: w trybie wspolnego profilu zrodlem jest state.json AMC
        # (radio.stations), a nie prywatna kopia -- inaczej Radio bylo puste.
        # Uklad rozstrzygamy RAZ: ten sam obiekt decyduje tez o tym, czy host
        # dostanie zgode na zapis kolejki (patrz _queue_persistence_arguments).
        self.layout = resolve_layout()
        self._profile_audio_outputs = read_profile_outputs(self.layout.state_json)
        # Punkt startowy komunikatow i czas wlasny z PRAWDZIWEGO profilu AMC.
        # Profil C# pozostaje tylko do odczytu; prywatne nadpisania sa
        # nakladane nizej i zapisywane w magazynie AMC Python.
        self.messages: MessagePolicy = load_message_policy(self.layout)
        apply_message_overrides(
            self.messages,
            enabled=self.options.message_enabled,
            seek_messages=self.options.message_seek_messages,
            arrow_seek_messages=self.options.message_arrow_seek_messages,
            percentage_seek_messages=(
                self.options.message_percentage_seek_messages
            ),
            volume_messages=self.options.message_volume_messages,
            playback_messages=self.options.message_playback_messages,
            bookmark_navigation_messages=(
                self.options.message_bookmark_navigation_messages
            ),
            percent_announcement=self.options.message_percent_announcement,
            templates=self.options.message_templates,
        )
        self.messages.custom_seek_seconds = resolve_custom_seek_seconds(
            self.options.custom_seek_seconds,
            self.messages.custom_seek_seconds,
        )
        self._detailed_hints = resolve_detailed_hints(
            self.options.detailed_hints,
            self.messages.detailed_hints,
        )
        self._global_transient_previews = resolve_global_transient_previews(
            self.options.global_transient_previews,
            load_global_transient_previews(self.layout.state_json),
        )
        self._remember_local_playback_positions = (
            resolve_remember_local_playback_positions(
                self.options.remember_local_playback_positions,
                load_remember_local_playback_positions(self.layout.state_json),
            )
        )
        self.radio = RadioSource(self.layout)
        self._radio_snapshot = LiteFrame._with_radio_recording_options(
            self, self.radio.load()
        )
        # Jednorazowa, bezpieczna kontynuacja historii z głównego AMC. Profil
        # źródłowy pozostaje tylko do odczytu; dalsze wyniki zapisuje prywatny
        # stan wxPython. Po Id nie dublujemy wpisów już przejętych wcześniej.
        if not self.state.recognized_tracks_imported_from_amc:
            known_recognition_ids = {
                str(entry.get("id") or "")
                for entry in self.state.recognized_tracks
            }
            self.state.recognized_tracks = radio_recognition.read_tracks([
                *self.state.recognized_tracks,
                *(
                    entry for entry in self._radio_snapshot.recognized_tracks
                    if str(entry.get("id") or "") not in known_recognition_ids
                ),
            ])
            self.state.recognized_tracks_imported_from_amc = True
        self.stations = self._radio_snapshot.list
        self.navigator = Navigator()
        self._transient_preview_return: TransientNavigationSnapshot | None = None
        # Biblioteka AMC (SQLite, tylko odczyt). Wlascicielem zapisu profilu
        # Wykonawca nagran i zegara pozostaje w hoscie C#. Interfejs wxPython
        # moze teraz edytowac prywatna kopie planow, ale sam nie uruchamia
        # drugiego, konkurencyjnego zegara.
        self.library = LibrarySource()
        self.podcasts = PodcastSource(self.layout)
        self.tidal = TidalSource(self.layout)
        self.search_sources = SearchSources(
            self.library, self.radio, self.podcasts, self.tidal
        )
        self._tidal_queue_rows = list(tidal_queue_rows(state.tidal_queue_items))
        self._tidal_effective_sort_modes = {
            scope: state.tidal_sort_modes.get(scope, SORT_ADDED_NEWEST)
            for scope in (
                TIDAL_VIEW_LIBRARY,
                TIDAL_VIEW_FAVORITES,
                TIDAL_VIEW_PLAYLISTS,
            )
        }
        self._spotify_effective_sort_modes = {
            scope: state.spotify_sort_modes.get(scope, SORT_ADDED_NEWEST)
            for scope in (
                "liked", "albums", "artists", "playlists", "podcasts", "episodes",
            )
        }
        # Kazde otwarcie katalogu ma numer. Odpowiedz rozpoczęta przed
        # opuszczeniem sesji nie moze po powrocie podmienic nowszej listy.
        self._tidal_navigation_version = 0
        self._spotify_navigation_version = 0
        self._podcast_loaded_counts: dict[str, int] = {}
        self._spotify_loaded_counts: dict[str, int] = {}
        # ``None`` w stanie prywatnym dziedziczy wybor glownego AMC. Do czasu
        # pierwszego odczytu widoku trzymamy bezpieczny domysl; wynik strony
        # niesie potem faktycznie uzyty tryb i aktualizuje zaznaczenie menu.
        self._podcast_inbox_sort_mode = (
            state.podcast_inbox_sort_mode or SORT_ADDED_NEWEST
        )
        self.navigator.restore(state.navigation)

        # Brama zna zycie okna, wiec spozniony wynik nie dotknie zniszczonego
        # okna. Nazwy strumieni ("folder", "status"...) uniewazniaja poprzednie
        # zadania tego samego rodzaju.
        self.gate = StaleResultGate(alive=self._window_alive)
        self.runner = BackgroundRunner(self.gate, to_gui=wx.CallAfter)

        self.client: LiteHostClient | None = None
        self._last_status: dict = {}
        self._transport_status_by_session: dict[SessionId, dict] = {}
        self._radio_transport_status_poll_pending = False
        self._last_recording_status: dict = {}
        self._status_poll_pending = False
        self._recording_status_poll_pending = False
        self._podcast_checkpoint_pending = False
        self._podcast_checkpoint_due = 0.0
        self._podcast_checkpoint_active = False
        self._local_checkpoint_pending = False
        self._local_checkpoint_due = 0.0
        self._local_checkpoint_active = False
        self._last_local_resume_error: str | None = None
        self._podcast_refresh_pending = False
        self._podcast_automatic_refresh_pending = False
        self._podcast_automatic_refresh_due = time.monotonic() + 60.0
        self._last_automatic_podcast_error: str | None = None
        self._radio_recognition_pending = False
        self._radio_recognition_due = (
            time.monotonic() + 6.0
            if self.options.radio_recognition_monitoring
            else float("inf")
        )
        self._last_radio_recognition_error: str | None = None
        self._podcast_download_pending = False
        self._podcast_favorite_pending = False
        self._podcast_add_pending = False
        self._radio_search_action_pending = False
        self._podcast_opml_pending = False
        self._playlist_membership_pending = False
        self._last_podcast_progress_error: str | None = None
        self._recording_history_persist_error = False
        self._audio_clip_export_in_progress = False
        self._audio_clip_export_percent = -1
        self._audio_clip_export_operation_id: str | None = None
        self._audio_clip_edit_in_progress = False
        self._audio_clip_edit_percent = -1
        self._audio_clip_edit_operation_id: str | None = None
        self._audio_clip_edit_kind: str | None = None
        self._audio_clip_track_end_intent: AudioClipTrackEndIntent | None = None
        # Enter zatwierdzający modalny dialog Shift+F2 może na Windows trafić
        # jeszcze do odzyskującej fokus listy jako aktywacja wiersza. Wtedy
        # odtwarzacz otwierał plik równolegle z File.Move i zmiana nazwy mogła
        # przegrać wyścig o uchwyt. Bramka pozostaje aktywna do odpowiedzi
        # hosta, a krótki termin osłania także spóźnione natywne zdarzenie.
        self._local_file_rename_pending = False
        self._local_file_rename_activation_guard_until = 0.0
        #: Ostatnia lokalna sesja, która zaczęła grać, zachowana dla zgodności
        #: ze starszymi ścieżkami błędów. Faktyczny stan jest wielosesyjny:
        #: Radio może grać równolegle z Plikami albo Podcastami.
        self._playing_session: SessionId | None = None
        self._playing_sessions: set[SessionId] = set()
        self._pending_playback_session: SessionId | None = None
        self._pending_spotify_playback: PlaySpotifyItem | None = None
        # Oryginalny TIDAL jest osobnym odtwarzaczem. Ta flaga wlacza tylko
        # jego transport; nie udaje stanu lokalnego WindowsMediaOutput.
        self._tidal_desktop_has_playback = False
        # Migawka autonomicznego urządzenia. Nie jest stanem lokalnego
        # WindowsMediaOutput i nie może zostać nadpisana przez jego timer.
        self._wiim_snapshot: dict = {}
        self._wiim_active_device_id = ""
        self._wiim_network_stream_sort_mode = SORT_ADDED_NEWEST
        self._wiim_status_poll_pending = False
        self._sonos_snapshot: dict = {}
        self._sonos_active_household_id = ""
        self._sonos_active_group_id = ""
        self._sonos_browse_household_id = ""
        self._sonos_own_stream_sort_mode = SORT_CUSTOM
        self._sonos_pending_move_ids: list[str] = []
        self._sonos_content_version = 0
        self._sonos_status_poll_pending = False
        # Jeden tor żądań Sonos. Odczyt początkowy, timer i polecenia nie mogą
        # zajmować równocześnie miejsc współbieżnych LiteHosta. Polecenie
        # naciśnięte podczas odczytu czeka tutaj i wykonuje się po nim.
        self._sonos_request_pending = False
        self._sonos_retry_pending = False
        self._sonos_pending_activation: ActivateSonosGroup | None = None
        self._sonos_pending_material: PlaySonosMaterial | None = None
        self._sonos_command_queue: list[
            tuple[str, str, str, int | None, float | None, int]
        ] = []
        # Ostatni świadomie uruchomiony preset osobno dla każdej sesji. Jest
        # stanem bieżącego procesu, nie profilem ani tekstem dla NVDA.
        self._last_preset_slot_by_session: dict[SessionId, int] = {}
        self._radio_activity_cues: dict[tuple[bool, bool], object] = {}

        self._build_ui()
        self._bind_keys()
        self._start_engine()

    # ------------------------------------------------------------------ UI

    def _build_ui(self) -> None:
        self.panel = wx.Panel(self)
        self.session_label = wx.StaticText(self.panel, label="Pliki lokalne")
        font = self.session_label.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.session_label.SetFont(font)

        # --- widok listy
        self.list_panel = wx.Panel(self.panel)
        # POLE FILTRA. JEDNO, wspolne dla kazdej listy -- dokladnie jak
        # ``FilterBox`` w oryginale (MainWindow.xaml:521-524), ktory stoi nad
        # ``MediaList`` i obsluguje wszystkie widoki. Nie ma osobnej kontrolki
        # na sesje ani na widok: filtrowana jest ta lista, ktora jest WIDOCZNA.
        #
        # Etykieta ``wx.StaticText`` z ``&F``: na Windows klawisz dostepu z
        # etykiety przenosi fokus do NASTEPNEJ kontrolki w kolejnosci tabulacji,
        # czyli do pola. Nazwa dostepna pola ustawiona osobno, bo czytnik czyta
        # ``accName`` kontrolki, nie sasiedniego napisu.
        self.filter_label = wx.StaticText(self.list_panel, label="&Filtruj liste:")
        self.filter_box = wx.TextCtrl(self.list_panel)
        self.filter_box.SetName("Filtruj liste")
        self._apply_detailed_hints()
        #: Tekst filtra PER WIDOK (odpowiednik ``navigation.Filters``).
        self.filter_state = list_filter.FilterState()
        #: Kontekst widoku, dla ktorego pole JUZ pokazuje swoj tekst. Chroni od
        #: zapisania cudzego filtra pod kluczem widoku, do ktorego wlasnie
        #: wchodzimy: ``SetValue`` wysyla ``EVT_TEXT`` tak samo jak pisanie
        #: uzytkownika, wiec bez tej bramki przywracanie filtra samo by go
        #: nadpisywalo. ``_BRAK_KONTEKSTU``, bo ``None`` jest LEGALNYM
        #: kontekstem (widok Folderow ma ``library_view=None``).
        self._filter_context: object = _BRAK_KONTEKSTU
        #: Czy TERAZ przywracamy tekst pola z zapisanego stanu. Wtedy zmiana
        #: tekstu nie jest gestem uzytkownika i nie moze nic oglaszac.
        self._restoring_filter = False
        self.files_list = MediaListCtrl(
            self.list_panel, self.navigator.sessions[SessionId.FILES].model, "Pliki lokalne",
            self.navigator.sessions[SessionId.FILES],
        )
        self.radio_list = MediaListCtrl(
            self.list_panel, self.navigator.sessions[SessionId.RADIO].model, "Stacje radiowe",
            self.navigator.sessions[SessionId.RADIO],
        )
        self.podcasts_list = MediaListCtrl(
            self.list_panel,
            self.navigator.sessions[SessionId.PODCASTS].model,
            "Podcasty i YouTube",
            self.navigator.sessions[SessionId.PODCASTS],
        )
        self.tidal_list = MediaListCtrl(
            self.list_panel,
            self.navigator.sessions[SessionId.TIDAL].model,
            "TIDAL",
            self.navigator.sessions[SessionId.TIDAL],
        )
        self.spotify_list = MediaListCtrl(
            self.list_panel,
            self.navigator.sessions[SessionId.SPOTIFY].model,
            "Spotify",
            self.navigator.sessions[SessionId.SPOTIFY],
        )
        self.wiim_list = MediaListCtrl(
            self.list_panel,
            self.navigator.sessions[SessionId.WIIM].model,
            "Urządzenia WiiM",
            self.navigator.sessions[SessionId.WIIM],
        )
        self.sonos_list = MediaListCtrl(
            self.list_panel,
            self.navigator.sessions[SessionId.SONOS].model,
            "Grupy Sonos",
            self.navigator.sessions[SessionId.SONOS],
        )
        self.radio_list.Hide()
        self.podcasts_list.Hide()
        self.tidal_list.Hide()
        self.spotify_list.Hide()
        self.wiim_list.Hide()
        self.sonos_list.Hide()
        list_sizer = wx.BoxSizer(wx.VERTICAL)
        list_sizer.Add(self.filter_label, 0, wx.BOTTOM, 3)
        list_sizer.Add(self.filter_box, 0, wx.EXPAND | wx.BOTTOM, 8)
        list_sizer.Add(self.files_list, 1, wx.EXPAND)
        list_sizer.Add(self.radio_list, 1, wx.EXPAND)
        list_sizer.Add(self.podcasts_list, 1, wx.EXPAND)
        list_sizer.Add(self.tidal_list, 1, wx.EXPAND)
        list_sizer.Add(self.spotify_list, 1, wx.EXPAND)
        list_sizer.Add(self.wiim_list, 1, wx.EXPAND)
        list_sizer.Add(self.sonos_list, 1, wx.EXPAND)
        self.list_panel.SetSizer(list_sizer)

        # --- widok odtwarzacza (zwykle kontrolki, nie wlasne rysowanie)
        self.player_panel = wx.Panel(self.panel)
        self.now_playing = wx.StaticText(self.player_panel, label="Nic nie jest odtwarzane")
        self.now_playing.SetName("Teraz odtwarzane")
        self.time_label = wx.StaticText(self.player_panel, label="0 s / nieznany")
        self.time_label.SetName("Czas")

        self.play_button = wx.Button(
            self.player_panel, label=transport_button_label(playing=False)
        )
        self.volume_slider = wx.Slider(
            self.player_panel, value=self.options.volume, minValue=0, maxValue=100,
            style=wx.SL_HORIZONTAL,
        )
        self.volume_slider.SetName("Głośność w procentach")
        # Tempo ma tylko siedem prawdziwych wartości silnika. Pole wyboru
        # udostępnia NVDA ich znaczenie i natywnie obsługuje Home/End; suwak
        # procentowy wystawiał niejasne liczby 100 i 200 oraz sugerował
        # wartości, których silnik w ogóle nie przyjmuje.
        self.rate_choice = wx.Choice(
            self.player_panel,
            choices=[playback_rate_choice_label(rate) for rate in PLAYBACK_RATES],
        )
        self.rate_choice.SetName("Prędkość odtwarzania")
        self.rate_choice.SetSelection(PLAYBACK_RATES.index(
            clamp_playback_rate(self.options.rate)
        ))

        player_sizer = wx.BoxSizer(wx.VERTICAL)
        for control, flag in (
            (self.now_playing, 0),
            (self.time_label, 0),
            (self.play_button, 0),
            (wx.StaticText(self.player_panel, label="&Glosnosc:"), 0),
            (self.volume_slider, 0),
            (wx.StaticText(self.player_panel, label="&Predkosc:"), 0),
            (self.rate_choice, 0),
        ):
            player_sizer.Add(control, flag, wx.ALL | wx.EXPAND, 6)
        self.player_panel.SetSizer(player_sizer)
        self.player_panel.Hide()

        self.status_field = wx.StaticText(self.panel, label="Gotowe")
        self.status_field.SetName("Komunikaty")

        # NATYWNY pasek stanu ramki (``msctls_statusbar32``) -- to jego szuka
        # ``NVDA+End``. Bez niego NVDA nie znajdowal kontrolki paska stanu i
        # siekal TYTUL okna, czytajac jego ostatnie slowo ("wieczorne" z
        # "Uspokojenie wieczorne"); tak samo w widoku odtwarzacza po ``F6``.
        # Kolejna ``wx.StaticText`` tego nie naprawila, bo jej rola to
        # ``STATICTEXT``, a nie pasek stanu.
        #
        # Pasek ramki wx NIE jest w kolejnosci tabulacji i nie przyjmuje
        # fokusu, czyli spelnia warunek oryginalu z
        # ``AccessiblePlaybackStatusStrip.cs``: dostepny dla ``NVDA+End``,
        # nigdy nie bedacy celem klawiatury. Nie przejmujemy zadnego gestu
        # czytnika -- NVDA znajduje go sam.
        self.CreateStatusBar(1, style=wx.STB_DEFAULT_STYLE)
        self.status_bar = NativeStatusBar(self.GetStatusBar())
        self.status_bar.show("Gotowe")

        # Kanal mowy zostaje bez zmian; pasek stanu jest DODATKIEM obok niego,
        # a nie zamiast -- ``Announcer`` sam nic nie traci.
        self.announcer = Announcer(self.status_field, status_bar=self.status_bar)
        self._keyboard_help_active = False

        #: Sciezki WYCIETE przez Ctrl+X i jeszcze nie wklejone, po ``item_id``.
        #: Odpowiednik ``_pendingExternalMoves`` (``MainWindow.xaml.cs:25306``).
        #: Trzymamy to w pamieci okna, a NIE w profilu -- profil wspoldzielony
        #: otwieramy tylko do czytania i oczekujace przeniesienie nie jest
        #: stanem, ktory ma przetrwac zamkniecie programu.
        self.pending_external_moves: dict[str, str] = {}
        #: Pliki, ktore po Ctrl+X rzeczywiscie zniknely ze starej sciezki.
        #: To tylko filtr biezacego procesu: wspolna baza pelnego AMC pozostaje
        #: do odczytu, ale odswiezenie widoku nie moze przywrocic martwego
        #: wiersza, ktory wlasnie przeniosl shell Windows.
        self._completed_external_move_ids: set[str] = set()
        #: (Id playlisty, Id elementów) rozpoczęte przez Ctrl+X. To stan
        #: chwilowy okna; nie trafia do profilu i znika dopiero po udanym
        #: Ctrl+V albo po zastąpieniu kolejnym wyborem.
        self._pending_internal_playlist_move: (
            tuple[str, str, tuple[str, ...]] | None
        ) = None
        self._playlist_order_pending = False

        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(self.session_label, 0, wx.ALL, 8)
        outer.Add(self.list_panel, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
        outer.Add(self.player_panel, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
        outer.Add(self.status_field, 0, wx.ALL | wx.EXPAND, 8)
        self.panel.SetSizer(outer)

        self._build_menu()

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_timer, self.timer)
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self.Bind(wx.EVT_ACTIVATE, self._on_window_activate)

        self._focus_active_list_initially()

    def _focus_active_list_initially(self) -> None:
        """Fokus startowy NA LISTE, nie w pole filtra.

        Pole filtra stoi w kolejnosci tabulacji przed lista, wiec bez tego wx
        daje fokus startowy edycji -- zmierzone na zywym przebiegu:
        ``focus_class='TextCtrl'``, ``filter_has_focus=True``. Niewidomy
        uzytkownik startowalby w pustym polu, bez strzalek po pozycjach.

        To jedyne miejsce, ktore ten fokus ustawia; ``_sync_views`` dalej rusza
        fokusem TYLKO przy zmianie widoku, wiec nie ma dwoch sciezek.
        """
        self._active_list().SetFocus()

    def _build_menu(self) -> None:
        """Pasek menu z OPISU w ``menu_model`` -- bez wlasnej logiki polecen.

        Kazda pozycja konczy sie wywolaniem ``_dispatch`` z ta sama ``Action``,
        ktorej uzywa skrot klawiszowy. Nie ma tu drugiej sciezki wykonania,
        wiec menu nie moze sie rozjechac ze skrotem.

        Skrot dopisujemy do etykiety po tabulatorze: wx pokazuje go po prawej,
        a czytnik ekranu czyta razem z nazwa. To TYLKO podpis -- klawisze
        obsluguje ``_on_key``, dlatego nie rejestrujemy tu akceleratorow
        (odebralyby strzalki i literowa nawigacje natywnej liscie).
        """
        # Przy zmianie sesji budujemy nowy, krotki zestaw pozycji. Usuwamy
        # stare powiazania identyfikatorow, zeby wielokrotne Ctrl+1..Ctrl+6
        # nie dokladalo kolejnych wywolan tego samego polecenia.
        for identifier in getattr(self, "_menu_handler_ids", ()):
            self.Unbind(wx.EVT_MENU, id=identifier)
        old_bar = self.GetMenuBar() if hasattr(self, "GetMenuBar") else None
        if old_bar is not None:
            self.SetMenuBar(None)

        bar = wx.MenuBar()
        #: Pozycje zalezne od kontekstu; stan ustawia ``_refresh_menu_state``.
        self._menu_items: list[tuple[wx.MenuItem, menu_model.MenuItem]] = []
        self._menu_handler_ids: list[int] = []

        for described in menu_model.menus_for_session(
            self.navigator.active,
            self.options.session_order,
        ):
            native = wx.Menu()
            for entry in described.items:
                if entry.is_separator:
                    native.AppendSeparator()
                    continue
                if entry.builtin == "tempo-submenu":
                    native.AppendSubMenu(self._build_tempo_menu(), entry.label)
                    continue
                label = self._menu_native_label(entry)
                identifier = wx.ID_EXIT if entry.builtin == "quit" else wx.ID_ANY
                if entry.checkable:
                    # ``AppendCheckItem``, nie ``Append``: tylko pozycja
                    # zaznaczalna niesie STAN, ktory czytnik ekranu powie przy
                    # samym przejsciu po menu. Stan poczatkowy stawia
                    # ``_refresh_menu_state``, zeby byla JEDNA droga.
                    item = native.AppendCheckItem(identifier, label)
                else:
                    item = native.Append(identifier, label)
                self._menu_items.append((item, entry))
                if entry.builtin == "quit":
                    self.Bind(wx.EVT_MENU, lambda _e: self.Close(), id=item.GetId())
                else:
                    action = entry.action
                    assert action is not None  # pilnuje tego test modelu menu
                    self.Bind(
                        wx.EVT_MENU,
                        lambda _e, chosen=action: self._dispatch(chosen),
                        id=item.GetId(),
                    )
                self._menu_handler_ids.append(item.GetId())
            bar.Append(native, described.title)

        self.SetMenuBar(bar)
        if old_bar is not None:
            # Zmiana sesji moze przyjsc z pozycji wlasnie otwartego menu.
            # Niszczenie jego obiektu wewnatrz biezacego zdarzenia jest
            # ryzykowne; po powrocie do petli wx nie jest juz uzywany.
            wx.CallAfter(old_bar.Destroy)
        self._menu_session = self.navigator.active
        self._refresh_menu_state()

    def _build_tempo_menu(self) -> wx.Menu:
        """Podmenu algorytmow -- zachowane bez zmian, ze stanem Check."""
        algorithms = wx.Menu()
        self.tempo_items = {}
        for value, label in TEMPO_LABELS.items():
            item = algorithms.AppendRadioItem(wx.ID_ANY, label)
            item.Check(value == self.options.tempo_algorithm)
            self.tempo_items[value] = item
            self.Bind(
                wx.EVT_MENU,
                lambda _event, choice=value: self._set_tempo_algorithm(choice),
                id=item.GetId(),
            )
            if hasattr(self, "_menu_handler_ids"):
                self._menu_handler_ids.append(item.GetId())
        return algorithms

    def _menu_native_label(
        self,
        entry: menu_model.MenuItem,
        label_override: str | None = None,
    ) -> str:
        """Etykieta menu z czytelnym podpisem skrotu, bez obcego akceleratora."""

        label = label_override or entry.label
        if not entry.shortcut:
            return label
        text = self._menu_shortcut_text(entry.shortcut)
        if entry.accelerator:
            return f"{label}\t{text}"
        # Bez tabulatora: wx nie rejestruje akceleratora okna, ale NVDA nadal
        # czyta skrot jako czesc celowej, uzytkowej nazwy pozycji.
        return f"{label} ({text})"

    @staticmethod
    def _menu_shortcut_text(chord: str) -> str:
        """Zapis skrotu zrozumialy dla uzytkownika i dla wx.

        Nasze tablice uzywaja nazw klawiszy wx (``Back``, ``Return``), ktore po
        polsku nic nie mowia. Tlumaczymy tylko PODPIS, nie dzialanie.
        """
        names = {
            "Back": "Backspace",
            "Return": "Enter",
            "Space": "Spacja",
            "Prior": "Page Up",
            "Next": "Page Down",
        }
        head, _, key = chord.rpartition("+")
        return f"{head}+{names.get(key, key)}" if head else names.get(key, key)

    def _refresh_menu_state(self) -> None:
        """Wylaczaj pozycje, ktore teraz nie zadzialaja -- zamiast udawac.

        Uczciwie wylaczona pozycja jest dla czytnika ekranu informacja
        ("niedostepne"), a nie cisza po probie uzycia. Wspolny profil AMC
        czytamy tylko do odczytu, wiec zarzadzanie stacjami zyje wylacznie
        w sesji radiowej.
        """
        if not hasattr(self, "_menu_items"):
            return
        radio = self.navigator.active is SessionId.RADIO
        files = self.navigator.active is SessionId.FILES
        podcasts = self.navigator.active is SessionId.PODCASTS
        # "Cos gra" rozpoznajemy po TYM SAMYM statusie z hosta, z ktorego
        # korzysta ``_announce_time`` -- nie po wlasnym liczniku.
        if self.navigator.active is SessionId.TIDAL:
            playing = bool(getattr(self, "_tidal_desktop_has_playback", False))
        elif self.navigator.active is SessionId.WIIM:
            playing = bool(getattr(self, "_wiim_active_device_id", ""))
        elif self.navigator.active is SessionId.SONOS:
            playing = bool(getattr(self, "_sonos_active_group_id", ""))
        else:
            playing = bool(self._last_status)
        session = self.navigator.sessions[self.navigator.active]
        session_transport = getattr(
            self, "_transport_status_by_session", {}
        ).get(self.navigator.active, {})
        session_muted = bool(session_transport.get("muted"))
        podcast_inbox = (
            podcasts
            and session.view is View.LIST
            and session.library_view is LibraryView.PODCAST_INBOX
        )
        tidal_view_scopes = {
            LibraryView.TIDAL_LIBRARY: TIDAL_VIEW_LIBRARY,
            LibraryView.TIDAL_FAVORITES: TIDAL_VIEW_FAVORITES,
            LibraryView.TIDAL_PLAYLISTS: TIDAL_VIEW_PLAYLISTS,
        }
        tidal_scope = tidal_view_scopes.get(session.library_view)
        tidal_collection = (
            self.navigator.active is SessionId.TIDAL
            and session.view is View.LIST
            and tidal_scope is not None
        )
        spotify_scope = (
            session.spotify_context.view
            if (
                self.navigator.active is SessionId.SPOTIFY
                and session.view is View.LIST
                and isinstance(
                    session.spotify_context,
                    OpenSpotifyCollectionView,
                )
            )
            else None
        )
        spotify_collection = spotify_scope is not None
        has_row = session.model.selected_row is not None
        selected_row = session.model.selected_row
        selected_kind = (
            selected_row.kind
            if selected_row is not None
            else ""
        )
        recording_status = getattr(self, "_last_recording_status", {}) or {}
        active_recordings = recording_status.get("recordings") or []
        radio_recording = bool(
            radio
            and selected_row is not None
            and any(
                (
                    str(recording.get("stationId") or "")
                    == selected_row.item_id
                )
                or (
                    bool(selected_row.url)
                    and str(recording.get("url") or "").casefold()
                    == selected_row.url.casefold()
                )
                for recording in active_recordings
                if isinstance(recording, dict)
            )
        )
        selected_recording = next((
            recording
            for recording in active_recordings
            if isinstance(recording, dict)
            and selected_row is not None
            and (
                str(recording.get("stationId") or "") == selected_row.item_id
                or (
                    bool(selected_row.url)
                    and str(recording.get("url") or "").casefold()
                    == selected_row.url.casefold()
                )
            )
        ), None)
        recording_paused = bool(
            isinstance(selected_recording, dict)
            and (
                selected_recording.get("paused") is True
                or str(selected_recording.get("state") or "").casefold() == "paused"
            )
        )
        favorite_kinds = {
            SessionId.FILES: {"track"},
            SessionId.RADIO: {"station"},
            SessionId.PODCASTS: {"podcast", "episode"},
            SessionId.TIDAL: {"track", "video"},
        }
        playlist_kinds = {
            SessionId.FILES: {"track"},
            SessionId.RADIO: {"station"},
            SessionId.PODCASTS: {"episode"},
        }
        playlist_contents = (
            session.view is View.LIST
            and bool(session.library_playlist_id)
            and (
                self.navigator.active in (SessionId.FILES, SessionId.RADIO)
                and session.library_view is LibraryView.PLAYLIST_CONTENTS
                or self.navigator.active is SessionId.PODCASTS
                and session.library_view
                is LibraryView.PODCAST_PLAYLIST_CONTENTS
            )
        )
        podcast_sort_actions = {
            Action.SORT_PODCAST_INBOX_ADDED: SORT_ADDED_NEWEST,
            Action.SORT_PODCAST_INBOX_ALPHABETICAL: SORT_ALPHABETICAL,
            Action.SORT_PODCAST_INBOX_BY_PODCAST: SORT_CUSTOM,
        }
        tidal_sort_actions = {
            Action.SORT_TIDAL_COLLECTION_ADDED: SORT_ADDED_NEWEST,
            Action.SORT_TIDAL_COLLECTION_ALPHABETICAL: SORT_ALPHABETICAL,
            Action.SORT_TIDAL_COLLECTION_CUSTOM: SORT_CUSTOM,
        }
        spotify_sort_actions = {
            Action.SORT_SPOTIFY_COLLECTION_ADDED: SORT_ADDED_NEWEST,
            Action.SORT_SPOTIFY_COLLECTION_ALPHABETICAL: SORT_ALPHABETICAL,
            Action.SORT_SPOTIFY_COLLECTION_CATALOG: SORT_CUSTOM,
        }
        wiim_sort_actions = {
            Action.SORT_WIIM_NETWORK_STREAMS_ADDED: SORT_ADDED_NEWEST,
            Action.SORT_WIIM_NETWORK_STREAMS_ALPHABETICAL: SORT_ALPHABETICAL,
            Action.SORT_WIIM_NETWORK_STREAMS_CUSTOM: SORT_CUSTOM,
        }
        sonos_sort_actions = {
            Action.SORT_SONOS_OWN_STREAMS_ADDED: SORT_ADDED_NEWEST,
            Action.SORT_SONOS_OWN_STREAMS_ALPHABETICAL: SORT_ALPHABETICAL,
            Action.SORT_SONOS_OWN_STREAMS_CUSTOM: SORT_CUSTOM,
        }
        for item, entry in self._menu_items:
            enabled = True
            if entry.needs_radio_session and not radio:
                enabled = False
            if entry.needs_files_session and not files:
                enabled = False
            if entry.needs_radio_recording and not radio_recording:
                enabled = False
            if entry.needs_podcast_session and not podcasts:
                enabled = False
            if entry.needs_podcast_inbox and not podcast_inbox:
                enabled = False
            if entry.needs_tidal_collection and not tidal_collection:
                enabled = False
            if entry.needs_spotify_collection and not spotify_collection:
                enabled = False
            if entry.needs_wiim_stream and (
                self.navigator.active is not SessionId.WIIM
                or session.library_view is not LibraryView.WIIM_NETWORK_STREAMS
                or selected_kind != "wiimNetworkStream"
            ):
                enabled = False
            if entry.needs_sonos_own_stream and (
                self.navigator.active is not SessionId.SONOS
                or session.library_view is not LibraryView.SONOS_OWN_STREAMS
                or (
                    entry.needs_selection
                    and selected_kind != "sonosOwnStream"
                )
            ):
                enabled = False
            if entry.needs_playback and not playing:
                enabled = False
            if entry.needs_player_view and session.view is not View.PLAYER:
                enabled = False
            if entry.needs_selection and not has_row:
                enabled = False
            if entry.needs_podcast_item and (
                not podcasts or selected_kind not in ("podcast", "episode")
            ):
                enabled = False
            if entry.needs_favorite_item and selected_kind not in favorite_kinds.get(
                self.navigator.active, set()
            ):
                enabled = False
            if entry.needs_playlist_item and selected_kind not in playlist_kinds.get(
                self.navigator.active, set()
            ):
                enabled = False
            if entry.needs_queue_item:
                queue_item = bool(
                    selected_row is not None
                    and (
                        self.navigator.active is SessionId.FILES
                        and selected_kind == "track"
                        or self.navigator.active is SessionId.PODCASTS
                        and selected_kind == "episode"
                        or self.navigator.active is SessionId.TIDAL
                        and selected_kind == "track"
                        and bool(selected_row.service_id)
                        and bool(selected_row.related_album_service_id)
                    )
                )
                if not queue_item:
                    enabled = False
            if entry.needs_play_next_item and not (
                selected_row is not None
                and (
                    self.navigator.active is SessionId.FILES
                    and selected_kind == "track"
                    or self.navigator.active is SessionId.PODCASTS
                    and selected_kind == "episode"
                )
            ):
                enabled = False
            if entry.needs_podcast_library_item and not (
                podcasts
                and selected_row is not None
                and bool(selected_row.item_id)
                and (
                    selected_kind == "podcast"
                    or selected_kind == "episode" and bool(selected_row.parent_id)
                )
            ):
                enabled = False
            if entry.needs_tidal_library_item and not (
                self.navigator.active is SessionId.TIDAL
                and selected_row is not None
                and selected_kind in {"album", "artist", "playlist"}
                and bool(selected_row.item_id)
                and bool(selected_row.service_id)
            ):
                enabled = False
            if entry.needs_playlist_contents and not playlist_contents:
                enabled = False
            if entry.needs_podcast_episode and (
                not podcasts or selected_kind != "episode"
            ):
                enabled = False
            if item.IsEnabled() != enabled:
                item.Enable(enabled)
            if entry.checkable and entry.action in podcast_sort_actions:
                item.Check(
                    podcast_sort_actions[entry.action]
                    == self._podcast_inbox_sort_mode
                )
            elif entry.checkable and entry.action in tidal_sort_actions:
                item.Check(
                    tidal_scope is not None
                    and tidal_sort_actions[entry.action]
                    == self._tidal_effective_sort_modes.get(
                        tidal_scope, SORT_ADDED_NEWEST
                    )
                )
            elif entry.checkable and entry.action in spotify_sort_actions:
                item.Check(
                    spotify_scope is not None
                    and spotify_sort_actions[entry.action]
                    == self._spotify_effective_sort_modes.get(
                        spotify_scope, SORT_ADDED_NEWEST
                    )
                )
            elif entry.checkable and entry.action in wiim_sort_actions:
                item.Check(
                    wiim_sort_actions[entry.action]
                    == self._wiim_network_stream_sort_mode
                )
            elif entry.checkable and entry.action in sonos_sort_actions:
                item.Check(
                    sonos_sort_actions[entry.action]
                    == self._sonos_own_stream_sort_mode
                )
            elif entry.checkable and entry.action is Action.TOGGLE_RADIO_RECOGNITION_MONITORING:
                item.Check(self.options.radio_recognition_monitoring)
            elif entry.checkable and entry.action is Action.TOGGLE_RADIO_RECOGNITION_ANNOUNCEMENTS:
                item.Check(self.options.radio_recognition_announcements)
            elif entry.checkable and entry.action is Action.RECORD_PAUSE:
                item.Check(recording_paused)
                if recording_paused:
                    label = "&Wznów nagrywanie"
                elif radio_recording:
                    label = "&Wstrzymaj nagrywanie"
                else:
                    label = "&Wstrzymaj albo wznów nagrywanie"
                native_label = self._menu_native_label(entry, label)
                if item.GetItemLabel() != native_label:
                    item.SetItemLabel(native_label)
            elif entry.checkable and entry.action is Action.TOGGLE_MUTE:
                item.Check(session_muted)
                label = (
                    "Włącz dźwięk bieżącej sesji (&V)"
                    if session_muted
                    else "Wycisz bieżącą sesję (&V)"
                )
                native_label = self._menu_native_label(entry, label)
                if item.GetItemLabel() != native_label:
                    item.SetItemLabel(native_label)
            elif entry.checkable and entry.action is Action.KEYBOARD_HELP:
                item.Check(self._keyboard_help_active)

    def _bind_list(self, control: MediaListCtrl) -> None:
        """Wspolne powiazania klawiatury i wyboru dla list plikow i radia."""
        # Druga, bezposrednia bramka na samej kontrolce. SysListView32 potrafi
        # przejac drukowalny Shift+R jako wyszukiwanie po literze, zanim
        # zdarzenie dotrze do EVT_KEY_DOWN. Ctrl+, ma te sama pewna droge do
        # ustawien. Pozostale znaki nadal oddajemy natywnej liscie.
        control.Bind(wx.EVT_CHAR_HOOK, self._on_list_shortcut_hook)
        control.Bind(wx.EVT_KEY_DOWN, self._on_key)
        control.Bind(
            wx.EVT_LIST_ITEM_ACTIVATED,
            lambda _e: self._activate_selected_if_ready(),
        )
        control.Bind(wx.EVT_LIST_ITEM_FOCUSED, self._on_item_focused)
        control.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_item_selected)
        control.Bind(wx.EVT_LIST_ITEM_DESELECTED, self._on_item_deselected)

    def _bind_keys(self) -> None:
        self.Bind(wx.EVT_CHAR_HOOK, self._on_player_shortcut_hook)
        for control in (
            self.files_list,
            self.radio_list,
            self.podcasts_list,
            self.tidal_list,
            self.spotify_list,
            self.wiim_list,
            self.sonos_list,
        ):
            self._bind_list(control)
        for control in (self.player_panel, self.play_button):
            control.Bind(wx.EVT_KEY_DOWN, self._on_key)
        # POLE FILTRA ma WLASNA obsluge klawiszy, nie ``_on_key``: w edycji
        # litery naleza do pola, nie do skrotow. Odpowiednik bramki oryginalu
        # ``if (Keyboard.FocusedElement is TextBox)`` z
        # ``MainWindow.xaml.cs:21000`` -- tam rowniez tylko Enter/Down (i
        # osobno Escape) sa przechwytywane, a reszta idzie do pola.
        self.filter_box.Bind(wx.EVT_TEXT, self._on_filter_text)
        self.filter_box.Bind(wx.EVT_KEY_DOWN, self._on_filter_key)
        self.play_button.Bind(wx.EVT_BUTTON, lambda _e: self._play_pause())
        self.volume_slider.Bind(wx.EVT_SLIDER, self._on_volume_slider)
        self.rate_choice.Bind(wx.EVT_CHOICE, self._on_rate_choice)

    def _on_list_shortcut_hook(self, event: wx.KeyEvent) -> None:
        """Polecenia, ktorych natywna lista nie moze zabrac jako liter."""
        # Presety przechwytujemy jako caly kontrakt. Szczegolnie kombinacja
        # Ctrl+Shift+0 ginie w natywnej liscie Windows przed EVT_KEY_DOWN,
        # choc minus i znak rownosci przechodza ta sama droga poprawnie.
        if chord_from_event(event).canonical in {
            "F2",
            "Shift+F2",
            "Delete",
            "Shift+Delete",
            "Ctrl+C",
            "Ctrl+F",
            "Ctrl+Shift+F",
            "Ctrl+X",
            "Ctrl+V",
            "Ctrl+I",
            "Alt+D",
            "Alt+R",
            "Alt+Shift+R",
            "Alt+Up",
            "Alt+Down",
            "Shift+R",
            "Ctrl+Alt+S",
            "Ctrl+Alt+Shift+S",
            "Ctrl+,",
        } | set(GLOBAL_VIEW_SHORTCUTS) | set(PRESET_SHORTCUTS):
            # Ctrl+C musi zostac zatrzymane PRZED natywnym SysListView32,
            # zeby gest wykonal tylko polecenie AMC. Angielskie "Copy"
            # zgloszone w odbiorze nie pochodzi jednak z kontrolki: na
            # komputerze testowym wypowiada je globalna funkcja
            # ``clipboardCommandAnnouncement`` dodatku NVDA Extension Global
            # Plugin. Aplikacja nie moze jej wyciszyc bez przejmowania
            # zwyklych gestow NVDA; zachowujemy wiec natywna droge i wlasny,
            # prawdziwy komunikat sukcesu.
            self._on_key(event)
            return
        event.Skip()

    # -------------------------------------------------------- wyszukiwanie

    def _show_search(self, *, all_services: bool) -> None:
        """Ctrl+F/Ctrl+Shift+F: a separate catalogue window, as in AMC."""

        if self.navigator.view is View.PLAYER:
            self.announcer.say("Wyszukiwanie jest dostępne na listach")
            return
        session_before = self.navigator.active
        current_scope_label = (
            speaker_search_scope_label(session_before)
            if session_before in SPEAKER_SESSIONS
            else SESSION_LABELS[session_before]
        )

        dialog = SearchDialog(
            self,
            all_services=all_services,
            current_session_label=current_scope_label,
            run_search=lambda query, target: self._run_search_query(
                query,
                target,
                all_services=all_services,
                session_before=session_before,
            ),
            copy_text=self._to_clipboard,
            history=list(self.state.search_history.get(
                "global" if all_services else session_before.value,
                [],
            )),
            record_query=lambda query: self._record_search_query(
                "global" if all_services else session_before.value,
                query,
            ),
            detailed_hints=self._detailed_hints,
        )
        try:
            result = dialog.ShowModal()
            selected = dialog.selected_result
            selected_results = list(dialog.selected_results)
            selected_action = dialog.selected_action
        finally:
            dialog.Destroy()
        if result == wx.ID_OK and selected is not None:
            self._complete_search_result_action(
                selected,
                selected_results or [selected],
                selected_action,
            )

    def _record_search_query(self, scope: str, query: str) -> list[str]:
        history = add_search_history(
            list(self.state.search_history.get(scope, [])),
            query,
        )
        self.state.search_history[scope] = history
        try:
            self.store.save(self.state)
        except OSError:
            # Search must remain usable when the private history cannot be
            # persisted.  The in-memory list still works for this process.
            pass
        return list(history)

    @staticmethod
    def _search_dialog_alive(dialog: SearchDialog) -> bool:
        try:
            return dialog.IsShown()
        except RuntimeError:
            return False

    def _run_search_query(
        self,
        query: str,
        dialog: SearchDialog,
        *,
        all_services: bool,
        session_before: SessionId,
    ) -> None:
        sessions = (
            (
                SessionId.FILES,
                SessionId.RADIO,
                SessionId.PODCASTS,
                SessionId.TIDAL,
                SessionId.WIIM,
                SessionId.SONOS,
                SessionId.SPOTIFY,
            )
            if all_services
            else (session_before,)
        )
        speaker_snapshots = {
            session_id: (
                tuple(self.navigator.sessions[session_id].model.rows),
                self.navigator.sessions[session_id].library_view,
            )
            for session_id in sessions
            if session_id in SPEAKER_SESSIONS
        }
        cached = dialog.catalog

        def work() -> tuple[
            SearchCollection,
            list[SearchEntry],
            tuple[str, ...],
        ]:
            if cached is not None:
                collected = cached
            else:
                base = self.search_sources.collect(sessions)
                loaded_speaker_entries = tuple(
                    entry
                    for session_id, (rows, source_view) in speaker_snapshots.items()
                    for entry in speaker_search_entries(
                        session_id,
                        rows,
                        source_view,
                    )
                )
                collected = SearchCollection(
                    (*base.entries, *loaded_speaker_entries),
                    base.warnings,
                )
            results = search_entries(list(collected.entries), query)
            warnings = list(collected.warnings)
            if SessionId.RADIO in sessions:
                client = self.client
                if client is None:
                    warnings.append(
                        "Publiczny katalog stacji radiowych jest niedostępny"
                    )
                else:
                    try:
                        payload = client.search_radio_directory(query)
                        remote, remote_warnings = radio_entries_from_payload(payload)
                        results = merge_saved_and_remote(
                            results,
                            remote,
                            saved_catalog=[
                                entry for entry in collected.entries
                                if entry.session_id is SessionId.RADIO
                            ],
                        )
                        warnings.extend(remote_warnings)
                    except (HostError, HostUnavailable, ValueError):
                        warnings.append(
                            "Nie udało się przeszukać publicznego katalogu "
                            "stacji radiowych"
                        )
            if SessionId.PODCASTS in sessions:
                client = self.client
                if client is None:
                    warnings.append(
                        "Publiczne katalogi podcastów i YouTube są niedostępne"
                    )
                else:
                    try:
                        payload = client.search_podcast_directories(query)
                        remote, remote_warnings = entries_from_payload(payload)
                        results = merge_saved_and_remote(
                            results,
                            remote,
                            saved_catalog=[
                                entry for entry in collected.entries
                                if entry.session_id is SessionId.PODCASTS
                            ],
                        )
                        warnings.extend(remote_warnings)
                    except (HostError, HostUnavailable, ValueError):
                        # Zapisane wyniki pozostają użyteczne. Nie pokazujemy
                        # repr wyjątku ani nazwy klasy w dostępnej etykiecie.
                        warnings.append(
                            "Nie udało się przeszukać publicznych katalogów "
                            "podcastów i YouTube"
                        )
            # Tak jak w pełnym AMC, katalog konta TIDAL przeszukujemy tylko
            # w lokalnym Ctrl+F. Globalne Ctrl+Shift+F nie może przestać
            # działać dlatego, że wygasło logowanie jednego serwisu.
            if SessionId.TIDAL in sessions and not all_services:
                client = self.client
                if client is None:
                    warnings.append("Katalog TIDAL jest niedostępny")
                else:
                    try:
                        payload = client.tidal_search(query)
                        online = container_result_from_host(payload)
                        saved_by_service_id = {
                            candidate.row.service_id: candidate
                            for candidate in collected.entries
                            if candidate.session_id is SessionId.TIDAL
                            and candidate.row.service_id
                        }
                        known = {
                            (candidate.session_id, candidate.row.item_id)
                            for candidate in results
                        }
                        for row in online.rows:
                            candidate = saved_by_service_id.get(row.service_id)
                            if candidate is None:
                                candidate = SearchEntry(
                                    SessionId.TIDAL,
                                    row,
                                    remote_kind="tidalCatalog",
                                )
                            identity = (candidate.session_id, candidate.row.item_id)
                            if identity in known:
                                continue
                            known.add(identity)
                            results.append(candidate)
                    except (HostError, HostUnavailable, TidalContainerPayloadError):
                        warnings.append("Nie udało się przeszukać katalogu TIDAL")
            # Spotify, podobnie jak TIDAL, korzysta z katalogu konta tylko w
            # bieżącej sesji. Samo wyszukiwanie nie zapisuje żadnego wyniku.
            if SessionId.SPOTIFY in sessions and not all_services:
                client = self.client
                if client is None:
                    warnings.append("Katalog Spotify jest niedostępny")
                else:
                    try:
                        payload = client.spotify_search(query)
                        online = spotify_container_result_from_payload(payload)
                        known = {
                            (candidate.session_id, candidate.row.item_id)
                            for candidate in results
                        }
                        for row in online.rows:
                            candidate = SearchEntry(
                                SessionId.SPOTIFY,
                                row,
                                remote_kind="spotifyCatalog",
                            )
                            identity = (candidate.session_id, candidate.row.item_id)
                            if identity in known:
                                continue
                            known.add(identity)
                            results.append(candidate)
                        if online.warning:
                            warnings.append(online.warning)
                    except (
                        HostError,
                        HostUnavailable,
                        SpotifyContainerPayloadError,
                    ):
                        warnings.append("Nie udało się przeszukać katalogu Spotify")
            return collected, results, tuple(dict.fromkeys(warnings))

        def done(result: tuple[
            SearchCollection,
            list[SearchEntry],
            tuple[str, ...],
        ]) -> None:
            if self._search_dialog_alive(dialog):
                dialog.catalog = result[0]
                dialog.show_results(result[1], result[2])

        def failed(_error: Exception) -> None:
            if self._search_dialog_alive(dialog):
                dialog.search_failed()

        # One stream means a second Enter invalidates the older result.  The
        # work remains read-only; only the newest query may update the dialog.
        self.runner.submit("catalog-search", work, done, failed)

    def _complete_search_result_action(
        self,
        entry: SearchEntry,
        selected: list[SearchEntry],
        action: SearchResultAction,
    ) -> None:
        """Open the real list, then run the same command as that list uses."""

        if (
            entry.session_id is SessionId.TIDAL
            and action in (SearchResultAction.OPEN, SearchResultAction.RELATIONS)
        ):
            self._open_tidal_search_result(
                entry,
                relations=action is SearchResultAction.RELATIONS,
            )
            return

        if (
            entry.session_id is SessionId.SPOTIFY
            and action in (
                SearchResultAction.OPEN,
                SearchResultAction.RELATIONS,
                SearchResultAction.TOGGLE_PLAYBACK,
            )
        ):
            self._open_spotify_search_result(
                entry,
                relations=action is SearchResultAction.RELATIONS,
            )
            if action is SearchResultAction.TOGGLE_PLAYBACK:
                self._dispatch(Action.ACTIVATE)
            return

        if action is SearchResultAction.RELATIONS:
            self.announcer.say(
                "Przejście do albumu, wykonawcy lub podcastu jest dostępne "
                "dla wyników TIDAL i Spotify"
            )
            return

        remote = [candidate for candidate in selected if candidate.remote_kind]
        if remote:
            if len(remote) != len(selected):
                self.announcer.say(
                    "Dla jednego działania wybierz wyniki zapisane albo wyniki katalogu"
                )
                return
            targets = (
                remote
                if action in (
                    SearchResultAction.QUEUE,
                    SearchResultAction.PLAY_NEXT,
                    SearchResultAction.FAVORITE,
                    SearchResultAction.LIBRARY,
                    SearchResultAction.PLAYLIST,
                )
                else [entry]
            )
            self._complete_remote_search_result_action(targets, action)
            return

        if action is SearchResultAction.OPEN:
            self._open_search_result(entry)
            return

        selected_ids = [candidate.row.item_id for candidate in selected]

        def after_open() -> None:
            LiteFrame._perform_search_result_action(self, entry, action)

        self._open_search_result(
            entry,
            selected_ids=selected_ids,
            after_open=after_open,
        )

    def _open_tidal_search_result(
        self,
        entry: SearchEntry,
        *,
        relations: bool,
    ) -> None:
        """Use catalogue identity directly; never materialize a library row."""

        self._transient_preview_return = None
        self._switch_session(SessionId.TIDAL)
        self._run(self.navigator.open_tidal_search_result(
            entry.row,
            relations=relations,
        ))

    def _open_spotify_search_result(
        self,
        entry: SearchEntry,
        *,
        relations: bool,
    ) -> None:
        """Use the online Spotify row transiently and never save it."""

        self._transient_preview_return = None
        self._switch_session(SessionId.SPOTIFY)
        # Pierwsze przejście do sesji mogło równolegle zacząć wczytywać
        # korzeń. Wynik wyszukiwania jest jawnym celem i nie może zostać po
        # chwili przykryty spóźnioną odpowiedzią korzenia.
        self._spotify_navigation_version += 1
        self._run(self.navigator.open_spotify_search_result(
            entry.row,
            relations=relations,
        ))

    def _perform_search_result_action(
        self,
        entry: SearchEntry,
        action: SearchResultAction,
    ) -> None:
        """Uruchom dokładnie tę samą komendę co na rzeczywistej liście."""

        if action is SearchResultAction.TOGGLE_PLAYBACK:
            self._dispatch(Action.ACTIVATE)
        elif action is SearchResultAction.QUEUE:
            self._dispatch(Action.ADD_TO_QUEUE)
        elif action is SearchResultAction.PLAY_NEXT:
            self._dispatch(Action.TOGGLE_PLAY_NEXT)
        elif action is SearchResultAction.FAVORITE:
            self._dispatch(Action.TOGGLE_FAVORITE)
        elif action is SearchResultAction.LIBRARY:
            if entry.session_id is SessionId.PODCASTS:
                self._toggle_podcast_library()
            elif entry.session_id is SessionId.TIDAL:
                self._toggle_tidal_membership(favorite=False)
            else:
                self.announcer.say("Ten zapisany wynik jest już w Bibliotece")
        elif action is SearchResultAction.PLAYLIST:
            self._dispatch(Action.MANAGE_PLAYLIST_MEMBERSHIP)
        elif action is SearchResultAction.PRESET:
            self._dispatch(Action.ASSIGN_PRESET)
        elif action is SearchResultAction.INFORMATION:
            if entry.session_id is SessionId.PODCASTS:
                self._show_podcast_description()
            else:
                self._announce_quick_information()
        elif action is SearchResultAction.DOWNLOAD:
            self._dispatch(Action.DOWNLOAD_PODCAST_EPISODES)
        elif action is SearchResultAction.SAVE_AS:
            self._dispatch(Action.SAVE_PODCAST_EPISODE_AS)

    def _complete_remote_search_result_action(
        self,
        entries: list[SearchEntry],
        action: SearchResultAction,
    ) -> None:
        """Materializuj publiczny wynik, nie ujawniając jego modelowego ID."""

        if not entries:
            return
        lead = entries[0]
        if lead.session_id is SessionId.RADIO:
            self._complete_remote_radio_search_result_action(entries, action)
            return
        if lead.session_id is SessionId.TIDAL:
            if action is SearchResultAction.INFORMATION:
                self.announcer.say(lead.accessible_label)
            elif action in (SearchResultAction.LIBRARY, SearchResultAction.FAVORITE):
                self._change_tidal_search_result_membership(
                    entries,
                    favorite=action is SearchResultAction.FAVORITE,
                )
            else:
                self.announcer.say(
                    "Ten wynik TIDAL można otworzyć albo jawnie dodać do kolekcji"
                )
            return
        if lead.session_id is SessionId.SPOTIFY:
            if action is SearchResultAction.INFORMATION:
                self.announcer.say(lead.accessible_label)
            else:
                self.announcer.say(
                    "Ten wynik Spotify można przeglądać albo odtworzyć; "
                    "zapisywanie w kolekcji nie jest jeszcze dostępne"
                )
            return
        if action is SearchResultAction.INFORMATION:
            self.announcer.say(lead.accessible_label)
            return
        video_only_actions = {
            SearchResultAction.TOGGLE_PLAYBACK,
            SearchResultAction.QUEUE,
            SearchResultAction.PLAY_NEXT,
            SearchResultAction.PLAYLIST,
            SearchResultAction.PRESET,
            SearchResultAction.DOWNLOAD,
            SearchResultAction.SAVE_AS,
        }
        if (
            action in video_only_actions
            and any(entry.remote_kind != "youtubeVideo" for entry in entries)
        ):
            self.announcer.say(
                "To działanie jest dostępne dla materiałów YouTube; "
                "podcast lub kanał otwórz klawiszem Enter"
            )
            return
        if action is SearchResultAction.SAVE_AS and len(entries) != 1:
            self.announcer.say("Zapisz jako działa dla jednego materiału")
            return
        if self._podcast_add_pending:
            self.announcer.say("Dodawanie źródła już trwa")
            return
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie działa, nie mogę otworzyć wyniku")
            return

        self._podcast_add_pending = True
        started = (
            "Otwieranie wyniku katalogu"
            if action is SearchResultAction.OPEN
            else "Przygotowywanie wyniku katalogu"
        )
        self.status_field.SetLabel(started)
        self.status_bar.show(started)
        self.announcer.say(started)

        def work() -> list[dict]:
            payloads: list[dict] = []
            for entry in entries:
                payload = client.add_podcast_source(
                    entry.row.url or "",
                    entry.row.title,
                )
                if not isinstance(payload, dict):
                    raise ValueError("Nieprawidłowa odpowiedź silnika")
                payloads.append(payload)
            if action is SearchResultAction.FAVORITE:
                subscriptions = [
                    str(payload.get("subscriptionId") or "").strip()
                    for entry, payload in zip(entries, payloads)
                    if entry.remote_kind != "youtubeVideo"
                ]
                episodes = [
                    str(payload.get("preferredEpisodeId") or "").strip()
                    for entry, payload in zip(entries, payloads)
                    if entry.remote_kind == "youtubeVideo"
                ]
                subscriptions = [value for value in subscriptions if value]
                episodes = [value for value in episodes if value]
                client.toggle_podcast_favorites(subscriptions, episodes)
            return payloads

        def done(payloads: list[dict]) -> None:
            self._podcast_add_pending = False
            count = len(payloads)
            if action in (SearchResultAction.LIBRARY, SearchResultAction.FAVORITE):
                target = (
                    "ulubionych"
                    if action is SearchResultAction.FAVORITE
                    else "Biblioteki"
                )
                message = (
                    f"Dodano do {target}: {lead.row.title}"
                    if count == 1
                    else f"Dodano do {target}: {count} elementów"
                )
                self.status_field.SetLabel(message)
                self.status_bar.show(message)
                self.announcer.say(message)
                return

            first = payloads[0]
            subscription_id = str(first.get("subscriptionId") or "").strip()
            preferred_ids = [
                str(payload.get("preferredEpisodeId") or "").strip()
                for payload in payloads
            ]
            preferred_ids = [value for value in preferred_ids if value]
            if not subscription_id:
                self.announcer.say("Nie udało się otworzyć wyniku katalogu")
                return
            self._switch_session(SessionId.PODCASTS)

            def after_refresh() -> None:
                if preferred_ids:
                    self._active_list().select_item_ids(preferred_ids)
                if action is not SearchResultAction.OPEN:
                    LiteFrame._perform_search_result_action(self, lead, action)

            self._open_podcast_view(
                OpenPodcastView(
                    subscription_id=subscription_id,
                    preferred_id=preferred_ids[0] if preferred_ids else None,
                ),
                after_refresh=after_refresh,
            )

        def failed(error: Exception) -> None:
            self._podcast_add_pending = False
            message = (
                str(error)
                if isinstance(error, (HostError, HostUnavailable))
                else "Nie udało się otworzyć wyniku katalogu"
            )
            self.status_field.SetLabel(message)
            self.status_bar.show(message)
            self.announcer.say(message)

        self.runner.submit("podcast-search-action", work, done, failed)

    def _change_tidal_search_result_membership(
        self,
        entries: list[SearchEntry],
        *,
        favorite: bool,
    ) -> None:
        """Save online TIDAL rows only after an explicit collection command."""

        client = self.client
        if client is None:
            self.announcer.say("Silnik nie działa, nie mogę zmienić kolekcji TIDAL")
            return
        allowed = {"track", "video"} if favorite else {"album", "artist", "playlist"}
        rows = [
            entry.row for entry in entries
            if entry.row.kind in allowed
            and entry.row.item_id
            and entry.row.service_id
        ]
        if not rows:
            self.announcer.say(
                "Do Ulubionych TIDAL wybierz utwór lub materiał wideo"
                if favorite else
                "Do Biblioteki TIDAL wybierz album, wykonawcę albo playlistę"
            )
            return
        items = [{
            "itemId": row.item_id,
            "externalId": row.service_id,
            "title": row.title,
            "kind": row.kind,
            "artist": row.artist_name,
            "publicUri": row.url or "",
        } for row in rows]

        def done(payload: dict) -> None:
            message = str((payload or {}).get("message") or "").strip()
            self.announcer.say(message or "Zmieniono kolekcję TIDAL")

        self.runner.submit(
            "tidal-search-membership",
            lambda: client.tidal_collection_membership(
                items,
                mode="favorite" if favorite else "library",
            ),
            done,
            lambda error: self.announcer.say(
                f"Nie udało się zmienić kolekcji TIDAL: {error}"
            ),
        )

    def _complete_remote_radio_search_result_action(
        self,
        entries: list[SearchEntry],
        action: SearchResultAction,
    ) -> None:
        """Open a directory result transiently; save only on explicit request."""

        if not entries:
            return
        lead = entries[0]
        if action is SearchResultAction.INFORMATION:
            self.announcer.say(lead.accessible_label)
            return
        if action in (SearchResultAction.QUEUE, SearchResultAction.PLAY_NEXT):
            self.announcer.say("Ta funkcja nie jest dostępna w Radiu internetowym")
            return
        if action in (SearchResultAction.DOWNLOAD, SearchResultAction.SAVE_AS):
            self.announcer.say("Pobieranie nie jest dostępne dla stacji radiowych")
            return
        if action is SearchResultAction.OPEN:
            self._switch_session(SessionId.RADIO)
            self._run(self.navigator.open_radio_search_result(lead.row))
            return
        if getattr(self, "_radio_search_action_pending", False):
            self.announcer.say("Dodawanie stacji już trwa")
            return
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie działa, nie mogę otworzyć stacji")
            return

        self._radio_search_action_pending = True
        started = "Otwieranie stacji" if action is SearchResultAction.OPEN else "Przygotowywanie stacji"
        self.status_field.SetLabel(started)
        self.status_bar.show(started)
        self.announcer.say(started)

        def work() -> tuple[list[dict], dict | None]:
            payloads: list[dict] = []
            for entry in entries:
                payload = client.add_radio_station(
                    entry.row.title,
                    entry.row.url or "",
                )
                if not isinstance(payload, dict):
                    raise ValueError("Nieprawidłowa odpowiedź silnika")
                payloads.append(payload)
            favorite_payload = None
            if action is SearchResultAction.FAVORITE:
                ids = [
                    str(payload.get("preferredStationId") or "").strip()
                    for payload in payloads
                ]
                ids = [value for value in ids if value]
                if ids:
                    result = client.toggle_profile_favorites("radio", ids)
                    favorite_payload = result if isinstance(result, dict) else {}
            return payloads, favorite_payload

        def done(result: tuple[list[dict], dict | None]) -> None:
            self._radio_search_action_pending = False
            payloads, favorite_payload = result
            station_ids = [
                str(payload.get("preferredStationId") or "").strip()
                for payload in payloads
            ]
            station_ids = [value for value in station_ids if value]
            if not station_ids:
                self.announcer.say("Nie udało się otworzyć stacji")
                return
            if action in (SearchResultAction.LIBRARY, SearchResultAction.FAVORITE):
                target = "ulubionych" if action is SearchResultAction.FAVORITE else "Biblioteki"
                count = len(station_ids)
                if action is SearchResultAction.FAVORITE and favorite_payload is not None:
                    changed = int(favorite_payload.get("changed") or 0)
                    if changed <= 0:
                        message = "Ulubione bez zmian"
                    else:
                        message = (
                            f"Dodano do ulubionych: {lead.row.title}"
                            if count == 1 else f"Dodano do ulubionych: {count} elementów"
                        )
                else:
                    message = (
                        f"Dodano do {target}: {lead.row.title}"
                        if count == 1 else f"Dodano do {target}: {count} elementów"
                    )
                self.status_field.SetLabel(message)
                self.status_bar.show(message)
                self.announcer.say(message)
                return

            self._switch_session(SessionId.RADIO)

            def after_refresh() -> None:
                self._active_list().select_item_ids(station_ids)
                if action is not SearchResultAction.OPEN:
                    LiteFrame._perform_search_result_action(self, lead, action)

            self._open_radio_view(OpenLibraryView(
                None,
                preferred_id=station_ids[0],
                target_session_id=SessionId.RADIO,
            ), after_refresh=after_refresh)

        def failed(error: Exception) -> None:
            self._radio_search_action_pending = False
            message = (
                str(error)
                if isinstance(error, (HostError, HostUnavailable))
                else "Nie udało się otworzyć stacji"
            )
            self.status_field.SetLabel(message)
            self.status_bar.show(message)
            self.announcer.say(message)

        self.runner.submit("radio-search-action", work, done, failed)

    def _open_search_result(
        self,
        entry: SearchEntry,
        *,
        selected_ids: list[str] | None = None,
        after_open: Callable[[], None] | None = None,
    ) -> None:
        """Return to the result's real list and select its stable item ID."""

        self._transient_preview_return = None
        self._switch_session(entry.session_id)
        item_id = entry.row.item_id

        def complete() -> None:
            if selected_ids:
                self._active_list().select_item_ids(selected_ids)
            if after_open is not None:
                after_open()

        if entry.session_id is SessionId.FILES:
            self._open_library_view(OpenLibraryView(
                LibraryView.ALL_FILES,
                preferred_id=item_id,
                target_session_id=SessionId.FILES,
            ), after_refresh=complete)
            return
        if entry.session_id is SessionId.RADIO:
            self._open_radio_view(OpenLibraryView(
                None,
                preferred_id=item_id,
                target_session_id=SessionId.RADIO,
            ), after_refresh=complete)
            return
        if entry.session_id is SessionId.PODCASTS:
            if entry.row.kind == "episode" and entry.parent_id:
                self._open_podcast_view(OpenPodcastView(
                    subscription_id=entry.parent_id,
                    preferred_id=item_id,
                ), after_refresh=complete)
            else:
                self._open_podcast_library(
                    preferred_id=item_id,
                    after_refresh=complete,
                )
            return
        if entry.session_id is SessionId.TIDAL:
            target = entry.source_view
            if target not in (
                LibraryView.TIDAL_LIBRARY,
                LibraryView.TIDAL_FAVORITES,
                LibraryView.TIDAL_PLAYLISTS,
            ):
                target = LibraryView.TIDAL_LIBRARY
            self._open_tidal_view(
                OpenTidalView(target, preferred_id=item_id),
                after_refresh=complete,
            )
            return
        if entry.session_id in SPEAKER_SESSIONS:
            state = self.navigator.sessions[entry.session_id]
            if state.library_view is not entry.source_view:
                self.announcer.say(
                    "Wczytana lista zmieniła się. Wykonaj wyszukiwanie ponownie"
                )
                return
            if not state.model.select_id(item_id):
                self.announcer.say(
                    "Tego wyniku nie ma już na wczytanej liście"
                )
                return
            self._sync_views()
            complete()
            active = self._active_list()
            active.SetFocus()
            active.sync_cursor()

    # -------------------------------------------------------------- filtr

    def _focus_filter(self) -> None:
        """Ctrl+K: fokus do pola filtra. Port ``FocusFilter`` (cs:22210-22220).

        ``SelectAll`` jest z oryginalu i ma konkretny sens dla uzytkownika
        czytnika: ponowne Ctrl+K zaznacza caly stary tekst, wiec pisanie go
        zastepuje, a nie dokleja sie do niego po omacku.

        Komunikat idzie przez ``announcer``, czyli te sama droga, ktora caly
        port ma zmierzona na zywym NVDA. Tresc wybiera ten sam przelacznik
        ``DetailedHints`` co w glownym AMC.
        """
        if self.navigator.view is View.PLAYER:
            # W odtwarzaczu nie ma listy do filtrowania. Mowimy o tym, zamiast
            # po cichu przenosic fokus do pola schowanego pod panelem.
            self.announcer.say("Filtr dziala na liscie, nie w odtwarzaczu")
            return
        self.filter_box.SetFocus()
        self.filter_box.SelectAll()
        self.announcer.say(
            list_filter.filter_entered_message(self._detailed_hints)
        )

    def _apply_detailed_hints(self) -> None:
        """Ustaw pomoc UI Automation bez rozdmuchiwania nazwy kontrolki."""
        self.filter_box.SetHelpText(
            list_filter.FILTER_HELP_TEXT if self._detailed_hints else ""
        )

    def _on_filter_text(self, event) -> None:
        """Zmiana tekstu filtra. Port ``FilterBox_TextChanged`` (cs:23650).

        Wybor celujemy po ``item_id``, tak jak oryginal przez
        ``preferredItemId`` -- zaznaczony utwor, ktory nadal przechodzi filtr,
        ZOSTAJE zaznaczony. Nic tu nie dotyka kolejki ani zrodla danych: filtr
        jest wlasciwoscia widoku, model zostaje pelny.
        """
        event.Skip()
        if self._restoring_filter:
            # Przywracanie tekstu przy wejsciu w widok nie jest gestem
            # uzytkownika: nie oglaszamy i nie nadpisujemy stanu.
            return
        context = self._current_view_context()
        self.filter_state.set_for_view(context, self.filter_box.GetValue())
        self._filter_context = context
        # Pisanie nie jest zadaniem odczytu liczby wynikow. Zachowaj zwykle
        # echo klawiszy NVDA; brak wynikow wyjasni proba wejscia na liste.
        self._apply_filter_to_list(announce_status=False)

    def _apply_filter_to_list(self, *, announce_status: bool = True) -> None:
        """Dociagnij WIDOCZNA liste do tekstu filtra. Jedna wspolna droga.

        Nie ma tu wlasnego wstawiania wierszy: ustawiamy ``filter_query`` i
        wolamy ``sync_rows``, czyli DOKLADNIE ten mechanizm, ktorym idzie kazda
        inna zmiana listy (diff, punktowe operacje, wybor po ID, zero operacji
        gdy nic sie nie zmienilo). Dlatego filtr nie ma wlasnej sciezki, ktora
        mogla by sie rozjechac z odebranym zachowaniem list.
        """
        query = self.filter_box.GetValue()
        active = self._active_list()
        active.filter_query = query
        active.sync_rows()
        # Bramki ``needs_selection`` zaleza od tego, CO sync_rows wybral --
        # ``MediaListCtrl.sync_rows`` ustawia wybor przez ``model.select_id``
        # (gui.py:605), czyli NIE przez ``EVT_LIST_ITEM_SELECTED``. Zmierzone
        # na zywym GUI (statusclip-4): po filtrze byl zaznaczony wiersz, a
        # "Skopiuj adres" zostawalo wylaczone, wiec jego akcelerator POLYKAL
        # Ctrl+Shift+C.
        self._refresh_menu_state()
        if announce_status:
            self.announcer.say(
                list_filter.results_status_text(query, active.visible_count())
            )

    def _on_filter_key(self, event: wx.KeyEvent) -> None:
        """Klawisze W POLU filtra. Tylko te, ktore oryginal przechwytuje.

        * Enter albo strzalka w dol -> wyniki (``FocusFilterResults``, cs:22200).
          Przy PUSTYM wyniku fokus ZOSTAJE w polu, a uzytkownik slyszy, co
          zrobic -- przeniesienie fokusu na liste bez wierszy zostawiloby go
          w miejscu, z ktorego nie slychac nic.
        * Escape -> czysci filtr i wraca na liste (``ReturnToMediaListFromEscape``,
          cs:22551-22561). Drugiego stopnia oryginalu (pusty filtr => poziom
          wyzej) tu NIE MA: w tym porcie wyjscie w gore nalezy do Backspace, a
          dorzucanie Escape do nawigacji byloby zmiana poza tym przyrostem.

        KAZDY inny klawisz (litery, w tym polskie, strzalki w poziomie, Home,
        Backspace) idzie do pola przez ``event.Skip()``. Nie mapujemy niczego
        na gesty czytnika ekranu.
        """
        code = event.GetKeyCode()
        if chord_from_event(event).canonical == "Ctrl+Alt+Return":
            self._dispatch(Action.SESSION_OPTIONS)
            return
        if code in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER, wx.WXK_DOWN):
            self._focus_filter_results()
            return
        if code == wx.WXK_ESCAPE:
            self._clear_filter_and_return()
            return
        event.Skip()

    def _focus_filter_results(self) -> None:
        """Przejscie Z POLA na liste wynikow. Port ``FocusFilterResults``."""
        active = self._active_list()
        if active.visible_count() == 0:
            self.announcer.say(list_filter.NO_RESULTS_MESSAGE)
            return
        active.SetFocus()
        # Kursor dociagamy PO przejsciu fokusu: czytnik ma przeczytac wiersz,
        # na ktorym naprawde stoi lista, a nie poprzedni.
        active.sync_cursor()

    def _clear_filter_and_return(self) -> None:
        """Escape w polu: wyczysc filtr, wroc na liste. Port cs:22551-22561."""
        active = self._active_list()
        had_text = bool(self.filter_box.GetValue())
        if had_text:
            context = self._current_view_context()
            self.filter_state.clear_for_view(context)
            self._set_filter_text("")
            active.filter_query = ""
            active.sync_rows()
        active.SetFocus()
        active.sync_cursor()
        # Komunikat po przywroceniu listy, zeby opisywal stan KONCOWY.
        if had_text:
            self.announcer.say(list_filter.FILTER_CLEARED_MESSAGE)

    def _current_view_context(self) -> tuple:
        """Klucz filtra = TOZSAMOSC WIDOKU z ``navigation.view_context``.

        Ten sam klucz, po ktorym lista rozpoznaje zmiane widoku. Drugi,
        wlasny system identyfikacji rozjechalby filtr z lista po cichu.
        """
        return view_context(self.navigator.session)

    def _set_filter_text(self, text: str) -> None:
        """Wstaw tekst do pola BEZ traktowania tego jako gestu uzytkownika.

        ``SetValue`` wysyla ``EVT_TEXT`` tak samo jak pisanie, wiec bez tej
        bramki przywracanie zapisanego filtra nadpisywaloby sam siebie i
        oglaszalo status bez powodu uzytkownika.
        """
        self._restoring_filter = True
        try:
            self.filter_box.SetValue(text)
        finally:
            self._restoring_filter = False

    def _restore_filter_for_current_view(self) -> None:
        """Wejscie w widok przywraca JEGO filtr. Port ``RestoreFilterForCurrentView``.

        Wolane z ``_sync_views``, czyli z jedynej drogi odwzorowania stanu --
        bez wlasnego haka na kazda komende nawigacji.
        """
        context = self._current_view_context()
        if context == self._filter_context:
            # Ten sam widok: pole juz pokazuje swoj tekst. Nie ruszamy go, bo
            # ``SetValue`` w trakcie pisania przestawialby karetke.
            return
        self._filter_context = context
        wanted = self.filter_state.text_for_view(context)
        if self.filter_box.GetValue() != wanted:
            self._set_filter_text(wanted)
        for control in tuple(
            candidate for candidate in (
                getattr(self, "files_list", None),
                getattr(self, "radio_list", None),
                getattr(self, "podcasts_list", None),
            )
            if candidate is not None
        ):
            control.filter_query = wanted if control is self._active_list() else ""

    def _set_tempo_algorithm(self, value: int) -> None:
        """Persist only a selection acknowledged by the real host."""
        if value not in TEMPO_LABELS:
            return
        previous = self.options.tempo_algorithm
        if self.client is None:
            for algorithm, item in self.tempo_items.items():
                item.Check(algorithm == previous)
            self.announcer.say("Silnik nie jest gotowy.")
            return
        client = self.client
        # JEDEN efektywny payload: ustawienia ogolne PO nalozeniu wyborow sesji.
        # Sam ``options.audio_payload()`` ucinalby zapisane Opcje sesji -- menu
        # Dzwiek zdmuchiwaloby je przy kazdej zmianie algorytmu.
        payload = session_options.engine_audio_payload(self.state)
        payload["tempoAlgorithm"] = value
        for item in self.tempo_items.values():
            item.Enable(False)

        def restore_selection(selected: int) -> None:
            for algorithm, item in self.tempo_items.items():
                item.Check(algorithm == selected)
                item.Enable(True)

        def failed(error: Exception) -> None:
            restore_selection(previous)
            self.announcer.say(f"Nie zmieniono algorytmu: {error}")

        def done(result: dict) -> None:
            if not isinstance(result, dict) or result.get("tempoAlgorithm") != value:
                failed(RuntimeError("Silnik nie potwierdził wybranego algorytmu."))
                return
            self.options.tempo_algorithm = value
            restore_selection(value)
            if self._save_state() is False:
                return
            suffix = ". Zmiana po ponownym otwarciu materiału." if result.get("appliesOnNextPlayback") else "."
            self.announcer.say(TEMPO_LABELS[value] + suffix)

        self.runner.submit("audio-settings", lambda: client.configure_audio(**payload), done, failed)

    # --------------------------------------------------------------- silnik

    def _window_alive(self) -> bool:
        """Brama zycia okna: wynik z tla nie moze dotknac zamknietego okna."""
        return bool(self) and not self.IsBeingDeleted()

    def _queue_persistence_arguments(self) -> dict[str, object]:
        """Czy TEN start okna ma byc pisarzem zapisanej kolejki.

        Decyduje UKLAD PROFILU, nie zyczenie wywolujacego:

        * ``PRIVATE_SANDBOX`` (wlasna pelna kopia) -- host dostaje sciezke i
          jawna zgode na zapis. To jedyny tryb, w ktorym kolejka przezywa
          zamkniecie okna.
        * ``READ_ONLY_MIRROR`` (wspolny profil uzytkownika) -- NIC nie
          wysylamy. Wlascicielem tych plikow jest pelne AMC (WPF), ktore nie
          zna naszej blokady; nasz zamek nie chronilby go przed niczym.

        Brak bazy w piaskownicy to zwykle przegladanie dysku: host zostaje w
        pamieci, a stara sciezka plikow dziala bez zmian.
        """
        layout = getattr(self, "layout", None) or resolve_layout()
        if not layout.may_write_profile:
            return {}
        if not layout.library_db.exists():
            return {}
        return {"profile_dir": str(layout.library_db.parent), "queue_write": True}

    def _start_engine(self) -> None:
        persistence = self._queue_persistence_arguments()
        # Co obiecalismy uzytkownikowi: bez tej zgody ``persistent=false`` jest
        # stanem NORMALNYM, a nie awaria warta ogloszenia.
        self._queue_write_requested = bool(persistence.get("queue_write"))
        self._last_persist_error: str | None = None
        layout = getattr(self, "layout", None)
        library_db = getattr(layout, "library_db", None)
        podcasts_db = getattr(layout, "podcasts_db", None)
        state_json = getattr(layout, "state_json", None)
        client = LiteHostClient(
            default_host_path(),
            timeshift_minutes=self.options.timeshift_minutes,
            # Odczyt list nadal nalezy do Pythona w trybie ro. Sciezka daje
            # hostowi C# wyłącznie możliwość wykonania wąskiej, transakcyjnej
            # operacji ``bookmark.add`` z własną bramką konfliktu WPF.
            library_db=(str(library_db) if library_db is not None and library_db.exists() else None),
            # Python nadal otwiera baze w mode=ro. Ta sciezka daje hostowi C#
            # wylacznie waska transakcje postepu jednego odcinka.
            podcasts_db=(
                str(podcasts_db)
                if podcasts_db is not None and podcasts_db.exists()
                else None
            ),
            state_json=(
                str(state_json)
                if state_json is not None and state_json.exists()
                else None
            ),
            on_event=self._on_engine_event,
            on_stderr=lambda line: None,
            **persistence,  # type: ignore[arg-type]
        )
        self.client = client
        # TEN SAM efektywny payload co w menu Dzwiek: nowy proces musi dostac
        # ustawienia ogolne PO nalozeniu zapisanych Opcji sesji. Sam
        # ``options.audio_payload()`` dawal hostowi ustawienie ogolne, wiec
        # zapis wracal z dysku BEZ TRWALEGO SKUTKU w silniku.
        settings = session_options.engine_audio_payload(self.state)
        profile_audio_outputs = getattr(self, "_profile_audio_outputs", None)
        if profile_audio_outputs is None:
            profile_audio_outputs = (
                read_profile_outputs(state_json)
                if state_json is not None
                else {}
            )
        private_audio_outputs = getattr(
            self.state,
            "audio_output_device_ids_by_session",
            {},
        )
        # Część testów uruchamia samą tę metodę, bez importów modułu GUI.
        # Produkcja zawsze używa wspólnego, walidującego resolvera; poniższa
        # mała rezerwa zachowuje zgodność takiej izolowanej próby metody.
        output_resolver = globals().get("effective_output_device_id")
        if output_resolver is None:
            def output_resolver(session, private, profile):
                key = session.value
                if isinstance(private, dict) and key in private:
                    return private[key] or None
                return profile.get(key) or None if isinstance(profile, dict) else None
        output_devices = {
            session.value: output_resolver(
                session,
                private_audio_outputs,
                profile_audio_outputs,
            )
            for session in (
                SessionId.FILES,
                SessionId.RADIO,
                SessionId.PODCASTS,
                SessionId.SPOTIFY,
            )
        }
        # ``_start_engine`` bywa tez wywolywane przez lekkie tryby testowe i
        # awaryjne, ktore nie otwieraja profilu radia. Brak migawki oznacza
        # wtedy po prostu brak planow do zsynchronizowania, a nie blad startu
        # calego odtwarzacza.
        radio_snapshot = getattr(self, "_radio_snapshot", None)
        schedule_payload = (
            LiteFrame._radio_schedule_sync_payload(radio_snapshot, self.state)
            if radio_snapshot is not None
            else None
        )
        podcast_values = (
            self.options.podcast_downloads_folder,
            self.options.podcast_rss_refresh_interval_minutes,
            self.options.podcast_youtube_refresh_interval_minutes,
            self.options.podcast_automatic_refresh_batch_size,
        )
        podcast_settings_payload = None
        if not any(value is None for value in podcast_values):
            podcast_settings_payload = {
                "downloads_folder": str(podcast_values[0] or ""),
                "rss_refresh_interval_minutes": int(podcast_values[1]),
                "youtube_refresh_interval_minutes": int(podcast_values[2]),
                "automatic_refresh_batch_size": int(podcast_values[3]),
            }

        try:
            nvda_window_handle = int(self.GetHandle())
        except Exception:
            nvda_window_handle = 0

        def work() -> dict:
            try:
                client.start()
                client.hello()
                if nvda_window_handle > 0:
                    client.configure_nvda_bridge(nvda_window_handle)
                result = client.configure_audio(**settings)
                client.configure_local_resume(
                    self._remember_local_playback_positions
                )
                for session_id, device_id in output_devices.items():
                    client.call(
                        "audio.selectOutput",
                        {
                            "sessionId": session_id,
                            "deviceId": device_id,
                            "restart": False,
                        },
                    )
                if schedule_payload is not None:
                    client.sync_radio_schedules(schedule_payload)
                if podcast_settings_payload is not None:
                    client.configure_podcast_global_settings(
                        **podcast_settings_payload
                    )
                return result
            except Exception:
                client.close()
                raise

        def done(_result: dict) -> None:
            self.timer.Start(1000)
            # Kolejnosc listy liczy host C# (CompareInfo pl-PL), nie wlasny
            # collator w Pythonie. Podpinamy ja DOPIERO tu, bo wymaga zywego
            # silnika. Bez niej LibrarySource swiadomie oddaje kolejnosc z
            # SQL-a zamiast udawac zgodnosc.
            collation = HostCollation(client.call)
            self.library.use_collation(collation)
            # Radio nie ma wlasnego ``use_collation`` -- jego widoki sa
            # bezstanowe, wiec kolacje trzymamy TUTAJ i podajemy na wywolanie.
            # Jeden obiekt dla obu sesji: to ten sam host i ten sam cache.
            self._collation = collation
            self._load_initial_content()
            if self.options.startup_target == "SessionList":
                # Lista jest zwykłym, natywnym dialogiem i powstaje dopiero
                # po gotowości hosta. Dzięki temu Enter może od razu przejść
                # do wybranej sesji, a Cancel zostawia ostatnią sesję.
                wx.CallAfter(self._show_session_list)

        def failed(error: Exception) -> None:
            self.client = None
            _append_frontend_log(
                self.store,
                f"Silnik nie wystartował: {type(error).__name__}: {error}",
            )
            self.announcer.say(f"Silnik nie wystartował: {error}. Odtwarzanie niedostępne.")

        self.runner.submit("startup", work, done, failed)

    def _on_engine_event(self, name: str, data: dict) -> None:
        """Zdarzenie z WATKU silnika - przerzucamy do GUI przez CallAfter."""
        wx.CallAfter(self._handle_engine_event, name, data)

    def _handle_engine_event(self, name: str, data: dict) -> None:
        if not self._window_alive():
            return
        if name == nvda_bridge.EVENT_NAME:
            self._handle_nvda_command(data)
            return
        if name == "audio.outputFallback":
            paused = bool(data.get("paused"))
            previous = self._transport_status_by_session.get(SessionId.RADIO, {})
            self._transport_status_by_session[SessionId.RADIO] = {
                **previous,
                "paused": paused,
                "playing": True,
                "sessionId": SessionId.RADIO.value,
            }
            if self.navigator.active is SessionId.RADIO:
                self._set_transport_label(playing=not paused)
            self.announcer.say(
                "Wybrane urządzenie audio jest niedostępne. "
                + (
                    "Radio jest wstrzymane na urządzeniu domyślnym"
                    if paused
                    else "Radio gra na urządzeniu domyślnym"
                )
            )
        elif name == "audio.clipExportProgress":
            # Postep ma byc dostepny przez pole i NVDA+End, ale NIE moze
            # przerywac mowy co 5%. Zdarzenie koncowe jest oglaszane raz przez
            # odpowiedz operacji w ``_start_audio_clip_export``.
            operation_id = str(data.get("operationId") or "")
            if (
                self._audio_clip_export_in_progress
                and operation_id == (self._audio_clip_export_operation_id or "")
            ):
                percent = max(0, min(100, int(data.get("percent") or 0)))
                if percent != self._audio_clip_export_percent:
                    self._audio_clip_export_percent = percent
                    file_name = str(data.get("name") or "").strip()
                    text = f"Zapisywanie fragmentu: {percent}%"
                    if file_name:
                        text += f". {file_name}"
                    self.status_field.SetLabel(text)
                    self.status_bar.show(text)
        elif name == "podcast.downloadProgress":
            if self._podcast_download_pending:
                current = max(1, int(data.get("current") or 1))
                total = max(current, int(data.get("total") or current))
                title = str(data.get("title") or "odcinek").strip() or "odcinek"
                percent = int(data.get("percent") or 0)
                text = (
                    f"Pobieranie {current} z {total}: {title}"
                    if percent < 0
                    else f"Pobieranie {current} z {total}: {percent}%. {title}"
                )
                # Postęp jest dostępny przez pasek stanu i NVDA+End, lecz nie
                # przerywa mowy co kilka procent.
                self.status_field.SetLabel(text)
                self.status_bar.show(text)
        elif name == "audio.clipRemoveStarted":
            operation_id = str(data.get("operationId") or "")
            if (
                self._audio_clip_edit_in_progress
                and operation_id == (self._audio_clip_edit_operation_id or "")
            ):
                self.announcer.say("Usuwanie fragmentu. Odtwarzanie zatrzymano")
        elif name == "audio.clipRemoveProgress":
            # Jak przy eksporcie: postep jest dostepny w pasku, ale nie
            # przerywa NVDA co kilka procent. Id operacji odrzuca spoznione
            # zdarzenie poprzedniej edycji.
            operation_id = str(data.get("operationId") or "")
            if (
                self._audio_clip_edit_in_progress
                and operation_id == (self._audio_clip_edit_operation_id or "")
            ):
                percent = max(0, min(100, int(data.get("percent") or 0)))
                if percent != self._audio_clip_edit_percent:
                    self._audio_clip_edit_percent = percent
                    file_name = str(data.get("name") or "").strip()
                    text = f"Usuwanie fragmentu: {percent}%"
                    if file_name:
                        text += f". {file_name}"
                    self.status_field.SetLabel(text)
                    self.status_bar.show(text)
        elif name == "audio.clipAppendStarted":
            operation_id = str(data.get("operationId") or "")
            if (
                self._audio_clip_edit_in_progress
                and self._audio_clip_edit_kind == "append"
                and operation_id == (self._audio_clip_edit_operation_id or "")
            ):
                file_name = str(data.get("name") or "").strip()
                text = "Dopisywanie fragmentu rozpoczęte"
                if file_name:
                    text += f": {file_name}"
                self.announcer.say(text)
        elif name == "audio.clipAppendProgress":
            operation_id = str(data.get("operationId") or "")
            if (
                self._audio_clip_edit_in_progress
                and self._audio_clip_edit_kind == "append"
                and operation_id == (self._audio_clip_edit_operation_id or "")
            ):
                percent = max(0, min(100, int(data.get("percent") or 0)))
                if percent != self._audio_clip_edit_percent:
                    self._audio_clip_edit_percent = percent
                    file_name = str(data.get("name") or "").strip()
                    text = f"Dopisywanie fragmentu: {percent}%"
                    if file_name:
                        text += f". {file_name}"
                    self.status_field.SetLabel(text)
                    self.status_bar.show(text)
        elif name == "playback.started":
            # POTWIERDZENIE startu. Dopiero teraz material jest "biezacy" dla
            # Ctrl+B: samo wyslanie ``files.play`` jeszcze niczego nie dowodzi.
            # Pole nazywa sie ``id`` (LiteEngineHandlers.cs:54), nie
            # ``itemId``, i czesto niesie ``file:<path>``, bo tak host sklada
            # Id przy przegladaniu folderow -- a to NIE jest profilowe Id.
            # Dlatego tozsamosc bierzemy z kandydata zapisanego przy zlecaniu,
            # a z hosta tylko FAKT, ze start sie udal.
            if data.get("engine") == "files":
                target = self._pending_playback_session
                if target not in (SessionId.FILES, SessionId.PODCASTS):
                    target = SessionId.FILES
                self.navigator.note_playback_started(target)
                self._playing_session = target
                self._playing_sessions.discard(SessionId.FILES)
                self._playing_sessions.discard(SessionId.PODCASTS)
                self._playing_sessions.add(target)
                self._podcast_checkpoint_active = target is SessionId.PODCASTS
                if self._podcast_checkpoint_active:
                    self._podcast_checkpoint_due = 0.0
                self._local_checkpoint_active = target is SessionId.FILES
                if self._local_checkpoint_active:
                    self._local_checkpoint_due = 0.0
                self._pending_playback_session = None
            elif data.get("engine") == "radio":
                self._playing_session = SessionId.RADIO
                self._playing_sessions.add(SessionId.RADIO)
                self._schedule_radio_recognition_after_source_change()
            elif data.get("engine") == "spotify":
                pending = self._pending_spotify_playback
                item_id = str(data.get("id") or "")
                title = str(data.get("title") or "")
                if pending is not None:
                    item_id = pending.item_id
                    title = pending.title
                confirmed_row = self.navigator.note_spotify_playback_started(
                    item_id, title
                )
                if confirmed_row is not None:
                    self._record_spotify_history(confirmed_row)
                self._playing_session = SessionId.SPOTIFY
                self._playing_sessions.add(SessionId.SPOTIFY)
                self._pending_spotify_playback = None
                if self._pending_playback_session is SessionId.SPOTIFY:
                    self._pending_playback_session = None
                fallback_device = str(
                    data.get("audioOutputFallbackDeviceName") or ""
                ).strip()
                if fallback_device:
                    self.announcer.say(
                        f"Zapamiętane urządzenie audio {fallback_device} "
                        "jest niedostępne. Spotify odtwarza na domyślnym "
                        "urządzeniu systemowym"
                    )
            if data.get("tempoFallbackReason"):
                self.announcer.say(
                    "Wybrany algorytm tempa jest niedostępny. Używany SoundTouch."
                )
        elif name == "playback.ended":
            # Przy ZYWEJ kolejce koniec utworu nie jest koncem sluchania: host
            # zaraz przysle ``queue.advanced``. Mowienie "Koniec utworu" przed
            # nazwa nastepnego byloby tylko halasem, dlatego milczymy i czekamy.
            if not data.get("queueContinues"):
                self.announcer.say("Koniec utworu")
            playing_sessions = getattr(self, "_playing_sessions", set())
            if not isinstance(playing_sessions, set):
                playing_sessions = set()
            ended_podcast = SessionId.PODCASTS in playing_sessions
            if data.get("engine") == "files" and not data.get("queueContinues"):
                playing_sessions.discard(SessionId.FILES)
                playing_sessions.discard(SessionId.PODCASTS)
                self._playing_sessions = playing_sessions
            if data.get("engine") == "spotify":
                playing_sessions.discard(SessionId.SPOTIFY)
                self._playing_sessions = playing_sessions
            if ended_podcast:
                self._podcast_checkpoint_active = False
            if data.get("engine") == "files" and not data.get("queueContinues"):
                self._local_checkpoint_active = False
        elif name == "queue.advanced":
            # NATURALNE przejscie policzone przez sesje Core po stronie hosta.
            # GUI tylko odwzorowuje to, co host NAPRAWDE zaczal grac.
            self._run(self.navigator.note_queue_advanced(
                str(data.get("id") or ""), str(data.get("title") or "")
            ))
        elif name == "playback.failed":
            if data.get("engine") == "spotify":
                pending = self._pending_spotify_playback
                self._pending_spotify_playback = None
                if self._pending_playback_session is SessionId.SPOTIFY:
                    self._pending_playback_session = None
                self._playing_sessions.discard(SessionId.SPOTIFY)
                if pending is not None:
                    self.navigator.restore_spotify_playback_after_failed_handoff(
                        pending.previous_item_id,
                        pending.previous_title,
                    )
                self.announcer.say(
                    "Nie udało się odtworzyć Spotify: "
                    + str(data.get("message") or "błąd")
                )
                return
            failed_session = self._pending_playback_session
            if failed_session is None and data.get("engine") == "radio":
                failed_session = SessionId.RADIO
            if failed_session is None and data.get("engine") == "files":
                failed_session = next(
                    (
                        session
                        for session in (SessionId.PODCASTS, SessionId.FILES)
                        if session in self._playing_sessions
                    ),
                    None,
                )
            if failed_session is None:
                failed_session = self._playing_session
            self._pending_playback_session = None
            if failed_session is not None:
                self._playing_sessions.discard(failed_session)
            if failed_session is SessionId.PODCASTS:
                self._podcast_checkpoint_active = False
            if failed_session is SessionId.FILES:
                self._local_checkpoint_active = False
            self._run(self.navigator.note_playback_failed(
                f"Nie udalo sie odtworzyc: {data.get('message', 'blad')}",
                failed_session,
            ))
        elif name == "podcast.progressSaveFailed":
            self._note_podcast_progress_error(
                str(data.get("message") or "Nie udało się zapisać postępu odcinka")
            )
        elif name == "radio.nowPlaying":
            title = str(data.get("streamTitle") or "").strip()
            if title:
                self.now_playing.SetLabel(title)
                self.announcer.say(title)
                # Zdarzenie niesie tylko tytul. Pelny tekst paska (stacja,
                # parametry audio, tytul) pobierze najblizszy status hosta.
                self._refresh_status()
        elif name == "radio.recordingScheduled":
            # To zdarzenie przychodzi DOKLADNIE wtedy, gdy termin staje sie
            # wymagalny i host zaklada aktywne nagranie. Bez tej galezi plan
            # wygladal na martwy az do otwarcia dekodera albo bledu.
            station = str(data.get("stationName") or "stacja")
            self.announcer.say(
                f"Rozpoczynam zaplanowane nagrywanie: {station}"
            )
        elif name == "radio.recordingStarted":
            # Reczne Ctrl+R potwierdza odpowiedz ``recordingToggle``, a plan
            # potwierdza ``recordingScheduled``. Zdarzenie otwarcia pliku ma
            # tylko odswiezyc stan listy; drugie zdanie z nazwa pliku
            # zagluszaloby nawigacje NVDA.
            pass
        elif name == "radio.recordingFinished":
            station = str(data.get("stationName") or "stacja")
            scheduled = bool(str(data.get("scheduleName") or "").strip())
            count = int(data.get("savedFileCount") or 0)
            path = str(data.get("path") or "").strip()
            if count > 1:
                self.announcer.say(
                    f"Zakończono {'zaplanowane ' if scheduled else ''}nagrywanie {station}. "
                    f"Zapisano plików: {count}"
                )
            elif path:
                self.announcer.say(
                    f"Zakończono {'zaplanowane ' if scheduled else ''}nagrywanie "
                    f"{station}: {Path(path).name}"
                )
            else:
                self.announcer.say(
                    f"Zakończono {'zaplanowane ' if scheduled else ''}nagrywanie: {station}"
                )
        elif name == "radio.recordingStopped":
            station = str(data.get("stationName") or "stacja")
            scheduled = bool(str(data.get("scheduleName") or "").strip())
            count = int(data.get("savedFileCount") or 0)
            path = str(data.get("path") or "").strip()
            prefix = "Zatrzymano zaplanowane nagrywanie" if scheduled else "Zatrzymano nagrywanie"
            if count > 1:
                self.announcer.say(f"{prefix} {station}. Zapisano plików: {count}")
            elif path:
                self.announcer.say(f"{prefix} {station}: {Path(path).name}")
            else:
                self.announcer.say(f"{prefix}: {station}")
        elif name == "radio.recordingFailed":
            station = str(data.get("stationName") or "stacja")
            reason = str(data.get("error") or "nie utworzono pliku")
            scheduled = bool(str(data.get("scheduleName") or "").strip())
            subject = "wykonać zaplanowanego nagrania" if scheduled else "nagrać"
            self.announcer.say(f"Nie udało się {subject} {station}: {reason}")
        terminal_recording_event = name in (
            "radio.recordingFinished",
            "radio.recordingStopped",
            "radio.recordingFailed",
        )
        if terminal_recording_event:
            bookmark_error = str(data.get("bookmarkError") or "").strip()
            if bookmark_error:
                self.announcer.say(
                    f"Nie zapisano zakładek nagrania: {bookmark_error}"
                )
            self._remember_recording_result(data)
        if name.startswith("radio.recording"):
            # Zdarzenie opisuje pojedyncza zmiane, natomiast lista potrzebuje
            # pelnej migawki wszystkich nagran. Odswiezamy ja bez dodatkowego
            # komunikatu; samo zdarzenie powyzej jest jedyna mowa.
            self._refresh_recording_status()
            radio_state = self.navigator.sessions[SessionId.RADIO]
            if radio_state.library_view is LibraryView.ACTIVE_RADIO_RECORDINGS:
                self._show_active_radio_recordings(announce=False)
        if terminal_recording_event:
            files_state = self.navigator.sessions[SessionId.FILES]
            if files_state.library_view is LibraryView.RECORDED_RADIO_FILES:
                self._show_radio_recording_history(announce=False)
        if name == "queue.advanced" or (
            name in ("playback.started", "playback.ended")
            and data.get("engine") == "files"
        ):
            self._refresh_live_queue()
        if name == "queue.advanced" or (
            name == "playback.ended" and data.get("engine") == "files"
        ):
            # Także ostatni utwór zapisuje pustkę, ale nie emituje queue.advanced.
            # Kolejka WLASNIE sie zmienila, czyli host wlasnie probowal ja
            # zapisac. Pytamy tu, a nie w _refresh_live_queue, bo tamta droga
            # istnieje tylko w otwartym Ctrl+Q.
            self._check_queue_persistence()

    # --------------------------------------------- slyszalna trwalosc kolejki

    def _note_queue_persistence(self, payload: dict) -> None:
        """Powiedz PRAWDE o zapisie kolejki -- raz, a nie co zdarzenie.

        Zasady, w tej kolejnosci:

        * Nie prosilismy o zapis (zwykly, tylko-do-odczytu start) -->
          ``persistent=false`` jest stanem normalnym. Milczymy; obiecywanie
          albo oplakiwanie trwalosci, ktorej nie zamawialismy, to halas.
        * Zapis sie udal --> tez milczymy. Powodzenie nie jest komunikatem.
        * Swiadomy pisarz dostal odmowe --> mowimy, co sie stalo i dlaczego,
          krotko. Powtorzenia TEJ SAMEJ przyczyny tlumimy: host przysyla ja
          przy kazdym przejsciu kolejki, a czytnik ekranu nie jest logiem.
        """
        if not getattr(self, "_queue_write_requested", False):
            return
        error = str((payload or {}).get("persistError") or "").strip()
        if not error:
            # Zapis wrocil do zdrowia: nastepna awaria znow jest nowiną.
            self._last_persist_error = None
            return
        if error == getattr(self, "_last_persist_error", None):
            return
        self._last_persist_error = error
        self.announcer.say(f"Nie zapisałem kolejki: {error}")

    def _handle_nvda_command(self, data: dict) -> None:
        """Wykonaj jedno polecenie istniejącego dodatku i odeślij wynik.

        Zdarzenie pochodzi wyłącznie z hosta C#, który sprawdził wersję,
        długość i białą listę na potoku bieżącego użytkownika. Walidujemy je
        ponownie przed dotknięciem UI. Id korelacji nigdy nie jest czytane ani
        pokazywane w kontrolce.
        """
        client = self.client
        if client is None or not client.alive or not isinstance(data, dict):
            return
        request_id = data.get("requestId")
        command = data.get("command")
        if not isinstance(request_id, str) or not request_id:
            return

        if not isinstance(command, str) or command not in nvda_bridge.ALLOWED_COMMANDS:
            ok, message = False, "Nieobsługiwane polecenie dodatku AMC."
        else:
            try:
                ok, message = self._execute_nvda_command(command)
            except Exception as error:
                _append_frontend_log(
                    self.store,
                    f"Polecenie dodatku NVDA nie powiodło się: {type(error).__name__}: {error}",
                )
                ok, message = False, "Nie udało się wykonać polecenia dodatku AMC."

        try:
            client.reply_to_nvda(request_id, ok=ok, message=message)
        except (HostError, HostUnavailable):
            # Dodatek ma własny limit czasu i poda użytkownikowi jednoznaczny
            # komunikat. Nie dokładamy drugiej, spóźnionej zapowiedzi w oknie.
            pass

    def _execute_nvda_command(self, command: str) -> tuple[bool, str]:
        visible_auxiliary_window = any(
            window is not self
            and bool(getattr(window, "IsShown", lambda: False)())
            for window in wx.GetTopLevelWindows()
        )
        if (
            visible_auxiliary_window
            and command not in nvda_bridge.WORKS_WITH_OPEN_WINDOW
        ):
            return (
                False,
                "AMC jest zajęty. Zamknij otwarte okno dialogowe lub spróbuj za chwilę.",
            )

        if command in nvda_bridge.READ_COMMANDS:
            return True, {
                "status": self._nvda_status_message,
                "context": self._nvda_context_message,
                "nowPlaying": self._nvda_now_playing_message,
            }[command]()

        if command in nvda_bridge.SPECIAL_COMMANDS:
            direction = 1 if command == "presetNext" else -1
            self._navigate_nvda_preset(direction)
            return True, (
                "Następny preset" if direction > 0 else "Poprzedni preset"
            )

        if command in nvda_bridge.KNOWN_NOT_IMPLEMENTED:
            return False, nvda_bridge.unavailable_message(command)

        if command in nvda_bridge.SESSION_COMMANDS:
            sessions = tuple(SessionId)
            current = sessions.index(self.navigator.active)
            direction = 1 if command == "sessionNext" else -1
            target = sessions[(current + direction) % len(sessions)]
            self._switch_session(target)
            return True, SESSION_LABELS[target]

        action = nvda_bridge.action_for(command)
        if action is None:
            return False, "Nieobsługiwane polecenie dodatku AMC."
        if not self._action_available_in_active_session(action):
            return False, "To polecenie nie jest dostępne w bieżącej sesji."

        if command in nvda_bridge.OPEN_WINDOW_COMMANDS:
            # Najpierw odpowiadamy dodatkowi, dopiero w następnym obrocie
            # pętli UI otwieramy ewentualne okno modalne. Inaczej dialog
            # zatrzymałby odpowiedź aż do zamknięcia i dodatek zgłosił timeout.
            _present_main_window(self)
            wx.CallAfter(self._dispatch, action)
            return True, ""

        self.announcer.begin_capture()
        try:
            self._dispatch(action)
        except Exception:
            self.announcer.end_capture()
            raise
        message = self.announcer.end_capture()
        return True, message

    def _nvda_playback_snapshot(self) -> dict:
        if self.navigator.active is SessionId.WIIM:
            return self._wiim_snapshot
        if self.navigator.active is SessionId.SONOS:
            return self._sonos_snapshot
        return self._transport_status_by_session.get(self.navigator.active, {})

    def _nvda_status_message(self) -> str:
        session = self.navigator.session
        session_name = SESSION_LABELS[self.navigator.active]
        if self.navigator.active is SessionId.TIDAL:
            # TIDAL gra w obcej aplikacji. Dopóki nie przechowujemy ostatniej
            # migawki SMTC, nie wolno z samego tytułu wywnioskować „pauzy” ani
            # „odtwarzania”: byłby to wymyślony stan czytany globalnie przez
            # NVDA. Informujemy wyłącznie o tym, co AMC naprawdę wie.
            if not self._tidal_desktop_has_playback:
                return "TIDAL, brak otwartego nagrania."
            title = session.now_playing_title.strip()
            if title:
                return f"{title}, TIDAL, sterowanie w oryginalnej aplikacji."
            return "TIDAL, materiał otwarty w oryginalnej aplikacji."

        snapshot = self._nvda_playback_snapshot()
        title = str(
            session.now_playing_title
            or snapshot.get("title")
            or snapshot.get("currentTitle")
            or ""
        ).strip()
        if not title:
            return f"{session_name}, brak otwartego nagrania."

        playback = str(snapshot.get("playbackState") or "").casefold()
        paused = bool(snapshot.get("paused")) or playback in {
            "paused", "pause", "wstrzymano", "zatrzymane", "stopped"
        }
        state = "pauza" if paused else "odtwarzanie"
        muted = ", wyciszone" if bool(snapshot.get("muted")) else ""
        raw_volume = snapshot.get("volume", self.options.volume)
        volume = (
            int(raw_volume)
            if isinstance(raw_volume, (int, float)) and not isinstance(raw_volume, bool)
            else self.options.volume
        )
        recording = ""
        if self.navigator.active is SessionId.RADIO:
            station_id = str(
                snapshot.get("id") or session.now_playing_id or ""
            ).strip()
            recording = current_station_recording_label(
                getattr(self, "_last_recording_status", {}),
                station_id,
            )
        recording_part = f", {recording}" if recording else ""
        return (
            f"{title}, {session_name}, {state}{recording_part}{muted}, "
            f"głośność {volume}%."
        )

    def _nvda_context_message(self) -> str:
        session_name = SESSION_LABELS[self.navigator.active]
        if self.navigator.session.view is View.PLAYER:
            return f"{session_name}, Odtwarzacz"
        label = str(self._active_list().GetName() or session_name).strip()
        if len(label) > 240:
            label = label[:240]
        return f"{session_name}, {label}"

    def _nvda_now_playing_message(self) -> str:
        snapshot = self._nvda_playback_snapshot()
        if self.navigator.active is SessionId.TIDAL:
            if not self._tidal_desktop_has_playback:
                return "TIDAL, brak bieżącego materiału w AMC."
            title = self.navigator.session.now_playing_title.strip()
            return title or "TIDAL, brak informacji o tytule."
        if self.navigator.active is SessionId.RADIO:
            text = str(snapshot.get("currentBroadcastText") or "").strip()
            if text:
                return text
        if self.navigator.active is SessionId.WIIM:
            text = wiim_now_playing_label(snapshot).strip()
            if text:
                return text
        if self.navigator.active is SessionId.SONOS:
            text = sonos_now_playing_label(snapshot).strip()
            if text:
                return text
        title = self.navigator.session.now_playing_title.strip()
        return title or f"{SESSION_LABELS[self.navigator.active]}, nic nie jest odtwarzane."

    def _check_queue_persistence(self) -> None:
        """Zapytaj o stan zapisu po NATURALNYM przejsciu kolejki.

        Osobno od ``_refresh_live_queue``, bo ta milczy poza widokiem Ctrl+Q --
        a blad zapisu trzeba uslyszec takze patrzac na odtwarzacz. Pytanie
        idzie przez ``runner`` (czyli POZA brama hosta i bez trzymania zamkow
        koordynatora), zadnego nowego timera ani drugiego silnika.
        """
        client = self.client
        if client is None or not getattr(self, "_queue_write_requested", False):
            return

        def done(payload: dict) -> None:
            if self._window_alive():
                self._note_queue_persistence(payload or {})

        def failed(error: Exception) -> None:
            # Samo pytanie padlo; to NIE jest dowod odmowy zapisu, wiec nie
            # zmyslamy przyczyny.
            return None

        self.runner.submit("queue-persist", client.queue_status, done, failed)

    # ------------------------------------------------------- tresc poczatkowa

    def _load_initial_content(self) -> None:
        # Zaznaczenie idzie za radio.currentItemId profilu AMC, a nie wraca
        # odruchowo na wiersz 0 (w zmierzonym profilu biezaca stacja ma indeks 80).
        self._run(self.navigator.apply_stations(
            rows_from_stations(self.stations.as_payload()),
            preferred_id=self._radio_snapshot.current_id,
        ))
        # Porzadek profilu obowiazuje juz po starcie, nie dopiero po Ctrl+L.
        # Wstepne dane zapewniaja liste takze przy odmowie drugiego odczytu;
        # finalny odczyt/kolacja sa poza watkiem GUI. Brak preferred_id chroni
        # wybor wykonany przez uzytkownika w czasie oczekiwania.
        self._open_radio_view(OpenLibraryView(
            view=None, target_session_id=SessionId.RADIO,
        ))
        # Blad ODCZYTU stacji nie jest tym samym co profil bez stacji. Dopoki
        # RadioSource oddawalo pusta liste w obu przypadkach, uzytkownik slyszal
        # cisze takze wtedy, gdy profil byl uszkodzony albo zajety.
        if self._radio_snapshot.load_error:
            self.announcer.say(self._radio_snapshot.load_error)
        if getattr(self.navigator, "active", None) is SessionId.PODCASTS:
            self._open_podcast_library(
                preferred_id=self.navigator.sessions[SessionId.PODCASTS].list_anchor_id
            )
        if getattr(self.navigator, "active", None) is SessionId.WIIM:
            self._load_wiim_devices(
                preferred_id=self.navigator.sessions[SessionId.WIIM].list_anchor_id
            )
        if getattr(self.navigator, "active", None) is SessionId.SONOS:
            self._load_sonos_targets(
                preferred_id=self.navigator.sessions[SessionId.SONOS].list_anchor_id
            )
        # Biblioteka AMC ma PIERWSZENSTWO nad przegladaniem dysku. Dawniej
        # bylo odwrotnie: pytalismy ``Path(folder).exists()``, a skoro sciezki
        # profilu (D:\, C:\Users\micha) na tej maszynie nie istnieja, lista pod
        # Ctrl+1 byla pusta -- to jest zglaszany blad.
        if self.library.is_available:
            # ``saved_folder`` otwiera SQLite, a jestesmy w ``done()`` zadania
            # startowego, czyli pod ``wx.CallAfter``. Nieobsluzony wyjatek nie
            # wyszedlby poza log i okno zostaloby puste ORAZ ciche. Zamiast tego
            # mowimy co sie stalo i wczytujemy Biblioteke od korzenia -- blad
            # ZAPAMIETANEGO folderu nie moze odciac calej Biblioteki.
            try:
                folder = self.library.saved_folder()
            except Exception as error:
                self.announcer.say(
                    f"Nie mogę odczytać zapamiętanego folderu: {error}. "
                    "Pokazuję Bibliotekę od początku."
                )
                folder = None
            self._open_library(folder)
            return
        folder = self.navigator.sessions[SessionId.FILES].folder_path or self.options.last_folder
        if folder and Path(folder).exists():
            self._open_folder(folder)
        else:
            self.announcer.say(self.library.describe() or "Wybierz folder: Ctrl+O")

    def _return_to_library(self) -> None:
        """Ctrl+L: powrot do ZAPAMIETANEGO widoku Biblioteki (cs:701-705).

        Nazwe widoku czytamy z profilu teraz, w watku GUI -- to jeden wiersz
        ``local_state``, nie lista. Blad odczytu nie moze odciac Biblioteki
        (jak przy ``saved_folder``, gui.py:1661-1668), wiec wtedy wracamy do
        Folderow i mowimy, co sie stalo.
        """
        if self.navigator.active is SessionId.RADIO:
            self._run(self.navigator.return_to_library(LIBRARY_VIEW_FOLDERS))
            return
        if self.navigator.active is SessionId.PODCASTS:
            self._open_podcast_library(
                preferred_id=self.navigator.sessions[SessionId.PODCASTS].library_return_id
            )
            return
        if self.navigator.active is SessionId.TIDAL:
            self._open_tidal_view(OpenTidalView(
                LibraryView.TIDAL_LIBRARY,
                preferred_id=self.navigator.sessions[SessionId.TIDAL].library_return_id,
            ))
            return
        if self.navigator.active is SessionId.SPOTIFY:
            self._open_spotify_view(OpenSpotifyView(
                preferred_id=self.navigator.sessions[SessionId.SPOTIFY].library_return_id,
            ))
            return
        if not self.library.is_available:
            self.announcer.say(self.library.describe() or "Biblioteka niedostepna")
            return
        try:
            saved = self.library.saved_library_view()
        except Exception as error:
            self.announcer.say(
                f"Nie mogę odczytać zapamiętanego widoku Biblioteki: {error}. "
                "Pokazuję Foldery."
            )
            saved = LIBRARY_VIEW_FOLDERS
        self._run(self.navigator.return_to_library(saved))

    def _open_library(self, folder: str | None, preferred_id: str | None = None) -> None:
        """Wczytanie poziomu Biblioteki z SQLite -- POZA watkiem GUI.

        Baza ma 11 tysiecy rekordow, wiec odczyt nie moze blokowac okna, nawet
        jesli jest szybki.

        BEZ zapowiedzi \"Wczytywanie...\": oryginal przy wejsciu w widok nic
        takiego nie mowi, a dla uzytkownika czytnika to szum przed KAZDA lista.
        Komunikaty o PUSTEJ bibliotece, degradacji odczytu i bledzie zostaja --
        usuwamy rutyne, nie diagnostyke.
        """

        def work() -> LibrarySnapshot:
            return self.library.load(folder)

        def done(snapshot: LibrarySnapshot) -> None:
            if snapshot.is_empty:
                self.announcer.say("Biblioteka jest pusta")
                return
            # Degradacja odczytu (stara migawka, zastepcza kolejnosc) NIE MOZE
            # przejsc w ciszy: do tej pory oba pola snapshotu byly martwe.
            notice = degradation_notice(snapshot)
            if notice:
                self.announcer.say(notice)
            self._run(self.navigator.apply_folder(
                snapshot.folder_path or "", snapshot.rows, preferred_id=preferred_id))

        def failed(error: Exception) -> None:
            self.announcer.say(f"Nie moge wczytac Biblioteki: {error}")

        self.runner.submit("folder", work, done, failed)

    _VIEW_KEYS = {
        LibraryView.ALL_FILES: "all_files",
        LibraryView.FAVORITES: "favorites",
        LibraryView.PLAYLISTS: "playlists",
        LibraryView.PLAYLIST_CONTENTS: "playlist_contents",
        LibraryView.HISTORY: "history",
        LibraryView.SAVED_QUEUE: "saved_queue",
        LibraryView.ITEM_BOOKMARKS: "item_bookmarks",
        LibraryView.ALL_BOOKMARKS: "all_bookmarks",
    }

    def _open_radio_view(
        self,
        intent: OpenLibraryView,
        *,
        restore_selected_ids: list[str] | None = None,
        after_refresh: Callable[[], None] | None = None,
    ) -> None:
        """Odczyt Radia ma osobny bilet zadania, bez lokalnego katalogu plikow."""
        if intent.view not in (
            None,
            LibraryView.FAVORITES,
            LibraryView.HISTORY,
            LibraryView.PLAYLISTS,
            LibraryView.PLAYLIST_CONTENTS,
        ):
            self.announcer.say("Ten widok nie jest jeszcze dostępny w Radiu")
            return
        source = self.radio
        scope = (
            "playlist_contents"
            if intent.view is LibraryView.PLAYLIST_CONTENTS
            else intent.view.value if intent.view else "library"
        )
        # Kolacje czytamy TERAZ, w watku GUI, i wysylamy jako wartosc --
        # zagladanie do pola okna z watku roboczego scigaloby sie ze startem
        # silnika. ``None`` znaczy ,,hosta jeszcze nie ma'' i widok uczciwie
        # nazwie kolejnosc zastepcza.
        collation = getattr(self, "_collation", None)

        def work():
            from .radio_views import load_view
            return load_view(
                source,
                scope,
                collation=collation,
                playlist_id=intent.playlist_id,
            )

        def done(result) -> None:
            if result.unavailable_reason:
                if self.navigator.active is SessionId.RADIO:
                    self.announcer.say(result.unavailable_reason)
                return
            events = self.navigator.apply_radio_view(
                intent.view, result.heading, result.rows,
                preferred_id=intent.preferred_id,
                order_matches_amc=result.order_matches_amc,
                playlist_id=intent.playlist_id,
                fallback_to_playlists=result.fallback_to_playlists,
            )
            # Odczyt zaczal sie w Radiu, ale uzytkownik mogl juz przejsc do Plikow.
            # Zachowujemy stan wlasciwej sesji, nie przestawiamy obcego fokusu.
            if self.navigator.active is SessionId.RADIO:
                self._run(events)
                if (
                    restore_selected_ids
                    and self.navigator.session.library_view
                    is LibraryView.PLAYLIST_CONTENTS
                    and self.navigator.session.library_playlist_id
                    == intent.playlist_id
                ):
                    self._active_list().select_item_ids(restore_selected_ids)
                if result.missing_item_count:
                    self.announcer.say(
                        f"Pozycje historii bez stacji w profilu: {result.missing_item_count}")
                if after_refresh is not None:
                    after_refresh()

        def failed(error: Exception) -> None:
            if self.navigator.active is SessionId.RADIO:
                if after_refresh is not None:
                    after_refresh()
                self.announcer.say(f"Nie mogę wczytać listy radia: {error}")

        self.runner.submit("radio-view", work, done, failed)

    def _open_tidal_view(
        self,
        intent: OpenTidalView,
        *,
        after_refresh: Callable[[], None] | None = None,
    ) -> None:
        """Read one account collection view, with the saved cache as fallback."""
        scopes = {
            LibraryView.TIDAL_LIBRARY: TIDAL_VIEW_LIBRARY,
            LibraryView.TIDAL_FAVORITES: TIDAL_VIEW_FAVORITES,
            LibraryView.TIDAL_PLAYLISTS: TIDAL_VIEW_PLAYLISTS,
        }
        scope = scopes.get(intent.view)
        if scope is None:
            self.announcer.say("Ten widok nie jest dostępny w TIDAL")
            return
        self._tidal_navigation_version += 1
        version = self._tidal_navigation_version
        client = self.client
        sort_override = self.state.tidal_sort_modes.get(scope)
        collation = getattr(self, "_collation", None)

        def work():
            if client is not None:
                try:
                    payload = client.tidal_collection_view(scope)
                    fresh = container_result_from_host(payload)
                    result = self.tidal.order_rows(
                        scope,
                        fresh.heading,
                        fresh.rows,
                        sort_mode=sort_override,
                        collation=collation,
                    )
                    warning = (
                        str(payload.get("warning") or "").strip()
                        if isinstance(payload, dict) else ""
                    )
                    return result, warning
                except Exception as error:
                    cached = self.tidal.load_view(
                        scope,
                        sort_mode=sort_override,
                        collation=collation,
                    )
                    return cached, (
                        "Nie udało się odświeżyć TIDAL; pokazano ostatni "
                        f"zapis: {error}"
                    )
            return self.tidal.load_view(
                scope,
                sort_mode=sort_override,
                collation=collation,
            ), ""

        def done(result) -> None:
            if (
                version != self._tidal_navigation_version
                or self.navigator.active is not SessionId.TIDAL
            ):
                return
            view_result, warning = result
            self._tidal_effective_sort_modes[scope] = view_result.sort_mode
            events = self.navigator.apply_tidal_view(
                intent.view,
                view_result.heading,
                list(view_result.rows),
                preferred_id=intent.preferred_id,
                order_matches_amc=view_result.order_matches_amc,
            )
            # Wynik aktualizuje tylko stan TIDAL. Jeśli użytkownik zdążył
            # przejść do innej sesji, nie przenosimy tam fokusu ani mowy.
            if intent.announcement:
                self._sync_views()
                if view_result.rows:
                    self.announcer.say(intent.announcement)
                else:
                    empty = next(
                        (event.text for event in events if isinstance(event, Announce)),
                        view_result.heading,
                    )
                    self.announcer.say(f"{intent.announcement}, {empty}")
            else:
                self._run(events)
            self._refresh_menu_state()
            if warning:
                self.announcer.say(warning)
            if after_refresh is not None:
                after_refresh()

        def failed(error: Exception) -> None:
            if (
                version != self._tidal_navigation_version
                or self.navigator.active is not SessionId.TIDAL
            ):
                return
            self.announcer.say(
                str(error)
                if isinstance(error, TidalProfileError)
                else "Nie udało się odczytać biblioteki TIDAL"
            )

        self.runner.submit("tidal-view", work, done, failed)

    def _open_tidal_container(self, intent: OpenTidalContainer) -> None:
        """Open album, playlist or artist section through the shared C# API."""
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie jest gotowy")
            return
        self._tidal_navigation_version += 1
        version = self._tidal_navigation_version

        def work():
            payload = client.tidal_container_items(
                item_id=intent.item_id,
                external_id=intent.service_id,
                title=intent.title,
                kind=intent.kind,
                artist=intent.artist,
                public_uri=intent.public_uri,
                artist_section=intent.artist_section,
            )
            return container_result_from_host(payload)

        def done(result) -> None:
            if (
                version != self._tidal_navigation_version
                or self.navigator.active is not SessionId.TIDAL
            ):
                return
            self._run(self.navigator.apply_tidal_container(
                intent,
                result.heading,
                list(result.rows),
            ))

        def failed(error: Exception) -> None:
            if (
                version != self._tidal_navigation_version
                or self.navigator.active is not SessionId.TIDAL
            ):
                return
            if isinstance(error, (HostError, TidalContainerPayloadError)):
                self.announcer.say(str(error))
            else:
                self.announcer.say("Nie udało się otworzyć katalogu TIDAL")

        self.runner.submit("tidal-navigation", work, done, failed)

    def _show_tidal_relations(self, intent: ShowTidalRelations) -> None:
        """Show a keyboard-driven destination list without a context-menu role."""
        if not intent.choices:
            return
        # Gdy istnieje tylko jeden jednoznaczny cel (np. album -> wykonawca),
        # prawa strzalka wykonuje go od razu. Przy wielu celach zwykle
        # wx.Menu dodawalo w mowie „menu kontekstowe”, a tytul wygladal jak
        # trzecia pozycja. Natywna lista pokazuje wylacznie prawdziwe cele.
        if len(intent.choices) == 1:
            self._run(self.navigator.activate_tidal_relation(intent.choices[0]))
            return
        active_list = self._active_list()
        dialog = RelationDestinationDialog(
            self,
            title=intent.title,
            labels=tuple(choice.label for choice in intent.choices),
        )
        selected: int | None = None
        try:
            if dialog.ShowModal() == wx.ID_OK:
                selected = dialog.selected_index
        finally:
            dialog.Destroy()
            wx.CallAfter(active_list.SetFocus)
        if selected is not None:
            self._run(self.navigator.activate_tidal_relation(intent.choices[selected]))

    # ------------------------------------------------------------- Spotify

    def _open_spotify_view(self, intent: OpenSpotifyView) -> None:
        """Read the fixed Spotify collection root and its account status."""

        client = self.client
        if client is None:
            self.announcer.say("Silnik nie jest gotowy")
            return
        self._spotify_navigation_version += 1
        version = self._spotify_navigation_version

        def work():
            root = spotify_root_result_from_payload(client.spotify_collection_root())
            try:
                account = spotify_account_summary_from_payload(
                    client.spotify_account_status()
                )
            except (HostError, HostUnavailable):
                account = spotify_account_summary_from_payload(None)
            return root, account

        def done(result) -> None:
            if (
                version != self._spotify_navigation_version
                or self.navigator.active is not SessionId.SPOTIFY
            ):
                return
            root, account = result
            self._run(self.navigator.apply_spotify_view(
                root.heading,
                list(root.rows),
                preferred_id=intent.preferred_id,
            ))
            if account.label and not account.connected:
                self.announcer.say(account.label)

        def failed(error: Exception) -> None:
            if (
                version != self._spotify_navigation_version
                or self.navigator.active is not SessionId.SPOTIFY
            ):
                return
            self.announcer.say(
                str(error)
                if isinstance(error, (HostError, SpotifyContainerPayloadError))
                else "Nie udało się otworzyć biblioteki Spotify"
            )

        self.runner.submit("spotify-navigation", work, done, failed)

    def _open_spotify_collection_view(
        self,
        intent: OpenSpotifyCollectionView,
        *,
        attempt: int = 0,
    ) -> None:
        """Read one collection category without changing the account."""

        client = self.client
        if client is None:
            self.announcer.say("Silnik nie jest gotowy")
            return
        self._spotify_navigation_version += 1
        version = self._spotify_navigation_version
        previous_count = self._spotify_loaded_counts.get(intent.view, 0)
        requested = requested_count(
            previous_count,
            load_more=intent.load_more,
        )
        sort_mode = getattr(self, "_spotify_effective_sort_modes", {}).get(
            intent.view,
            SORT_ADDED_NEWEST,
        )

        def work():
            return spotify_container_result_from_payload(
                client.spotify_collection_view(
                    intent.view,
                    loaded_count=requested,
                    sort_mode=sort_mode,
                )
            )

        def done(result) -> None:
            if (
                version != self._spotify_navigation_version
                or self.navigator.active is not SessionId.SPOTIFY
            ):
                return
            rows = list(result.rows)
            loaded_count = len(rows)
            self._spotify_loaded_counts[intent.view] = loaded_count
            preferred_id = intent.preferred_id
            if intent.load_more and previous_count < loaded_count:
                preferred_id = rows[previous_count].item_id
            if result.has_more:
                rows.append(load_more_row(
                    f"spotify:{intent.view}",
                    loaded_count,
                ))
            self._run(self.navigator.apply_spotify_collection_view(
                intent,
                result.heading,
                rows,
                preferred_id=preferred_id,
            ))
            if result.warning:
                self.announcer.say(result.warning)

        def failed(error: Exception) -> None:
            if (
                version != self._spotify_navigation_version
                or self.navigator.active is not SessionId.SPOTIFY
            ):
                return
            if LiteFrame._retry_busy_spotify_navigation(
                self,
                error,
                version=version,
                attempt=attempt,
                retry=lambda: self._open_spotify_collection_view(
                    intent,
                    attempt=attempt + 1,
                ),
            ):
                return
            self.announcer.say(
                str(error)
                if isinstance(error, (HostError, SpotifyContainerPayloadError))
                else "Nie udało się odczytać kolekcji Spotify"
            )

        self.runner.submit("spotify-navigation", work, done, failed)

    def _open_spotify_container(
        self,
        intent: OpenSpotifyContainer,
        *,
        attempt: int = 0,
    ) -> None:
        """Open an album, playlist, podcast or artist section read-only."""

        client = self.client
        if client is None:
            self.announcer.say("Silnik nie jest gotowy")
            return
        self._spotify_navigation_version += 1
        version = self._spotify_navigation_version

        def work():
            return spotify_container_result_from_payload(
                client.spotify_container_items(
                    external_id=intent.service_id,
                    title=intent.title,
                    kind=intent.kind,
                    artist=intent.artist,
                    artist_section=intent.section,
                )
            )

        def done(result) -> None:
            if (
                version != self._spotify_navigation_version
                or self.navigator.active is not SessionId.SPOTIFY
            ):
                return
            # Brak zawartosci udostepnionej przez Spotify nie jest pustym
            # kontenerem, do ktorego wolno wejsc.  Zostawiamy model, historie
            # nawigacji, zaznaczenie i fokus bez zmian; NVDA dostaje tylko
            # celowy komunikat hosta.  To odpowiada staremu AMC, ktore po
            # odmowie API rowniez pozostawalo na wybranej playliscie.
            if not result.available:
                self.announcer.say(
                    result.warning
                    or "Spotify nie udostępnił zawartości tego elementu."
                )
                return
            self._run(self.navigator.apply_spotify_container(
                intent,
                result.heading,
                list(result.rows),
            ))
            if result.warning:
                self.announcer.say(result.warning)
            if result.has_more:
                self.announcer.say(
                    "Spotify ma więcej wyników; dalsze strony nie są jeszcze dostępne"
                )

        def failed(error: Exception) -> None:
            if (
                version != self._spotify_navigation_version
                or self.navigator.active is not SessionId.SPOTIFY
            ):
                return
            if LiteFrame._retry_busy_spotify_navigation(
                self,
                error,
                version=version,
                attempt=attempt,
                retry=lambda: self._open_spotify_container(
                    intent,
                    attempt=attempt + 1,
                ),
            ):
                return
            self.announcer.say(
                str(error)
                if isinstance(error, (HostError, SpotifyContainerPayloadError))
                else "Nie udało się otworzyć zawartości Spotify"
            )

        self.runner.submit("spotify-navigation", work, done, failed)

    def _retry_busy_spotify_navigation(
        self,
        error: Exception,
        *,
        version: int,
        attempt: int,
        retry: Callable[[], None],
    ) -> bool:
        """Retain one Enter while a shared long-operation slot is busy.

        The host deliberately rejects excess concurrent network reads instead
        of building an unbounded queue.  A deliberate Spotify activation must
        nevertheless survive a short collision with another provider read.
        The navigation version makes the retry safe: a later Enter, Back or
        session switch wins and the older callback becomes a no-op.
        """

        if not (
            isinstance(error, HostError)
            and error.code == "operation_busy"
            and attempt < 20
        ):
            return False

        def run_retry() -> None:
            if (
                version == self._spotify_navigation_version
                and self.navigator.active is SessionId.SPOTIFY
            ):
                retry()

        call_later = getattr(wx, "CallLater", None)
        if callable(call_later):
            call_later(250, run_retry)
        else:
            run_retry()
        return True

    def _show_spotify_relations(self, intent: ShowSpotifyRelations) -> None:
        """Show only real Spotify destinations in an accessible list."""

        if not intent.choices:
            return
        if len(intent.choices) == 1:
            self._run(self.navigator.activate_spotify_relation(intent.choices[0]))
            return
        active_list = self._active_list()
        dialog = RelationDestinationDialog(
            self,
            title=intent.title,
            labels=tuple(choice.label for choice in intent.choices),
        )
        selected: int | None = None
        try:
            if dialog.ShowModal() == wx.ID_OK:
                selected = dialog.selected_index
        finally:
            dialog.Destroy()
            wx.CallAfter(active_list.SetFocus)
        if selected is not None:
            self._run(self.navigator.activate_spotify_relation(intent.choices[selected]))

    def _play_spotify(self, intent: PlaySpotifyItem) -> None:
        """Hand one safe catalogue identity to the native Librespot engine."""

        client = self.client
        if client is None:
            self.navigator.restore_spotify_playback_after_failed_handoff(
                intent.previous_item_id,
                intent.previous_title,
            )
            self.announcer.say("Silnik nie działa, nie mogę odtworzyć Spotify")
            return
        self._pending_spotify_playback = intent
        self._pending_playback_session = SessionId.SPOTIFY

        def done(_payload: dict) -> None:
            # Przyjęcie polecenia nie znaczy jeszcze, że słychać dźwięk.
            # Stan zatwierdzi dopiero zdarzenie playback.started.
            self._refresh_status()

        def failed(error: Exception) -> None:
            if self._pending_spotify_playback is intent:
                self._pending_spotify_playback = None
                self._pending_playback_session = None
                self.navigator.restore_spotify_playback_after_failed_handoff(
                    intent.previous_item_id,
                    intent.previous_title,
                )
            self.announcer.say(f"Nie udało się odtworzyć Spotify: {error}")

        self.runner.submit(
            "playback",
            lambda: client.spotify_play(
                item_id=intent.item_id,
                title=intent.title,
                external_id=intent.service_id,
                kind=intent.kind,
                volume=self.options.volume,
            ),
            done,
            failed,
        )

    def _record_spotify_history(self, row: Row) -> None:
        """Persist one playback only after Librespot confirmed its start."""

        previous = list(self.state.spotify_playback_history)
        updated = record_spotify_history_row(previous, row)
        if updated == previous:
            return
        self.state.spotify_playback_history = updated
        if self._save_state() is False:
            self.state.spotify_playback_history = previous

    def _open_library_view(
        self,
        intent: OpenLibraryView,
        *,
        restore_selected_ids: list[str] | None = None,
        after_refresh: Callable[[], None] | None = None,
    ) -> None:
        """Wczytanie nazwanego widoku Biblioteki -- tak samo POZA watkiem GUI.

        "Wszystkie pliki" to kilka tysiecy wierszy plus klucze kolacji z hosta,
        wiec odczyt w watku GUI zamrozilby okno w trakcie czytania listy.
        """
        if intent.target_session_id is SessionId.RADIO:
            self._open_radio_view(intent)
            return
        if not self.library.is_available:
            # Niedostepne D: w kopii profilu NIE znaczy pustej Biblioteki --
            # to brak samej bazy, i tak to nazywamy.
            self.announcer.say(self.library.describe() or "Biblioteka niedostepna")
            return

        view = intent.view
        key = self._VIEW_KEYS[view]
        playlist_id = intent.playlist_id
        item_id = intent.item_id
        # Kontekst biezacego materialu CZYTAMY TERAZ, w watku GUI, i wysylamy
        # do watku roboczego jako wartosci. Zajrzenie do nawigatora z tamtej
        # strony scigaloby sie ze zmiana sesji w trakcie odczytu.
        current_session_id = intent.current_session_id
        current_item_id = intent.current_item_id

        def work():
            return self.library.load_view(
                key,
                playlist_id=playlist_id,
                item_id=item_id,
                current_session_id=current_session_id,
                current_item_id=current_item_id,
            )

        def done(result) -> None:
            if result.fallback_view is not None:
                self._run(self.navigator.apply_library_view(
                    view, result.heading, [], fallback_to_playlists=True))
                if after_refresh is not None:
                    after_refresh()
                return
            # ``sees_live_writes`` dotyczy calego odczytu, nie jednego widoku,
            # wiec mowimy o nim ta sama droga co w Folderach.
            if not result.sees_live_writes:
                self.announcer.say("Uwaga: zamrozona migawka profilu.")
            self._run(self.navigator.apply_library_view(
                view,
                result.heading,
                result.rows,
                preferred_id=intent.preferred_id,
                playlist_id=playlist_id,
                order_matches_amc=result.order_matches_amc,
                item_id=item_id,
                bookmark_targets=result.bookmark_targets,
                bookmark_contexts=result.bookmark_contexts,
                queue_flags=result.queue_flags,
            ))
            if (
                restore_selected_ids
                and self.navigator.active is SessionId.FILES
                and self.navigator.session.view is View.LIST
                and self.navigator.session.library_view is LibraryView.PLAYLIST_CONTENTS
                and self.navigator.session.library_playlist_id == playlist_id
            ):
                self._active_list().select_item_ids(restore_selected_ids)
            if after_refresh is not None:
                after_refresh()

        def failed(error: Exception) -> None:
            if after_refresh is not None:
                after_refresh()
            self.announcer.say(f"Nie moge wczytac widoku: {error}")

        self.runner.submit("folder", work, done, failed)

    # ------------------------------------------------------------- klawisze

    @staticmethod
    def _screen_reader_modifier_down() -> bool:
        """Czy fizycznie trzymany jest klawisz modyfikujący NVDA.

        wx nie pokazuje Insertu ani Caps Locka jako modyfikatora zdarzenia,
        więc ``chord_from_event`` widzi np. NVDA+End jak zwykły End. Stare AMC
        rozwiązywało to przez sprawdzenie stanu klawisza w Win32. Zachowujemy
        ten sam, wąski kontrakt: Insert, NumPad Insert/0 albo Caps Lock.
        """
        if os.name != "nt":
            return False
        try:
            import ctypes

            get_async_key_state = ctypes.windll.user32.GetAsyncKeyState
            return any(
                int(get_async_key_state(virtual_key)) & 0x8000
                for virtual_key in (0x2D, 0x60, 0x14)
            )
        except (AttributeError, OSError):
            return False

    def _on_player_shortcut_hook(self, event: wx.KeyEvent) -> None:
        # Pomoc klawiatury musi być pierwszą bramką. W przeciwnym razie
        # pole filtra albo natywna lista wykonałyby opisywany skrót, zanim
        # AMC zdążyłby go tylko nazwać.
        keyboard_help_handler = getattr(self, "_handle_keyboard_help_event", None)
        if keyboard_help_handler is not None and keyboard_help_handler(event):
            return

        # POLE FILTRA JEST SZCZELNE. ``EVT_CHAR_HOOK`` widzi klawisze przed
        # kontrolka, wiec bez tej bramki Enter i Backspace z pola wpadaly do
        # globalnej nawigacji: zmierzone na zywym GUI (Enter otwieral folder,
        # Backspace wynosil o poziom wyzej) zamiast dojsc do
        # ``_on_filter_key``. Odpowiednik ``if (Keyboard.FocusedElement is
        # TextBox)`` z oryginalu (MainWindow.xaml.cs:21000): gdy fokus jest w
        # polu, klawisze naleza WYLACZNIE do pola i jego wlasnej obslugi.
        if wx.Window.FindFocus() is self.filter_box:
            self._on_filter_key(event)
            return

        focus = wx.Window.FindFocus()
        if focus is None or wx.GetTopLevelParent(focus) is not self:
            event.Skip()
            return

        # NVDA+Up czyta fokus, NVDA+End pasek stanu, a NVDA+Down porusza się
        # po obiektach. wx nie raportuje Insertu/Caps Locka w modyfikatorach,
        # więc bez osobnego sprawdzenia odtwarzacz zmieniał głośność albo
        # przewijał utwór. Przepuszczamy gest również przed kontrolkami
        # głośności i tempa; ich natywna obsługa też nie może go przejąć.
        canonical = chord_from_event(event).canonical
        screen_reader_modifier_down = getattr(
            self,
            "_screen_reader_modifier_down",
            lambda: False,
        )
        if (
            self.navigator.view is View.PLAYER
            and canonical in {"Up", "Down", "End"}
            and screen_reader_modifier_down()
        ):
            event.Skip()
            return

        # Windowsowa kontrolka listy potrafi przejac F2 (wlasna edycja
        # etykiety) oraz Delete, zanim dotra do EVT_KEY_DOWN kontrolki. Te
        # cztery gesty sa poleceniami AMC, wiec przechwytujemy je juz na
        # poziomie okna. Reszte klawiszy listy nadal dostaje natywna kontrolka
        # -- szczegolnie strzalki, Home/End i wyszukiwanie przyrostowe NVDA.
        if self.navigator.view is not View.PLAYER:
            # Ctrl+Shift+0 wymaga tej wczesnej drogi tak samo jak w starym
            # AMC; pozostawienie go kontrolce listy daje cisze i brak akcji.
            # SysListView32 używa gołej Spacji do własnego zaznaczania i na
            # Windows potrafi połknąć ją przed EVT_KEY_DOWN. W Sonos Spacja
            # jest sterowaniem aktywną grupą również podczas przeglądania
            # Biblioteki. Ctrl+Spacja nadal należy do wielokrotnego zaznaczenia.
            if (
                getattr(getattr(self.navigator, "active", None), "value", "")
                == "sonos"
                and canonical == "Space"
            ):
                self._on_key(event)
                return
            if (
                getattr(getattr(self.navigator, "active", None), "value", "")
                == "radio"
                and getattr(
                    getattr(
                        getattr(self.navigator, "session", None),
                        "library_view",
                        None,
                    ),
                    "value",
                    "",
                )
                == "activeRadioRecordings"
                and canonical in ("B", "Shift+B", "Ctrl+Shift+B")
            ):
                self._on_key(event)
                return
            if canonical in {
                "F2",
                "Shift+F2",
                "Delete",
                "Shift+Delete",
                # Jawne polecenia AMC. Zwykła lista Windows potrafi połknąć
                # kombinacje literowe jako wyszukiwanie przyrostowe, zanim
                # dotrą do EVT_KEY_DOWN kontrolki. Przechwytujemy wyłącznie
                # gesty z modyfikatorami; gołe litery nadal należą do listy.
                "Ctrl+Shift+U",
                "Ctrl+Shift+P",
                "Ctrl+Shift+L",
                "Ctrl+Shift+Q",
                "Ctrl+Shift+Return",
                "Ctrl+Shift+H",
                "Ctrl+R",
                "Shift+R",
                "Ctrl+Alt+S",
                "Ctrl+Alt+Shift+S",
                "Ctrl+,",
                "Ctrl+F1",
                # To jest NAJWCZEŚNIEJSZA bramka wx: CHAR_HOOK głównego okna
                # przychodzi przed zdarzeniem listy. Zatrzymuje natywne
                # wykonanie gestu; nie zatrzymuje globalnego komunikatu
                # schowka skonfigurowanego w zewnętrznym dodatku NVDA.
                "Ctrl+C",
                "Ctrl+Shift+C",
                "Ctrl+X",
                "Ctrl+V",
                # Wspólne podglądy muszą dotrzeć do resolvera także z
                # natywnej listy. Sama obecność w shortcuts.py nie wystarcza:
                # SysListView32 potrafi wcześniej potraktować literę jako
                # własne polecenie i nie wysłać EVT_KEY_DOWN do AMC.
                "Ctrl+I",
                "Alt+D",
                "Alt+R",
                "Alt+Shift+R",
                "Alt+Up",
                "Alt+Down",
            } | set(GLOBAL_VIEW_SHORTCUTS) | set(PRESET_SHORTCUTS):
                self._on_key(event)
                return
            event.Skip()
            return

        # Gdy fokus jest na regulacji, niemodyfikowane klawisze edycji należą
        # do niej: strzałki zmieniają wartość, a Home/End ustawiają skrajne
        # wartości. Wcześniej globalny router przejmował je także na polu
        # tempa, przez co obie kontrolki pozornie regulowały głośność.
        volume_slider = getattr(self, "volume_slider", None)
        rate_choice = getattr(self, "rate_choice", None)
        if focus is volume_slider and canonical in {
            "Left", "Right", "Up", "Down", "Home", "End", "Prior", "Next",
        }:
            current = int(volume_slider.GetValue())
            value = {
                "Left": current - 1,
                "Down": current - 1,
                "Right": current + 1,
                "Up": current + 1,
                "Prior": current + 10,
                "Next": current - 10,
                "Home": 0,
                "End": 100,
            }[canonical]
            self._set_volume(value)
            return
        if focus is rate_choice and canonical in {
            "Left", "Right", "Up", "Down", "Home", "End", "Prior", "Next",
        }:
            event.Skip()
            return

        # Native dialog processing on a button consumes player keys before
        # KEY_DOWN. The existing resolver passes unknown keys (e.g. Tab) on.
        self._on_key(event)

    def _on_key(self, event: wx.KeyEvent) -> None:
        keyboard_help_handler = getattr(self, "_handle_keyboard_help_event", None)
        if keyboard_help_handler is not None and keyboard_help_handler(event):
            return
        chord = chord_from_event(event)
        player = self.navigator.view is View.PLAYER
        if (
            player
            and chord.canonical in {"Up", "Down", "End"}
            and self._screen_reader_modifier_down()
        ):
            event.Skip()
            return
        radio = self.navigator.active is SessionId.RADIO
        podcast_inbox = (
            not player
            and self.navigator.active is SessionId.PODCASTS
            and self.navigator.session.library_view is LibraryView.PODCAST_INBOX
        )
        tidal_collection = (
            not player
            and self.navigator.active is SessionId.TIDAL
            and self.navigator.session.library_view in (
                LibraryView.TIDAL_LIBRARY,
                LibraryView.TIDAL_FAVORITES,
                LibraryView.TIDAL_PLAYLISTS,
            )
        )
        spotify_collection = (
            not player
            and self.navigator.active is SessionId.SPOTIFY
            and isinstance(
                self.navigator.session.spotify_context,
                OpenSpotifyCollectionView,
            )
        )
        # WPF czyści aktywny filtr także wtedy, gdy fokus jest już na wynikach.
        if not player and chord.canonical == "Escape" and self.filter_box.GetValue():
            self._clear_filter_and_return()
            return
        if (
            not player
            and self.navigator.active is SessionId.TIDAL
            and chord.canonical == "Ctrl+Return"
        ):
            self._run(self.navigator.play_selected_tidal_container())
            return
        if (
            not player
            and self.navigator.active is SessionId.TIDAL
            and chord.canonical == "Right"
        ):
            self._run(self.navigator.tidal_relations())
            return
        # Pelne AMC przechwytuje Page Up/Page Down w sesji TIDAL takze na
        # liscie, bo zewnetrzny TIDAL nie ma widoku odtwarzacza AMC. Bez tej
        # galezi klawisze przewijalyby tylko strone listy i transport bylby
        # dostepny dopiero po otwarciu sztucznego, mylacego odtwarzacza.
        if (
            not player
            and self.navigator.active is SessionId.TIDAL
            and self._tidal_desktop_has_playback
            and chord.canonical in (
                "Prior", "Next", "Shift+Prior", "Shift+Next"
            )
        ):
            forward = chord.key == "Next"
            if chord.shift:
                self._tidal_external_skip(forward)
            else:
                self._queue_step(forward)
            return
        if (
            chord.ctrl
            and not chord.alt
            and not chord.shift
            and chord.key in "123456789"
        ):
            action = session_order.action_for_slot(
                int(chord.key), self.options.session_order
            )
            if action is not None:
                self._dispatch(action)
                return
        action = resolve(
            chord,
            player_view=player,
            radio_session=radio,
            radio_recording_context=(
                radio
                and not player
                and self.navigator.session.library_view
                is LibraryView.ACTIVE_RADIO_RECORDINGS
            ),
            podcast_inbox=podcast_inbox,
            podcast_session=self.navigator.active is SessionId.PODCASTS,
            tidal_session=self.navigator.active is SessionId.TIDAL,
            tidal_collection=tidal_collection,
            spotify_session=self.navigator.active is SessionId.SPOTIFY,
            spotify_collection=spotify_collection,
            wiim_session=self.navigator.active is SessionId.WIIM,
            wiim_streams=(
                not player
                and self.navigator.active is SessionId.WIIM
                and self.navigator.session.library_view
                is LibraryView.WIIM_NETWORK_STREAMS
            ),
            sonos_session=self.navigator.active is SessionId.SONOS,
            sonos_own_streams=(
                not player
                and self.navigator.active is SessionId.SONOS
                and self.navigator.session.library_view
                is LibraryView.SONOS_OWN_STREAMS
            ),
        )
        if action is None:
            # Klawisz NIE jest nasz: oddajemy go kontrolce, zeby natywna
            # nawigacja i czytnik ekranu dzialaly bez zmian.
            event.Skip()
            return
        self._dispatch(action)

    def _dispatch(self, action: Action) -> None:
        if (
            action in TRANSIENT_PREVIEW_ACTIONS
            and not is_transient_preview_available(
                action,
                self.navigator.active,
                global_previews=getattr(self, "_global_transient_previews", True),
            )
        ):
            self.announcer.say(transient_preview_unavailable_message(action))
            return
        if (
            self.navigator.active is SessionId.PODCASTS
            and action in {
                Action.VIEW_ALL_FILES,
                Action.VIEW_FOLDERS,
                Action.VIEW_ITEM_BOOKMARKS,
                Action.VIEW_ALL_BOOKMARKS,
                Action.OPEN_FOLDER_DIALOG,
                Action.OPEN_FILE_DIALOG,
            }
        ):
            self.announcer.say(
                "To polecenie dotyczy Biblioteki plików. "
                "Do podcastów wrócisz skrótem Ctrl+L"
            )
            return
        if self.navigator.active is SessionId.TIDAL:
            if action is Action.SHOW_PLAYER:
                self.announcer.say(
                    "TIDAL odtwarza w oryginalnej aplikacji i nie ma "
                    "odtwarzacza AMC"
                )
                return
            if action not in TIDAL_SUPPORTED_ACTIONS:
                self.announcer.say(
                    "Ta funkcja nie dotyczy odtwarzania w oryginalnym TIDALu"
                )
                return
        if self.navigator.active is SessionId.SPOTIFY:
            spotify_history_removal = (
                action is Action.REMOVE_SELECTED
                and self.navigator.session.library_view
                is LibraryView.SPOTIFY_HISTORY
            )
            if (
                action not in SPOTIFY_SUPPORTED_ACTIONS
                and not spotify_history_removal
            ):
                self.announcer.say(
                    "Ta funkcja nie jest jeszcze dostępna w sesji Spotify"
                )
                return
        if self.navigator.active is SessionId.WIIM:
            if action not in WIIM_SUPPORTED_ACTIONS:
                self.announcer.say(
                    "To polecenie nie jest dostępne w sesji WiiM"
                )
                return
        if self.navigator.active is SessionId.SONOS:
            if action not in SONOS_SUPPORTED_ACTIONS:
                self.announcer.say(
                    "To polecenie nie jest dostępne w sesji Sonos"
                )
                return
        if action is Action.SESSION_FILES:
            self._transient_preview_return = None
            self._switch_session(SessionId.FILES)
        elif action is Action.SESSION_RADIO:
            self._transient_preview_return = None
            self._switch_session(SessionId.RADIO)
        elif action is Action.SESSION_PODCASTS:
            self._transient_preview_return = None
            self._switch_session(SessionId.PODCASTS)
        elif action is Action.SESSION_TIDAL:
            self._transient_preview_return = None
            self._switch_session(SessionId.TIDAL)
        elif action is Action.SESSION_SPOTIFY:
            self._transient_preview_return = None
            self._switch_session(SessionId.SPOTIFY)
        elif action is Action.SESSION_WIIM:
            self._transient_preview_return = None
            self._switch_session(SessionId.WIIM)
        elif action is Action.SESSION_SONOS:
            self._transient_preview_return = None
            self._switch_session(SessionId.SONOS)
        elif action is Action.SESSION_LIST:
            self._show_session_list()
        elif action in (Action.PREVIOUS_SESSION, Action.NEXT_SESSION):
            target = session_order.adjacent(
                self.navigator.active,
                -1 if action is Action.PREVIOUS_SESSION else 1,
                self.options.session_order,
            )
            self._transient_preview_return = None
            self._switch_session(target)
        elif action is Action.COMMAND_PALETTE:
            self._show_command_palette()
        elif action is Action.SELECT_SONOS_TARGET:
            self._load_sonos_targets(
                preferred_id=self.navigator.sessions[SessionId.SONOS].list_anchor_id
            )
        elif action is Action.ACTIVATE:
            self._activate_selected_if_ready()
        elif action is Action.PARENT_FOLDER:
            if not LiteFrame._restore_transient_preview(self, announce=False):
                self._run(self.navigator.go_to_parent())
        elif action is Action.CLOSE_LIST_PREVIEW:
            # Escape nie jest drugim Backspace. Nadal zamyka chwilowe
            # podglady (nagrywane, historia nagran, harmonogramy, nowe
            # odcinki) i zagniezdzone widoki, ale NIE przenosi z otwartego
            # folderu Biblioteki do jego rodzica. Natywna lista odzyskuje
            # fokus bez dopowiadania "Powrot, ... lista".
            if LiteFrame._restore_transient_preview(self, announce=False):
                return
            state = self.navigator.session
            if (
                self.navigator.active is SessionId.FILES
                and state.library_view is None
            ):
                return
            self._run(self.navigator.go_to_parent())
        elif action is Action.SHOW_PLAYER:
            # F6 w odtwarzaczu TEZ wraca na liste (navigator.show_player), wiec
            # musi przejsc przez polityke pauzy tak samo jak Escape.
            if self.navigator.session.view is View.PLAYER:
                self._leave_player_to_list()
            else:
                self._run(self.navigator.show_player())
        elif action is Action.SHOW_LIST:
            self._leave_player_to_list()
        elif action is Action.SESSION_OPTIONS:
            self._show_session_options()
        elif action is Action.SELECT_AUDIO_OUTPUT:
            self._choose_audio_output()
        elif action is Action.PREVIOUS_AUDIO_OUTPUT:
            self._cycle_audio_output(-1)
        elif action is Action.NEXT_AUDIO_OUTPUT:
            self._cycle_audio_output(1)
        elif action is Action.GENERAL_SETTINGS:
            self._show_general_playback_options()
        elif action is Action.VIEW_PRESETS:
            self._show_presets()
        elif action is Action.VIEW_WIIM_NETWORK_STREAMS:
            self._show_wiim_network_streams()
        elif action in {
            Action.WIIM_SELECT_INPUT,
            Action.WIIM_SELECT_OUTPUT,
            Action.WIIM_SELECT_EQUALIZER,
            Action.WIIM_SELECT_REPEAT,
            Action.WIIM_SET_SLEEP_TIMER,
        }:
            self._show_wiim_option(action)
        elif action is Action.WIIM_TOGGLE_SHUFFLE:
            self._toggle_wiim_shuffle()
        elif action is Action.WIIM_PREVIOUS_SOURCE:
            self._navigate_wiim_source(-1)
        elif action is Action.WIIM_NEXT_SOURCE:
            self._navigate_wiim_source(1)
        elif action is Action.ADD_WIIM_NETWORK_STREAM:
            self._add_wiim_network_stream()
        elif action is Action.EDIT_WIIM_NETWORK_STREAM:
            self._edit_wiim_network_stream()
        elif action is Action.REMOVE_WIIM_NETWORK_STREAMS:
            self._remove_wiim_network_streams()
        elif action is Action.IMPORT_WIIM_NETWORK_STREAMS:
            self._import_wiim_network_streams()
        elif action is Action.EXPORT_WIIM_NETWORK_STREAMS:
            self._export_wiim_network_streams()
        elif action in {
            Action.SORT_WIIM_NETWORK_STREAMS_ADDED,
            Action.SORT_WIIM_NETWORK_STREAMS_ALPHABETICAL,
            Action.SORT_WIIM_NETWORK_STREAMS_CUSTOM,
        }:
            self._set_wiim_network_stream_sort(action)
        elif action is Action.ADD_SONOS_OWN_STREAM:
            self._add_sonos_own_stream()
        elif action is Action.EDIT_SONOS_OWN_STREAM:
            self._edit_sonos_own_stream()
        elif action is Action.REMOVE_SONOS_OWN_STREAMS:
            self._remove_sonos_own_streams()
        elif action is Action.IMPORT_SONOS_OWN_STREAMS:
            self._import_sonos_own_streams()
        elif action in {
            Action.SORT_SONOS_OWN_STREAMS_ADDED,
            Action.SORT_SONOS_OWN_STREAMS_ALPHABETICAL,
            Action.SORT_SONOS_OWN_STREAMS_CUSTOM,
        }:
            self._set_sonos_own_stream_sort(action)
        elif action is Action.MOVE_SONOS_OWN_STREAM_UP:
            self._move_sonos_own_streams(-1)
        elif action is Action.MOVE_SONOS_OWN_STREAM_DOWN:
            self._move_sonos_own_streams(1)
        elif action is Action.CUT_SONOS_OWN_STREAMS:
            self._cut_sonos_own_streams()
        elif action is Action.PASTE_SONOS_OWN_STREAMS:
            self._paste_sonos_own_streams()
        elif action is Action.EXPORT_SONOS_OWN_STREAMS:
            self._export_sonos_own_streams()
        elif action is Action.ASSIGN_PRESET:
            self._assign_preset()
        elif (slot := preset_slot(action)) is not None:
            self._activate_preset(slot)
        elif action is Action.PLAY_PAUSE:
            self._play_pause()
        elif action is Action.TOGGLE_MUTE:
            self._toggle_mute()
        elif action is Action.ADD_BOOKMARK:
            self._add_bookmark()
        elif action is Action.ADD_NAMED_BOOKMARK:
            self._add_bookmark(named=True)
        elif action in (Action.PREVIOUS_BOOKMARK, Action.NEXT_BOOKMARK):
            self._navigate_bookmark(action is Action.NEXT_BOOKMARK)
        elif action is Action.CLIP_MARK_START:
            self._mark_audio_clip(start=True)
        elif action is Action.CLIP_MARK_END:
            self._mark_audio_clip(start=False)
        elif action is Action.CLIP_JUMP_START:
            self._jump_to_audio_clip_boundary(end=False)
        elif action is Action.CLIP_JUMP_END:
            self._jump_to_audio_clip_boundary(end=True)
        elif action is Action.CLIP_PREVIOUS_BOUNDARY:
            self._jump_to_relative_audio_clip_boundary(direction=-1)
        elif action is Action.CLIP_NEXT_BOUNDARY:
            self._jump_to_relative_audio_clip_boundary(direction=1)
        elif action is Action.CLIP_EXPORT:
            self._export_audio_clip()
        elif action is Action.CLIP_APPEND:
            self._append_audio_clip()
        elif action is Action.CLIP_REMOVE:
            self._remove_audio_clip()
        elif action is Action.CLIP_CLEAR:
            self._clear_audio_clip_selection()
        elif action in (Action.QUEUE_NEXT, Action.QUEUE_PREVIOUS):
            self._queue_step(action is Action.QUEUE_NEXT)
        elif action in (Action.ADD_TO_QUEUE, Action.TOGGLE_PLAY_NEXT):
            self._toggle_queue_membership(action is Action.TOGGLE_PLAY_NEXT)
        elif action is Action.TOGGLE_FAVORITE:
            if self.navigator.active is SessionId.PODCASTS:
                self._toggle_podcast_favorite()
            elif self.navigator.active is SessionId.TIDAL:
                self._toggle_tidal_membership(favorite=True)
            else:
                self._toggle_profile_favorite()
        elif action is Action.MANAGE_PLAYLIST_MEMBERSHIP:
            self._manage_playlist_membership()
        elif action in (
            Action.TIDAL_TOGGLE_LIBRARY,
            Action.TIDAL_TOGGLE_FAVORITE,
        ):
            self._toggle_tidal_membership(
                favorite=action is Action.TIDAL_TOGGLE_FAVORITE
            )
        elif (step := seek_step_seconds(action, custom_seconds=self.messages.custom_seek_seconds)) is not None:
            # Krok czyta parytet transportu: 10 / 30 / 60 s i czas z ustawien
            # AMC (MainWindow.xaml.cs:21583-21590, 22387-22394). Wartosc
            # wlasna bierzemy z profilu, nie z twardej liczby.
            self._seek(float(step))
        elif (percent := seek_percent_value(action)) is not None:
            self._seek_percent(percent)
        elif action in (
            Action.VOLUME_UP_5, Action.VOLUME_DOWN_5,
            Action.VOLUME_UP_1, Action.VOLUME_DOWN_1,
        ):
            self._adjust_volume({
                Action.VOLUME_UP_5: 5, Action.VOLUME_DOWN_5: -5,
                Action.VOLUME_UP_1: 1, Action.VOLUME_DOWN_1: -1,
            }[action])
        elif action is Action.RATE_UP:
            # Drabina predkosci z oryginalu, nie plaskie +/- 0,1
            # (MainWindow.xaml.cs:16090-16115).
            self._set_rate(next_playback_rate(self.options.rate, +1))
        elif action is Action.RATE_DOWN:
            self._set_rate(next_playback_rate(self.options.rate, -1))
        elif action is Action.RATE_RESET:
            self._set_rate(1.0)
        elif action in (Action.TIME_ELAPSED, Action.TIME_REMAINING, Action.TIME_TOTAL):
            self._announce_time(action)
        elif action in (Action.TRACK_START, Action.TRACK_END):
            self._seek_to_track_edge(action is Action.TRACK_END)
        elif action is Action.TOGGLE_SEEK_MESSAGES:
            self._toggle_seek_messages()
        elif action is Action.OPEN_FOLDER_DIALOG:
            self._choose_folder()
        elif action is Action.OPEN_FILE_DIALOG:
            self._choose_file()
        elif action is Action.QUICK_INFORMATION:
            self._announce_quick_information()
        elif action is Action.SPOTIFY_RELATIONS:
            self._run(self.navigator.spotify_relations())
        elif action in {
            Action.SPOTIFY_VIEW_LIKED,
            Action.SPOTIFY_VIEW_ALBUMS,
            Action.SPOTIFY_VIEW_ARTISTS,
            Action.SPOTIFY_VIEW_PLAYLISTS,
            Action.SPOTIFY_VIEW_PODCASTS,
            Action.SPOTIFY_VIEW_EPISODES,
        }:
            view, title = {
                Action.SPOTIFY_VIEW_LIKED: ("liked", "Polubione utwory"),
                Action.SPOTIFY_VIEW_ALBUMS: ("albums", "Albumy"),
                Action.SPOTIFY_VIEW_ARTISTS: ("artists", "Wykonawcy"),
                Action.SPOTIFY_VIEW_PLAYLISTS: ("playlists", "Playlisty"),
                Action.SPOTIFY_VIEW_PODCASTS: ("podcasts", "Podcasty"),
                Action.SPOTIFY_VIEW_EPISODES: ("episodes", "Zapisane odcinki"),
            }[action]
            self._open_spotify_collection_view(OpenSpotifyCollectionView(
                f"spotify-collection:{view}",
                view,
                title,
            ))
        elif action is Action.COPY_NAME:
            self._copy_name()
        elif action is Action.COPY_ADDRESS:
            self._copy_address()
        elif action is Action.CUT_FILE:
            self._cut_or_start_internal_playlist_move()
        elif action is Action.PASTE_OR_MOVE:
            self._paste_internal_playlist_move()
        elif action is Action.MOVE_LIST_ITEM_UP:
            self._move_playlist_selection(-1)
        elif action is Action.MOVE_LIST_ITEM_DOWN:
            self._move_playlist_selection(1)
        elif action is Action.RENAME_LIBRARY_ITEM:
            self._rename_library_item()
        elif action is Action.RENAME_LOCAL_FILE:
            self._rename_local_file()
        elif action is Action.REMOVE_SELECTED:
            self._remove_selected_items()
        elif action is Action.RECYCLE_SELECTED:
            self._recycle_selected_files()
        elif action in (Action.SEARCH_CURRENT, Action.SEARCH_ALL):
            self._show_search(all_services=action is Action.SEARCH_ALL)
        elif action is Action.FOCUS_FILTER:
            self._focus_filter()
        elif action is Action.STATION_ADD:
            self._station_add()
        elif action is Action.STATION_EDIT:
            self._station_edit()
        elif action is Action.STATION_DELETE:
            self._station_delete()
        elif action is Action.STATION_IMPORT:
            self._station_import()
        elif action is Action.STATION_EXPORT_FAVORITES:
            self._station_export_favorites()
        elif action is Action.RECORD_TOGGLE:
            self._toggle_radio_recording()
        elif action is Action.RECORD_PAUSE:
            self._toggle_radio_recording_pause()
        elif action is Action.RECORD_SPLIT:
            self._split_radio_recording()
        elif action is Action.RECORD_STOP_ALL:
            self._stop_all_radio_recordings()
        elif action is Action.VIEW_ACTIVE_RECORDINGS:
            self._show_active_radio_recordings()
        elif action is Action.VIEW_RECORDED_RADIO_FILES:
            self._show_radio_recording_history()
        elif action is Action.ADD_RADIO_SCHEDULE:
            self._show_radio_schedules(create_for_selected=True)
        elif action is Action.MANAGE_RADIO_SCHEDULES:
            self._show_radio_schedules()
        elif action is Action.ADD_PODCAST_SOURCE:
            self._add_podcast_source()
        elif action is Action.IMPORT_PODCAST_OPML:
            self._import_podcast_opml()
        elif action is Action.EXPORT_PODCAST_OPML:
            self._export_podcast_opml()
        elif action is Action.EXPORT_YOUTUBE_SUBSCRIPTIONS:
            self._export_youtube_subscriptions()
        elif action is Action.VIEW_PODCAST_INBOX:
            self._show_podcast_inbox()
        elif action is Action.VIEW_PODCAST_DOWNLOADS:
            self._show_podcast_downloads()
        elif action in (
            Action.SORT_PODCAST_INBOX_ADDED,
            Action.SORT_PODCAST_INBOX_ALPHABETICAL,
            Action.SORT_PODCAST_INBOX_BY_PODCAST,
        ):
            self._set_podcast_inbox_sort(action)
        elif action in (
            Action.SORT_TIDAL_COLLECTION_ADDED,
            Action.SORT_TIDAL_COLLECTION_ALPHABETICAL,
            Action.SORT_TIDAL_COLLECTION_CUSTOM,
        ):
            self._set_tidal_collection_sort(action)
        elif action in (
            Action.SORT_SPOTIFY_COLLECTION_ADDED,
            Action.SORT_SPOTIFY_COLLECTION_ALPHABETICAL,
            Action.SORT_SPOTIFY_COLLECTION_CATALOG,
        ):
            self._set_spotify_collection_sort(action)
        elif action is Action.REFRESH_PODCAST:
            self._refresh_podcasts(refresh_all=False)
        elif action is Action.REFRESH_PODCAST_LIBRARY:
            self._refresh_podcasts(refresh_all=True)
        elif action is Action.DOWNLOAD_PODCAST_EPISODES:
            self._download_podcast_episodes()
        elif action is Action.SAVE_PODCAST_EPISODE_AS:
            self._save_podcast_episode_as()
        elif action is Action.SHOW_PODCAST_DESCRIPTION:
            self._show_podcast_description()
        elif action is Action.CURRENT_RADIO_BROADCAST_INFORMATION:
            self._announce_current_radio_broadcast_information()
        elif action is Action.RECOGNIZE_RADIO_TRACK:
            self._recognize_radio_track(automatic=False)
        elif action is Action.TOGGLE_RADIO_RECOGNITION_MONITORING:
            self._toggle_radio_recognition_monitoring()
        elif action is Action.TOGGLE_RADIO_RECOGNITION_ANNOUNCEMENTS:
            self._toggle_radio_recognition_announcements()
        elif action is Action.VIEW_RADIO_RECOGNITION_HISTORY:
            self._show_radio_recognition_history()
        elif action is Action.GO_TO_RELATED_PODCAST:
            self._go_to_related_podcast()
        elif action is Action.TOGGLE_PODCAST_FAVORITE:
            self._toggle_podcast_favorite()
        elif action is Action.TOGGLE_PODCAST_LIBRARY:
            self._toggle_podcast_library()
        elif action is Action.PODCAST_PLAYBACK_OPTIONS:
            self._show_podcast_playback_options()
        elif action is Action.VIEW_ALL_FILES:
            self._run(self.navigator.open_library_view(LibraryView.ALL_FILES))
        elif action is Action.VIEW_FAVORITES:
            if self.navigator.active is SessionId.PODCASTS:
                self._transient_preview_return = None
                self._open_podcast_aggregate(
                    OpenPodcastAggregateView(LibraryView.PODCAST_FAVORITES)
                )
            elif self.navigator.active is SessionId.TIDAL:
                self._open_tidal_view(OpenTidalView(LibraryView.TIDAL_FAVORITES))
            elif self.navigator.active is SessionId.SONOS:
                self._open_sonos_view(OpenSonosView(
                    LibraryView.SONOS_FAVORITES,
                    household_id=self._sonos_content_household_id(),
                ))
            else:
                self._run(self.navigator.open_library_view(LibraryView.FAVORITES))
        elif action is Action.VIEW_PLAYLISTS:
            if self.navigator.active is SessionId.PODCASTS:
                self._open_podcast_playlist_view(OpenPodcastPlaylistView())
            elif self.navigator.active is SessionId.TIDAL:
                self._open_tidal_view(OpenTidalView(LibraryView.TIDAL_PLAYLISTS))
            elif self.navigator.active is SessionId.SONOS:
                self._open_sonos_view(OpenSonosView(
                    LibraryView.SONOS_PLAYLISTS,
                    household_id=self._sonos_content_household_id(),
                ))
            else:
                self._run(self.navigator.open_library_view(LibraryView.PLAYLISTS))
        elif action is Action.VIEW_FOLDERS:
            # Foldery Biblioteki dzialaly juz z menu kontekstu startu; tutaj
            # dostaja jawne wejscie (Alt+1, jak MainWindow.xaml:446).
            self._open_library(self.library.saved_folder())
        elif action is Action.VIEW_LIBRARY:
            # Ctrl+L jest jawnym przejsciem, a nie zamknieciem podgladu.
            self._transient_preview_return = None
            if self.navigator.active is SessionId.WIIM:
                context = self._wiim_device_context()
                self._run(self.navigator.open_wiim_source_library(
                    device_id=context[1] if context else None,
                    return_id=context[0] if context else None,
                ))
            elif self.navigator.active is SessionId.SONOS:
                self._open_sonos_view(OpenSonosView(
                    LibraryView.SONOS_LIBRARY,
                    household_id=self._sonos_content_household_id(),
                ))
            elif self.navigator.active is SessionId.SPOTIFY:
                self._open_spotify_view(OpenSpotifyView(
                    preferred_id=self.navigator.sessions[
                        SessionId.SPOTIFY
                    ].library_return_id,
                ))
            else:
                self._return_to_library()
        elif action is Action.VIEW_HISTORY:
            self._show_playback_history_preview()
        elif action is Action.VIEW_SAVED_QUEUE:
            if self.navigator.active is SessionId.PODCASTS:
                self._transient_preview_return = None
                self._open_podcast_aggregate(
                    OpenPodcastAggregateView(LibraryView.PODCAST_QUEUE)
                )
            elif self.navigator.active is SessionId.TIDAL:
                self._open_tidal_queue()
            else:
                self._run(self.navigator.open_queue_view())
        elif action is Action.VIEW_ITEM_BOOKMARKS:
            self._run(self.navigator.open_item_bookmarks())
        elif action is Action.VIEW_ALL_BOOKMARKS:
            # Ctrl+B i pozycja menu wchodza TA SAMA droga: jedna akcja, jeden
            # dispatcher. Inaczej gest i menu mogly by sie rozjechac.
            self._run(self.navigator.open_all_bookmarks())
        elif action is Action.HELP:
            self._show_help()
        elif action is Action.KEYBOARD_HELP:
            self._toggle_keyboard_help()
        elif action is Action.VERSION_INFO:
            wx.MessageBox(
                window_title(),
                "Wersja programu",
                wx.OK | wx.ICON_INFORMATION,
                self,
            )
            self._restore_focus_after_dialog()

    # ---------------------------------------------------- wykonanie zamiarow

    def _run(self, intents: list[object]) -> None:
        """Wykonaj zamiary zwrocone przez Navigator. To JEDYNE miejsce, w
        ktorym logika nawigacji spotyka wx."""
        announcements_after_empty_update: list[str] = []
        for intent in intents:
            if isinstance(intent, Announce):
                # Pusta natywna lista nie ma wiersza do przeczytania. Najpierw
                # kończymy jej aktualizację, dopiero potem mówimy wynik. Dzięki
                # temu systemowy stan usuwanego dziecka nie dopisuje na końcu
                # słowa „nieznane”.
                if (
                    intent.text.strip().casefold() == "zero elementów"
                    and self.navigator.session.view is View.LIST
                    and self.navigator.session.model.selected_row is None
                ):
                    announcements_after_empty_update.append(intent.text)
                else:
                    self.announcer.say(intent.text)
            elif isinstance(intent, OpenFolder):
                # Gdy Biblioteka jest dostepna, wchodzenie w foldery czyta
                # SQLite, a nie dysk -- sciezki profilu moga tu nie istniec.
                if self.library.is_available:
                    self._open_library(intent.path or None, preferred_id=intent.preferred_id)
                else:
                    self._open_folder(intent.path, preferred_id=intent.preferred_id)
            elif isinstance(intent, OpenLibraryView):
                self._open_library_view(intent)
            elif isinstance(intent, OpenQueueView):
                self._open_queue_view()
            elif isinstance(intent, OpenPodcastView):
                self._open_podcast_view(intent)
            elif isinstance(intent, OpenPodcastAggregateView):
                self._open_podcast_aggregate(intent)
            elif isinstance(intent, OpenPodcastPlaylistView):
                self._open_podcast_playlist_view(intent)
            elif isinstance(intent, OpenSpotifyView):
                self._open_spotify_view(intent)
            elif isinstance(intent, OpenSpotifyCollectionView):
                self._open_spotify_collection_view(intent)
            elif isinstance(intent, OpenSpotifyContainer):
                self._open_spotify_container(intent)
            elif isinstance(intent, OpenTidalView):
                self._open_tidal_view(intent)
            elif isinstance(intent, OpenTidalContainer):
                self._open_tidal_container(intent)
            elif isinstance(intent, OpenSonosView):
                self._open_sonos_view(intent)
            elif isinstance(intent, ShowTidalRelations):
                self._show_tidal_relations(intent)
            elif isinstance(intent, ShowSpotifyRelations):
                self._show_spotify_relations(intent)
            elif isinstance(intent, PlayTrack):
                self._play_track(intent)
            elif isinstance(intent, PlayFromQueue):
                self._play_from_queue(intent)
            elif isinstance(intent, PlayQueueAt):
                self._play_queue_at(intent)
            elif isinstance(intent, PlayStation):
                self._play_station(intent)
            elif isinstance(intent, PlayMedia):
                self._play_media(intent)
            elif isinstance(intent, PlayTidalTrack):
                self._play_tidal_track(intent)
            elif isinstance(intent, PlayTidalContainer):
                self._play_tidal_container(intent)
            elif isinstance(intent, PlaySpotifyItem):
                self._play_spotify(intent)
            elif isinstance(intent, ActivateWiiMDevice):
                self._activate_wiim_device(intent)
            elif isinstance(intent, PlayWiiMNetworkStream):
                self._activate_wiim_network_stream(intent)
            elif isinstance(intent, OpenWiiMDevicePresets):
                self._show_wiim_presets()
            elif isinstance(intent, OpenWiiMNetworkStreams):
                self._show_wiim_network_streams()
            elif isinstance(intent, ActivateSonosGroup):
                self._activate_sonos_group(intent)
            elif isinstance(intent, PlaySonosMaterial):
                self._play_sonos_material(intent)
        self._sync_views()
        for text in announcements_after_empty_update:
            self._announce_after_native_list_update(text)

    def _sync_views(self) -> None:
        """Odwzoruj stan nawigatora. Fokus ruszamy TYLKO przy zmianie widoku."""
        session = self.navigator.session
        # Menu musi zgadzac sie z kontekstem, ktory wlasnie sie zmienil.
        if (
            hasattr(self, "_menu_items")
            and getattr(self, "_menu_session", self.navigator.active)
            is not self.navigator.active
        ):
            self._build_menu()
        else:
            self._refresh_menu_state()
        self.session_label.SetLabel({
            SessionId.FILES: "Pliki lokalne",
            SessionId.RADIO: "Radio internetowe",
            SessionId.PODCASTS: "Podcasty i YouTube",
            SessionId.TIDAL: "TIDAL",
            SessionId.SPOTIFY: "Spotify",
            SessionId.WIIM: "WiiM",
            SessionId.SONOS: "Sonos",
        }[self.navigator.active])

        active_list = self._active_list()
        # Jawna, użytkowa nazwa BIEŻĄCEGO widoku. Model nadal przechowuje enum,
        # lecz NVDA nigdy go nie zobaczy; pozycję i licznik czyta natywna lista.
        view_label = {
            LibraryView.ALL_FILES: "Wszystkie pliki",
            LibraryView.FAVORITES: "Ulubione",
            LibraryView.PLAYLISTS: "Playlisty",
            LibraryView.PLAYLIST_CONTENTS: "Playlista",
            LibraryView.HISTORY: "Historia odtwarzania",
            LibraryView.SAVED_QUEUE: "Zapisana kolejka",
            LibraryView.LIVE_QUEUE: "Kolejka odtwarzania",
            LibraryView.ITEM_BOOKMARKS: "Zakładki",
            LibraryView.ACTIVE_RADIO_RECORDINGS: "Nagrywane",
            LibraryView.RECORDED_RADIO_FILES: "Nagrane",
            LibraryView.RADIO_RECORDING_SCHEDULES: "Harmonogramy nagrywania",
            LibraryView.SONOS_LIBRARY: "Biblioteka Sonos",
            LibraryView.SONOS_FAVORITES: "Ulubione Sonos",
            LibraryView.SONOS_PLAYLISTS: "Playlisty Sonos",
            LibraryView.SONOS_OWN_STREAMS: "Moje stacje Sonos",
            LibraryView.SPOTIFY_LIBRARY: "Biblioteka Spotify",
            LibraryView.SPOTIFY_CONTAINER: session.spotify_heading,
            LibraryView.SPOTIFY_HISTORY: "Spotify — Historia odtwarzania",
        }.get(
            session.library_view,
            getattr(active_list, "_base_accessible_label", None),
        )
        if view_label is not None:
            set_accessible_label = getattr(active_list, "set_accessible_label", None)
            if callable(set_accessible_label):
                set_accessible_label(view_label)
        all_lists = tuple(
            candidate for candidate in (
                getattr(self, "files_list", None),
                getattr(self, "radio_list", None),
                getattr(self, "podcasts_list", None),
                getattr(self, "tidal_list", None),
                getattr(self, "spotify_list", None),
                getattr(self, "wiim_list", None),
                getattr(self, "sonos_list", None),
            )
            if candidate is not None
        )
        other_lists = tuple(control for control in all_lists if control is not active_list)
        # FILTR TEGO WIDOKU przywracamy PRZED ``sync_rows``, bo on wlasnie
        # liczy stan zadany listy. Port ``RestoreFilterForCurrentView``
        # (MainWindow.xaml.cs:10196-10204): wejscie w widok oddaje jego wlasny
        # tekst filtra, a nie tekst widoku, z ktorego przyszlismy.
        self._restore_filter_for_current_view()
        # JEDNA droga odswiezenia dla WSZYSTKICH widokow, bez wymiany kontrolki.
        # ``sync_rows`` sam decyduje, czy jest co robic: gdy dane, kolejnosc,
        # teksty i kursor sa te same, nie wykonuje ZADNEJ operacji na liscie.
        # Dlatego wolanie go na koncu kazdego ``_run`` (takze po samym
        # komunikacie czy Ctrl+C) nie odswieza juz listy bez potrzeby.
        #
        # Rekreacja kontrolki (nowy HWND dla czystego cache czytnika) byla tu
        # przez chwile i ZOSTALA WYCOFANA PO POMIARZE. Usuwala wprawdzie stara
        # nazwe z nowym licznikiem, ale na glownym widoku (2476 wierszy)
        # czytnik przestawal mowic wybrany wiersz w ogole -- slychac bylo tylko
        # naglowek widoku. Kwity: ``przed-po-przed.json`` (stary kod, wiersz
        # czytany) vs ``przed-po-po.json`` (z rekreacja, cisza) oraz para
        # ``odbior-listy-Z-REKREACJA.json`` / ``odbior-listy-BEZ-REKREACJI.json``.
        # Siedem prob ratowania rekreacji (kolejnosc fokus/wypelnienie, obrot
        # petli, podwojny ``SetFocus``, wymuszony ``SetItemState``, kolejnosc
        # ``Destroy``, zdjecie nakladki) nie przywrocilo tego odczytu.
        # Problem "stara nazwa z nowym licznikiem" rozwiazuje teraz sama zmiana
        # na zwykla liste: tekst siedzi w kontrolce, a nie w cache wirtualnym,
        # wiec stara nazwa nie ma skad wrocic.
        # Po powrocie z Total Commandera/Explorera shell mogl juz wykonac
        # przeniesienie przygotowane przez Ctrl+X. Baza pelnego AMC jest dla
        # tego interfejsu tylko do odczytu, wiec filtr procesu zapobiega
        # ponownemu pokazaniu wiersza do czasu nastepnego uruchomienia/skanu.
        self._hide_completed_external_moves_from_files_model()
        active_list.sync_rows()

        want_player = session.view is View.PLAYER
        changed = self.player_panel.IsShown() != want_player or any(
            control.IsShown() for control in other_lists
        )

        self.list_panel.Show(not want_player)
        self.player_panel.Show(want_player)
        active_list.Show(not want_player)
        for control in other_lists:
            control.Hide()
        self.panel.Layout()

        # Dzwiek TIDALa nie przechodzi przez AMC. Pozostawienie aktywnych
        # suwakow glosnosci i tempa zmienialoby ukryty lokalny silnik, choc
        # uzytkownik jest w odtwarzaczu TIDAL. Przycisk gra/pauza pozostaje
        # aktywny, bo jest jawnie kierowany do sesji systemowej TIDALa.
        tidal_external = self.navigator.active is SessionId.TIDAL
        spotify_read_only = self.navigator.active is SessionId.SPOTIFY
        wiim_remote = self.navigator.active is SessionId.WIIM
        sonos_remote = self.navigator.active is SessionId.SONOS
        wiim_ready = (
            not wiim_remote
            or bool(self._wiim_snapshot)
            and self._wiim_snapshot.get("deviceId")
            == self._wiim_active_device_id
        )
        sonos_ready = (
            not sonos_remote
            or bool(self._sonos_snapshot)
            and self._sonos_snapshot.get("groupId")
            == self._sonos_active_group_id
        )
        sonos_volume = (
            sonos_ready
            and self._sonos_snapshot.get("fixedVolume") is not True
            and self._sonos_snapshot.get("volume") is not None
        )
        self.volume_slider.Enable(
            not (tidal_external or spotify_read_only) and wiim_ready
            and (not sonos_remote or sonos_volume)
        )
        self.rate_choice.Enable(not (
            tidal_external or spotify_read_only or wiim_remote or sonos_remote
        ))

        if want_player:
            if wiim_remote and self._wiim_snapshot:
                self._apply_wiim_snapshot(self._wiim_snapshot, announce=False)
            elif sonos_remote and self._sonos_snapshot:
                self._apply_sonos_snapshot(self._sonos_snapshot, announce=False)
            else:
                self.now_playing.SetLabel(
                    session.now_playing_title or "Nic nie jest odtwarzane"
                )
            if self.navigator.active is SessionId.RADIO:
                # F6 najpierw oglasza wejscie do odtwarzacza. Natychmiast potem
                # przywracamy z ostatniej migawki wlasciwa tresc NVDA+End.
                self._update_native_playback_status(self._last_status)
            if changed:
                self.play_button.SetFocus()
        elif changed:
            active_list.SetFocus()

    def _active_list(self) -> MediaListCtrl:
        # Galazie zamiast slownika: testy logiki buduja lekkie okno tylko z
        # kontrolkami sesji, ktora sprawdzaja. Slownik obliczalby wszystkie
        # wartosci z gory i pytal o ``podcasts_list`` nawet przy sesji Plikow.
        if self.navigator.active is SessionId.FILES:
            return self.files_list
        if self.navigator.active is SessionId.RADIO:
            return self.radio_list
        if self.navigator.active is SessionId.PODCASTS:
            return self.podcasts_list
        if self.navigator.active is SessionId.SPOTIFY:
            return self.spotify_list
        if self.navigator.active is SessionId.WIIM:
            return self.wiim_list
        if self.navigator.active is SessionId.SONOS:
            return self.sonos_list
        return self.tidal_list

    def _on_item_focused(self, event: wx.ListEvent) -> None:
        """Fokus jest kotwica akcji takze wtedy, gdy wiersz nie jest wybrany.

        To natywny etap windowsowego wyboru nieprzylegajacego:
        Ctrl+strzalka przesuwa fokus bez kasowania dotychczasowych zaznaczen,
        a Ctrl+Spacja przelacza dopiero ten wiersz. Model przechowuje jedno ID
        wlasnie jako kotwice nawigacji; pelny zbior zaznaczen nadal pozostaje
        w SysListView32 i nie jest tu kopiowany ani emulowany.
        """
        control = event.GetEventObject()
        if not isinstance(control, MediaListCtrl) or control.updating:
            event.Skip()
            return
        item_id = control.shown_item_id(event.GetIndex())
        if item_id is not None:
            self.navigator.session.model.select_id(item_id)
            self._refresh_menu_state()
            self._play_radio_activity_cue(self.navigator.session.model.selected_row)
        event.Skip()

    def _play_radio_activity_cue(self, row: Row | None) -> None:
        """Opcjonalny, krotki sygnal stanu. Nie dotyka hosta ani audio AMC."""
        if (
            row is None
            or row.kind != "station"
            or getattr(self.navigator, "active", None) is not SessionId.RADIO
        ):
            return
        playback = bool(
            row.playback_activity and self.options.radio_playback_state_sound
        )
        recording = bool(
            row.recording_activity and self.options.radio_recording_state_sound
        )
        if not playback and not recording:
            return
        try:
            import wx.adv as wxadv

            key = (playback, recording)
            sound = self._radio_activity_cues.get(key)
            if sound is None:
                sound = wxadv.Sound()
                if not sound.CreateFromData(
                    activity_cue_wav(playback=playback, recording=recording)
                ):
                    return
                self._radio_activity_cues[key] = sound
            sound.Play(wxadv.SOUND_ASYNC)
        except (ImportError, AttributeError, RuntimeError):
            # Sygnal jest dodatkiem. Jego brak nie moze zepsuc strzalek ani
            # wypowiadania nazwy stacji przez natywna liste.
            return

    def _on_item_selected(self, event: wx.ListEvent) -> None:
        """Zaznaczenie z klawiatury/myszy wraca do modelu, zeby ID pozostal
        stabilny po odswiezeniu listy.

        BRAMKA ``updating``: nasza wlasna aktualizacja listy (wstawienie wiersza,
        ``SetItemState``) wysyla DOKLADNIE TO SAMO zdarzenie co ruch
        uzytkownika. Bez bramki przejsciowy indeks z trwajacej podmiany
        nadpisalby swiadomy wybor uzytkownika -- np. po wstawieniu pierwszego
        wiersza model wskazywalby 0 zamiast zapamietanego utworu.
        """
        control = event.GetEventObject()
        if isinstance(control, MediaListCtrl) and control.updating:
            event.Skip()
            return
        # INDEKS Z KONTROLKI, NIE Z MODELU. Przy aktywnym filtrze lista
        # pokazuje tylko wiersze dopasowane, wiec ``GetIndex()`` numeruje
        # WIDOCZNE wiersze. Przelozenie go na ``item_id`` tego, co kontrolka
        # faktycznie ma w ``_shown``, jest jedyna poprawna droga -- bez tego
        # strzalka w dol na przefiltrowanej liscie wybieralaby w modelu
        # zupelnie inny utwor (ten pod tym samym numerem w PELNYM zbiorze), a
        # Enter odtwarzalby nie to, co czytnik przeczytal.
        if isinstance(control, MediaListCtrl):
            item_id = control.shown_item_id(event.GetIndex())
            if item_id is not None:
                self.navigator.session.model.select_id(item_id)
                self._refresh_menu_state()
                event.Skip()
                return
        self.navigator.session.model.select_index(event.GetIndex())
        # Bramki ``needs_selection`` zmieniaja sie WRAZ Z ZAZNACZENIEM, a nie
        # tylko przy zmianie widoku. Zmierzone na zywym GUI (statusclip-2):
        # bez tego wywolania pozycja "Skopiuj adres" zostawala WYLACZONA po
        # strzalce na liscie, a wylaczony akcelerator POLYKAL Ctrl+Shift+C --
        # klawisz docieral do okna i nie robil nic.
        self._refresh_menu_state()
        event.Skip()

    def _on_item_deselected(self, event: wx.ListEvent) -> None:
        """Nie pozwol, by model wskazywal wiersz usuniety z zaznaczenia.

        Przy Ctrl+klik lub skracaniu zakresu Shift natywna lista moze zostawic
        fokus na wierszu juz niezaznaczonym. To POPRAWNY stan dla Ctrl+Spacji:
        kotwica modelu zostaje wtedy na fokusie, a ``_cursor_target`` nie
        zamienia go z powrotem w zaznaczenie. Gdy fokus jest gdzie indziej,
        kotwice przenosimy na rzeczywiscie zaznaczony wiersz.
        """
        control = event.GetEventObject()
        if not isinstance(control, MediaListCtrl) or control.updating:
            event.Skip()
            return
        item_id = control.shown_item_id(event.GetIndex())
        model = self.navigator.session.model
        if item_id is not None and model.selected_id == item_id:
            focused = control.GetFocusedItem()
            if focused != event.GetIndex():
                replacement = (
                    focused
                    if control._is_index_selected(focused)
                    else control.GetFirstSelected()
                )
                replacement_id = control.shown_item_id(replacement)
                model.select_id(replacement_id)
            self._refresh_menu_state()
        event.Skip()

    def _activate(self) -> None:
        self._run(self.navigator.activate_selected(
            stay_on_list_after_radio_enter=(
                self.navigator.active in (SessionId.RADIO, SessionId.SONOS)
                and self.options.stay_on_list_after_radio_enter
            )
        ))

    def _current_preset_target(self) -> profile_presets.PresetTarget | None:
        """Element listy albo faktycznie odtwarzany element widoku gracza."""
        session = self.navigator.active
        state = self.navigator.session
        row = state.model.selected_row
        if state.view is View.PLAYER and state.now_playing_id:
            row = next(
                (
                    candidate for candidate in (
                        *state.playback_source_rows,
                        *state.model.rows,
                    )
                    if candidate.item_id == state.now_playing_id
                ),
                None,
            )
            # Plik otwarty bezposrednio przez Ctrl+O moze nie miec jeszcze
            # wiersza w Bibliotece, ale host zwraca jego prawdziwa sciezke.
            if row is None and session is SessionId.FILES:
                source = self._last_status.get("source")
                if isinstance(source, str) and source.strip():
                    row = Row(
                        item_id=state.now_playing_id,
                        title=state.now_playing_title or Path(source).name,
                        kind="track",
                        path=source.strip(),
                    )
        return profile_presets.target_from_row(session, row)

    def _active_sonos_target_row(self) -> Row | None:
        """Bieżąca grupa z ostatniej topologii; identyfikatory nie są tekstem UI."""
        if not self._sonos_active_household_id or not self._sonos_active_group_id:
            return None
        return next((
            row
            for row in self.navigator.sessions[SessionId.SONOS].sonos_target_rows
            if row.parent_id == self._sonos_active_household_id
            and row.service_id == self._sonos_active_group_id
            and row.service_kind == "sonosGroup"
        ), None)

    def _preset_inputs(self, session: SessionId) -> tuple[dict, list[dict]]:
        """Niezmienne migawki dla watku odczytujacego duzy profil AMC."""
        overrides = {
            key: [dict(item) for item in value]
            for key, value in self.state.preset_overrides.items()
        }
        stations = self.stations.as_payload() if session is SessionId.RADIO else []
        return overrides, stations

    def _show_presets(self) -> None:
        """Ctrl+Alt+P: jawna lista 12 miejsc, bez zapisu i bez technicznych ID."""
        session = self.navigator.active
        if session is SessionId.WIIM:
            self._show_wiim_presets()
            return
        target = self._current_preset_target()
        overrides, _stations = self._preset_inputs(session)

        def work() -> tuple[profile_presets.PresetEntry, ...]:
            return profile_presets.effective_entries(
                self.layout.state_json, session, overrides
            )

        def done(entries: tuple[profile_presets.PresetEntry, ...]) -> None:
            if self.navigator.active is not session:
                return
            session_name = session_options.session_display_name(session)
            with PresetListDialog(
                self,
                choices=profile_presets.choices(entries),
                session_name=session_name,
                current_target=target,
            ) as dialog:
                if dialog.ShowModal() != wx.ID_OK:
                    self._active_list().SetFocus() if self.navigator.view is View.LIST else self.play_button.SetFocus()
                    return
                choice = dialog.selected_choice
            if choice is not None:
                self._activate_preset(choice.slot)

        def failed(error: Exception) -> None:
            if isinstance(error, profile_presets.PresetProfileError):
                self.announcer.say(str(error))
            else:
                self.announcer.say("Nie udało się odczytać presetów")

        self.runner.submit("preset", work, done, failed)

    def _wiim_device_context(self) -> tuple[str, str, str] | None:
        """Zwróć wybrane urządzenie bez umieszczania jego Id w interfejsie."""
        state = self.navigator.sessions[SessionId.WIIM]
        row = state.model.selected_row
        if (
            row is not None
            and row.kind == "device"
            and row.service_kind == "device"
            and row.service_id
        ):
            return row.item_id, row.service_id, row.title
        device_id = (
            state.library_item_id
            if state.library_view in (
                LibraryView.WIIM_SOURCE_LIBRARY,
                LibraryView.WIIM_NETWORK_STREAMS,
            )
            else None
        ) or self._wiim_active_device_id
        if not device_id:
            return None
        rows = (
            state.wiim_device_rows
            if state.wiim_device_rows
            else tuple(state.model.rows)
        )
        row = next(
            (
                candidate for candidate in rows
                if candidate.kind == "device"
                and candidate.service_kind == "device"
                and candidate.service_id == device_id
            ),
            None,
        )
        if row is None:
            return None
        return row.item_id, device_id, row.title

    def _show_wiim_network_streams(
        self,
        *,
        preferred_stream_id: str | None = None,
        announcement: str | None = None,
    ) -> None:
        """Zapisane strumienie dla wybranego urządzenia WiiM."""
        client = self.client
        context = self._wiim_device_context()
        if client is None:
            self.announcer.say("Silnik nie jest gotowy")
            return
        if context is None:
            self.announcer.say("Wybierz urządzenie WiiM")
            return
        item_id, device_id, _device_title = context
        self._wiim_active_device_id = device_id
        return_to_sources = (
            self.navigator.sessions[SessionId.WIIM].library_view
            is LibraryView.WIIM_SOURCE_LIBRARY
        )

        def done(payload: object) -> None:
            if self.navigator.active is not SessionId.WIIM:
                return
            if isinstance(payload, dict):
                sort_mode = str(payload.get("sortMode") or "")
                if sort_mode in {
                    SORT_ADDED_NEWEST,
                    SORT_ALPHABETICAL,
                    SORT_CUSTOM,
                }:
                    self._wiim_network_stream_sort_mode = sort_mode
            try:
                rows = list(wiim_network_stream_rows(
                    payload,
                    device_id=device_id,
                ))
            except WiiMPayloadError as error:
                self.announcer.say(str(error))
                return
            self._run(self.navigator.apply_wiim_network_streams(
                rows,
                device_id=device_id,
                return_id=item_id,
                preferred_id=(
                    f"wiim-stream:{preferred_stream_id}"
                    if preferred_stream_id else None
                ),
                return_to_sources=return_to_sources,
            ))
            if announcement:
                self.announcer.say(announcement)

        self.runner.submit(
            "wiim-network-streams",
            client.wiim_network_streams,
            done,
            lambda error: self.announcer.say(
                f"Nie udało się odczytać strumieni WiiM: {error}"
            ),
        )

    def _selected_wiim_stream_rows(self) -> list[Row]:
        """Zwróć tylko zapisane strumienie, nigdy urządzenie ani techniczny wpis."""
        return [
            row for row in self._selected_action_rows()
            if row.kind == "wiimNetworkStream"
            and row.service_kind == "wiimNetworkStream"
            and bool(row.service_id)
        ]

    def _add_wiim_network_stream(self) -> None:
        client = self._profile_edit_client()
        if client is None:
            return
        context = self._wiim_device_context()
        if context is None:
            self.announcer.say("Wybierz urządzenie WiiM")
            return
        with StationDialog(
            self,
            "Dodaj strumień WiiM",
            network_stream=True,
        ) as dialog:
            if dialog.ShowModal() != wx.ID_OK:
                self._restore_focus_after_dialog()
                return
            name, url = dialog.values

        def done(payload: object) -> None:
            result = payload if isinstance(payload, dict) else {}
            preferred = str(result.get("preferredStreamId") or "") or None
            message = str(result.get("message") or f"Dodano strumień WiiM: {name}")
            self._show_wiim_network_streams(
                preferred_stream_id=preferred,
                announcement=message,
            )

        self.runner.submit(
            "wiim-stream-edit",
            lambda: client.wiim_add_network_stream(name, url),
            done,
            lambda error: self.announcer.say(f"Nie dodano strumienia WiiM: {error}"),
        )

    def _edit_wiim_network_stream(self) -> None:
        rows = self._selected_wiim_stream_rows()
        if len(rows) != 1:
            self.announcer.say("Do edycji wybierz jeden strumień WiiM")
            return
        client = self._profile_edit_client()
        if client is None:
            return
        selected = rows[0]
        stream_id = selected.service_id or ""

        def loaded(payload: object) -> None:
            try:
                loaded_id, current_name, current_url = wiim_network_stream_edit_info(payload)
            except WiiMPayloadError as error:
                self.announcer.say(str(error))
                return
            with StationDialog(
                self,
                "Edytuj strumień WiiM",
                current_name,
                current_url,
                network_stream=True,
            ) as dialog:
                if dialog.ShowModal() != wx.ID_OK:
                    self._restore_focus_after_dialog()
                    return
                name, url = dialog.values

            def saved(result_payload: object) -> None:
                result = result_payload if isinstance(result_payload, dict) else {}
                preferred = str(result.get("preferredStreamId") or loaded_id)
                message = str(
                    result.get("message") or f"Zapisano strumień WiiM: {name}"
                )
                self._show_wiim_network_streams(
                    preferred_stream_id=preferred,
                    announcement=message,
                )

            self.runner.submit(
                "wiim-stream-edit",
                lambda: client.wiim_edit_network_stream(loaded_id, name, url),
                saved,
                lambda error: self.announcer.say(
                    f"Nie zapisano strumienia WiiM: {error}"
                ),
            )

        self.runner.submit(
            "wiim-stream-edit-info",
            lambda: client.wiim_network_stream_edit_info(stream_id),
            loaded,
            lambda error: self.announcer.say(
                f"Nie odczytano strumienia WiiM: {error}"
            ),
        )

    def _remove_wiim_network_streams(self) -> None:
        rows = self._selected_wiim_stream_rows()
        if not rows:
            self.announcer.say("Wybierz strumień WiiM do usunięcia")
            return
        client = self._profile_edit_client()
        if client is None:
            return
        prompt = (
            f"Usunąć strumień {rows[0].title} z AMC? "
            "Lista w aplikacji WiiM Home pozostanie bez zmian."
            if len(rows) == 1 else
            f"Usunąć wybrane strumienie z AMC: {len(rows)}? "
            "Lista w aplikacji WiiM Home pozostanie bez zmian."
        )
        if wx.MessageBox(
            prompt,
            "Potwierdzenie",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
            self,
        ) != wx.YES:
            self._restore_focus_after_dialog()
            return
        stream_ids = [row.service_id for row in rows if row.service_id]

        def done(payload: object) -> None:
            result = payload if isinstance(payload, dict) else {}
            message = str(
                result.get("message")
                or f"Usunięto strumienie WiiM: {len(stream_ids)}"
            )
            self._show_wiim_network_streams(announcement=message)

        self.runner.submit(
            "wiim-stream-edit",
            lambda: client.wiim_remove_network_streams(stream_ids),
            done,
            lambda error: self.announcer.say(
                f"Nie usunięto strumieni WiiM: {error}"
            ),
        )

    def _import_wiim_network_streams(self) -> None:
        client = self._profile_edit_client()
        if client is None:
            return
        if self._wiim_device_context() is None:
            self.announcer.say("Wybierz urządzenie WiiM")
            return
        with wx.FileDialog(
            self,
            "Otwórz playlistę lub plik ze strumieniami WiiM",
            wildcard=(
                "Playlisty (*.m3u;*.m3u8;*.pls)|*.m3u;*.m3u8;*.pls|"
                "Wszystkie pliki (*.*)|*.*"
            ),
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as dialog:
            if dialog.ShowModal() != wx.ID_OK:
                self._restore_focus_after_dialog()
                return
            path = dialog.GetPath()

        def done(payload: object) -> None:
            result = payload if isinstance(payload, dict) else {}
            preferred = str(result.get("preferredStreamId") or "") or None
            message = str(
                result.get("message") or "Zakończono import strumieni WiiM"
            )
            self._show_wiim_network_streams(
                preferred_stream_id=preferred,
                announcement=message,
            )

        self.runner.submit(
            "wiim-stream-import",
            lambda: client.wiim_import_network_streams(path),
            done,
            lambda error: self.announcer.say(
                f"Nie można zaimportować playlisty: {error}"
            ),
        )

    def _export_wiim_network_streams(self) -> None:
        client = self._profile_edit_client()
        if client is None:
            return
        with wx.FileDialog(
            self,
            "Eksportuj strumienie do WiiM Home",
            defaultFile="Strumienie WiiM AMC.m3u",
            wildcard="Playlisty M3U (*.m3u)|*.m3u|Wszystkie pliki (*.*)|*.*",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as dialog:
            if dialog.ShowModal() != wx.ID_OK:
                self._restore_focus_after_dialog()
                return
            path = str(Path(dialog.GetPath()).with_suffix(".m3u"))

        def done(payload: object) -> None:
            result = payload if isinstance(payload, dict) else {}
            count = int(result.get("exportedCount") or 0)
            self.announcer.say(f"Wyeksportowano strumienie WiiM: {count}")
            self._restore_focus_after_dialog()

        self.runner.submit(
            "wiim-stream-export",
            lambda: client.wiim_export_network_streams(path),
            done,
            lambda error: self.announcer.say(
                f"Nie można zapisać playlisty: {error}"
            ),
        )

    def _set_wiim_network_stream_sort(self, action: Action) -> None:
        modes = {
            Action.SORT_WIIM_NETWORK_STREAMS_ADDED: SORT_ADDED_NEWEST,
            Action.SORT_WIIM_NETWORK_STREAMS_ALPHABETICAL: SORT_ALPHABETICAL,
            Action.SORT_WIIM_NETWORK_STREAMS_CUSTOM: SORT_CUSTOM,
        }
        mode = modes[action]
        client = self._profile_edit_client()
        if client is None:
            return
        selected = next(iter(self._selected_wiim_stream_rows()), None)
        preferred = selected.service_id if selected is not None else None

        def done(payload: object) -> None:
            result = payload if isinstance(payload, dict) else {}
            self._wiim_network_stream_sort_mode = mode
            message = str(result.get("message") or "Zmieniono kolejność strumieni WiiM")
            self._show_wiim_network_streams(
                preferred_stream_id=preferred,
                announcement=message,
            )

        self.runner.submit(
            "wiim-stream-sort",
            lambda: client.wiim_sort_network_streams(mode),
            done,
            lambda error: self.announcer.say(
                f"Nie zapisano kolejności strumieni WiiM: {error}"
            ),
        )

    def _activate_wiim_network_stream(
        self, intent: PlayWiiMNetworkStream
    ) -> None:
        """Uruchom strumień po Id; adres nigdy nie przechodzi do wx/NVDA."""
        client = self.client
        if client is None:
            self._run(self.navigator.back_to_list())
            self.announcer.say("Silnik nie jest gotowy")
            return
        self._wiim_active_device_id = intent.device_id
        self._wiim_snapshot = {}
        self.now_playing.SetLabel(intent.title)
        self._set_transport_label(playing=False, preparing=True)

        def done(payload: object) -> None:
            try:
                state = wiim_snapshot(payload)
            except WiiMPayloadError as error:
                failed(error)
                return
            if state.get("deviceId") != self._wiim_active_device_id:
                return
            session = self.navigator.sessions[SessionId.WIIM]
            session.player_entry_anchor_id = intent.item_id
            session.list_anchor_id = intent.item_id
            session.now_playing_id = intent.item_id
            session.now_playing_title = intent.title
            session.current_material_id = intent.item_id
            session.view = View.PLAYER
            self._wiim_snapshot = state
            if self.navigator.active is SessionId.WIIM:
                self._sync_views()
                self._apply_wiim_snapshot(state, announce=True)

        def failed(error: Exception) -> None:
            session = self.navigator.sessions[SessionId.WIIM]
            session.view = View.LIST
            if self.navigator.active is SessionId.WIIM:
                self._sync_views()
                self.announcer.say(str(error))

        self.runner.submit(
            "wiim-network-stream-play",
            lambda: client.wiim_play_network_stream(
                intent.device_id,
                intent.stream_id,
            ),
            done,
            failed,
        )

    def _show_wiim_option(self, action: Action) -> None:
        """Otwórz jedną opcję odtwarzacza WiiM z etykietami hosta C#."""
        option_by_action = {
            Action.WIIM_SELECT_INPUT: "input",
            Action.WIIM_SELECT_OUTPUT: "output",
            Action.WIIM_SELECT_EQUALIZER: "equalizer",
            Action.WIIM_SELECT_REPEAT: "repeat",
            Action.WIIM_SET_SLEEP_TIMER: "sleep",
        }
        option = option_by_action.get(action)
        client = self.client
        context = self._wiim_device_context()
        if option is None:
            self.announcer.say("Nieznane ustawienie WiiM")
            return
        if client is None:
            self.announcer.say("Silnik nie jest gotowy")
            return
        if self.navigator.view is not View.PLAYER or context is None:
            self.announcer.say(
                "To ustawienie WiiM jest dostępne po otwarciu sterowania urządzeniem"
            )
            return
        _item_id, device_id, device_title = context

        def done(payload: object) -> None:
            if (
                self.navigator.active is not SessionId.WIIM
                or self.navigator.view is not View.PLAYER
                or self._wiim_active_device_id != device_id
            ):
                return
            try:
                (
                    _returned_device_title,
                    title,
                    description,
                    choices,
                    selected_index,
                ) = wiim_option_choices(payload)
            except WiiMPayloadError as error:
                self.announcer.say(str(error))
                return
            with WiiMOptionDialog(
                self,
                title=title,
                description=description,
                choices=choices,
                selected_index=selected_index,
            ) as dialog:
                if dialog.ShowModal() != wx.ID_OK:
                    self._restore_focus_after_dialog()
                    return
                choice = dialog.selected_choice
            if choice is None:
                self._restore_focus_after_dialog()
                return

            def applied(result: object) -> None:
                try:
                    state = wiim_snapshot(result)
                except WiiMPayloadError as error:
                    self.announcer.say(str(error))
                    return
                if (
                    self.navigator.active is not SessionId.WIIM
                    or self.navigator.view is not View.PLAYER
                    or self._wiim_active_device_id != device_id
                ):
                    return
                self._wiim_snapshot = state
                self._apply_wiim_snapshot(state, announce=True)
                self.play_button.SetFocus()

            self.runner.submit(
                f"wiim-option-set-{option}",
                lambda: client.wiim_set_option(device_id, option, choice.value),
                applied,
                lambda error: self.announcer.say(
                    f"Nie udało się zastosować ustawienia urządzenia "
                    f"{device_title}: {error}"
                ),
            )

        self.runner.submit(
            f"wiim-option-read-{option}",
            lambda: client.wiim_options(device_id, option),
            done,
            lambda error: self.announcer.say(
                f"Urządzenie {device_title} nie udostępniło tej opcji: {error}"
            ),
        )

    def _toggle_wiim_shuffle(self) -> None:
        client = self.client
        context = self._wiim_device_context()
        if client is None:
            self.announcer.say("Silnik nie jest gotowy")
            return
        if self.navigator.view is not View.PLAYER or context is None:
            self.announcer.say(
                "Losowanie WiiM jest dostępne po otwarciu sterowania urządzeniem"
            )
            return
        _item_id, device_id, device_title = context

        def done(payload: object) -> None:
            try:
                state = wiim_snapshot(payload)
            except WiiMPayloadError as error:
                self.announcer.say(str(error))
                return
            if (
                self.navigator.active is not SessionId.WIIM
                or self.navigator.view is not View.PLAYER
                or self._wiim_active_device_id != device_id
            ):
                return
            self._wiim_snapshot = state
            self._apply_wiim_snapshot(state, announce=True)
            self.play_button.SetFocus()

        self.runner.submit(
            "wiim-shuffle-toggle",
            lambda: client.wiim_toggle_shuffle(device_id),
            done,
            lambda error: self.announcer.say(
                f"Nie udało się zmienić losowania urządzenia "
                f"{device_title}: {error}"
            ),
        )

    def _show_wiim_presets(self, *, select_for_shortcut: bool = False) -> None:
        """Lista 12 miejsc urządzenia albo wybór celu skrótu AMC."""
        client = self.client
        context = self._wiim_device_context()
        if client is None:
            self.announcer.say("Silnik nie jest gotowy")
            return
        if context is None:
            self.announcer.say("Wybierz urządzenie WiiM")
            return
        item_id, device_id, device_title = context
        overrides, _stations = self._preset_inputs(SessionId.WIIM)

        def work():
            payload = client.wiim_presets(device_id)
            returned_title, choices = wiim_preset_choices(payload)
            entries = profile_presets.effective_wiim_entries(
                self.layout.state_json,
                device_id,
                choices,
                overrides,
            )
            return returned_title, choices, entries

        def done(result) -> None:
            if self.navigator.active is not SessionId.WIIM:
                return
            returned_title, choices, entries = result
            shortcut_slots = {
                number: entry.slot
                for entry in entries
                if (number := profile_presets.wiim_native_preset_number(entry))
                is not None
            }
            with WiiMPresetListDialog(
                self,
                choices=choices,
                device_title=returned_title or device_title,
                shortcut_slots_by_preset=shortcut_slots,
                select_for_shortcut=select_for_shortcut,
            ) as dialog:
                if dialog.ShowModal() != wx.ID_OK:
                    if self.navigator.view is View.LIST:
                        self._active_list().SetFocus()
                    else:
                        self.play_button.SetFocus()
                    return
                choice = dialog.selected_choice
            if choice is not None:
                if dialog.shortcut_assignment_requested:
                    self._assign_wiim_preset_shortcut(
                        device_id,
                        returned_title or device_title,
                        choice,
                        entries,
                    )
                else:
                    self._activate_wiim_preset(
                        item_id,
                        device_id,
                        returned_title or device_title,
                        choice,
                    )

        self.runner.submit(
            "wiim-presets",
            work,
            done,
            lambda error: self.announcer.say(
                f"Nie udało się odczytać presetów urządzenia {device_title}: {error}"
            ),
        )

    def _assign_wiim_preset_shortcut(
        self,
        device_id: str,
        device_title: str,
        native_choice: WiiMPresetChoice,
        entries: tuple[profile_presets.PresetEntry, ...],
    ) -> None:
        """Przypisz gotowy preset urządzenia bez zmiany samego urządzenia."""
        try:
            target = profile_presets.wiim_native_target(native_choice)
        except ValueError as error:
            self.announcer.say(str(error))
            return
        choices = profile_presets.choices(entries)
        free = profile_presets.first_free_slot(entries)
        existing = profile_presets.existing_target_slot(entries, target)
        initial = existing or free or 1
        with PresetAssignmentDialog(
            self,
            target=target,
            choices=choices,
            first_free_slot=free,
            initial_slot=initial,
            session_name=f"WiiM, {device_title}",
        ) as dialog:
            if dialog.ShowModal() != wx.ID_OK:
                self._restore_focus_after_dialog()
                return
            slot = dialog.selected_slot
            action = dialog.selected_action

        updated = (
            profile_presets.remove_entry(entries, slot)
            if action == "remove"
            else profile_presets.replace_entry(entries, target, slot)
        )
        key = profile_presets.wiim_device_preset_key(device_id)
        previous = {
            name: [dict(item) for item in value]
            for name, value in self.state.preset_overrides.items()
        }
        next_overrides = {
            name: [dict(item) for item in value]
            for name, value in previous.items()
        }
        next_overrides[key] = profile_presets.entries_payload(updated)
        self.state.preset_overrides = next_overrides
        try:
            self.store.save(self.state)
        except Exception:
            self.state.preset_overrides = previous
            self.announcer.say(
                "Nie udało się zapisać przypisania. Niczego nie zmieniono"
            )
            return
        spoken = profile_presets.shortcut_label(slot, spoken=True)
        if action == "remove":
            self.announcer.say(
                f"Usunięto przypisanie Ctrl+Shift+{spoken}. "
                "Preset urządzenia pozostał bez zmian"
            )
        else:
            self.announcer.say(
                f"Ctrl+Shift+{spoken} uruchamia preset {native_choice.number}, "
                f"{native_choice.title}. Ustawienia urządzenia nie zostały zmienione"
            )

    def _activate_wiim_shortcut_preset(self, slot: int) -> None:
        """Rozwiąż miejsce Ctrl+Shift dla bieżącego urządzenia WiiM."""
        client = self.client
        context = self._wiim_device_context()
        spoken = profile_presets.shortcut_label(slot, spoken=True)
        if client is None:
            self.announcer.say("Silnik nie jest gotowy")
            return
        if context is None:
            self.announcer.say("Wybierz urządzenie WiiM")
            return
        item_id, device_id, device_title = context
        overrides, _stations = self._preset_inputs(SessionId.WIIM)

        def work():
            payload = client.wiim_presets(device_id)
            returned_title, choices = wiim_preset_choices(payload)
            entries = profile_presets.effective_wiim_entries(
                self.layout.state_json,
                device_id,
                choices,
                overrides,
            )
            return returned_title, choices, entries

        def done(result) -> None:
            if self.navigator.active is not SessionId.WIIM:
                return
            returned_title, choices, entries = result
            entry = next((entry for entry in entries if entry.slot == slot), None)
            number = profile_presets.wiim_native_preset_number(entry)
            if number is None:
                self.announcer.say(
                    f"Preset {spoken} pusty. Ctrl+Alt+Shift+P przypisuje "
                    "gotowy preset WiiM"
                )
                return
            choice = next(
                (choice for choice in choices if choice.number == number),
                None,
            )
            if choice is None or not choice.occupied:
                self.announcer.say(
                    f"Skrót Ctrl+Shift+{spoken} wskazuje preset {number}, "
                    "który nie jest już dostępny w urządzeniu"
                )
                return
            if choice.activation_error:
                self.announcer.say(choice.activation_error)
                return
            self._last_preset_slot_by_session[SessionId.WIIM] = slot
            self._activate_wiim_preset(
                item_id,
                device_id,
                returned_title or device_title,
                choice,
            )

        self.runner.submit(
            "wiim-shortcut-preset",
            work,
            done,
            lambda error: self.announcer.say(
                f"Nie udało się uruchomić presetu urządzenia {device_title}: {error}"
            ),
        )

    def _activate_wiim_preset(
        self,
        item_id: str,
        device_id: str,
        device_title: str,
        choice: WiiMPresetChoice,
    ) -> None:
        """Uruchom zajęty preset i dopiero po sukcesie pokaż odtwarzacz."""
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie jest gotowy")
            return

        def done(payload: object) -> None:
            try:
                state = wiim_snapshot(payload)
            except WiiMPayloadError as error:
                self.announcer.say(str(error))
                return
            if state.get("deviceId") != device_id:
                return
            session = self.navigator.sessions[SessionId.WIIM]
            session.player_entry_anchor_id = item_id
            session.list_anchor_id = item_id
            session.now_playing_id = item_id
            session.now_playing_title = device_title
            session.current_material_id = item_id
            session.view = View.PLAYER
            self._wiim_active_device_id = device_id
            self._wiim_snapshot = state
            if self.navigator.active is SessionId.WIIM:
                self._sync_views()
                self._apply_wiim_snapshot(state, announce=True)

        self.runner.submit(
            "wiim-preset-activate",
            lambda: client.wiim_activate_preset(device_id, choice.number),
            done,
            lambda error: self.announcer.say(
                f"Nie udało się uruchomić presetu urządzenia {device_title}: {error}"
            ),
        )

    def _assign_preset(self) -> None:
        """Ctrl+Alt+Shift+P: trwale zapisz tylko prywatne nadpisanie wxPython."""
        session = self.navigator.active
        if session is SessionId.WIIM:
            self._show_wiim_presets(select_for_shortcut=True)
            return
        target = self._current_preset_target()
        if target is None:
            self.announcer.say(
                f"Wybierz element sesji {session_options.session_display_name(session)}, "
                "który chcesz przypisać do presetu"
            )
            return
        overrides, _stations = self._preset_inputs(session)

        def work() -> tuple[profile_presets.PresetEntry, ...]:
            return profile_presets.effective_entries(
                self.layout.state_json, session, overrides
            )

        def done(entries: tuple[profile_presets.PresetEntry, ...]) -> None:
            if self.navigator.active is not session:
                return
            free = profile_presets.first_free_slot(entries)
            existing_slot = profile_presets.existing_target_slot(entries, target)
            initial = existing_slot or free or 1
            existing = next(
                (entry for entry in entries if entry.slot == existing_slot),
                None,
            )
            fixed_row = (
                self._active_sonos_target_row()
                if session is SessionId.SONOS else None
            )
            fixed_available = bool(
                fixed_row is not None
                and fixed_row.service_members
                and (
                    target.sonos_household_id is None
                    or target.sonos_household_id == fixed_row.parent_id
                )
            )
            with PresetAssignmentDialog(
                self,
                target=target,
                choices=profile_presets.choices(entries),
                first_free_slot=free,
                initial_slot=initial,
                session_name=session_options.session_display_name(session),
                fixed_target_title=(fixed_row.title if fixed_row else ""),
                fixed_target_available=fixed_available,
                fixed_target_initially_selected=bool(
                    existing is not None
                    and existing.sonos_fixed_player_ids
                ),
            ) as dialog:
                if dialog.ShowModal() != wx.ID_OK:
                    self._active_list().SetFocus() if self.navigator.view is View.LIST else self.play_button.SetFocus()
                    return
                slot = dialog.selected_slot
                action = dialog.selected_action
                fixed_selected = dialog.fixed_target_selected

            assigned_target = target
            if action != "remove" and fixed_selected and fixed_row is not None:
                assigned_target = profile_presets.PresetTarget(
                    target.target_id,
                    target.target_kind,
                    target.title,
                    target.location,
                    sonos_household_id=(
                        target.sonos_household_id or fixed_row.parent_id
                    ),
                    sonos_fixed_player_ids=fixed_row.service_members,
                )

            updated = (
                profile_presets.remove_entry(entries, slot)
                if action == "remove"
                else profile_presets.replace_entry(entries, assigned_target, slot)
            )
            previous = {
                key: [dict(item) for item in value]
                for key, value in self.state.preset_overrides.items()
            }
            next_overrides = {
                key: [dict(item) for item in value]
                for key, value in previous.items()
            }
            next_overrides[session.value] = profile_presets.entries_payload(updated)
            self.state.preset_overrides = next_overrides
            try:
                self.store.save(self.state)
            except Exception:
                self.state.preset_overrides = previous
                self.announcer.say("Nie udało się zapisać presetów. Niczego nie zmieniono")
                return

            spoken = profile_presets.shortcut_label(slot, spoken=True)
            if action == "remove":
                self.announcer.say(f"Usunięto preset {spoken}")
            else:
                self.announcer.say(f"Zapisano preset {spoken}: {target.title}")

        def failed(error: Exception) -> None:
            if isinstance(error, profile_presets.PresetProfileError):
                self.announcer.say(str(error))
            else:
                self.announcer.say("Nie udało się przygotować przypisania presetu")

        self.runner.submit("preset", work, done, failed)

    def _activate_preset(self, slot: int) -> None:
        """Uruchom preset profilu AMC albo jego prywatne nadpisanie wxPython."""
        session = self.navigator.active
        if session is SessionId.WIIM:
            self._activate_wiim_shortcut_preset(slot)
            return
        spoken = profile_presets.shortcut_label(slot, spoken=True)
        overrides, stations = self._preset_inputs(session)

        def work():
            return profile_presets.resolve_preset(
                self.layout.state_json,
                session,
                slot,
                overrides=overrides,
                current_stations=stations,
            )

        def done(resolved: profile_presets.ResolvedPreset) -> None:
            # Preset nalezy do sesji z chwili nacisniecia. Odpowiedz po zmianie
            # sesji nie moze uruchomic materialu w obcym kontekscie.
            if self.navigator.active is not session:
                return
            entry = resolved.entry
            if entry is None:
                self.announcer.say(
                    f"Preset {spoken} pusty. Ctrl+Alt+Shift+P przypisuje bieżący element."
                )
                return

            if session is SessionId.RADIO:
                target = resolved.radio_target
                if target is None:
                    self.announcer.say(
                        f"Preset {spoken} jest niedostępny. Stacji nie ma już w profilu."
                    )
                    return
                sequence = tuple(
                    Row(
                        item_id=item.item_id,
                        title=item.title,
                        kind="station",
                        url=item.url,
                        show_kind=False,
                    )
                    for item in resolved.radio_sequence
                )
                target_row = next(
                    item for item in sequence if item.item_id == target.item_id
                )
                self._last_preset_slot_by_session[session] = slot
                self._run(self.navigator.activate_radio_preset(
                    target_row,
                    sequence,
                    open_player=self.options.open_player_when_activating_preset,
                ))
                return

            if session is SessionId.SONOS and entry.target_kind.casefold() in {
                "sonos-favorite",
                "sonos-playlist",
                "sonos-own-stream",
            }:
                self._last_preset_slot_by_session[session] = slot
                self._activate_sonos_preset(entry, spoken)
                return

            kind = entry.target_kind.casefold()
            if kind == "folder" and entry.location:
                self._last_preset_slot_by_session[session] = slot
                self._open_library(entry.location)
                return
            if kind == "amcplaylist":
                playlist_id = entry.location
                if not playlist_id and ":" in entry.target_id:
                    playlist_id = entry.target_id.split(":", 1)[1]
                if playlist_id:
                    self._last_preset_slot_by_session[session] = slot
                    self._open_library_view(OpenLibraryView(
                        view=LibraryView.PLAYLIST_CONTENTS,
                        playlist_id=playlist_id,
                        target_session_id=SessionId.FILES,
                    ))
                    return
            if kind in ("track", "file") and entry.location:
                self._last_preset_slot_by_session[session] = slot
                target_row = Row(
                    item_id=entry.target_id,
                    title=entry.title or Path(entry.location).name,
                    kind="track",
                    path=entry.location,
                )
                self._run(self.navigator.activate_local_preset(
                    target_row,
                    open_player=self.options.open_player_when_activating_preset,
                ))
                return
            self.announcer.say(
                f"Preset {spoken} istnieje, ale ten rodzaj materiału nie jest jeszcze przeniesiony."
            )

        def failed(error: Exception) -> None:
            if isinstance(error, profile_presets.PresetProfileError):
                self.announcer.say(str(error))
            else:
                self.announcer.say("Nie udało się odczytać presetu")

        self.runner.submit("preset", work, done, failed)

    def _navigate_nvda_preset(self, direction: int) -> None:
        """Dodatek NVDA: przejdź po zajętych presetach bieżącej sesji.

        Odczyt profilu może być duży, dlatego nie blokuje wątku okna ani
        odpowiedzi do dodatku. Wynik rozpoczęty w jednej sesji nie uruchomi
        niczego po przełączeniu do innej.
        """

        session = self.navigator.active
        if session is SessionId.WIIM:
            self._navigate_nvda_wiim_preset(direction)
            return
        target = self._current_preset_target()
        overrides, _stations = self._preset_inputs(session)
        current_slot = self._last_preset_slot_by_session.get(session)

        def work() -> profile_presets.PresetEntry | None:
            entries = profile_presets.effective_entries(
                self.layout.state_json, session, overrides
            )
            return profile_presets.adjacent_entry(
                entries,
                direction=direction,
                current_target=target,
                current_slot=current_slot,
            )

        def done(entry: profile_presets.PresetEntry | None) -> None:
            if self.navigator.active is not session:
                return
            if entry is None:
                self.announcer.say(
                    f"Brak zapisanych presetów: "
                    f"{session_options.session_display_name(session)}"
                )
                return
            self._activate_preset(entry.slot)

        self.runner.submit(
            "preset-navigate",
            work,
            done,
            lambda error: self.announcer.say(
                str(error)
                if isinstance(error, profile_presets.PresetProfileError)
                else "Nie udało się odczytać presetów"
            ),
        )

    def _navigate_nvda_wiim_preset(self, direction: int) -> None:
        """WiiM: użyj żywej listy urządzenia, bez otwierania jej w oknie."""

        client = self.client
        context = self._wiim_device_context()
        if client is None:
            self.announcer.say("Silnik nie jest gotowy")
            return
        if context is None:
            self.announcer.say("Wybierz urządzenie WiiM")
            return
        item_id, device_id, device_title = context
        overrides, _stations = self._preset_inputs(SessionId.WIIM)
        current_slot = self._last_preset_slot_by_session.get(SessionId.WIIM)

        def work():
            payload = client.wiim_presets(device_id)
            returned_title, choices = wiim_preset_choices(payload)
            entries = profile_presets.effective_wiim_entries(
                self.layout.state_json,
                device_id,
                choices,
                overrides,
            )
            if current_slot is None:
                current_number = next(
                    (choice.number for choice in choices if choice.current),
                    None,
                )
                active_slot = next(
                    (
                        entry.slot
                        for entry in entries
                        if profile_presets.wiim_native_preset_number(entry)
                        == current_number
                    ),
                    None,
                )
            else:
                active_slot = current_slot
            entry = profile_presets.adjacent_entry(
                entries,
                direction=direction,
                current_slot=active_slot,
            )
            return returned_title, choices, entry

        def done(result) -> None:
            if self.navigator.active is not SessionId.WIIM:
                return
            returned_title, choices, entry = result
            if entry is None:
                self.announcer.say(f"Brak zapisanych presetów: {device_title}")
                return
            number = profile_presets.wiim_native_preset_number(entry)
            choice = next(
                (candidate for candidate in choices if candidate.number == number),
                None,
            )
            if choice is None or not choice.occupied:
                self.announcer.say("Wybrany preset WiiM nie jest już dostępny")
                return
            if choice.activation_error:
                self.announcer.say(choice.activation_error)
                return
            self._last_preset_slot_by_session[SessionId.WIIM] = entry.slot
            self._activate_wiim_preset(
                item_id,
                device_id,
                returned_title or device_title,
                choice,
            )

        self.runner.submit(
            "wiim-preset-navigate",
            work,
            done,
            lambda error: self.announcer.say(
                f"Nie udało się odczytać presetów urządzenia {device_title}: {error}"
            ),
        )

    def _activate_sonos_preset(
        self,
        entry: profile_presets.PresetEntry,
        spoken_slot: str,
    ) -> None:
        """Uruchom materiał presetu na bieżącej albo dokładnie zapisanej grupie."""
        if self.navigator.active is not SessionId.SONOS:
            return
        kind = {
            "sonos-favorite": "favorite",
            "sonos-playlist": "playlist",
            "sonos-own-stream": "ownStream",
        }.get(entry.target_kind.casefold())
        if kind is None:
            self.announcer.say(
                f"Preset {spoken_slot} ma nieobsługiwany rodzaj materiału Sonos"
            )
            return

        fixed = tuple(sorted(set(entry.sonos_fixed_player_ids)))
        if not fixed:
            if not self._sonos_active_household_id or not self._sonos_active_group_id:
                self.announcer.say(
                    "Nie wybrano głośników Sonos. Wybierz grupę skrótem "
                    "Control F5 i spróbuj ponownie. Nic nie uruchomiłem"
                )
                return
            self._start_sonos_preset_material(
                entry,
                kind,
                spoken_slot,
                self._sonos_active_household_id,
                self._sonos_active_group_id,
            )
            return

        if not entry.sonos_household_id:
            self.announcer.say(
                f"Preset {spoken_slot} nie ma bezpiecznie zapisanego domu Sonos. "
                "Przypisz go ponownie. Nic nie uruchomiłem"
            )
            return
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie jest gotowy")
            return

        def done(payload: object) -> None:
            if self.navigator.active is not SessionId.SONOS:
                return
            try:
                rows = list(sonos_target_rows(payload))
            except SonosPayloadError:
                self.announcer.say(
                    "Nie udało się odczytać grup Sonos. Nic nie uruchomiłem"
                )
                return
            wanted = set(fixed)
            matches = [
                row for row in rows
                if row.parent_id == entry.sonos_household_id
                and set(row.service_members) == wanted
                and bool(row.service_id)
            ]
            if not matches:
                self.announcer.say(
                    "Nie ma teraz grupy Sonos o dokładnie tym zestawie "
                    "głośników. Zgrupuj je tak jak przy zapisie presetu. "
                    "Niczego nie uruchomiłem i nie przegrupowałem"
                )
                return
            if len(matches) > 1:
                self.announcer.say(
                    "Kilka grup Sonos ma ten sam zestaw głośników, więc wybór "
                    "nie jest jednoznaczny. Nic nie uruchomiłem"
                )
                return
            target = matches[0]
            self.navigator.sessions[SessionId.SONOS].sonos_target_rows = tuple(rows)
            self._start_sonos_preset_material(
                entry,
                kind,
                spoken_slot,
                target.parent_id or "",
                target.service_id or "",
            )

        self.runner.submit(
            "sonos-preset-target",
            client.sonos_targets,
            done,
            lambda _error: self.announcer.say(
                "Nie udało się odczytać grup Sonos. Nic nie uruchomiłem"
            ),
        )

    def _start_sonos_preset_material(
        self,
        entry: profile_presets.PresetEntry,
        kind: str,
        spoken_slot: str,
        household_id: str,
        group_id: str,
    ) -> None:
        if (
            kind in {"favorite", "playlist"}
            and entry.sonos_household_id
            and entry.sonos_household_id != household_id
        ):
            self.announcer.say(
                f"Preset {spoken_slot} zapisano dla innego domu Sonos. "
                "Przypisz go ponownie w tym domu. Nic nie uruchomiłem"
            )
            return
        if not household_id or not group_id:
            self.announcer.say(
                "Nie wybrano głośników Sonos. Nic nie uruchomiłem"
            )
            return
        self._sonos_active_household_id = household_id
        self._sonos_active_group_id = group_id
        self._play_sonos_material(PlaySonosMaterial(
            item_id=f"sonos-preset:{entry.slot}",
            title=entry.title or "Preset Sonos",
            household_id=household_id,
            kind=kind,
            material_id=entry.target_id,
        ))

    def _switch_session(self, session_id: SessionId) -> None:
        if self.navigator.active is SessionId.TIDAL and session_id is not SessionId.TIDAL:
            self._tidal_navigation_version += 1
        if (
            self.navigator.active is SessionId.SPOTIFY
            and session_id is not SessionId.SPOTIFY
        ):
            self._spotify_navigation_version += 1
        self._run(self.navigator.switch_session(session_id))
        if session_id is SessionId.PODCASTS:
            state = self.navigator.sessions[SessionId.PODCASTS]
            if not state.model.rows:
                self._open_podcast_library(preferred_id=state.list_anchor_id)
        elif session_id is SessionId.TIDAL:
            state = self.navigator.sessions[SessionId.TIDAL]
            if not state.model.rows:
                self._open_tidal_view(OpenTidalView(
                    LibraryView.TIDAL_LIBRARY,
                    preferred_id=state.list_anchor_id,
                ))
        elif session_id is SessionId.SPOTIFY:
            state = self.navigator.sessions[SessionId.SPOTIFY]
            if not state.model.rows:
                self._open_spotify_view(OpenSpotifyView(
                    preferred_id=state.list_anchor_id,
                ))
        elif session_id is SessionId.WIIM:
            state = self.navigator.sessions[SessionId.WIIM]
            if not state.model.rows:
                self._load_wiim_devices(preferred_id=state.list_anchor_id)
        elif session_id is SessionId.SONOS:
            state = self.navigator.sessions[SessionId.SONOS]
            if not state.model.rows:
                self._load_sonos_targets(preferred_id=state.list_anchor_id)

    def _show_session_list(self) -> None:
        """Ctrl+Shift+S i dodatek NVDA: wybór sesji bez nazw modelu."""
        with SessionSelectionDialog(
            self,
            self.navigator.active,
            self.options.session_order,
        ) as dialog:
            if dialog.ShowModal() != wx.ID_OK:
                self._restore_focus_after_dialog()
                return
            selected = dialog.selected_session
        if selected is not None:
            self._transient_preview_return = None
            self._switch_session(selected)
            # Gdy użytkownik zatwierdzi już aktywną sesję, _sync_views nie
            # zmienia widoku i celowo nie ustawia fokusu ponownie. Po zamknięciu
            # dialogu lista albo odtwarzacz nadal muszą jednak odzyskać fokus.
            wx.CallAfter(self._restore_focus_after_dialog)

    def _show_command_palette(self) -> None:
        entries = command_entries_for_session(
            self.navigator.active,
            self.options.session_order,
        )
        with CommandPaletteDialog(self, entries) as dialog:
            if dialog.ShowModal() != wx.ID_OK:
                self._restore_focus_after_dialog()
                return
            selected = dialog.selected_entry
        self._restore_focus_after_dialog()
        if selected is not None:
            self._dispatch(selected.action)

    # --------------------------------------------------------------- WiiM

    def _load_wiim_devices(self, preferred_id: str | None = None) -> None:
        """Wczytaj wyłącznie zapisane urządzenia; adresy pozostają w C#."""
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie jest gotowy")
            return

        def done(payload: object) -> None:
            try:
                rows = list(wiim_device_rows(payload))
            except WiiMPayloadError as error:
                self.announcer.say(str(error))
                return
            state = self.navigator.sessions[SessionId.WIIM]
            # Pierwszenstwo ma wybor z prywatnego stanu AMC Python albo
            # urzadzenie uzywane w tym procesie. Pole ``selected`` hosta jest
            # tylko zgodnosciowym fallbackiem starego profilu i nie moze za
            # kazdym razem przestawiac fokusu z Pro Plus na WiiM Sound.
            selected_id = preferred_id or state.wiim_device_return_id
            if selected_id is None and self._wiim_active_device_id:
                active_row = next((
                    row for row in rows
                    if row.service_id == self._wiim_active_device_id
                ), None)
                if active_row is not None:
                    selected_id = active_row.item_id
            if selected_id is None and isinstance(payload, dict):
                raw_items = payload.get("items")
                if isinstance(raw_items, list):
                    selected = next((
                        item for item in raw_items
                        if isinstance(item, dict) and item.get("selected") is True
                    ), None)
                    if isinstance(selected, dict):
                        candidate = selected.get("itemId")
                        if isinstance(candidate, str) and any(
                            row.item_id == candidate for row in rows
                        ):
                            selected_id = candidate
            events = self.navigator.apply_wiim_devices(rows, selected_id)
            if self.navigator.active is SessionId.WIIM:
                self._run(events)
            else:
                self._sync_views()

        self.runner.submit(
            "wiim-devices",
            client.wiim_devices,
            done,
            lambda error: self.announcer.say(
                f"Nie udało się odczytać urządzeń WiiM: {error}"
            ),
        )

    def _activate_wiim_device(self, intent: ActivateWiiMDevice) -> None:
        client = self.client
        if client is None:
            self._run(self.navigator.back_to_list())
            self.announcer.say("Silnik nie jest gotowy")
            return
        self._wiim_active_device_id = intent.device_id
        self._wiim_snapshot = {}
        # Tytuł urządzenia jest uczciwym stanem przejściowym, zanim przyjdzie
        # migawka utworu. Nie pokazujemy technicznego identyfikatora.
        self.now_playing.SetLabel(intent.title)
        self._set_transport_label(playing=False, preparing=True)

        def done(payload: object) -> None:
            try:
                state = wiim_snapshot(payload)
            except WiiMPayloadError as error:
                failed(error)
                return
            if state.get("deviceId") != self._wiim_active_device_id:
                return
            self._wiim_snapshot = state
            if (
                self.navigator.active is SessionId.WIIM
                and self.navigator.view is View.PLAYER
            ):
                self._apply_wiim_snapshot(state, announce=True)

        def failed(error: Exception) -> None:
            state = self.navigator.sessions[SessionId.WIIM]
            state.view = View.LIST
            if self.navigator.active is SessionId.WIIM:
                self._sync_views()
                self.announcer.say(str(error))

        self.runner.submit(
            "wiim-snapshot",
            lambda: client.wiim_snapshot(intent.device_id),
            done,
            failed,
        )

    def _apply_wiim_snapshot(
        self, state: dict, *, announce: bool = False
    ) -> None:
        """Pokaż migawkę WiiM bez przepuszczania repr, adresu ani Id."""
        label = wiim_now_playing_label(state)
        if self.now_playing.GetLabel() != label:
            self.now_playing.SetLabel(label)
        # Nazwa kontrolki jest stałą etykietą pola. Treść utworu pozostaje
        # jego wartością/tekstem, więc po przejściu do innej sesji nie może
        # zostać stara nazwa WiiM czytana nad nowym tytułem.
        self.now_playing.SetName("Teraz odtwarzane")
        time_label = player_time_label(
            state.get("positionSeconds"), state.get("durationSeconds")
        )
        if self.time_label.GetLabel() != time_label:
            self.time_label.SetLabel(time_label)
        volume = int(state.get("volume") or 0)
        if self.volume_slider.GetValue() != volume:
            self.volume_slider.SetValue(volume)
        self.volume_slider.Enable(True)
        playback = str(state.get("playbackState") or "").casefold()
        self._set_transport_label(
            playing=playback in {"odtwarzanie", "playing", "play"}
        )
        if announce:
            message = str(state.get("message") or "").strip()
            self.announcer.say(message or label)

    def _wiim_transport(
        self, command: str, *, volume: int | None = None
    ) -> None:
        client = self.client
        device_id = self._wiim_active_device_id
        if client is None or not device_id:
            self.announcer.say(
                "Brak aktywnego urządzenia WiiM. Naciśnij Enter na urządzeniu"
            )
            return

        def done(payload: object) -> None:
            try:
                state = wiim_snapshot(payload)
            except WiiMPayloadError as error:
                self.announcer.say(str(error))
                return
            if state.get("deviceId") != self._wiim_active_device_id:
                return
            self._wiim_snapshot = state
            if self.navigator.active is SessionId.WIIM:
                self._apply_wiim_snapshot(state, announce=True)

        self.runner.submit(
            "wiim-transport",
            lambda: client.wiim_transport(
                device_id, command, volume=volume
            ),
            done,
            lambda error: self.announcer.say(
                f"Nie udało się sterować urządzeniem WiiM: {error}"
            ),
        )

    def _navigate_wiim_source(self, direction: int) -> None:
        """Alt+Page Up/Down: ten sam zakres źródeł co w pełnym AMC."""
        client = self.client
        device_id = self._wiim_active_device_id
        if (
            client is None
            or not device_id
            or self.navigator.active is not SessionId.WIIM
            or self.navigator.view is not View.PLAYER
        ):
            self.announcer.say(
                "Przechodzenie po źródłach WiiM jest dostępne "
                "w odtwarzaczu urządzenia"
            )
            return

        def done(payload: object) -> None:
            try:
                state = wiim_snapshot(payload)
            except WiiMPayloadError as error:
                self.announcer.say(str(error))
                return
            if (
                self.navigator.active is not SessionId.WIIM
                or self.navigator.view is not View.PLAYER
                or state.get("deviceId") != self._wiim_active_device_id
            ):
                return
            self._wiim_snapshot = state
            self._apply_wiim_snapshot(state, announce=True)
            self.play_button.SetFocus()

        self.runner.submit(
            "wiim-source-navigation",
            lambda: client.wiim_navigate_source(device_id, direction),
            done,
            lambda error: self.announcer.say(str(error)),
        )

    # ---------------------------------------------------------------- Sonos

    def _load_sonos_targets(self, preferred_id: str | None = None) -> None:
        """Wczytaj grupy przez wspólny Core; token konta zostaje w C#."""
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie jest gotowy")
            return

        def done(payload: object) -> None:
            try:
                rows = list(sonos_target_rows(payload))
            except SonosPayloadError as error:
                self.announcer.say(str(error))
                return
            selected_id = preferred_id
            if self._sonos_active_group_id:
                active = next((
                    row.item_id for row in rows
                    if row.service_id == self._sonos_active_group_id
                    and row.parent_id == self._sonos_active_household_id
                ), None)
                selected_id = active or selected_id
            events = self.navigator.apply_sonos_targets(rows, selected_id)
            selected = self.navigator.sessions[SessionId.SONOS].model.selected_row
            if selected is not None and selected.parent_id:
                self._sonos_browse_household_id = selected.parent_id
            if self.navigator.active is SessionId.SONOS:
                self._run(events)
            else:
                self._sync_views()

        self.runner.submit(
            "sonos-targets",
            client.sonos_targets,
            done,
            lambda error: self.announcer.say(
                f"Nie udało się odczytać grup Sonos: {error}"
            ),
        )

    def _activate_sonos_group(
        self, intent: ActivateSonosGroup, *, attempt: int = 0
    ) -> None:
        client = self.client
        if client is None:
            self._run(self.navigator.back_to_list())
            self.announcer.say("Silnik nie jest gotowy")
            return
        self._sonos_active_household_id = intent.household_id
        self._sonos_active_group_id = intent.group_id
        self._sonos_browse_household_id = intent.household_id
        self._sonos_snapshot = {}
        self.now_playing.SetLabel(intent.title)
        self._set_transport_label(playing=False, preparing=True)
        if (
            getattr(self, "_sonos_request_pending", False)
            or getattr(self, "_sonos_retry_pending", False)
        ):
            # Użytkownik może wrócić na listę i wybrać inną grupę, gdy stary
            # odczyt jeszcze kończy się w chmurze. Nie uruchamiamy drugiego
            # równolegle; ostatni świadomy wybór wykona się zaraz po pierwszym.
            self._sonos_pending_activation = intent
            self._sonos_pending_material = None
            return
        self._sonos_request_pending = True

        def done(payload: object) -> None:
            try:
                state = sonos_snapshot(payload)
            except SonosPayloadError as error:
                failed(error)
                return
            if (
                state.get("householdId") != self._sonos_active_household_id
                or state.get("groupId") != self._sonos_active_group_id
            ):
                self._finish_sonos_request()
                return
            self._sonos_snapshot = state
            if (
                self.navigator.active is SessionId.SONOS
                and self.navigator.view is View.PLAYER
            ):
                self._apply_sonos_snapshot(state, announce=True)
            self._finish_sonos_request()
            if (
                self.navigator.active is SessionId.SONOS
                and intent.household_id == self._sonos_active_household_id
                and intent.group_id == self._sonos_active_group_id
            ):
                self._open_sonos_view(OpenSonosView(
                    LibraryView.SONOS_LIBRARY,
                    household_id=intent.household_id,
                    preferred_id=None,
                ))

        def failed(error: Exception) -> None:
            if (
                isinstance(error, HostError)
                and error.code == "operation_busy"
                and attempt < 20
                and intent.household_id == self._sonos_active_household_id
                and intent.group_id == self._sonos_active_group_id
                and self.navigator.active is SessionId.SONOS
            ):
                self._sonos_request_pending = False
                self._sonos_retry_pending = True

                def retry() -> None:
                    self._sonos_retry_pending = False
                    pending_activation = self._sonos_pending_activation
                    self._sonos_pending_activation = None
                    if pending_activation is not None:
                        self._activate_sonos_group(pending_activation)
                    elif (
                        intent.household_id == self._sonos_active_household_id
                        and intent.group_id == self._sonos_active_group_id
                        and self.navigator.active is SessionId.SONOS
                    ):
                        self._activate_sonos_group(intent, attempt=attempt + 1)
                    else:
                        self._start_next_sonos_command()

                call_later = getattr(wx, "CallLater", None)
                if callable(call_later):
                    call_later(250, retry)
                else:
                    retry()
                return
            if (
                intent.household_id == self._sonos_active_household_id
                and intent.group_id == self._sonos_active_group_id
            ):
                state = self.navigator.sessions[SessionId.SONOS]
                state.view = View.LIST
                if self.navigator.active is SessionId.SONOS:
                    self._sync_views()
                    self.announcer.say(str(error))
            self._finish_sonos_request()

        self.runner.submit(
            "sonos-snapshot",
            lambda: client.sonos_snapshot(intent.household_id, intent.group_id),
            done,
            failed,
        )

    def _apply_sonos_snapshot(
        self, state: dict, *, announce: bool = False
    ) -> None:
        """Pokaż tylko jawne etykiety stanu, bez identyfikatorów Sonosa."""
        label = sonos_now_playing_label(state)
        if self.now_playing.GetLabel() != label:
            self.now_playing.SetLabel(label)
        self.now_playing.SetName("Teraz odtwarzane")
        time_label = player_time_label(
            state.get("positionSeconds"), state.get("durationSeconds")
        )
        if self.time_label.GetLabel() != time_label:
            self.time_label.SetLabel(time_label)
        volume = state.get("volume")
        if isinstance(volume, int) and self.volume_slider.GetValue() != volume:
            self.volume_slider.SetValue(volume)
        self.volume_slider.Enable(
            isinstance(volume, int) and state.get("fixedVolume") is not True
        )
        playback = str(state.get("playbackState") or "").casefold()
        self._set_transport_label(
            playing=playback in {"odtwarzanie", "playing", "play"}
        )
        if announce:
            message = str(state.get("message") or "").strip()
            self.announcer.say(message or label)

    def _sonos_transport(
        self,
        command: str,
        *,
        volume: int | None = None,
        seconds: float | None = None,
    ) -> None:
        client = self.client
        household_id = self._sonos_active_household_id
        group_id = self._sonos_active_group_id
        if client is None or not household_id or not group_id:
            self.announcer.say(
                "Brak aktywnej grupy Sonos. Naciśnij Enter na grupie"
            )
            return

        self._sonos_command_queue.append((
            household_id,
            group_id,
            command,
            volume,
            seconds,
            0,
        ))
        self._start_next_sonos_command()

    def _start_next_sonos_command(self) -> None:
        """Uruchom pierwsze aktualne polecenie, nigdy równolegle z odczytem."""
        if (
            getattr(self, "_sonos_request_pending", False)
            or getattr(self, "_sonos_retry_pending", False)
        ):
            return
        client = self.client
        if client is None:
            self._sonos_command_queue.clear()
            return
        request = None
        while self._sonos_command_queue:
            candidate = self._sonos_command_queue.pop(0)
            household_id, group_id, _command, _volume, _seconds, _attempt = candidate
            if (
                self.navigator.active is SessionId.SONOS
                and household_id == self._sonos_active_household_id
                and group_id == self._sonos_active_group_id
            ):
                request = candidate
                break
        if request is None:
            return
        household_id, group_id, command, volume, seconds, attempt = request
        self._sonos_request_pending = True

        def done(payload: object) -> None:
            try:
                state = sonos_snapshot(payload)
            except SonosPayloadError as error:
                self.announcer.say(str(error))
                self._finish_sonos_request()
                return
            if (
                state.get("householdId") != self._sonos_active_household_id
                or state.get("groupId") != self._sonos_active_group_id
            ):
                self._finish_sonos_request()
                return
            self._sonos_snapshot = state
            if self.navigator.active is SessionId.SONOS:
                self._apply_sonos_snapshot(state, announce=True)
            self._finish_sonos_request()

        def failed(error: Exception) -> None:
            if (
                isinstance(error, HostError)
                and error.code == "operation_busy"
                and attempt < 20
                and household_id == self._sonos_active_household_id
                and group_id == self._sonos_active_group_id
                and self.navigator.active is SessionId.SONOS
            ):
                self._sonos_request_pending = False
                self._sonos_retry_pending = True
                self._sonos_command_queue.insert(0, (
                    household_id,
                    group_id,
                    command,
                    volume,
                    seconds,
                    attempt + 1,
                ))

                def retry() -> None:
                    self._sonos_retry_pending = False
                    # W czasie oczekiwania użytkownik mógł świadomie wybrać
                    # inną grupę. Ostatni wybór ma pierwszeństwo przed
                    # ponowieniem starego polecenia.
                    self._finish_sonos_request()

                call_later = getattr(wx, "CallLater", None)
                if callable(call_later):
                    call_later(250, retry)
                else:
                    retry()
                return
            self.announcer.say(
                f"Nie udało się sterować grupą Sonos: {error}"
            )
            self._finish_sonos_request()

        self.runner.submit(
            "sonos-transport",
            lambda: client.sonos_transport(
                household_id,
                group_id,
                command,
                volume=volume,
                seconds=seconds,
            ),
            done,
            failed,
        )

    def _finish_sonos_request(self) -> None:
        """Zwolnij tor Sonosa i wykonaj ostatni wybór albo czekające polecenie."""
        self._sonos_request_pending = False
        pending_activation = self._sonos_pending_activation
        self._sonos_pending_activation = None
        if pending_activation is not None:
            self._activate_sonos_group(pending_activation)
            return
        pending_material = getattr(self, "_sonos_pending_material", None)
        self._sonos_pending_material = None
        if pending_material is not None:
            self._play_sonos_material(pending_material)
            return
        self._start_next_sonos_command()

    def _sonos_content_household_id(self) -> str:
        """Dom do odczytu treści, nigdy tekst pokazywany użytkownikowi."""
        if self._sonos_active_household_id:
            return self._sonos_active_household_id
        state = self.navigator.sessions[SessionId.SONOS]
        row = state.model.selected_row
        if row is not None and row.parent_id:
            return row.parent_id
        if state.library_item_id:
            return state.library_item_id
        return self._sonos_browse_household_id

    def _open_sonos_view(
        self,
        intent: OpenSonosView,
        *,
        announcement: str | None = None,
    ) -> None:
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie jest gotowy")
            return
        household_id = intent.household_id or self._sonos_content_household_id()
        if not household_id:
            self.announcer.say(
                "Najpierw wybierz grupę Sonos skrótem Control F5"
            )
            self._load_sonos_targets()
            return
        self._sonos_browse_household_id = household_id
        if intent.view is not LibraryView.SONOS_OWN_STREAMS:
            self._sonos_pending_move_ids = []
        self._sonos_content_version += 1
        version = self._sonos_content_version
        state = self.navigator.sessions[SessionId.SONOS]
        return_id = (
            state.model.selected_id
            if state.library_view is LibraryView.SONOS_LIBRARY
            else state.library_return_id
        )

        if intent.view is LibraryView.SONOS_LIBRARY:
            work = client.sonos_library
        elif intent.view is LibraryView.SONOS_FAVORITES:
            work = lambda: client.sonos_materials(household_id, "favorite")
        elif intent.view is LibraryView.SONOS_PLAYLISTS:
            work = lambda: client.sonos_materials(household_id, "playlist")
        elif intent.view is LibraryView.SONOS_OWN_STREAMS:
            work = lambda: client.sonos_materials(household_id, "ownStream")
        else:
            self.announcer.say("Ten widok Sonosa nie jest jeszcze dostępny")
            return

        def done(payload: object) -> None:
            if version != self._sonos_content_version:
                return
            if (
                intent.view is LibraryView.SONOS_OWN_STREAMS
                and isinstance(payload, dict)
            ):
                sort_mode = str(payload.get("sortMode") or "")
                if sort_mode in {
                    SORT_ADDED_NEWEST,
                    SORT_ALPHABETICAL,
                    SORT_CUSTOM,
                }:
                    self._sonos_own_stream_sort_mode = sort_mode
            try:
                if intent.view is LibraryView.SONOS_LIBRARY:
                    rows = list(sonos_library_rows(payload, household_id))
                    events = self.navigator.apply_sonos_library(
                        rows,
                        household_id=household_id,
                        preferred_id=intent.preferred_id or return_id,
                    )
                else:
                    rows = list(sonos_material_rows(payload, household_id))
                    events = self.navigator.apply_sonos_materials(
                        intent.view,
                        rows,
                        household_id=household_id,
                        preferred_id=intent.preferred_id,
                        return_id=return_id,
                    )
            except SonosPayloadError as error:
                self.announcer.say(str(error))
                return
            if self.navigator.active is SessionId.SONOS:
                self._run(events)
                if intent.view is not LibraryView.SONOS_LIBRARY:
                    message = announcement or sonos_response_message(payload)
                    self.announcer.say(message or (
                        "Zero elementów" if not rows else "Lista Sonos"
                    ))
            else:
                self._sync_views()

        def failed(error: Exception) -> None:
            if version == self._sonos_content_version:
                self.announcer.say(
                    f"Nie udało się odczytać Biblioteki Sonos: {error}"
                )

        self.runner.submit(
            "sonos-library",
            work,
            done,
            failed,
        )

    def _selected_sonos_own_stream_rows(self) -> list[Row]:
        """Zwróć lokalne stacje AMC, nigdy ulubione ani playlisty Sonosa."""
        if (
            self.navigator.active is not SessionId.SONOS
            or self.navigator.session.library_view
            is not LibraryView.SONOS_OWN_STREAMS
        ):
            return []
        return [
            row for row in self._selected_action_rows()
            if row.kind == "sonosOwnStream"
            and row.service_kind == "ownStream"
            and bool(row.service_id)
        ]

    def _reload_sonos_own_streams(
        self,
        *,
        preferred_stream_id: str | None = None,
        announcement: str | None = None,
    ) -> None:
        household_id = self._sonos_content_household_id()
        if not household_id:
            self.announcer.say(
                "Najpierw wybierz grupę Sonos skrótem Control F5"
            )
            return
        self._open_sonos_view(
            OpenSonosView(
                LibraryView.SONOS_OWN_STREAMS,
                household_id=household_id,
                preferred_id=(
                    f"sonos-stream:{preferred_stream_id}"
                    if preferred_stream_id else None
                ),
            ),
            announcement=announcement,
        )

    def _add_sonos_own_stream(self) -> None:
        client = self._profile_edit_client()
        if client is None:
            return
        if self.navigator.session.library_view is not LibraryView.SONOS_OWN_STREAMS:
            self.announcer.say("Otwórz kategorię Moje stacje Sonosa")
            return
        with StationDialog(
            self,
            "Dodaj stację Sonos",
            network_stream=True,
        ) as dialog:
            if dialog.ShowModal() != wx.ID_OK:
                self._restore_focus_after_dialog()
                return
            name, url = dialog.values

        def done(payload: object) -> None:
            result = payload if isinstance(payload, dict) else {}
            preferred = str(result.get("preferredStreamId") or "") or None
            message = str(result.get("message") or f"Dodano stację Sonos: {name}")
            self._reload_sonos_own_streams(
                preferred_stream_id=preferred,
                announcement=message,
            )

        self.runner.submit(
            "sonos-own-stream-edit",
            lambda: client.sonos_add_own_stream(name, url),
            done,
            lambda error: self.announcer.say(
                f"Nie dodano stacji Sonos: {error}"
            ),
        )

    def _edit_sonos_own_stream(self) -> None:
        rows = self._selected_sonos_own_stream_rows()
        if len(rows) != 1:
            self.announcer.say("Do edycji wybierz jedną stację Sonos")
            return
        client = self._profile_edit_client()
        if client is None:
            return
        stream_id = rows[0].service_id or ""

        def loaded(payload: object) -> None:
            try:
                loaded_id, current_name, current_url = (
                    sonos_own_stream_edit_info(payload)
                )
            except SonosPayloadError as error:
                self.announcer.say(str(error))
                return
            with StationDialog(
                self,
                "Edytuj stację Sonos",
                current_name,
                current_url,
                network_stream=True,
            ) as dialog:
                if dialog.ShowModal() != wx.ID_OK:
                    self._restore_focus_after_dialog()
                    return
                name, url = dialog.values

            def saved(result_payload: object) -> None:
                result = result_payload if isinstance(result_payload, dict) else {}
                preferred = str(result.get("preferredStreamId") or loaded_id)
                message = str(
                    result.get("message") or f"Zapisano stację Sonos: {name}"
                )
                self._reload_sonos_own_streams(
                    preferred_stream_id=preferred,
                    announcement=message,
                )

            self.runner.submit(
                "sonos-own-stream-edit",
                lambda: client.sonos_edit_own_stream(
                    loaded_id, name, url
                ),
                saved,
                lambda error: self.announcer.say(
                    f"Nie zapisano stacji Sonos: {error}"
                ),
            )

        self.runner.submit(
            "sonos-own-stream-edit-info",
            lambda: client.sonos_own_stream_edit_info(stream_id),
            loaded,
            lambda error: self.announcer.say(
                f"Nie odczytano stacji Sonos: {error}"
            ),
        )

    def _remove_sonos_own_streams(self) -> None:
        rows = self._selected_sonos_own_stream_rows()
        if not rows:
            self.announcer.say("Wybierz stację Sonos do usunięcia")
            return
        client = self._profile_edit_client()
        if client is None:
            return
        prompt = (
            f"Usunąć stację {rows[0].title} z AMC? "
            "Ulubione i playlisty na koncie Sonos pozostaną bez zmian."
            if len(rows) == 1 else
            f"Usunąć wybrane stacje z AMC: {len(rows)}? "
            "Ulubione i playlisty na koncie Sonos pozostaną bez zmian."
        )
        if wx.MessageBox(
            prompt,
            "Potwierdzenie",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
            self,
        ) != wx.YES:
            self._restore_focus_after_dialog()
            return
        stream_ids = [row.service_id for row in rows if row.service_id]

        def done(payload: object) -> None:
            result = payload if isinstance(payload, dict) else {}
            removed = set(stream_ids)
            self._sonos_pending_move_ids = [
                stream_id for stream_id in self._sonos_pending_move_ids
                if stream_id not in removed
            ]
            message = str(
                result.get("message")
                or f"Usunięto stacje Sonos: {len(stream_ids)}"
            )
            self._reload_sonos_own_streams(announcement=message)

        self.runner.submit(
            "sonos-own-stream-edit",
            lambda: client.sonos_remove_own_streams(stream_ids),
            done,
            lambda error: self.announcer.say(
                f"Nie usunięto stacji Sonos: {error}"
            ),
        )

    def _import_sonos_own_streams(self) -> None:
        client = self._profile_edit_client()
        if client is None:
            return
        if self.navigator.session.library_view is not LibraryView.SONOS_OWN_STREAMS:
            self.announcer.say("Otwórz kategorię Moje stacje Sonosa")
            return
        with wx.FileDialog(
            self,
            "Importuj playlistę do Moich stacji Sonosa",
            wildcard=(
                "Playlisty (*.m3u;*.m3u8;*.pls)|*.m3u;*.m3u8;*.pls|"
                "Wszystkie pliki (*.*)|*.*"
            ),
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as dialog:
            if dialog.ShowModal() != wx.ID_OK:
                self._restore_focus_after_dialog()
                return
            path = dialog.GetPath()

        def done(payload: object) -> None:
            result = payload if isinstance(payload, dict) else {}
            preferred = str(result.get("preferredStreamId") or "") or None
            message = str(
                result.get("message") or "Zakończono import stacji Sonos"
            )
            self._reload_sonos_own_streams(
                preferred_stream_id=preferred,
                announcement=message,
            )

        self.runner.submit(
            "sonos-own-stream-import",
            lambda: client.sonos_import_own_streams(path),
            done,
            lambda error: self.announcer.say(
                f"Nie można zaimportować playlisty: {error}"
            ),
        )

    def _set_sonos_own_stream_sort(self, action: Action) -> None:
        modes = {
            Action.SORT_SONOS_OWN_STREAMS_ADDED: SORT_ADDED_NEWEST,
            Action.SORT_SONOS_OWN_STREAMS_ALPHABETICAL: SORT_ALPHABETICAL,
            Action.SORT_SONOS_OWN_STREAMS_CUSTOM: SORT_CUSTOM,
        }
        mode = modes[action]
        client = self._profile_edit_client()
        if client is None:
            return
        selected = next(iter(self._selected_sonos_own_stream_rows()), None)
        preferred = selected.service_id if selected is not None else None

        def done(payload: object) -> None:
            result = payload if isinstance(payload, dict) else {}
            self._sonos_own_stream_sort_mode = mode
            if mode != SORT_CUSTOM:
                self._sonos_pending_move_ids = []
            message = str(
                result.get("message") or "Zmieniono kolejność stacji Sonos"
            )
            self._reload_sonos_own_streams(
                preferred_stream_id=preferred,
                announcement=message,
            )

        self.runner.submit(
            "sonos-own-stream-sort",
            lambda: client.sonos_sort_own_streams(mode),
            done,
            lambda error: self.announcer.say(
                f"Nie zapisano kolejności stacji Sonos: {error}"
            ),
        )

    def _move_sonos_own_streams(self, direction: int) -> None:
        if self._sonos_own_stream_sort_mode != SORT_CUSTOM:
            self.announcer.say(
                "Przenoszenie działa w kolejności własnej. Naciśnij Alt 3"
            )
            return
        rows = self._selected_sonos_own_stream_rows()
        if not rows:
            self.announcer.say("Najpierw wybierz stację")
            return
        client = self._profile_edit_client()
        if client is None:
            return
        stream_ids = [row.service_id for row in rows if row.service_id]

        def done(payload: object) -> None:
            result = payload if isinstance(payload, dict) else {}
            preferred = str(result.get("preferredStreamId") or "") or None
            message = str(result.get("message") or "Przeniesiono stację Sonos")
            self._reload_sonos_own_streams(
                preferred_stream_id=preferred,
                announcement=message,
            )

        self.runner.submit(
            "sonos-own-stream-order",
            lambda: client.sonos_move_own_streams(stream_ids, direction),
            done,
            lambda error: self.announcer.say(str(error)),
        )

    def _cut_sonos_own_streams(self) -> None:
        if self._sonos_own_stream_sort_mode != SORT_CUSTOM:
            self.announcer.say(
                "Przenoszenie działa w kolejności własnej. Naciśnij Alt 3"
            )
            return
        rows = self._selected_sonos_own_stream_rows()
        if not rows:
            self.announcer.say("Najpierw wybierz stację")
            return
        self._sonos_pending_move_ids = [
            row.service_id for row in rows if row.service_id
        ]
        self.announcer.say(
            "Zaznaczono stację do przeniesienia. "
            "Wybierz miejsce i naciśnij Control V"
            if len(self._sonos_pending_move_ids) == 1 else
            f"Zaznaczono {len(self._sonos_pending_move_ids)} stacji do "
            "przeniesienia. Wybierz miejsce i naciśnij Control V"
        )

    def _paste_sonos_own_streams(self) -> None:
        if self._sonos_own_stream_sort_mode != SORT_CUSTOM:
            self.announcer.say(
                "Przenoszenie działa w kolejności własnej. Naciśnij Alt 3"
            )
            return
        if not self._sonos_pending_move_ids:
            self.announcer.say(
                "Najpierw naciśnij Control X na stacji do przeniesienia"
            )
            return
        target = next(iter(self._selected_sonos_own_stream_rows()), None)
        if target is None or not target.service_id:
            self.announcer.say("Nie wybrano miejsca docelowego")
            return
        client = self._profile_edit_client()
        if client is None:
            return
        pending = list(self._sonos_pending_move_ids)

        def done(payload: object) -> None:
            result = payload if isinstance(payload, dict) else {}
            preferred = str(result.get("preferredStreamId") or "") or None
            message = str(result.get("message") or "Przeniesiono stacje Sonos")
            self._sonos_pending_move_ids = []
            self._reload_sonos_own_streams(
                preferred_stream_id=preferred,
                announcement=message,
            )

        self.runner.submit(
            "sonos-own-stream-order",
            lambda: client.sonos_place_own_streams(
                pending, target.service_id or ""
            ),
            done,
            lambda error: self.announcer.say(str(error)),
        )

    def _export_sonos_own_streams(self) -> None:
        client = self._profile_edit_client()
        if client is None:
            return
        if self.navigator.session.library_view is not LibraryView.SONOS_OWN_STREAMS:
            self.announcer.say("Otwórz kategorię Moje stacje Sonosa")
            return
        with wx.FileDialog(
            self,
            "Eksportuj Moje stacje Sonosa",
            defaultFile="Moje stacje Sonosa AMC.m3u",
            wildcard="Playlisty M3U (*.m3u)|*.m3u|Wszystkie pliki (*.*)|*.*",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as dialog:
            if dialog.ShowModal() != wx.ID_OK:
                self._restore_focus_after_dialog()
                return
            path = str(Path(dialog.GetPath()).with_suffix(".m3u"))

        def done(payload: object) -> None:
            result = payload if isinstance(payload, dict) else {}
            count = int(result.get("exportedCount") or 0)
            self.announcer.say(f"Wyeksportowano stacje Sonos: {count}")
            self._restore_focus_after_dialog()

        self.runner.submit(
            "sonos-own-stream-export",
            lambda: client.sonos_export_own_streams(path),
            done,
            lambda error: self.announcer.say(
                f"Nie można zapisać playlisty: {error}"
            ),
        )

    def _play_sonos_material(
        self, intent: PlaySonosMaterial, *, attempt: int = 0
    ) -> None:
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie jest gotowy")
            return
        if self.navigator.active is not SessionId.SONOS:
            return
        if (
            not self._sonos_active_group_id
            or self._sonos_active_household_id != intent.household_id
        ):
            self.announcer.say(
                "Wybierz grupę Sonos skrótem Control F5, a potem uruchom materiał ponownie"
            )
            return
        if self._sonos_request_pending or self._sonos_retry_pending:
            self._sonos_pending_material = intent
            return

        household_id = self._sonos_active_household_id
        group_id = self._sonos_active_group_id
        self._sonos_request_pending = True

        def done(payload: object) -> None:
            try:
                state = sonos_snapshot(payload)
            except SonosPayloadError as error:
                failed(error)
                return
            if (
                household_id != self._sonos_active_household_id
                or group_id != self._sonos_active_group_id
            ):
                self._finish_sonos_request()
                return
            session = self.navigator.sessions[SessionId.SONOS]
            session.now_playing_id = intent.item_id
            session.now_playing_title = intent.title
            session.current_material_id = intent.item_id
            self._sonos_snapshot = state
            if self.navigator.active is SessionId.SONOS:
                state["message"] = intent.title
                self._apply_sonos_snapshot(state, announce=True)
            self._finish_sonos_request()

        def failed(error: Exception) -> None:
            if (
                isinstance(error, HostError)
                and error.code == "operation_busy"
                and attempt < 20
                and household_id == self._sonos_active_household_id
                and group_id == self._sonos_active_group_id
            ):
                self._sonos_request_pending = False
                self._sonos_retry_pending = True

                def retry() -> None:
                    self._sonos_retry_pending = False
                    self._play_sonos_material(intent, attempt=attempt + 1)

                call_later = getattr(wx, "CallLater", None)
                if callable(call_later):
                    call_later(250, retry)
                else:
                    retry()
                return
            self.announcer.say(f"Nie udało się uruchomić materiału Sonos: {error}")
            session = self.navigator.sessions[SessionId.SONOS]
            if (
                self.navigator.active is SessionId.SONOS
                and session.view is View.PLAYER
                and session.now_playing_id == intent.item_id
            ):
                session.view = View.LIST
                self._sync_views()
            self._finish_sonos_request()

        self.runner.submit(
            "sonos-material",
            lambda: client.sonos_load_material(
                household_id,
                group_id,
                intent.kind,
                intent.material_id,
            ),
            done,
            failed,
        )

    # ------------------------------------------------ Podcasty i YouTube

    def _apply_podcast_result(self, events: list[object]) -> None:
        """Apply data silently when its session is no longer on screen."""
        if self.navigator.active is SessionId.PODCASTS:
            self._run(events)
        else:
            self._sync_views()

    def _open_podcast_library(
        self,
        preferred_id: str | None = None,
        *,
        completion_message: str = "",
        after_refresh: Callable[[], None] | None = None,
    ) -> None:
        """Load the shared AMC podcast/channel library outside the GUI thread."""
        if not self.podcasts.is_available:
            if self.navigator.active is SessionId.PODCASTS:
                self.announcer.say("Nie znaleziono biblioteki podcastów AMC")
            return

        def work():
            return self.podcasts.subscriptions()

        def done(subscriptions) -> None:
            if completion_message:
                state = self.navigator.sessions[SessionId.PODCASTS]
                if (
                    self.navigator.active is not SessionId.PODCASTS
                    or state.view is not View.LIST
                    or state.library_view is not LibraryView.PODCAST_LIBRARY
                ):
                    return
            events = self.navigator.apply_podcast_library(
                subscription_rows(subscriptions), preferred_id=preferred_id
            )
            if completion_message:
                self._sync_views()
                self.announcer.say(completion_message)
            else:
                self._apply_podcast_result(events)
            if after_refresh is not None:
                after_refresh()

        def failed(error: Exception) -> None:
            if self.navigator.active is SessionId.PODCASTS:
                self.announcer.say(str(error) if isinstance(error, PodcastProfileError)
                                   else "Nie udało się odczytać biblioteki podcastów")

        self.runner.submit("podcast-view", work, done, failed)

    def _open_podcast_view(
        self,
        intent: OpenPodcastView,
        *,
        completion_message: str = "",
        after_refresh: Callable[[], None] | None = None,
    ) -> None:
        if not intent.subscription_id:
            self._open_podcast_library(
                preferred_id=intent.preferred_id,
                completion_message=completion_message,
                after_refresh=after_refresh,
            )
            return

        subscription_id = intent.subscription_id
        previous_count = self._podcast_loaded_counts.get(subscription_id, 0)
        requested = requested_count(
            previous_count,
            load_more=intent.load_more,
            page_size=PODCAST_PAGE_SIZE,
        )

        def work():
            subscription = self.podcasts.subscription(subscription_id)
            if subscription is None:
                raise PodcastProfileError("Tego podcastu nie ma już w Bibliotece.")
            page = self.podcasts.episodes(subscription_id, loaded_count=requested)
            return subscription, page

        def done(result) -> None:
            if completion_message:
                state = self.navigator.sessions[SessionId.PODCASTS]
                if (
                    self.navigator.active is not SessionId.PODCASTS
                    or state.view is not View.LIST
                    or state.library_view is not LibraryView.PODCAST_EPISODES
                    or state.library_playlist_id != subscription_id
                ):
                    return
            subscription, page = result
            self._podcast_loaded_counts[subscription_id] = page.loaded_count
            preferred = intent.preferred_id
            if intent.load_more and previous_count < len(page.rows):
                candidate = page.rows[previous_count]
                if candidate.kind == "episode":
                    preferred = candidate.item_id
            events = self.navigator.apply_podcast_episodes(
                subscription_id,
                subscription.title,
                page.rows,
                preferred_id=preferred,
            )
            if completion_message:
                self._sync_views()
                self.announcer.say(completion_message)
            else:
                self._apply_podcast_result(events)
            if after_refresh is not None:
                after_refresh()

        def failed(error: Exception) -> None:
            if self.navigator.active is SessionId.PODCASTS:
                self.announcer.say(str(error) if isinstance(error, PodcastProfileError)
                                   else "Nie udało się odczytać odcinków")

        self.runner.submit("podcast-view", work, done, failed)

    def _show_podcast_inbox(self) -> None:
        """Ctrl+I: global preview that Escape restores exactly."""
        self._begin_transient_preview()
        self.navigator.active = SessionId.PODCASTS
        # Oznaczamy widok od razu, zanim watek SQLite odda dane. Escape ma
        # dzialac takze podczas wczytywania, a spozniony wynik po Escape nie
        # moze ponownie otworzyc podgladu.
        podcast_state = self.navigator.sessions[SessionId.PODCASTS]
        podcast_state.library_view = LibraryView.PODCAST_INBOX
        podcast_state.view = View.LIST
        self._open_podcast_aggregate(
            OpenPodcastAggregateView(LibraryView.PODCAST_INBOX)
        )

    def _show_podcast_downloads(self) -> None:
        if self.navigator.active is not SessionId.PODCASTS:
            self.announcer.say(
                "Pobrane odcinki są dostępne w sesji Podcasty i YouTube"
            )
            return
        self._transient_preview_return = None
        self._open_podcast_aggregate(
            OpenPodcastAggregateView(LibraryView.PODCAST_DOWNLOADS)
        )

    def _set_podcast_inbox_sort(self, action: Action) -> None:
        """Alt+1/2/3 in the podcast inbox, with a private durable choice."""
        state = self.navigator.sessions[SessionId.PODCASTS]
        if (
            self.navigator.active is not SessionId.PODCASTS
            or state.view is not View.LIST
            or state.library_view is not LibraryView.PODCAST_INBOX
        ):
            self.announcer.say(
                "Sortowanie Alt+1, Alt+2 i Alt+3 działa w Nowych odcinkach"
            )
            return

        choices = {
            Action.SORT_PODCAST_INBOX_ADDED: (
                SORT_ADDED_NEWEST,
                "Według dodania, najnowsze na początku",
            ),
            Action.SORT_PODCAST_INBOX_ALPHABETICAL: (
                SORT_ALPHABETICAL,
                "Alfabetycznie",
            ),
            Action.SORT_PODCAST_INBOX_BY_PODCAST: (
                SORT_CUSTOM,
                "Według podcastu",
            ),
        }
        choice = choices.get(action)
        if choice is None:
            return
        mode, label = choice
        previous_override = self.state.podcast_inbox_sort_mode
        previous_effective = self._podcast_inbox_sort_mode
        self.state.podcast_inbox_sort_mode = mode
        self._podcast_inbox_sort_mode = mode
        if not self._save_state():
            self.state.podcast_inbox_sort_mode = previous_override
            self._podcast_inbox_sort_mode = previous_effective
            self._refresh_menu_state()
            return

        self._refresh_menu_state()
        self._open_podcast_aggregate(OpenPodcastAggregateView(
            LibraryView.PODCAST_INBOX,
            preferred_id=state.model.selected_id,
            announcement=label,
        ))

    def _set_tidal_collection_sort(self, action: Action) -> None:
        """Alt+1/2/3 for one TIDAL root, stored outside the shared profile."""
        state = self.navigator.sessions[SessionId.TIDAL]
        scopes = {
            LibraryView.TIDAL_LIBRARY: TIDAL_VIEW_LIBRARY,
            LibraryView.TIDAL_FAVORITES: TIDAL_VIEW_FAVORITES,
            LibraryView.TIDAL_PLAYLISTS: TIDAL_VIEW_PLAYLISTS,
        }
        scope = scopes.get(state.library_view)
        if (
            self.navigator.active is not SessionId.TIDAL
            or state.view is not View.LIST
            or scope is None
        ):
            self.announcer.say(
                "Sortowanie Alt+1, Alt+2 i Alt+3 działa w Bibliotece, "
                "Ulubionych i Playlistach TIDAL"
            )
            return

        choices = {
            Action.SORT_TIDAL_COLLECTION_ADDED: (
                SORT_ADDED_NEWEST,
                "Według dodania, najnowsze na początku",
            ),
            Action.SORT_TIDAL_COLLECTION_ALPHABETICAL: (
                SORT_ALPHABETICAL,
                "Alfabetycznie",
            ),
            Action.SORT_TIDAL_COLLECTION_CUSTOM: (
                SORT_CUSTOM,
                "Kolejność własna",
            ),
        }
        choice = choices.get(action)
        if choice is None:
            return
        mode, label = choice
        previous_modes = dict(self.state.tidal_sort_modes)
        previous_effective = self._tidal_effective_sort_modes.get(scope)
        self.state.tidal_sort_modes[scope] = mode
        self._tidal_effective_sort_modes[scope] = mode
        if not self._save_state():
            self.state.tidal_sort_modes = previous_modes
            if previous_effective is None:
                self._tidal_effective_sort_modes.pop(scope, None)
            else:
                self._tidal_effective_sort_modes[scope] = previous_effective
            self._refresh_menu_state()
            return

        self._refresh_menu_state()
        self._open_tidal_view(OpenTidalView(
            state.library_view,
            preferred_id=state.model.selected_id,
            announcement=label,
        ))

    def _set_spotify_collection_sort(self, action: Action) -> None:
        """Alt+1/2/3 for a named Spotify collection, outside nested items."""

        state = self.navigator.sessions[SessionId.SPOTIFY]
        context = state.spotify_context
        if (
            self.navigator.active is not SessionId.SPOTIFY
            or state.view is not View.LIST
            or not isinstance(context, OpenSpotifyCollectionView)
        ):
            self.announcer.say(
                "Sortowanie Alt+1, Alt+2 i Alt+3 działa w głównych "
                "kolekcjach Spotify"
            )
            return

        choices = {
            Action.SORT_SPOTIFY_COLLECTION_ADDED: (
                SORT_ADDED_NEWEST,
                "Według dodania, najnowsze na początku",
            ),
            Action.SORT_SPOTIFY_COLLECTION_ALPHABETICAL: (
                SORT_ALPHABETICAL,
                "Alfabetycznie",
            ),
            Action.SORT_SPOTIFY_COLLECTION_CATALOG: (
                SORT_CUSTOM,
                "Kolejność katalogu Spotify",
            ),
        }
        choice = choices.get(action)
        if choice is None:
            return
        mode, label = choice
        scope = context.view
        previous_modes = dict(self.state.spotify_sort_modes)
        previous_effective = self._spotify_effective_sort_modes.get(scope)
        self.state.spotify_sort_modes[scope] = mode
        self._spotify_effective_sort_modes[scope] = mode
        if not self._save_state():
            self.state.spotify_sort_modes = previous_modes
            if previous_effective is None:
                self._spotify_effective_sort_modes.pop(scope, None)
            else:
                self._spotify_effective_sort_modes[scope] = previous_effective
            self._refresh_menu_state()
            return

        # Nowy porządek musi zacząć od pierwszej porcji. Host sortuje pełną
        # kolekcję PRZED stronicowaniem, więc kolejne „Załaduj więcej” pozostaje
        # stabilne i nie dubluje pozycji z poprzedniego układu.
        self._spotify_loaded_counts.pop(scope, None)
        self._refresh_menu_state()
        self.announcer.say(label)
        self._open_spotify_collection_view(OpenSpotifyCollectionView(
            context.item_id,
            scope,
            context.title,
            preferred_id=state.model.selected_id,
            replace_current=True,
        ))

    def _open_podcast_aggregate(
        self,
        intent: OpenPodcastAggregateView,
        *,
        completion_message: str = "",
    ) -> None:
        if intent.view not in (
            LibraryView.PODCAST_FAVORITES,
            LibraryView.PODCAST_HISTORY,
            LibraryView.PODCAST_QUEUE,
            LibraryView.PODCAST_INBOX,
            LibraryView.PODCAST_DOWNLOADS,
        ):
            return
        if not self.podcasts.is_available:
            self._restore_transient_preview(announce=False, force=True)
            self.announcer.say("Nie znaleziono biblioteki podcastów AMC")
            return

        key = intent.view.value
        previous_count = self._podcast_loaded_counts.get(key, 0)
        requested = requested_count(
            previous_count,
            load_more=intent.load_more,
            page_size=PODCAST_PAGE_SIZE,
        )
        sort_mode_override = self.state.podcast_inbox_sort_mode

        def work():
            if intent.view is LibraryView.PODCAST_FAVORITES:
                return self.podcasts.favorites(
                    loaded_count=requested,
                    collation=getattr(self, "_collation", None),
                )
            if intent.view is LibraryView.PODCAST_HISTORY:
                return self.podcasts.history(loaded_count=requested)
            if intent.view is LibraryView.PODCAST_QUEUE:
                return self.podcasts.queue(loaded_count=requested)
            if intent.view is LibraryView.PODCAST_INBOX:
                return self.podcasts.inbox(
                    loaded_count=requested,
                    sort_mode=sort_mode_override,
                    collation=getattr(self, "_collation", None),
                )
            return self.podcasts.downloads(loaded_count=requested)

        def done(page) -> None:
            if (
                intent.view is LibraryView.PODCAST_INBOX
                and self._transient_preview_return is None
            ):
                return
            if completion_message:
                state = self.navigator.sessions[SessionId.PODCASTS]
                if (
                    self.navigator.active is not SessionId.PODCASTS
                    or state.view is not View.LIST
                    or state.library_view is not intent.view
                ):
                    return
            self._podcast_loaded_counts[key] = page.loaded_count
            if (
                intent.view is LibraryView.PODCAST_INBOX
                and page.sort_mode in (
                    SORT_ADDED_NEWEST,
                    SORT_ALPHABETICAL,
                    SORT_CUSTOM,
                )
            ):
                self._podcast_inbox_sort_mode = page.sort_mode
            preferred = intent.preferred_id
            if intent.load_more and previous_count < len(page.rows):
                candidate = page.rows[previous_count]
                if candidate.kind in ("podcast", "episode"):
                    preferred = candidate.item_id
            heading = {
                LibraryView.PODCAST_FAVORITES: "Ulubione",
                LibraryView.PODCAST_HISTORY: "Historia odtwarzania",
                LibraryView.PODCAST_QUEUE: "Kolejka",
                LibraryView.PODCAST_INBOX: "Nowe odcinki i materiały",
                LibraryView.PODCAST_DOWNLOADS: "Pobrane",
            }[intent.view]
            events = self.navigator.apply_podcast_aggregate(
                intent.view,
                heading,
                page.rows,
                preferred_id=preferred,
                order_matches_amc=page.order_matches_amc,
            )
            count = sum(
                1 for row in page.rows if row.kind in ("podcast", "episode")
            )
            if completion_message:
                # Wynik odswiezenia ma zastapic zwykly naglowek widoku. Lista
                # zostaje najpierw podmieniona, a czytnik dostaje jeden,
                # konkretny komunikat z licznikami -- rowniez gdy jest pusta.
                self._sync_views()
                self.announcer.say(completion_message)
            elif self.navigator.active is SessionId.PODCASTS and intent.announcement:
                # Przy zmianie porzadku najwazniejsza jest nowa wlasciwosc,
                # nie powtorny naglowek ani techniczna wartosc modelu.
                self._sync_views()
                if count:
                    self.announcer.say(intent.announcement)
                else:
                    message = next(
                        (event.text for event in events if isinstance(event, Announce)),
                        heading,
                    )
                    self.announcer.say(f"{intent.announcement}, {message}")
            elif self.navigator.active is SessionId.PODCASTS and count == 0:
                self._sync_views()
                message = next(
                    (event.text for event in events if isinstance(event, Announce)),
                    heading,
                )
                self._announce_after_native_list_update(message)
            else:
                self._apply_podcast_result(events)

        def failed(error: Exception) -> None:
            if (
                intent.view is LibraryView.PODCAST_INBOX
                and self._transient_preview_return is None
            ):
                return
            message = (
                str(error) if isinstance(error, PodcastProfileError)
                else "Nie udało się odczytać odcinków"
            )
            if intent.view is LibraryView.PODCAST_INBOX:
                self._restore_transient_preview(announce=False, force=True)
                self.announcer.say(message)
            elif self.navigator.active is SessionId.PODCASTS:
                self.announcer.say(message)

        self.runner.submit("podcast-view", work, done, failed)

    def _open_podcast_playlist_view(
        self,
        intent: OpenPodcastPlaylistView,
        *,
        restore_selected_ids: list[str] | None = None,
        after_refresh: Callable[[], None] | None = None,
    ) -> None:
        """Ctrl+P and one playlist, backed by the shared AMC profile."""

        if not self.podcasts.is_available:
            self.announcer.say("Nie znaleziono biblioteki podcastów AMC")
            return
        playlist_id = intent.playlist_id
        key = f"podcast-playlist:{playlist_id}" if playlist_id else "podcast-playlists"
        previous_count = self._podcast_loaded_counts.get(key, 0)
        requested = requested_count(
            previous_count,
            load_more=bool(playlist_id and intent.load_more),
            page_size=PODCAST_PAGE_SIZE,
        )

        def work():
            if playlist_id:
                return self.podcasts.playlist(
                    playlist_id,
                    loaded_count=requested,
                )
            return self.podcasts.playlists()

        def done(page) -> None:
            self._podcast_loaded_counts[key] = page.loaded_count
            if playlist_id:
                preferred = intent.preferred_id
                if intent.load_more and previous_count < len(page.rows):
                    candidate = page.rows[previous_count]
                    if candidate.kind == "episode":
                        preferred = candidate.item_id
                events = self.navigator.apply_podcast_playlist_contents(
                    playlist_id,
                    page.playlist_title or intent.playlist_title or "Playlista",
                    page.rows,
                    preferred_id=preferred,
                )
            else:
                events = self.navigator.apply_podcast_playlists(
                    page.rows,
                    preferred_id=intent.preferred_id,
                )
            if self.navigator.active is SessionId.PODCASTS:
                self._apply_podcast_result(events)
                if (
                    restore_selected_ids
                    and self.navigator.session.library_view
                    is LibraryView.PODCAST_PLAYLIST_CONTENTS
                    and self.navigator.session.library_playlist_id == playlist_id
                ):
                    self._active_list().select_item_ids(restore_selected_ids)
                if after_refresh is not None:
                    after_refresh()

        def failed(error: Exception) -> None:
            if self.navigator.active is not SessionId.PODCASTS:
                return
            if after_refresh is not None:
                after_refresh()
            self.announcer.say(
                str(error) if isinstance(error, PodcastProfileError)
                else "Nie udało się odczytać playlist podcastów"
            )

        self.runner.submit("podcast-playlists", work, done, failed)

    def _current_podcast_subscription_id(self) -> str | None:
        """Zrodlo dla F5 bez ujawniania technicznego identyfikatora w UI."""
        state = self.navigator.sessions[SessionId.PODCASTS]
        if state.library_view is LibraryView.PODCAST_EPISODES:
            return state.library_playlist_id
        row = state.model.selected_row
        if state.library_view is LibraryView.PODCAST_LIBRARY:
            return row.item_id if row is not None and row.kind == "podcast" else None
        if row is not None and row.kind == "episode":
            return row.parent_id
        return None

    def _add_podcast_source(self) -> None:
        """Ctrl+N: dodaj RSS, kolekcję YouTube albo publiczne medium."""
        if self.navigator.active is not SessionId.PODCASTS:
            self.announcer.say(
                "Dodawanie źródła jest dostępne w sesji Podcasty i YouTube"
            )
            return
        if self._podcast_add_pending:
            self.announcer.say("Dodawanie źródła już trwa")
            return
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie działa, nie mogę dodać źródła")
            return

        with PodcastSourceDialog(self) as dialog:
            if dialog.ShowModal() != wx.ID_OK:
                return
            address, title = dialog.values
        if not address:
            self.announcer.say("Wpisz adres źródła")
            return

        self._podcast_add_pending = True
        started = "Sprawdzanie i dodawanie źródła"
        self.status_field.SetLabel(started)
        self.status_bar.show(started)
        self.announcer.say(started)

        def work() -> dict:
            result = client.add_podcast_source(address, title)
            return result if isinstance(result, dict) else {}

        def done(payload: dict) -> None:
            self._podcast_add_pending = False
            source_title = str(payload.get("title") or title or "źródło").strip()
            source_label = str(payload.get("sourceLabel") or "źródło").strip()
            count = max(0, int(payload.get("itemCount") or 0))
            if bool(payload.get("added")):
                change = "Dodano"
            elif bool(payload.get("restored")):
                change = "Ponownie dodano"
            else:
                change = "Zaktualizowano"
            message = (
                f"{change}: {source_label}: {source_title}. "
                f"Pozycji: {count}"
            )
            self.status_field.SetLabel(message)
            self.status_bar.show(message)

            subscription_id = str(payload.get("subscriptionId") or "").strip()
            state = self.navigator.sessions[SessionId.PODCASTS]
            if (
                subscription_id
                and self.navigator.active is SessionId.PODCASTS
                and state.view is View.LIST
                and state.library_view is LibraryView.PODCAST_LIBRARY
            ):
                self._open_podcast_library(
                    preferred_id=subscription_id,
                    completion_message=message,
                )
                return
            self.announcer.say(message)

        def failed(error: Exception) -> None:
            self._podcast_add_pending = False
            message = (
                str(error)
                if isinstance(error, (HostError, HostUnavailable))
                else "Nie udało się dodać źródła"
            )
            self.status_field.SetLabel(message)
            self.status_bar.show(message)
            self.announcer.say(message)

        self.runner.submit("podcast-add", work, done, failed)

    def _import_podcast_opml(self) -> None:
        """Ctrl+O w sesji podcastów: sprawdź OPML, wybierz i zaimportuj RSS."""
        if self.navigator.active is not SessionId.PODCASTS:
            self.announcer.say("Import OPML jest dostępny w sesji Podcasty i YouTube")
            return
        if self._podcast_opml_pending:
            self.announcer.say("Import lub eksport OPML już trwa")
            return
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie działa, nie mogę zaimportować podcastów")
            return

        with wx.FileDialog(
            self,
            message="Importuj podcasty z OPML",
            wildcard="Pliki OPML i XML (*.opml;*.xml)|*.opml;*.xml|Wszystkie pliki (*.*)|*.*",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as picker:
            if picker.ShowModal() != wx.ID_OK:
                return
            path = picker.GetPath()

        self._podcast_opml_pending = True
        started = "Odczytywanie listy podcastów z OPML"
        self.status_field.SetLabel(started)
        self.status_bar.show(started)
        self.announcer.say(started)

        def inspect() -> dict:
            result = client.inspect_podcast_opml(path)
            return result if isinstance(result, dict) else {}

        def inspected(payload: dict) -> None:
            entries = payload.get("entries")
            if not isinstance(entries, list) or not entries:
                self._podcast_opml_pending = False
                self.announcer.say("Plik OPML nie zawiera adresów podcastów")
                return
            with PodcastOpmlImportDialog(self, entries) as dialog:
                if dialog.ShowModal() != wx.ID_OK:
                    self._podcast_opml_pending = False
                    message = "Import OPML anulowany"
                    self.status_field.SetLabel(message)
                    self.status_bar.show(message)
                    return
                selected = dialog.selected_feed_urls

            message = f"Importowanie podcastów: {len(selected)}"
            self.status_field.SetLabel(message)
            self.status_bar.show(message)
            self.announcer.say(message)

            def import_selected() -> dict:
                result = client.import_podcast_opml(path, selected)
                return result if isinstance(result, dict) else {}

            def imported(result: dict) -> None:
                self._podcast_opml_pending = False
                imported_count = max(0, int(result.get("imported") or 0))
                failed_count = max(0, int(result.get("failed") or 0))
                completed = (
                    f"Zaimportowano podcasty: {imported_count}. "
                    f"Niepowodzenia: {failed_count}"
                )
                self.status_field.SetLabel(completed)
                self.status_bar.show(completed)
                state = self.navigator.sessions[SessionId.PODCASTS]
                if (
                    self.navigator.active is SessionId.PODCASTS
                    and state.view is View.LIST
                    and state.library_view is LibraryView.PODCAST_LIBRARY
                ):
                    self._open_podcast_library(completion_message=completed)
                else:
                    self.announcer.say(completed)

            def import_failed(error: Exception) -> None:
                self._podcast_opml_pending = False
                message = (
                    str(error)
                    if isinstance(error, (HostError, HostUnavailable))
                    else "Nie udało się zaimportować podcastów"
                )
                self.status_field.SetLabel(message)
                self.status_bar.show(message)
                self.announcer.say(message)

            self.runner.submit(
                "podcast-opml-import",
                import_selected,
                imported,
                import_failed,
            )

        def inspect_failed(error: Exception) -> None:
            self._podcast_opml_pending = False
            message = (
                str(error)
                if isinstance(error, (HostError, HostUnavailable))
                else "Nie udało się odczytać pliku OPML"
            )
            self.status_field.SetLabel(message)
            self.status_bar.show(message)
            self.announcer.say(message)

        self.runner.submit("podcast-opml-inspect", inspect, inspected, inspect_failed)

    def _export_podcast_opml(self) -> None:
        """Eksportuj zapisane podcasty RSS przez wspólny eksporter Core."""
        if self.navigator.active is not SessionId.PODCASTS:
            self.announcer.say("Eksport OPML jest dostępny w sesji Podcasty i YouTube")
            return
        if self._podcast_opml_pending:
            self.announcer.say("Import lub eksport OPML już trwa")
            return
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie działa, nie mogę wyeksportować podcastów")
            return

        with wx.FileDialog(
            self,
            message="Eksportuj bibliotekę podcastów do OPML",
            defaultFile="Podcasty AMC.opml",
            wildcard="Pliki OPML (*.opml)|*.opml|Pliki XML (*.xml)|*.xml",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as picker:
            if picker.ShowModal() != wx.ID_OK:
                return
            path = picker.GetPath()

        self._podcast_opml_pending = True
        started = "Eksportowanie biblioteki podcastów do OPML"
        self.status_field.SetLabel(started)
        self.status_bar.show(started)

        def work() -> dict:
            result = client.export_podcast_opml(path)
            return result if isinstance(result, dict) else {}

        def done(payload: dict) -> None:
            self._podcast_opml_pending = False
            count = max(0, int(payload.get("count") or 0))
            message = f"Wyeksportowano podcasty: {count}"
            self.status_field.SetLabel(message)
            self.status_bar.show(message)
            self.announcer.say(message)

        def failed(error: Exception) -> None:
            self._podcast_opml_pending = False
            message = (
                str(error)
                if isinstance(error, (HostError, HostUnavailable))
                else "Nie udało się wyeksportować biblioteki podcastów"
            )
            self.status_field.SetLabel(message)
            self.status_bar.show(message)
            self.announcer.say(message)

        self.runner.submit("podcast-opml-export", work, done, failed)

    def _export_youtube_subscriptions(self) -> None:
        """Eksportuj kanały do innych klientów albo wszystkie źródła do OPML."""
        if self.navigator.active is not SessionId.PODCASTS:
            self.announcer.say(
                "Eksport kanałów YouTube jest dostępny w sesji Podcasty i YouTube"
            )
            return
        if self._podcast_opml_pending:
            self.announcer.say("Import lub eksport źródeł już trwa")
            return
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie działa, nie mogę wyeksportować kanałów YouTube")
            return

        with wx.FileDialog(
            self,
            message="Eksportuj subskrypcje YouTube",
            defaultFile="Kanaly YouTube AMC.csv",
            wildcard=YOUTUBE_EXPORT_WILDCARD,
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as picker:
            if picker.ShowModal() != wx.ID_OK:
                return
            path = youtube_export_path_for_filter(
                picker.GetPath(),
                picker.GetFilterIndex(),
            )

        self._podcast_opml_pending = True
        started = "Eksportowanie kanałów YouTube"
        self.status_field.SetLabel(started)
        self.status_bar.show(started)

        def work() -> dict:
            result = client.export_youtube_subscriptions(path)
            return result if isinstance(result, dict) else {}

        def done(payload: dict) -> None:
            self._podcast_opml_pending = False
            exported = max(0, int(payload.get("exported") or 0))
            skipped = max(0, int(payload.get("skippedPlaylists") or 0))
            if str(payload.get("format") or "").casefold() == "opml":
                message = (
                    f"Wyeksportowano kanały i playlisty YouTube: {exported}. "
                    "Plik OPML jest przeznaczony do czytników RSS"
                )
            elif skipped:
                message = (
                    f"Wyeksportowano kanały YouTube: {exported}; "
                    f"pominięto playlisty: {skipped}. "
                    "Plik CSV można importować w NewPipe i FreeTube"
                )
            else:
                message = (
                    f"Wyeksportowano kanały YouTube: {exported}. "
                    "Plik CSV można importować w NewPipe i FreeTube"
                )
            self.status_field.SetLabel(message)
            self.status_bar.show(message)
            self.announcer.say(message)

        def failed(error: Exception) -> None:
            self._podcast_opml_pending = False
            message = (
                str(error)
                if isinstance(error, (HostError, HostUnavailable))
                else "Nie udało się wyeksportować kanałów YouTube"
            )
            self.status_field.SetLabel(message)
            self.status_bar.show(message)
            self.announcer.say(message)

        self.runner.submit("podcast-youtube-export", work, done, failed)

    def _refresh_podcasts(self, *, refresh_all: bool) -> None:
        """F5/Ctrl+F5: wspolny mechanizm odswiezania glownego AMC.

        Host C# pozostaje jedynym pisarzem ``podcasts.db``. Praca sieciowa
        biegnie w tle i nie zatrzymuje odtwarzania. Po odpowiedzi odczytujemy
        na nowo tylko widok, ktory uzytkownik nadal ma przed soba.
        """
        if self.navigator.active is not SessionId.PODCASTS:
            self.announcer.say(
                "Odświeżanie źródeł jest dostępne w sesji Podcasty i YouTube"
            )
            return
        if self._podcast_refresh_pending:
            self.announcer.say("Odświeżanie źródeł już trwa")
            return
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie działa, nie mogę odświeżyć źródeł")
            return

        subscription_id = None if refresh_all else self._current_podcast_subscription_id()
        if not refresh_all and not subscription_id:
            self.announcer.say("Zaznacz podcast albo otwórz jego listę odcinków")
            return

        self._podcast_refresh_pending = True
        self.status_bar.show(
            "Odświeżanie wszystkich źródeł podcastów"
            if refresh_all
            else "Odświeżanie wybranego źródła podcastów"
        )

        def work() -> dict:
            result = client.refresh_podcasts(subscription_id)
            return result if isinstance(result, dict) else {}

        def done(payload: dict) -> None:
            self._podcast_refresh_pending = False
            requested = max(0, int(payload.get("requested") or 0))
            succeeded = max(0, int(payload.get("succeeded") or 0))
            added = max(0, int(payload.get("addedEpisodes") or 0))
            inbox = max(0, int(payload.get("inboxCount") or 0))
            message = (
                f"Odświeżono źródła: {succeeded} z {requested}. "
                f"Nowe teraz: {added}. W skrzynce: {inbox}."
            )
            self.status_bar.show(message)

            # Tak jak w glownym AMC wynik nie wyrywa uzytkownika z odtwarzacza
            # ani z innej sesji. Zmiany sa w bazie i pojawia sie przy kolejnym
            # otwarciu listy.
            if self.navigator.active is not SessionId.PODCASTS:
                return
            state = self.navigator.sessions[SessionId.PODCASTS]
            if state.view is not View.LIST:
                return
            preferred_id = state.model.selected_id
            if state.library_view is LibraryView.PODCAST_LIBRARY:
                self._open_podcast_library(
                    preferred_id=preferred_id,
                    completion_message=message,
                )
            elif state.library_view is LibraryView.PODCAST_EPISODES:
                current_id = state.library_playlist_id
                if current_id:
                    self._open_podcast_view(
                        OpenPodcastView(
                            subscription_id=current_id,
                            preferred_id=preferred_id,
                        ),
                        completion_message=message,
                    )
            elif state.library_view in (
                LibraryView.PODCAST_FAVORITES,
                LibraryView.PODCAST_HISTORY,
                LibraryView.PODCAST_QUEUE,
                LibraryView.PODCAST_INBOX,
                LibraryView.PODCAST_DOWNLOADS,
            ):
                self._open_podcast_aggregate(
                    OpenPodcastAggregateView(
                        state.library_view,
                        preferred_id=preferred_id,
                    ),
                    completion_message=message,
                )

        def failed(error: Exception) -> None:
            self._podcast_refresh_pending = False
            message = (
                str(error)
                if isinstance(error, (HostError, HostUnavailable))
                else "Nie udało się odświeżyć źródeł podcastów"
            )
            self.status_bar.show(message)
            if self.navigator.active is SessionId.PODCASTS:
                self.announcer.say(message)

        self.runner.submit("podcast-refresh", work, done, failed)

    def _download_podcast_episodes(self) -> None:
        """Ctrl+D: pobierz jeden lub wiele zaznaczonych odcinków."""
        if self.navigator.active is not SessionId.PODCASTS:
            self.announcer.say("Pobieranie odcinków jest dostępne w sesji Podcasty i YouTube")
            return
        if self._podcast_download_pending:
            self.announcer.say("Pobieranie odcinków już trwa")
            return
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie działa, nie mogę pobrać odcinków")
            return

        rows: list[Row] = []
        seen: set[str] = set()
        for row in self._selected_action_rows():
            if row.kind != "episode" or row.item_id in seen:
                continue
            seen.add(row.item_id)
            rows.append(row)
        if not rows:
            self.announcer.say("Zaznacz co najmniej jeden odcinek podcastu")
            return

        episode_ids = [row.item_id for row in rows]
        preferred_id = rows[0].item_id
        self._podcast_download_pending = True
        started = (
            "Pobieranie odcinka"
            if len(rows) == 1
            else f"Pobieranie odcinków: {len(rows)}"
        )
        self.announcer.say(started)

        def work() -> dict:
            result = client.download_podcast_episodes(episode_ids)
            return result if isinstance(result, dict) else {}

        def done(payload: dict) -> None:
            self._podcast_download_pending = False
            requested = max(0, int(payload.get("requested") or len(rows)))
            downloaded = max(0, int(payload.get("downloaded") or 0))
            already = max(0, int(payload.get("alreadyDownloaded") or 0))
            failed_count = max(0, int(payload.get("failed") or 0))
            if requested > 1:
                parts = [f"Pobrano: {downloaded}"]
                if already:
                    parts.append(f"już pobrane: {already}")
                if failed_count:
                    parts.append(f"niepowodzenia: {failed_count}")
                message = ". ".join(parts)
            elif downloaded:
                message = f"Pobrano odcinek: {rows[0].title}"
            elif already:
                message = f"Odcinek jest już pobrany: {rows[0].title}"
            else:
                detail = str(payload.get("firstFailure") or "").strip()
                message = (
                    f"Nie można pobrać odcinka: {detail}"
                    if detail
                    else "Nie udało się pobrać odcinka"
                )
            self.status_field.SetLabel(message)
            self.status_bar.show(message)
            if not self._reload_podcast_list_after_download(preferred_id, message):
                self.announcer.say(message)

        def failed(error: Exception) -> None:
            self._podcast_download_pending = False
            message = (
                str(error)
                if isinstance(error, (HostError, HostUnavailable))
                else "Nie udało się pobrać odcinków"
            )
            self.status_field.SetLabel(message)
            self.status_bar.show(message)
            self.announcer.say(message)

        self.runner.submit("podcast-download", work, done, failed)

    def _save_podcast_episode_as(self) -> None:
        """Ctrl+S: jedna jawnie nazwana kopia, bez zmiany pola Pobrane."""
        if self.navigator.active is not SessionId.PODCASTS:
            self.announcer.say("Zapisywanie odcinka jest dostępne w sesji Podcasty i YouTube")
            return
        if self._podcast_download_pending:
            self.announcer.say("Pobieranie odcinków już trwa")
            return
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie działa, nie mogę zapisać odcinka")
            return

        rows = [row for row in self._selected_action_rows() if row.kind == "episode"]
        if len(rows) != 1:
            self.announcer.say(
                "Zapisz jako działa dla jednego odcinka. Wybierz jeden odcinek i spróbuj ponownie"
            )
            return
        row = rows[0]
        self._podcast_download_pending = True
        self.status_bar.show("Przygotowywanie zapisu odcinka")

        def prepare() -> dict:
            result = client.podcast_save_as_info(row.item_id)
            return result if isinstance(result, dict) else {}

        def prepared(info: dict) -> None:
            suggested = str(
                info.get("suggestedFileName") or "Odcinek podcastu.mp3"
            ).strip()
            initial_folder = str(info.get("initialFolder") or "").strip()
            extension = Path(suggested).suffix or ".mp3"
            with wx.FileDialog(
                self,
                message="Zapisz odcinek podcastu jako",
                defaultDir=initial_folder,
                defaultFile=suggested,
                wildcard=(
                    f"Plik audio (*{extension})|*{extension}|"
                    "Wszystkie pliki (*.*)|*.*"
                ),
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            ) as picker:
                if picker.ShowModal() != wx.ID_OK:
                    self._podcast_download_pending = False
                    return
                destination = picker.GetPath()

            started = f"Pobieranie odcinka: {row.title}"
            self.status_field.SetLabel(started)
            self.status_bar.show(started)
            self.announcer.say("Pobieranie odcinka")

            def work() -> dict:
                result = client.save_podcast_episode_as(row.item_id, destination)
                return result if isinstance(result, dict) else {}

            def done(payload: dict) -> None:
                self._podcast_download_pending = False
                file_name = str(
                    payload.get("fileName") or Path(destination).name
                ).strip()
                message = f"Zapisano odcinek jako: {file_name}"
                self.status_field.SetLabel(message)
                self.status_bar.show(message)
                self.announcer.say(message)

            self.runner.submit("podcast-save-as", work, done, failed)

        def failed(error: Exception) -> None:
            self._podcast_download_pending = False
            message = (
                str(error)
                if isinstance(error, (HostError, HostUnavailable))
                else "Nie udało się zapisać odcinka"
            )
            self.status_field.SetLabel(message)
            self.status_bar.show(message)
            self.announcer.say(message)

        self.runner.submit("podcast-save-as-info", prepare, prepared, failed)

    def _show_podcast_description(self) -> None:
        """Alt+D: description first, then metadata, in a native text field."""
        if self.navigator.active is not SessionId.PODCASTS:
            self.announcer.say(
                "Pełny opis jest dostępny dla podcastu albo odcinka"
            )
            return
        row = self.navigator.sessions[SessionId.PODCASTS].model.selected_row
        if row is None or row.kind not in ("podcast", "episode"):
            self.announcer.say(
                "Pełny opis jest dostępny dla podcastu albo odcinka"
            )
            return
        requested_id = row.item_id
        requested_kind = row.kind

        def work() -> PodcastDescription | None:
            return self.podcasts.description(requested_id, requested_kind)

        def done(information: PodcastDescription | None) -> None:
            state = self.navigator.sessions[SessionId.PODCASTS]
            current = state.model.selected_row
            if (
                self.navigator.active is not SessionId.PODCASTS
                or current is None
                or current.item_id != requested_id
            ):
                return
            if information is None:
                self.announcer.say(
                    "Ten podcast nie zawiera opisu"
                    if requested_kind == "podcast"
                    else "Ten odcinek nie zawiera opisu"
                )
                return

            def copy_text(text: str) -> bool:
                copied = self._to_clipboard(text)
                if copied:
                    self.announcer.say("Skopiowano całą treść")
                return copied

            with PodcastDescriptionDialog(self, information, copy_text) as dialog:
                dialog.ShowModal()

        def failed(error: Exception) -> None:
            message = (
                str(error)
                if isinstance(error, PodcastProfileError)
                else "Nie udało się odczytać opisu"
            )
            self.announcer.say(message)

        self.runner.submit("podcast-description", work, done, failed)

    def _go_to_related_podcast(self) -> None:
        """Open the selected episode's parent and keep focus on the episode."""
        if self.navigator.active is not SessionId.PODCASTS:
            self.announcer.say(
                "Dla tego elementu nie znaleziono podcastu w Bibliotece"
            )
            return
        row = self.navigator.sessions[SessionId.PODCASTS].model.selected_row
        if row is None or row.kind != "episode":
            self.announcer.say(
                "Dla tego elementu nie znaleziono podcastu w Bibliotece"
            )
            return
        episode_id = row.item_id

        def work():
            return self.podcasts.related_podcast(episode_id)

        def done(subscription) -> None:
            state = self.navigator.sessions[SessionId.PODCASTS]
            current = state.model.selected_row
            if (
                self.navigator.active is not SessionId.PODCASTS
                or current is None
                or current.item_id != episode_id
            ):
                return
            if subscription is None:
                self.announcer.say(
                    "Dla tego elementu nie znaleziono podcastu w Bibliotece"
                )
                return
            state.library_return_id = subscription.subscription_id
            self._open_podcast_view(OpenPodcastView(
                subscription_id=subscription.subscription_id,
                subscription_title=subscription.title,
                preferred_id=episode_id,
            ))

        def failed(error: Exception) -> None:
            self.announcer.say(
                str(error)
                if isinstance(error, PodcastProfileError)
                else "Nie udało się odnaleźć podcastu tego odcinka"
            )

        self.runner.submit("podcast-go-to-related", work, done, failed)

    def _routine_template_text(self, key: str, **values: str) -> str | None:
        """Utworz celowy tekst bez ujawniania identyfikatora zdarzenia."""
        policy = getattr(self, "messages", None)
        if not isinstance(policy, MessagePolicy):
            policy = MessagePolicy()
        return policy.render(key, **values)

    def _announce_routine_text(self, text: str | None) -> None:
        """Rutynowy komunikat respektuje nadrzedny wylacznik mowy.

        Przy wylaczonej mowie tekst nadal trafia do pola statusu, tak jak w
        glownym AMC. Pusty szablon nie tworzy ani mowy, ani statusu.
        """
        if not text:
            return
        policy = getattr(self, "messages", None)
        if not isinstance(policy, MessagePolicy):
            policy = MessagePolicy()
        if policy.speaks_routine:
            self.announcer.say(text)
            return
        show = getattr(self.announcer, "show", None)
        if callable(show):
            show(text)

    def _routine_completion_text(self, text: str | None) -> str:
        """Tekst do wypowiedzenia po asynchronicznym odswiezeniu listy."""
        if not text:
            return ""
        policy = getattr(self, "messages", None)
        if not isinstance(policy, MessagePolicy):
            policy = MessagePolicy()
        if policy.speaks_routine:
            return text
        LiteFrame._announce_routine_text(self, text)
        return ""

    def _toggle_podcast_favorite(self) -> None:
        """Ctrl+Shift+U: jeden wspólny stan dla całego zaznaczenia."""
        if self.navigator.active is not SessionId.PODCASTS:
            self.announcer.say(
                "Ulubione podcasty są dostępne w sesji Podcasty i YouTube"
            )
            return
        if getattr(self, "_podcast_favorite_pending", False):
            self.announcer.say("Zmiana stanu ulubionych już trwa")
            return
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie działa, nie mogę zmienić ulubionych")
            return

        rows: list[Row] = []
        seen: set[tuple[str, str]] = set()
        for row in self._selected_action_rows():
            if row.kind not in ("podcast", "episode") or not row.item_id:
                continue
            key = (row.kind, row.item_id)
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
        if not rows:
            self.announcer.say("Zaznacz podcast albo odcinek")
            return

        subscription_ids = [row.item_id for row in rows if row.kind == "podcast"]
        episode_ids = [row.item_id for row in rows if row.kind == "episode"]
        preferred_id = rows[0].item_id
        self._podcast_favorite_pending = True

        def work() -> dict:
            result = client.toggle_podcast_favorites(
                subscription_ids,
                episode_ids,
            )
            return result if isinstance(result, dict) else {}

        def done(payload: dict) -> None:
            self._podcast_favorite_pending = False
            favorite = bool(payload.get("favorite"))
            label = rows[0].title if len(rows) == 1 else format_item_count(len(rows))
            message = LiteFrame._routine_template_text(
                self,
                "favorite.added" if favorite else "favorite.removed",
                item=label,
            )

            if self.navigator.active is not SessionId.PODCASTS:
                LiteFrame._announce_routine_text(self, message)
                return
            state = self.navigator.sessions[SessionId.PODCASTS]
            if state.view is not View.LIST:
                LiteFrame._announce_routine_text(self, message)
                return
            completion = LiteFrame._routine_completion_text(self, message)
            if state.library_view is LibraryView.PODCAST_LIBRARY:
                self._open_podcast_library(
                    preferred_id=preferred_id,
                    completion_message=completion,
                )
                return
            if not self._reload_podcast_list_after_download(
                preferred_id, completion
            ):
                LiteFrame._announce_routine_text(self, message)

        def failed(error: Exception) -> None:
            self._podcast_favorite_pending = False
            message = (
                str(error)
                if isinstance(error, (HostError, HostUnavailable))
                else "Nie udało się zmienić stanu ulubionych"
            )
            self.status_field.SetLabel(message)
            self.status_bar.show(message)
            self.announcer.say(message)

        self.runner.submit("podcast-favorite", work, done, failed)

    def _toggle_podcast_library(self) -> None:
        """Ctrl+Shift+L: podcast albo źródło nadrzędne wybranego odcinka."""
        if self.navigator.active is not SessionId.PODCASTS:
            return
        if getattr(self, "_podcast_library_pending", False):
            self.announcer.say("Zmiana Biblioteki już trwa")
            return
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie działa, nie mogę zmienić Biblioteki")
            return

        rows = [
            row for row in self._selected_action_rows()
            if row.kind in ("podcast", "episode")
        ]
        subscription_ids = list(dict.fromkeys(
            row.item_id if row.kind == "podcast" else (row.parent_id or "")
            for row in rows
            if row.item_id and (row.kind == "podcast" or row.parent_id)
        ))
        if not subscription_ids:
            self.announcer.say("Zaznacz podcast albo odcinek")
            return
        label = rows[0].title if len(rows) == 1 else format_item_count(len(rows))
        self._podcast_library_pending = True

        def done(payload: dict) -> None:
            self._podcast_library_pending = False
            added = bool((payload or {}).get("added"))
            message = (
                f"Dodano do Biblioteki: {label}"
                if added else f"Usunięto z Biblioteki: {label}"
            )
            if self.navigator.active is not SessionId.PODCASTS:
                self.announcer.say(message)
                return
            state = self.navigator.sessions[SessionId.PODCASTS]
            if state.view is not View.LIST:
                self.announcer.say(message)
                return
            if (
                not added
                and state.library_view is LibraryView.PODCAST_EPISODES
                and state.library_playlist_id in subscription_ids
            ):
                # Pełne AMC wraca wtedy do głównej Biblioteki, zamiast
                # zostawiać odłączoną listę odcinków usuniętego źródła.
                state.library_view = LibraryView.PODCAST_LIBRARY
                state.library_playlist_id = None
                self._open_podcast_library(completion_message=message)
                return
            if state.library_view is LibraryView.PODCAST_LIBRARY:
                self._open_podcast_library(
                    preferred_id=subscription_ids[0] if added else None,
                    completion_message=message,
                )
                return
            if not self._reload_podcast_list_after_download(
                rows[0].item_id,
                message,
            ):
                self.announcer.say(message)

        def failed(error: Exception) -> None:
            self._podcast_library_pending = False
            self.announcer.say(f"Nie udało się zmienić Biblioteki: {error}")

        self.runner.submit(
            "podcast-library",
            lambda: client.toggle_podcast_library(subscription_ids),
            done,
            failed,
        )

    def _toggle_podcast_queue(self, play_next: bool) -> None:
        """Zmień trwałą kolejkę wybranych odcinków podcastów."""
        if getattr(self, "_podcast_queue_pending", False):
            self.announcer.say("Zmiana kolejki podcastów już trwa")
            return
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie działa, nie mogę zmienić kolejki")
            return
        rows = [
            row for row in self._selected_action_rows()
            if row.kind == "episode" and row.item_id
        ]
        if not rows:
            self.announcer.say("Do kolejki podcastów wybierz odcinek")
            return
        episode_ids = list(dict.fromkeys(row.item_id for row in rows))
        self._podcast_queue_pending = True

        def done(payload: dict) -> None:
            self._podcast_queue_pending = False
            payload = payload or {}
            changed = int(payload.get("changed") or 0)
            if changed <= 0:
                self.announcer.say("Kolejka podcastów bez zmian")
                return
            added = bool(payload.get("added"))
            label = rows[0].title if changed == 1 else format_item_count(changed)
            if play_next:
                message = LiteFrame._routine_template_text(
                    self,
                    "playnext.added" if added else "playnext.removed",
                    item=label,
                )
            else:
                message = LiteFrame._routine_template_text(
                    self,
                    "queue.added" if added else "queue.removed",
                    item=label,
                )
            state = self.navigator.sessions[SessionId.PODCASTS]
            if (
                self.navigator.active is SessionId.PODCASTS
                and state.view is View.LIST
                and state.library_view is LibraryView.PODCAST_QUEUE
            ):
                self._open_podcast_aggregate(
                    OpenPodcastAggregateView(
                        LibraryView.PODCAST_QUEUE,
                        preferred_id=episode_ids[0] if added else None,
                    ),
                    completion_message=LiteFrame._routine_completion_text(
                        self, message
                    ),
                )
            else:
                LiteFrame._announce_routine_text(self, message)

        def failed(error: Exception) -> None:
            self._podcast_queue_pending = False
            self.announcer.say(f"Nie udało się zmienić kolejki podcastów: {error}")

        self.runner.submit(
            "podcast-queue",
            lambda: client.toggle_podcast_queue(
                episode_ids,
                play_next=play_next,
            ),
            done,
            failed,
        )

    def _show_podcast_playback_options(self) -> None:
        """Alt+Shift+Enter: opcje zaznaczonego podcastu albo odcinka."""
        if self.navigator.active is not SessionId.PODCASTS:
            self.announcer.say(
                "Opcje są dostępne dla podcastu albo odcinka"
            )
            return
        if getattr(self, "_podcast_options_pending", False):
            self.announcer.say("Opcje odtwarzania są już otwierane")
            return
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie działa, nie mogę otworzyć opcji")
            return

        state = self.navigator.sessions[SessionId.PODCASTS]
        row = state.model.selected_row if state.view is View.LIST else next(
            (
                candidate for candidate in state.playback_source_rows
                if candidate.item_id == state.now_playing_id
            ),
            None,
        )
        if row is None and state.view is View.PLAYER and state.now_playing_id:
            row = Row(
                item_id=state.now_playing_id,
                title=state.now_playing_title or "Odcinek bez nazwy",
                kind="episode",
            )
        if row is None or row.kind not in ("podcast", "episode"):
            self.announcer.say("Zaznacz podcast albo odcinek")
            return

        item_id = row.item_id
        target = row.kind
        item_title = row.title
        self._podcast_options_pending = True

        def prepared(payload: dict) -> None:
            options = payload if isinstance(payload, dict) else {}
            dialog = PodcastPlaybackOptionsDialog(self, options)
            chosen: dict[str, object] | None = None
            try:
                if dialog.ShowModal() == wx.ID_OK:
                    chosen = dialog.values
            finally:
                dialog.Destroy()
            if chosen is None:
                self._podcast_options_pending = False
                self._restore_focus_after_dialog()
                return

            def saved(result: dict) -> None:
                self._podcast_options_pending = False
                saved_options = (
                    result.get("options")
                    if isinstance(result, dict) and isinstance(result.get("options"), dict)
                    else {}
                )
                title = str(saved_options.get("title") or item_title).strip()
                label = "podcastu" if target == "podcast" else "odcinka"
                message = f"Zapisano opcje {label}: {title}"
                if isinstance(result, dict) and result.get("appliesOnNextPlayback"):
                    message += ". Ustawienia toru dźwięku obowiązują od następnego otwarcia materiału"
                self.status_field.SetLabel(message)
                self.status_bar.show(message)
                self.announcer.say(message)
                self._restore_focus_after_dialog()

            def save_failed(error: Exception) -> None:
                self._podcast_options_pending = False
                self.announcer.say(f"Nie zapisano opcji odtwarzania: {error}")
                self._restore_focus_after_dialog()

            self.runner.submit(
                "podcast-options-save",
                lambda: client.set_podcast_playback_options(
                    item_id, target, chosen or {}
                ),
                saved,
                save_failed,
            )

        def failed(error: Exception) -> None:
            self._podcast_options_pending = False
            self.announcer.say(f"Nie można otworzyć opcji odtwarzania: {error}")

        self.runner.submit(
            "podcast-options-read",
            lambda: client.podcast_playback_options(item_id, target),
            prepared,
            failed,
        )

    def _reload_podcast_list_after_download(
        self, preferred_id: str, completion_message: str
    ) -> bool:
        """Odśwież tylko nadal otwartą listę, bez wyrywania z odtwarzacza."""
        if self.navigator.active is not SessionId.PODCASTS:
            return False
        state = self.navigator.sessions[SessionId.PODCASTS]
        if state.view is not View.LIST:
            return False
        if state.library_view is LibraryView.PODCAST_EPISODES:
            if state.library_playlist_id:
                self._open_podcast_view(
                    OpenPodcastView(
                        subscription_id=state.library_playlist_id,
                        preferred_id=preferred_id,
                    ),
                    completion_message=completion_message,
                )
                return True
        elif state.library_view in (
            LibraryView.PODCAST_FAVORITES,
            LibraryView.PODCAST_HISTORY,
            LibraryView.PODCAST_QUEUE,
            LibraryView.PODCAST_INBOX,
            LibraryView.PODCAST_DOWNLOADS,
        ):
            self._open_podcast_aggregate(
                OpenPodcastAggregateView(
                    state.library_view,
                    preferred_id=preferred_id,
                ),
                completion_message=completion_message,
            )
            return True
        return False

    def _begin_transient_preview(self) -> None:
        if self._transient_preview_return is None:
            self._transient_preview_return = self.navigator.capture_transient_navigation()

    def _show_playback_history_preview(self) -> None:
        """Ctrl+H: jedna Historia i Escape dokladnie do miejsca wywolania."""
        self._begin_transient_preview()
        origin = self.navigator.active
        if origin is SessionId.RADIO:
            self._open_radio_view(OpenLibraryView(
                LibraryView.HISTORY,
                target_session_id=SessionId.RADIO,
            ))
            return
        if origin is SessionId.PODCASTS:
            self._open_podcast_aggregate(
                OpenPodcastAggregateView(LibraryView.PODCAST_HISTORY)
            )
            return
        if origin is SessionId.SPOTIFY:
            rows = list(spotify_history_rows(
                self.state.spotify_playback_history
            ))
            self._run(self.navigator.apply_spotify_history(rows))
            return

        # WiiM i Sonos nie maja w profilu wlasnego katalogu historii, z ktorego
        # mozna zbudowac uzytkowe wiersze. Pokazujemy istniejaca Historie
        # plikow lokalnych jako wspolny podglad i zachowujemy cala sesje
        # urzadzenia do powrotu przez Escape.
        self.navigator.active = SessionId.FILES
        self._open_library_view(OpenLibraryView(
            LibraryView.HISTORY,
            target_session_id=SessionId.FILES,
        ))

    def _restore_transient_preview(
        self, *, announce: bool = True, force: bool = False
    ) -> bool:
        snapshot = getattr(self, "_transient_preview_return", None)
        if snapshot is None:
            return False
        current = self.navigator.session.library_view
        if not force and current not in (
            LibraryView.HISTORY,
            LibraryView.PODCAST_HISTORY,
            LibraryView.ACTIVE_RADIO_RECORDINGS,
            LibraryView.RECORDED_RADIO_FILES,
            LibraryView.RADIO_RECORDING_SCHEDULES,
            LibraryView.PODCAST_INBOX,
            LibraryView.SPOTIFY_HISTORY,
        ):
            return False
        self._transient_preview_return = None
        events = self.navigator.restore_transient_navigation(snapshot)
        if announce:
            self._run(events)
        else:
            self._sync_views()
        return True

    def _announce_after_native_list_update(self, text: str) -> None:
        """Daj SysListView32 zakonczyc zdarzenia pustki, potem podaj wynik.

        Usuniecie ostatniego wiersza generuje w Windows osobne zdarzenie
        dostepnosciowe. Samo ``CallAfter`` bywa za wczesne: NVDA potrafi wtedy
        dopisac PO naszym komunikacie systemowe ``pusto, nieznane``. Krotki
        jednorazowy timer nie blokuje GUI i sprawia, ze koncowa, pozostajaca
        informacja jest jednoznaczna: ``zero elementów``.
        """
        call_later = getattr(wx, "CallLater", None)
        if callable(call_later):
            call_later(90, self.announcer.say, text)
        else:
            # Atrapy wx w testach bez CallLater zachowuja dotychczasowa droge.
            wx.CallAfter(self.announcer.say, text)

    # ---------------------------------------------------------------- pliki

    def _open_folder(self, path: str, preferred_id: str | None = None) -> None:
        """Skan folderu idzie POZA GUI. Wynik przeterminowany jest odrzucany."""
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie dziala, nie moge wczytac folderu")
            return
        self.announcer.say("Wczytywanie...")

        def work() -> dict:
            return client.list_folder(path)

        def done(payload: dict) -> None:
            # Brama juz odrzucila wynik, jesli uzytkownik poszedl dalej albo
            # okno zniknelo - tutaj jestesmy tylko dla AKTUALNEGO skanu.
            rows = rows_from_folder_payload(payload)
            self.options.last_folder = path
            self._run(self.navigator.apply_folder(path, rows, preferred_id=preferred_id))

        def failed(error: Exception) -> None:
            self.announcer.say(f"Nie moge wczytac folderu: {error}")

        self.runner.submit("folder", work, done, failed)

    def _copy_name(self) -> None:
        """Ctrl+C: nazwy zaznaczonych elementow, po jednej w wierszu.

        Odpowiednik ``CopyActionItemName`` (MainWindow.xaml.cs:24755): pelne
        AMC czyta ``SelectedItems``, zachowuje kolejnosc listy i laczy nazwy
        przez ``Environment.NewLine``.
        """
        rows = [row for row in self._selected_action_rows() if row.title]
        if not rows:
            self.announcer.say("Nie ma czego skopiować")
            return
        self._clear_pending_external_moves()
        if self._to_clipboard(os.linesep.join(row.title for row in rows)):
            self.announcer.say(
                COPIED_NAME_MESSAGE
                if len(rows) == 1
                else f"Skopiowano nazwy: {format_item_count(len(rows))}"
            )

    def _selected_action_rows(self) -> list[Row]:
        """Wiersze dla polecenia: natywny wielokrotny wybor albo kursor.

        ``ListModel`` celowo nadal przechowuje jedno ID, bo sluzy ono do
        przywracania fokusu po zmianie widoku. Zakres zaznaczony Shiftem/Ctrl
        zyje w kontrolce i tylko stamtad moze zostac odczytany bez utraty.
        """
        try:
            rows = self._active_list().selected_rows()
        except (AttributeError, TypeError):
            # Testy czystej logiki oraz widok odtwarzacza nie musza miec
            # zbudowanej natywnej kontrolki.
            rows = []
        if rows:
            return rows
        row = self.navigator.session.model.selected_row
        return [] if row is None else [row]

    def _clear_pending_external_moves(self) -> None:
        pending = getattr(self, "pending_external_moves", None)
        if pending is not None:
            pending.clear()

    def _on_window_activate(self, event: wx.ActivateEvent) -> None:
        """Po powrocie do AMC rozpoznaj przeniesienie wykonane przez shell."""

        event.Skip()
        if event.GetActive():
            wx.CallAfter(self._reconcile_completed_external_moves)

    def _hide_completed_external_moves_from_files_model(self) -> bool:
        """Ukryj przeniesione wiersze bez zapisu do wspoldzielonej bazy AMC."""

        completed = getattr(self, "_completed_external_move_ids", set())
        if not completed:
            return False
        navigator = getattr(self, "navigator", None)
        sessions = getattr(navigator, "sessions", None)
        if not sessions or SessionId.FILES not in sessions:
            return False
        model = sessions[SessionId.FILES].model
        rows = [row for row in model.rows if row.item_id not in completed]
        if len(rows) == len(model.rows):
            return False
        model.replace(rows, keep_selection=True)
        return True

    def _reconcile_completed_external_moves(self) -> None:
        """Usun z listy pliki dopiero po faktycznym przeniesieniu przez shell.

        Ctrl+X sam nie usuwa zrodla. Dopiero brak dawnej sciezki po powrocie
        do AMC potwierdza, ze Total Commander albo Explorer zakonczyl ruch.
        """

        pending = getattr(self, "pending_external_moves", None)
        if not pending:
            return
        moved = [
            (item_id, path)
            for item_id, path in tuple(pending.items())
            if not os.path.exists(path)
        ]
        if not moved:
            return

        model = self.navigator.sessions[SessionId.FILES].model
        titles = {row.item_id: row.title for row in model.rows}
        completed = getattr(self, "_completed_external_move_ids", None)
        if completed is None:
            completed = set()
            self._completed_external_move_ids = completed
        for item_id, _path in moved:
            completed.add(item_id)
            pending.pop(item_id, None)
        moved_paths = [path for _item_id, path in moved]
        self._forget_private_recording_history_paths(moved_paths)
        client = getattr(self, "client", None)
        if client is not None:
            # Ctrl+X tylko przygotowuje ruch. Historię czyścimy dopiero tutaj,
            # gdy stara ścieżka rzeczywiście zniknęła; anulowanie albo błąd
            # wklejenia nie usuwa wpisu.
            self.runner.submit(
                "recording-history-forget-moved",
                lambda: client.forget_recording_history_paths(moved_paths),
                lambda _payload: None,
                lambda _error: None,
            )
        changed = self._hide_completed_external_moves_from_files_model()
        if changed and self.navigator.active is SessionId.FILES:
            self._sync_views()

        if len(moved) == 1:
            item_id, path = moved[0]
            title = titles.get(item_id) or Path(path).name
            self.announcer.say(f"Plik przeniesiono poza AMC: {title}")
        else:
            self.announcer.say(
                f"Przeniesiono pliki poza AMC: {format_file_count(len(moved))}"
            )

    def _announce_quick_information(self) -> None:
        """Parametry zaznaczonego elementu, nie aktualnie odtwarzanego.

        Cache i uzupełnianie przez silnik działają poza wątkiem GUI;
        wspólny formatter Core składa napis, bramka odrzuca spóźniony wynik.
        """
        row = self.navigator.session.model.selected_row
        if self.navigator.active is SessionId.TIDAL:
            if row is None:
                self.announcer.say("Lista TIDAL jest pusta")
                return
            parts = [row.title]
            if row.detail:
                parts.append(row.detail)
            if row.kind_label:
                parts.append(row.kind_label)
            parts.append("format audio nie został udostępniony przez zapisany katalog TIDAL")
            self.announcer.say(", ".join(dict.fromkeys(parts)))
            return
        if self.navigator.active is SessionId.SPOTIFY:
            self._run(self.navigator.spotify_information())
            return
        if self.navigator.active is SessionId.WIIM:
            if self.navigator.view is View.PLAYER and self._wiim_snapshot:
                parts = [
                    str(self._wiim_snapshot.get(name) or "").strip()
                    for name in (
                        "title", "subtitle", "artist", "album", "source",
                        "playbackState",
                    )
                ]
                parts = list(dict.fromkeys(part for part in parts if part))
                volume = int(self._wiim_snapshot.get("volume") or 0)
                parts.append(
                    "wyciszone" if self._wiim_snapshot.get("muted")
                    else f"głośność {volume}%"
                )
                self.announcer.say(", ".join(parts))
                return
            self._announce_speaker_item_information(row)
            return
        if self.navigator.active is SessionId.SONOS:
            if self.navigator.view is View.PLAYER and self._sonos_snapshot:
                parts = [
                    str(self._sonos_snapshot.get(name) or "").strip()
                    for name in (
                        "title", "source", "stateText", "volumeText",
                        "positionText",
                    )
                ]
                parts = list(dict.fromkeys(part for part in parts if part))
                self.announcer.say(", ".join(parts) or "Brak informacji Sonos")
                return
            self._announce_speaker_item_information(row)
            return
        client = self.client
        plan = quick_info_plan(
            row,
            session=self.navigator.active.value,
            view=self.navigator.view.value,
            duration_ticks=row.duration_ticks if row is not None else 0,
            podcast_media_length=(
                row.podcast_media_length if row is not None else None
            ),
            podcast_media_type=(
                row.podcast_media_type if row is not None else None
            ),
            alive=self._window_alive,
        )
        if plan.message is not None:
            self.announcer.say(plan.message)
            return
        if plan.request is None or plan.guard is None:
            return
        if client is None:
            # Bez hosta nie ma POMIARU. Jedno uczciwe zdanie zamiast ciszy,
            # ktora wygladalaby jak ten sam martwy klawisz.
            self.announcer.say(HOST_ERROR_MESSAGE)
            return

        guard = plan.guard
        request = plan.request
        layout = self.layout
        assert row is not None

        def work() -> object:
            enriched = dict(request)
            enriched.update(read_cached_information(layout, row, guard.session))
            return client.call(QUICK_INFO_OP, enriched, timeout=12.0)

        def answer(payload: object) -> None:
            quick_info_reply(
                payload if isinstance(payload, dict) else {},
                guard=guard,
                item_id=self._selected_item_id(),
                session=self.navigator.active.value,
                view=self.navigator.view.value,
                say=self.announcer.say,
            )

        def failed(_error: Exception) -> None:
            quick_info_failure(
                error=_error,
                guard=guard,
                item_id=self._selected_item_id(),
                session=self.navigator.active.value,
                view=self.navigator.view.value,
                say=self.announcer.say,
            )

        # Budzet hosta to 5 s na plik i 6 s na strumien (cs:5493, cs:5522),
        # wiec czekamy odrobine dluzej, zeby to silnik oddal wynik, a nie my
        # zglosili falszywa awarie tuz przed nim.
        self.runner.submit(
            QUICK_INFO_STREAM,
            work,
            answer,
            failed,
        )

    def _announce_speaker_item_information(self, row: Row | None) -> None:
        """Jedna droga lewego klawisza dla WiiM i Sonosa."""

        session = self.navigator.active
        if session not in SPEAKER_SESSIONS:
            return
        if row is None:
            self.announcer.say(f"Lista {SESSION_LABELS[session]} jest pusta")
            return
        plan = speaker_information_plan(
            row,
            session=session,
            view=self.navigator.view.value,
            alive=self._window_alive,
        )
        if plan.message is not None:
            self.announcer.say(plan.message)
            return
        if plan.request is None or plan.guard is None:
            return
        client = self.client
        if client is None:
            self.announcer.say(speaker_information_text(row))
            return

        def done(payload: object) -> None:
            speaker_information_reply(
                payload if isinstance(payload, dict) else {},
                plan=plan,
                item_id=self._selected_item_id(),
                session=self.navigator.active.value,
                view=self.navigator.view.value,
                say=self.announcer.say,
            )

        def failed(_error: Exception) -> None:
            speaker_information_failure(
                plan=plan,
                item_id=self._selected_item_id(),
                session=self.navigator.active.value,
                view=self.navigator.view.value,
                say=self.announcer.say,
            )

        self.runner.submit(
            QUICK_INFO_STREAM,
            lambda: client.call(QUICK_INFO_OP, plan.request, timeout=12.0),
            done,
            failed,
        )

    def _selected_item_id(self) -> str | None:
        row = self.navigator.session.model.selected_row
        return None if row is None else row.item_id

    def _copy_address(self) -> None:
        """Ctrl+Shift+C: adresy albo PRAWDZIWE PLIKI calego zaznaczenia.

        Odpowiednik ``CopyItemLocations`` (MainWindow.xaml.cs:24744-24814).
        Tu wlasnie trafil adres, ktory wczesniej czytnik wymawial przy KAZDYM
        wierszu -- funkcja nie znika, zmienia sie moment jej uzycia.

        ZGLOSZENIE, ktore to naprawia: komunikat mowil o kopiowaniu pliku,
        a wklejenie w Total Commanderze nic nie robilo, bo schowek dostawal
        TYLKO tekst sciezki. Oryginal ustawia DWA formaty naraz
        (``MainWindow.xaml.cs:24781``):

            data.SetData(DataFormats.UnicodeText, string.Join(NewLine, localPaths));
            data.SetFileDropList(fileDropList);

        czyli ``CF_HDROP`` ORAZ tekst. Wiec dla lokalnego, ISTNIEJACEGO pliku
        lub folderu robimy to samo: ``wx.FileDataObject`` + ``wx.TextDataObject``
        w ``wx.DataObjectComposite``.

        Slowa komunikatu nadal opisuja DANE, nie zamiar -- patrz
        ``copied_address_message``.
        """
        rows = self._selected_action_rows()
        if not rows:
            self.announcer.say("Nie ma czego skopiować")
            return
        if any(not row.address for row in rows):
            self.announcer.say(
                "Ten element nie ma zapisanego adresu"
                if len(rows) == 1
                else "Co najmniej jeden zaznaczony element nie ma zapisanego adresu"
            )
            return

        entries: list[tuple[Row, str, str | None]] = []
        for row in rows:
            drop = self._file_drop_path(row.address)
            # Tekst istniejacego pliku dostaje sprowadzona zwykla sciezke;
            # pozostale elementy zachowuja swoj bezposredni adres.
            entries.append((row, drop or row.address, drop))

        file_paths: list[str] = []
        seen_paths: set[str] = set()
        for _row, _text, path in entries:
            if path is None:
                continue
            key = os.path.normcase(path).casefold()
            if key not in seen_paths:
                seen_paths.add(key)
                file_paths.append(path)

        self._clear_pending_external_moves()
        text = os.linesep.join(entry[1] for entry in entries)
        if not self._to_clipboard(text, file_paths=file_paths or None):
            return

        if len(rows) == 1:
            self.announcer.say(copied_address_message(
                rows[0], file_copied=bool(file_paths)))
        elif all(entry[2] is not None for entry in entries):
            self.announcer.say(
                f"Skopiowano pliki i pełne ścieżki: {format_file_count(len(file_paths))}"
            )
        elif file_paths:
            address_count = sum(entry[2] is None for entry in entries)
            self.announcer.say(
                f"Skopiowano pliki: {len(file_paths)}; adresy: {address_count}"
            )
        elif all(row.kind == "station" for row in rows):
            self.announcer.say(
                f"Skopiowano bezpośrednie adresy: {format_item_count(len(rows))}"
            )
        else:
            self.announcer.say(f"Skopiowano adresy: {format_item_count(len(rows))}")

    @staticmethod
    def _file_drop_path(address: str) -> str | None:
        """Sciezka do file dropu albo ``None``, gdy go nie wolno ustawic.

        DWA warunki, oba z oryginalu i oba konieczne:

        1. ``TryGetLocalPath`` (``MainWindow.xaml.cs:5378``) -- czy to w ogole
           sciezka lokalna. Adres strumienia radiowego nie jest, wiec stacja
           dalej dostaje sam tekst i swoj dotychczasowy komunikat.
        2. ISTNIENIE na dysku. Oryginal sprawdza je w dwoch miejscach i w dwoch
           wariantach: ``CopySearchResultLocations`` (:24835) dokłada
           ``File.Exists``, a ``RadioPresetsWindow.xaml.cs:156-158`` pyta
           ``File.Exists(path) || Directory.Exists(path)``, bo wpis moze
           wskazywac FOLDER. Nasza lista pokazuje i pliki, i foldery, wiec
           bierzemy wariant szerszy -- jedyny, ktory nie klamie o folderze.

        Nieistniejace zrodlo celowo NIE dostaje file dropu: Windows i tak
        odmowilby wklejenia, a my nie moglibysmy ogłosic skopiowanego pliku
        bez powtorzenia tego samego zgloszenia.
        """
        if not is_local_path(address):
            return None
        path = local_path_from_source(address)
        return path if os.path.exists(path) else None

    def _open_profile_playlist_context(self) -> tuple[str, str, str] | None:
        """(sesja profilu, playlista, rodzaj wiersza) otwartej zawartości.

        Wartości służą wyłącznie do wąskiego wywołania hosta. Nie są
        dołączane do etykiet, statusu ani komunikatów NVDA.
        """
        state = self.navigator.session
        if (
            state.view is View.LIST
            and state.library_playlist_id
        ):
            contract = None
            if state.library_view is LibraryView.PLAYLIST_CONTENTS:
                contract = {
                    SessionId.FILES: ("local", "track"),
                    SessionId.RADIO: ("radio", "station"),
                }.get(self.navigator.active)
            elif (
                self.navigator.active is SessionId.PODCASTS
                and state.library_view
                is LibraryView.PODCAST_PLAYLIST_CONTENTS
            ):
                contract = ("podcasts", "episode")
            if contract is not None:
                return contract[0], state.library_playlist_id, contract[1]
        return None

    def _cut_or_start_internal_playlist_move(self) -> None:
        """Ctrl+X: najpierw wewnętrzna kolejność, poza playlistą pliki."""
        context = self._open_profile_playlist_context()
        if context is None:
            self._cut_file()
            return
        session_id, playlist_id, item_kind = context
        if self.filter_box.GetValue().strip():
            self.announcer.say(
                "Wyczyść filtr klawiszem Escape przed przenoszeniem elementów"
            )
            return
        rows = [
            row for row in self._selected_action_rows()
            if row.kind == item_kind and row.item_id
        ]
        item_ids = list(dict.fromkeys(row.item_id for row in rows))
        if not item_ids:
            self.announcer.say("Wybierz element do przeniesienia")
            return
        self._pending_internal_playlist_move = (
            session_id, playlist_id, tuple(item_ids)
        )
        self._clear_pending_external_moves()
        self.announcer.say(
            "Zaznaczono element do przeniesienia. "
            "Wybierz miejsce i naciśnij Ctrl+V"
            if len(item_ids) == 1
            else f"Zaznaczono do przeniesienia: {format_item_count(len(item_ids))}. "
                 "Wybierz miejsce i naciśnij Ctrl+V"
        )

    def _playlist_order_rows(
        self, item_kind: str
    ) -> tuple[list[Row], list[str]] | None:
        """Zaznaczenie i pełna widoczna kolejność bez filtra."""
        if self.filter_box.GetValue().strip():
            self.announcer.say(
                "Wyczyść filtr klawiszem Escape przed zmianą kolejności"
            )
            return None
        rows = [
            row for row in self._selected_action_rows()
            if row.kind == item_kind and row.item_id
        ]
        if not rows:
            self.announcer.say("Wybierz plik do przeniesienia")
            return None
        visible_ids = [
            row.item_id for row in self.navigator.session.model.rows
            if row.kind == item_kind and row.item_id
        ]
        return rows, visible_ids

    def _move_playlist_selection(self, direction: int) -> None:
        """Alt+Up/Down: ciągły blok o jedną pozycję jak w głównym AMC."""
        context = self._open_profile_playlist_context()
        if context is None:
            self.announcer.say(
                "Ręczne przenoszenie działa w otwartej playliście"
            )
            return
        session_id, playlist_id, item_kind = context
        if self._playlist_order_pending:
            self.announcer.say("Zmiana kolejności playlisty już trwa")
            return
        prepared = self._playlist_order_rows(item_kind)
        if prepared is None:
            return
        rows, visible_ids = prepared
        selected_ids = list(dict.fromkeys(row.item_id for row in rows))
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie działa. Kolejność nie została zmieniona")
            return

        selected_set = set(selected_ids)
        positions = [
            index for index, item_id in enumerate(visible_ids)
            if item_id in selected_set
        ]
        adjacent_title = "sąsiedni element"
        if positions and positions[-1] - positions[0] + 1 == len(positions):
            adjacent_index = positions[0] - 1 if direction < 0 else positions[-1] + 1
            if 0 <= adjacent_index < len(self.navigator.session.model.rows):
                adjacent_title = self.navigator.session.model.rows[adjacent_index].title
        self._playlist_order_pending = True

        def work() -> dict:
            result = client.move_profile_playlist_items(
                session_id,
                playlist_id,
                selected_ids,
                visible_ids,
                direction,
            )
            return result if isinstance(result, dict) else {}

        def done(result: dict) -> None:
            self._playlist_order_pending = False
            status = str(result.get("status") or "invalid")
            if status != "moved":
                self.announcer.say({
                    "boundary": (
                        "To początek tej listy" if direction < 0
                        else "To koniec tej listy"
                    ),
                    "nonContiguous": (
                        "Do wspólnego przeniesienia zaznacz ciągły blok elementów"
                    ),
                }.get(status, "Nie można zmienić kolejności zaznaczenia"))
                return
            self._pending_internal_playlist_move = None
            moved = (
                "Przeniesiono" if len(selected_ids) == 1
                else f"Przeniesiono {format_item_count(len(selected_ids))}"
            )
            message = (
                f"{moved} w górę, nad {adjacent_title}"
                if direction < 0
                else f"{moved} w dół, pod {adjacent_title}"
            )
            current = self._open_profile_playlist_context()
            if current is not None and current[:2] == (session_id, playlist_id):
                self._refresh_profile_view(
                    preferred_id=selected_ids[0],
                    selected_ids=selected_ids,
                    after_refresh=lambda: self.announcer.say(message),
                )
            else:
                self.announcer.say(message)

        def failed(error: Exception) -> None:
            self._playlist_order_pending = False
            self.announcer.say(f"Nie zmieniono kolejności playlisty: {error}")

        self.runner.submit("playlist-order-move", work, done, failed)

    def _paste_internal_playlist_move(self) -> None:
        """Ctrl+V: wstaw wcześniej wycięty blok przed bieżącym wierszem."""
        context = self._open_profile_playlist_context()
        if context is None:
            self.announcer.say(
                "Przenoszenie przed wybrany element działa w otwartej playliście"
            )
            return
        session_id, playlist_id, item_kind = context
        if self.filter_box.GetValue().strip():
            self.announcer.say(
                "Wyczyść filtr klawiszem Escape przed przenoszeniem elementów"
            )
            return
        pending = self._pending_internal_playlist_move
        if pending is None or pending[:2] != (session_id, playlist_id):
            self.announcer.say(
                "Najpierw zaznacz element lub grupę skrótem Ctrl+X"
            )
            return
        if self._playlist_order_pending:
            self.announcer.say("Zmiana kolejności playlisty już trwa")
            return
        target = self.navigator.session.model.selected_row
        if target is None or target.kind != item_kind or not target.item_id:
            self.announcer.say(
                "Wybierz element, przed którym chcesz przenieść zaznaczenie"
            )
            return
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie działa. Kolejność nie została zmieniona")
            return
        selected_ids = list(pending[2])
        target_id = target.item_id
        target_title = target.title
        self._playlist_order_pending = True

        def work() -> dict:
            result = client.place_profile_playlist_items_before(
                session_id, playlist_id, selected_ids, target_id
            )
            return result if isinstance(result, dict) else {}

        def done(result: dict) -> None:
            self._playlist_order_pending = False
            status = str(result.get("status") or "invalid")
            if status != "moved":
                self.announcer.say({
                    "targetInSelection": "Wybierz inny element jako miejsce docelowe",
                    "targetMissing": "Nie znaleziono wskazanego miejsca docelowego",
                    "unchanged": "Elementy są już w tym miejscu",
                }.get(status, "Nie można przenieść zaznaczonych elementów"))
                return
            self._pending_internal_playlist_move = None
            message = (
                f"Przeniesiono przed {target_title}"
                if len(selected_ids) == 1
                else f"Przeniesiono {format_item_count(len(selected_ids))} "
                     f"przed {target_title}"
            )
            current = self._open_profile_playlist_context()
            if current is not None and current[:2] == (session_id, playlist_id):
                self._refresh_profile_view(
                    preferred_id=selected_ids[0],
                    selected_ids=selected_ids,
                    after_refresh=lambda: self.announcer.say(message),
                )
            else:
                self.announcer.say(message)

        def failed(error: Exception) -> None:
            self._playlist_order_pending = False
            self.announcer.say(f"Nie przeniesiono elementów playlisty: {error}")

        self.runner.submit("playlist-order-place", work, done, failed)

    def _cut_file(self) -> None:
        """Ctrl+X: zaznaczone pliki GOTOWE DO PRZENIESIENIA poza AMC.

        Port ``CutLocalFilesForExternalMove`` (``MainWindow.xaml.cs:25277``).
        Michal uzywa tego w dzialajacym AMC i prosil o zgodne zachowanie.

        CZEGO TA FUNKCJA NIE ROBI -- i to jest regula oryginalu, nie nasze
        uproszczenie: SAMA NIE USUWA PLIKU. Oryginal tylko zapisuje schowek i
        zapamietuje sciezki w ``_pendingExternalMoves`` (:25306-25309);
        skasowanie zrodla wykonuje SHELL przy wklejeniu, a
        ``ReconcileCompletedExternalMoves`` (:25315) jedynie ZAUWAZA, ze plik
        zniknal. Gdybysmy usuwali sami, nieudane wklejenie skasowaloby nagranie.

        Warunki sa WEZSZE niz przy kopiowaniu i tak samo jest w C#:
        tylko ISTNIEJACY PLIK (``File.Exists``, :25289) -- folder sie nie
        kwalifikuje, choc do KOPIOWANIA jak najbardziej.
        """
        rows = self._selected_action_rows()
        if not rows:
            self.announcer.say("Brak pliku do wycięcia")
            return
        # Widok zakladek: wiersz wskazuje ``bookmark:<id>``, czyli ani plik,
        # ani sciezke (:25280-25284).
        if self.navigator.session.library_view is LibraryView.ALL_BOOKMARKS:
            self.announcer.say("Wycinanie plików nie działa na liście zakładek")
            return
        entries = [(row, self._cut_file_path(row.address)) for row in rows]
        if any(path is None for _row, path in entries):
            self.announcer.say(
                "Wycinanie jest dostępne tylko dla istniejących plików lokalnych")
            return
        paths: list[str] = []
        seen_paths: set[str] = set()
        for _row, path in entries:
            assert path is not None
            key = os.path.normcase(path).casefold()
            if key not in seen_paths:
                seen_paths.add(key)
                paths.append(path)
        file_arguments = (
            {"file_path": paths[0]}
            if len(paths) == 1
            else {"file_paths": paths}
        )
        if not self._to_clipboard(
            os.linesep.join(paths),
            preferred_drop_effect=DROPEFFECT_MOVE,
            **file_arguments,
        ):
            return
        # Zapamietujemy OCZEKUJACE przeniesienie, tak jak oryginal. Samo
        # zapamietanie nic nie usuwa -- sluzy pozniejszemu rozpoznaniu, ze
        # plik juz nie lezy pod stara sciezka.
        self.pending_external_moves.clear()
        for row, path in entries:
            assert path is not None
            self.pending_external_moves[row.item_id] = path
        self.announcer.say(
            "Plik gotowy do przeniesienia. Wklej go w folderze docelowym"
            if len(paths) == 1
            else f"Pliki gotowe do przeniesienia: {format_file_count(len(paths))}. "
                 "Wklej je w folderze docelowym"
        )

    @staticmethod
    def _cut_file_path(address: str) -> str | None:
        """Sciezka do wyciecia albo ``None``.

        Rozni sie od ``_file_drop_path`` JEDNYM warunkiem i jest to roznica z
        oryginalu: wycinanie wymaga ``File.Exists`` (:25289), wiec FOLDER sie
        nie kwalifikuje. Kopiowanie bierze wariant szerszy (plik lub folder),
        bo ``RadioPresetsWindow.xaml.cs:156-158`` pyta o oba.
        """
        if not address or not is_local_path(address):
            return None
        path = local_path_from_source(address)
        return path if os.path.isfile(path) else None

    def _to_clipboard(
        self,
        text: str,
        *,
        file_path: str | None = None,
        file_paths: list[str] | None = None,
        preferred_drop_effect: int | None = None,
    ) -> bool:
        """Zapis do schowka Windows. Porazke MOWIMY, nie udajemy sukcesu.

        Schowek bywa chwilowo zajety przez inny proces -- odpowiednik
        ``ClipboardRetry`` z AMC, ktory tez zwraca komunikat bledu zamiast
        komunikatu sukcesu.

        ``file_path``/``file_paths`` ustawiaja DODATKOWO format plikowy (``wx.FileDataObject``,
        czyli ``CF_HDROP``) obok tekstu -- jak ``SetFileDropList`` w oryginale.
        Bez niego zostaje JEDEN format tekstowy, dokladnie jak dotad; dlatego
        ``Ctrl+C`` (nazwa) i stacje nie zmieniaja zachowania ani o jotę.
        """
        try:
            if not wx.TheClipboard.Open():
                self.announcer.say("Schowek jest zajęty, spróbuj ponownie")
                return False
            try:
                paths = file_paths if file_paths is not None else (
                    [file_path] if file_path is not None else [])
                if not paths:
                    data = wx.TextDataObject(text)
                else:
                    # Kolejnosc jak w oryginale: najpierw tekst (``UnicodeText``),
                    # potem file drop. Preferowany jest format PLIKOWY -- o niego
                    # chodzi w zgloszeniu, a odbiorcy tekstowi (edytor, pole
                    # wyszukiwania) i tak wezma galaz tekstowa.
                    data = wx.DataObjectComposite()
                    data.Add(wx.TextDataObject(text))
                    files = wx.FileDataObject()
                    for path in paths:
                        files.AddFile(path)
                    data.Add(files, True)
                    if preferred_drop_effect is not None:
                        # ``Preferred DropEffect``: TRZECI format, ktorym shell
                        # rozpoznaje WYCIECIE. ``SetData("Preferred DropEffect",
                        # BitConverter.GetBytes(2))`` w C# to 4 bajty little
                        # endian -- ``wx.CustomDataObject`` przyjmuje je wprost.
                        effect = wx.CustomDataObject(wx.DataFormat("Preferred DropEffect"))
                        effect.SetData(
                            preferred_drop_effect.to_bytes(4, "little", signed=False))
                        data.Add(effect)
                if not wx.TheClipboard.SetData(data):
                    # ``wxClipboard::SetData`` zwraca BOOL i nie rzuca wyjatku,
                    # gdy schowek odmowi przyjecia obiektu. Bez tej bramki
                    # porazka konczyla sie komunikatem sukcesu przy pustym
                    # schowku -- tym samym zgloszeniem, tylko cichszym.
                    self.announcer.say("Nie udało się skopiować do schowka")
                    return False
                # ``Flush`` to TRWALOSC po zamknieciu naszego procesu, a nie
                # sam zapis: dane juz LEZA w schowku i wklejenie zadziala.
                # Dlatego jego ``False`` NIE jest bledem kopiowania -- inaczej
                # program klamalby w druga strone.
                wx.TheClipboard.Flush()
            finally:
                wx.TheClipboard.Close()
        except Exception as error:
            self.announcer.say(f"Nie udało się skopiować: {error}")
            return False
        return True

    def _choose_folder(self) -> None:
        with wx.DirDialog(self, "Wybierz folder z muzyka", style=wx.DD_DIR_MUST_EXIST) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                self._switch_session(SessionId.FILES)
                self._open_folder(dialog.GetPath())

    def _choose_file(self) -> None:
        wildcard = "Audio|*.mp3;*.flac;*.wav;*.m4a;*.ogg;*.opus;*.wma;*.aac|Wszystkie|*.*"
        with wx.FileDialog(
            self, "Wybierz plik", wildcard=wildcard, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as dialog:
            if dialog.ShowModal() != wx.ID_OK:
                return
            path = dialog.GetPath()
            self._switch_session(SessionId.FILES)
            self._play_track(PlayTrack(path, f"file:{path}", Path(path).name))
            folder = str(Path(path).parent)
            self._open_folder(folder, preferred_id=f"file:{path}")

    # ----------------------------------------------------------- odtwarzanie

    def _play_track(self, intent: PlayTrack) -> None:
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie dziala, nie moge odtworzyc")
            return
        self._pending_playback_session = SessionId.FILES

        def work() -> dict:
            client.configure_audio(
                **session_options.resolve_audio_payload(
                    self.options,
                    session_options.effective_overrides(
                        self.state, SessionId.FILES
                    ),
                )
            )
            return client.play_file(
                intent.path,
                item_id=intent.item_id,
                volume=self.options.volume,
                rate=self.options.rate,
                title=intent.title,
                # Skok zakladki jedzie Z TYM SAMYM zadaniem, nie osobnym seek.
                position_seconds=intent.position_seconds,
            )

        def done(_payload: dict) -> None:
            self._playing_session = SessionId.FILES
            self._playing_sessions.discard(SessionId.PODCASTS)
            self._playing_sessions.add(SessionId.FILES)
            self._refresh_status()

        def failed(error: Exception) -> None:
            if self._pending_playback_session is SessionId.FILES:
                self._pending_playback_session = None
            self._run(self.navigator.note_playback_failed(
                f"Nie udalo sie odtworzyc: {error}", SessionId.FILES
            ))

        self.runner.submit("playback", work, done, failed)

    def _play_media(self, intent: PlayMedia) -> None:
        """Play an episode/YouTube item through the existing C# audio engine."""
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie działa, nie mogę odtworzyć")
            return

        self._pending_playback_session = SessionId.PODCASTS

        def work() -> dict:
            # Jeden WindowsMediaOutput obsługuje Pliki i Podcasty. Przed
            # każdym startem ustawiamy bazę WŁAŚCIWEJ sesji; host nakłada na
            # nią jeszcze nadpisania podcastu i odcinka z podcasts.db.
            client.configure_audio(
                **session_options.resolve_audio_payload(
                    self.options,
                    session_options.effective_overrides(
                        self.state, SessionId.PODCASTS
                    ),
                )
            )
            return client.play_media(
                intent.source,
                item_id=intent.item_id,
                title=intent.title,
                volume=self.options.volume,
                rate=self.options.rate,
                position_seconds=intent.position_seconds,
            )

        def done(_payload: dict) -> None:
            self._playing_session = SessionId.PODCASTS
            self._playing_sessions.discard(SessionId.FILES)
            self._playing_sessions.add(SessionId.PODCASTS)
            self._refresh_status()

        def failed(error: Exception) -> None:
            if self._pending_playback_session is SessionId.PODCASTS:
                self._pending_playback_session = None
            self._run(self.navigator.note_playback_failed(
                f"Nie udało się odtworzyć: {error}", SessionId.PODCASTS
            ))

        self.runner.submit("playback", work, done, failed)

    def _play_tidal_track(self, intent: PlayTidalTrack) -> None:
        """Hand one track to original TIDAL; AMC itself plays no audio here."""
        self._play_tidal_item(
            intent,
            lambda client, restart_consent: client.tidal_desktop_play(
                item_id=intent.item_id,
                external_id=intent.service_id,
                title=intent.title,
                related_album_external_id=intent.related_album_service_id,
                restart_consent=restart_consent,
            ),
        )

    def _play_tidal_container(self, intent: PlayTidalContainer) -> None:
        """Hand a whole album or playlist to original TIDAL."""
        self._play_tidal_item(
            intent,
            lambda client, restart_consent: client.tidal_desktop_play_container(
                item_id=intent.item_id,
                external_id=intent.service_id,
                title=intent.title,
                kind=intent.kind,
                restart_consent=restart_consent,
            ),
        )

    def _toggle_tidal_membership(self, *, favorite: bool) -> None:
        """Ctrl+Shift+U/L: zmień prawdziwą kolekcję konta TIDAL."""
        if self.navigator.active is not SessionId.TIDAL:
            return
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie działa, nie mogę zmienić kolekcji TIDAL")
            return
        rows = self._selected_action_rows()
        allowed = {"track", "video"} if favorite else {"album", "artist", "playlist"}
        rows = [
            row for row in rows
            if row.kind in allowed and row.service_id and row.item_id
        ]
        if not rows:
            self.announcer.say(
                "Do Ulubionych TIDAL wybierz utwór lub materiał wideo"
                if favorite else
                "Do Biblioteki TIDAL wybierz album, wykonawcę albo playlistę"
            )
            return
        items = [
            {
                "itemId": row.item_id,
                "externalId": row.service_id,
                "title": row.title,
                "kind": row.kind,
                "artist": row.artist_name,
                "publicUri": row.url or "",
            }
            for row in rows
        ]
        active_view = self.navigator.sessions[SessionId.TIDAL].library_view
        preferred_id = rows[0].item_id

        def done(payload: dict) -> None:
            result = payload or {}
            message = str(result.get("message") or "").strip()
            self.announcer.say(message or "Zmieniono kolekcję TIDAL")
            relevant_views = (
                {LibraryView.TIDAL_FAVORITES}
                if favorite else
                {LibraryView.TIDAL_LIBRARY, LibraryView.TIDAL_PLAYLISTS}
            )
            if active_view in relevant_views:
                self._open_tidal_view(OpenTidalView(
                    active_view,
                    preferred_id=preferred_id if bool(result.get("added")) else None,
                ))

        self.runner.submit(
            "tidal-membership",
            lambda: client.tidal_collection_membership(
                items,
                mode="favorite" if favorite else "library",
            ),
            done,
            lambda error: self.announcer.say(
                f"Nie udało się zmienić kolekcji TIDAL: {error}"
            ),
        )

    def _play_tidal_item(
        self,
        intent: PlayTidalTrack | PlayTidalContainer,
        request: Callable[[LiteHostClient, bool], dict],
    ) -> None:
        """Shared confirmation and rollback for external TIDAL hand-offs."""
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie działa, nie mogę sterować TIDALem")
            return

        had_playback = self._tidal_desktop_has_playback
        previous_id = intent.previous_item_id if had_playback else ""
        previous_title = intent.previous_title if previous_id else ""

        self.announcer.say(f"{intent.title}: przekazuję do oryginalnego TIDALa")

        def restore_or_fail(message: str) -> None:
            if had_playback and previous_id:
                self.navigator.restore_tidal_playback_after_failed_handoff(
                    previous_id, previous_title
                )
                self.announcer.say(message)
                self._sync_views()
                return
            self._tidal_desktop_has_playback = False
            self._run(self.navigator.note_playback_failed(message, SessionId.TIDAL))

        def submit(restart_consent: bool) -> None:
            def work() -> dict:
                return request(client, restart_consent)

            def done(payload: dict) -> None:
                result = payload or {}
                message = str(
                    result.get("message")
                    or "Nie udało się przekazać elementu oryginalnemu TIDALowi"
                )
                if bool(result.get("needsRestartConsent")):
                    self.announcer.say(message)
                    question = (
                        message
                        + ". Zamknąć oryginalny TIDAL i uruchomić go ponownie?"
                    )
                    dialog = wx.MessageDialog(
                        self,
                        question,
                        "Odtwarzanie w oryginalnym TIDALu",
                        wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
                    )
                    try:
                        if hasattr(dialog, "SetName"):
                            dialog.SetName(
                                "Potwierdzenie ponownego uruchomienia TIDALa"
                            )
                        if hasattr(dialog, "SetYesNoLabels"):
                            dialog.SetYesNoLabels(
                                "Tak, uruchom ponownie",
                                "Nie, pozostaw TIDAL bez zmian",
                            )
                        answer = dialog.ShowModal()
                    finally:
                        dialog.Destroy()
                    self._restore_focus_after_dialog()
                    if answer == wx.ID_YES:
                        self.announcer.say(
                            f"{intent.title}: uruchamiam ponownie oryginalny TIDAL"
                        )
                        submit(True)
                    else:
                        restore_or_fail(
                            "Odtwarzanie w oryginalnym TIDALu anulowane"
                        )
                    return
                if not bool(result.get("success")):
                    restore_or_fail(message)
                    return

                self._tidal_desktop_has_playback = True
                self.navigator.note_tidal_playback_started(
                    intent.item_id,
                    intent.title,
                    uses_external_queue=isinstance(intent, PlayTidalContainer),
                )
                self.announcer.say(message)
                self._sync_views()

            submit_error = lambda error: restore_or_fail(
                f"Nie udało się przekazać elementu oryginalnemu TIDALowi: {error}"
            )
            self.runner.submit("tidal-playback", work, done, submit_error)

        submit(False)

    def _add_bookmark(self, *, named: bool = False) -> None:
        """Dodaj szybka albo nazwana zakladke przez waski zapis hosta C#."""
        if self.navigator.active is SessionId.RADIO:
            self._add_radio_recording_bookmark(named=named)
            return
        if self.navigator.active is not SessionId.FILES:
            self.announcer.say(
                "Zakładki w tej sesji nie są jeszcze dostępne w tej wersji"
            )
            return
        state = self.navigator.session
        item_id = state.current_material_id or state.pending_material_id
        if not item_id:
            self.announcer.say("Bieżący plik nie ma identyfikatora Biblioteki")
            return
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie działa, nie mogę dodać zakładki")
            return

        name: str | None = None
        if named:
            with RenameItemDialog(
                self,
                title="Dodaj nazwaną zakładkę",
                prompt="&Nazwa zakładki:",
                field_name="Nazwa zakładki",
                value="",
                help_text=(
                    "Nazwa opisuje bieżące miejsce w odtwarzanym pliku."
                ),
            ) as dialog:
                if dialog.ShowModal() != wx.ID_OK:
                    return
                name = dialog.value
            if not name:
                self.announcer.say("Nazwa zakładki nie może być pusta")
                return

        def done(payload: dict) -> None:
            seconds = float((payload or {}).get("positionSeconds") or 0.0)
            position = format_duration(seconds)
            stored_name = str((payload or {}).get("name") or name or "").strip()
            if named and (payload or {}).get("added"):
                self.announcer.say(
                    f"Dodano zakładkę {stored_name}: {position}"
                )
            elif named and (payload or {}).get("nameChanged"):
                self.announcer.say(
                    f"Nadano nazwę zakładce {stored_name}: {position}"
                )
            elif named:
                self.announcer.say(
                    f"Zakładka {stored_name} już istnieje: {position}"
                )
            elif (payload or {}).get("added"):
                self.announcer.say(f"Dodano zakładkę: {position}")
            else:
                self.announcer.say(f"Zakładka już istnieje: {position}")

        self.runner.submit(
            "bookmark-write",
            lambda: client.add_bookmark(
                item_id=item_id,
                item_title=state.now_playing_title or item_id,
                name=name,
            ),
            done,
            lambda error: self.announcer.say(f"Nie można dodać zakładki: {error}"),
        )

    def _add_radio_recording_bookmark(self, *, named: bool) -> None:
        """B/Shift+B: znacznik bieżącej części trwającego nagrania radia."""
        station = self._recording_station()
        if station is None:
            return
        client = self.client
        if client is None:
            self.announcer.say(
                "Silnik nie działa, nie mogę dodać zakładki nagrania"
            )
            return

        name: str | None = None
        if named:
            with RenameItemDialog(
                self,
                title="Dodaj nazwaną zakładkę nagrania",
                prompt="&Nazwa zakładki:",
                field_name="Nazwa zakładki",
                value="",
                help_text=(
                    "Nazwa opisuje bieżące miejsce w nagraniu stacji."
                ),
            ) as dialog:
                if dialog.ShowModal() != wx.ID_OK:
                    return
                name = dialog.value
            if not name:
                self.announcer.say("Nazwa zakładki nie może być pusta")
                return

        def done(payload: dict) -> None:
            result = payload or {}
            state = str(result.get("state") or "")
            if state == "notRecording":
                self.announcer.say(f"Stacja nie jest nagrywana: {station.name}")
                return
            if state in ("starting", "busy"):
                self.announcer.say(
                    "Nagranie jeszcze się uruchamia albo trwa zmiana części"
                )
                return
            seconds = float(result.get("positionSeconds") or 0.0)
            position = format_duration(seconds)
            stored_name = str(result.get("name") or name or "").strip()
            affected = int(result.get("affectedCount") or 0)
            suffix = f", nagrania: {affected}" if affected > 1 else ""
            if state == "duplicate":
                self.announcer.say(
                    f"Nazwana zakładka nagrania już istnieje: {position}"
                    if named
                    else f"Zakładka nagrania już istnieje: {position}"
                )
                return
            self.announcer.say(
                f"Dodano zakładkę {stored_name}: {position}{suffix}"
                if named
                else f"Dodano zakładkę nagrania: {position}{suffix}"
            )

        self.runner.submit(
            "radio-recording-bookmark",
            lambda: client.add_radio_recording_bookmark(
                station.id,
                station.url,
                name,
            ),
            done,
            lambda error: self.announcer.say(
                f"Nie można dodać zakładki nagrania: {error}"
            ),
        )

    def _navigate_bookmark(self, forward: bool) -> None:
        """Shift+Page Up/Down: nawigacja po zakładkach bieżącego pliku."""
        if self.navigator.active is not SessionId.FILES:
            self.announcer.say(
                "Nawigacja po zakładkach jest dostępna dla plików lokalnych"
            )
            return
        client = self.client
        if client is None:
            self.announcer.say(
                "Silnik nie działa, nawigacja po zakładkach jest niedostępna"
            )
            return

        direction = 1 if forward else -1

        def done(payload: dict) -> None:
            result = payload or {}
            if not result.get("found"):
                self.announcer.say(
                    "Brak następnej zakładki w tym materiale"
                    if forward
                    else "Brak poprzedniej zakładki w tym materiale"
                )
                return
            raw_position = result.get("positionSeconds")
            position = (
                float(raw_position)
                if isinstance(raw_position, (int, float))
                and not isinstance(raw_position, bool)
                else 0.0
            )
            self._last_status = {
                **self._last_status,
                "positionSeconds": position,
            }
            name = result.get("name")
            text = (
                f"{name.strip()}, {format_duration(position)}"
                if isinstance(name, str) and name.strip()
                else format_duration(position)
            )
            if (
                self.messages.seek_messages
                and self.messages.bookmark_navigation_messages
                and self.messages.speaks_routine
            ):
                self.announcer.say(text)
            else:
                self.announcer.show(text)

        self.runner.submit(
            "bookmark-navigation",
            lambda: client.navigate_bookmark(direction),
            done,
            lambda error: self.announcer.say(
                f"Nie można przejść do zakładki: {error}"
            ),
        )

    # ------------------------------------------------------ fragmenty audio

    def _request_audio_clip_context(
        self,
        on_ready: Callable[[AudioClipContext, AudioClipSelection], None],
    ) -> None:
        """Pobierz pozycje i tozsamosc z hosta, nie ze starego ticka GUI."""
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie działa, wycinanie fragmentu jest niedostępne")
            return

        # Host obsluguje Radio oraz wspolny silnik Plikow/Podcastow rownolegle.
        # ``status()`` bez sessionId pyta o ostatnio dotkniety tor. Okresowy
        # odczyt stanu Radia moze wiec odbyc sie pomiedzy uruchomieniem
        # nagrania z widoku "Nagrane" a nacisnieciem I/O. Dostawalismy wtedy
        # poprawny status RADIA i bledny komunikat, ze odtwarzane nagranie nie
        # jest plikiem multimedialnym. Kontekst wycinania zawsze nalezy do
        # widocznego odtwarzacza Plikow albo Podcastow, wiec wskazujemy sesje
        # jawnie i nigdy nie korzystamy tu z historycznego routingu hosta.
        requested_session = self.navigator.active
        if requested_session not in (SessionId.FILES, SessionId.PODCASTS):
            self.announcer.say(
                "Wycinanie fragmentu jest dostępne dla plików lokalnych "
                "i pobranych odcinków podcastów"
            )
            return
        player_view_active = self.navigator.view is View.PLAYER

        def work() -> tuple[dict, bool]:
            payload = client.status(requested_session.value) or {}
            source = payload.get("source")
            # File.Exists dla dysku sieciowego/chmury moze czekac. Nie robimy
            # tego na watku GUI, bo podczas czekania NVDA stracilby cale okno.
            exists = (
                Path(source).is_file()
                if isinstance(source, str) and source.strip()
                else False
            )
            return payload, exists

        def done(result: tuple[dict, bool]) -> None:
            payload, source_exists = result
            self._last_status = payload or {}
            context, error = clip_context_from_status(
                payload,
                files_session_active=True,
                player_view_active=player_view_active,
                path_exists=lambda _path: source_exists,
            )
            if context is None:
                # Mowa pozostaje krotka i uzytkowa, ale prywatny dziennik ma
                # zachowac dowod, DLACZEGO host odrzucil I/O. Bez tego po
                # ponownym uruchomieniu widzielismy tylko efekt w NVDA, a nie
                # to, czy zniknelo Id, sciezka, czas czy wlasciwa sesja.
                store = getattr(self, "store", None)
                if store is not None:
                    _append_frontend_log(
                        store,
                        "Kontekst fragmentu odrzucony: "
                        f"żądana sesja={requested_session.value}; "
                        f"silnik={payload.get('engine')!r}; "
                        f"sesja hosta={payload.get('sessionId')!r}; "
                        f"id obecne={bool(payload.get('id'))}; "
                        f"źródło={payload.get('source')!r}; "
                        f"plik istnieje={source_exists}; "
                        f"pozycja={payload.get('positionSeconds')!r}; "
                        f"czas={payload.get('durationSeconds')!r}; "
                        f"powód={error or 'brak kontekstu'}",
                    )
                self.announcer.say(error or "Bieżący element nie jest lokalnym plikiem multimedialnym")
                return
            selection = restore_clip_selection(
                self.state.clip_selections,
                context.item_id,
                context.source_path,
                context.duration_seconds,
            )
            on_ready(context, selection)

        self.runner.submit(
            "audio-clip-context",
            work,
            done,
            lambda error: self.announcer.say(
                f"Nie można odczytać położenia fragmentu: {error}"
            ),
        )

    def _persist_audio_clip_selection(self, selection: AudioClipSelection) -> bool:
        previous = list(self.state.clip_selections)
        self.state.clip_selections = update_clip_selections(previous, selection)
        self.state.options = self.options.clamp()
        self.state.navigation = self.navigator.snapshot()
        try:
            self.store.save(self.state)
        except OSError as error:
            self.state.clip_selections = previous
            self.announcer.say(f"Nie mogę zapisać zaznaczenia fragmentu: {error}")
            return False
        return True

    def _mark_audio_clip(self, *, start: bool) -> None:
        def ready(context: AudioClipContext, selection: AudioClipSelection) -> None:
            marked_position = context.position_seconds
            marked_to_source_end = False
            if start:
                accepted = selection.set_start(
                    context.item_id,
                    context.source_path,
                    marked_position,
                    context.duration_seconds,
                )
                if not accepted:
                    self.announcer.say(
                        "Początek fragmentu musi znajdować się przed jego końcem"
                    )
                    return
            else:
                marked_position, marked_to_source_end = resolve_clip_end_position(
                    context,
                    getattr(self, "_audio_clip_track_end_intent", None),
                    now=time.monotonic(),
                )
                accepted = selection.set_end(
                    context.item_id,
                    context.source_path,
                    marked_position,
                    context.duration_seconds,
                )
                if not accepted:
                    self.announcer.say(
                        "Koniec fragmentu musi znajdować się po jego początku"
                    )
                    return
                self._audio_clip_track_end_intent = None
            if not self._persist_audio_clip_selection(selection):
                return

            if start:
                formatted_time = format_clip_time(selection.start_seconds or 0.0)
                text = f"Początek fragmentu: {formatted_time}"
                if selection.end_seconds is not None:
                    text += ". Długość: " + format_clip_time(
                        selection.end_seconds - (selection.start_seconds or 0.0)
                    )
            else:
                formatted_time = format_clip_time(selection.end_seconds or 0.0)
                text = f"Koniec fragmentu: {formatted_time}"
                if selection.start_seconds is not None:
                    text += ". Długość: " + format_clip_time(
                        (selection.end_seconds or 0.0) - selection.start_seconds
                    )
                else:
                    text += ". Ustaw początek klawiszem I"
                if marked_to_source_end:
                    text += ". Do końca pliku"
            self.announcer.say(text)

        self._request_audio_clip_context(ready)

    def _clear_audio_clip_selection(self) -> None:
        def ready(context: AudioClipContext, selection: AudioClipSelection) -> None:
            if selection.start_seconds is None and selection.end_seconds is None:
                self.announcer.say("Ten plik nie ma zaznaczonego fragmentu")
                return
            # Zachowujemy tozsamosc do usuniecia rekordu. ``Clear`` modelu C#
            # zeruje ja, a WPF przekazuje potem osobno biezacy MediaItem.
            empty = AudioClipSelection(
                item_id=context.item_id,
                source_path=context.source_path,
            )
            if self._persist_audio_clip_selection(empty):
                self.announcer.say("Zaznaczenie fragmentu wyczyszczone")

        self._request_audio_clip_context(ready)

    def _seek_to_audio_clip_position(self, target: float, label: str) -> None:
        client = self.client
        if client is None:
            return

        def done(payload: dict) -> None:
            raw_position = (payload or {}).get("positionSeconds")
            position = (
                float(raw_position)
                if isinstance(raw_position, (int, float)) and not isinstance(raw_position, bool)
                else target
            )
            self._last_status = {**self._last_status, "positionSeconds": position}
            if self.messages.seek_messages and self.messages.speaks_routine:
                self.announcer.say(f"{label} fragmentu: {format_clip_time(position)}")

        self.runner.submit(
            "audio-clip-seek",
            lambda: client.seek_to_position(target),
            done,
            lambda error: self.announcer.say(f"Nie mogę przejść do granicy fragmentu: {error}"),
        )

    def _jump_to_audio_clip_boundary(self, *, end: bool) -> None:
        def ready(context: AudioClipContext, selection: AudioClipSelection) -> None:
            if not selection.matches(context.item_id, context.source_path):
                self.announcer.say("Ten plik nie ma zaznaczonego fragmentu")
                return
            position = selection.end_seconds if end else selection.start_seconds
            if position is None:
                self.announcer.say(
                    "Nie ustawiono końca fragmentu"
                    if end
                    else "Nie ustawiono początku fragmentu"
                )
                return
            self._seek_to_audio_clip_position(position, "Koniec" if end else "Początek")

        self._request_audio_clip_context(ready)

    def _jump_to_relative_audio_clip_boundary(self, *, direction: int) -> None:
        def ready(context: AudioClipContext, selection: AudioClipSelection) -> None:
            if not selection.matches(context.item_id, context.source_path):
                self.announcer.say("Ten plik nie ma zaznaczonego fragmentu")
                return
            position = selection.find_relative_boundary(
                context.position_seconds, direction
            )
            if position is None:
                self.announcer.say(
                    "Brak poprzedniej granicy fragmentu"
                    if direction < 0
                    else "Brak następnej granicy fragmentu"
                )
                return
            label = "Początek" if position == selection.start_seconds else "Koniec"
            self._seek_to_audio_clip_position(position, label)

        self._request_audio_clip_context(ready)

    def _export_audio_clip(self) -> None:
        if self._audio_clip_export_in_progress:
            self.announcer.say("Zapisywanie fragmentu już trwa")
            return
        if self._audio_clip_edit_in_progress:
            self.announcer.say(
                "Dopisywanie fragmentu już trwa"
                if self._audio_clip_edit_kind == "append"
                else "Usuwanie fragmentu już trwa"
            )
            return

        def ready(context: AudioClipContext, selection: AudioClipSelection) -> None:
            if not selection.is_complete:
                self.announcer.say(
                    "Zaznacz początek klawiszem I i koniec klawiszem O"
                )
                return
            client = self.client
            if client is None:
                return

            def capabilities_done(payload: dict) -> None:
                choices = format_choices_from_payload(payload)
                if not choices:
                    self.announcer.say("Brak dostępnego sposobu zapisu fragmentu")
                    return
                notice = str((payload or {}).get("notice") or "").strip()
                self._choose_audio_clip_destination(
                    context, selection, choices, notice
                )

            self.runner.submit(
                "audio-clip-capabilities",
                lambda: client.audio_clip_capabilities(context.source_path),
                capabilities_done,
                lambda error: self.announcer.say(
                    f"Nie można przygotować zapisu fragmentu: {error}"
                ),
            )

        self._request_audio_clip_context(ready)

    def _choose_audio_clip_destination(
        self,
        context: AudioClipContext,
        selection: AudioClipSelection,
        choices: list[AudioClipFormatChoice],
        notice: str,
    ) -> None:
        dialog = AudioClipExportDialog(
            self,
            context=context,
            selection=selection,
            choices=choices,
            notice=notice,
        )
        chosen: AudioClipFormatChoice | None = None
        try:
            dialog.format_choice.SetFocus()
            if dialog.ShowModal() == wx.ID_OK:
                chosen = dialog.selected_format
        finally:
            dialog.Destroy()
        if chosen is None:
            self._restore_focus_after_dialog()
            return

        wildcard = (
            f"Plik FLAC (*{chosen.extension})|*{chosen.extension}"
            if chosen.value == "flac"
            else f"Plik WAV (*{chosen.extension})|*{chosen.extension}"
            if chosen.value == "wav"
            else f"Oryginalny format (*{chosen.extension})|*{chosen.extension}"
        )
        default_name = suggested_clip_file_name(context.title, chosen.extension)
        with wx.FileDialog(
            self,
            "Zapisz zaznaczony fragment jako nowy plik",
            defaultDir=str(Path(context.source_path).parent),
            defaultFile=default_name,
            wildcard=wildcard,
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as file_dialog:
            if file_dialog.ShowModal() != wx.ID_OK:
                self._restore_focus_after_dialog()
                return
            destination = file_dialog.GetPath()
        if not Path(destination).suffix:
            destination += chosen.extension
        self._start_audio_clip_export(context, selection, chosen, destination)

    def _start_audio_clip_export(
        self,
        context: AudioClipContext,
        selection: AudioClipSelection,
        chosen: AudioClipFormatChoice,
        destination: str,
    ) -> None:
        client = self.client
        if client is None or not selection.is_complete:
            return
        operation_id = uuid.uuid4().hex
        self._audio_clip_export_in_progress = True
        self._audio_clip_export_percent = 0
        self._audio_clip_export_operation_id = operation_id
        progress_text = f"Zapisywanie fragmentu: 0%. {Path(destination).name}"
        self.status_field.SetLabel(progress_text)
        self.status_bar.show(progress_text)
        self.announcer.say(f"Rozpoczęto zapisywanie fragmentu: {Path(destination).name}")

        def done(payload: dict) -> None:
            self._audio_clip_export_in_progress = False
            self._audio_clip_export_percent = 100
            self._audio_clip_export_operation_id = None
            name = str((payload or {}).get("name") or Path(destination).name)
            self.announcer.say(f"Fragment zapisany: {name}")
            self._restore_focus_after_dialog()

        def failed(error: Exception) -> None:
            self._audio_clip_export_in_progress = False
            self._audio_clip_export_percent = -1
            self._audio_clip_export_operation_id = None
            self.announcer.say(f"Nie udało się zapisać fragmentu: {error}")
            self._restore_focus_after_dialog()

        self.runner.submit(
            "audio-clip-export",
            lambda: client.export_audio_clip(
                source_path=context.source_path,
                destination_path=destination,
                start_seconds=selection.start_seconds or 0.0,
                end_seconds=selection.end_seconds or 0.0,
                format_value=chosen.value,
                operation_id=operation_id,
            ),
            done,
            failed,
        )

    def _append_audio_clip(self) -> None:
        if self._audio_clip_edit_in_progress:
            self.announcer.say(
                "Dopisywanie fragmentu już trwa"
                if self._audio_clip_edit_kind == "append"
                else "Usuwanie fragmentu już trwa"
            )
            return
        if self._audio_clip_export_in_progress:
            self.announcer.say("Zapisywanie fragmentu już trwa")
            return

        def ready(context: AudioClipContext, selection: AudioClipSelection) -> None:
            if not selection.is_complete:
                self.announcer.say(
                    "Zaznacz początek klawiszem I i koniec klawiszem O"
                )
                return
            client = self.client
            if client is None:
                return

            with wx.FileDialog(
                self,
                "Wybierz istniejący plik, na końcu którego dopisać fragment",
                defaultDir=str(Path(context.source_path).parent),
                wildcard=(
                    "Obsługiwane audio (*.wav;*.flac;*.mp3;*.m4a;*.aac;*.ogg;*.oga;*.opus)|"
                    "*.wav;*.flac;*.mp3;*.m4a;*.aac;*.ogg;*.oga;*.opus"
                ),
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
            ) as file_dialog:
                if file_dialog.ShowModal() != wx.ID_OK:
                    self._restore_focus_after_dialog()
                    return
                target_path = file_dialog.GetPath()
            self._restore_focus_after_dialog()

            def prepare() -> tuple[object, bool]:
                capabilities = client.audio_clip_append_capabilities(
                    context.source_path,
                    target_path,
                )
                keep_backup = resolve_keep_audio_edit_backups(
                    self.options.keep_audio_edit_backups,
                    self.layout.state_json
                )
                return capabilities, keep_backup

            def prepared(result: tuple[object, bool]) -> None:
                capabilities, keep_backup = result
                if not isinstance(capabilities, dict):
                    self.announcer.say(
                        "Nie można sprawdzić możliwości dopisania fragmentu. Pliki nie zostały zmienione"
                    )
                    return
                if capabilities.get("available") is not True:
                    message = str(capabilities.get("message") or "").strip()
                    self.announcer.say(
                        message
                        or "Dopisanie fragmentu do tego pliku jest niedostępne"
                    )
                    return
                if capabilities.get("requiresLossyReencode") is True:
                    if not self._confirm_audio_clip_append(keep_backup=keep_backup):
                        return
                self._start_audio_clip_append(
                    context,
                    selection,
                    target_path=target_path,
                    keep_backup=keep_backup,
                )

            self.runner.submit(
                "audio-clip-append-preflight",
                prepare,
                prepared,
                lambda error: self.announcer.say(str(error)),
            )

        self._request_audio_clip_context(ready)

    def _confirm_audio_clip_append(self, *, keep_backup: bool) -> bool:
        dialog = wx.MessageDialog(
            self,
            append_clip_confirmation_text(keep_backup=keep_backup),
            "Ponowna kompresja pliku docelowego",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING,
        )
        try:
            if hasattr(dialog, "SetName"):
                dialog.SetName("Potwierdzenie dopisania fragmentu")
            if hasattr(dialog, "SetYesNoLabels"):
                dialog.SetYesNoLabels(
                    "Tak, dopisz fragment",
                    "Nie, pozostaw plik",
                )
            confirmed = dialog.ShowModal() == wx.ID_YES
        finally:
            dialog.Destroy()
        self._restore_focus_after_dialog()
        if not confirmed:
            self.announcer.say("Dopisywanie fragmentu anulowane")
        return confirmed

    def _start_audio_clip_append(
        self,
        context: AudioClipContext,
        selection: AudioClipSelection,
        *,
        target_path: str,
        keep_backup: bool,
    ) -> None:
        client = self.client
        if client is None or not selection.is_complete:
            return
        operation_id = uuid.uuid4().hex
        self._audio_clip_edit_in_progress = True
        self._audio_clip_edit_kind = "append"
        self._audio_clip_edit_percent = 0
        self._audio_clip_edit_operation_id = operation_id
        target_name = Path(target_path).name
        progress_text = f"Dopisywanie fragmentu: 0%. {target_name}"
        self.status_field.SetLabel(progress_text)
        self.status_bar.show(progress_text)

        def done(payload: dict) -> None:
            self._audio_clip_edit_in_progress = False
            self._audio_clip_edit_kind = None
            self._audio_clip_edit_percent = 100
            self._audio_clip_edit_operation_id = None
            result = payload if isinstance(payload, dict) else {}
            backup_path = result.get("backupPath")
            backup_text = describe_backup_outcome(
                keep_backup,
                backup_path if isinstance(backup_path, str) else None,
            )
            if isinstance(backup_path, str) and backup_path.strip():
                backup_text += " " + Path(backup_path).name
            warning = result.get("reencodeWarning")
            warning_text = ""
            if isinstance(warning, str) and warning.strip():
                # Backend może dopisać do ostrzeżenia nazwę kopii. Los kopii
                # opisujemy niżej na podstawie osobnego, rzeczywistego pola.
                warning_text = warning.strip().split(" Poprzednia wersja", 1)[0]
            message = f"Fragment dopisany na końcu: {target_name}."
            if warning_text:
                message += f" {warning_text}"
            message += f" {backup_text}"
            self.status_field.SetLabel(message)
            self.status_bar.show(message)
            self.announcer.say(message)
            self._restore_focus_after_dialog()

        def failed(error: Exception) -> None:
            self._audio_clip_edit_in_progress = False
            self._audio_clip_edit_kind = None
            self._audio_clip_edit_percent = -1
            self._audio_clip_edit_operation_id = None
            message = f"Nie udało się dopisać fragmentu: {error}"
            self.status_field.SetLabel(message)
            self.status_bar.show(message)
            self.announcer.say(message)
            self._restore_focus_after_dialog()

        self.runner.submit(
            "audio-clip-append",
            lambda: client.append_audio_clip(
                source_path=context.source_path,
                target_path=target_path,
                start_seconds=selection.start_seconds or 0.0,
                end_seconds=selection.end_seconds or 0.0,
                keep_backup=keep_backup,
                operation_id=operation_id,
            ),
            done,
            failed,
        )

    def _remove_audio_clip(self) -> None:
        if self._audio_clip_edit_in_progress:
            self.announcer.say(
                "Dopisywanie fragmentu już trwa"
                if self._audio_clip_edit_kind == "append"
                else "Usuwanie fragmentu już trwa"
            )
            return
        if self._audio_clip_export_in_progress:
            self.announcer.say("Zapisywanie fragmentu już trwa")
            return

        def ready(context: AudioClipContext, selection: AudioClipSelection) -> None:
            if not selection.is_complete:
                self.announcer.say(
                    "Zaznacz początek klawiszem I i koniec klawiszem O"
                )
                return
            client = self.client
            if client is None:
                return

            def prepare() -> tuple[object, bool]:
                capabilities = client.audio_clip_removal_capabilities(
                    context.source_path
                )
                keep_backup = resolve_keep_audio_edit_backups(
                    self.options.keep_audio_edit_backups,
                    self.layout.state_json
                )
                return capabilities, keep_backup

            def prepared(result: tuple[object, bool]) -> None:
                capabilities, keep_backup = result
                if not isinstance(capabilities, dict):
                    self.announcer.say(
                        "Nie można sprawdzić możliwości edycji pliku. Oryginalny plik nie został zmieniony"
                    )
                    return
                if capabilities.get("available") is not True:
                    message = str(capabilities.get("message") or "").strip()
                    self.announcer.say(
                        message
                        or "Usuwanie fragmentu z tego pliku jest niedostępne"
                    )
                    return
                self._confirm_audio_clip_removal(
                    context,
                    selection,
                    keep_backup=keep_backup,
                )

            self.runner.submit(
                "audio-clip-remove-preflight",
                prepare,
                prepared,
                lambda error: self.announcer.say(str(error)),
            )

        self._request_audio_clip_context(ready)

    def _confirm_audio_clip_removal(
        self,
        context: AudioClipContext,
        selection: AudioClipSelection,
        *,
        keep_backup: bool,
    ) -> None:
        if not selection.is_complete:
            return
        dialog = wx.MessageDialog(
            self,
            remove_clip_confirmation_text(
                selection.start_seconds or 0.0,
                selection.end_seconds or 0.0,
                keep_backup=keep_backup,
            ),
            "Usuń fragment z oryginalnego pliku",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING,
        )
        try:
            # Jawne etykiety sa wazne dla NVDA: uzytkownik slyszy skutek
            # przycisku, a nie samo ogolne "Tak" / "Nie".
            if hasattr(dialog, "SetName"):
                dialog.SetName("Potwierdzenie usunięcia fragmentu")
            if hasattr(dialog, "SetYesNoLabels"):
                dialog.SetYesNoLabels(
                    "Tak, usuń fragment",
                    "Nie, pozostaw plik",
                )
            confirmed = dialog.ShowModal() == wx.ID_YES
        finally:
            dialog.Destroy()
        self._restore_focus_after_dialog()
        if not confirmed:
            return
        self._start_audio_clip_removal(
            context,
            selection,
            keep_backup=keep_backup,
        )

    def _start_audio_clip_removal(
        self,
        context: AudioClipContext,
        selection: AudioClipSelection,
        *,
        keep_backup: bool,
    ) -> None:
        client = self.client
        if client is None or not selection.is_complete:
            return
        operation_id = uuid.uuid4().hex
        self._audio_clip_edit_in_progress = True
        self._audio_clip_edit_kind = "remove"
        self._audio_clip_edit_percent = 0
        self._audio_clip_edit_operation_id = operation_id
        progress_text = f"Usuwanie fragmentu: 0%. {Path(context.source_path).name}"
        self.status_field.SetLabel(progress_text)
        self.status_bar.show(progress_text)

        def done(payload: dict) -> None:
            self._audio_clip_edit_in_progress = False
            self._audio_clip_edit_kind = None
            self._audio_clip_edit_percent = 100
            self._audio_clip_edit_operation_id = None
            result = payload if isinstance(payload, dict) else {}
            raw_duration = result.get("durationSeconds")
            duration = (
                float(raw_duration)
                if isinstance(raw_duration, (int, float))
                and not isinstance(raw_duration, bool)
                else max(
                    0.0,
                    context.duration_seconds
                    - ((selection.end_seconds or 0.0) - (selection.start_seconds or 0.0)),
                )
            )
            next_position = min(selection.start_seconds or 0.0, duration)
            self._last_status = {
                **self._last_status,
                "positionSeconds": next_position,
                "durationSeconds": duration,
                "paused": False,
            }
            empty = AudioClipSelection(
                item_id=context.item_id,
                source_path=context.source_path,
            )
            self._persist_audio_clip_selection(empty)

            backup_path = result.get("backupPath")
            backup_text = describe_backup_outcome(
                keep_backup,
                backup_path if isinstance(backup_path, str) else None,
            )
            if isinstance(backup_path, str) and backup_path.strip():
                backup_text += " " + Path(backup_path).name
            message = f"Fragment usunięty. {backup_text}"
            self.status_field.SetLabel(message)
            self.status_bar.show(message)
            self.announcer.say(message)
            self._restore_focus_after_dialog()

        def failed(error: Exception) -> None:
            self._audio_clip_edit_in_progress = False
            self._audio_clip_edit_kind = None
            self._audio_clip_edit_percent = -1
            self._audio_clip_edit_operation_id = None
            message = f"Nie udało się usunąć fragmentu: {error}"
            self.status_field.SetLabel(message)
            self.status_bar.show(message)
            self.announcer.say(message)
            self._restore_focus_after_dialog()

        self.runner.submit(
            "audio-clip-remove",
            lambda: client.remove_audio_clip(
                source_path=context.source_path,
                start_seconds=selection.start_seconds or 0.0,
                end_seconds=selection.end_seconds or 0.0,
                source_duration_seconds=context.duration_seconds,
                keep_backup=keep_backup,
                operation_id=operation_id,
            ),
            done,
            failed,
        )

    def _play_from_queue(self, intent: PlayFromQueue) -> None:
        """Start ZYWEJ kolejki hosta od wybranego wiersza.

        Dwa zadania pod rzad w JEDNYM watku roboczym: ``queue.set`` wczytuje
        kolejnosc (nic nie gra), ``queue.playAt`` zaczyna od wskazanej pozycji.
        Rozdzielone, bo samo wejscie w widok nie moze niczego odtworzyc.
        """
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie dziala, nie moge odtworzyc")
            return

        items = [
            # ``isInQueue``/``isPlayNext`` sa WYMAGANE: pozycja bez zadnej z
            # nich nie jest dla hosta czescia kolejki
            # (``LiteQueueCoordinator.Set`` -> ``SynchronizeQueueOrder``) i
            # utwor zagra, ale naturalny koniec NIE poprowadzi dalej.
            # Wartosci bierzemy z ODCZYTU profilu, a nie wymuszamy ``True``:
            # inaczej blok "odtworz nastepne" zlalby sie ze zwykla kolejka.
            {
                "id": row.item_id,
                "path": row.path,
                "title": row.title,
                "isInQueue": intent.flags.get(row.item_id, (True, False))[0],
                "isPlayNext": intent.flags.get(row.item_id, (True, False))[1],
            }
            for row in intent.rows
        ]
        # Kolejnosc WIDOKU podajemy jawnie. Bez ``order`` host odtworzylby ja z
        # kolejnosci ``items``, co dzis wychodzi na to samo -- ale jawny
        # kontrakt nie zalezy od tej zbieznosci.
        order = [row.item_id for row in intent.rows]

        def work() -> dict:
            client.configure_audio(
                **session_options.resolve_audio_payload(
                    self.options,
                    session_options.effective_overrides(
                        self.state, SessionId.FILES
                    ),
                )
            )
            client.queue_set(items, order=order)
            return client.queue_play_at(
                intent.item_id, volume=self.options.volume, rate=self.options.rate
            )

        def done(payload: dict) -> None:
            self._note_queue_persistence(payload or {})
            self._refresh_status()

        def failed(error: Exception) -> None:
            self._run(self.navigator.note_playback_failed(f"Nie udalo sie odtworzyc: {error}"))

        self.runner.submit("playback", work, done, failed)

    def _open_queue_view(self) -> None:
        """Ctrl+Q: stan hosta, także po zużyciu ostatniego wiersza.

        Zapis profilu służy tylko jako początek, zanim host przyjął kolejkę.
        Pusta zainicjalizowana kolejka nie odtwarza zużytych wpisów z dysku.
        """
        client = self.client
        if client is None:
            self._run(self.navigator.open_library_view(LibraryView.SAVED_QUEUE))
            return

        def work() -> dict:
            return client.queue_status()

        def done(payload: dict) -> None:
            rows = rows_from_queue_status(payload or {})
            if not rows and not payload.get("initialized", False):
                # Jeszcze nie wczytano żadnej kolejki do tego hosta.
                self._run(self.navigator.open_library_view(LibraryView.SAVED_QUEUE))
                return
            current = payload.get("currentId")
            self._run(self.navigator.apply_live_queue(
                rows, current_id=str(current) if current else None
            ))

        def failed(error: Exception) -> None:
            # Brak odpowiedzi silnika nie moze skonczyc sie cisza ani pusta
            # lista: mowimy, co sie stalo, i oddajemy widok zapisany.
            self.announcer.say(f"Nie moge odczytac kolejki silnika: {error}")
            self._run(self.navigator.open_library_view(LibraryView.SAVED_QUEUE))

        self.runner.submit("folder", work, done, failed)

    def _toggle_queue_membership(self, play_next: bool) -> None:
        """Zmień kolejkę dla natywnego wielokrotnego zaznaczenia.

        Pliki i podcasty mają zwykłą kolejkę oraz „odtwórz jako następne”.
        TIDAL ma własną trwałą kolejkę, ale nie obiecuje „następnego”, którego
        oryginalna aplikacja TIDAL nie udostępnia. Nie składamy aktywnej kolejki
        ponownie, więc grający plik, pozycja, pauza i wyjście audio pozostają
        nietknięte.
        """
        if self.navigator.active is SessionId.PODCASTS:
            self._toggle_podcast_queue(play_next)
            return
        if self.navigator.active is SessionId.TIDAL and not play_next:
            self._toggle_tidal_queue()
            return
        if self.navigator.active is not SessionId.FILES:
            self.announcer.say("To polecenie dotyczy Biblioteki plików")
            return
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie działa, nie mogę zmienić kolejki")
            return

        rows = self._selected_action_rows()
        if not rows:
            self.announcer.say("Nie wybrano żadnego pliku")
            return
        if any(row.kind != "track" for row in rows):
            self.announcer.say("Do kolejki można dodać tylko pliki")
            return

        items = [
            {"id": row.item_id, "title": row.title, "path": row.path}
            for row in rows
        ]
        call = (
            client.queue_toggle_play_next
            if play_next
            else client.queue_toggle_membership
        )

        def done(payload: dict) -> None:
            payload = payload or {}
            self._note_queue_persistence(payload)
            changed = int(payload.get("changed") or 0)
            if changed <= 0:
                self.announcer.say("Kolejka bez zmian")
                return
            label = rows[0].title if changed == 1 else format_item_count(changed)
            added = bool(payload.get("added"))
            if play_next:
                message = LiteFrame._routine_template_text(
                    self,
                    "playnext.added" if added else "playnext.removed",
                    item=label,
                )
            else:
                message = LiteFrame._routine_template_text(
                    self,
                    "queue.added" if added else "queue.removed",
                    item=label,
                )
            LiteFrame._announce_routine_text(self, message)
            self._refresh_live_queue()

        def failed(error: Exception) -> None:
            self.announcer.say(f"Nie mogę zmienić kolejki: {error}")

        self.runner.submit("queue-membership", lambda: call(items), done, failed)

    def _manage_playlist_membership(self) -> None:
        """Ctrl+Shift+P: pełne, atomowe okno playlist głównego AMC."""
        active = self.navigator.active
        supported = {
            SessionId.FILES: ("local", "track", "Wybierz plik"),
            SessionId.RADIO: ("radio", "station", "Wybierz stację radiową"),
            SessionId.PODCASTS: ("podcasts", "episode", "Wybierz odcinek podcastu"),
        }
        contract = supported.get(active)
        if contract is None:
            self.announcer.say("Playlisty AMC nie są dostępne w tej sesji")
            return
        if self._playlist_membership_pending:
            self.announcer.say("Zmiana playlist już trwa")
            return
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie działa, nie mogę otworzyć playlist")
            return
        session_id, expected_kind, empty_message = contract
        rows = [
            row for row in self._selected_action_rows()
            if row.kind == expected_kind and row.item_id
        ]
        if not rows:
            self.announcer.say(empty_message)
            return
        item_ids = list(dict.fromkeys(row.item_id for row in rows))
        preferred_id = item_ids[0]
        target_label = (
            rows[0].title
            if len(item_ids) == 1
            else format_item_count(len(item_ids))
        )
        origin_session = active
        self._playlist_membership_pending = True

        def load() -> dict:
            result = client.profile_playlists(session_id)
            return result if isinstance(result, dict) else {}

        def loaded(payload: dict) -> None:
            if self.navigator.active is not origin_session:
                self._playlist_membership_pending = False
                return
            try:
                choices = playlist_choices_from_payload(payload, item_ids)
            except PlaylistPayloadError as error:
                self._playlist_membership_pending = False
                self.announcer.say(str(error))
                return
            original = [choice.payload() for choice in choices]
            with PlaylistMembershipDialog(
                self,
                choices=choices,
                selected_item_ids=item_ids,
                target_label=target_label,
            ) as dialog:
                if dialog.ShowModal() != wx.ID_OK:
                    self._playlist_membership_pending = False
                    self._restore_focus_after_dialog()
                    return
                replacements = dialog.result_playlists
            self._restore_focus_after_dialog()
            if replacements == original:
                self._playlist_membership_pending = False
                self.announcer.say(f"Playlisty bez zmian dla: {target_label}")
                return

            def save() -> dict:
                result = client.replace_profile_playlists(session_id, replacements)
                return result if isinstance(result, dict) else {}

            def saved(_result: dict) -> None:
                self._playlist_membership_pending = False
                message = f"Zapisano zmiany playlist dla: {target_label}"
                if (
                    self.navigator.active is origin_session
                    and self.navigator.session.view is View.LIST
                ):
                    self._refresh_profile_view(preferred_id=preferred_id)
                self.announcer.say(message)

            def save_failed(error: Exception) -> None:
                self._playlist_membership_pending = False
                self.announcer.say(f"Nie zapisano zmian playlist: {error}")

            self.runner.submit("playlist-membership-save", save, saved, save_failed)

        def load_failed(error: Exception) -> None:
            self._playlist_membership_pending = False
            self.announcer.say(f"Nie mogę odczytać playlist: {error}")

        self.runner.submit("playlist-membership-load", load, loaded, load_failed)

    def _toggle_profile_favorite(self) -> None:
        """Ctrl+Shift+U dla lokalnych plików i stacji radiowych."""
        active = self.navigator.active
        if active not in (SessionId.FILES, SessionId.RADIO):
            self.announcer.say("Ulubione nie są dostępne w tej sesji")
            return
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie działa, nie mogę zmienić Ulubionych")
            return
        expected_kind = "track" if active is SessionId.FILES else "station"
        rows = [
            row for row in self._selected_action_rows()
            if row.kind == expected_kind and row.item_id
        ]
        if not rows:
            self.announcer.say(
                "Wybierz plik" if active is SessionId.FILES else "Wybierz stację radiową"
            )
            return
        session_id = "files" if active is SessionId.FILES else "radio"
        item_ids = list(dict.fromkeys(row.item_id for row in rows))
        preferred_id = item_ids[0]

        def done(payload: dict) -> None:
            payload = payload or {}
            changed = int(payload.get("changed") or 0)
            favorite = bool(payload.get("favorite"))
            label = rows[0].title if len(item_ids) == 1 else format_item_count(len(item_ids))
            if changed <= 0:
                message = "Ulubione bez zmian"
            else:
                message = LiteFrame._routine_template_text(
                    self,
                    "favorite.added" if favorite else "favorite.removed",
                    item=label,
                )
            if self.navigator.session.view is View.PLAYER:
                if changed <= 0:
                    self.announcer.say(message)
                else:
                    LiteFrame._announce_routine_text(self, message)
                return
            self._refresh_profile_view(preferred_id=preferred_id)
            if changed <= 0:
                self.announcer.say(message)
            else:
                LiteFrame._announce_routine_text(self, message)

        def failed(error: Exception) -> None:
            self.announcer.say(f"Nie mogę zmienić Ulubionych: {error}")

        self.runner.submit(
            "profile-favorite",
            lambda: client.toggle_profile_favorites(session_id, item_ids),
            done,
            failed,
        )

    def _open_tidal_queue(self, preferred_id: str | None = None) -> None:
        self._transient_preview_return = None
        self._run(self.navigator.apply_tidal_queue(
            list(self._tidal_queue_rows),
            preferred_id=preferred_id,
        ))

    def _toggle_tidal_queue(self) -> None:
        """Ctrl+Shift+Q: prywatna, trwała kolejka do oryginalnego TIDALa."""
        selected = [
            row for row in self._selected_action_rows()
            if row.kind == "track" and row.service_id
            and row.related_album_service_id
        ]
        if not selected:
            self.announcer.say(
                "Do kolejki TIDAL wybierz utwór, który ma dane albumu"
            )
            return
        existing = {row.item_id for row in self._tidal_queue_rows}
        remove = all(row.item_id in existing for row in selected)
        selected_ids = {row.item_id for row in selected}
        if remove:
            self._tidal_queue_rows = [
                row for row in self._tidal_queue_rows
                if row.item_id not in selected_ids
            ]
        else:
            self._tidal_queue_rows.extend(
                row for row in selected if row.item_id not in existing
            )
        previous = list(self.state.tidal_queue_items)
        self.state.tidal_queue_items = tidal_queue_payload(self._tidal_queue_rows)
        try:
            self.store.save(self.state)
        except OSError as error:
            self.state.tidal_queue_items = previous
            self.announcer.say(f"Nie zapisano kolejki TIDAL: {error}")
            return
        label = (
            selected[0].title if len(selected) == 1
            else format_item_count(len(selected))
        )
        LiteFrame._announce_routine_text(
            self,
            LiteFrame._routine_template_text(
                self,
                "queue.removed" if remove else "queue.added",
                item=label,
            ),
        )
        state = self.navigator.sessions[SessionId.TIDAL]
        if state.library_view is LibraryView.TIDAL_QUEUE:
            self._open_tidal_queue(
                preferred_id=None if remove else selected[0].item_id
            )

    def _refresh_live_queue(self) -> None:
        """Odśwież już otwartą kolejkę bez nawigacji i przejmowania fokusu."""
        state = self.navigator.session
        if state.library_view is not LibraryView.LIVE_QUEUE or self.client is None:
            return
        client = self.client

        def current() -> bool:
            return (
                self.navigator.session is state
                and state.library_view is LibraryView.LIVE_QUEUE
            )

        def done(payload: dict) -> None:
            if not current():
                return
            rows = rows_from_queue_status(payload or {})
            if rows == state.model.rows:
                return
            state.model.replace(rows, preferred_id=state.model.selected_id)
            self._sync_views()

        def failed(error: Exception) -> None:
            if current():
                self.announcer.say(f"Nie mogę odświeżyć kolejki: {error}")

        self.runner.submit("queue-refresh", client.queue_status, done, failed)

    def _play_queue_at(self, intent: PlayQueueAt) -> None:
        """Enter w ZYWYM widoku: start od wiersza kolejki, ktora host juz ma.

        Bez ``queue.set``: kolejka po stronie hosta JEST stanem, a nie kopia
        ekranu. Ponowne wyslanie jej z wierszy widoku skasowalo by to, co sesja
        Core wie o pozycjach juz odegranych.
        """
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie dziala, nie moge odtworzyc")
            return

        def work() -> dict:
            client.configure_audio(
                **session_options.resolve_audio_payload(
                    self.options,
                    session_options.effective_overrides(
                        self.state, SessionId.FILES
                    ),
                )
            )
            return client.queue_play_at(
                intent.item_id, volume=self.options.volume, rate=self.options.rate
            )

        def done(payload: dict) -> None:
            self._note_queue_persistence(payload or {})
            self._refresh_status()

        def failed(error: Exception) -> None:
            self._run(self.navigator.note_playback_failed(f"Nie udalo sie odtworzyc: {error}"))

        self.runner.submit("playback", work, done, failed)

    def _queue_step(self, forward: bool) -> None:
        """Page Down / Page Up: lista zrodlowa ALBO prawdziwa kolejka.

        Pełne AMC zmienia element źródła, z którego otwarto odtwarzacz. Tylko
        wejście z Zapisanej/Zywej kolejki deleguje krok do koordynatora hosta.
        Dawniej każde naciśnięcie szło do ``queue.*`` i zwykły plik albo stacja
        kończyły komunikatem „początek/koniec kolejki”.
        """
        if self.navigator.active is SessionId.WIIM:
            self._wiim_transport("next" if forward else "previous")
            return
        if self.navigator.active is SessionId.SONOS:
            self._sonos_transport("next" if forward else "previous")
            return

        source_intents = self.navigator.step_playback_source(forward)
        if source_intents is not None:
            self._run(source_intents)
            return

        if self.navigator.active is SessionId.TIDAL:
            self._tidal_external_skip(forward)
            return

        client = self.client
        if client is None:
            self.announcer.say("Silnik nie dziala")
            return

        call = client.queue_next if forward else client.queue_previous

        def work() -> dict:
            return call(volume=self.options.volume, rate=self.options.rate)

        def done(payload: dict) -> None:
            # Mowimy to, co host NAPRAWDE zaczal grac, a nie to, o co prosilismy.
            if payload and payload.get("moved"):
                title = str(payload.get("currentTitle") or "").strip()
                self._run(self.navigator.note_queue_advanced(
                    str(payload.get("currentId") or ""), title
                ))
            else:
                self.announcer.say(
                    "Koniec kolejki" if forward else "Poczatek kolejki"
                )
            self._note_queue_persistence(payload or {})
            self._refresh_status()

        def failed(error: Exception) -> None:
            self.announcer.say(f"Nie moge zmienic utworu: {error}")

        self.runner.submit("playback", work, done, failed)

    def _tidal_external_skip(self, forward: bool) -> None:
        """Fallback to TIDAL's own queue only when AMC has no source list."""
        client = self.client
        if client is None or not self._tidal_desktop_has_playback:
            self.announcer.say("Najpierw uruchom utwór w oryginalnym TIDALu")
            return

        command = "next" if forward else "previous"

        def done(payload: dict) -> None:
            result = payload or {}
            if not bool(result.get("handled")):
                self._tidal_desktop_has_playback = False
            self.announcer.say(str(
                result.get("message")
                or ("Oryginalny TIDAL nie ma następnego utworu"
                    if forward else
                    "Oryginalny TIDAL nie ma poprzedniego utworu")
            ))

        self.runner.submit(
            "tidal-transport",
            lambda: client.tidal_external_transport(command),
            done,
            lambda error: self.announcer.say(
                f"Nie mogę sterować oryginalnym TIDALem: {error}"
            ),
        )

    def _play_station(self, intent: PlayStation) -> None:
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie dziala, nie moge odtworzyc")
            return
        self._pending_playback_session = SessionId.RADIO

        def work() -> dict:
            return client.play_station(
                intent.url, volume=self.options.volume, item_id=intent.item_id, title=intent.title
            )

        def done(_payload: dict) -> None:
            self._playing_session = SessionId.RADIO
            self._playing_sessions.add(SessionId.RADIO)
            self._refresh_status()

        def failed(error: Exception) -> None:
            if self._pending_playback_session is SessionId.RADIO:
                self._pending_playback_session = None
            self._run(self.navigator.note_playback_failed(f"Nie moge polaczyc ze stacja: {error}"))

        self.runner.submit("playback", work, done, failed)

    def _pause_on_player_exit_if_needed(self, session: SessionId) -> None:
        """Wstrzymaj po wyjsciu z odtwarzacza, jesli TA sesja tak ma ustawione.

        Port ``MainWindow.ApplyPlaybackPolicyWhenLeavingPlayer``
        (MainWindow.xaml.cs:2396-2420) zwezony do tego, co port ma dzisiaj.
        Oryginal stosuje polityke WYLACZNIE przy powrocie na liste
        (``ShouldApplyPlaybackExitPolicy`` -> ``ReturnToList``), a w porcie
        Escape, F6 i menu "Powrót na listę" wszystkie prowadza do
        ``navigator.back_to_list()`` -- dlatego guard stoi dokladnie tam.

        Trzy warunki odmowy, kazdy z powodem:

        * wychodząca sesja nie ma własnego aktywnego toru; Radio i
          Pliki/Podcasty są pamiętane niezależnie, a polecenie niesie sessionId,
        * nic nie gra w tej sesji (odpowiednik ``session.HasCurrentItem``),
        * host juz jest wstrzymany -- ``pauseResume`` to przelacznik, wiec
          drugie wywolanie WZNOWILO by odtwarzanie, czyli dokladnie odwrotnie
          niz zada opcja (oryginal ma na to ``session.IsPlaying``).

        Zapisana opcja zastepuje sama REGULE pauzy. Zaznaczenie, filtr i widok
        listy zostaja nietkniete -- to osobna droga (``back_to_list``).
        """
        client = self.client
        if client is None:
            return
        playing_sessions = getattr(self, "_playing_sessions", set())
        if session not in playing_sessions and self._playing_session is not session:
            return
        state = self.navigator.sessions.get(session)
        if state is None or state.now_playing_id is None:
            return
        if not session_options.resolve_pause_on_player_exit(
            self.options, session_options.effective_overrides(self.state, session)
        ):
            return
        statuses = getattr(self, "_transport_status_by_session", {})
        status = statuses.get(session, self._last_status)
        if bool(status.get("paused")):
            return

        def done(payload: dict) -> None:
            paused = bool((payload or {}).get("paused"))
            updated = {**status, **(payload or {}), "paused": paused}
            statuses[session] = updated
            self._transport_status_by_session = statuses
            if self.navigator.active is session:
                self._last_status = updated
            self._set_transport_label(playing=not paused)

        # Przez istniejacy TaskRunner z bramka zywego kontekstu: synchroniczne
        # wywolanie hosta na watku GUI zawiesilo by okno na czas call timeout.
        self.runner.submit(
            "playback",
            lambda: client.pause_resume(session.value),
            done,
            lambda _error: None,
        )

    def _leave_player_to_list(self) -> None:
        """Wyjscie z odtwarzacza na liste: najpierw polityka, potem nawigacja.

        Kolejnosc jak w oryginale (MainWindow.xaml.cs:2335-2338): polityka
        pauzy czyta stan sesji SPRZED przebudowy widoku.
        """
        session = self.navigator.active
        if self.navigator.session.view is View.PLAYER:
            self._pause_on_player_exit_if_needed(session)
        self._run(self.navigator.back_to_list(
            follow_playback=self.options.follow_playback_on_player_exit
        ))

    def _choose_audio_output(self) -> None:
        """Shift+A: wybierz i zapamietaj wyjscie osobno dla jednej sesji."""
        if self.navigator.active is SessionId.WIIM:
            self.announcer.say(
                "WiiM odtwarza na własnym urządzeniu sieciowym. "
                "Wybierz urządzenie z listy sesji WiiM"
            )
            return
        if self.navigator.active is SessionId.SONOS:
            self.announcer.say(
                "Sonos odtwarza na własnej grupie głośników. "
                "Wybierz grupę z listy sesji Sonos"
            )
            return
        if self.navigator.active is SessionId.TIDAL:
            self.announcer.say(
                "TIDAL korzysta z urządzenia domyślnego swojego odtwarzacza. "
                "Osobny wybór urządzenia nie jest jeszcze dostępny"
            )
            return
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie jest gotowy")
            return
        session = self.navigator.active
        session_name = session_options.session_display_name(session)
        previous_device_id = effective_output_device_id(
            session,
            self.state.audio_output_device_ids_by_session,
            self._profile_audio_outputs,
        )

        def prepared(payload: dict) -> None:
            choices = choices_from_payload(payload)
            if not choices:
                self.announcer.say("Nie udało się odczytać urządzeń audio")
                return
            dialog = AudioOutputDeviceDialog(
                self,
                session_name,
                choices,
                previous_device_id,
            )
            selected: AudioOutputChoice | None = None
            try:
                if dialog.ShowModal() == wx.ID_OK:
                    selected = dialog.selected_choice
            finally:
                dialog.Destroy()
            self._restore_focus_after_dialog()
            if selected is None:
                return
            self._apply_audio_output_choice(
                client,
                session,
                session_name,
                previous_device_id,
                selected,
            )

        self.runner.submit(
            "audio-output-list",
            lambda: client.audio_outputs(previous_device_id, session.value),
            prepared,
            lambda error: self.announcer.say(
                f"Nie udało się odczytać urządzeń audio: {error}"
            ),
        )

    def _cycle_audio_output(self, direction: int) -> None:
        """Ctrl+[ / Ctrl+]: switch one local session without a dialog."""

        session = self.navigator.active
        if session is SessionId.WIIM:
            self.announcer.say(
                "WiiM odtwarza na własnym urządzeniu sieciowym. "
                "Wybierz urządzenie z listy sesji WiiM"
            )
            return
        if session is SessionId.SONOS:
            self.announcer.say(
                "Sonos odtwarza na własnej grupie głośników. "
                "Wybierz grupę z listy sesji Sonos"
            )
            return
        if session is SessionId.TIDAL:
            self.announcer.say(
                "TIDAL korzysta z urządzenia wybranego w oryginalnym odtwarzaczu"
            )
            return
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie jest gotowy")
            return
        session_name = session_options.session_display_name(session)
        previous_device_id = effective_output_device_id(
            session,
            self.state.audio_output_device_ids_by_session,
            self._profile_audio_outputs,
        )

        def prepared(payload: dict) -> None:
            choices = choices_from_payload(payload)
            selected = adjacent_available_choice(
                choices,
                previous_device_id,
                direction,
            )
            if selected is None or selected.device_id == previous_device_id:
                self.announcer.say(
                    f"Brak innego dostępnego urządzenia audio dla sesji {session_name}"
                )
                return
            self._apply_audio_output_choice(
                client,
                session,
                session_name,
                previous_device_id,
                selected,
            )

        self.runner.submit(
            "audio-output-list",
            lambda: client.audio_outputs(previous_device_id, session.value),
            prepared,
            lambda error: self.announcer.say(
                f"Nie udało się odczytać urządzeń audio: {error}"
            ),
        )

    def _apply_audio_output_choice(
        self,
        client: LiteHostClient,
        session: SessionId,
        session_name: str,
        previous_device_id: str | None,
        selected: AudioOutputChoice,
    ) -> None:
        """Apply, persist and if necessary roll back one output selection."""

        previous_private = dict(self.state.audio_output_device_ids_by_session)

        def applied(result: dict) -> None:
            next_private = dict(previous_private)
            next_private[session.value] = selected.device_id or ""
            self.state.audio_output_device_ids_by_session = next_private
            if not self._save_state():
                self.state.audio_output_device_ids_by_session = previous_private
                # The engine already applied the choice. Restore the exact
                # previous effective endpoint so memory, sound and disk agree.
                self.runner.submit(
                    "audio-output-rollback",
                    lambda: client.select_audio_output(
                        session.value,
                        previous_device_id,
                        restart=True,
                    ),
                    lambda _payload: None,
                    lambda _error: None,
                )
                return
            self.announcer.say(audio_output_selection_message(
                selected.label,
                using_default=(
                    selected.device_id is not None
                    and bool((result or {}).get("usingDefault"))
                ),
            ))

        self.runner.submit(
            "audio-output-select",
            lambda: client.select_audio_output(
                session.value,
                selected.device_id,
                restart=True,
            ),
            applied,
            lambda error: self.announcer.say(
                f"Nie zmieniono urządzenia audio: {error}"
            ),
        )

    def _show_general_playback_options(self) -> None:
        """Ustawienia ogolne wxPython z natychmiastowym, atomowym zapisem."""
        effective_wake = radio_schedule_settings.effective_wake(
            self._radio_snapshot.wake_scheduled_recordings,
            self.state.radio_schedule_wake_override,
        )
        try:
            podcast_settings = self.podcasts.global_settings()
        except PodcastProfileError:
            podcast_settings = PodcastGlobalSettings()
        try:
            keep_audio_edit_backups = resolve_keep_audio_edit_backups(
                self.options.keep_audio_edit_backups,
                self.layout.state_json,
            )
        except AudioEditSettingsReadError:
            # Nie blokuj pozostałych ustawień przez uszkodzony stary profil.
            # Włączenie kopii jest tu bezpiecznym wyborem: niczego nie usuwa,
            # a zapis okna ustanowi od tej chwili jawną politykę wxPython.
            keep_audio_edit_backups = True
            self.announcer.say(
                "Nie można odczytać poprzedniego ustawienia kopii po edycji. "
                "Wybrano zachowywanie kopii"
            )
        custom_seek_seconds = resolve_custom_seek_seconds(
            self.options.custom_seek_seconds,
            self.messages.custom_seek_seconds,
        )
        global_transient_previews = resolve_global_transient_previews(
            self.options.global_transient_previews,
            self._global_transient_previews,
        )
        remember_local_playback_positions = (
            resolve_remember_local_playback_positions(
                self.options.remember_local_playback_positions,
                self._remember_local_playback_positions,
            )
        )
        detailed_hints = resolve_detailed_hints(
            self.options.detailed_hints,
            self._detailed_hints,
        )
        dialog = GeneralPlaybackOptionsDialog(
            self,
            self.options,
            self._radio_snapshot.recording,
            effective_wake,
            podcast_settings,
            keep_audio_edit_backups,
            custom_seek_seconds,
            global_transient_previews,
            remember_local_playback_positions,
            detailed_hints,
            self.messages,
        )
        chosen: dict[str, object] | None = None
        try:
            if dialog.ShowModal() == wx.ID_OK:
                chosen = dialog.values
        finally:
            dialog.Destroy()
        self._restore_focus_after_dialog()
        if chosen is None:
            return

        chosen_wake = bool(chosen.pop("radio_schedule_wake_override"))
        previous = {name: getattr(self.options, name) for name in chosen}
        previous_wake = self.state.radio_schedule_wake_override
        for name, value in chosen.items():
            setattr(self.options, name, value)
        self.state.radio_schedule_wake_override = chosen_wake
        if not self._save_state():
            for name, value in previous.items():
                setattr(self.options, name, value)
            self.state.radio_schedule_wake_override = previous_wake
            self.state.options = self.options
            return
        self._radio_snapshot = LiteFrame._with_radio_recording_options(
            self, self._radio_snapshot
        )
        self.messages.custom_seek_seconds = resolve_custom_seek_seconds(
            self.options.custom_seek_seconds,
            self.messages.custom_seek_seconds,
        )
        self._global_transient_previews = resolve_global_transient_previews(
            self.options.global_transient_previews,
            self._global_transient_previews,
        )
        self._remember_local_playback_positions = (
            resolve_remember_local_playback_positions(
                self.options.remember_local_playback_positions,
                self._remember_local_playback_positions,
            )
        )
        self._detailed_hints = resolve_detailed_hints(
            self.options.detailed_hints,
            self._detailed_hints,
        )
        self.messages.detailed_hints = self._detailed_hints
        apply_message_overrides(
            self.messages,
            enabled=self.options.message_enabled,
            seek_messages=self.options.message_seek_messages,
            arrow_seek_messages=self.options.message_arrow_seek_messages,
            percentage_seek_messages=(
                self.options.message_percentage_seek_messages
            ),
            volume_messages=self.options.message_volume_messages,
            playback_messages=self.options.message_playback_messages,
            bookmark_navigation_messages=(
                self.options.message_bookmark_navigation_messages
            ),
            percent_announcement=self.options.message_percent_announcement,
            templates=self.options.message_templates,
        )
        self._apply_detailed_hints()
        # Komunikaty wierszy zmieniaja sie od razu. Nowe preferencje
        # nagrywania trafia do kolejnego Ctrl+R i nastepnej synchronizacji
        # harmonogramow; dlugosc timeshiftu obowiazuje po restarcie hosta.
        self._apply_radio_activity_status()
        self._radio_recognition_due = (
            time.monotonic() + 6.0
            if self.options.radio_recognition_monitoring
            else float("inf")
        )
        # Kolejność sesji zmienia jednocześnie skróty, podpisy menu i paletę
        # poleceń, więc samo odświeżenie stanów zaznaczeń nie wystarcza.
        self._build_menu()
        # Zapis na dysku jest juz zakonczony i to jest wlasciwy moment na
        # krotkie potwierdzenie. Konfiguracja hosta idzie dalej w tle i nie
        # moze opozniac komunikatu NVDA o kilka wywolan miedzyprocesowych.
        self.announcer.say("Zapisano ustawienia")
        client = self.client
        if client is None:
            return

        def apply_to_host() -> list[str]:
            warnings: list[str] = []
            try:
                client.configure_audio(
                    **session_options.engine_audio_payload(self.state)
                )
            except Exception:
                warnings.append("ustawienia dźwięku")
            try:
                client.configure_local_resume(
                    self._remember_local_playback_positions
                )
            except Exception:
                warnings.append("zapamiętywanie pozycji lokalnych plików")
            try:
                client.sync_radio_schedules(
                    self._radio_schedule_sync_payload(
                        self._radio_snapshot, self.state
                    )
                )
            except Exception:
                warnings.append("ustawienia harmonogramów")
            podcast_payload = self._podcast_settings_payload()
            if podcast_payload is not None:
                try:
                    client.configure_podcast_global_settings(**podcast_payload)
                except Exception:
                    warnings.append("ustawienia Podcastów i YouTube")
            return warnings

        def applied_to_host(warnings: list[str]) -> None:
            if warnings:
                self.announcer.say(
                    "Po ponownym uruchomieniu programu zostaną zastosowane: "
                    + ", ".join(warnings)
                )

        self.runner.submit(
            "general-settings-apply",
            apply_to_host,
            applied_to_host,
            lambda _error: self.announcer.say(
                "Zastosowanie ustawień wymaga ponownego uruchomienia programu"
            ),
        )

    def _with_radio_recording_options(self, snapshot):
        """Naloz zapisane opcje wxPython na odczytany profil glownego AMC."""
        options = getattr(self, "options", None)
        if options is None:
            return snapshot
        snapshot.recording = preferences_with_overrides(
            snapshot.recording,
            recording_format=options.radio_recording_format,
            bitrate_kbps=options.radio_recording_bitrate_kbps,
            default_folder=options.radio_recordings_folder,
            override_default_folder=(
                options.radio_recordings_folder is not None
            ),
            use_podcast_downloads_folder=(
                options.radio_use_podcast_downloads_folder
            ),
            podcast_downloads_folder=options.podcast_downloads_folder,
            override_podcast_downloads_folder=(
                options.podcast_downloads_folder is not None
            ),
            prefer_station_folder=(
                options.radio_prefer_station_folder_in_new_schedules
            ),
        )
        return snapshot

    def _podcast_settings_payload(self) -> dict[str, object] | None:
        """Komplet albo brak: host nigdy nie dostaje polowicznej konfiguracji."""
        options = self.options
        values = (
            options.podcast_downloads_folder,
            options.podcast_rss_refresh_interval_minutes,
            options.podcast_youtube_refresh_interval_minutes,
            options.podcast_automatic_refresh_batch_size,
        )
        if any(value is None for value in values):
            return None
        return {
            "downloads_folder": str(values[0] or ""),
            "rss_refresh_interval_minutes": int(values[1]),
            "youtube_refresh_interval_minutes": int(values[2]),
            "automatic_refresh_batch_size": int(values[3]),
        }

    def _show_session_options(self) -> None:
        """Opcje sesji: dialog, wybor sesji, Zapisz/Anuluj, zapis i SKUTEK.

        Sesje otwarcia bierzemy z nawigatora, ale KONFIGUROWANA sesja pochodzi
        z dialogu -- wymaganie jest takie, by dalo sie ustawic druga sesje BEZ
        przelaczenia odsluchu. Dialog oddaje ``drafts``: wybory kazdej sesji,
        ktorej uzytkownik dotknal.

        Anuluj, Escape i krzyzyk konczy sie TUTAJ: poza ``wx.ID_OK`` nie
        wolamy ani zapisu, ani silnika. Fokus wraca PO ``Destroy``, bo przed
        nim wx oddal by go z powrotem oknu modalnemu.
        """
        opened = self.navigator.active
        if not session_options.capabilities_for(opened).has_options:
            self.announcer.say(
                f"Sesja {session_options.session_display_name(opened)} nie ma jeszcze "
                "opcji wykonywanych przez ten interfejs"
            )
            return
        drafts = {
            session: session_options.effective_overrides(self.state, session)
            for session in (SessionId.FILES, SessionId.RADIO, SessionId.PODCASTS)
        }
        dialog = SessionOptionsDialog(
            self, opened, self.options, drafts[opened], drafts=drafts
        )
        chosen: dict | None = None
        try:
            if dialog.ShowModal() == wx.ID_OK:
                chosen = dialog.drafts
        finally:
            dialog.Destroy()

        if chosen is None:
            self._restore_focus_after_dialog()
            return

        self._apply_session_option_drafts(chosen)
        self._restore_focus_after_dialog()

    def _apply_session_option_drafts(self, drafts: dict) -> None:
        """Zatwierdz wybory ze wszystkich edytowanych sesji.

        SILNIK IDZIE PRZEZ TASKRUNNER. ``audio.configure`` to wywolanie
        procesu hosta z wlasnym timeoutem; na watku GUI zawieszalo by okno i
        czytnik ekranu na caly ten czas. ``runner.submit`` ma bramke zywego
        kontekstu, wiec spozniony wynik nie dotknie zamknietego okna.

        SPOJNOSC RAM / SILNIK / DYSK. Zmieniamy tylko sesje, ktorych wybor
        NAPRAWDE rozni sie od stanu trwalego. Gdy dysk ODMOWI zapisu, wracamy
        do stanu sprzed zmiany -- i w pamieci, i w silniku. Bez tego
        uzytkownik slyszal "Nie moge zapisac" i zaraz po nim "Zapisano", a
        RAM/silnik zostawaly z wyborem, ktorego na dysku nie ma.
        """
        poprzednie = {
            session: session_options.effective_overrides(self.state, session)
            for session in (SessionId.FILES, SessionId.RADIO, SessionId.PODCASTS)
        }
        zmienione = [
            session
            for session, overrides in drafts.items()
            if overrides.restricted_to(session_options.capabilities_for(session))
            != poprzednie.get(session)
        ]
        if not zmienione:
            self.announcer.say("Opcje sesji bez zmian.")
            return

        def work() -> list:
            # Watek roboczy: wylacznie rozmowa z hostem i zmiana stanu w RAM.
            # Zapis na dysk i mowa czytnika zostaja w ``done`` (watek GUI).
            return [
                session_options.apply_session_options(
                    self.state, session, drafts[session], client=self.client
                )
                for session in zmienione
            ]

        def done(results: list) -> None:
            odmowa = next((item for item in results if not item.saved), None)
            if odmowa is not None:
                # Odmowa silnika: ``apply_session_options`` nie dotknelo stanu.
                self.announcer.say(odmowa.message)
                return
            if self._save_state() is False:
                # Dysk odmowil. ``_save_state`` juz powiedzial dlaczego --
                # drugi komunikat ze slowem "Zapisano" byl by klamstwem.
                for session in zmienione:
                    session_options.restore_session_options(
                        self.state, session, poprzednie[session], client=self.client
                    )
                return
            tresc = " ".join(item.message for item in results)
            if any(item.applies_on_next_playback for item in results):
                # Prawda komunikatu: host zwrocil ``appliesOnNextPlayback``,
                # wiec biezace granie zostaje po staremu.
                tresc += " Przetwarzanie dźwięku zmieni się przy następnym uruchomieniu materiału."
            self.announcer.say(tresc)

        def failed(error: Exception) -> None:
            self.announcer.say(f"Nie zapisano opcji sesji: {error}")

        self.runner.submit("session-options", work, done, failed)

    def _restore_focus_after_dialog(self) -> None:
        """Fokus po zamknieciu okna modalnego: lista TEJ sesji albo odtwarzacz.

        Bez tego fokus zostaje na ramce i czytnik ekranu nie ma czego czytac, a
        klawisze listy nie dochodza do kontrolki.

        Lista pochodzi z ``_active_list()``. ``LiteFrame`` NIE ma pola
        ``list_ctrl``: sa dwie listy (``files_list``, ``radio_list``) i o
        wlasciwej decyduje aktywna sesja. Wolanie nieistniejacego pola
        konczylo sie ``AttributeError`` i fokus ginal po KAZDYM zamknieciu
        dialogu -- tak samo po Anuluj jak po Zapisz.
        """
        target = (
            self.play_button
            if self.navigator.session.view is View.PLAYER
            else self._active_list()
        )
        if target is not None:
            target.SetFocus()

    def _play_pause(self) -> None:
        client = self.client
        if client is None:
            return

        if self.navigator.active is SessionId.TIDAL:
            if not self._tidal_desktop_has_playback:
                self.announcer.say(
                    "Najpierw uruchom utwór w oryginalnym TIDALu"
                )
                return

            def tidal_done(payload: dict) -> None:
                result = payload or {}
                if not bool(result.get("handled")):
                    self._tidal_desktop_has_playback = False
                self.announcer.say(str(
                    result.get("message") or "Oryginalny TIDAL nie odpowiada"
                ))

            self.runner.submit(
                "tidal-transport",
                lambda: client.tidal_external_transport("toggle"),
                tidal_done,
                lambda error: self.announcer.say(
                    f"Nie mogę sterować oryginalnym TIDALem: {error}"
                ),
            )
            return

        if self.navigator.active is SessionId.WIIM:
            self._wiim_transport("toggle")
            return
        if self.navigator.active is SessionId.SONOS:
            self._sonos_transport("toggle")
            return

        session = self.navigator.active

        def done(payload: dict) -> None:
            paused = bool((payload or {}).get("paused"))
            updated = {
                **self._transport_status_by_session.get(session, {}),
                **(payload or {}),
            }
            self._transport_status_by_session[session] = updated
            self._last_status = updated
            # Etykieta zawsze zgodna ze stanem: po wstrzymaniu przycisk ma juz
            # proponowac odtwarzanie (MainWindow.xaml.cs:2560).
            self._set_transport_label(playing=not paused)
            message = transport_confirmation(paused=paused)
            if (
                self.messages.announces_playback
                and self.messages.speaks_routine
            ):
                self.announcer.say(message)
            else:
                self.announcer.show(message)

        self.runner.submit(
            "transport",
            lambda session_id=session.value: client.pause_resume(session_id),
            done,
            lambda error: self.announcer.say(f"Blad: {error}"),
        )

    def _toggle_mute(self) -> None:
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie działa")
            return
        session = self.navigator.active

        def done(payload: dict) -> None:
            muted = bool((payload or {}).get("muted"))
            updated = {
                **self._transport_status_by_session.get(session, {}),
                **(payload or {}),
            }
            self._transport_status_by_session[session] = updated
            self._last_status = updated
            self.announcer.say("Wyciszono" if muted else "Włączono dźwięk")

        self.runner.submit(
            "transport-mute",
            lambda session_id=session.value: client.toggle_mute(session_id),
            done,
            lambda error: self.announcer.say(f"Błąd: {error}"),
        )

    def _set_transport_label(self, *, playing: bool, preparing: bool = False) -> None:
        """Jedno miejsce, ktore nazywa przycisk transportu.

        Czytnik czyta nazwe przycisku przy fokusie, wiec etykieta i nazwa
        dostepnosciowa musza byc tym samym slowem -- inaczej widac jedno, a
        slychac drugie. Nie ogłaszamy tu nic sami: zmiana etykiety to nie
        potwierdzenie gestu, a dwa zrodla mowy daja podwojna zapowiedz.
        """
        label = transport_button_label(playing=playing, preparing=preparing)
        if self.play_button.GetLabel() == label:
            return
        self.play_button.SetLabel(label)
        self.play_button.SetName(label.replace("&", ""))

    def _seek(self, delta: float) -> None:
        client = self.client
        if client is None:
            return
        if self.navigator.active is SessionId.SONOS:
            self._sonos_transport("seekRelative", seconds=delta)
            return
        self.runner.submit(
            "transport",
            lambda session_id=self.navigator.active.value: client.seek_by(delta, session_id),
            # Oryginal pyta najpierw o przelaczniki: CommandRouter.cs:534-539
            # sprawdza Messages.SeekMessages, a dla strzalek dodatkowo
            # ArrowSeekMessages -- i DOPIERO wtedy formatuje czas. Dostarczona
            # wersja mowila bezwarunkowo, dlatego strzalki gadaly non stop.
            lambda payload: self._announce_seek(payload),
            lambda error: self.announcer.say(f"Nie moge przewinac: {error}"),
        )

    def _announce_seek(self, payload: dict | None) -> None:
        """Komunikat po przewinieciu -- tylko jesli ustawienia na to pozwalaja."""
        text = self.messages.arrow_seek_text((payload or {}).get("positionSeconds"))
        if text is not None and self.messages.speaks_routine:
            self.announcer.say(text)

    def _seek_to_track_edge(self, to_end: bool) -> None:
        """Home/End w odtwarzaczu. Port ``CommandRouter.cs:316-324``.

        End NIE jest skokiem na 100%: oryginal celuje w
        ``Max(Zero, Duration - 10s)``, zeby na koncu bylo jeszcze czego
        posluchac, a utwor nie konczyl sie w tej samej chwili. Home to czysta
        pozycja zero i oryginal mowi przy niej doslownie \"0:00\".

        Uzywamy TEGO SAMEGO ``seek_to_position`` hosta, co skok procentowy --
        nie dokladamy nowej komendy protokolu.
        """
        client = self.client
        if client is None:
            return
        if not to_end:
            self._audio_clip_track_end_intent = None
            self.runner.submit(
                "transport",
                lambda session_id=self.navigator.active.value: client.seek_to_position(0.0, session_id),
                # cs:318 -- staly napis, nie odczyt pozycji z odpowiedzi.
                lambda _payload: self._announce_track_edge("0:00"),
                lambda error: self.announcer.say(f"Nie moge przewinac: {error}"),
            )
            return

        duration = self._last_status.get("durationSeconds")
        if not isinstance(duration, (int, float)) or duration <= 0:
            # Bez czasu trwania konca nie da sie policzyc. Milczenie
            # wygladaloby na zepsuty klawisz, wiec mowimy -- to blad
            # wykonania, nie rutynowy komunikat (jak cs:546-551 przy %).
            self.announcer.say("Nie znam czasu trwania, nie moge skoczyc na koniec")
            return
        target = max(0.0, float(duration) - TRACK_END_MARGIN_SECONDS)
        self.runner.submit(
            "transport",
            lambda session_id=self.navigator.active.value: client.seek_to_position(target, session_id),
            lambda payload: self._complete_track_end_seek(
                payload,
                duration=float(duration),
                target=target,
            ),
            lambda error: self.announcer.say(f"Nie moge przewinac: {error}"),
        )

    def _complete_track_end_seek(
        self,
        payload: dict | None,
        *,
        duration: float,
        target: float,
    ) -> None:
        raw_position = (payload or {}).get("positionSeconds")
        position = (
            float(raw_position)
            if isinstance(raw_position, (int, float))
            and not isinstance(raw_position, bool)
            else target
        )
        self._last_status = {**self._last_status, "positionSeconds": position}
        item_id = self._last_status.get("id")
        source_path = self._last_status.get("source")
        if (
            isinstance(item_id, str)
            and item_id.strip()
            and isinstance(source_path, str)
            and source_path.strip()
        ):
            self._audio_clip_track_end_intent = AudioClipTrackEndIntent(
                item_id=item_id.strip(),
                source_path=source_path,
                duration_seconds=duration,
                preview_start_seconds=target,
                expires_at=time.monotonic() + 120.0,
            )
        else:
            self._audio_clip_track_end_intent = None
        self._announce_track_edge(format_clock(target))

    def _announce_track_edge(self, text: str) -> None:
        """cs:318 i cs:323 pytaja o TE SAME dwie bramki, co strzalki."""
        if self.messages.announces_arrow_seek and self.messages.speaks_routine:
            self.announcer.say(text)

    def _seek_percent(self, percent: int) -> None:
        """Skok procentowy (gole cyfry 0..9) -- wlasna rodzina przelacznikow.

        CommandRouter.cs:545-560 trzyma dla procentow OSOBNE przelaczniki
        (PercentageSeekMessages / PercentageSeekAnnouncement), wiec NIE
        dziedzicza one po polityce strzalek.
        """
        client = self.client
        if client is None:
            return
        if self.navigator.active is SessionId.SONOS:
            duration = self._sonos_snapshot.get("durationSeconds")
            position = self._sonos_snapshot.get("positionSeconds")
            if (
                not isinstance(duration, (int, float))
                or isinstance(duration, bool)
                or duration <= 0
                or not isinstance(position, (int, float))
                or isinstance(position, bool)
            ):
                self.announcer.say(
                    "Sonos nie podał czasu potrzebnego do skoku procentowego"
                )
                return
            delta = float(duration) * percent / 100.0 - float(position)
            if abs(delta) < 0.001:
                self.announcer.say(f"{percent}%")
                return
            self._sonos_transport("seekRelative", seconds=delta)
            return
        duration = self._last_status.get("durationSeconds")
        if not isinstance(duration, (int, float)) or duration <= 0:
            # cs:546-551 -- brak czasu trwania to blad wykonania, mowiony
            # ZAWSZE, bo inaczej gest wygladalby na niedzialajacy.
            text = self.messages.percent_seek_text(
                percent, position_seconds=None, duration_seconds=None
            )
            if text is not None:
                self.announcer.say(text)
            return
        target = float(duration) * percent / 100.0
        self.runner.submit(
            "transport",
            lambda session_id=self.navigator.active.value: client.seek_to_position(target, session_id),
            lambda payload: self._announce_seek_percent(percent, payload, float(duration)),
            lambda error: self.announcer.say(f"Nie moge przewinac: {error}"),
        )

    def _announce_seek_percent(
        self, percent: int, payload: dict | None, duration: float
    ) -> None:
        text = self.messages.percent_seek_text(
            percent,
            position_seconds=(payload or {}).get("positionSeconds"),
            duration_seconds=duration,
        )
        if text is not None and self.messages.speaks_routine:
            self.announcer.say(text)

    def _adjust_volume(self, delta: int) -> None:
        if self.navigator.active is SessionId.WIIM:
            command = {
                5: "volumeUp5",
                -5: "volumeDown5",
                1: "volumeUp1",
                -1: "volumeDown1",
            }.get(delta)
            if command is not None:
                self._wiim_transport(command)
                return
        if self.navigator.active is SessionId.SONOS:
            command = {
                5: "volumeUp5",
                -5: "volumeDown5",
                1: "volumeUp1",
                -1: "volumeDown1",
            }.get(delta)
            if command is not None:
                self._sonos_transport(command)
                return
        self._set_volume(self.options.volume + delta)

    def _set_volume(self, value: int) -> None:
        value = max(0, min(100, int(value)))
        self.volume_slider.SetValue(value)
        if self.navigator.active is SessionId.WIIM:
            self._wiim_transport("setVolume", volume=value)
            return
        if self.navigator.active is SessionId.SONOS:
            self._sonos_transport("setVolume", volume=value)
            return
        self.options.volume = value
        # Glosnosc tez ma swoj przelacznik (CommandRouter.cs:566-575) i swoj
        # szablon "{value}%" -- nie wlasne zdanie "Glosnosc 70".
        text = self.messages.volume_text(value)
        if text is not None and self.messages.speaks_routine:
            self.announcer.say(text)
        client = self.client
        if client is not None:
            self.runner.submit(
                "volume",
                lambda session_id=self.navigator.active.value: client.set_volume(value, session_id),
                lambda _p: None,
                lambda _e: None,
            )

    def _set_rate(self, value: float) -> None:
        # Przyciecie jak SetPlaybackRate (DemoMediaSession.cs:381): do
        # NAJBLIZSZEGO szczebla drabiny, nie do dowolnej wartosci z suwaka.
        value = clamp_playback_rate(value)
        self.options.rate = value
        self.rate_choice.SetSelection(PLAYBACK_RATES.index(value))
        # Format jak w oryginale: "1,25x" (MainWindow.xaml.cs:16122), a nie
        # "Tempo 125 procent".
        self.announcer.say(format_playback_rate(value))
        client = self.client
        if client is not None:
            self.runner.submit(
                "rate",
                lambda session_id=self.navigator.active.value: client.set_rate(value, session_id),
                lambda _p: None,
                lambda _e: None,
            )

    def _on_volume_slider(self, event: wx.CommandEvent) -> None:
        self._set_volume(self.volume_slider.GetValue())
        event.Skip()

    def _on_rate_choice(self, event: wx.CommandEvent) -> None:
        selection = self.rate_choice.GetSelection()
        if 0 <= selection < len(PLAYBACK_RATES):
            self._set_rate(PLAYBACK_RATES[selection])
        event.Skip()

    def _announce_time(self, action: Action) -> None:
        """Czas na zadanie: Ctrl+Shift+E / R / T.

        To komenda WPROST od uzytkownika, wiec oryginal NIE filtruje jej
        przelacznikami przewijania -- CommandRouter.cs:325-335 idzie prosto do
        AnnounceTemplate. Domyslny szablon to sam czas, bez slowa "Minelo":
        release .383 pokazuje "3:51". Slowo pojawia sie tylko wtedy, gdy
        uzytkownik sam wpisal je do szablonu w ustawieniach AMC.
        """
        if self.navigator.active is SessionId.TIDAL:
            self._announce_tidal_time(action)
            return
        if self.navigator.active is SessionId.WIIM:
            state = self._wiim_snapshot
            text = time_announcement(
                action,
                self.messages,
                position=state.get("positionSeconds"),
                duration=state.get("durationSeconds"),
            )
            if text is not None:
                self.announcer.say(text)
            else:
                self.announcer.say("Urządzenie WiiM nie podało tego czasu")
            return
        if self.navigator.active is SessionId.SONOS:
            state = self._sonos_snapshot
            text = time_announcement(
                action,
                self.messages,
                position=state.get("positionSeconds"),
                duration=state.get("durationSeconds"),
            )
            if text is not None:
                self.announcer.say(text)
            else:
                self.announcer.say("Sonos nie podał tego czasu")
            return
        status = self._last_status
        text = time_announcement(
            action,
            self.messages,
            position=status.get("positionSeconds"),
            duration=status.get("durationSeconds"),
        )
        if text is not None:
            self.announcer.say(text)

    def _announce_tidal_time(self, action: Action) -> None:
        """Read only time values that original TIDAL actually exposes."""
        client = self.client
        if client is None or not self._tidal_desktop_has_playback:
            self.announcer.say("Najpierw uruchom utwór w oryginalnym TIDALu")
            return

        def done(payload: dict) -> None:
            state = payload or {}
            if not bool(state.get("hasSession")):
                self._tidal_desktop_has_playback = False
                self.announcer.say(
                    "Oryginalny TIDAL nie podaje teraz czasu utworu"
                )
                return
            raw_position = state.get("positionSeconds")
            raw_duration = state.get("durationSeconds")
            position = (
                float(raw_position)
                if isinstance(raw_position, (int, float))
                and not isinstance(raw_position, bool)
                else None
            )
            duration = (
                float(raw_duration)
                if isinstance(raw_duration, (int, float))
                and not isinstance(raw_duration, bool)
                and raw_duration > 0
                else None
            )
            if action is Action.TIME_ELAPSED and position is None:
                self.announcer.say(
                    "Oryginalny TIDAL nie podaje czasu od początku"
                )
                return
            if action is Action.TIME_TOTAL and duration is None:
                self.announcer.say(
                    "Oryginalny TIDAL nie podaje czasu całkowitego"
                )
                return
            if action is Action.TIME_REMAINING and (
                position is None or duration is None
            ):
                self.announcer.say(
                    "Oryginalny TIDAL nie podaje czasu pozostałego"
                )
                return
            text = time_announcement(
                action,
                self.messages,
                position=position,
                duration=duration,
            )
            if text is not None:
                self.announcer.say(text)

        self.runner.submit(
            "tidal-state",
            client.tidal_external_state,
            done,
            lambda error: self.announcer.say(
                f"Nie mogę odczytać czasu z oryginalnego TIDALa: {error}"
            ),
        )

    def _toggle_seek_messages(self) -> None:
        """Ctrl+Shift+G -- przelacznik komunikatow przewijania.

        AMC Python zapisuje wybor we wlasnym stanie i nie dotyka profilu
        starego interfejsu. Potwierdzenie samego przelaczenia jest jawna
        odpowiedzia na gest, wiec zostaje wypowiedziane takze przy wylaczaniu.
        """
        previous = self.messages.seek_messages
        result = self.messages.toggle_seek_messages()
        if result.changed:
            previous_override = self.options.message_seek_messages
            self.options.message_seek_messages = self.messages.seek_messages
            if not self._save_state():
                self.options.message_seek_messages = previous_override
                self.messages.seek_messages = previous
                return
        self.announcer.say(result.message)

    # ------------------------------------------------------------- status

    def _update_native_playback_status(self, payload: dict | None = None) -> None:
        """Wpisz do NVDA+End gotowy tekst hosta, bez wywolywania mowy.

        Host C# sklada stacje, parametry audio i metadane strumienia tym samym
        formatterem co Alt+D. Python nie pokazuje surowych identyfikatorow ani
        nie zgaduje bitrate'u.
        """
        status = payload if isinstance(payload, dict) else self._last_status
        text = str(status.get("currentBroadcastText") or "").strip()
        bar = getattr(self, "status_bar", None)
        if text and bar is not None:
            bar.show(text)

    def _on_timer(self, _event: wx.TimerEvent) -> None:
        # Stan transportu i nagran odswiezamy takze na liscie: dzieki temu
        # wiersz stacji uczciwie mowi, czy jest odtwarzany albo nagrywany.
        # Etykiete czasu nadal zmieniamy tylko w widoku odtwarzacza.
        self._refresh_status()
        self._refresh_wiim_status()
        self._refresh_sonos_status()
        self._refresh_recording_status()
        self._checkpoint_podcast_if_due()
        self._checkpoint_local_if_due()
        self._refresh_due_podcasts_automatically()
        self._recognize_radio_if_due()

    def _recognize_radio_if_due(self) -> None:
        if (
            not self.options.radio_recognition_monitoring
            or self._radio_recognition_pending
            or time.monotonic() < self._radio_recognition_due
        ):
            return
        # Tak jak pełne AMC nie odpytujemy usługi, gdy nie ma właściwego
        # źródła. Zegar obudzi potwierdzony start Radia albo nagrywania.
        if not self._recognition_source_available():
            self._radio_recognition_due = float("inf")
            return
        self._radio_recognition_due = time.monotonic() + 60.0
        self._recognize_radio_track(automatic=True)

    def _refresh_due_podcasts_automatically(self) -> None:
        """Co minute zlec hostowi tylko nalezne zrodla, bez rutynowej mowy."""
        client = self.client
        now = time.monotonic()
        if (
            client is None
            or not self.podcasts.is_available
            or self._podcast_refresh_pending
            or self._podcast_automatic_refresh_pending
            or now < self._podcast_automatic_refresh_due
        ):
            return
        self._podcast_automatic_refresh_due = now + 60.0
        self._podcast_automatic_refresh_pending = True
        self._podcast_refresh_pending = True

        def done(payload: dict) -> None:
            self._podcast_automatic_refresh_pending = False
            self._podcast_refresh_pending = False
            self._last_automatic_podcast_error = None
            requested = max(0, int((payload or {}).get("requested") or 0))
            if requested <= 0:
                return
            added = max(0, int((payload or {}).get("addedEpisodes") or 0))
            if added:
                self.status_bar.show(
                    f"Automatycznie dodano nowe odcinki: {added}"
                )
            if self.navigator.active is SessionId.PODCASTS:
                self._refresh_profile_view()

        def failed(error: Exception) -> None:
            self._podcast_automatic_refresh_pending = False
            self._podcast_refresh_pending = False
            message = str(error).strip() or "Automatyczne sprawdzanie nie powiodło się"
            if message != self._last_automatic_podcast_error:
                self._last_automatic_podcast_error = message
                self.status_bar.show(message)

        self.runner.submit(
            "podcast-auto-refresh",
            client.refresh_podcasts_automatically,
            done,
            failed,
        )

    def _checkpoint_podcast_if_due(self) -> None:
        """Co 15 sekund zlec zapis jak w pelnym AMC, bez dodatkowej mowy."""
        client = self.client
        if (
            client is None
            or not self._podcast_checkpoint_active
            or self._podcast_checkpoint_pending
            or time.monotonic() < self._podcast_checkpoint_due
        ):
            return
        self._podcast_checkpoint_pending = True
        # Termin przesuwamy PRZED zadaniem: szybkie ticki nie moga ustawic
        # kilku rownoleglych zapisow tego samego czasu.
        self._podcast_checkpoint_due = time.monotonic() + 15.0

        def done(_payload: dict) -> None:
            self._podcast_checkpoint_pending = False
            self._last_podcast_progress_error = None

        def failed(error: Exception) -> None:
            self._podcast_checkpoint_pending = False
            self._note_podcast_progress_error(str(error))

        self.runner.submit(
            "podcast-checkpoint",
            client.checkpoint_podcast,
            done,
            failed,
        )

    def _checkpoint_local_if_due(self) -> None:
        """Co 15 sekund zapisz pozycję lokalnego pliku bez dodatkowej mowy."""
        client = self.client
        if (
            client is None
            or not self._local_checkpoint_active
            or self._local_checkpoint_pending
            or time.monotonic() < self._local_checkpoint_due
        ):
            return
        self._local_checkpoint_pending = True
        self._local_checkpoint_due = time.monotonic() + 15.0

        def done(payload: dict) -> None:
            self._local_checkpoint_pending = False
            error = str((payload or {}).get("persistError") or "").strip()
            if not error:
                self._last_local_resume_error = None
                return
            if error == self._last_local_resume_error:
                return
            self._last_local_resume_error = error
            self.announcer.say(
                f"Nie zapisano pozycji lokalnego pliku: {error}"
            )

        def failed(error: Exception) -> None:
            self._local_checkpoint_pending = False
            message = str(error).strip() or "Nie udało się zapisać pozycji"
            if message == self._last_local_resume_error:
                return
            self._last_local_resume_error = message
            self.announcer.say(
                f"Nie zapisano pozycji lokalnego pliku: {message}"
            )

        self.runner.submit(
            "local-checkpoint",
            client.checkpoint_local,
            done,
            failed,
        )

    def _note_podcast_progress_error(self, message: str) -> None:
        """Jedna slyszalna informacja na przyczyne; timer nie jest logiem."""
        cleaned = message.strip() or "Nie udało się zapisać postępu odcinka"
        if cleaned == self._last_podcast_progress_error:
            return
        self._last_podcast_progress_error = cleaned
        self.announcer.say(f"Nie zapisano postępu odcinka: {cleaned}")

    def _refresh_status(self) -> None:
        client = self.client
        if client is None or getattr(self, "_status_poll_pending", False):
            return
        local_sessions = (
            SessionId.FILES,
            SessionId.RADIO,
            SessionId.PODCASTS,
            SessionId.SPOTIFY,
        )
        active = self.navigator.active
        if active in local_sessions:
            requested_session = active
        elif SessionId.RADIO in self._playing_sessions:
            requested_session = SessionId.RADIO
        elif SessionId.PODCASTS in self._playing_sessions:
            requested_session = SessionId.PODCASTS
        elif SessionId.SPOTIFY in self._playing_sessions:
            requested_session = SessionId.SPOTIFY
        else:
            requested_session = SessionId.FILES
        self._status_poll_pending = True
        def done(payload: dict) -> None:
            self._status_poll_pending = False
            if not payload:
                return
            self._transport_status_by_session[requested_session] = payload
            self._last_status = payload
            self._update_native_playback_status(payload)
            remote_player = (
                self.navigator.active is SessionId.WIIM
                or self.navigator.active is SessionId.SONOS
                or (
                    self.navigator.active is SessionId.TIDAL
                    and self._tidal_desktop_has_playback
                )
            )
            if self.navigator.view is View.PLAYER and not remote_player:
                position = payload.get("positionSeconds")
                duration = payload.get("durationSeconds")
                label = player_time_label(position, duration)
                # Odswiezamy etykiete tylko gdy TEKST sie zmienil - inaczej
                # czytnik ekranu dostawalby zmiane co sekunde bez potrzeby.
                if self.time_label.GetLabel() != label:
                    self.time_label.SetLabel(label)
            # Etykieta transportu podaza za PRAWDZIWYM stanem hosta, nie tylko
            # za nasza Spacja: odtwarzanie zaczete Enterem na liscie albo
            # zakonczony plik tez musza ja poprawic. Bez ogloszenia -- samo
            # odswiezenie statusu nie jest gestem uzytkownika.
            if "paused" in payload and not remote_player:
                self._set_transport_label(playing=not bool(payload.get("paused")))
            self._apply_radio_activity_status()

        def failed(_error: Exception) -> None:
            self._status_poll_pending = False

        self.runner.submit(
            "status",
            lambda: client.status(requested_session.value),
            done,
            failed,
        )
        if requested_session is not SessionId.RADIO:
            self._refresh_radio_transport_status()

    def _refresh_radio_transport_status(self) -> None:
        """Odczytaj Radio osobno, nawet gdy użytkownik steruje Plikami."""
        client = self.client
        if client is None or self._radio_transport_status_poll_pending:
            return
        self._radio_transport_status_poll_pending = True

        def done(payload: dict) -> None:
            self._radio_transport_status_poll_pending = False
            if payload:
                self._transport_status_by_session[SessionId.RADIO] = payload
                self._apply_radio_activity_status()

        def failed(_error: Exception) -> None:
            self._radio_transport_status_poll_pending = False

        self.runner.submit(
            "radio-transport-status",
            lambda: client.status(SessionId.RADIO.value),
            done,
            failed,
        )

    def _refresh_wiim_status(self) -> None:
        """Cichy odczyt aktywnego WiiM, tak jak okresowy odczyt w AMC."""
        client = self.client
        device_id = self._wiim_active_device_id
        if (
            client is None
            or not device_id
            or self.navigator.active is not SessionId.WIIM
            or self.navigator.view is not View.PLAYER
            or getattr(self, "_wiim_status_poll_pending", False)
        ):
            return
        self._wiim_status_poll_pending = True

        def done(payload: object) -> None:
            self._wiim_status_poll_pending = False
            try:
                state = wiim_snapshot(payload)
            except WiiMPayloadError:
                return
            if (
                self.navigator.active is not SessionId.WIIM
                or self.navigator.view is not View.PLAYER
                or state.get("deviceId") != self._wiim_active_device_id
            ):
                return
            self._wiim_snapshot = state
            self._apply_wiim_snapshot(state, announce=False)

        def failed(_error: Exception) -> None:
            self._wiim_status_poll_pending = False

        self.runner.submit(
            "wiim-status",
            lambda: client.wiim_snapshot(device_id),
            done,
            failed,
        )

    def _refresh_sonos_status(self) -> None:
        """Cichy odczyt aktywnej grupy, bez nakładania zapytań timera."""
        client = self.client
        household_id = self._sonos_active_household_id
        group_id = self._sonos_active_group_id
        if (
            client is None
            or not household_id
            or not group_id
            or self.navigator.active is not SessionId.SONOS
            or self.navigator.view is not View.PLAYER
            or getattr(self, "_sonos_status_poll_pending", False)
            or getattr(self, "_sonos_request_pending", False)
            or getattr(self, "_sonos_retry_pending", False)
            or getattr(self, "_sonos_pending_activation", None) is not None
            or bool(getattr(self, "_sonos_command_queue", ()))
        ):
            return
        self._sonos_status_poll_pending = True
        self._sonos_request_pending = True

        def done(payload: object) -> None:
            self._sonos_status_poll_pending = False
            try:
                state = sonos_snapshot(payload)
            except SonosPayloadError:
                self._finish_sonos_request()
                return
            if (
                self.navigator.active is not SessionId.SONOS
                or self.navigator.view is not View.PLAYER
                or state.get("householdId") != self._sonos_active_household_id
                or state.get("groupId") != self._sonos_active_group_id
            ):
                self._finish_sonos_request()
                return
            self._sonos_snapshot = state
            self._apply_sonos_snapshot(state, announce=False)
            self._finish_sonos_request()

        def failed(_error: Exception) -> None:
            self._sonos_status_poll_pending = False
            self._finish_sonos_request()

        self.runner.submit(
            "sonos-status",
            lambda: client.sonos_snapshot(household_id, group_id),
            done,
            failed,
        )

    def _refresh_recording_status(self) -> None:
        """Pobierz jedna migawke nagran bez mowy i bez nakladania zapytan."""
        client = self.client
        if client is None or getattr(self, "_recording_status_poll_pending", False):
            return
        self._recording_status_poll_pending = True

        def done(payload: dict) -> None:
            self._recording_status_poll_pending = False
            self._last_recording_status = payload or {}
            # Zdarzenie rozpoczęcia nagrania dociera przed tą pełną migawką.
            # Dopiero tutaj znamy pewnie nową liczbę aktywnych torów, więc
            # ponownie wyznaczamy termin automatycznego rozpoznawania.
            self._schedule_radio_recognition_after_source_change()
            state = self.navigator.sessions[SessionId.RADIO]
            if state.library_view is LibraryView.ACTIVE_RADIO_RECORDINGS:
                preferred_id = state.model.selected_id
                state.model.replace(
                    active_recording_rows(self._last_recording_status),
                    preferred_id=preferred_id,
                )
                if self.navigator.active is SessionId.RADIO:
                    self._sync_views()
                return
            self._apply_radio_activity_status()

        def failed(_error: Exception) -> None:
            self._recording_status_poll_pending = False

        self.runner.submit(
            "radio-recording-status",
            client.radio_recording_status,
            done,
            failed,
        )

    def _apply_radio_activity_status(self) -> None:
        """Zmien tylko dynamiczny opis zwyklych list Radia."""
        state = self.navigator.sessions[SessionId.RADIO]
        if state.library_view not in (
            None,
            LibraryView.FAVORITES,
            LibraryView.HISTORY,
            LibraryView.PLAYLIST_CONTENTS,
        ):
            return
        rows = station_activity_rows(
            state.model.rows,
            transport_status=getattr(self, "_transport_status_by_session", {}).get(
                SessionId.RADIO,
                self._last_status if self._last_status.get("engine") == "radio" else {},
            ),
            recording_status=self._last_recording_status,
            playback_position=self.options.radio_playback_state_position,
            recording_position=self.options.radio_recording_state_position,
        )
        if rows == state.model.rows:
            return
        preferred_id = state.model.selected_id
        state.model.replace(rows, preferred_id=preferred_id)
        if self.navigator.active is SessionId.RADIO:
            self._sync_views()

    # ------------------------------------------------------- edycja Biblioteki

    def _single_edit_row(self, what: str) -> Row | None:
        rows = self._selected_action_rows()
        if len(rows) != 1:
            self.announcer.say(f"Do {what} wybierz jeden element")
            return None
        return rows[0]

    def _activate_selected_if_ready(self) -> None:
        """Nie odtwarzaj pliku Enterem, który właśnie zatwierdził Shift+F2."""
        if getattr(self, "_local_file_rename_pending", False):
            return
        if time.monotonic() < getattr(
            self, "_local_file_rename_activation_guard_until", 0.0
        ):
            return
        self._activate()

    def _profile_edit_client(self) -> LiteHostClient | None:
        if self.client is None:
            self.announcer.say("Silnik nie działa. Zmiana nie została zapisana")
            return None
        return self.client

    def _current_profile_view_name(self) -> str:
        view = self.navigator.session.library_view
        return "library" if view is None else view.value

    def _refresh_profile_view(
        self,
        preferred_id: str | None = None,
        *,
        selected_ids: list[str] | None = None,
        after_refresh: Callable[[], None] | None = None,
    ) -> None:
        """Wczytaj ponownie TEN SAM widok po wąskiej zmianie hosta."""
        state = self.navigator.session
        if self.navigator.active is SessionId.RADIO:
            self._open_radio_view(
                OpenLibraryView(
                    view=state.library_view,
                    playlist_id=state.library_playlist_id,
                    preferred_id=preferred_id,
                    target_session_id=SessionId.RADIO,
                ),
                restore_selected_ids=selected_ids,
                after_refresh=after_refresh,
            )
            return
        if self.navigator.active is SessionId.PODCASTS:
            if state.library_view is LibraryView.PODCAST_LIBRARY:
                self._open_podcast_library(preferred_id=preferred_id)
            elif state.library_view is LibraryView.PODCAST_EPISODES:
                if state.library_playlist_id:
                    self._open_podcast_view(OpenPodcastView(
                        subscription_id=state.library_playlist_id,
                        preferred_id=preferred_id,
                    ))
            elif state.library_view in (
                LibraryView.PODCAST_FAVORITES,
                LibraryView.PODCAST_HISTORY,
                LibraryView.PODCAST_QUEUE,
                LibraryView.PODCAST_INBOX,
                LibraryView.PODCAST_DOWNLOADS,
            ):
                self._open_podcast_aggregate(OpenPodcastAggregateView(
                    state.library_view,
                    preferred_id=preferred_id,
                ))
            elif state.library_view is LibraryView.PODCAST_PLAYLISTS:
                self._open_podcast_playlist_view(
                    OpenPodcastPlaylistView(preferred_id=preferred_id),
                    after_refresh=after_refresh,
                )
            elif (
                state.library_view is LibraryView.PODCAST_PLAYLIST_CONTENTS
                and state.library_playlist_id
            ):
                self._open_podcast_playlist_view(
                    OpenPodcastPlaylistView(
                        playlist_id=state.library_playlist_id,
                        playlist_title=state.library_return_view or "Playlista",
                        preferred_id=preferred_id,
                    ),
                    restore_selected_ids=selected_ids,
                    after_refresh=after_refresh,
                )
            return
        if self.navigator.active is SessionId.TIDAL:
            view = state.library_view
            if view not in (
                LibraryView.TIDAL_LIBRARY,
                LibraryView.TIDAL_FAVORITES,
                LibraryView.TIDAL_PLAYLISTS,
            ):
                view = LibraryView.TIDAL_LIBRARY
            self._open_tidal_view(OpenTidalView(view, preferred_id=preferred_id))
            return
        if state.library_view is None:
            self._open_library(state.folder_path or None, preferred_id=preferred_id)
            return
        if state.library_view is LibraryView.LIVE_QUEUE:
            self._open_queue_view()
            return
        if state.library_view is LibraryView.RECORDED_RADIO_FILES:
            self._show_radio_recording_history(
                announce=False,
                preferred_id=preferred_id,
            )
            return
        if state.library_view not in self._VIEW_KEYS:
            self.announcer.say("Zmiana została zapisana. Odśwież bieżący widok")
            return
        self._open_library_view(
            OpenLibraryView(
                view=state.library_view,
                playlist_id=state.library_playlist_id,
                preferred_id=preferred_id,
                item_id=state.library_item_id,
                target_session_id=SessionId.FILES,
            ),
            restore_selected_ids=selected_ids,
            after_refresh=after_refresh,
        )

    def _rename_library_item(self) -> None:
        if self.navigator.active is SessionId.RADIO:
            self._station_edit()
            return
        row = self._single_edit_row("zmiany nazwy")
        if row is None:
            return
        if self.navigator.active is SessionId.PODCASTS:
            if row.kind != "podcast":
                self.announcer.say(
                    "Wybierz podcast lub kanał na głównej liście. "
                    "Nazwy odcinków pochodzą ze źródła"
                )
                return
            client = self._profile_edit_client()
            if client is None:
                return
            with RenameItemDialog(
                self,
                title="Zmień nazwę podcastu lub kanału",
                prompt="&Nowa nazwa podcastu lub kanału:",
                field_name="Nowa nazwa podcastu lub kanału",
                value=row.title,
                help_text=(
                    "Zmiana dotyczy nazwy wyświetlanej przez AMC. "
                    "Nazwa w źródle RSS lub YouTube pozostanie bez zmian."
                ),
            ) as dialog:
                if dialog.ShowModal() != wx.ID_OK:
                    return
                title = dialog.value
            if not title:
                self.announcer.say("Nowa nazwa podcastu lub kanału nie może być pusta")
                return

            def done(_payload: object) -> None:
                self._refresh_profile_view(preferred_id=row.item_id)
                self.announcer.say(f"Zmieniono nazwę podcastu lub kanału: {title}")

            self.runner.submit(
                "profile-edit",
                lambda: client.rename_podcast_subscription(row.item_id, title),
                done,
                lambda error: self.announcer.say(f"Nie zmieniono nazwy: {error}"),
            )
            return

        if row.kind != "track":
            self.announcer.say("Wybrany element nie jest plikiem lokalnym")
            return
        client = self._profile_edit_client()
        if client is None:
            return
        with RenameItemDialog(
            self,
            title="Zmień nazwę w Bibliotece",
            prompt="&Nowa nazwa w Bibliotece:",
            field_name="Nowa nazwa w Bibliotece",
            value=row.title,
            help_text="Plik na dysku nie zmieni nazwy.",
        ) as dialog:
            if dialog.ShowModal() != wx.ID_OK:
                return
            title = dialog.value
        if not title:
            self.announcer.say("Nowa nazwa w Bibliotece nie może być pusta")
            return
        if title == row.title:
            self.announcer.say("Nazwa w Bibliotece nie została zmieniona")
            return

        def done(_payload: object) -> None:
            self._refresh_profile_view(preferred_id=row.item_id)
            self.announcer.say(f"Zmieniono nazwę w Bibliotece: {title}")

        self.runner.submit(
            "profile-edit",
            lambda: client.rename_library_item(row.item_id, title),
            done,
            lambda error: self.announcer.say(f"Nie zmieniono nazwy: {error}"),
        )

    def _rename_local_file(self) -> None:
        if self.navigator.active is not SessionId.FILES:
            self.announcer.say("Zmiana nazwy pliku na dysku jest dostępna w Plikach lokalnych")
            return
        row = self._single_edit_row("zmiany nazwy pliku")
        if row is None:
            return
        if row.kind != "track" or not row.path:
            self.announcer.say("Wybrany element nie jest plikiem lokalnym")
            return
        client = self._profile_edit_client()
        if client is None:
            return
        current_name = Path(row.path).stem
        with RenameItemDialog(
            self,
            title="Zmień nazwę pliku na dysku",
            prompt="&Nowa nazwa pliku bez rozszerzenia:",
            field_name="Nowa nazwa pliku bez rozszerzenia",
            value=current_name,
            help_text="Rozszerzenie pliku pozostanie bez zmian.",
        ) as dialog:
            if dialog.ShowModal() != wx.ID_OK:
                return
            new_name = dialog.value
            # Bramka musi powstać JESZCZE PRZED zniszczeniem modalnego
            # dialogu. Na Windows oddanie fokusu podczas ``__exit__`` może
            # synchronicznie dostarczyć liście Enter, którym użytkownik
            # zatwierdził nazwę. Poprzednio ustawialiśmy flagę dopiero po
            # wyjściu z ``with`` i po ``SetFocus``. Ten krótki przedział
            # wystarczał, żeby uruchomić plik i ścigać się z File.Move.
            self._local_file_rename_pending = True
            self._local_file_rename_activation_guard_until = time.monotonic() + 1.0
        # Dialog jest już zniszczony. Jawnie oddajemy fokus tej samej liście,
        # zamiast pozwolić ramce albo odtwarzaczowi przejąć go po Enterze.
        self._restore_focus_after_dialog()
        if not new_name:
            self._local_file_rename_pending = False
            self.announcer.say("Nowa nazwa pliku nie może być pusta")
            return

        def done(payload: object) -> None:
            self._local_file_rename_pending = False
            data = payload if isinstance(payload, dict) else {}
            file_name = str(data.get("fileName") or new_name)
            new_path = str(data.get("path") or "").strip()
            if not new_path or not os.path.isfile(new_path):
                self.announcer.say(
                    "Nie zmieniono nazwy pliku: silnik nie potwierdził "
                    "nowego pliku na dysku"
                )
                self._refresh_profile_view(preferred_id=row.item_id)
                return
            old_key = os.path.normcase(os.path.normpath(row.path))
            for item in getattr(self.state, "recording_history", []):
                if not isinstance(item, dict):
                    continue
                candidate = item.get("path")
                if (
                    isinstance(candidate, str)
                    and os.path.normcase(os.path.normpath(candidate)) == old_key
                ):
                    item["path"] = new_path
            try:
                self.store.save(self.state)
            except (OSError, TypeError, ValueError):
                self.announcer.say(
                    "Zmieniono nazwę pliku, ale nie zapisano nowej ścieżki w historii"
                )
            self._refresh_profile_view(preferred_id=row.item_id)
            self.announcer.say(f"Zmieniono nazwę pliku na dysku: {file_name}")

        def failed(error: Exception) -> None:
            self._local_file_rename_pending = False
            # Operacja hosta mogła zatrzymać odtwarzanie albo częściowo
            # zmienić stan, zanim otrzymała błąd systemu plików. Ponowne
            # wczytanie nie udaje sukcesu, ale gwarantuje, że lista pokazuje
            # rzeczywisty stan dysku i zachowuje ten sam stabilny wiersz.
            self._refresh_profile_view(preferred_id=row.item_id)
            self.announcer.say(f"Nie zmieniono nazwy pliku: {error}")

        self.runner.submit(
            "profile-edit",
            lambda: client.rename_local_file(
                row.item_id, new_name, path=row.path
            ),
            done,
            failed,
        )

    def _forget_private_recording_history_paths(self, paths: list[str]) -> None:
        """Usuń prywatne kopie wpisów po potwierdzonej operacji na dysku."""
        keys: set[str] = set()
        for path in paths:
            try:
                keys.add(os.path.normcase(os.path.abspath(path)))
            except (TypeError, ValueError, OSError):
                continue
        if not keys:
            return
        current = getattr(self.state, "recording_history", [])
        if not isinstance(current, list):
            return
        kept: list[dict] = []
        changed = False
        for item in current:
            if not isinstance(item, dict):
                continue
            candidate = item.get("path") or item.get("outputPath")
            try:
                key = (
                    os.path.normcase(os.path.abspath(candidate))
                    if isinstance(candidate, str) and candidate.strip()
                    else ""
                )
            except (TypeError, ValueError, OSError):
                key = ""
            if key and key in keys:
                changed = True
                continue
            kept.append(item)
        if not changed:
            return
        self.state.recording_history = kept
        try:
            self.store.save(self.state)
        except (OSError, TypeError, ValueError):
            # Wspólny profil został już poprawiony przez host. Prywatna kopia
            # zostanie ponownie uzgodniona przy następnym zapisie stanu.
            pass

    def _remove_selected_items(self) -> None:
        if (
            self.navigator.active is SessionId.SPOTIFY
            and self.navigator.session.library_view
            is LibraryView.SPOTIFY_HISTORY
        ):
            self._remove_spotify_history_entries()
            return
        if (
            self.navigator.active is SessionId.FILES
            and self.navigator.session.library_view
            in (LibraryView.ITEM_BOOKMARKS, LibraryView.ALL_BOOKMARKS)
        ):
            self._remove_selected_bookmarks()
            return
        if (
            self.navigator.active is SessionId.PODCASTS
            and self.navigator.session.library_view
            is LibraryView.PODCAST_FAVORITES
        ):
            # Wszystkie wiersze tego widoku są ulubione, więc wspólna
            # transakcja ToggleFavorites usuwa dokładnie całe zaznaczenie.
            # Dotyczy zarówno źródeł, jak i odcinków i zachowuje wielokrotny
            # wybór kontrolki Windows.
            self._toggle_podcast_favorite()
            return
        rows = [
            row for row in self._selected_action_rows()
            if row.kind not in ("parent", "folder", "playlist", "loadMore")
        ]
        if not rows:
            self.announcer.say("Brak elementu do usunięcia")
            return
        if (
            self.navigator.active is SessionId.PODCASTS
            and self.navigator.session.library_view
            is not LibraryView.PODCAST_HISTORY
            and self.navigator.session.library_view
            is not LibraryView.PODCAST_QUEUE
            and self.navigator.session.library_view
            is not LibraryView.PODCAST_PLAYLIST_CONTENTS
            and any(row.kind != "podcast" for row in rows)
        ):
            self.announcer.say("Usuń źródło z głównej listy Podcastów i YouTube")
            return
        client = self._profile_edit_client()
        if client is None:
            return
        session_id = self.navigator.active.value
        view = self._current_profile_view_name()
        playlist_id = (
            self.navigator.session.library_playlist_id
            if view == LibraryView.PODCAST_PLAYLIST_CONTENTS.value
            else None
        )
        item_ids = [row.item_id for row in rows]
        titles = [row.title for row in rows]

        def done(_payload: object) -> None:
            self._refresh_profile_view()
            label = titles[0] if len(titles) == 1 else format_item_count(len(titles))
            if view in (
                LibraryView.HISTORY.value,
                LibraryView.PODCAST_HISTORY.value,
            ):
                message = f"Usunięto z Historii odtwarzania: {label}. Pliki i Biblioteka pozostały bez zmian"
            elif view == LibraryView.FAVORITES.value:
                message = f"Usunięto z Ulubionych: {label}"
            elif view in (LibraryView.SAVED_QUEUE.value, LibraryView.LIVE_QUEUE.value):
                message = f"Usunięto z Kolejki: {label}"
            elif view == LibraryView.PODCAST_QUEUE.value:
                message = f"Usunięto z Kolejki podcastów: {label}"
            elif view == LibraryView.PODCAST_PLAYLIST_CONTENTS.value:
                message = f"Usunięto z playlisty: {label}"
            elif session_id == SessionId.FILES.value:
                message = f"Usunięto z Biblioteki: {label}. Plik pozostał na dysku"
            elif session_id == SessionId.PODCASTS.value:
                message = f"Usunięto z Biblioteki podcastów: {label}"
            else:
                message = f"Usunięto stację: {label}"
            self.announcer.say(message)

        self.runner.submit(
            "profile-edit",
            lambda: client.remove_profile_items(
                session_id,
                view,
                item_ids,
                playlist_id=playlist_id,
            ),
            done,
            lambda error: self.announcer.say(f"Nie usunięto: {error}"),
        )

    def _remove_spotify_history_entries(self) -> None:
        """Delete removes only private history rows, never Spotify content."""

        selected = [
            row for row in self._selected_action_rows()
            if row.kind in ("track", "episode") and row.service_id
        ]
        if not selected:
            self.announcer.say("Brak wpisu Historii Spotify do usunięcia")
            return
        selected_ids = {row.item_id for row in selected}
        selected_external_ids = {row.service_id for row in selected}
        model_rows = list(self.navigator.session.model.rows)
        previous_selected_id = self.navigator.session.model.selected_id
        first_index = min(
            (
                index for index, row in enumerate(model_rows)
                if row.item_id in selected_ids
            ),
            default=0,
        )
        previous = list(self.state.spotify_playback_history)
        kept = [
            item for item in previous
            if item.get("externalId") not in selected_external_ids
        ]
        if len(kept) == len(previous):
            self.announcer.say("Historia Spotify bez zmian")
            return
        remaining = list(spotify_history_rows(kept))
        preferred_id = (
            remaining[min(first_index, len(remaining) - 1)].item_id
            if remaining
            else None
        )
        self.state.spotify_playback_history = kept
        self.navigator.session.model.replace(
            remaining, preferred_id=preferred_id
        )
        if self._save_state() is False:
            self.state.spotify_playback_history = previous
            self.navigator.session.model.replace(
                model_rows, preferred_id=previous_selected_id
            )
            return
        self._sync_views()
        label = (
            selected[0].title
            if len(selected) == 1
            else format_item_count(len(selected))
        )
        self.announcer.say(
            f"Usunięto z Historii Spotify: {label}. "
            "Biblioteka Spotify pozostała bez zmian"
        )

    def _remove_selected_bookmarks(self) -> None:
        """Delete w widoku zakładek usuwa wpisy, nigdy pliki źródłowe."""
        state = self.navigator.session
        rows = self._selected_action_rows()
        bookmark_rows = [
            row for row in rows if row.item_id.startswith("bookmark:")
        ]
        if not bookmark_rows or len(bookmark_rows) != len(rows):
            self.announcer.say("Brak zakładki do usunięcia")
            return
        client = self._profile_edit_client()
        if client is None:
            return

        selected_ids = {row.item_id for row in bookmark_rows}
        first_index = min(
            (
                index for index, row in enumerate(state.model.rows)
                if row.item_id in selected_ids
            ),
            default=0,
        )
        remaining = [
            row for row in state.model.rows if row.item_id not in selected_ids
        ]
        preferred_id = (
            remaining[min(first_index, len(remaining) - 1)].item_id
            if remaining
            else None
        )
        bookmark_ids = [
            row.item_id.removeprefix("bookmark:") for row in bookmark_rows
        ]
        label = (
            bookmark_rows[0].title
            if len(bookmark_rows) == 1
            else format_item_count(len(bookmark_rows))
        )

        def done(payload: object) -> None:
            data = payload if isinstance(payload, dict) else {}
            removed = int(data.get("removedCount") or 0)
            if removed <= 0:
                self.announcer.say("Zakładki bez zmian")
                return
            self._refresh_profile_view(preferred_id=preferred_id)
            self.announcer.say(f"Usunięto z Zakładek: {label}")

        self.runner.submit(
            "bookmark-remove",
            lambda: client.remove_bookmarks(bookmark_ids),
            done,
            lambda error: self.announcer.say(f"Nie usunięto zakładki: {error}"),
        )

    def _recycle_selected_files(self) -> None:
        if self.navigator.active is not SessionId.FILES:
            self.announcer.say("Przenoszenie do Kosza jest dostępne tylko dla plików lokalnych")
            return
        rows = [row for row in self._selected_action_rows() if row.kind == "track" and row.path]
        if not rows:
            self.announcer.say("Brak pliku do przeniesienia do Kosza")
            return
        label = rows[0].title if len(rows) == 1 else format_item_count(len(rows))
        if wx.MessageBox(
            f"Przenieść do Kosza: {label}?\n\n"
            "Pliki zostaną też usunięte z AMC. Można je odzyskać z systemowego Kosza.",
            "Przenieś pliki do Kosza",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING,
            self,
        ) != wx.YES:
            return
        client = self._profile_edit_client()
        if client is None:
            return
        item_ids = [row.item_id for row in rows]

        def done(payload: object) -> None:
            data = payload if isinstance(payload, dict) else {}
            removed = data.get("removed") if isinstance(data.get("removed"), list) else []
            failures = data.get("failures") if isinstance(data.get("failures"), list) else []
            removed_paths = [
                str(item.get("path"))
                for item in removed
                if isinstance(item, dict) and isinstance(item.get("path"), str)
            ]
            if removed_paths:
                self._forget_private_recording_history_paths(removed_paths)
            self._refresh_profile_view()
            if removed:
                removed_label = rows[0].title if len(removed) == 1 else format_item_count(len(removed))
                self.announcer.say(f"Przeniesiono do Kosza i usunięto z AMC: {removed_label}")
            if failures:
                self.announcer.say("Nie przeniesiono do Kosza: " + "; ".join(map(str, failures)))

        self.runner.submit(
            "profile-edit",
            lambda: client.recycle_local_files(
                item_ids,
                paths=[row.path for row in rows if row.path],
            ),
            done,
            lambda error: self.announcer.say(f"Nie przeniesiono do Kosza: {error}"),
        )

    # ------------------------------------------------------------- stacje

    def _selected_station(self) -> Station | None:
        row = self.navigator.sessions[SessionId.RADIO].model.selected_row
        if row is None:
            return None
        saved = self.stations.find(row.item_id)
        if saved is not None:
            return saved
        # Historia i Ulubione moga pokazywac stacje spoza biezacego zakresu
        # Biblioteki. Wiersz nadal niesie zamierzona nazwe i adres; nigdy nie
        # podstawiamy technicznej reprezentacji obiektu pod etykiete NVDA.
        if row.kind == "station" and row.url:
            return Station(id=row.item_id, name=row.title, url=row.url)
        return None

    def _recording_station(self) -> Station | None:
        if self.navigator.active is not SessionId.RADIO:
            self.announcer.say(
                "Nagrywanie ręczne jest dostępne dla wybranej stacji radia internetowego"
            )
            return None
        station = self._selected_station()
        if station is None:
            self.announcer.say("Wybierz stację radiową")
        return station

    def _announce_current_radio_broadcast_information(self) -> None:
        """Alt+D: stacja, parametry audio i aktualna audycja albo utwor."""
        client = self.client
        if client is None:
            self.announcer.say("Silnik odtwarzania jest niedostępny")
            return

        def done(payload: object) -> None:
            data = payload if isinstance(payload, dict) else {}
            text = str(data.get("text") or "").strip()
            self.announcer.say(
                text or "Brak informacji o bieżącej audycji lub utworze"
            )

        self.runner.submit(
            "radio-current-broadcast",
            client.current_radio_broadcast_information,
            done,
            lambda error: self.announcer.say(str(error)),
        )

    def _recognition_source_available(self) -> bool:
        scope = radio_recognition.normalize_scope(
            self.options.radio_recognition_scope
        )
        radio_status = getattr(self, "_transport_status_by_session", {}).get(
            SessionId.RADIO,
            {},
        )
        current = (
            scope in (
                radio_recognition.CURRENT_STATION,
                radio_recognition.CURRENT_AND_RECORDING_STATIONS,
            )
            and SessionId.RADIO in self._playing_sessions
            and not bool(radio_status.get("paused"))
        )
        recording_status = self._last_recording_status or {}
        recording_rows = recording_status.get("recordings")
        if isinstance(recording_rows, list):
            has_unpaused_recording = any(
                isinstance(row, dict)
                and not bool(row.get("paused"))
                and str(row.get("state") or "") != "stopping"
                for row in recording_rows
            )
        else:
            # Zgodność ze starszym hostem, który podawał tylko licznik.
            has_unpaused_recording = int(recording_status.get("count") or 0) > 0
        recordings = (
            scope in (
                radio_recognition.RECORDING_STATIONS,
                radio_recognition.CURRENT_AND_RECORDING_STATIONS,
            )
            and has_unpaused_recording
        )
        return current or recordings

    def _schedule_radio_recognition_after_source_change(self) -> None:
        if not self.options.radio_recognition_monitoring:
            self._radio_recognition_due = float("inf")
            return
        if not self._recognition_source_available():
            return
        self._radio_recognition_due = min(
            self._radio_recognition_due,
            time.monotonic() + 6.0,
        )

    def _recognize_radio_track(self, *, automatic: bool) -> None:
        """S albo zegar: gotowy wynik wraca, audio pozostaje w hoscie C#."""
        client = self.client
        if client is None:
            if not automatic:
                self.announcer.say("Silnik odtwarzania jest niedostępny")
            return
        if self._radio_recognition_pending:
            if not automatic:
                self.announcer.say("Rozpoznawanie już trwa")
            return
        if not automatic and SessionId.RADIO not in self._playing_sessions:
            self.announcer.say("Najpierw uruchom stację radiową")
            return

        scope = (
            radio_recognition.normalize_scope(
                self.options.radio_recognition_scope
            )
            if automatic
            else radio_recognition.CURRENT_STATION
        )
        self._radio_recognition_pending = True
        if not automatic:
            self.announcer.say("Rozpoznaję utwór")

        def done(payload: object) -> None:
            self._radio_recognition_pending = False
            merged = radio_recognition.merge_host_result(
                self.state.recognized_tracks,
                payload,
            )
            recognized_any = bool(merged.added or merged.duplicates)
            self._radio_recognition_due = time.monotonic() + (
                60.0 if recognized_any else 15.0
            ) if self.options.radio_recognition_monitoring else float("inf")
            self._last_radio_recognition_error = None

            if merged.added:
                self._save_state()
                if automatic:
                    if (
                        self.options.radio_recognition_announcements
                        and self.messages.speaks_routine
                    ):
                        for entry in merged.added:
                            self.announcer.say(
                                "Rozpoznano w stacji "
                                f"{entry['stationName']}: "
                                f"{radio_recognition.recognition_label(entry)}"
                            )
                else:
                    for entry in merged.added:
                        self.announcer.say(
                            "Rozpoznano: "
                            + radio_recognition.recognition_label(entry)
                        )
                return

            if automatic:
                return
            if merged.duplicates:
                self.announcer.say(
                    "Rozpoznano: "
                    + radio_recognition.recognition_label(merged.duplicates[0])
                    + ". Ten utwór jest już w najnowszej historii"
                )
                return
            message = (
                merged.failures[0]
                if merged.failures
                else merged.message
                or "Nie rozpoznano utworu"
            )
            self.announcer.say(message)

        def failed(error: Exception) -> None:
            self._radio_recognition_pending = False
            self._radio_recognition_due = (
                time.monotonic() + 15.0
                if self.options.radio_recognition_monitoring
                else float("inf")
            )
            message = str(error).strip() or "Nie udało się rozpoznać utworu"
            if automatic:
                if message != self._last_radio_recognition_error:
                    self._last_radio_recognition_error = message
                    self.status_bar.show(message)
            else:
                self.announcer.say(message)

        self.runner.submit(
            "radio-recognition",
            lambda: client.recognize_radio_tracks(scope),
            done,
            failed,
        )

    def _toggle_radio_recognition_monitoring(self) -> None:
        previous = self.options.radio_recognition_monitoring
        self.options.radio_recognition_monitoring = not previous
        if not self._save_state():
            self.options.radio_recognition_monitoring = previous
            return
        enabled = self.options.radio_recognition_monitoring
        self._radio_recognition_due = (
            time.monotonic() + 6.0 if enabled else float("inf")
        )
        self._refresh_menu_state()
        if enabled:
            message = (
                "Włączono i zapamiętano obserwowanie rozpoznawania: "
                + radio_recognition.scope_label(
                    self.options.radio_recognition_scope
                ).casefold()
            )
            if not self._recognition_source_available():
                message += (
                    ". Rozpoznawanie rozpocznie się, gdy pojawi się "
                    "odpowiednie źródło"
                )
            self.announcer.say(message)
        else:
            self.announcer.say(
                "Wyłączono i zapamiętano obserwowanie rozpoznawania utworów"
            )

    def _toggle_radio_recognition_announcements(self) -> None:
        previous = self.options.radio_recognition_announcements
        self.options.radio_recognition_announcements = not previous
        if not self._save_state():
            self.options.radio_recognition_announcements = previous
            return
        self._refresh_menu_state()
        if self.options.radio_recognition_announcements:
            self.announcer.say("Włączono oznajmianie rozpoznanych utworów")
        elif self.options.radio_recognition_monitoring:
            self.announcer.say(
                "Wyłączono oznajmianie rozpoznanych utworów. "
                "Obserwowanie nadal działa, a wyniki trafiają do historii"
            )
        else:
            self.announcer.say(
                "Wyłączono oznajmianie rozpoznanych utworów. "
                "Obserwowanie pozostaje wyłączone"
            )

    def _show_radio_recognition_history(self) -> None:
        dialog = RadioRecognitionHistoryDialog(
            self,
            self.state.recognized_tracks,
            copy_to_clipboard=self._to_clipboard,
            announce=self.announcer.say,
        )
        changed = False
        try:
            dialog.ShowModal()
            changed = dialog.changed
        finally:
            dialog.Destroy()
        if changed:
            self._save_state()
        self._restore_focus_after_dialog()

    def _toggle_radio_recording(self) -> None:
        client = self.client
        station = self._recording_station()
        if client is None or station is None:
            return

        # Ustawienia mogly zostac zmienione w glownym AMC juz po starcie wx.
        # Czytamy je ponownie bez zapisu i nie podmieniamy widoku listy.
        snapshot = LiteFrame._with_radio_recording_options(
            self, self.radio.load(previous=self._radio_snapshot)
        )
        payload = snapshot.recording.payload_for(station)

        def done(result: dict) -> None:
            # Parzystosc ze starym AMC: gest Ctrl+R od razu daje jedno
            # krotkie potwierdzenie. Zdarzenie recordingStarted uaktualnia
            # liste, ale dla nagrania recznego nie powtarza komunikatu ani
            # nazwy pliku. Blad uruchomienia nadal przyjdzie osobnym
            # recordingFailed, wiec nie udajemy, ze plik juz istnieje.
            action = str((result or {}).get("action") or "")
            if action == "starting":
                self.announcer.say(
                    f"Rozpoczynam nagrywanie w tle: {station.name}"
                )
            elif action == "stopping":
                self.announcer.say(f"Zatrzymuję nagrywanie: {station.name}")
            self._refresh_recording_status()

        self.runner.submit(
            "radio-recording-command",
            lambda: client.toggle_radio_recording(payload),
            done,
            lambda error: self.announcer.say(f"Nie można zmienić nagrywania: {error}"),
        )

    def _toggle_radio_recording_pause(self) -> None:
        client = self.client
        station = self._recording_station()
        if client is None or station is None:
            return

        def done(result: dict) -> None:
            state = str((result or {}).get("state") or "")
            if state == "paused":
                position = format_duration((result or {}).get("positionSeconds"))
                suffix = (
                    ". Zapis oryginalnego strumienia pozostał aktywny"
                    if int((result or {}).get("unpausableCount") or 0) else ""
                )
                self.announcer.say(
                    f"Wstrzymano nagrywanie: {station.name}, {position}{suffix}"
                )
            elif state == "recording":
                self.announcer.say(f"Wznowiono nagrywanie: {station.name}")
            elif state == "notRecording":
                self.announcer.say(f"Stacja nie jest nagrywana: {station.name}")
            elif state == "starting":
                self.announcer.say("Nagranie jeszcze się uruchamia")
            elif state == "unsupported":
                self.announcer.say(
                    str((result or {}).get("reason") or "Pauza jest niedostępna")
                )
            else:
                self.announcer.say(
                    "Trwa finalizowanie albo rozpoczynanie części nagrania"
                )

        self.runner.submit(
            "radio-recording-command",
            lambda: client.toggle_radio_recording_pause(station.id, station.url),
            done,
            lambda error: self.announcer.say(
                f"Nie można zmienić pauzy nagrania: {error}"
            ),
        )

    def _split_radio_recording(self) -> None:
        client = self.client
        station = self._recording_station()
        if client is None or station is None:
            return

        def done(result: dict) -> None:
            state = str((result or {}).get("state") or "")
            if state == "split":
                path = str((result or {}).get("currentPath") or "").strip()
                suffix = f": {Path(path).name}" if path else ""
                self.announcer.say(
                    f"Rozpoczęto nową część nagrania {station.name}{suffix}"
                )
            elif state == "tooSoon":
                self.announcer.say(
                    "Nowa część nagrania już trwa. Ponowne T pominięte"
                )
            elif state == "notRecording":
                self.announcer.say(f"Stacja nie jest nagrywana: {station.name}")
            elif state == "starting":
                self.announcer.say("Nagranie jeszcze się uruchamia")
            elif state == "stopping":
                self.announcer.say("Nagranie jest już zatrzymywane")
            else:
                self.announcer.say(
                    "Trwa finalizowanie albo rozpoczynanie części nagrania"
                )

        self.announcer.say(f"Zapisuję bieżącą część nagrania: {station.name}")
        self.runner.submit(
            "radio-recording-command",
            lambda: client.split_radio_recording(station.id, station.url),
            done,
            lambda error: self.announcer.say(f"Nie można podzielić nagrania: {error}"),
        )

    def _stop_all_radio_recordings(self) -> None:
        client = self.client
        if client is None:
            return

        def done(result: dict) -> None:
            count = int((result or {}).get("stopping") or 0)
            if count == 0:
                self.announcer.say("Brak trwających nagrań")
            elif count == 1:
                self.announcer.say("Zatrzymuję nagrywanie")
            else:
                self.announcer.say(f"Zatrzymuję wszystkie nagrania: {count}")

        self.runner.submit(
            "radio-recording-command",
            client.stop_all_radio_recordings,
            done,
            lambda error: self.announcer.say(f"Nie można zatrzymać nagrań: {error}"),
        )

    def _show_active_radio_recordings(self, *, announce: bool = True) -> None:
        """Pokaz stan hosta, bez ujawniania technicznych identyfikatorow."""
        client = self.client
        if client is None:
            if announce:
                self.announcer.say("Silnik odtwarzania jest niedostępny")
            return
        if announce:
            self._begin_transient_preview()
            # Sam wynik wypowie nazwe podgladu. Osobne "Radio internetowe"
            # przed nim byloby podwojnym komunikatem po jednym Alt+R.
            self.navigator.active = SessionId.RADIO
        preferred_id = self.navigator.sessions[SessionId.RADIO].model.selected_id

        def done(payload: dict) -> None:
            if announce and self._transient_preview_return is None:
                return
            rows = active_recording_rows(payload)
            events = self.navigator.apply_radio_view(
                LibraryView.ACTIVE_RADIO_RECORDINGS,
                "Nagrywane",
                rows,
                preferred_id=preferred_id,
            )
            if self.navigator.active is not SessionId.RADIO:
                return
            if announce:
                if rows:
                    self._run(events)
                else:
                    # Najpierw opróżniamy natywna liste, a dopiero potem
                    # wypowiadamy wynik. Gdy komunikat szedl przed zmiana
                    # kontrolki, zdarzenie usuniecia ostatniego wiersza
                    # dopisywalo na koncu mylace "nieznane".
                    self._sync_views()
                    self._announce_after_native_list_update(events[0].text)
            else:
                # Odswiezenie po zdarzeniu nie moze zagluszac komunikatu o
                # starcie, zatrzymaniu lub bledzie nagrania.
                self._sync_views()

        def failed(error: Exception) -> None:
            if announce and self.navigator.active is SessionId.RADIO:
                self._restore_transient_preview(announce=False, force=True)
                self.announcer.say(f"Nie można wczytać trwających nagrań: {error}")

        self.runner.submit(
            "radio-recordings-view",
            client.radio_recording_status,
            done,
            failed,
        )

    def _remember_recording_result(self, payload: object) -> bool:
        """Utrwal wynik w prywatnym stanie bez zmiany profilu pelnego AMC."""
        entry = recording_history_payload_from_event(payload)
        if entry is None:
            return False
        history = [
            item for item in getattr(self.state, "recording_history", [])
            if isinstance(item, dict) and item.get("id") != entry["id"]
        ]
        self.state.recording_history = [entry, *history][:1_000]
        try:
            self.store.save(self.state)
        except (OSError, TypeError, ValueError):
            # Komunikat o zakonczeniu nagrania pozostaje pojedynczy. Problem
            # zapisu wyjasnimy po otwarciu Historii, gdzie jest istotny.
            self._recording_history_persist_error = True
            return False
        self._recording_history_persist_error = False
        return True

    def _show_radio_recording_history(
        self,
        *,
        announce: bool = True,
        preferred_id: str | None = None,
    ) -> None:
        """Alt+Shift+R: biezaca sesja hosta i nagrania nadal na dysku."""
        if announce:
            self._begin_transient_preview()
            self.navigator.active = SessionId.FILES
        previous = self._radio_snapshot
        client = self.client

        def work():
            snapshot = LiteFrame._with_radio_recording_options(
                self, self.radio.load(previous=previous)
            )
            current_entries = ()
            current_error = ""
            if client is not None:
                try:
                    payload = client.radio_recording_history()
                    current_entries = recording_history_from_amc_state({
                        "radio": {
                            "recordingHistory": payload.get("recordings", [])
                            if isinstance(payload, dict) else []
                        }
                    })
                except (HostError, HostUnavailable, OSError) as error:
                    current_error = str(error)
            stored_entries = recording_history_from_amc_state({
                "radio": {
                    "recordingHistory": getattr(
                        self.state, "recording_history", []
                    )
                }
            })
            return (
                snapshot,
                recording_history_rows(
                    recent_recording_history(current_entries, stored_entries),
                ),
                current_error,
            )

        def done(result) -> None:
            if announce and self._transient_preview_return is None:
                return
            if not announce and (
                self.navigator.active is not SessionId.FILES
                or self.navigator.sessions[SessionId.FILES].library_view
                is not LibraryView.RECORDED_RADIO_FILES
            ):
                return
            snapshot, rows, current_error = result
            self._radio_snapshot = snapshot
            self.stations = snapshot.list
            if announce and snapshot.load_error and not rows:
                self._restore_transient_preview(announce=False, force=True)
                self.announcer.say(snapshot.load_error)
                return
            events = self.navigator.apply_library_view(
                LibraryView.RECORDED_RADIO_FILES,
                "Historia nagrywania",
                rows,
                preferred_id=preferred_id,
            )
            if self.navigator.active is SessionId.FILES:
                if announce:
                    self._run(events)
                else:
                    self._sync_views()
                if announce and snapshot.load_error:
                    self.announcer.say(snapshot.load_error)
                if announce and current_error:
                    self.announcer.say(
                        "Historia bieżącej sesji nagrywania jest chwilowo niedostępna"
                    )

        def failed(error: Exception) -> None:
            if announce:
                self._restore_transient_preview(announce=False, force=True)
                self.announcer.say(f"Nie można wczytać historii nagrywania: {error}")

        self.runner.submit("radio-recording-history", work, done, failed)

    def _show_radio_schedules(self, *, create_for_selected: bool = False) -> None:
        """Ctrl+Shift+H: natywne zarzadzanie planami wykonywanymi przez host."""
        client = self.client
        if client is None:
            self.announcer.say("Silnik odtwarzania jest niedostępny")
            return
        previous = self._radio_snapshot
        selected_station = self._selected_station() if create_for_selected else None
        if create_for_selected and selected_station is None:
            self.announcer.say("Zaznacz stację, dla której chcesz zaplanować nagranie")
            return

        def work():
            snapshot = LiteFrame._with_radio_recording_options(
                self, self.radio.load(previous=previous)
            )
            schedules = radio_schedule_settings.effective_schedules(
                snapshot.recording_schedules,
                self.state.radio_schedule_overrides,
            )
            wake = radio_schedule_settings.effective_wake(
                snapshot.wake_scheduled_recordings,
                self.state.radio_schedule_wake_override,
            )
            payload = client.sync_radio_schedules(
                self._radio_schedule_sync_payload(snapshot, self.state)
            )
            return snapshot, schedules, wake, payload

        def done(result) -> None:
            snapshot, schedules, wake, payload = result
            self._radio_snapshot = snapshot
            self.stations = snapshot.list
            schedules = radio_schedule_settings.schedules_from_host_status(
                payload, schedules
            )
            if self.state.radio_schedule_overrides is not None:
                # Host jest zrodlem prawdy o wykonanym terminie: po nagraniu
                # jednorazowym wylacza plan, a cykliczny przesuwa. Utrwalamy
                # te zmiany w prywatnym pliku wxPython, nie w profilu WPF.
                previous_effective = self.state.radio_schedule_overrides
                self.state.radio_schedule_overrides = schedules
                try:
                    self.store.save(self.state)
                except Exception:
                    self.state.radio_schedule_overrides = previous_effective
                    self.announcer.say(
                        "Nie udało się zapisać aktualnego terminu harmonogramu"
                    )
            if snapshot.load_error and not schedules:
                self.announcer.say(snapshot.load_error)
                return

            def commit(updated: list[dict], updated_wake: bool):
                old_schedules = self.state.radio_schedule_overrides
                old_wake = self.state.radio_schedule_wake_override
                self.state.radio_schedule_overrides = (
                    radio_schedule_settings.clone_schedules(updated)
                )
                self.state.radio_schedule_wake_override = bool(updated_wake)
                try:
                    self.store.save(self.state)
                    synced = client.sync_radio_schedules(
                        self._radio_schedule_sync_payload(snapshot, self.state)
                    )
                    self.state.radio_schedule_overrides = (
                        radio_schedule_settings.schedules_from_host_status(
                            synced, self.state.radio_schedule_overrides
                        )
                    )
                    self.store.save(self.state)
                    return synced
                except Exception:
                    # Zapis i wykonawca sa jedna zmiana z punktu widzenia
                    # uzytkownika. Gdy ktorykolwiek etap zawiedzie, wracamy do
                    # poprzednich danych i probujemy przywrocic je hostowi.
                    self.state.radio_schedule_overrides = old_schedules
                    self.state.radio_schedule_wake_override = old_wake
                    try:
                        self.store.save(self.state)
                    except Exception:
                        pass
                    try:
                        client.sync_radio_schedules(
                            self._radio_schedule_sync_payload(snapshot, self.state)
                        )
                    except Exception:
                        pass
                    raise

            if create_for_selected and selected_station is not None:
                self._open_new_radio_schedule(
                    snapshot=snapshot,
                    schedules=schedules,
                    wake=wake,
                    selected_station=selected_station,
                    commit=commit,
                )
                return

            with RadioSchedulesDialog(
                self,
                stations=snapshot.stations,
                recording=snapshot.recording,
                schedules=schedules,
                wake_scheduled_recordings=wake,
                labels_payload=payload,
                commit=commit,
                initial_station_id=(
                    selected_station.id if selected_station is not None else None
                ),
            ) as dialog:
                dialog.ShowModal()
            if self.navigator.view is View.LIST:
                self._active_list().SetFocus()
            else:
                self.play_button.SetFocus()
            if snapshot.load_error:
                self.announcer.say(snapshot.load_error)

        def failed(error: Exception) -> None:
            self.announcer.say(f"Nie można wczytać harmonogramu nagrywania: {error}")

        self.runner.submit("radio-schedules", work, done, failed)

    def _open_new_radio_schedule(
        self,
        *,
        snapshot,
        schedules: list[dict],
        wake: bool,
        selected_station: Station,
        commit,
    ) -> None:
        """Shift+R: od razu formularz nowego planu dla wskazanej stacji.

        Wczesniejsza droga najpierw otwierala okno zarzadzania, a dopiero z
        ``wx.CallAfter`` probowala nalozyc na nie drugi modalny dialog. Na
        zywym Windows ten posredni krok potrafil nie pokazac formularza.
        """
        stations = list(snapshot.stations)
        if all(station.id != selected_station.id for station in stations):
            stations.append(selected_station)
        schedule = None
        with RadioScheduleEditorDialog(
            self,
            stations=stations,
            recording=snapshot.recording,
            global_wake=wake,
            preferred_station_id=selected_station.id,
        ) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                schedule = dialog.result_schedule
        if schedule is None:
            self._restore_focus_after_dialog()
            return
        try:
            commit([*schedules, schedule], wake)
        except Exception:
            self.announcer.say(
                "Nie udało się zapisać harmonogramu. Niczego nie zmieniono"
            )
        else:
            name = str(schedule.get("name") or schedule.get("stationName") or "plan")
            self.announcer.say(f"Dodano plan {name}")
        self._restore_focus_after_dialog()

    @staticmethod
    def _radio_schedule_sync_payload(snapshot, state: LiteState | None = None) -> dict:
        """Efektywne plany ida do hosta; profil pelnego AMC pozostaje read-only."""
        recording = snapshot.recording
        schedules = radio_schedule_settings.effective_schedules(
            snapshot.recording_schedules,
            state.radio_schedule_overrides if state is not None else None,
        )
        wake = radio_schedule_settings.effective_wake(
            snapshot.wake_scheduled_recordings,
            state.radio_schedule_wake_override if state is not None else None,
        )
        return {
            "schedules": schedules,
            "defaultFolder": recording.default_folder or "",
            "folderPreset": recording.folder_preset,
            "stationFolders": dict(recording.station_folders),
            "recordingFormat": recording.format,
            "recordingBitrateKbps": recording.bitrate_kbps,
            "wakeScheduledRecordings": wake,
        }

    def _reload_stations(self, preferred_id: str | None = None) -> None:
        rows = rows_from_stations(self.stations.as_payload())
        if self.radio.may_edit:
            self._radio_snapshot.current_id = preferred_id or self._radio_snapshot.current_id
            self.radio.save(self._radio_snapshot)
        self._run(self.navigator.apply_stations(rows, preferred_id=preferred_id))

    def _station_add(self) -> None:
        self._switch_session(SessionId.RADIO)
        with StationDialog(self, "Dodaj stacje") as dialog:
            if dialog.ShowModal() != wx.ID_OK:
                return
            name, url = dialog.values
        if not self.radio.may_edit:
            client = self._profile_edit_client()
            if client is None:
                return

            def done(payload: dict) -> None:
                result = payload or {}
                station_id = str(result.get("preferredStationId") or "") or None
                station_name = str(result.get("preferredStationName") or name)
                updated = int(result.get("updatedCount") or 0)
                message = (
                    f"Zaktualizowano stację: {station_name}"
                    if updated
                    else f"Dodano stację do Biblioteki: {station_name}"
                )
                self._open_radio_view(
                    OpenLibraryView(
                        view=None,
                        preferred_id=station_id,
                        target_session_id=SessionId.RADIO,
                    ),
                    after_refresh=lambda: self.announcer.say(message),
                )

            self.runner.submit(
                "profile-edit",
                lambda: client.add_radio_station(name, url),
                done,
                lambda error: self.announcer.say(f"Nie dodano stacji: {error}"),
            )
            return
        try:
            station = self.stations.add(name, url)
        except ValueError as error:
            self.announcer.say(str(error))
            return
        self._reload_stations(preferred_id=station.id)
        self.announcer.say(f"Dodano {station.name}")

    def _station_edit(self) -> None:
        station = self._selected_station()
        if station is None:
            self.announcer.say("Nie wybrano stacji")
            return
        with StationDialog(self, "Zmien stacje", station.name, station.url) as dialog:
            if dialog.ShowModal() != wx.ID_OK:
                return
            name, url = dialog.values
        if not self.radio.may_edit:
            client = self._profile_edit_client()
            if client is None:
                return

            def done(_payload: object) -> None:
                self._refresh_profile_view(preferred_id=station.id)
                self.announcer.say(f"Zapisano nazwę i adres stacji: {name}")

            self.runner.submit(
                "profile-edit",
                lambda: client.edit_radio_station(station.id, name, url),
                done,
                lambda error: self.announcer.say(f"Nie zapisano stacji: {error}"),
            )
            return
        try:
            self.stations.edit(station.id, name, url)
        except ValueError as error:
            self.announcer.say(str(error))
            return
        self._reload_stations(preferred_id=station.id)
        self.announcer.say(f"Zapisano {name or url}")

    def _station_delete(self) -> None:
        station = self._selected_station()
        if station is None:
            self.announcer.say("Nie wybrano stacji")
            return
        if wx.MessageBox(
            f"Usunac stacje {station.name}?", "Potwierdzenie",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION, self,
        ) != wx.YES:
            return
        if not self.radio.may_edit:
            client = self._profile_edit_client()
            if client is None:
                return
            view = self._current_profile_view_name()

            def done(_payload: object) -> None:
                self._refresh_profile_view()
                self.announcer.say(f"Usunięto {station.name}")

            self.runner.submit(
                "profile-edit",
                lambda: client.remove_profile_items("radio", view, [station.id]),
                done,
                lambda error: self.announcer.say(f"Nie usunięto stacji: {error}"),
            )
            return
        self.stations.remove(station.id)
        self._reload_stations()
        self.announcer.say(f"Usunieto {station.name}")

    def _station_import(self) -> None:
        """Import M3U/PLS ISTNIEJACYM importerem AMC (w hoscie).

        Plik uzytkownika czytamy TYLKO po jego wskazaniu - nic nie jest
        przenoszone ani kopiowane automatycznie.
        """
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie dziala, import niedostepny")
            return
        wildcard = "Listy stacji|*.m3u;*.m3u8;*.pls;*.xspf;*.asx|Wszystkie|*.*"
        with wx.FileDialog(
            self, "Wskaz liste stacji", wildcard=wildcard, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as dialog:
            if dialog.ShowModal() != wx.ID_OK:
                return
            path = dialog.GetPath()

        self._switch_session(SessionId.RADIO)

        def work() -> dict:
            if self.radio.may_edit:
                return client.import_playlist(path)
            return client.import_playlist_to_library(path)

        def done(payload: dict) -> None:
            result = payload or {}
            if self.radio.may_edit:
                entries = result.get("stations") or []
                added, skipped = self.stations.merge_imported(entries)
                self._reload_stations()
                self.announcer.say(f"Zaimportowano {added}, pominięto {skipped}")
                return

            added = int(result.get("addedCount") or 0)
            promoted = int(result.get("promotedCount") or 0)
            skipped = int(result.get("skippedCount") or 0)
            if added == 0 and promoted == 0:
                self.announcer.say(
                    "Playlista nie zawiera nowych prawidłowych stacji"
                    if skipped
                    else "Playlista nie zawiera stacji radiowych"
                )
                return
            station_id = str(result.get("preferredStationId") or "") or None
            message = (
                f"Dodano nowe stacje: {added}. "
                f"Włączono istniejące w Bibliotece: {promoted}. "
                "Zachowano dotychczasowe nazwy"
            )
            if skipped:
                message += f". Pominięto: {skipped}"
            self._open_radio_view(
                OpenLibraryView(
                    view=None,
                    preferred_id=station_id,
                    target_session_id=SessionId.RADIO,
                ),
                after_refresh=lambda: self.announcer.say(message),
            )

        self.runner.submit(
            "import", work, done, lambda error: self.announcer.say(f"Import nieudany: {error}")
        )

    def _station_export_favorites(self) -> None:
        """Eksport Ulubionych przez wspólny, bezpieczny eksporter AMC."""
        client = self.client
        if client is None:
            self.announcer.say("Silnik nie działa, eksport niedostępny")
            return
        with wx.FileDialog(
            self,
            message="Eksportuj ulubione stacje do playlisty",
            defaultFile="Ulubione stacje AMC.m3u",
            wildcard=RADIO_EXPORT_WILDCARD,
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as dialog:
            if dialog.ShowModal() != wx.ID_OK:
                self._restore_focus_after_dialog()
                return
            path = radio_export_path_for_filter(
                dialog.GetPath(),
                dialog.GetFilterIndex(),
            )

        def done(payload: dict) -> None:
            count = int((payload or {}).get("exportedCount") or 0)
            self.announcer.say(f"Wyeksportowano ulubione stacje: {count}")

        self.runner.submit(
            "radio-export",
            lambda: client.export_radio_favorites(path),
            done,
            lambda error: self.announcer.say(str(error)),
        )

    # --------------------------------------------------------------- pomoc

    def _toggle_keyboard_help(self) -> None:
        self._keyboard_help_active = not bool(getattr(self, "_keyboard_help_active", False))
        self._refresh_menu_state()
        self.announcer.say(
            "Pomoc klawiatury włączona. Naciśnij skrót, aby poznać jego "
            "działanie. Ctrl+F1 lub Escape wyłącza pomoc"
            if self._keyboard_help_active
            else "Pomoc klawiatury wyłączona"
        )

    @staticmethod
    def _is_modifier_only_event(event: wx.KeyEvent) -> bool:
        code = event.GetKeyCode()
        return code in {
            getattr(wx, "WXK_CONTROL", -1),
            getattr(wx, "WXK_SHIFT", -2),
            getattr(wx, "WXK_ALT", -3),
            getattr(wx, "WXK_RAW_CONTROL", -4),
        }

    def _shortcut_action_for_help(self, chord: Chord) -> Action | None:
        player = self.navigator.view is View.PLAYER
        session = self.navigator.sessions[self.navigator.active]
        return resolve(
            chord,
            player_view=player,
            radio_session=self.navigator.active is SessionId.RADIO,
            radio_recording_context=(
                not player
                and self.navigator.active is SessionId.RADIO
                and session.library_view is LibraryView.ACTIVE_RADIO_RECORDINGS
            ),
            podcast_inbox=(
                not player
                and self.navigator.active is SessionId.PODCASTS
                and session.library_view is LibraryView.PODCAST_INBOX
            ),
            podcast_session=self.navigator.active is SessionId.PODCASTS,
            tidal_session=self.navigator.active is SessionId.TIDAL,
            tidal_collection=(
                not player
                and self.navigator.active is SessionId.TIDAL
                and session.library_view in (
                    LibraryView.TIDAL_LIBRARY,
                    LibraryView.TIDAL_FAVORITES,
                    LibraryView.TIDAL_PLAYLISTS,
                )
            ),
            spotify_session=self.navigator.active is SessionId.SPOTIFY,
            spotify_collection=(
                not player
                and self.navigator.active is SessionId.SPOTIFY
                and isinstance(
                    session.spotify_context,
                    OpenSpotifyCollectionView,
                )
            ),
            wiim_session=self.navigator.active is SessionId.WIIM,
            wiim_streams=(
                not player
                and self.navigator.active is SessionId.WIIM
                and session.library_view is LibraryView.WIIM_NETWORK_STREAMS
            ),
            sonos_session=self.navigator.active is SessionId.SONOS,
            sonos_own_streams=(
                not player
                and self.navigator.active is SessionId.SONOS
                and session.library_view is LibraryView.SONOS_OWN_STREAMS
            ),
        )

    def _action_available_in_active_session(self, action: Action) -> bool:
        if (
            self.navigator.active is SessionId.SPOTIFY
            and action is Action.REMOVE_SELECTED
            and self.navigator.session.library_view
            is LibraryView.SPOTIFY_HISTORY
        ):
            return True
        supported = {
            SessionId.TIDAL: TIDAL_SUPPORTED_ACTIONS,
            SessionId.SPOTIFY: SPOTIFY_SUPPORTED_ACTIONS,
            SessionId.WIIM: WIIM_SUPPORTED_ACTIONS,
            SessionId.SONOS: SONOS_SUPPORTED_ACTIONS,
        }.get(self.navigator.active)
        return supported is None or action in supported

    def _handle_keyboard_help_event(self, event: wx.KeyEvent) -> bool:
        chord = chord_from_event(event)
        if not bool(getattr(self, "_keyboard_help_active", False)):
            if chord.canonical != "Ctrl+F1":
                return False
            self._toggle_keyboard_help()
            return True

        if self._is_modifier_only_event(event):
            return True
        if chord.canonical in ("Ctrl+F1", "Escape"):
            self._toggle_keyboard_help()
            return True

        action = self._shortcut_action_for_help(chord)
        self.announcer.say(
            keyboard_help_announcement(
                chord,
                action,
                SESSION_LABELS[self.navigator.active],
                available=(
                    action is None
                    or self._action_available_in_active_session(action)
                ),
            )
        )
        return True

    def _show_help(self) -> None:
        lines = [f"{chord}\t{label}" for chord, label in describe()]
        wx.MessageBox("\n".join(lines), "Skroty klawiszowe", wx.OK | wx.ICON_INFORMATION, self)

    # -------------------------------------------------------- zapis i koniec

    def _save_state(self) -> bool:
        """Utrwal prywatny stan. ``False`` = dysk ODMOWIL zapisu.

        Wynik jest istotny: wolacz, ktory wlasnie zmienil stan w pamieci i w
        silniku, musi umiec rozpoznac odmowe i wrocic do stanu trwalego.
        Bez tego uzytkownik slyszal "Nie moge zapisac" i zaraz po nim
        "Zapisano", a profil rozjezdzal sie z tym, co naprawde gra.
        """
        self.state.options = self.options.clamp()
        # Stacji NIE dopisujemy do prywatnego stanu: we wspolnym profilu naleza
        # do AMC, a w piaskownicy zapisuje je RadioSource.
        self.state.navigation = self.navigator.snapshot()
        try:
            self.store.save(self.state)
        except OSError as error:
            self.announcer.say(f"Nie moge zapisac ustawien: {error}")
            return False
        return True

    def _on_close(self, event: wx.CloseEvent) -> None:
        # Zamknięcie przez nową wersję, instalator albo użytkownika jest tą
        # samą operacją. Nigdy nie kończymy hosta, dopóki trwa nagrywanie.
        # Odpowiedź pobieramy bezpośrednio z właściciela toru, a nie tylko z
        # okresowej migawki interfejsu. Brak odpowiedzi również oznacza odmowę:
        # bezpieczeństwo nagrania ma pierwszeństwo przed automatyczną wymianą.
        can_veto = bool(getattr(event, "CanVeto", lambda: True)())
        if can_veto and self.client is not None and self.client.alive:
            try:
                recording_status = self.client.radio_recording_status()
                self._last_recording_status = recording_status
            except Exception:
                event.Veto()
                self.announcer.say(
                    "Nie zamykam AMC Python, ponieważ nie można potwierdzić "
                    "stanu nagrywania"
                )
                _present_main_window(self)
                return
            if int((recording_status or {}).get("count") or 0) > 0:
                event.Veto()
                self.announcer.say(
                    "Nie zamykam AMC Python, ponieważ trwa nagrywanie"
                )
                _present_main_window(self)
                return
        self.timer.Stop()
        # Dlugie operacje fragmentu sa jawnie anulowane przed EOF hosta.
        # Edytory C# usuwaja swoje pliki techniczne i nie dotykaja oryginalu
        # przed zweryfikowanym, atomowym etapem podmiany.
        if self.client is not None:
            operation_ids = {
                value
                for value in (
                    self._audio_clip_export_operation_id,
                    self._audio_clip_edit_operation_id,
                )
                if value
            }
            for operation_id in operation_ids:
                try:
                    self.client.cancel_audio_clip(operation_id)
                except Exception:
                    # ``client.close`` ma jeszcze awaryjne zamkniecie procesu;
                    # okna nie blokujemy osobnym komunikatem podczas wyjscia.
                    pass
        self.gate.cancel_all()
        self._save_state()
        if self.client is not None:
            self.client.close()
        event.Skip()


class LiteApp(wx.App):
    def OnInit(self) -> bool:  # noqa: N802 - API wx
        self.SetAppName(APP_NAME)
        # Drugi frontend nie może uruchamiać drugiego właściciela postępu
        # podcastów ani osobnego silnika audio. Wcześniej takie okno otwierało
        # się bez hosta: lista była widoczna, lecz Enter, Ctrl+R i informacje
        # pod lewą strzałką nie działały. Checker musi pozostać polem aplikacji
        # przez cały MainLoop; zmienna lokalna zostałaby zwolniona za wcześnie.
        self._instance_checker = wx.SingleInstanceChecker(
            f"{APP_NAME}-{wx.GetUserId()}"
        )
        if self._instance_checker.IsAnotherRunning():
            requested = _request_previous_instance_close()
            released = requested and _wait_for_previous_instance(
                self._instance_checker
            )
            if not released:
                _activate_window_handle(_windows_main_window())
                wx.MessageBox(
                    "Poprzednia instancja AMC Python pozostała uruchomiona. "
                    "Może trwać nagrywanie albo program nie potwierdził "
                    "bezpiecznego zamknięcia.",
                    "AMC Python",
                    wx.OK | wx.ICON_INFORMATION,
                )
                return False

            # Checker utworzony, gdy blokada należała do poprzednika, nie musi
            # automatycznie stać się jej właścicielem. Tworzymy go ponownie;
            # drugie sprawdzenie zamyka krótkie okno wyścigu dwóch uruchomień.
            self._instance_checker = wx.SingleInstanceChecker(
                f"{APP_NAME}-{wx.GetUserId()}"
            )
            if self._instance_checker.IsAnotherRunning():
                _activate_window_handle(_windows_main_window())
                return False
        # ``Window.SetHelpText`` zapisuje tekst dopiero przez aktywnego
        # HelpProvidera. Bez niego metoda przyjmowala podpowiedz, lecz natywna
        # kontrolka oddawala pusty ``GetHelpText`` i NVDA nie mial czego
        # odczytac. Provider powstaje przed ramka i zyje razem z aplikacja.
        if hasattr(wx, "SimpleHelpProvider") and hasattr(wx, "HelpProvider"):
            self._help_provider = wx.SimpleHelpProvider()
            wx.HelpProvider.Set(self._help_provider)
        store = StateStore()
        frame = LiteFrame(store, store.load())
        if hasattr(self, "SetTopWindow"):
            self.SetTopWindow(frame)
        _present_main_window(frame)
        wx.CallAfter(_present_main_window, frame)
        return True


def main() -> int:
    # Na Windows wlasciwe DPI daje czytelny tekst i poprawne wspolrzedne.
    if os.name == "nt":
        try:
            import ctypes

            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # type: ignore[attr-defined]
        except Exception:
            pass
    app = LiteApp(False)
    app.MainLoop()
    return 0
