"""Opis menu jako DANE -- bez zaleznosci od wx.

Menu AMC-wx-Lite nie ma wlasnej logiki. Kazda pozycja niesie ``Action``,
ktora juz istnieje i ktora wywoluje ten sam ``MainWindow._dispatch``, co
skrot klawiszowy. GUI tylko zamienia ten opis na ``wx.MenuBar``.

Dlaczego osobny modul, a nie od razu ``wx.Menu``:
  * da sie go sprawdzic testem bez okna i bez czytnika ekranu,
  * widac na jednej stronie, czy skrot w menu zgadza sie z tablica skrotow,
  * nie da sie przypadkiem dopisac pozycji z wlasna logika obok dispatchera.

Nazwy pozycji pochodza z pelnego AMC (MainWindow.xaml), nie sa wymyslone:
  458  "_Wszystkie pliki alfabetycznie"   Alt+2
  426  "_Ulubione"                        Ctrl+U
  427  "_Playlisty"                       Ctrl+P

Czego tu NIE MA i dlaczego:
  * 237 martwych pozycji z pelnego AMC -- nie kopiujemy menu, ktore nic nie
    robi w tej aplikacji,
  * pozycji "niedostepne" jako zapowiedzi -- menu wymienia tylko to, co
    naprawde dziala dzisiaj,
  * zapisu do wspolnego profilu -- jest czytany tylko do odczytu, wiec
    pozycje zmieniajace stacje sa UCZCIWIE wylaczane poza sesja radiowa.
"""

from __future__ import annotations

from dataclasses import dataclass

from .navigation import SessionId
from .shortcuts import (
    Action,
    SONOS_SUPPORTED_ACTIONS,
    TIDAL_SUPPORTED_ACTIONS,
    WIIM_SUPPORTED_ACTIONS,
)


@dataclass(frozen=True, slots=True)
class MenuItem:
    """Jedna pozycja. ``action`` prowadzi do dispatchera, ``builtin`` do okna.

    ``shortcut`` jest tylko PODPISEM -- klawisz obsluguje ``shortcuts.resolve``.
    Test pilnuje, zeby podpis zgadzal sie z prawda.
    """

    label: str = ""
    action: Action | None = None
    builtin: str | None = None
    shortcut: str | None = None
    #: Czy ``shortcut`` wolno oddac wx jako AKCELERATOR (tekst po ``\t``).
    #:
    #: Domyslnie tak. Dla GOLYCH klawiszy edycji (Backspace, Spacja, Delete)
    #: musi byc ``False``: wx robi z takiego podpisu akcelerator na poziomie
    #: OKNA, ktory ma pierwszenstwo przed kontrolka z fokusem i POLYKA klawisz
    #: w polu filtra. Zmierzone na zywym GUI (final-recovery, plan D):
    #: Backspace nie kasowal znaku, tylko wynosil uzytkownika o poziom wyzej.
    #: Sam skrot dziala dalej -- obsluguja go tablice w ``shortcuts``.
    accelerator: bool = True
    #: Wylaczana poza sesja radiowa, zamiast udawac, ze zadziala.
    needs_radio_session: bool = False
    #: Dostępna wyłącznie dla lokalnych plików, np. zakładki materiału.
    needs_files_session: bool = False
    #: Dostępna tylko dla wskazanej stacji, która ma aktywny tor nagrywania.
    needs_radio_recording: bool = False
    #: Widok dostepny wylacznie wewnatrz sesji Podcasty i YouTube.
    needs_podcast_session: bool = False
    #: Te trzy pozycje sa aktywne tylko w zbiorczym widoku Nowych odcinkow.
    needs_podcast_inbox: bool = False
    #: Aktywna wyłącznie w jednym z trzech głównych widoków kolekcji TIDAL.
    needs_tidal_collection: bool = False
    #: Aktywna tylko na liście zapisanych strumieni, nie na urządzeniu WiiM.
    needs_wiim_stream: bool = False
    #: Aktywna tylko w lokalnej kategorii „Moje stacje” sesji Sonos.
    needs_sonos_own_stream: bool = False
    #: Pozycja PRZELACZNIKA: wx ma ja wstawic jako ``AppendCheckItem``.
    #:
    #: Nie jest to kosmetyka. Zwykla pozycja menu nie niesie stanu, wiec
    #: czytnik ekranu powiedzialby tylko nazwe i uzytkownik nie wiedzialby, czy
    #: opcja jest wlaczona, dopoki jej nie przestawi. Pozycja zaznaczalna ma
    #: rolę "pole wyboru" i stan "zaznaczone"/"niezaznaczone" w nazwie
    #: dostepnosciowej, wiec stan slychac BEZ zmieniania go.
    checkable: bool = False
    #: Wymaga czegos grajacego (transport, pytanie o czas).
    needs_playback: bool = False
    #: Dostępna wyłącznie po otwarciu panelu odtwarzacza danej sesji.
    needs_player_view: bool = False
    #: Wymaga zaznaczonego wiersza na liscie (kopiowanie, otwarcie).
    needs_selection: bool = False
    #: Wymaga zaznaczonego podcastu albo odcinka, nie np. „Załaduj więcej”.
    needs_podcast_item: bool = False
    #: Wymaga elementu, ktory w aktywnej sesji moze nalezec do Ulubionych.
    #: Rozdzielenie tej bramki od samego ``needs_selection`` zapobiega
    #: oferowaniu polecenia m.in. na folderze, albumie TIDAL albo w WiiM.
    needs_favorite_item: bool = False
    #: Wymaga utworu, stacji albo odcinka obsługiwanego przez lokalne playlisty
    #: AMC. Podcast nagłówkowy, kontener TIDAL i urządzenie sieciowe odpadają.
    needs_playlist_item: bool = False
    #: Wymaga otwartej zawartości lokalnej playlisty. To węższy warunek niż
    #: zwykły element mogący należeć do playlisty: dotyczy ręcznej kolejności.
    needs_playlist_contents: bool = False
    #: Wymaga zaznaczonego odcinka; wykonanie sprawdza jeszcze członkostwo
    #: podcastu w Bibliotece na świeżym, tylko do odczytu odczycie SQLite.
    needs_podcast_episode: bool = False
    #: Pusta krotka oznacza pozycje wspolna. Wpisane sesje oznaczaja, ze
    #: pozycji w ogole nie ma w innych sesjach -- nie zostaje tam jako
    #: mylace, wyszarzone polecenie obcej uslugi.
    visible_sessions: tuple[SessionId, ...] = ()
    is_separator: bool = False


@dataclass(frozen=True, slots=True)
class Menu:
    title: str
    items: tuple[MenuItem, ...]


