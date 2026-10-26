using AccessibleMediaController.Core.Configuration;

namespace AccessibleMediaController.Core.Presentation;

/// <summary>
/// Krotkie etykiety list „Nagrywane” i „Historia nagrywania”. Przy zwyklej
/// nawigacji NVDA ma slyszec stan oraz nazwe pliku, bez powtarzania stacji,
/// harmonogramu, daty i folderu. Pelna sciezka oraz folder nadal sa dostepne
/// w szczegolach i komunikatach bledu, ale nie zagluszaja kazdego wiersza.
///
/// Druga czesc zgloszenia (punkt3): po przeniesieniu pliku poza AMC wiersz
/// nadal mowil „Nagrano”, a Enter szedl w martwa sciezke. Dlatego stan
/// brakującego pliku jest tu jawnym parametrem - wolajacy podaje wynik
/// TANIEJ obserwacji, a nie synchroniczny <c>File.Exists</c> po calej
/// bibliotece przy kazdej klatce listy (patrz <see cref="RecordingPathProbe"/>).
/// </summary>
public static class RadioRecordingRowLabels
{
    private const string FolderPrefix = "folder ";

    /// <summary>
    /// Nazwa folderu docelowego gotowa do odczytu, albo <c>null</c>, gdy
    /// nagranie nie ma sciezki (proba nieudana) lub sciezki nie da sie
    /// zinterpretowac. Nigdy nie zwraca samego slowa „folder” bez nazwy.
    /// </summary>
    public static string? FolderLabel(string? path)
    {
        if (string.IsNullOrWhiteSpace(path)) return null;
        string? name;
        try
        {
            var normalized = System.IO.Path.IsPathFullyQualified(path.Trim())
                ? System.IO.Path.GetFullPath(path.Trim()) : path.Trim();
            var directory = System.IO.Path.GetDirectoryName(normalized);
            if (string.IsNullOrWhiteSpace(directory)) return null;
            name = System.IO.Path.GetFileName(
                System.IO.Path.TrimEndingDirectorySeparator(directory));
            // Korzen dysku (C:\, /) nie ma nazwy pliku - czytamy wtedy sam korzen.
            if (string.IsNullOrWhiteSpace(name)) name = directory;
        }
        catch (Exception exception) when (
            exception is ArgumentException or System.IO.PathTooLongException or NotSupportedException)
        {
            return null;
        }
        return string.IsNullOrWhiteSpace(name) ? null : FolderPrefix + name;
    }

    /// <summary>
    /// Dopisuje folder docelowy na KONIEC gotowej etykiety wiersza. Idempotentne:
    /// etykieta, ktora juz konczy sie tym folderem, wraca bez zmian, zeby przy
    /// odswiezeniu listy nie czytac folderu dwa razy.
    /// </summary>
    public static string AppendFolder(string label, string? path)
    {
        var folder = FolderLabel(path);
        if (folder is null) return label;
        if (label.TrimEnd().EndsWith(folder, StringComparison.Ordinal)) return label;
        return label.Length == 0 ? folder : $"{label}, {folder}";
    }

    /// <summary>Uzyteczna nazwa nagrania: nazwa pliku bez rozszerzenia.</summary>
    public static string? FileNameLabel(string? path)
    {
        if (string.IsNullOrWhiteSpace(path)) return null;
        try
        {
            var name = System.IO.Path.GetFileNameWithoutExtension(path.Trim());
            return string.IsNullOrWhiteSpace(name) ? null : name;
        }
        catch (Exception exception) when (
            exception is ArgumentException or System.IO.PathTooLongException)
        {
            return null;
        }
    }

    /// <summary>
    /// Wiersz Alt+R. Dopoki zapisywany plik nie ma jeszcze sciezki, uzywa
    /// nazwy stacji zamiast technicznej wartosci lub pustego wiersza.
    /// </summary>
    public static string DescribeActiveRow(string? path, string? fallbackName) =>
        $"Nagrywane, {ResolveRecordingName(path, fallbackName, "plik jest przygotowywany")}";

