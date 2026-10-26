namespace AccessibleMediaController.Core.Presentation;

public enum RecognitionHistoryCommandId
{
    OpenTrack,
    OpenAlbum,
    ShowActions,
    QuickInformation,
    CopyDescription,
    CopyTrackLink,
    MoveUp,
    MoveDown,
    Delete
}

public sealed record RecognitionHistoryCommandSpec(
    RecognitionHistoryCommandId Id,
    string Shortcut,
    string Name,
    string Description);

/// <summary>
/// Jedno źródło nazw, skrótów i opisów dla okna historii, pomocy oraz testów.
/// Warstwa Windows dopisuje wyłącznie mapowanie fizycznych klawiszy.
/// </summary>
public static class RecognitionHistoryCommands
{
    public static IReadOnlyList<RecognitionHistoryCommandSpec> Definitions { get; } =
    [
        new(RecognitionHistoryCommandId.OpenTrack, "Enter", "Odtwórz utwór",
            "Wyszukuje na żądanie i odtwarza utwór w usłudze domyślnej."),
        new(RecognitionHistoryCommandId.OpenAlbum, "Ctrl+Enter", "Pokaż album",
            "Otwiera album w usłudze domyślnej wewnątrz AMC i ustawia fokus na rozpoznanym utworze."),
        new(RecognitionHistoryCommandId.ShowActions, "Strzałka w prawo", "Działania i powiązania",
            "Pokazuje krótką listę najważniejszych relacji oraz otwierania w AMC i oryginalnych aplikacjach. Pełna lista jest w menu kontekstowym."),
        new(RecognitionHistoryCommandId.QuickInformation, "Strzałka w lewo", "Informacje o utworze",
            "Odczytuje tytuł, wykonawcę, album i stację."),
        new(RecognitionHistoryCommandId.CopyDescription, "Ctrl+C", "Kopiuj opis",
            "Kopiuje pełny wielowierszowy opis rozpoznania."),
        new(RecognitionHistoryCommandId.CopyTrackLink, "Ctrl+Shift+C", "Kopiuj łącze do utworu",
            "Kopiuje dokładne łącze w usłudze domyślnej."),
        new(RecognitionHistoryCommandId.MoveUp, "Alt+Strzałka w górę", "Przenieś wyżej",
            "Przenosi zaznaczone wpisy o jedną pozycję wyżej."),
        new(RecognitionHistoryCommandId.MoveDown, "Alt+Strzałka w dół", "Przenieś niżej",
            "Przenosi zaznaczone wpisy o jedną pozycję niżej."),
        new(RecognitionHistoryCommandId.Delete, "Delete", "Usuń wpis",
            "Usuwa zaznaczone wpisy z historii.")
    ];
}
