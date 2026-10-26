using System.IO;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Presentation;
using AccessibleMediaController.Core.Sessions;

namespace AccessibleMediaController.Windows;

/// <summary>
/// Odswiezanie list po RZECZYWISTYM przeniesieniu nagrania oraz krotkie,
/// jednoznaczne etykiety plikow w zwyklej nawigacji.
///
/// Wymaganie historii nagrań:
///  * po Ctrl+X i wklejeniu pliku poza AMC w Historii nagrywania nadal stalo
///    „Nagrano nazwa”, a Enter szedl w martwa stara sciezke,
///  * wiersz ma podawac tylko stan i nazwe pliku. Stacja, harmonogram, data i
///    folder nie moga powtarzac sie przy kazdym ruchu strzalka.
///
/// Osobny plik partial, zeby nie rozlewac tego po 25 tysiacach linii
/// MainWindow.xaml.cs. Sama logika (etykiety, przepisywanie sciezek, tania
/// obserwacja) siedzi w Core i jest zmierzona bez GUI.
/// </summary>
public partial class MainWindow
{
    /// <summary>
    /// Tania obserwacja „czy plik nagrania jest na dysku”, wspolna dla wszystkich
    /// klatek listy. OCHRONA SZYBKOSCI: bez tego kazda klatka Historii
    /// nagrywania robilaby synchroniczny <c>File.Exists</c> po calej kolekcji,
    /// czyli przy filtrowaniu kilkaset uderzen w dysk na jeden znak. To cofnaloby
    /// przyspieszenie AMC, ktore Michal potwierdzil.
    /// </summary>
    private readonly RecordingPathProbe _recordingPathProbe = new(File.Exists, Directory.Exists);

    /// <summary>
    /// Wiersz Historii nagrywania: skutek i nazwa pliku. Stan brakujacego pliku
    /// bierze sie z taniej obserwacji, nie ze skanu biblioteki.
    /// </summary>
    private MediaItemRow CreateConciseRecordingHistoryRow(
        RadioRecordingHistorySettings entry,
        DateTime nowUtc)
    {
        var fileMissing = RadioRecordingHistoryLabels.HasPlayableFile(entry)
            && _recordingPathProbe.IsMissing(entry.Path);
        var fileUnavailable = RadioRecordingHistoryLabels.HasPlayableFile(entry)
            && _recordingPathProbe.IsUnavailable(entry.Path);
        var label = RadioRecordingRowLabels.DescribeHistoryRow(entry, nowUtc, fileMissing, fileUnavailable);
        var item = new MediaItem
        {
            Id = $"radio-recording-history:{entry.Id}",
            Title = label,
            Kind = MediaItemKind.Track,
            Source = entry.Path,
            // Wpis po przeniesieniu pliku nie udaje gotowego do odtworzenia.
            IsAvailable = RadioRecordingRowLabels.IsPlayableNow(entry, fileMissing || fileUnavailable),
            IsInLibrary = false
        };
        return new MediaItemRow(item, label, label, recordingHistoryEntry: entry);
    }

    /// <summary>
    /// Zwykly plik nagrania z biblioteki. FormatListItem zawiera stacje,
    /// wykonawce, folder i inne metadane potrzebne w pozostalych widokach;
    /// Historia nagrywania celowo ich nie dziedziczy.
    /// </summary>
    private static MediaItemRow CreateConciseRecordedFileRow(MediaItem item)
    {
        var name = RadioRecordingRowLabels.FileNameLabel(item.Source) ?? item.Title;
        var label = RadioRecordingRowLabels.DescribeRecordedFile(item.Source, item.Title);
        return new MediaItemRow(item, label, name);
    }

    /// <summary>
    /// Plik naprawde zmienil miejsce (obserwator folderu albo przeniesienie w
    /// AMC). Przepisuje odwolania historii na nowa sciezke i uniewaznia tania
    /// obserwacje DOKLADNIE dla dwoch sciezek - nie dla calej biblioteki.
    /// Zwraca <c>true</c>, gdy trzeba zapisac stan.
    /// </summary>
    private bool RewriteRecordingHistoryPath(string oldPath, string newPath)
    {
        _recordingPathProbe.Invalidate(oldPath);
        _recordingPathProbe.Invalidate(newPath);
        var changed = RadioRecordingHistoryPathRewriter.Rewrite(
            _state.Radio.RecordingHistory,
            oldPath,
            newPath);
        return changed > 0;
    }