SEPARATOR = MenuItem(is_separator=True)
FILES_ONLY = (SessionId.FILES,)
PODCASTS_ONLY = (SessionId.PODCASTS,)
WIIM_ONLY = (SessionId.WIIM,)
SONOS_ONLY = (SessionId.SONOS,)
LOCAL_MEDIA = (SessionId.FILES, SessionId.PODCASTS)
LOCAL_AUDIO = (SessionId.FILES, SessionId.RADIO, SessionId.PODCASTS)
LOCAL_TIMELINE = (SessionId.FILES, SessionId.RADIO, SessionId.PODCASTS)
PLAYER_SESSIONS = (
    SessionId.FILES,
    SessionId.RADIO,
    SessionId.PODCASTS,
    SessionId.WIIM,
    SessionId.SONOS,
)


def menus_for_session(session_id: SessionId) -> tuple[Menu, ...]:
    """Menu bez polecen nalezacych do innej sesji.

    Separatory sa porzadkowane po filtrowaniu, zeby NVDA nie czytal pustych
    grup na poczatku, koncu ani dwoch separatorow obok siebie.
    """

    supported = {
        SessionId.TIDAL: TIDAL_SUPPORTED_ACTIONS,
        SessionId.WIIM: WIIM_SUPPORTED_ACTIONS,
        SessionId.SONOS: SONOS_SUPPORTED_ACTIONS,
    }.get(session_id)
    menus: list[Menu] = []
    for described in build_menus():
        items: list[MenuItem] = []
        for entry in described.items:
            if entry.visible_sessions and session_id not in entry.visible_sessions:
                continue
            if (
                supported is not None
                and entry.action is not None
                and entry.action not in supported
            ):
                continue
            if entry.is_separator:
                if items and not items[-1].is_separator:
                    items.append(entry)
                continue
            items.append(entry)
        while items and items[-1].is_separator:
            items.pop()
        if items:
            menus.append(Menu(described.title, tuple(items)))
    return tuple(menus)


