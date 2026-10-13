"""Skroty klawiszowe AMC-wx-Lite.

KAZDY skrot ponizej zostal ODCZYTANY ZE ZRODEL pelnego AMC, nie wymyslony.
Zrodla (gałąź hermes/wx-lite-after416, baza 4.1.6):

  src/AccessibleMediaController.Windows/MainWindow.xaml.cs
    21449  modifiers == ModifierKeys.Control && TryGetDigitKey(...) -> SessionSlot
           => Ctrl+cyfra wybiera sesje.
    20773  e.Key == Key.F6 && Modifiers is None or Shift
    20775      _playerViewActive && Shift -> ReturnFromPlayerToList()
    20778      else ShowPlayerView()
           => F6 idzie do odtwarzacza, Shift+F6 wraca na liste.
    20792  Modifiers == None && e.Key == Key.Escape -> ReturnFromPlayerToList()
           => Escape z odtwarzacza wraca na liste.
    20832  Modifiers == None && e.Key == Key.Back (poza polem tekstowym)
           => Backspace wychodzi do folderu nadrzednego.
    21687  (ModifierKeys.None, Key.Space) => CommandIds.PlayPause
           => Spacja to pauza/wznowienie.

  src/AccessibleMediaController.Core/Input/KeyboardProfile.cs  (profil globalny,
  uzywany PO AKORDZIE PREFIKSU; te same KIERUNKI przenosimy na okno wx):
    57-60  Left/Right = przewijanie 10 s, Up/Down = glosnosc +-5
    63-66  Shift+Left/Right = 60 s, Shift+Up/Down = glosnosc +-1
    70-72  Ctrl+E czas miniony, Ctrl+R pozostaly, Ctrl+T calkowity

UWAGA o strzalkach: w pelnym AMC Up/Down zmieniaja glosnosc dopiero PO akordzie
prefiksu, bo zwykle strzalki musza chodzic po liscie. Tutaj tak samo - na liscie
strzalki naleza do natywnego ListCtrl, a glosnosc i przewijanie dzialaja w widoku
ODTWARZACZA, gdzie nie ma po czym chodzic. To swiadoma decyzja, nie rozjazd.

POPRAWKA PARYTETU TRANSPORTU (zgloszenie z realnego uruchomienia)
-----------------------------------------------------------------
Michal uruchomil ten wariant na prawdziwym profilu i transport NIE byl tym
transportem, ktory zna z AMC: nie dzialalo ``Ctrl+Shift+E/R/T`` (dzialalo
``Ctrl+E/R/T``), nie dzialalo ``Ctrl+Left/Right``, a predkosci nie dalo sie
znalezc pod klawiszami oryginalu.

Zrodlo bledu: powyzsze wiersze ``KeyboardProfile.cs:70-72`` opisuja profil
czytany PO AKORDZIE PREFIKSU -- to INNA WARSTWA niz klawisze okna. Wziecie ich
za skroty okna dalo gesty, ktorych oryginal w oknie nie ma, i zabralo gesty,
ktore ma. Warstwa okna to:

  MainWindow.xaml.cs  (dwie drogi tego samego okna: 215xx sciezka klawiszy
  i 22xxx tablica skrotow -- OBIE musza sie zgadzac)
    21583-21590 / 22387-22394  przewijanie, CZTERY pary:
        (None)        Left/Right -> SeekBackward10  / SeekForward10
        (Shift)       Left/Right -> SeekBackward30  / SeekForward30
        (Control)     Left/Right -> SeekBackward60  / SeekForward60
        (Control|Alt) Left/Right -> SeekBackwardCustom / SeekForwardCustom
      => ``Shift`` to 30 s, NIE 60 s. 60 s siedzi pod ``Ctrl``.
    21595-21597 / 22395-22397  predkosc odtwarzania:
        Shift+OemComma  -> PlaybackRateDown
        Shift+OemPeriod -> PlaybackRateUp
        Ctrl+OemPeriod  -> PlaybackRateReset
      => NIE ``Ctrl+Up/Down`` ani ``Ctrl+0``.
    21670 / 22188  Ctrl+Shift+G -> SettingsToggleSeekMessages
    21674-21676 / 22190-22192  Ctrl+Shift+E/R/T -> TimeElapsed/Remaining/Total
    21555-21557 / 22348-22350  cyfra BEZ modyfikatora -> SeekPercent(digit*10)
    21454-21456  Ctrl+cyfra -> SessionSlot, a Ctrl+0 -> SessionList
      => ``Ctrl+0`` NIE jest resetem tempa; to cudzy gest.
    21662  Ctrl+E -> ExportRadioFavorites
      => w oknie ``Ctrl+E`` nalezy do eksportu, wiec alias czasu byl bledem.
    20778-20785  F6 i Shift+F6: na LISCIE oba ida do ShowPlayerView, w
      ODTWARZACZU oba wracaja na liste (warunek to ``_playerViewActive``).

Zadne z powyzszych nie jest przechwytywaniem gestow czytnika ekranu: NVDA+Up,
NVDA+End i reszta gestow czytnika pozostaja nietkniete, a strzalki PIONOWE na
LISCIE nadal naleza do natywnej kontrolki.

LEWA STRZALKA NA LISCIE (zgloszenie z realnego uruchomienia)
------------------------------------------------------------
Michal zglosil, ze na listach stacji i plikow nie dziala lewa strzalka, ktora
w AMC czyta parametry zaznaczonego wiersza. Potwierdzone WYKONANIEM resolvera:
``resolve(Chord("Left"), player_view=False, radio_session=True)`` oddawalo
``None`` (to samo dla ``radio_session=False``), czyli klawisz ginal w kontrolce.
Brak byl rzeczywisty, nie domniemany.

Zrodlo wzorca: ``MainWindow.xaml.cs:23206-23216`` -- ``MediaList_PreviewKeyDown``
lapie ``Key.Left`` przy ``Keyboard.Modifiers == ModifierKeys.None`` i oddaje go
albo sciezce folderu (``$"{item.Title}: {folderPath}"``), albo
``AnnounceQuickMediaInformation(item)``. Dlatego ``Left`` jest w ``LIST_VIEW``,
a ``Shift/Ctrl/Alt+Left`` NIE sa -- modyfikator wyklucza te galaz w oryginale.
W ODTWARZACZU ``Left`` zostaje przewijaniem 10 s, bez zmian.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Action(Enum):
    SESSION_FILES = "session.files"
    SESSION_RADIO = "session.radio"
    SESSION_PODCASTS = "session.podcasts"
    SESSION_TIDAL = "session.tidal"
    SESSION_WIIM = "session.wiim"
    SESSION_SONOS = "session.sonos"
    SESSION_LIST = "session.list"
    SELECT_SONOS_TARGET = "sonos.target.select"
    ACTIVATE = "activate"
    PARENT_FOLDER = "parent"
    # Escape na liscie nie jest aliasem Backspace. Zamyka podglad lub
    # zagniezdzony widok, ale w drzewie folderow Biblioteki nie przechodzi do
    # katalogu nadrzednego. Ta roznica jest istotna przy obsludze bez wzroku:
    # przypadkowy Escape nie moze przeniesc fokusu do innego poziomu listy.
    CLOSE_LIST_PREVIEW = "view.closePreview"
    SHOW_PLAYER = "view.player"
    SHOW_LIST = "view.list"
    PLAY_PAUSE = "transport.playPause"
    TOGGLE_MUTE = "transport.toggleMute"
    # Zmiana utworu W KOLEJCE. Nastepstwo liczy zywa kolejka hosta, wiec te
    # akcje maja sens tylko wtedy, gdy kolejka naprawde prowadzi odtwarzanie.
    QUEUE_NEXT = "queue.next"
    QUEUE_PREVIOUS = "queue.previous"
    ADD_TO_QUEUE = "action.queue.add"
    TOGGLE_PLAY_NEXT = "action.queue.playNextToggle"
    TOGGLE_FAVORITE = "action.favorite.toggle"
    MANAGE_PLAYLIST_MEMBERSHIP = "action.playlists.membership"
    TIDAL_TOGGLE_LIBRARY = "tidal.library.toggle"
    TIDAL_TOGGLE_FAVORITE = "tidal.favorite.toggle"
    # Prawa strzalka na liscie TIDAL. To polecenie jest kontekstowe: zależnie
    # od wiersza pokazuje przejście do albumu, wykonawcy albo oba kierunki.
    # Osobna akcja jest potrzebna przede wszystkim Pomocy klawiatury -- bez
    # niej działający gest był opisywany jako brak polecenia.
    TIDAL_RELATIONS = "tidal.relations"
    SEEK_BACK_10 = "seek.back10"
    SEEK_FORWARD_10 = "seek.forward10"
    # Shift to 30 s (MainWindow.xaml.cs:21585-21586). Dostarczona wersja
    # wiazala Shift z 60 s -- przez to dwa gesty robily to samo, a para
    # Ctrl+Left/Right nie robila nic.
    SEEK_BACK_30 = "seek.back30"
    SEEK_FORWARD_30 = "seek.forward30"
    SEEK_BACK_60 = "seek.back60"
    SEEK_FORWARD_60 = "seek.forward60"
    # Ctrl+Alt: krok z USTAWIEN uzytkownika (PlaybackSettings.CustomSeekSeconds,
    # domyslnie 300 s, zakres 5..1800 -- AppSettings.cs:280-295).
    SEEK_BACK_CUSTOM = "seek.backCustom"
    SEEK_FORWARD_CUSTOM = "seek.forwardCustom"
    # Skok procentowy: cyfra BEZ modyfikatora w odtwarzaczu
    # (MainWindow.xaml.cs:21555-21557 -> CommandIds.SeekPercent(digit * 10)).
    # Osobne wartosci, bo oryginal ma osobne identyfikatory komend -- jedna
    # akcja z parametrem nie dalaby sie sprawdzic w tablicy skrotow.
    SEEK_PERCENT_0 = "seek.percent.0"
    SEEK_PERCENT_10 = "seek.percent.10"
    SEEK_PERCENT_20 = "seek.percent.20"
    SEEK_PERCENT_30 = "seek.percent.30"
    SEEK_PERCENT_40 = "seek.percent.40"
    SEEK_PERCENT_50 = "seek.percent.50"
    SEEK_PERCENT_60 = "seek.percent.60"
    SEEK_PERCENT_70 = "seek.percent.70"
    SEEK_PERCENT_80 = "seek.percent.80"
    SEEK_PERCENT_90 = "seek.percent.90"
    VOLUME_UP_5 = "volume.up5"
    VOLUME_DOWN_5 = "volume.down5"
    VOLUME_UP_1 = "volume.up1"
    VOLUME_DOWN_1 = "volume.down1"
    RATE_UP = "rate.up"
    RATE_DOWN = "rate.down"
    RATE_RESET = "rate.reset"
    TIME_ELAPSED = "time.elapsed"
    TIME_REMAINING = "time.remaining"
    TIME_TOTAL = "time.total"
    ADD_BOOKMARK = "action.bookmark.add"
    ADD_NAMED_BOOKMARK = "action.bookmark.addNamed"
    PREVIOUS_BOOKMARK = "transport.bookmark.previous"
    NEXT_BOOKMARK = "transport.bookmark.next"
    CLIP_MARK_START = "audio.clip.markStart"
    CLIP_MARK_END = "audio.clip.markEnd"
    CLIP_JUMP_START = "audio.clip.jumpStart"
    CLIP_JUMP_END = "audio.clip.jumpEnd"
    CLIP_PREVIOUS_BOUNDARY = "audio.clip.previousBoundary"
    CLIP_NEXT_BOUNDARY = "audio.clip.nextBoundary"
    CLIP_EXPORT = "audio.clip.export"
    CLIP_APPEND = "audio.clip.appendToFile"
    CLIP_REMOVE = "editing.clip.removeFromOriginal"
    CLIP_CLEAR = "audio.clip.clear"
    #: Home/End w odtwarzaczu. ID WPROST z oryginalu (CommandIds.cs:40-41),
    #: zeby przyszly port komend sieciowych i palety nie wymyslal wlasnych.
    TRACK_START = "transport.trackStart"
    TRACK_END = "transport.trackEnd"
    # CommandIds.SettingsToggleSeekMessages, Ctrl+Shift+G
    # (MainWindow.xaml.cs:21670 i 22188).
    TOGGLE_SEEK_MESSAGES = "settings.toggleSeekMessages"
    GENERAL_SETTINGS = "settings.general"
    SELECT_AUDIO_OUTPUT = "audio.selectOutput"
    PREVIOUS_AUDIO_OUTPUT = "audio.previousOutput"
    NEXT_AUDIO_OUTPUT = "audio.nextOutput"
    PRESET_1 = "preset.1"
    PRESET_2 = "preset.2"
    PRESET_3 = "preset.3"
    PRESET_4 = "preset.4"
    PRESET_5 = "preset.5"
    PRESET_6 = "preset.6"
    PRESET_7 = "preset.7"
    PRESET_8 = "preset.8"
    PRESET_9 = "preset.9"
    PRESET_10 = "preset.10"
    PRESET_11 = "preset.11"
    PRESET_12 = "preset.12"
    VIEW_PRESETS = "presets.view"
    ASSIGN_PRESET = "presets.assign"
    VIEW_WIIM_NETWORK_STREAMS = "wiim.networkStreams.view"
    WIIM_SELECT_INPUT = "wiim.input.select"
    WIIM_SELECT_OUTPUT = "wiim.output.select"
    WIIM_SELECT_EQUALIZER = "wiim.equalizer.select"
    WIIM_SELECT_REPEAT = "wiim.repeat.select"
    WIIM_TOGGLE_SHUFFLE = "wiim.shuffle.toggle"
    WIIM_SET_SLEEP_TIMER = "wiim.sleepTimer.set"
    WIIM_PREVIOUS_SOURCE = "wiim.source.previous"
    WIIM_NEXT_SOURCE = "wiim.source.next"
    ADD_WIIM_NETWORK_STREAM = "wiim.networkStreams.add"
    EDIT_WIIM_NETWORK_STREAM = "wiim.networkStreams.edit"
    REMOVE_WIIM_NETWORK_STREAMS = "wiim.networkStreams.remove"
    IMPORT_WIIM_NETWORK_STREAMS = "wiim.networkStreams.import"
    EXPORT_WIIM_NETWORK_STREAMS = "wiim.networkStreams.export"
    SORT_WIIM_NETWORK_STREAMS_ADDED = "wiim.networkStreams.sort.added"
    SORT_WIIM_NETWORK_STREAMS_ALPHABETICAL = "wiim.networkStreams.sort.alphabetical"
    SORT_WIIM_NETWORK_STREAMS_CUSTOM = "wiim.networkStreams.sort.custom"
    ADD_SONOS_OWN_STREAM = "sonos.ownStreams.add"
    EDIT_SONOS_OWN_STREAM = "sonos.ownStreams.edit"
    REMOVE_SONOS_OWN_STREAMS = "sonos.ownStreams.remove"
    IMPORT_SONOS_OWN_STREAMS = "sonos.ownStreams.import"
    SORT_SONOS_OWN_STREAMS_ADDED = "sonos.ownStreams.sort.added"
    SORT_SONOS_OWN_STREAMS_ALPHABETICAL = "sonos.ownStreams.sort.alphabetical"
    SORT_SONOS_OWN_STREAMS_CUSTOM = "sonos.ownStreams.sort.custom"
    MOVE_SONOS_OWN_STREAM_UP = "sonos.ownStreams.moveUp"
    MOVE_SONOS_OWN_STREAM_DOWN = "sonos.ownStreams.moveDown"
    CUT_SONOS_OWN_STREAMS = "sonos.ownStreams.cut"
    PASTE_SONOS_OWN_STREAMS = "sonos.ownStreams.paste"
    EXPORT_SONOS_OWN_STREAMS = "sonos.ownStreams.export"
    OPEN_FOLDER_DIALOG = "files.openFolder"
    OPEN_FILE_DIALOG = "files.openFile"
    COPY_NAME = "clipboard.copyName"
    COPY_ADDRESS = "clipboard.copyAddress"
    #: Ctrl+X jest kontekstowe jak w głównym AMC: w otwartej playliście
    #: rozpoczyna wewnętrzne przenoszenie, a w pozostałych lokalnych widokach
    #: przygotowuje rzeczywiste pliki do przeniesienia poza AMC.
    CUT_FILE = "clipboard.cutFile"
    PASTE_OR_MOVE = "clipboard.pasteOrMove"
    MOVE_LIST_ITEM_UP = "library.moveItemUp"
    MOVE_LIST_ITEM_DOWN = "library.moveItemDown"
    RENAME_LIBRARY_ITEM = "library.renameItem"
    RENAME_LOCAL_FILE = "library.renameFile"
    REMOVE_SELECTED = "library.removeSelected"
    RECYCLE_SELECTED = "library.recycleSelected"
    STATION_ADD = "radio.add"
    STATION_EDIT = "radio.edit"
    STATION_DELETE = "radio.delete"
    STATION_IMPORT = "radio.import"
    STATION_EXPORT_FAVORITES = "radio.exportFavorites"
    RECORD_TOGGLE = "radio.recording.toggle"
    RECORD_PAUSE = "radio.recording.pause"
    RECORD_SPLIT = "radio.recording.split"
    RECORD_STOP_ALL = "radio.recording.stopAll"
    VIEW_ACTIVE_RECORDINGS = "radio.recording.activeView"
    VIEW_RECORDED_RADIO_FILES = "radio.recording.completedView"
    ADD_RADIO_SCHEDULE = "radio.recording.schedule.add"
    MANAGE_RADIO_SCHEDULES = "radio.recording.schedules"
    VIEW_PODCAST_INBOX = "podcasts.inbox"
    VIEW_PODCAST_DOWNLOADS = "podcasts.downloads"
    SORT_PODCAST_INBOX_ADDED = "podcasts.inbox.sort.added"
    SORT_PODCAST_INBOX_ALPHABETICAL = "podcasts.inbox.sort.alphabetical"
    SORT_PODCAST_INBOX_BY_PODCAST = "podcasts.inbox.sort.byPodcast"
    SORT_TIDAL_COLLECTION_ADDED = "tidal.collection.sort.added"
    SORT_TIDAL_COLLECTION_ALPHABETICAL = "tidal.collection.sort.alphabetical"
    SORT_TIDAL_COLLECTION_CUSTOM = "tidal.collection.sort.custom"
    ADD_PODCAST_SOURCE = "podcasts.source.add"
    IMPORT_PODCAST_OPML = "podcasts.opml.import"
    EXPORT_PODCAST_OPML = "podcasts.opml.export"
    EXPORT_YOUTUBE_SUBSCRIPTIONS = "podcasts.youtube.export"
    REFRESH_PODCAST = "podcasts.refresh.current"
    REFRESH_PODCAST_LIBRARY = "podcasts.refresh.all"
    DOWNLOAD_PODCAST_EPISODES = "podcasts.download.selected"
    SAVE_PODCAST_EPISODE_AS = "podcasts.download.saveAs"
    SHOW_PODCAST_DESCRIPTION = "podcasts.description"
    CURRENT_RADIO_BROADCAST_INFORMATION = "radio.currentBroadcastInformation"
    RECOGNIZE_RADIO_TRACK = "radio.recognition.now"
    TOGGLE_RADIO_RECOGNITION_MONITORING = "radio.recognition.monitor.toggle"
    TOGGLE_RADIO_RECOGNITION_ANNOUNCEMENTS = "radio.recognition.announcements.toggle"
    VIEW_RADIO_RECOGNITION_HISTORY = "radio.recognition.history"
    GO_TO_RELATED_PODCAST = "podcasts.goToRelated"
    TOGGLE_PODCAST_FAVORITE = "podcasts.favorite.toggle"
    TOGGLE_PODCAST_LIBRARY = "podcasts.library.toggle"
    PODCAST_PLAYBACK_OPTIONS = "podcasts.playbackOptions"
    VIEW_ALL_FILES = "library.allFiles"
    VIEW_FAVORITES = "library.favorites"
    VIEW_PLAYLISTS = "library.playlists"
    # Nazwy odpowiadaja komendom C#, ktore te widoki otwieraja:
    #   CommandIds.ViewFolders  (MainWindow.xaml:446, Alt+1)
    #   CommandIds.ViewHistory  (CommandIds.cs:182, MainWindow.xaml:488, Ctrl+H)
    #   CommandIds.ViewQueue    (CommandIds.cs:149, MainWindow.xaml:487, Ctrl+Q)
    VIEW_FOLDERS = "library.folders"
    # ``CommandIds.ViewLibrary`` (CommandIds.cs:81, Ctrl+L z
    # MainWindow.xaml:427-428 i cs:22173). NIE jest tozsame z VIEW_FOLDERS:
    # CommandRouter.cs:390 woła ShowView("Biblioteka"), a cs:701-705 podmienia
    # te nazwe na ZAPAMIETANY widok profilu -- Foldery albo Wszystkie pliki.
    VIEW_LIBRARY = "view.library"
    VIEW_HISTORY = "view.history"
    VIEW_SAVED_QUEUE = "view.queue"
    # UWAGA: to NIE jest CommandIds.ViewBookmarks. Tamta komenda (Ctrl+B)
    # pokazuje WSZYSTKIE zakladki (BookmarkIndex.GetForDisplay,
    # BookmarkIndex.cs:19-28). Tutaj mamy port GetForItem (cs:30-36), czyli
    # zakladki JEDNEGO zaznaczonego elementu -- zakres wezszy, wiec wlasny
    # identyfikator i wlasny gest, zeby nie obiecywac cudzego zbioru.
    VIEW_ITEM_BOOKMARKS = "library.itemBookmarks"
    # To JUZ jest port CommandIds.ViewBookmarks (BookmarkIndex.GetForDisplay,
    # BookmarkIndex.cs:19-28): WSZYSTKIE zakladki profilu, wszystkich sesji.
    # Osobna akcja od VIEW_ITEM_BOOKMARKS, bo zakres jest inny -- jedna akcja
    # z przelacznikiem kazalaby zgadywac, ktory zbior widzi uzytkownik.
    VIEW_ALL_BOOKMARKS = "library.allBookmarks"
    # Port ``Filter_Click`` -> ``ShowFilter``/``FocusFilter``
    # (MainWindow.xaml:491 "_Filtruj listę" Ctrl+K; MainWindow.xaml.cs:25455
    # i :22210). NIE jest to ``CommandIds.SearchCurrent``/``SearchAll``
    # (Ctrl+F / Ctrl+Shift+F, MainWindow.xaml:501-502): tamte otwieraja osobne
    # okno wynikow, a tu zwezamy liste, ktora juz jest na ekranie.
    FOCUS_FILTER = "list.filter"
    SEARCH_CURRENT = "view.search.current"
    SEARCH_ALL = "view.search.all"
    # LEWA STRZALKA NA LISCIE: krotka informacja uzupelniajaca o ZAZNACZONYM
    # wierszu (bitrate, czestotliwosc, rozmiar, czas...). Gest ODCZYTANY, nie
    # wymyslony: ``MainWindow.xaml.cs:23206-23216`` w
    # ``MediaList_PreviewKeyDown`` lapie ``Key.Left`` bez modyfikatora i
    # oddaje go albo sciezce folderu, albo
    # ``AnnounceQuickMediaInformation(item)``.
    #
    # To NIE koliduje z natywna nawigacja listy: ``wx.ListCtrl`` w trybie
    # raportu uzywa strzalek PIONOWYCH do zmiany wiersza, a pozioma strzalka w
    # lewo nie ma w nim wlasnego znaczenia (tak samo jak w ``ListView`` WPF,
    # ktory oryginal przechwytuje). Gesty czytnika ekranu zostaja nietkniete --
    # NVDA czyta kolumny swoim modyfikatorem, nie sama strzalka.
    QUICK_INFORMATION = "list.quickInformation"
    #: Opcje sesji (Ctrl+Alt+Enter). Port ``SessionPlaybackOptionsEditor``.
    #:
    #: Jedno WSPOLNE wejscie dla obu sesji -- dialog sam pokazuje tylko te
    #: opcje, ktore dana sesja umie wykonac (``session_options``). Oryginal nie
    #: ma tego gestu w oknie (otwiera opcje z menu sesji), wiec klawisz jest
    #: WLASNY dla portu: Ctrl+Alt+Enter nie koliduje ani z aktywacja (gole
    #: Enter), ani z para Ctrl+Alt+Left/Right (przewijanie wlasnym krokiem).
    SESSION_OPTIONS = "session.options"
    HELP = "help"
    KEYBOARD_HELP = "keyboard.help"


# TIDAL ma osobny tor: katalog czyta oficjalne API, a dzwiek odtwarza oryginalna
# aplikacja TIDAL. Jawna lista obslugiwanych polecen jest celowo restrykcyjna:
# nowy skrot nie moze przypadkiem trafic do lokalnego silnika AMC.
TIDAL_SUPPORTED_ACTIONS = frozenset({
    Action.SESSION_FILES,
    Action.SESSION_RADIO,
    Action.SESSION_PODCASTS,
    Action.SESSION_TIDAL,
    Action.SESSION_WIIM,
    Action.SESSION_SONOS,
    Action.SESSION_LIST,
    Action.ACTIVATE,
    Action.PARENT_FOLDER,
    Action.CLOSE_LIST_PREVIEW,
    Action.SHOW_LIST,
    Action.PLAY_PAUSE,
    Action.QUEUE_NEXT,
    Action.QUEUE_PREVIOUS,
    Action.ADD_TO_QUEUE,
    Action.TOGGLE_FAVORITE,
    Action.TIDAL_TOGGLE_LIBRARY,
    Action.TIDAL_TOGGLE_FAVORITE,
    Action.TIDAL_RELATIONS,
    Action.SORT_TIDAL_COLLECTION_ADDED,
    Action.SORT_TIDAL_COLLECTION_ALPHABETICAL,
    Action.SORT_TIDAL_COLLECTION_CUSTOM,
    Action.TIME_ELAPSED,
    Action.TIME_REMAINING,
    Action.TIME_TOTAL,
    Action.SESSION_OPTIONS,
    Action.VIEW_PRESETS,
    Action.GENERAL_SETTINGS,
    Action.TOGGLE_SEEK_MESSAGES,
    Action.ASSIGN_PRESET,
    Action.PRESET_1,
    Action.PRESET_2,
    Action.PRESET_3,
    Action.PRESET_4,
    Action.PRESET_5,
    Action.PRESET_6,
    Action.PRESET_7,
    Action.PRESET_8,
    Action.PRESET_9,
    Action.PRESET_10,
    Action.PRESET_11,
    Action.PRESET_12,
    Action.QUICK_INFORMATION,
    Action.COPY_NAME,
    Action.COPY_ADDRESS,
    Action.FOCUS_FILTER,
    Action.SEARCH_CURRENT,
    Action.SEARCH_ALL,
    Action.VIEW_LIBRARY,
    Action.VIEW_FAVORITES,
    Action.VIEW_PLAYLISTS,
    Action.VIEW_SAVED_QUEUE,
    Action.VIEW_ACTIVE_RECORDINGS,
    Action.VIEW_RECORDED_RADIO_FILES,
    Action.MANAGE_RADIO_SCHEDULES,
    Action.VIEW_PODCAST_INBOX,
    Action.HELP,
    Action.KEYBOARD_HELP,
})


# WiiM jest autonomicznym odtwarzaczem sieciowym. Dopoki polecenie nie ma
# jawnej drogi ``wiim.*`` w hoscie, nie moze trafic do lokalnego silnika audio.
WIIM_SUPPORTED_ACTIONS = frozenset({
    Action.SESSION_FILES,
    Action.SESSION_RADIO,
    Action.SESSION_PODCASTS,
    Action.SESSION_TIDAL,
    Action.SESSION_WIIM,
    Action.SESSION_SONOS,
    Action.SESSION_LIST,
    Action.ACTIVATE,
    Action.PARENT_FOLDER,
    Action.CLOSE_LIST_PREVIEW,
    Action.SHOW_PLAYER,
    Action.SHOW_LIST,
    Action.PLAY_PAUSE,
    Action.QUEUE_NEXT,
    Action.QUEUE_PREVIOUS,
    Action.VOLUME_UP_5,
    Action.VOLUME_DOWN_5,
    Action.VOLUME_UP_1,
    Action.VOLUME_DOWN_1,
    Action.TIME_ELAPSED,
    Action.TIME_REMAINING,
    Action.TIME_TOTAL,
    Action.VIEW_PRESETS,
    Action.ASSIGN_PRESET,
    *(Action[f"PRESET_{slot}"] for slot in range(1, 13)),
    Action.VIEW_WIIM_NETWORK_STREAMS,
    Action.WIIM_SELECT_INPUT,
    Action.WIIM_SELECT_OUTPUT,
    Action.WIIM_SELECT_EQUALIZER,
    Action.WIIM_SELECT_REPEAT,
    Action.WIIM_TOGGLE_SHUFFLE,
    Action.WIIM_SET_SLEEP_TIMER,
    Action.WIIM_PREVIOUS_SOURCE,
    Action.WIIM_NEXT_SOURCE,
    Action.ADD_WIIM_NETWORK_STREAM,
    Action.EDIT_WIIM_NETWORK_STREAM,
    Action.REMOVE_WIIM_NETWORK_STREAMS,
    Action.IMPORT_WIIM_NETWORK_STREAMS,
    Action.EXPORT_WIIM_NETWORK_STREAMS,
    Action.SORT_WIIM_NETWORK_STREAMS_ADDED,
    Action.SORT_WIIM_NETWORK_STREAMS_ALPHABETICAL,
    Action.SORT_WIIM_NETWORK_STREAMS_CUSTOM,
    Action.GENERAL_SETTINGS,
    Action.TOGGLE_SEEK_MESSAGES,
    Action.QUICK_INFORMATION,
    Action.COPY_NAME,
    Action.FOCUS_FILTER,
    Action.VIEW_ACTIVE_RECORDINGS,
    Action.VIEW_RECORDED_RADIO_FILES,
    Action.MANAGE_RADIO_SCHEDULES,
    Action.VIEW_PODCAST_INBOX,
    Action.HELP,
    Action.KEYBOARD_HELP,
})


# Sonos jest autonomicznym odtwarzaczem sieciowym. Polecenia spoza tej listy
# nie mogą przypadkiem trafić do lokalnego silnika plików.
SONOS_SUPPORTED_ACTIONS = frozenset({
    Action.SESSION_FILES,
    Action.SESSION_RADIO,
    Action.SESSION_PODCASTS,
    Action.SESSION_TIDAL,
    Action.SESSION_WIIM,
    Action.SESSION_SONOS,
    Action.SESSION_LIST,
    Action.SELECT_SONOS_TARGET,
    Action.ACTIVATE,
    Action.PARENT_FOLDER,
    Action.CLOSE_LIST_PREVIEW,
    Action.SHOW_PLAYER,
    Action.SHOW_LIST,
    Action.PLAY_PAUSE,
    Action.QUEUE_NEXT,
    Action.QUEUE_PREVIOUS,
    Action.SEEK_BACK_10,
    Action.SEEK_FORWARD_10,
    Action.SEEK_BACK_30,
    Action.SEEK_FORWARD_30,
    Action.SEEK_BACK_60,
    Action.SEEK_FORWARD_60,
    Action.SEEK_BACK_CUSTOM,
    Action.SEEK_FORWARD_CUSTOM,
    Action.SEEK_PERCENT_0,
    Action.SEEK_PERCENT_10,
    Action.SEEK_PERCENT_20,
    Action.SEEK_PERCENT_30,
    Action.SEEK_PERCENT_40,
    Action.SEEK_PERCENT_50,
    Action.SEEK_PERCENT_60,
    Action.SEEK_PERCENT_70,
    Action.SEEK_PERCENT_80,
    Action.SEEK_PERCENT_90,
    Action.VOLUME_UP_5,
    Action.VOLUME_DOWN_5,
    Action.VOLUME_UP_1,
    Action.VOLUME_DOWN_1,
    Action.TIME_ELAPSED,
    Action.TIME_REMAINING,
    Action.TIME_TOTAL,
    Action.VIEW_PRESETS,
    Action.ASSIGN_PRESET,
    Action.PRESET_1,
    Action.PRESET_2,
    Action.PRESET_3,
    Action.PRESET_4,
    Action.PRESET_5,
    Action.PRESET_6,
    Action.PRESET_7,
    Action.PRESET_8,
    Action.PRESET_9,
    Action.PRESET_10,
    Action.PRESET_11,
    Action.PRESET_12,
    Action.GENERAL_SETTINGS,
    Action.TOGGLE_SEEK_MESSAGES,
    Action.QUICK_INFORMATION,
    Action.COPY_NAME,
    Action.VIEW_LIBRARY,
    Action.VIEW_FAVORITES,
    Action.VIEW_PLAYLISTS,
    Action.ADD_SONOS_OWN_STREAM,
    Action.EDIT_SONOS_OWN_STREAM,
    Action.REMOVE_SONOS_OWN_STREAMS,
    Action.IMPORT_SONOS_OWN_STREAMS,
    Action.SORT_SONOS_OWN_STREAMS_ADDED,
    Action.SORT_SONOS_OWN_STREAMS_ALPHABETICAL,
    Action.SORT_SONOS_OWN_STREAMS_CUSTOM,
    Action.MOVE_SONOS_OWN_STREAM_UP,
    Action.MOVE_SONOS_OWN_STREAM_DOWN,
    Action.CUT_SONOS_OWN_STREAMS,
    Action.PASTE_SONOS_OWN_STREAMS,
    Action.EXPORT_SONOS_OWN_STREAMS,
    Action.FOCUS_FILTER,
    Action.VIEW_ACTIVE_RECORDINGS,
    Action.VIEW_RECORDED_RADIO_FILES,
    Action.MANAGE_RADIO_SCHEDULES,
    Action.VIEW_PODCAST_INBOX,
    Action.HELP,
    Action.KEYBOARD_HELP,
})


@dataclass(frozen=True, slots=True)
class Chord:
    """Klawisz + modyfikatory. Nazwy klawiszy wlasne, zeby nie wiazac sie z wx."""

    key: str
    ctrl: bool = False
    shift: bool = False
    alt: bool = False

    @property
    def canonical(self) -> str:
        parts = []
        if self.ctrl:
            parts.append("Ctrl")
        if self.alt:
            parts.append("Alt")
        if self.shift:
            parts.append("Shift")
        parts.append(self.key)
        return "+".join(parts)


# Skroty dzialajace W WIDOKU LISTY. Strzalki NIE sa tu wpisane - naleza do
# natywnego ListCtrl, zeby czytnik ekranu i Narrator dzialaly bez dodatku.
LIST_VIEW: dict[str, Action] = {
    "Ctrl+0": Action.SESSION_LIST,
    "Ctrl+1": Action.SESSION_FILES,
    "Ctrl+2": Action.SESSION_RADIO,
    "Ctrl+3": Action.SESSION_PODCASTS,
    "Ctrl+4": Action.SESSION_TIDAL,
    "Ctrl+5": Action.SESSION_WIIM,
    "Ctrl+6": Action.SESSION_SONOS,
    "Return": Action.ACTIVATE,
    "Back": Action.PARENT_FOLDER,
    # Kontekstowe polecenia edycji z głównego AMC. F2 zmienia nazwę
    # widoczną w Bibliotece (albo nazwę/adres stacji, albo nazwę źródła
    # podcastów), Shift+F2 zmienia prawdziwą nazwę pliku. Delete nie dotyka
    # pliku; Shift+Delete po potwierdzeniu wysyła plik do systemowego Kosza.
    "F2": Action.RENAME_LIBRARY_ITEM,
    "Shift+F2": Action.RENAME_LOCAL_FILE,
    "Delete": Action.REMOVE_SELECTED,
    "Shift+Delete": Action.RECYCLE_SELECTED,
    # Escape i Backspace maja rozne role. Escape czysci filtr albo zamyka
    # rzeczywisty podglad/podwidok; nie przechodzi po drzewie folderow.
    # Backspace powyzej pozostaje jedynym gestem "folder nadrzedny".
    "Escape": Action.CLOSE_LIST_PREVIEW,
    "F6": Action.SHOW_PLAYER,
    # Shift+F6 na LISCIE tez idzie do odtwarzacza: warunek oryginalu to
    # ``_playerViewActive && Shift`` (MainWindow.xaml.cs:20780), a na liscie
    # pierwszy czlon jest falszem, wiec wykonuje sie galaz ShowPlayerView.
    "Shift+F6": Action.SHOW_PLAYER,
    "Space": Action.PLAY_PAUSE,
    "Ctrl+M": Action.TOGGLE_MUTE,
    # Czas: Ctrl+SHIFT+E/R/T (MainWindow.xaml.cs:21674-21676, 22190-22192).
    # Samo Ctrl+E/R/T nalezy do profilu PO PREFIKSIE, a w oknie Ctrl+E to
    # eksport ulubionych stacji (cs:21662) -- stad brak aliasow.
    "Ctrl+Shift+E": Action.TIME_ELAPSED,
    "Ctrl+Shift+R": Action.TIME_REMAINING,
    "Ctrl+Shift+T": Action.TIME_TOTAL,
    # Przelacznik automatycznych komunikatow odtwarzacza (cs:21670, 22188).
    "Ctrl+Shift+G": Action.TOGGLE_SEEK_MESSAGES,
    # MainWindow.xaml:42-45  OpenLocalFilesMenuItem   Ctrl+O        -> PLIKI
    # MainWindow.xaml:46-49  OpenLocalFolderMenuItem  Ctrl+Shift+O  -> FOLDER
    # Port mial te dwie pozycje odwrotnie, przez co Ctrl+O otwieralo dialog
    # folderu. Kolejnosc jest ustalona przez oryginal, nie przez wygode.
    "Ctrl+O": Action.OPEN_FILE_DIALOG,
    "Ctrl+Shift+O": Action.OPEN_FOLDER_DIALOG,
    # Adres NA ZADANIE, tak jak w pelnym AMC (MainWindow.xaml.cs:20717-20732).
    # Dzieki temu lista moze czytac samo nazwe, a pelny adres nadal jest
    # dostepny jednym skrotem -- nie zabieramy funkcji, przenosimy ja.
    "Ctrl+C": Action.COPY_NAME,
    "Ctrl+Shift+C": Action.COPY_ADDRESS,
    # Ctrl+X/Ctrl+V najpierw próbują wewnętrznego przenoszenia w otwartej
    # playliście; poza nią Ctrl+X zachowuje dotychczasowe wycięcie pliku.
    "Ctrl+X": Action.CUT_FILE,
    "Ctrl+V": Action.PASTE_OR_MOVE,
    "Alt+Up": Action.MOVE_LIST_ITEM_UP,
    "Alt+Down": Action.MOVE_LIST_ITEM_DOWN,
    # Nazwane widoki Biblioteki. Skroty WPROST ze wzorca, nie wymyslone:
    #   MainWindow.xaml:458  "_Wszystkie pliki alfabetycznie"  Alt+2
    #   MainWindow.xaml:426  "_Ulubione"                       Ctrl+U
    #   MainWindow.xaml:427  "_Playlisty"                      Ctrl+P
    # Zadny z nich nie koliduje z Ctrl+1/Ctrl+2 (sesje) ani z Ctrl+O.
    "Alt+2": Action.VIEW_ALL_FILES,
    "Ctrl+U": Action.VIEW_FAVORITES,
    "Ctrl+P": Action.VIEW_PLAYLISTS,
    # Widoki aktywnosci. Skroty ODCZYTANE z kodu, nie zgadniete:
    #   MainWindow.xaml:446  "Foldery _Biblioteki"     Alt+1
    #   MainWindow.xaml:487  "_Kolejka"                Ctrl+Q
    #   MainWindow.xaml:488  "_Historia odtwarzania"   Ctrl+H
    # (te same pary w KeyboardProfile.cs:84 i :90 oraz w sciezce klawiszy
    # MainWindow.xaml.cs:21674-21675.)
    "Alt+1": Action.VIEW_FOLDERS,
    # MainWindow.xaml:427-428 i MainWindow.xaml.cs:22173 -- powrot do
    # Biblioteki z KAZDEGO nazwanego widoku (Ulubione, Historia, ...).
    "Ctrl+L": Action.VIEW_LIBRARY,
    "Ctrl+Q": Action.VIEW_SAVED_QUEUE,
    # Jednoznaczny zestaw bez dawnego duplikatu Shift+Enter:
    # Ctrl+Shift+Q zmienia zwykla kolejke, Ctrl+Shift+Enter ustawia blok
    # „odtworz nastepne”. Sam Shift+Enter zostaje wolny na przyszla funkcje.
    "Ctrl+Shift+Q": Action.ADD_TO_QUEUE,
    "Ctrl+Shift+Return": Action.TOGGLE_PLAY_NEXT,
    "Ctrl+Shift+U": Action.TOGGLE_FAVORITE,
    "Ctrl+Shift+P": Action.MANAGE_PLAYLIST_MEMBERSHIP,
    "Ctrl+H": Action.VIEW_HISTORY,
    # Ctrl+B to ViewBookmarks oryginalu (MainWindow.xaml:489): WSZYSTKIE
    # zakladki. Teraz mamy ten zbior naprawde (GetForDisplay), wiec skrot
    # dostaje swoje wlasne znaczenie, a wezszy widok zakladek ZAZNACZONEGO
    # pliku zostaje pod Ctrl+Shift+B. Dwa zakresy, dwa gesty -- zaden nie
    # podmienia drugiemu zbioru pod reka.
    "Ctrl+B": Action.VIEW_ALL_BOOKMARKS,
    "Ctrl+Shift+B": Action.VIEW_ITEM_BOOKMARKS,
    # Filtr listy. Gest ODCZYTANY, nie zgadniety: MainWindow.xaml:491
    # ``<MenuItem Header="_Filtruj listę" InputGestureText="Ctrl+K" ...>``.
    # Osobne okno wyszukiwania, nie filtr bieżącej listy. Gesty wprost z
    # MainWindow.xaml:501-502 i obu tablic skrótów MainWindow.xaml.cs.
    "Ctrl+K": Action.FOCUS_FILTER,
    "Ctrl+F": Action.SEARCH_CURRENT,
    "Ctrl+Shift+F": Action.SEARCH_ALL,
    # LEWA STRZALKA bez modyfikatora. Jedyny wpis ze strzalka w tablicy listy:
    # oryginal wymaga ``Keyboard.Modifiers == ModifierKeys.None``
    # (cs:23206), wiec Shift/Ctrl/Alt+Left NIE sa tu wpisane i zostaja
    # kontrolce. Strzalki PIONOWE nadal naleza wylacznie do listy.
    "Left": Action.QUICK_INFORMATION,
    # Opcje sesji: TEN SAM gest co w odtwarzaczu, bo zakres (sesja) jest ten
    # sam niezaleznie od widoku.
    "Ctrl+Alt+Return": Action.SESSION_OPTIONS,
    # Ustawienia ogolne: gest z pelnego AMC (MainWindow.xaml:162 oraz
    # MainWindow.xaml.cs:21126). Przecinek jest zwyklym kodem ASCII, wiec
    # ``chord_from_event`` sklada z niego dokladnie "Ctrl+,".
    "Ctrl+,": Action.GENERAL_SETTINGS,
    # Pelne AMC: Shift+A wybiera wyjscie audio osobno dla biezacej sesji.
    "Shift+A": Action.SELECT_AUDIO_OUTPUT,
    # Szybka zmiana podczas odtwarzania, bez otwierania dialogu. Nawiasy sa
    # para kierunkowa i nie koliduja z istniejacymi skrótami transportu.
    "Ctrl+[": Action.PREVIOUS_AUDIO_OUTPUT,
    "Ctrl+]": Action.NEXT_AUDIO_OUTPUT,
    # Zarzadzanie presetami z pelnego AMC (MainWindow.xaml:428-435).
    "Ctrl+Alt+P": Action.VIEW_PRESETS,
    "Ctrl+Alt+Shift+P": Action.ASSIGN_PRESET,
    "F1": Action.HELP,
    "Ctrl+F1": Action.KEYBOARD_HELP,
}

PRESET_ACTIONS: dict[int, Action] = {
    slot: Action[f"PRESET_{slot}"] for slot in range(1, 13)
}
PRESET_SHORTCUTS: dict[str, int] = {
    **{f"Ctrl+Shift+{slot}": slot for slot in range(1, 10)},
    "Ctrl+Shift+0": 10,
    "Ctrl+Shift+-": 11,
    "Ctrl+Shift+=": 12,
    "Ctrl+Shift++": 12,
}


def preset_slot(action: Action) -> int | None:
    return next((slot for slot, candidate in PRESET_ACTIONS.items() if candidate is action), None)


for _chord, _slot in PRESET_SHORTCUTS.items():
    LIST_VIEW[_chord] = PRESET_ACTIONS[_slot]

# Dodatkowo w sesji radiowej: zarzadzanie wlasna lista stacji.
RADIO_LIST_VIEW: dict[str, Action] = {
    "Ctrl+N": Action.STATION_ADD,
    "F2": Action.STATION_EDIT,
    "Delete": Action.STATION_DELETE,
    # W pelnym AMC import jest kontekstowym Ctrl+O w sesji Radia. Ctrl+I
    # nalezy globalnie do widoku nowych odcinkow i materialow.
    "Ctrl+O": Action.STATION_IMPORT,
    "Ctrl+E": Action.STATION_EXPORT_FAVORITES,
    # Skroty nagrywania z pelnego AMC (MainWindow.xaml.cs:21396-21446).
    # Ctrl+R dziala na liscie i w odtwarzaczu; Shift+Spacja steruje pauza.
    "Ctrl+R": Action.RECORD_TOGGLE,
    "Shift+Space": Action.RECORD_PAUSE,
    "Shift+R": Action.ADD_RADIO_SCHEDULE,
    "Alt+D": Action.CURRENT_RADIO_BROADCAST_INFORMATION,
    "Ctrl+Alt+S": Action.VIEW_RADIO_RECOGNITION_HISTORY,
    "Ctrl+Alt+Shift+S": Action.TOGGLE_RADIO_RECOGNITION_ANNOUNCEMENTS,
}

# Litery bez modyfikatora sa bezpieczne tylko w odtwarzaczu Radia. Na liscie
# T i R musza pozostac natywnej kontroli (wyszukiwanie przyrostowe).
RADIO_PLAYER_VIEW: dict[str, Action] = {
    "Ctrl+O": Action.STATION_IMPORT,
    "Ctrl+E": Action.STATION_EXPORT_FAVORITES,
    "R": Action.RECORD_TOGGLE,
    "Ctrl+R": Action.RECORD_TOGGLE,
    "Shift+Space": Action.RECORD_PAUSE,
    "Shift+R": Action.ADD_RADIO_SCHEDULE,
    "T": Action.RECORD_SPLIT,
    "B": Action.ADD_BOOKMARK,
    "Shift+B": Action.ADD_NAMED_BOOKMARK,
    "Alt+D": Action.CURRENT_RADIO_BROADCAST_INFORMATION,
    "S": Action.RECOGNIZE_RADIO_TRACK,
    "Shift+S": Action.TOGGLE_RADIO_RECOGNITION_MONITORING,
    "Ctrl+Alt+S": Action.VIEW_RADIO_RECOGNITION_HISTORY,
    "Ctrl+Alt+Shift+S": Action.TOGGLE_RADIO_RECOGNITION_ANNOUNCEMENTS,
}

# Skroty W WIDOKU ODTWARZACZA. Tu strzalki sa wolne, wiec przejmuja role
# z profilu globalnego AMC (przewijanie i glosnosc).
PLAYER_VIEW: dict[str, Action] = {
    "Ctrl+0": Action.SESSION_LIST,
    "Ctrl+1": Action.SESSION_FILES,
    "Ctrl+2": Action.SESSION_RADIO,
    "Ctrl+3": Action.SESSION_PODCASTS,
    "Ctrl+4": Action.SESSION_TIDAL,
    "Ctrl+5": Action.SESSION_WIIM,
    "Ctrl+6": Action.SESSION_SONOS,
    "Escape": Action.SHOW_LIST,
    "Shift+F6": Action.SHOW_LIST,
    "F6": Action.SHOW_LIST,
    "Space": Action.PLAY_PAUSE,
    "Ctrl+M": Action.TOGGLE_MUTE,
    # Skróty istnieją także w tablicy odtwarzacza pełnego AMC, lecz sama
    # komenda odpowiada wtedy jasno: wyszukiwanie jest dostępne na listach.
    "Ctrl+F": Action.SEARCH_CURRENT,
    "Ctrl+Shift+F": Action.SEARCH_ALL,
    # Pelne AMC: gola litera B w otwartym odtwarzaczu dodaje szybka zakladke.
    # Ctrl+B pozostaje zbiorcza lista zakladek i nie jest aliasem tej akcji.
    "B": Action.ADD_BOOKMARK,
    # Na LISCIE Ctrl+Shift+B pozostaje widokiem zakladek zaznaczonego pliku.
    # W ODTWARZACZU ten sam gest ma znaczenie z glownego AMC: dialog nazwy.
    "Ctrl+Shift+B": Action.ADD_NAMED_BOOKMARK,
    # Nawigacja po zakładkach bieżącego materiału. Gesty wprost z głównego
    # AMC (MainWindow.xaml.cs:21646-21647 i 22457-22458). Nie mylić z
    # Alt+Page Up/Down, które poruszają granicami zaznaczonego fragmentu.
    "Shift+Prior": Action.PREVIOUS_BOOKMARK,
    "Shift+Next": Action.NEXT_BOOKMARK,
    "Ctrl+B": Action.VIEW_ALL_BOOKMARKS,
    # Zaznaczenie fragmentu i jego plikowe operacje. Gesty wprost z obu
    # sciezek klawiatury pelnego AMC (MainWindow.xaml.cs:21619-21627 oraz
    # 22430-22438). Ctrl+X jest tutaj inna akcja niz wyciecie pliku na liscie:
    # dziala tylko w odtwarzaczu i prowadzi przez potwierdzenie, wspolny edytor
    # C#, kopie bezpieczenstwa i weryfikacje zapisanego wyniku.
    "I": Action.CLIP_MARK_START,
    "O": Action.CLIP_MARK_END,
    "Shift+I": Action.CLIP_JUMP_START,
    "Shift+O": Action.CLIP_JUMP_END,
    "Alt+Prior": Action.CLIP_PREVIOUS_BOUNDARY,
    "Alt+Next": Action.CLIP_NEXT_BOUNDARY,
    "Ctrl+S": Action.CLIP_EXPORT,
    "Ctrl+D": Action.CLIP_APPEND,
    "Ctrl+X": Action.CLIP_REMOVE,
    "Shift+X": Action.CLIP_CLEAR,
    # Poprzedni/nastepny utwor kolejki. Gesty z oryginalu (MainWindow.xaml:714
    # i :717 -- menu odtwarzacza, te same akceleratory na przyciskach :995-1000).
    "Prior": Action.QUEUE_PREVIOUS,
    "Next": Action.QUEUE_NEXT,
    "Ctrl+Shift+Q": Action.ADD_TO_QUEUE,
    "Ctrl+Shift+Return": Action.TOGGLE_PLAY_NEXT,
    "Ctrl+Shift+U": Action.TOGGLE_FAVORITE,
    "Ctrl+Shift+P": Action.MANAGE_PLAYLIST_MEMBERSHIP,
    "Left": Action.SEEK_BACK_10,
    "Right": Action.SEEK_FORWARD_10,
    # Cztery pary krokow z oryginalu (MainWindow.xaml.cs:21583-21590,
    # 22387-22394). Shift = 30 s, Ctrl = 60 s, Ctrl+Alt = czas z ustawien.
    "Shift+Left": Action.SEEK_BACK_30,
    "Shift+Right": Action.SEEK_FORWARD_30,
    "Ctrl+Left": Action.SEEK_BACK_60,
    "Ctrl+Right": Action.SEEK_FORWARD_60,
    "Ctrl+Alt+Left": Action.SEEK_BACK_CUSTOM,
    "Ctrl+Alt+Right": Action.SEEK_FORWARD_CUSTOM,
    "Up": Action.VOLUME_UP_5,
    "Down": Action.VOLUME_DOWN_5,
    "Shift+Up": Action.VOLUME_UP_1,
    "Shift+Down": Action.VOLUME_DOWN_1,
    # Predkosc pod klawiszami ORYGINALU (cs:21595-21597, 22395-22397).
    # Ctrl+Up/Down zostaly usuniete, bo oryginal ich nie ma. Ctrl+0 jest
    # lista sesji i znajduje sie wyzej razem z Ctrl+1..6 (cs:21454-21456).
    "Shift+,": Action.RATE_DOWN,
    "Shift+.": Action.RATE_UP,
    "Ctrl+.": Action.RATE_RESET,
    # Skok procentowy: cyfra bez modyfikatora (cs:21555-21557, 22348-22350).
    # W odtwarzaczu cyfry sa wolne; na liscie naleza do kontrolki, wiec tam ich
    # nie ma.
    "0": Action.SEEK_PERCENT_0,
    "1": Action.SEEK_PERCENT_10,
    "2": Action.SEEK_PERCENT_20,
    "3": Action.SEEK_PERCENT_30,
    "4": Action.SEEK_PERCENT_40,
    "5": Action.SEEK_PERCENT_50,
    "6": Action.SEEK_PERCENT_60,
    "7": Action.SEEK_PERCENT_70,
    "8": Action.SEEK_PERCENT_80,
    "9": Action.SEEK_PERCENT_90,
    "Ctrl+Shift+E": Action.TIME_ELAPSED,
    "Ctrl+Shift+R": Action.TIME_REMAINING,
    "Ctrl+Shift+T": Action.TIME_TOTAL,
    "Ctrl+Shift+G": Action.TOGGLE_SEEK_MESSAGES,
    # Home/End TYLKO w odtwarzaczu (MainWindow.xaml.cs:21598-21599 i
    # 22398-22399, oba warunkiem ``ModifierKeys.None``). Na liscie te klawisze
    # naleza do kontrolki. Ctrl/Shift/Alt nie odpowiadaja modyfikatorowi NVDA:
    # brak kolizji Insert/CapsLock+End wymaga osobnego odbioru z czytnikiem.
    "Home": Action.TRACK_START,
    "End": Action.TRACK_END,
    # Opcje sesji dzialaja takze z odtwarzacza: zakres to SESJA, nie widok.
    "Ctrl+Alt+Return": Action.SESSION_OPTIONS,
    "Ctrl+,": Action.GENERAL_SETTINGS,
    "Shift+A": Action.SELECT_AUDIO_OUTPUT,
    "Ctrl+[": Action.PREVIOUS_AUDIO_OUTPUT,
    "Ctrl+]": Action.NEXT_AUDIO_OUTPUT,
    "Ctrl+Alt+P": Action.VIEW_PRESETS,
    "Ctrl+Alt+Shift+P": Action.ASSIGN_PRESET,
    "F1": Action.HELP,
    "Ctrl+F1": Action.KEYBOARD_HELP,
    # Globalne zatrzymanie dziala niezaleznie od aktualnej sesji, jak w WPF.
    "Ctrl+Alt+Shift+R": Action.RECORD_STOP_ALL,
}

for _chord, _slot in PRESET_SHORTCUTS.items():
    PLAYER_VIEW[_chord] = PRESET_ACTIONS[_slot]

# To samo globalne polecenie z widoku listy.
LIST_VIEW["Ctrl+Alt+Shift+R"] = Action.RECORD_STOP_ALL
# Wspolne podglady pelnego AMC: dzialaja z listy i odtwarzacza niezaleznie od
# sesji, a Escape wraca do zapamietanego miejsca.
for _table in (LIST_VIEW, PLAYER_VIEW):
    _table["Alt+R"] = Action.VIEW_ACTIVE_RECORDINGS
    _table["Alt+Shift+R"] = Action.VIEW_RECORDED_RADIO_FILES
    _table["Ctrl+Shift+H"] = Action.MANAGE_RADIO_SCHEDULES
    _table["Ctrl+I"] = Action.VIEW_PODCAST_INBOX


PODCAST_INBOX_LIST_VIEW: dict[str, Action] = {
    "Alt+1": Action.SORT_PODCAST_INBOX_ADDED,
    "Alt+2": Action.SORT_PODCAST_INBOX_ALPHABETICAL,
    "Alt+3": Action.SORT_PODCAST_INBOX_BY_PODCAST,
    "F5": Action.REFRESH_PODCAST_LIBRARY,
}

# Kontekst sesji, niezaleznie od listy/odtwarzacza. F5 w skrzynce jest
# przesloniete powyzej, dokladnie jak w glownym AMC.
PODCAST_SESSION_VIEW: dict[str, Action] = {
    # Ctrl+U jest widokiem bieżącej sesji także z odtwarzacza. W Podcastach
    # obejmuje ulubione kanały i odcinki, a nie Bibliotekę plików lokalnych.
    "Ctrl+U": Action.VIEW_FAVORITES,
    "Ctrl+H": Action.VIEW_HISTORY,
    "Ctrl+N": Action.ADD_PODCAST_SOURCE,
    "Ctrl+O": Action.IMPORT_PODCAST_OPML,
    "F5": Action.REFRESH_PODCAST,
    "Ctrl+F5": Action.REFRESH_PODCAST_LIBRARY,
    # Jak w głównym AMC: na liście pobiera całe zaznaczenie, a w
    # odtwarzaczu bieżący odcinek. Ma pierwszeństwo przed plikowym dopisywaniem
    # fragmentu, które pod Ctrl+D pozostaje w sesji Plików lokalnych.
    "Ctrl+D": Action.DOWNLOAD_PODCAST_EPISODES,
    "Ctrl+S": Action.SAVE_PODCAST_EPISODE_AS,
    # Pełny AMC udostępnia pełny opis podcastu lub odcinka pod Alt+D zarówno
    # z listy, jak i z odtwarzacza. Sam opis pozostaje zwykłym tekstem tylko
    # do odczytu; skrót nie otwiera strony internetowej.
    "Alt+D": Action.SHOW_PODCAST_DESCRIPTION,
    # Opcje pojedynczego podcastu lub odcinka. Gest wprost z głównego AMC
    # (CommandIds.ItemPlaybackOptions): działa z listy i odtwarzacza.
    "Alt+Shift+Return": Action.PODCAST_PLAYBACK_OPTIONS,
    # Pelny AMC zmienia wspolnie cale zaznaczenie: gdy wszystkie elementy sa
    # ulubione, usuwa stan; w przeciwnym razie dodaje go wszystkim.
    "Ctrl+Shift+U": Action.TOGGLE_PODCAST_FAVORITE,
    # Odcinek nie ma osobnego członkostwa w Bibliotece: skrót zmienia jego
    # podcast nadrzędny, zgodnie z pełnym AMC.
    "Ctrl+Shift+L": Action.TOGGLE_PODCAST_LIBRARY,
}


TIDAL_SESSION_VIEW: dict[str, Action] = {
    "Ctrl+Shift+L": Action.TIDAL_TOGGLE_LIBRARY,
    "Ctrl+Shift+U": Action.TIDAL_TOGGLE_FAVORITE,
}


TIDAL_LIST_VIEW: dict[str, Action] = {
    # MainWindow.xaml.cs:21808-21810: kontekstowe menu relacji zaznaczonego
    # elementu. Pionowe strzalki nadal pozostaja natywnej liscie.
    "Right": Action.TIDAL_RELATIONS,
}


TIDAL_COLLECTION_LIST_VIEW: dict[str, Action] = {
    "Alt+1": Action.SORT_TIDAL_COLLECTION_ADDED,
    "Alt+2": Action.SORT_TIDAL_COLLECTION_ALPHABETICAL,
    "Alt+3": Action.SORT_TIDAL_COLLECTION_CUSTOM,
}


# W sesji WiiM Ctrl+O nie otwiera lokalnego pliku. Pokazuje zapisane w
# profilu AMC strumienie sieciowe dla zaznaczonego albo aktywnego urządzenia.
# Kontekst rozstrzygamy przed ogólną tablicą LIST_VIEW/PLAYER_VIEW.
WIIM_SESSION_VIEW: dict[str, Action] = {
    "Ctrl+O": Action.VIEW_WIIM_NETWORK_STREAMS,
    "Ctrl+N": Action.ADD_WIIM_NETWORK_STREAM,
    "Ctrl+Shift+O": Action.IMPORT_WIIM_NETWORK_STREAMS,
    "Ctrl+E": Action.EXPORT_WIIM_NETWORK_STREAMS,
    "F2": Action.EDIT_WIIM_NETWORK_STREAM,
    "Delete": Action.REMOVE_WIIM_NETWORK_STREAMS,
    "Alt+1": Action.SORT_WIIM_NETWORK_STREAMS_ADDED,
    "Alt+2": Action.SORT_WIIM_NETWORK_STREAMS_ALPHABETICAL,
    "Alt+3": Action.SORT_WIIM_NETWORK_STREAMS_CUSTOM,
}


# Klawisze odtwarzacza WiiM z pełnego AMC. Muszą mieć pierwszeństwo przed
# lokalnym zaznaczaniem fragmentu (I/O) i zwykłymi poleceniami plików.
WIIM_PLAYER_VIEW: dict[str, Action] = {
    # MainWindow.xaml.cs:21617-21618 i 22326-22327. To nie sa zwykle
    # poprzedni/nastepny utwor: pelne AMC przechodzi po zapisanych
    # strumieniach AMC albo zajetych, grywalnych presetach urzadzenia.
    "Alt+Prior": Action.WIIM_PREVIOUS_SOURCE,
    "Alt+Next": Action.WIIM_NEXT_SOURCE,
    "I": Action.WIIM_SELECT_INPUT,
    "O": Action.WIIM_SELECT_OUTPUT,
    "E": Action.WIIM_SELECT_EQUALIZER,
    "R": Action.WIIM_SELECT_REPEAT,
    "S": Action.WIIM_TOGGLE_SHUFFLE,
    "T": Action.WIIM_SET_SLEEP_TIMER,
}


SONOS_SESSION_VIEW: dict[str, Action] = {
    # Jak w głównym AMC: grupy i głośniki są celem sterowania, nie Biblioteką.
    "Ctrl+F5": Action.SELECT_SONOS_TARGET,
    "Ctrl+L": Action.VIEW_LIBRARY,
    "Ctrl+U": Action.VIEW_FAVORITES,
    "Ctrl+P": Action.VIEW_PLAYLISTS,
}


SONOS_OWN_STREAMS_VIEW: dict[str, Action] = {
    "Ctrl+N": Action.ADD_SONOS_OWN_STREAM,
    "F2": Action.EDIT_SONOS_OWN_STREAM,
    "Delete": Action.REMOVE_SONOS_OWN_STREAMS,
    # Tak samo jak w oryginalnym oknie Moje stacje Sonosa.
    "Ctrl+O": Action.IMPORT_SONOS_OWN_STREAMS,
    "Alt+1": Action.SORT_SONOS_OWN_STREAMS_ADDED,
    "Alt+2": Action.SORT_SONOS_OWN_STREAMS_ALPHABETICAL,
    "Alt+3": Action.SORT_SONOS_OWN_STREAMS_CUSTOM,
    "Alt+Up": Action.MOVE_SONOS_OWN_STREAM_UP,
    "Alt+Down": Action.MOVE_SONOS_OWN_STREAM_DOWN,
    "Ctrl+X": Action.CUT_SONOS_OWN_STREAMS,
    "Ctrl+V": Action.PASTE_SONOS_OWN_STREAMS,
    "Ctrl+E": Action.EXPORT_SONOS_OWN_STREAMS,
}


def resolve(
    chord: Chord,
    *,
    player_view: bool,
    radio_session: bool,
    radio_recording_context: bool = False,
    podcast_inbox: bool = False,
    podcast_session: bool = False,
    tidal_session: bool = False,
    tidal_collection: bool = False,
    wiim_session: bool = False,
    wiim_streams: bool = False,
    sonos_session: bool = False,
    sonos_own_streams: bool = False,
) -> Action | None:
    """Znajdz akcje dla klawisza w DANYM widoku. Brak wpisu = klawisz zostaje
    dla kontrolki (natywna nawigacja ma pierwszenstwo)."""
    table = PLAYER_VIEW if player_view else LIST_VIEW
    canonical = chord.canonical
    # W „Nowych odcinkach” te same cyfry co w glownym AMC zmieniaja
    # kolejnosc. Poza tym jednym widokiem Alt+1/Alt+2 zachowuja lokalne
    # znaczenie Folderow/Wszystkich plikow, a Alt+3 pozostaje wolne.
    if not player_view and podcast_inbox and canonical in PODCAST_INBOX_LIST_VIEW:
        return PODCAST_INBOX_LIST_VIEW[canonical]
    # Parity z głównym AMC: Ctrl+F5 zawsze odświeża wszystkie źródła sesji,
    # F5 w skrzynce robi to samo, a F5 w pozostałych widokach odświeża źródło
    # bieżącego podcastu lub odcinka.
    if podcast_session and canonical in PODCAST_SESSION_VIEW:
        return PODCAST_SESSION_VIEW[canonical]
    # Alt+1/2/3 w TIDAL sortuja tylko trzy rownorzedne korzenie kolekcji.
    # W albumie, wykonawcy ani kolejce klawisze nie moga wpasc w lokalne
    # znaczenie „Foldery/Wszystkie pliki”.
    if tidal_session and canonical in TIDAL_COLLECTION_LIST_VIEW:
        return (
            TIDAL_COLLECTION_LIST_VIEW[canonical]
            if not player_view and tidal_collection
            else None
        )
    if tidal_session and canonical in TIDAL_SESSION_VIEW:
        return TIDAL_SESSION_VIEW[canonical]
    if tidal_session and not player_view and canonical in TIDAL_LIST_VIEW:
        return TIDAL_LIST_VIEW[canonical]
    if player_view and wiim_session and canonical in WIIM_PLAYER_VIEW:
        return WIIM_PLAYER_VIEW[canonical]
    if wiim_session and canonical in WIIM_SESSION_VIEW:
        action = WIIM_SESSION_VIEW[canonical]
        if action in {
            Action.EDIT_WIIM_NETWORK_STREAM,
            Action.REMOVE_WIIM_NETWORK_STREAMS,
            Action.SORT_WIIM_NETWORK_STREAMS_ADDED,
            Action.SORT_WIIM_NETWORK_STREAMS_ALPHABETICAL,
            Action.SORT_WIIM_NETWORK_STREAMS_CUSTOM,
        } and not wiim_streams:
            return None
        return action
    if sonos_session and canonical in SONOS_OWN_STREAMS_VIEW:
        return SONOS_OWN_STREAMS_VIEW[canonical] if sonos_own_streams else None
    if sonos_session and canonical in SONOS_SESSION_VIEW:
        return SONOS_SESSION_VIEW[canonical]
    if sonos_session and canonical in {"Shift+A", "Ctrl+[", "Ctrl+]"}:
        # Sonos nie używa lokalnych wyjść Windows. Jego celem jest grupa pod
        # Ctrl+F5; nie wysyłamy tych gestów do dialogu urządzeń komputera.
        return None
    # Widoki Radia sa dostepne takze z odtwarzacza, bez wychodzenia Escape.
    # Ta sama akcja co na liscie/menu; nie przenosimy edycji stacji do PLAYER.
    if radio_session and canonical in ("Ctrl+L", "Ctrl+U", "Ctrl+H"):
        return LIST_VIEW[canonical]
    if player_view and radio_session and canonical in RADIO_PLAYER_VIEW:
        return RADIO_PLAYER_VIEW[canonical]
    # Na zwyklej liscie gola litera B pozostaje wyszukiwaniem przyrostowym.
    # Zakladke nagrania przejmujemy tylko w rownorzednym widoku Nagrywane.
    if (
        not player_view
        and radio_session
        and radio_recording_context
        and canonical in ("B", "Shift+B", "Ctrl+Shift+B")
    ):
        return (
            Action.ADD_BOOKMARK
            if canonical == "B"
            else Action.ADD_NAMED_BOOKMARK
        )
    if not player_view and radio_session and canonical in RADIO_LIST_VIEW:
        return RADIO_LIST_VIEW[canonical]
    return table.get(canonical)


def _help_entries() -> list[tuple[str, str, Action]]:
    """Tekst pomocy (F1). Po polsku, krotko, bez zaleznosci od wx."""
    labels = {
        Action.SESSION_FILES: "Pliki lokalne",
        Action.SESSION_RADIO: "Radio internetowe",
        Action.SESSION_PODCASTS: "Podcasty i YouTube",
        Action.SESSION_TIDAL: "TIDAL",
        Action.SESSION_WIIM: "WiiM",
        Action.SESSION_SONOS: "Sonos",
        Action.SESSION_LIST: "Wybierz sesję z listy",
        Action.SELECT_SONOS_TARGET: "Wybierz grupę Sonos",
        Action.ACTIVATE: "Otworz folder albo odtworz",
        Action.PARENT_FOLDER: "Folder nadrzedny",
        Action.CLOSE_LIST_PREVIEW: "Zamknij podglad lub podwidok",
        Action.SHOW_PLAYER: "Widok odtwarzacza",
        Action.SHOW_LIST: "Powrot na liste",
        Action.PLAY_PAUSE: "Pauza albo wznowienie",
        Action.TOGGLE_MUTE: "Wycisz albo włącz dźwięk bieżącej sesji",
        Action.QUEUE_NEXT: "Nastepny utwor kolejki",
        Action.QUEUE_PREVIOUS: "Poprzedni utwor kolejki",
        Action.ADD_TO_QUEUE: "Dodaj zaznaczenie do kolejki albo je usun",
        Action.TOGGLE_PLAY_NEXT: "Ustaw albo usun odtwarzanie jako nastepne",
        Action.TOGGLE_FAVORITE: "Dodaj lub usuń z Ulubionych",
        Action.MANAGE_PLAYLIST_MEMBERSHIP: "Zmień przynależność do playlist",
        Action.TIDAL_TOGGLE_LIBRARY: "Dodaj lub usuń z Biblioteki TIDAL",
        Action.TIDAL_TOGGLE_FAVORITE: "Dodaj lub usuń z Ulubionych TIDAL",
        Action.TIDAL_RELATIONS: (
            "Pokaż menu przejścia do albumu lub wykonawcy TIDAL"
        ),
        Action.SEEK_BACK_10: "Przewin 10 sekund wstecz",
        Action.SEEK_FORWARD_10: "Przewin 10 sekund w przod",
        Action.SEEK_BACK_30: "Przewin 30 sekund wstecz",
        Action.SEEK_FORWARD_30: "Przewin 30 sekund w przod",
        Action.SEEK_BACK_60: "Przewin minute wstecz",
        Action.SEEK_FORWARD_60: "Przewin minute w przod",
        # Krok tej pary ustawia uzytkownik w AMC (domyslnie 5 minut), wiec
        # pomoc nie moze podawac stalej liczby sekund.
        Action.SEEK_BACK_CUSTOM: "Przewin wstecz o czas z ustawien AMC",
        Action.SEEK_FORWARD_CUSTOM: "Przewin w przod o czas z ustawien AMC",
        Action.VOLUME_UP_5: "Glosniej o 5",
        Action.VOLUME_DOWN_5: "Ciszej o 5",
        Action.VOLUME_UP_1: "Glosniej o 1",
        Action.VOLUME_DOWN_1: "Ciszej o 1",
        Action.RATE_UP: "Szybciej (prędkość odtwarzania)",
        Action.RATE_DOWN: "Wolniej (prędkość odtwarzania)",
        Action.RATE_RESET: "Prędkość normalna",
        Action.TIME_ELAPSED: "Czas miniony",
        Action.TIME_REMAINING: "Czas pozostaly",
        Action.TIME_TOTAL: "Czas calkowity",
        Action.ADD_BOOKMARK: "Dodaj zakladke w biezacym miejscu",
        Action.ADD_NAMED_BOOKMARK: "Dodaj nazwana zakladke w biezacym miejscu",
        Action.PREVIOUS_BOOKMARK: "Poprzednia zakładka",
        Action.NEXT_BOOKMARK: "Następna zakładka",
        Action.CLIP_MARK_START: "Ustaw poczatek fragmentu",
        Action.CLIP_MARK_END: "Ustaw koniec fragmentu",
        Action.CLIP_JUMP_START: "Skocz do poczatku fragmentu",
        Action.CLIP_JUMP_END: "Skocz do konca fragmentu",
        Action.CLIP_PREVIOUS_BOUNDARY: "Poprzednia granica fragmentu",
        Action.CLIP_NEXT_BOUNDARY: "Nastepna granica fragmentu",
        Action.CLIP_EXPORT: "Zapisz zaznaczony fragment jako nowy plik",
        Action.CLIP_APPEND: "Dopisz zaznaczony fragment na koncu pliku",
        Action.CLIP_CLEAR: "Wyczysc zaznaczenie fragmentu",
        Action.TOGGLE_SEEK_MESSAGES: "Automatyczne komunikaty odtwarzacza",
        Action.ADD_PODCAST_SOURCE: "Dodaj podcast, kanał YouTube lub medium internetowe",
        Action.IMPORT_PODCAST_OPML: "Importuj podcasty z OPML",
        Action.EXPORT_PODCAST_OPML: "Eksportuj bibliotekę podcastów do OPML",
        Action.EXPORT_YOUTUBE_SUBSCRIPTIONS: "Eksportuj kanały i playlisty YouTube",
        Action.REFRESH_PODCAST: "Odśwież wybrany podcast, kanał lub playlistę",
        Action.REFRESH_PODCAST_LIBRARY: "Odśwież wszystkie źródła podcastów",
        Action.DOWNLOAD_PODCAST_EPISODES: "Pobierz zaznaczone odcinki podcastów",
        Action.SAVE_PODCAST_EPISODE_AS: "Zapisz jeden odcinek podcastu jako plik",
        Action.SHOW_PODCAST_DESCRIPTION: "Pokaż pełny opis podcastu lub odcinka",
        Action.CURRENT_RADIO_BROADCAST_INFORMATION: (
            "Odczytaj bieżącą audycję lub utwór w Radiu"
        ),
        Action.RECOGNIZE_RADIO_TRACK: "Rozpoznaj utwór z odtwarzanej stacji",
        Action.TOGGLE_RADIO_RECOGNITION_MONITORING: (
            "Włącz lub wyłącz obserwowanie rozpoznawania utworów"
        ),
        Action.TOGGLE_RADIO_RECOGNITION_ANNOUNCEMENTS: (
            "Włącz lub wyłącz oznajmianie rozpoznanych utworów"
        ),
        Action.VIEW_RADIO_RECOGNITION_HISTORY: "Pokaż rozpoznane utwory",
        Action.GO_TO_RELATED_PODCAST: "Przejdź do podcastu wybranego odcinka",
        Action.TOGGLE_PODCAST_FAVORITE: (
            "Dodaj zaznaczone podcasty lub odcinki do ulubionych albo je usuń"
        ),
        Action.TOGGLE_PODCAST_LIBRARY: (
            "Dodaj lub usuń podcast nadrzędny z Biblioteki"
        ),
        Action.PODCAST_PLAYBACK_OPTIONS: (
            "Opcje odtwarzania podcastu albo odcinka"
        ),
        # Skok procentowy. Dziesiec wierszy, bo oryginal ma dziesiec komend i
        # uzytkownik szuka w pomocy konkretnej cyfry, nie opisu rodziny.
        Action.SEEK_PERCENT_0: "Skok na poczatek utworu (0%)",
        Action.SEEK_PERCENT_10: "Skok do 10% utworu",
        Action.SEEK_PERCENT_20: "Skok do 20% utworu",
        Action.SEEK_PERCENT_30: "Skok do 30% utworu",
        Action.SEEK_PERCENT_40: "Skok do 40% utworu",
        Action.SEEK_PERCENT_50: "Skok do polowy utworu (50%)",
        Action.SEEK_PERCENT_60: "Skok do 60% utworu",
        Action.SEEK_PERCENT_70: "Skok do 70% utworu",
        Action.SEEK_PERCENT_80: "Skok do 80% utworu",
        Action.SEEK_PERCENT_90: "Skok do 90% utworu",
        Action.OPEN_FOLDER_DIALOG: "Wybierz folder",
        Action.OPEN_FILE_DIALOG: "Wybierz plik",
        Action.TRACK_START: "Poczatek utworu",
        # Pomoc mowi, ILE oryginal zostawia (CommandRouter.cs:321), zeby
        # uzytkownik nie uznal braku ciszy na koncu za blad.
        Action.TRACK_END: "Koniec utworu, dziesiec sekund przed koncem",
        Action.COPY_NAME: "Skopiuj nazwe",
        Action.COPY_ADDRESS: "Skopiuj adres",
        Action.CUT_FILE: "Wytnij plik albo zaznacz pozycje playlisty do przeniesienia",
        Action.PASTE_OR_MOVE: "Wstaw przenoszone pozycje przed bieżącym elementem",
        Action.MOVE_LIST_ITEM_UP: "Przenieś zaznaczenie wyżej na liście",
        Action.MOVE_LIST_ITEM_DOWN: "Przenieś zaznaczenie niżej na liście",
        Action.RENAME_LIBRARY_ITEM: "Zmień nazwę w Bibliotece lub nazwę źródła",
        Action.RENAME_LOCAL_FILE: "Zmień nazwę pliku na dysku",
        Action.REMOVE_SELECTED: "Usuń z bieżącego widoku bez kasowania pliku",
        Action.RECYCLE_SELECTED: "Przenieś zaznaczone pliki do Kosza",
        Action.STATION_ADD: "Dodaj stacje",
        Action.STATION_EDIT: "Zmien stacje",
        Action.STATION_DELETE: "Usun stacje",
        Action.STATION_IMPORT: "Importuj liste stacji",
        Action.STATION_EXPORT_FAVORITES: "Eksportuj ulubione stacje do playlisty",
        Action.RECORD_TOGGLE: "Rozpocznij albo zatrzymaj nagrywanie wybranej stacji",
        Action.RECORD_PAUSE: "Wstrzymaj albo wznow nagrywanie wybranej stacji",
        Action.RECORD_SPLIT: "Zapisz biezaca czesc i rozpocznij nowa",
        Action.RECORD_STOP_ALL: "Zatrzymaj wszystkie nagrania radia",
        Action.VIEW_ACTIVE_RECORDINGS: "Pokaz trwajace nagrania radia",
        Action.VIEW_RECORDED_RADIO_FILES: "Pokaz historie nagrywania radia",
        Action.ADD_RADIO_SCHEDULE: "Zaplanuj nagranie wybranej stacji",
        Action.MANAGE_RADIO_SCHEDULES: "Pokaz harmonogram nagrywania radia",
        Action.VIEW_PODCAST_INBOX: "Nowe odcinki i materiały",
        Action.VIEW_PODCAST_DOWNLOADS: "Pobrane odcinki podcastów",
        Action.SORT_PODCAST_INBOX_ADDED: (
            "Nowe odcinki: według dodania, najnowsze na początku"
        ),
        Action.SORT_PODCAST_INBOX_ALPHABETICAL: "Nowe odcinki: alfabetycznie",
        Action.SORT_PODCAST_INBOX_BY_PODCAST: "Nowe odcinki: według podcastu",
        Action.SORT_TIDAL_COLLECTION_ADDED: (
            "TIDAL: według dodania, najnowsze na początku"
        ),
        Action.SORT_TIDAL_COLLECTION_ALPHABETICAL: "TIDAL: alfabetycznie",
        Action.SORT_TIDAL_COLLECTION_CUSTOM: "TIDAL: kolejność własna",
        Action.VIEW_PRESETS: "Pokaż presety aktywnej sesji",
        Action.VIEW_WIIM_NETWORK_STREAMS: "Otwórz zapisane strumienie WiiM",
        Action.WIIM_SELECT_INPUT: "Wybierz wejście urządzenia WiiM",
        Action.WIIM_SELECT_OUTPUT: "Wybierz wyjście urządzenia WiiM",
        Action.WIIM_SELECT_EQUALIZER: "Wybierz ustawienie korektora WiiM",
        Action.WIIM_SELECT_REPEAT: "Wybierz tryb powtarzania WiiM",
        Action.WIIM_TOGGLE_SHUFFLE: "Włącz lub wyłącz losowanie WiiM",
        Action.WIIM_SET_SLEEP_TIMER: "Ustaw timer uśpienia WiiM",
        Action.WIIM_PREVIOUS_SOURCE: (
            "Poprzedni strumień lub zajęty preset urządzenia WiiM"
        ),
        Action.WIIM_NEXT_SOURCE: (
            "Następny strumień lub zajęty preset urządzenia WiiM"
        ),
        Action.ADD_WIIM_NETWORK_STREAM: "Dodaj strumień sieciowy WiiM",
        Action.EDIT_WIIM_NETWORK_STREAM: "Edytuj wybrany strumień WiiM",
        Action.REMOVE_WIIM_NETWORK_STREAMS: "Usuń wybrane strumienie WiiM z AMC",
        Action.IMPORT_WIIM_NETWORK_STREAMS: "Importuj playlistę strumieni WiiM",
        Action.EXPORT_WIIM_NETWORK_STREAMS: "Eksportuj strumienie do WiiM Home",
        Action.SORT_WIIM_NETWORK_STREAMS_ADDED: (
            "Strumienie WiiM: według dodania, najnowsze najpierw"
        ),
        Action.SORT_WIIM_NETWORK_STREAMS_ALPHABETICAL: (
            "Strumienie WiiM: alfabetycznie"
        ),
        Action.SORT_WIIM_NETWORK_STREAMS_CUSTOM: (
            "Strumienie WiiM: kolejność własna"
        ),
        Action.ASSIGN_PRESET: "Utwórz preset lub przypisz bieżący element",
        Action.VIEW_ALL_FILES: "Wszystkie pliki alfabetycznie",
        Action.VIEW_FAVORITES: "Ulubione",
        Action.VIEW_PLAYLISTS: "Playlisty",
        Action.VIEW_FOLDERS: "Foldery Biblioteki",
        Action.VIEW_LIBRARY: "Biblioteka: powrot do zapamietanego widoku",
        Action.VIEW_HISTORY: "Historia odtwarzania",
        # Wiersze pochodza z ZAPISANEGO profilu (host nie jest ich autorem), ale
        # Enter uruchamia z nich ZYWA kolejke hosta -- stad "Enter odtwarza".
        Action.VIEW_SAVED_QUEUE: "Kolejka: kolejka silnika, Enter odtwarza",
        # Jawnie wezszy zakres niz "Zakladki" w pelnym AMC.
        Action.VIEW_ITEM_BOOKMARKS: "Zakladki zaznaczonego pliku",
        # Pelny zbior. Nazwa mowi, ze to wszystkie sesje, bo widok pokazuje
        # tez wpisy, ktorych ten program nie odtworzy.
        Action.VIEW_ALL_BOOKMARKS: "Wszystkie zakladki",
        # Pomoc MUSI powiedziec cala droge wyjscia, bo pole filtra zabiera
        # klawisze liter i uzytkownik czytnika nie widzi, ze jest w edycji.
        Action.FOCUS_FILTER: (
            "Filtruj liste: Enter albo strzalka w dol przechodzi do wynikow, "
            "Escape czysci filtr"
        ),
        Action.SEARCH_CURRENT: "Szukaj w bieżącej usłudze",
        Action.SEARCH_ALL: "Szukaj we wszystkich usługach",
        # Nazwa mowi, CO klawisz daje, a nie jak dziala. "Uzupelniajace", bo
        # sama nazwa wiersza jest juz przeczytana przy nawigacji -- oryginal
        # celowo jej nie powtarza (QuickMediaInformationFormatter:8-10).
        Action.QUICK_INFORMATION: (
            "Informacje uzupelniajace o zaznaczonym wierszu "
            "(folder: sciezka)"
        ),
        Action.HELP: "Ta pomoc",
        Action.KEYBOARD_HELP: "Włącz lub wyłącz Pomoc klawiatury",
        # Pomoc mowi WPROST, ze zakres to sesja, a nie zaznaczony plik -- bez
        # tego uzytkownik nie wie, czego dotkna zmiany.
        Action.SESSION_OPTIONS: (
            "Opcje odtwarzania tej sesji: dialog pokazuje tylko opcje, "
            "ktore sesja umie wykonac"
        ),
        Action.SELECT_AUDIO_OUTPUT: (
            "Wybierz urządzenie audio dla bieżącej sesji"
        ),
        Action.PREVIOUS_AUDIO_OUTPUT: (
            "Poprzednie dostępne urządzenie audio bieżącej sesji"
        ),
        Action.NEXT_AUDIO_OUTPUT: (
            "Następne dostępne urządzenie audio bieżącej sesji"
        ),
        Action.GENERAL_SETTINGS: "Ustawienia interfejsu i odtwarzania",
    }
    labels.update({
        action: f"Uruchom preset {slot} bieżącej sesji"
        for slot, action in PRESET_ACTIONS.items()
    })
    # Nazwy klawiszy w pomocy musza byc TAKIE, jak na klawiaturze. Wewnetrzne
    # "Prior"/"Next" (z wx) czytnik przeczytalby jako obce slowa, a uzytkownik
    # nie znalazlby tych klawiszy pod palcami.
    readable_keys = {"Prior": "Page Up", "Next": "Page Down"}

    seen: set[Action] = set()
    out: list[tuple[str, str, Action]] = []
    for table in (
        PODCAST_INBOX_LIST_VIEW,
        PODCAST_SESSION_VIEW,
        TIDAL_LIST_VIEW,
        WIIM_SESSION_VIEW,
        WIIM_PLAYER_VIEW,
        SONOS_SESSION_VIEW,
        LIST_VIEW,
        RADIO_LIST_VIEW,
        RADIO_PLAYER_VIEW,
        PLAYER_VIEW,
    ):
        for chord, action in table.items():
            if action in seen:
                continue
            seen.add(action)
            label = chord
            for internal, spoken in readable_keys.items():
                label = label.replace(internal, spoken)
            # Ctrl+O jest celowo kontekstowe. Dwa identyczne naglowki w
            # pomocy wygladalyby jak sprzecznosc i ``dict(describe())``
            # zgubilby pierwszy. Dopowiadamy sesje tylko przy imporcie Radia;
            # zwykle Ctrl+O nadal brzmi po prostu jak wybor pliku.
            if action is Action.STATION_IMPORT:
                label = f"{label} (Radio internetowe)"
            elif action is Action.IMPORT_PODCAST_OPML:
                label = f"{label} (Podcasty i YouTube)"
            elif action is Action.VIEW_WIIM_NETWORK_STREAMS:
                label = f"{label} (WiiM)"
            elif action is Action.SELECT_SONOS_TARGET:
                label = f"{label} (Sonos)"
            elif action in {
                Action.ADD_WIIM_NETWORK_STREAM,
                Action.EDIT_WIIM_NETWORK_STREAM,
                Action.REMOVE_WIIM_NETWORK_STREAMS,
                Action.IMPORT_WIIM_NETWORK_STREAMS,
                Action.EXPORT_WIIM_NETWORK_STREAMS,
                Action.SORT_WIIM_NETWORK_STREAMS_ADDED,
                Action.SORT_WIIM_NETWORK_STREAMS_ALPHABETICAL,
                Action.SORT_WIIM_NETWORK_STREAMS_CUSTOM,
            }:
                label = f"{label} (Strumienie WiiM)"
            # Nigdy nie wystawiamy technicznego identyfikatora Enum do mowy
            # czytnika. Brak etykiety jest defektem katalogu, ale bezpieczny
            # tekst użytkowy nadal nie ujawnia ``action.value``.
            out.append((label, labels.get(action, "Polecenie AMC"), action))
    return out


def describe() -> list[tuple[str, str]]:
    """Tekst spisu F1 bez technicznych identyfikatorów poleceń."""
    return [(chord, label) for chord, label, _action in _help_entries()]


def describe_action(action: Action) -> str:
    """Jedna użytkowa nazwa polecenia dla Pomocy klawiatury Ctrl+F1."""
    for _chord, label, candidate in _help_entries():
        if candidate is action:
            return label
    return "Polecenie AMC"


def readable_chord(chord: Chord) -> str:
    """Nazwa klawisza przeznaczona do mowy, nie zapis wewnętrzny wx."""
    text = chord.canonical
    for internal, spoken in {
        "Prior": "Page Up",
        "Next": "Page Down",
        "Return": "Enter",
        "Back": "Backspace",
        "Space": "Spacja",
    }.items():
        text = text.replace(internal, spoken)
    return text


def keyboard_help_announcement(
    chord: Chord,
    action: Action | None,
    session_label: str,
    *,
    available: bool = True,
) -> str:
    """Zwięzły opis Ctrl+F1: skrót, polecenie i kontekst sesji."""
    shortcut = readable_chord(chord)
    if action is None:
        return f"{shortcut}. Brak polecenia w sesji {session_label}"
    label = describe_action(action)
    if not available:
        return f"{shortcut}. {label}. Niedostępne w sesji {session_label}"
    return f"{shortcut}. {label}. {session_label}"