    /// <summary>Gotowy plik w Historii nagrywania: tylko stan i nazwa.</summary>
    public static string DescribeRecordedFile(string? path, string? fallbackName) =>
        $"Nagrane, {ResolveRecordingName(path, fallbackName, "nieznany plik")}";

    /// <summary>
    /// Czy Enter ma czego odtworzyc TERAZ. <paramref name="fileMissing"/> pochodzi
    /// z obserwacji folderu albo z walidacji przy aktywacji - nie ze skanu
    /// biblioteki. Dzieki temu wpis po przeniesieniu pliku nie udaje gotowego.
    /// </summary>
    public static bool IsPlayableNow(RadioRecordingHistorySettings entry, bool fileMissing)
    {
        ArgumentNullException.ThrowIfNull(entry);
        return RadioRecordingHistoryLabels.HasPlayableFile(entry) && !fileMissing;
    }

    /// <summary>
    /// Komunikat po Enterze na wpisie, ktorego plik zniknal z dysku (przeniesiony
    /// poza AMC albo usuniety). Mowi wprost, czego nie ma.
    /// </summary>
    public static string DescribeMissing(RadioRecordingHistorySettings entry)
    {
        ArgumentNullException.ThrowIfNull(entry);
        if (!RadioRecordingHistoryLabels.HasPlayableFile(entry))
            return RadioRecordingHistoryLabels.DescribeUnplayable(entry);
        var station = string.IsNullOrWhiteSpace(entry.StationName)
            ? "nieznanej stacji"
            : entry.StationName;
        var name = FileNameLabel(entry.Path);
        var folder = FolderLabel(entry.Path);
        var where = folder is null ? string.Empty : $", {folder}";
        return name is null
            ? $"Plik nagrania {station} nie istnieje już na dysku"
            : $"Plik nagrania {station} nie istnieje już na dysku: {name}{where}";
    }

    /// <summary>
    /// Krotki wiersz Historii nagrywania: skutek i nazwa pliku. Stacje oraz
    /// powod dodajemy tylko wtedy, gdy proba nie utworzyla zadnego pliku i bez
    /// tych informacji dwa bledy bylyby nierozroznialne. Harmonogram, data i
    /// folder nie sa czescia zwyklej nawigacji po liscie.
    /// </summary>
    public static string DescribeHistoryRow(
        RadioRecordingHistorySettings entry,
        DateTime nowUtc,
        bool fileMissing, bool fileUnavailable = false)
    {
        ArgumentNullException.ThrowIfNull(entry);
        _ = nowUtc; // Zachowane w sygnaturze dla zgodnosci wywolan i testow.

        var outcome = RadioRecordingHistoryLabels.OutcomeLabel(entry.Outcome);
        if (fileMissing && RadioRecordingHistoryLabels.HasPlayableFile(entry))
            outcome = entry.Outcome == RadioRecordingOutcome.Completed
                ? "Brak pliku nagrania"
                : $"{outcome}, brak pliku nagrania";
        if (fileUnavailable && RadioRecordingHistoryLabels.HasPlayableFile(entry))
            outcome = entry.Outcome == RadioRecordingOutcome.Completed
                ? "Plik nagrania niedostępny"
                : $"{outcome}, plik nagrania niedostępny";

        var name = FileNameLabel(entry.Path);
        if (name is not null)
        {
            return $"{outcome}, {name}";
        }

        var parts = new List<string> { outcome };
        if (!string.IsNullOrWhiteSpace(entry.StationName))
            parts.Add(entry.StationName.Trim());
        if (!string.IsNullOrWhiteSpace(entry.Reason))
            parts.Add(entry.Reason.Trim().TrimEnd('.'));
        if (parts.Count == 1) parts.Add("nieznane nagranie");
        return string.Join(", ", parts);
    }

    private static string ResolveRecordingName(
        string? path,
        string? fallbackName,
        string emptyName) =>
        FileNameLabel(path)
        ?? (string.IsNullOrWhiteSpace(fallbackName) ? emptyName : fallbackName.Trim());
}
