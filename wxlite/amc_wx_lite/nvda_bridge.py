"""Wersjonowana lista poleceń dodatku NVDA dla interfejsu wxPython.

Potok i sprawdzenie bieżącego użytkownika należą do hosta C#. Ten moduł
zawiera jedynie jawną mapę zweryfikowanego polecenia na istniejącą akcję UI.
Nie przyjmuje identyfikatorów akcji, ścieżek ani poleceń powłoki z zewnątrz.
"""

from __future__ import annotations

from .shortcuts import Action

EVENT_NAME = "nvda.command"


ACTION_BY_COMMAND: dict[str, Action] = {
    "playPause": Action.PLAY_PAUSE,
    "previous": Action.QUEUE_PREVIOUS,
    "next": Action.QUEUE_NEXT,
    "volumeUp": Action.VOLUME_UP_5,
    "volumeDown": Action.VOLUME_DOWN_5,
    "mute": Action.TOGGLE_MUTE,
    "seekBack": Action.SEEK_BACK_10,
    "seekForward": Action.SEEK_FORWARD_10,
    "elapsed": Action.TIME_ELAPSED,
    "remaining": Action.TIME_REMAINING,
    "total": Action.TIME_TOTAL,
    "seekBack30": Action.SEEK_BACK_30,
    "seekForward30": Action.SEEK_FORWARD_30,
    "seekBack60": Action.SEEK_BACK_60,
    "seekForward60": Action.SEEK_FORWARD_60,
    "rateDown": Action.RATE_DOWN,
    "rateUp": Action.RATE_UP,
    "rateReset": Action.RATE_RESET,
    "trackStart": Action.TRACK_START,
    "trackEnd": Action.TRACK_END,
    "addBookmark": Action.ADD_BOOKMARK,
    "previousBookmark": Action.PREVIOUS_BOOKMARK,
    "nextBookmark": Action.NEXT_BOOKMARK,
    "favorite": Action.TOGGLE_FAVORITE,
    "queue": Action.ADD_TO_QUEUE,
    "recordToggle": Action.RECORD_TOGGLE,
    "recordPause": Action.RECORD_PAUSE,
    "recordSplit": Action.RECORD_SPLIT,
    "showPlayer": Action.SHOW_PLAYER,
    "showLibrary": Action.VIEW_LIBRARY,
    "showFavorites": Action.VIEW_FAVORITES,
    "showQueue": Action.VIEW_SAVED_QUEUE,
    "showPlaylists": Action.VIEW_PLAYLISTS,
    "showHistory": Action.VIEW_HISTORY,
    "showPresets": Action.VIEW_PRESETS,
    "showBookmarks": Action.VIEW_ALL_BOOKMARKS,
    "showAudioOutput": Action.SELECT_AUDIO_OUTPUT,
    "showSearch": Action.SEARCH_CURRENT,
    "showRecordings": Action.VIEW_ACTIVE_RECORDINGS,
    "showSchedules": Action.MANAGE_RADIO_SCHEDULES,
    "showRecognitions": Action.VIEW_RADIO_RECOGNITION_HISTORY,
    "refreshPodcastLibrary": Action.REFRESH_PODCAST_LIBRARY,
    **{f"preset{slot}": getattr(Action, f"PRESET_{slot}") for slot in range(1, 13)},
}

READ_COMMANDS = frozenset({"status", "context", "nowPlaying"})
SESSION_COMMANDS = frozenset({"sessionPrevious", "sessionNext"})
SPECIAL_COMMANDS: frozenset[str] = frozenset()

# Te komendy są prawidłową częścią istniejącego dodatku, lecz odpowiadają
# funkcjom, których AMC Python jeszcze nie ma. Jawna odmowa jest bezpieczniejsza
# niż podstawienie podobnej, ale innej czynności (np. zakładki za rozdział).
KNOWN_NOT_IMPLEMENTED = frozenset({
    "muteAll",
    "previousChapter",
    "nextChapter",
    "presetPrevious",
    "presetNext",
    "showChapters",
    "showSessions",
    "showCommands",
})

ALLOWED_COMMANDS = frozenset(
    frozenset(ACTION_BY_COMMAND)
    | READ_COMMANDS
    | SESSION_COMMANDS
    | SPECIAL_COMMANDS
    | KNOWN_NOT_IMPLEMENTED
)

OPEN_WINDOW_COMMANDS = frozenset({
    "showPlayer",
    "showLibrary",
    "showFavorites",
    "showQueue",
    "showPlaylists",
    "showHistory",
    "showPresets",
    "showBookmarks",
    "showChapters",
    "showSessions",
    "showAudioOutput",
    "showSearch",
    "showCommands",
    "showRecordings",
    "showSchedules",
    "showRecognitions",
})

WORKS_WITH_OPEN_WINDOW = frozenset({
    "volumeUp",
    "volumeDown",
    "mute",
    "playPause",
    "seekBack",
    "seekForward",
    "status",
    "context",
    "nowPlaying",
})


def action_for(command: str) -> Action | None:
    return ACTION_BY_COMMAND.get(command)


def unavailable_message(command: str) -> str:
    labels = {
        "muteAll": "Wyciszenie wszystkich sesji",
        "previousChapter": "Poprzedni rozdział",
        "nextChapter": "Następny rozdział",
        "presetPrevious": "Poprzedni preset",
        "presetNext": "Następny preset",
        "showChapters": "Lista rozdziałów",
        "showSessions": "Lista sesji",
        "showCommands": "Paleta poleceń",
    }
    label = labels.get(command, "To polecenie")
    return f"Funkcja „{label}” nie jest jeszcze dostępna w AMC Python."