    /// <summary>
    /// Plik zniknal ze starej sciezki, a nowego miejsca NIE znamy (wklejony poza
    /// AMC). Wpis historii ZOSTAJE - kasowanie zgubiloby historie, a chwilowo
    /// niedostepny dysk wygladalby jak celowe przeniesienie. Zmienia sie tylko
    /// obserwacja, dzieki czemu wiersz przestaje mowic „gotowy”, a Enter nie
    /// idzie w martwa sciezke.
    /// </summary>
    private void MarkRecordingPathMissing(string path) => _recordingPathProbe.MarkMissing(path);

    /// <summary>
    /// Walidacja PRZED Enterem: uniewaznia obserwacje tej jednej sciezki i mowi,
    /// czy da sie odtworzyc. Gdy nie - podaje uczciwy komunikat z nazwa i
    /// folderem. Jeden <c>File.Exists</c> na aktywacje, nie na klatke.
    /// </summary>
    private bool CanActivateRecordingHistoryEntry(
        RadioRecordingHistorySettings entry,
        out string message)
    {
        if (!RadioRecordingHistoryLabels.HasPlayableFile(entry))
        {
            message = RadioRecordingHistoryLabels.DescribeUnplayable(entry);
            return false;
        }
        _recordingPathProbe.Invalidate(entry.Path);
        if (!_recordingPathProbe.Exists(entry.Path))
        {
            message = _recordingPathProbe.IsUnavailable(entry.Path)
                ? RadioRecordingRowLabels.DescribeHistoryRow(entry, DateTime.UtcNow, false, true)
                : RadioRecordingRowLabels.DescribeMissing(entry);
            return false;
        }
        message = string.Empty;
        return true;
    }

    /// <summary>
    /// Reczne odswiezenie Biblioteki (F5) czysci pamiec obserwacji - user
    /// wyraznie prosi o ponowne spojrzenie na dysk.
    /// </summary>
    private void ResetRecordingPathObservations() => _recordingPathProbe.Clear();

    /// <summary>
    /// DELIKATNE odswiezenie wierszy Plikow nagranych z radia. Michal prosil, by
    /// listy „delikatnie sie odswiezaly”: nie przenosimy fokusu, nie skanujemy
    /// biblioteki i nie ruszamy innych widokow. Zachowujemy zaznaczenie po Id, a
    /// gdy wpis zniknal - fokus wraca tam, gdzie stal.
    /// </summary>
    private void RefreshRecordingAvailabilityOnActivation()
    {
        if (_isClosing || _playerViewActive
            || !string.Equals(_sessions.Current.Id, "local", StringComparison.Ordinal)
            || !string.Equals(_currentView, RecordedRadioFilesViewName, StringComparison.Ordinal))
            return;

        var changed = false;
        // Tylko pliki z aktualnego podglądu, raz po powrocie do okna.
        // Nie uruchamiamy synchronizacji ani skanu Folderów Biblioteki.
        var paths = _unfilteredItems
            .Select(row => row.RecordingHistoryEntry?.Path ?? row.Item.Source)
            .Where(path => !string.IsNullOrWhiteSpace(path))
            .Distinct(StringComparer.OrdinalIgnoreCase);
        foreach (var path in paths)
        {
            var previous = _recordingPathProbe.Exists(path);
            _recordingPathProbe.Invalidate(path);
            changed |= previous != _recordingPathProbe.Exists(path);
        }
        if (changed) RefreshRecordedRadioFilesRowsQuietly();
    }

    private void RefreshRecordedRadioFilesRowsQuietly()
    {
        if (_isClosing) return;
        if (_playerViewActive) return;
        // Tylko widok Plikow nagranych z radia. Inne widoki nalezą do innego
        // agenta i do globalnych podgladow - nie dotykamy ich.
        if (!string.Equals(_currentView, RecordedRadioFilesViewName, StringComparison.Ordinal)) return;

        var selectedId = SelectedItem?.Id;
        var hadListFocus = MediaList.IsKeyboardFocusWithin;
        if (hadListFocus) AnchorMediaListFocus();
        RefreshCurrentView(preferredItemId: selectedId);
        if (hadListFocus) RestoreMediaListFocusAfterRefresh();
    }
}