def build_menus() -> tuple[Menu, ...]:
    """Pelny opis paska menu. Kolejnosc jak w pelnym AMC: Pliki, Radio, Widok."""
    files = Menu(
        "&Pliki",
        (
            # Kolejnosc i gesty z oryginalu (MainWindow.xaml:42-49): pliki pod
            # Ctrl+O, folder pod Ctrl+Shift+O.
            # Ctrl+O jest kontekstowe (Pliki / Radio / Podcasty) jak w AMC.
            # Nie robimy z zadnej pozycji akceleratora okna, bo pierwsza
            # widoczna pozycja przejelaby gest przed resolverem sesji.
            MenuItem("Otwórz &plik", Action.OPEN_FILE_DIALOG, shortcut="Ctrl+O",
                     accelerator=False, visible_sessions=FILES_ONLY),
            MenuItem("Otwórz &folder", Action.OPEN_FOLDER_DIALOG,
                     shortcut="Ctrl+Shift+O", visible_sessions=FILES_ONLY),
            MenuItem(
                "Zapisane &strumienie WiiM",
                Action.VIEW_WIIM_NETWORK_STREAMS,
                shortcut="Ctrl+O",
                accelerator=False,
                visible_sessions=WIIM_ONLY,
            ),
            MenuItem(
                "Nowy str&umień WiiM…",
                Action.ADD_WIIM_NETWORK_STREAM,
                shortcut="Ctrl+N",
                accelerator=False,
                visible_sessions=WIIM_ONLY,
            ),
            MenuItem(
                "Importuj playlistę strumieni WiiM (&Q)…",
                Action.IMPORT_WIIM_NETWORK_STREAMS,
                shortcut="Ctrl+Shift+O",
                accelerator=False,
                visible_sessions=WIIM_ONLY,
            ),
            MenuItem(
                "Eksportuj strumienie do WiiM Home (&X)…",
                Action.EXPORT_WIIM_NETWORK_STREAMS,
                shortcut="Ctrl+E",
                accelerator=False,
                visible_sessions=WIIM_ONLY,
            ),
            MenuItem(
                "Nowa stacj&a Sonos…",
                Action.ADD_SONOS_OWN_STREAM,
                shortcut="Ctrl+N",
                accelerator=False,
                needs_sonos_own_stream=True,
                visible_sessions=SONOS_ONLY,
            ),
            MenuItem(
                "Importuj &listę do Moich stacji Sonosa…",
                Action.IMPORT_SONOS_OWN_STREAMS,
                shortcut="Ctrl+O",
                accelerator=False,
                needs_sonos_own_stream=True,
                visible_sessions=SONOS_ONLY,
            ),
            MenuItem(
                "Eksportuj Moje stacje Sonosa (&R)…",
                Action.EXPORT_SONOS_OWN_STREAMS,
                shortcut="Ctrl+E",
                accelerator=False,
                needs_sonos_own_stream=True,
                visible_sessions=SONOS_ONLY,
            ),
            MenuItem(
                "Dodaj podcast, kanał YouTube lub medium &internetowe",
                Action.ADD_PODCAST_SOURCE,
                shortcut="Ctrl+N",
                accelerator=False,
                needs_podcast_session=True,
                visible_sessions=PODCASTS_ONLY,
            ),
            MenuItem(
                "Importuj podcasty z OP&ML",
                Action.IMPORT_PODCAST_OPML,
                shortcut="Ctrl+O",
                accelerator=False,
                needs_podcast_session=True,
                visible_sessions=PODCASTS_ONLY,
            ),
            MenuItem(
                "&Eksportuj bibliotekę podcastów do OPML",
                Action.EXPORT_PODCAST_OPML,
                needs_podcast_session=True,
                visible_sessions=PODCASTS_ONLY,
            ),
            MenuItem(
                "Eksportuj subskrypcje &YouTube",
                Action.EXPORT_YOUTUBE_SUBSCRIPTIONS,
                needs_podcast_session=True,
                visible_sessions=PODCASTS_ONLY,
            ),
            MenuItem(
                "Odśwież wybrane źródło pod&castów",
                Action.REFRESH_PODCAST,
                shortcut="F5",
                accelerator=False,
                needs_podcast_session=True,
                visible_sessions=PODCASTS_ONLY,
            ),
            MenuItem(
                "Odśwież &wszystkie źródła podcastów",
                Action.REFRESH_PODCAST_LIBRARY,
                shortcut="Ctrl+F5",
                accelerator=False,
                needs_podcast_session=True,
                visible_sessions=PODCASTS_ONLY,
            ),
            MenuItem(
                "Po&bierz zaznaczone odcinki",
                Action.DOWNLOAD_PODCAST_EPISODES,
                shortcut="Ctrl+D",
                accelerator=False,
                needs_podcast_session=True,
                needs_selection=True,
                visible_sessions=PODCASTS_ONLY,
            ),
            MenuItem(
                "Zapisz odcinek &jako…",
                Action.SAVE_PODCAST_EPISODE_AS,
                shortcut="Ctrl+S",
                accelerator=False,
                needs_podcast_session=True,
                needs_selection=True,
                visible_sessions=PODCASTS_ONLY,
            ),
            MenuItem(
                "Pełny &opis podcastu lub odcinka…",
                Action.SHOW_PODCAST_DESCRIPTION,
                shortcut="Alt+D",
                accelerator=False,
                needs_podcast_session=True,
                needs_podcast_item=True,
                visible_sessions=PODCASTS_ONLY,
            ),
            SEPARATOR,
            # Backspace dzialal od dawna, ale wylacznie z klawiatury.
            #
            # BEZ ``needs_selection``, i to jest WARUNEK dostepnosci, nie
            # kosmetyka. wxWidgets zaklada akcelerator okna z tekstu etykiety
            # PO TABULATORZE (``_build_menu`` dokleja tam podpis skrotu).
            # Akcelerator wyprzedza ``EVT_KEY_DOWN`` kontrolki, a gdy pozycja
            # jest WYLACZONA, Windows dopasowuje go i NIE wysyla komendy
            # nikomu -- klawisz zostaje POLKNIETY. Na pustym widoku (brak
            # wiersza => pozycja wyszarzona) Backspace przestawal wiec
            # istniec i z pustych Zakladek nie bylo wyjscia klawiatura.
            # Zmierzone: ``wx-keys-seen.jsonl`` nie zawiera ANI JEDNEGO
            # Backspace, przy ``wx_lista_ma_fokus=true``.
            #
            # Wyjscie z widoku nie potrzebuje zaznaczenia: ``go_to_parent``
            # w nazwanym widoku woli ``_leave_library_view`` jeszcze przed
            # szukaniem wiersza rodzica.
            MenuItem("Folder &nadrzędny", Action.PARENT_FOLDER, shortcut="Back",
                     accelerator=False),
            SEPARATOR,
            MenuItem("&Zakończ", builtin="quit"),
        ),
    )

    library = Menu(
        "&Biblioteka",
        (
            # Foldery Biblioteki dzialaly, ale wejscia w menu nie bylo.
            # MainWindow.xaml:446 "Foldery _Biblioteki" Alt+1.
            # Powrot do Biblioteki z nazwanego widoku. MainWindow.xaml:427
            # "_Biblioteka" Ctrl+L -- pozycji tej w porcie brakowalo, wiec
            # z Ulubionych i Historii nie bylo jak wrocic jednym gestem.
            MenuItem("&Biblioteka", Action.VIEW_LIBRARY, shortcut="Ctrl+L"),
            # Alt+1/Alt+2 maja inne znaczenie w „Nowych odcinkach”. Obie
            # pozycje musza wiec tylko POKAZYWAC skrot, nie rejestrowac
            # akceleratora okna, ktory wyprzedzilby resolver kontekstowy.
            MenuItem("&Foldery Biblioteki", Action.VIEW_FOLDERS,
                     shortcut="Alt+1", accelerator=False),
            MenuItem("&Wszystkie pliki alfabetycznie", Action.VIEW_ALL_FILES,
                     shortcut="Alt+2", accelerator=False),
            MenuItem("&Ulubione", Action.VIEW_FAVORITES, shortcut="Ctrl+U"),
            MenuItem("&Playlisty", Action.VIEW_PLAYLISTS, shortcut="Ctrl+P"),
            MenuItem("Pr&esety…", Action.VIEW_PRESETS, shortcut="Ctrl+Alt+P"),
            MenuItem(
                "Utwórz lub p&rzypisz preset…",
                Action.ASSIGN_PRESET,
                shortcut="Ctrl+Alt+Shift+P",
            ),
            SEPARATOR,
            # Trzy odczyty aktywnosci. Skroty ODCZYTANE z kodu:
            #   MainWindow.xaml:488 "_Historia odtwarzania" Ctrl+H
            #   MainWindow.xaml:487 "_Kolejka"              Ctrl+Q
            MenuItem("&Historia odtwarzania", Action.VIEW_HISTORY, shortcut="Ctrl+H"),
            MenuItem("&Kolejka", Action.VIEW_SAVED_QUEUE, shortcut="Ctrl+Q"),
            # NIE "Zakładki" jak MainWindow.xaml:489. Tamta pozycja (Ctrl+B,
            # ViewBookmarks -> GetForDisplay) pokazuje WSZYSTKIE zakladki; my
            # mamy port GetForItem, czyli zakladki JEDNEGO zaznaczonego pliku.
            # Etykieta i gest musza ten wezszy zakres pokazac, a nie udawac
            # szerszej komendy oryginalu.
            MenuItem("&Zakładki zaznaczonego", Action.VIEW_ITEM_BOOKMARKS,
                     shortcut="Ctrl+Shift+B", accelerator=False,
                     needs_selection=True),
            # Pozycja oryginalu (MainWindow.xaml:489, Ctrl+B). Bez
            # ``needs_selection``: zbiorczy widok nie zalezy od zaznaczenia --
            # kontekst bierze z SESJI, a sesja moze nic nie odtwarzac.
            # Klawisz dostepu "i": "w" zajmuje "Wszystkie pliki
            # alfabetycznie", a "k" -- "Kolejka", obie w TYM SAMYM menu. Dwie
            # pozycje na jednej literze kazalyby uzytkownikowi czytnika
            # zgadywac, ktora sie wybierze.
            MenuItem("Wszystk&ie zakładki", Action.VIEW_ALL_BOOKMARKS,
                     shortcut="Ctrl+B"),
            SEPARATOR,
            MenuItem("&Otwórz zaznaczone", Action.ACTIVATE, shortcut="Return",
                     needs_selection=True),
            MenuItem(
                "Przejdź do podcastu tego o&dcinka",
                Action.GO_TO_RELATED_PODCAST,
                needs_podcast_session=True,
                needs_podcast_episode=True,
            ),
            MenuItem(
                "Z&mień stan ulubionych",
                Action.TOGGLE_FAVORITE,
                shortcut="Ctrl+Shift+U",
                accelerator=False,
                needs_favorite_item=True,
            ),
            MenuItem(
                "Przynależ&ność do playlist…",
                Action.MANAGE_PLAYLIST_MEMBERSHIP,
                shortcut="Ctrl+Shift+P",
                accelerator=False,
                needs_playlist_item=True,
            ),
            SEPARATOR,
            # Ctrl+C obsluguje wspolna droga klawiatury. Oddanie go dodatkowo
            # wx jako systemowego akceleratora menu powodowalo, ze NVDA mowil
            # najpierw angielskie "copy", a dopiero potem nasze celowe
            # "Skopiowano nazwe". Sam gest zatrzymuje jeszcze wczesny hook
            # listy w gui.py; bez niego Podcasty nadal przepuszczaly "copy"
            # do SysListView32. Skrot pozostaje widoczny w nazwie pozycji.
            MenuItem("&Skopiuj nazwę", Action.COPY_NAME, shortcut="Ctrl+C",
                     accelerator=False, needs_selection=True),
            MenuItem("W&ytnij lub zaznacz do przeniesienia", Action.CUT_FILE,
                     shortcut="Ctrl+X", accelerator=False),
            MenuItem("Skopiuj &adres", Action.COPY_ADDRESS, shortcut="Ctrl+Shift+C",
                     needs_selection=True),
            MenuItem(
                "Przenieś wyżej, Alt+strzałka w g&órę",
                Action.MOVE_LIST_ITEM_UP,
                accelerator=False,
                needs_selection=True,
                needs_playlist_contents=True,
            ),
            MenuItem(
                "Przenieś niżej, Alt+strzałka w dó&ł",
                Action.MOVE_LIST_ITEM_DOWN,
                accelerator=False,
                needs_selection=True,
                needs_playlist_contents=True,
            ),
            MenuItem(
                "Wstaw przenoszone przed bieżącym, Ctrl+&V",
                Action.PASTE_OR_MOVE,
                accelerator=False,
                needs_selection=True,
                needs_playlist_contents=True,
            ),
            SEPARATOR,
            MenuItem("Zmień nazwę w Bibliote&ce", Action.RENAME_LIBRARY_ITEM,
                     shortcut="F2", accelerator=False, needs_selection=True,
                     visible_sessions=LOCAL_MEDIA),
            MenuItem("Zmień nazwę pliku na dysku, plik ory&ginalny", Action.RENAME_LOCAL_FILE,
                     shortcut="Shift+F2", accelerator=False, needs_selection=True,
                     visible_sessions=FILES_ONLY),
            MenuItem("Usuń z bieżącego widoku, plik pozos&taje", Action.REMOVE_SELECTED,
                     shortcut="Delete", accelerator=False, needs_selection=True,
                     visible_sessions=LOCAL_MEDIA),
            MenuItem("Przenieś do Kosza, operac&ja plikowa", Action.RECYCLE_SELECTED,
                     shortcut="Shift+Delete", accelerator=False, needs_selection=True,
                     visible_sessions=FILES_ONLY),
            MenuItem(
                "Edytuj strumień WiiM (&X)…",
                Action.EDIT_WIIM_NETWORK_STREAM,
                shortcut="F2",
                accelerator=False,
                needs_selection=True,
                needs_wiim_stream=True,
                visible_sessions=WIIM_ONLY,
            ),
            MenuItem(
                "Usuń strumień WiiM z AMC (&Q)",
                Action.REMOVE_WIIM_NETWORK_STREAMS,
                shortcut="Delete",
                accelerator=False,
                needs_selection=True,
                needs_wiim_stream=True,
                visible_sessions=WIIM_ONLY,
            ),
            MenuItem(
                "Edytuj stację Sonos (&1)…",
                Action.EDIT_SONOS_OWN_STREAM,
                shortcut="F2",
                accelerator=False,
                needs_selection=True,
                needs_sonos_own_stream=True,
                visible_sessions=SONOS_ONLY,
            ),
            MenuItem(
                "Usuń stację Sonos z AMC (&2)",
                Action.REMOVE_SONOS_OWN_STREAMS,
                shortcut="Delete",
                accelerator=False,
                needs_selection=True,
                needs_sonos_own_stream=True,
                visible_sessions=SONOS_ONLY,
            ),
            MenuItem(
                "Sonos: przenieś wyżej (&5)",
                Action.MOVE_SONOS_OWN_STREAM_UP,
                shortcut="Alt+Up",
                accelerator=False,
                needs_selection=True,
                needs_sonos_own_stream=True,
                visible_sessions=SONOS_ONLY,
            ),
            MenuItem(
                "Sonos: przenieś niżej (&6)",
                Action.MOVE_SONOS_OWN_STREAM_DOWN,
                shortcut="Alt+Down",
                accelerator=False,
                needs_selection=True,
                needs_sonos_own_stream=True,
                visible_sessions=SONOS_ONLY,
            ),
            MenuItem(
                "Sonos: zaznacz do przeniesienia (&7)",
                Action.CUT_SONOS_OWN_STREAMS,
                shortcut="Ctrl+X",
                accelerator=False,
                needs_selection=True,
                needs_sonos_own_stream=True,
                visible_sessions=SONOS_ONLY,
            ),
            MenuItem(
                "Sonos: wstaw przed bieżącym (&8)",
                Action.PASTE_SONOS_OWN_STREAMS,
                shortcut="Ctrl+V",
                accelerator=False,
                needs_selection=True,
                needs_sonos_own_stream=True,
                visible_sessions=SONOS_ONLY,
            ),
            SEPARATOR,
            # Oryginal ma te pozycje w TYM SAMYM menu co widoki Kolejka/
            # Historia/Zakladki, po separatorze (MainWindow.xaml:490-491):
            #   <MenuItem Header="_Filtruj listę" InputGestureText="Ctrl+K" />
            # BEZ ``needs_selection``: filtr dziala takze na liscie, z ktorej
            # nic nie jest zaznaczone, a wylaczona pozycja menu polykalaby
            # akcelerator (czytnik mowilby wtedy "niedostepne" bez powodu).
            #
            MenuItem("Fi&ltruj listę", Action.FOCUS_FILTER, shortcut="Ctrl+K"),
        ),
    )

    # Osobne, krótkie menu zapobiega kolizjom klawiszy dostępu w rozbudowanym
    # menu Biblioteka. Funkcyjnie pozostaje tym samym osobnym oknem, które w
    # pełnym AMC jest obok filtra i ma te same skróty Ctrl+F/Ctrl+Shift+F.
    search = Menu(
        "S&zukaj",
        (
            MenuItem(
                "W &bieżącej usłudze",
                Action.SEARCH_CURRENT,
                shortcut="Ctrl+F",
            ),
            MenuItem(
                "&Globalnie",
                Action.SEARCH_ALL,
                shortcut="Ctrl+Shift+F",
            ),
        ),
    )

    radio = Menu(
        "&Radio",
        (
            MenuItem("&Dodaj stację", Action.STATION_ADD, shortcut="Ctrl+N",
                     accelerator=False, needs_radio_session=True),
            MenuItem("&Zmień stację", Action.STATION_EDIT, shortcut="F2",
                     needs_radio_session=True),
            MenuItem("&Usuń stację", Action.STATION_DELETE, shortcut="Delete",
                     accelerator=False, needs_radio_session=True),
            SEPARATOR,
            MenuItem("&Importuj M3U/PLS", Action.STATION_IMPORT, shortcut="Ctrl+O",
                     accelerator=False, needs_radio_session=True),
            MenuItem("Eksportuj ulubione stacje do pli&ku…",
                     Action.STATION_EXPORT_FAVORITES, shortcut="Ctrl+E",
                     accelerator=False, needs_radio_session=True),
            SEPARATOR,
            MenuItem("&Nagrywaj albo zatrzymaj wybraną stację",
                     Action.RECORD_TOGGLE, shortcut="Ctrl+R",
                     # Kontekstowy akcelerator wx potrafi pozostać wyłączony
                     # po zmianie sesji i połknąć Ctrl+R przed hookiem okna.
                     # Podpis zostaje w menu; polecenie obsługuje jawnie GUI.
                     accelerator=False, needs_radio_session=True),
            # Shift+Spacja i gola litera T nie moga zostac akceleratorami
            # okna: w polu filtra sa zwyklymi klawiszami edycji. Obsluguje je
            # resolver tylko wtedy, gdy fokus nie jest w polu tekstowym.
            MenuItem("&Wstrzymaj albo wznów nagrywanie",
                     Action.RECORD_PAUSE, shortcut="Shift+Space",
                     accelerator=False, needs_radio_session=True,
                     needs_radio_recording=True, checkable=True),
            MenuItem("Dodaj szybką zakładkę nag&rania",
                     Action.ADD_BOOKMARK, shortcut="B",
                     accelerator=False, needs_radio_session=True,
                     needs_radio_recording=True),
            MenuItem("Dodaj nazwaną zakładkę na&grania…",
                     Action.ADD_NAMED_BOOKMARK, shortcut="Shift+B",
                     accelerator=False, needs_radio_session=True,
                     needs_radio_recording=True),
            MenuItem("Podziel &bieżące nagranie",
                     Action.RECORD_SPLIT, shortcut="T",
                     accelerator=False, needs_radio_session=True),
            MenuItem("Zatrzymaj w&szystkie nagrania",
                     Action.RECORD_STOP_ALL, shortcut="Ctrl+Alt+Shift+R",
                     accelerator=False, needs_radio_session=True),
            MenuItem("Pokaż n&agrywane", Action.VIEW_ACTIVE_RECORDINGS,
                     shortcut="Alt+R"),
            MenuItem("&Historia nagrywania", Action.VIEW_RECORDED_RADIO_FILES,
                     shortcut="Alt+Shift+R"),
            MenuItem("Za&planuj nagranie wybranej stacji…",
                     Action.ADD_RADIO_SCHEDULE, shortcut="Shift+R",
                     # To polecenie jest kontekstowe i wymaga zaznaczenia.
                     # Wyłączony akcelerator wx potrafi połknąć Shift+R,
                     # zanim zdarzenie dotrze do resolvera listy. Sam podpis
                     # zostaje w menu, a klawisz obsługuje jawnie hook okna.
                     accelerator=False, needs_radio_session=True,
                     needs_selection=True),
            MenuItem("Harmonogra&m nagrywania", Action.MANAGE_RADIO_SCHEDULES,
                     shortcut="Ctrl+Shift+H"),
            SEPARATOR,
            MenuItem(
                "Bieżąca audycja lub u&twór",
                Action.CURRENT_RADIO_BROADCAST_INFORMATION,
                shortcut="Alt+D",
                accelerator=False,
                needs_radio_session=True,
            ),
            MenuItem(
                "Rozpozna&j utwór",
                Action.RECOGNIZE_RADIO_TRACK,
                shortcut="S",
                accelerator=False,
                needs_radio_session=True,
                needs_playback=True,
            ),
            MenuItem(
                "&Obserwuj rozpoznawanie",
                Action.TOGGLE_RADIO_RECOGNITION_MONITORING,
                shortcut="Shift+S",
                accelerator=False,
                needs_radio_session=True,
                checkable=True,
            ),
            MenuItem(
                "Oznajmiaj rozpoznane utwor&y",
                Action.TOGGLE_RADIO_RECOGNITION_ANNOUNCEMENTS,
                shortcut="Ctrl+Alt+Shift+S",
                accelerator=False,
                needs_radio_session=True,
                checkable=True,
            ),
            MenuItem(
                "Rozpoznan&e utwory…",
                Action.VIEW_RADIO_RECOGNITION_HISTORY,
                shortcut="Ctrl+Alt+S",
                accelerator=False,
                needs_radio_session=True,
            ),
        ),
    )

    playback = Menu(
        "&Odtwarzanie",
        (
            MenuItem("&Pauza albo wznowienie", Action.PLAY_PAUSE, shortcut="Space",
                     accelerator=False, needs_playback=True),
            MenuItem(
                "Wycisz albo włącz dźwięk bieżącej sesji (&V)",
                Action.TOGGLE_MUTE,
                shortcut="Ctrl+M",
                accelerator=False,
                checkable=True,
                needs_playback=True,
                visible_sessions=LOCAL_AUDIO,
            ),
            SEPARATOR,
            MenuItem(
                "Ustaw wejście WiiM (&5)…",
                Action.WIIM_SELECT_INPUT,
                shortcut="I",
                accelerator=False,
                needs_playback=True,
                needs_player_view=True,
                visible_sessions=WIIM_ONLY,
            ),
            MenuItem(
                "Ustaw wyjście WiiM (&6)…",
                Action.WIIM_SELECT_OUTPUT,
                shortcut="O",
                accelerator=False,
                needs_playback=True,
                needs_player_view=True,
                visible_sessions=WIIM_ONLY,
            ),
            MenuItem(
                "Korektor WiiM (&7)…",
                Action.WIIM_SELECT_EQUALIZER,
                shortcut="E",
                accelerator=False,
                needs_playback=True,
                needs_player_view=True,
                visible_sessions=WIIM_ONLY,
            ),
            MenuItem(
                "Powtarzanie WiiM (&8)…",
                Action.WIIM_SELECT_REPEAT,
                shortcut="R",
                accelerator=False,
                needs_playback=True,
                needs_player_view=True,
                visible_sessions=WIIM_ONLY,
            ),
            MenuItem(
                "Losowanie WiiM (&9)",
                Action.WIIM_TOGGLE_SHUFFLE,
                shortcut="S",
                accelerator=False,
                needs_playback=True,
                needs_player_view=True,
                visible_sessions=WIIM_ONLY,
            ),
            MenuItem(
                "Timer uśpienia WiiM (&Q)…",
                Action.WIIM_SET_SLEEP_TIMER,
                shortcut="T",
                accelerator=False,
                needs_playback=True,
                needs_player_view=True,
                visible_sessions=WIIM_ONLY,
            ),
            MenuItem(
                "Poprzedni strumień lub preset WiiM (&Z)",
                Action.WIIM_PREVIOUS_SOURCE,
                shortcut="Alt+Prior",
                accelerator=False,
                needs_playback=True,
                needs_player_view=True,
                visible_sessions=WIIM_ONLY,
            ),
            MenuItem(
                "Następny strumień lub preset WiiM (&N)",
                Action.WIIM_NEXT_SOURCE,
                shortcut="Alt+Next",
                accelerator=False,
                needs_playback=True,
                needs_player_view=True,
                visible_sessions=WIIM_ONLY,
            ),
            MenuItem("Dodaj &zakładkę", Action.ADD_BOOKMARK, shortcut="B",
                     accelerator=False, needs_playback=True,
                     needs_files_session=True, visible_sessions=FILES_ONLY),
            MenuItem(
                "Dodaj nazwaną zakładk&ę…",
                Action.ADD_NAMED_BOOKMARK,
                shortcut="Ctrl+Shift+B",
                accelerator=False,
                needs_playback=True,
                needs_files_session=True,
                visible_sessions=FILES_ONLY,
            ),
            MenuItem(
                "&2. Poprzednia zakładka, Shift+Page Up",
                Action.PREVIOUS_BOOKMARK,
                accelerator=False,
                needs_playback=True,
                needs_files_session=True,
                visible_sessions=FILES_ONLY,
            ),
            MenuItem(
                "&4. Następna zakładka, Shift+Page Down",
                Action.NEXT_BOOKMARK,
                accelerator=False,
                needs_playback=True,
                needs_files_session=True,
                visible_sessions=FILES_ONLY,
            ),
            SEPARATOR,
            # Zaznaczanie i edycja fragmentu. Kazda pozycja prowadzi do tej
            # samej akcji co klawisz w PLAYER_VIEW; brak akceleratora okna jest
            # celowy, bo Ctrl+X na liscie oznacza wyciecie calego pliku do
            # przeniesienia, a I/O naleza tam do wyszukiwania przyrostowego.
            MenuItem("Ustaw początek &fragmentu", Action.CLIP_MARK_START,
                     shortcut="I", accelerator=False, needs_playback=True,
                     visible_sessions=FILES_ONLY),
            MenuItem("Ustaw koniec fra&gmentu", Action.CLIP_MARK_END,
                     shortcut="O", accelerator=False, needs_playback=True,
                     visible_sessions=FILES_ONLY),
            MenuItem("Prz&ejdź do początku fragmentu", Action.CLIP_JUMP_START,
                     shortcut="Shift+I", accelerator=False, needs_playback=True,
                     visible_sessions=FILES_ONLY),
            MenuItem("Przejdź do końca fragmen&tu", Action.CLIP_JUMP_END,
                     shortcut="Shift+O", accelerator=False, needs_playback=True,
                     visible_sessions=FILES_ONLY),
            # ``Prior`` / ``Next`` sa wewnetrznymi nazwami klawiszy w tablicy.
            # Do etykiety dla uzytkownika trafiaja prawdziwe nazwy Page Up /
            # Page Down, bez ujawniania identyfikatora modelu.
            MenuItem("Wróć do poprzedniej granicy odsłuc&hu, Alt+Page Up",
                     Action.CLIP_PREVIOUS_BOUNDARY,
                     accelerator=False, needs_playback=True,
                     visible_sessions=FILES_ONLY),
            MenuItem("Prze&jdź do następnej granicy fragmentu, Alt+Page Down",
                     Action.CLIP_NEXT_BOUNDARY,
                     accelerator=False, needs_playback=True,
                     visible_sessions=FILES_ONLY),
            MenuItem("Zapisz zaznaczony fragment jako nowy p&lik…", Action.CLIP_EXPORT,
                     shortcut="Ctrl+S", accelerator=False, needs_playback=True,
                     visible_sessions=FILES_ONLY),
            MenuItem(
                "&Dopisz zaznaczony fragment na końcu istniejącego pliku…",
                Action.CLIP_APPEND,
                shortcut="Ctrl+D",
                accelerator=False,
                needs_playback=True,
                visible_sessions=FILES_ONLY,
            ),
            # Ctrl+X wystepuje juz w menu Pliki dla calego pliku. Tu gest jest
            # wpisany w celowa etykiete wraz z kontekstem, ale nie jako drugi
            # akcelerator okna, ktory odebralby go liscie.
            MenuItem(
                "Usuń zaznaczony fragment z oryginału &bez ponownego kodowania… "
                "(Ctrl+X w odtwarzaczu)",
                Action.CLIP_REMOVE,
                accelerator=False,
                needs_playback=True,
                visible_sessions=FILES_ONLY,
            ),
            MenuItem("Wyczyść zaznaczenie fragmentu, Shift+&X", Action.CLIP_CLEAR,
                     accelerator=False, needs_playback=True,
                     visible_sessions=FILES_ONLY),
            SEPARATOR,
            # Przewijanie. CZTERY kroki oryginalu (MainWindow.xaml.cs:21583-21590):
            # 10 s goly, 30 s z Shift, 60 s z Ctrl, czas z ustawien z Ctrl+Alt.
            # Dotad zadnego z nich nie bylo w menu, wiec uzytkownik, ktory nie
            # zna skrotu, nie mial jak przewinac inaczej niz suwakiem.
            #
            # GOLE Left/Right: ``accelerator=False`` z TEGO SAMEGO powodu, co
            # Backspace i Spacja powyzej. Zmierzone na zywym GUI/NVDA po
            # scaleniu transportu z filtrem (kwit-kolizja-1, plan KOL-POLE):
            # w polu filtra z tekstem "kaz" trzy strzalki w poziomie NIE
            # ruszyly karetki (3 -> 3 -> 3 -> 3), a NVDA powiedzialo trzy razy
            # "pusta" zamiast przeczytac znak. Akcelerator na poziomie OKNA ma
            # pierwszenstwo przed kontrolka z fokusem i polyka klawisz TAKZE
            # wtedy, gdy pozycja menu jest wyszarzona (nic nie gra) -- wiec
            # klawisz nie robil ani przewijania, ani edycji.
            #
            # Dlaczego tylko gole: Ctrl+Left/Right, Shift+Left/Right i
            # Ctrl+Alt+Left/Right ZMIERZONO w tym samym przebiegu (plany
            # KOL-POLE2 i KOL-POLE3) i one karetke/zaznaczenie przepuszczaja,
            # wiec nie ma powodu odbierac im podpisu-akceleratora.
            MenuItem("Przewiń &wstecz 10 sekund", Action.SEEK_BACK_10,
                     shortcut="Left", accelerator=False, needs_playback=True,
                     visible_sessions=LOCAL_TIMELINE),
            MenuItem("Przewiń w przód &10 sekund", Action.SEEK_FORWARD_10,
                     shortcut="Right", accelerator=False, needs_playback=True,
                     visible_sessions=LOCAL_TIMELINE),
            MenuItem("Przewiń wstecz &30 sekund", Action.SEEK_BACK_30,
                     shortcut="Shift+Left", needs_playback=True,
                     visible_sessions=LOCAL_TIMELINE),
            MenuItem("Przewiń w przód 3&0 sekund", Action.SEEK_FORWARD_30,
                     shortcut="Shift+Right", needs_playback=True,
                     visible_sessions=LOCAL_TIMELINE),
            MenuItem("Przewiń wstecz &minutę", Action.SEEK_BACK_60,
                     shortcut="Ctrl+Left", needs_playback=True,
                     visible_sessions=LOCAL_TIMELINE),
            MenuItem("Przewiń w przód m&inutę", Action.SEEK_FORWARD_60,
                     shortcut="Ctrl+Right", needs_playback=True,
                     visible_sessions=LOCAL_TIMELINE),
            MenuItem("Przewiń wstecz o czas z &ustawień AMC",
                     Action.SEEK_BACK_CUSTOM, shortcut="Ctrl+Alt+Left",
                     needs_playback=True, visible_sessions=LOCAL_TIMELINE),
            MenuItem("Przewiń w przód o czas z ustawień &AMC",
                     Action.SEEK_FORWARD_CUSTOM, shortcut="Ctrl+Alt+Right",
                     needs_playback=True, visible_sessions=LOCAL_TIMELINE),
            SEPARATOR,
            # Predkosc odtwarzania. Naglowki i akceleratory doslownie z
            # MainWindow.xaml:382-393 ("_Wolniej" Shift+, / "_Szybciej" Shift+.
            # / "Prędkość _normalna" Ctrl+.). Sam suwak "Tempo" w oknie NIE
            # jest odbiorem tej funkcji: uzytkownik czytnika szuka polecenia w
            # menu i w pomocy, a Michal zglosil wprost, ze predkosci nie
            # znalazl.
            #
            # Shift+, i Shift+. to na klawiaturze ZNAKI "<" i ">", czyli
            # zwykle wpisywanie. Jako akcelerator okna nie docieraly do pola
            # filtra: zmierzone (kwit-kolizja-1, plan KOL-ZNAKI) -- po obu
            # gestach tekst pola pozostal pusty, a dopiero zwykla litera
            # cokolwiek wpisala. Dlatego ``accelerator=False``; samo polecenie
            # dziala dalej przez tablice w ``shortcuts`` i przez menu.
            # Ctrl+. zmierzone osobno jako nieszkodliwe i zostaje z podpisem.
            MenuItem("Wol&niej", Action.RATE_DOWN, shortcut="Shift+,",
                     accelerator=False, needs_playback=True,
                     visible_sessions=LOCAL_MEDIA),
            MenuItem("&Szybciej", Action.RATE_UP, shortcut="Shift+.",
                     accelerator=False, needs_playback=True,
                     visible_sessions=LOCAL_MEDIA),
            MenuItem("Prędkość no&rmalna", Action.RATE_RESET, shortcut="Ctrl+.",
                     needs_playback=True, visible_sessions=LOCAL_MEDIA),
            SEPARATOR,
            # Skroty poprawione na te z oryginalu: Ctrl+SHIFT+E/R/T
            # (MainWindow.xaml.cs:21674-21676). Menu obiecywalo stare Ctrl+E/R/T,
            # czyli etykiete, ktora po poprawce tablicy byla by nieprawda.
            MenuItem("Czas minion&y", Action.TIME_ELAPSED, shortcut="Ctrl+Shift+E",
                     needs_playback=True, visible_sessions=LOCAL_TIMELINE),
            MenuItem("Czas p&ozostały", Action.TIME_REMAINING, shortcut="Ctrl+Shift+R",
                     needs_playback=True, visible_sessions=LOCAL_TIMELINE),
            MenuItem("Czas &całkowity", Action.TIME_TOTAL, shortcut="Ctrl+Shift+T",
                     needs_playback=True, visible_sessions=LOCAL_TIMELINE),
            SEPARATOR,
            # Przelacznik automatycznych komunikatow (cs:21670). We wspolnym
            # profilu wlascicielem state.json jest host C#, wiec akcja mowi,
            # gdzie te opcje zmienic -- zamiast udawac zapis.
            MenuItem("Automatyczne &komunikaty odtwarzacza",
                     Action.TOGGLE_SEEK_MESSAGES, shortcut="Ctrl+Shift+G",
                     visible_sessions=LOCAL_TIMELINE),
        ),
    )

    view = Menu(
        "&Widok",
        (
            MenuItem("Sesja: &Pliki lokalne", Action.SESSION_FILES, shortcut="Ctrl+1"),
            MenuItem("Sesja: &Radio", Action.SESSION_RADIO, shortcut="Ctrl+2"),
            MenuItem("Sesja: Podcasty i &YouTube", Action.SESSION_PODCASTS,
                     shortcut="Ctrl+3"),
            MenuItem("Sesja: &TIDAL", Action.SESSION_TIDAL, shortcut="Ctrl+4"),
            MenuItem("Sesja: &WiiM", Action.SESSION_WIIM, shortcut="Ctrl+5"),
            MenuItem("Sesja: &Sonos", Action.SESSION_SONOS, shortcut="Ctrl+6"),
            MenuItem(
                "Lista sesji… (&0)",
                Action.SESSION_LIST,
                shortcut="Ctrl+0",
                accelerator=False,
            ),
            MenuItem(
                "Wybierz &grupę Sonos",
                Action.SELECT_SONOS_TARGET,
                shortcut="Ctrl+F5",
                accelerator=False,
                visible_sessions=SONOS_ONLY,
            ),
            SEPARATOR,
            MenuItem("&Nowe odcinki i materiały", Action.VIEW_PODCAST_INBOX,
                     shortcut="Ctrl+I",
                     visible_sessions=(SessionId.PODCASTS,)),
            MenuItem("Po&brane", Action.VIEW_PODCAST_DOWNLOADS,
                     needs_podcast_session=True,
                     visible_sessions=(SessionId.PODCASTS,)),
            SEPARATOR,
            # Skroty sa kontekstowe. Nie robimy z nich akceleratorow okna:
            # wyszarzone poza skrzynka podcastow Alt+1/Alt+2 polknelyby wtedy
            # prawidlowe polecenia Biblioteki lokalnej przed resolverem.
            MenuItem("Według &dodania — najnowsze najpierw",
                     Action.SORT_PODCAST_INBOX_ADDED, shortcut="Alt+1",
                     accelerator=False, checkable=True,
                     needs_podcast_inbox=True,
                     visible_sessions=(SessionId.PODCASTS,)),
            MenuItem("&Alfabetycznie",
                     Action.SORT_PODCAST_INBOX_ALPHABETICAL, shortcut="Alt+2",
                     accelerator=False, checkable=True,
                     needs_podcast_inbox=True,
                     visible_sessions=(SessionId.PODCASTS,)),
            MenuItem("Według podcast&u",
                     Action.SORT_PODCAST_INBOX_BY_PODCAST, shortcut="Alt+3",
                     accelerator=False, checkable=True,
                     needs_podcast_inbox=True,
                     visible_sessions=(SessionId.PODCASTS,)),
            SEPARATOR,
            MenuItem("TIDAL: według dodania — na&jnowsze najpierw",
                     Action.SORT_TIDAL_COLLECTION_ADDED, shortcut="Alt+1",
                     accelerator=False, checkable=True,
                     needs_tidal_collection=True,
                     visible_sessions=(SessionId.TIDAL,)),
            MenuItem("TIDAL: alfabetyczni&e",
                     Action.SORT_TIDAL_COLLECTION_ALPHABETICAL, shortcut="Alt+2",
                     accelerator=False, checkable=True,
                     needs_tidal_collection=True,
                     visible_sessions=(SessionId.TIDAL,)),
            MenuItem("TIDAL: &kolejność własna",
                     Action.SORT_TIDAL_COLLECTION_CUSTOM, shortcut="Alt+3",
                     accelerator=False, checkable=True,
                     needs_tidal_collection=True,
                     visible_sessions=(SessionId.TIDAL,)),
            SEPARATOR,
            MenuItem("WiiM: według dodania, najnowsze najpierw (&1)",
                     Action.SORT_WIIM_NETWORK_STREAMS_ADDED, shortcut="Alt+1",
                     accelerator=False, checkable=True,
                     needs_wiim_stream=True,
                     visible_sessions=WIIM_ONLY),
            MenuItem("WiiM: alfabetycznie (&2)",
                     Action.SORT_WIIM_NETWORK_STREAMS_ALPHABETICAL,
                     shortcut="Alt+2", accelerator=False, checkable=True,
                     needs_wiim_stream=True,
                     visible_sessions=WIIM_ONLY),
            MenuItem("WiiM: kolejność własna (&3)",
                     Action.SORT_WIIM_NETWORK_STREAMS_CUSTOM, shortcut="Alt+3",
                     accelerator=False, checkable=True,
                     needs_wiim_stream=True,
                     visible_sessions=WIIM_ONLY),
            MenuItem("Sonos: według dodania, najnows&ze najpierw",
                     Action.SORT_SONOS_OWN_STREAMS_ADDED, shortcut="Alt+1",
                     accelerator=False, checkable=True,
                     needs_sonos_own_stream=True,
                     visible_sessions=SONOS_ONLY),
            MenuItem("Sonos: alfabetyczn&ie",
                     Action.SORT_SONOS_OWN_STREAMS_ALPHABETICAL,
                     shortcut="Alt+2", accelerator=False, checkable=True,
                     needs_sonos_own_stream=True,
                     visible_sessions=SONOS_ONLY),
            MenuItem("Sonos: kolejność własna (&C)",
                     Action.SORT_SONOS_OWN_STREAMS_CUSTOM, shortcut="Alt+3",
                     accelerator=False, checkable=True,
                     needs_sonos_own_stream=True,
                     visible_sessions=SONOS_ONLY),
            SEPARATOR,
            # ``accelerator=False``: ZMIERZONE na zywym GUI (statusclip-1).
            # Z akceleratorem pozycja byla WYLACZONA na liscie (nic nie gralo),
            # a wylaczony akcelerator okna POLYKA swoj klawisz -- F6 dochodzil
            # do okna (``code 345``), ale nie trafial ani do komendy, ani do
            # ``_on_key``, wiec widok zostawal na liscie. Skrot dziala dalej:
            # obsluguje go ``shortcuts.LIST_VIEW["F6"]``, bezwarunkowo.
            #
            # ``needs_playback`` ZOSTAJE: pozycja ma byc wyszarzona, gdy nie ma
            # czego pokazywac. Zdejmujemy tylko akcelerator.
            MenuItem("Widok &odtwarzacza", Action.SHOW_PLAYER, shortcut="F6",
                     accelerator=False, needs_playback=True,
                     visible_sessions=PLAYER_SESSIONS),
            # Powrot na liste istnial tylko z klawiatury (Escape/Shift+F6).
            # Akcja SHOW_LIST byla juz obslugiwana w _dispatch -- brakowalo
            # samego wejscia w menu, wiec nie jest to martwa pozycja.
            #
            # BEZ akceleratora, z tego samego powodu co Backspace wyzej: wx
            # zrobilby z podpisu akcelerator OKNA, ktory wyprzedza kontrolke z
            # fokusem. Escape ma trzy rozne znaczenia zaleznie od miejsca
            # (pole filtra czysci filtr, lista wychodzi o poziom wyzej,
            # odtwarzacz wraca na liste) -- jeden akcelerator okna splaszczylby
            # je do jednego i polknal klawisz w polu filtra.
            MenuItem("Powrót na &listę", Action.SHOW_LIST, shortcut="Escape",
                     accelerator=False, visible_sessions=PLAYER_SESSIONS),
        ),
    )

    # Menu Dzwiek juz istnialo i dziala -- model tylko oznacza miejsce, w
    # ktorym GUI dokleja swoje radio-itemy algorytmow (stan Check per pozycja).
    audio = Menu(
        # Alt+D jest poleceniem tresci: opis Podcastu albo informacja o
        # biezacej audycji Radia. Mnemonik menu nie moze przejmowac tego
        # samego gestu przed lista, dlatego menu otwieramy przez Alt+K.
        "Dźwię&k",
        (
            MenuItem(
                "&Algorytm przyspieszania",
                builtin="tempo-submenu",
                visible_sessions=LOCAL_AUDIO,
            ),
            SEPARATOR,
            # Bez akceleratora okna: Shift+A ma dzialac w liscie i
            # odtwarzaczu, ale w polu tekstowym nadal musi wpisywac wielkie A.
            MenuItem(
                "&Urządzenie audio bieżącej sesji…",
                Action.SELECT_AUDIO_OUTPUT,
                shortcut="Shift+A",
                accelerator=False,
                visible_sessions=LOCAL_AUDIO,
            ),
            MenuItem(
                "&Poprzednie urządzenie audio",
                Action.PREVIOUS_AUDIO_OUTPUT,
                shortcut="Ctrl+[",
                accelerator=False,
                visible_sessions=LOCAL_AUDIO,
            ),
            MenuItem(
                "&Następne urządzenie audio",
                Action.NEXT_AUDIO_OUTPUT,
                shortcut="Ctrl+]",
                accelerator=False,
                visible_sessions=LOCAL_AUDIO,
            ),
            # Opcje dotyczą sesji, także na pustej liście. Ctrl+Alt+Enter
            # jest skrótem okna, więc rejestrujemy natywny akcelerator;
            # sama obsługa KEY_DOWN listy nie uruchamiała dialogu w próbie wx.
            MenuItem(
                "&Opcje sesji…",
                Action.SESSION_OPTIONS,
                shortcut="Ctrl+Alt+Return",
                accelerator=True,
            ),
            MenuItem(
                "Opcje odtwarzania &elementu…",
                Action.PODCAST_PLAYBACK_OPTIONS,
                shortcut="Alt+Shift+Return",
                accelerator=False,
                needs_podcast_session=True,
                visible_sessions=PODCASTS_ONLY,
            ),
        ),
    )

    settings = Menu(
        "&Ustawienia",
        (
            MenuItem(
                "&Interfejs i zachowanie odtwarzania…",
                Action.GENERAL_SETTINGS,
                shortcut="Ctrl+,",
                accelerator=False,
            ),
        ),
    )

    help_menu = Menu(
        "Pomo&c",
        (
            MenuItem("&Skróty klawiszowe", Action.HELP, shortcut="F1"),
            MenuItem(
                "Pomoc &klawiatury",
                Action.KEYBOARD_HELP,
                shortcut="Ctrl+F1",
                accelerator=False,
                checkable=True,
            ),
        ),
    )

    return (files, library, search, radio, playback, view, audio, settings, help_menu)
