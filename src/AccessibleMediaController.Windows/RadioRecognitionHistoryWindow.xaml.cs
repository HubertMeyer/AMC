using System.IO;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Windows;
using System.Windows.Automation;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Threading;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Presentation;
using AccessibleMediaController.Windows.Controls;
using AccessibleMediaController.Windows.Services;
using Microsoft.Win32;

namespace AccessibleMediaController.Windows;

public partial class RadioRecognitionHistoryWindow : AccessibleWindow
{
    private readonly List<RadioRecognizedTrackSettings> _entries;
    private readonly RecognizedTrackStreamingService _defaultService;
    private readonly IRecognitionStreamingResolver? _streamingResolver;
    private readonly IAppleMusicRecognitionLinkResolver? _appleMusicLinkResolver;
    private readonly CancellationTokenSource _lifetimeCancellation = new();
    private List<RecognitionHistoryRow> _rows = [];
    private bool _updatingFilters;
    private bool _busy;

    public RadioRecognitionHistoryWindow(List<RadioRecognizedTrackSettings> entries)
        : this(entries, RecognizedTrackStreamingService.Spotify, null, null)
    {
    }

    internal RadioRecognitionHistoryWindow(
        List<RadioRecognizedTrackSettings> entries,
        RecognizedTrackStreamingService defaultService,
        IRecognitionStreamingResolver? streamingResolver,
        IAppleMusicRecognitionLinkResolver? appleMusicLinkResolver)
    {
        InitializeComponent();
        MenuAccessibility.NormalizeContextMenu(HistoryContextMenu);
        _entries = entries;
        _defaultService = defaultService;
        _streamingResolver = streamingResolver;
        _appleMusicLinkResolver = appleMusicLinkResolver;
        HistoryInstructions.Text = RecognitionHistoryCommandCatalog.Instructions(defaultService);
        RefreshStationFilters();
        RefreshRows();
    }

    public bool Changed { get; private set; }
    internal RecognitionHistoryRequest? RequestedAction { get; private set; }

    private void RefreshRows(string? preferredId = null, int fallbackIndex = 0)
    {
        var filterKey = (StationFilterCombo.SelectedItem as RecognitionStationFilter)?.Key;
        _rows = _entries
            .Where(entry => filterKey is null
                || string.Equals(RecognitionStationFilter.KeyFor(entry), filterKey, StringComparison.OrdinalIgnoreCase))
            .Select(entry => new RecognitionHistoryRow(entry))
            .ToList();
        HistoryList.ItemsSource = _rows;
        if (_rows.Count == 0)
        {
            HistoryList.SelectedIndex = -1;
            HistoryStatus.Text = filterKey is null
                ? "Historia jest pusta"
                : "Brak wpisów dla wybranej stacji";
            return;
        }
        var index = preferredId is null
            ? Math.Clamp(fallbackIndex, 0, _rows.Count - 1)
            : _rows.FindIndex(row => string.Equals(row.Entry.Id, preferredId, StringComparison.Ordinal));
        HistoryList.SelectedIndex = index >= 0 ? index : Math.Clamp(fallbackIndex, 0, _rows.Count - 1);
        HistoryStatus.Text = filterKey is null
            ? $"Wpisów: {_rows.Count}, wszystkie stacje"
            : $"Wpisów: {_rows.Count}, {(StationFilterCombo.SelectedItem as RecognitionStationFilter)?.Label}";
    }

    private void RefreshStationFilters(string? preferredKey = null)
    {
        preferredKey ??= (StationFilterCombo.SelectedItem as RecognitionStationFilter)?.Key;
        var filters = new List<RecognitionStationFilter>
        {
            new(null, "Wszystkie stacje")
        };
        filters.AddRange(_entries
            .GroupBy(RecognitionStationFilter.KeyFor, StringComparer.OrdinalIgnoreCase)
            .Select(group => new RecognitionStationFilter(
                group.Key,
                group.OrderByDescending(entry => entry.RecognizedUtcTicks).First().StationName))
            .OrderBy(filter => filter.Label, StringComparer.CurrentCultureIgnoreCase));

        _updatingFilters = true;
        StationFilterCombo.ItemsSource = filters;
        StationFilterCombo.SelectedItem = filters.FirstOrDefault(filter =>
            string.Equals(filter.Key, preferredKey, StringComparison.OrdinalIgnoreCase)) ?? filters[0];
        _updatingFilters = false;
    }

    private void StationFilterCombo_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_updatingFilters) return;
        RefreshRows();
    }

    private void Window_ContentRendered(object? sender, EventArgs e) => FocusSelectedRow();

    private void FocusSelectedRow()
    {
        HistoryList.UpdateLayout();
        if (HistoryList.SelectedIndex >= 0
            && HistoryList.ItemContainerGenerator.ContainerFromIndex(HistoryList.SelectedIndex)
                is ListBoxItem item)
        {
            item.Focus();
            Keyboard.Focus(item);
            return;
        }
        Keyboard.Focus(HistoryList);
    }

    private async void Window_PreviewKeyDown(object sender, KeyEventArgs e)
    {
        var key = e.Key == Key.System ? e.SystemKey : e.Key;
        var command = RecognitionHistoryCommandCatalog.Resolve(key, Keyboard.Modifiers);
        if (command is null) return;
        e.Handled = true;
        if (_busy && command.Id is not RecognitionHistoryCommandId.CopyDescription) return;

        switch (command.Id)
        {
            case RecognitionHistoryCommandId.OpenTrack:
                await RequestSelectedStreamingActionAsync(RecognitionHistoryRequestKind.PlayTrack);
                break;
            case RecognitionHistoryCommandId.OpenAlbum:
                await RequestSelectedStreamingActionAsync(RecognitionHistoryRequestKind.OpenAlbum);
                break;
            case RecognitionHistoryCommandId.ShowActions:
                ShowActionsMenu(RecognitionActionMenuScope.Quick);
                break;
            case RecognitionHistoryCommandId.QuickInformation:
                AnnounceQuickInformation();
                break;
            case RecognitionHistoryCommandId.CopyDescription:
                CopySelectedDescriptions();
                break;
            case RecognitionHistoryCommandId.CopyTrackLink:
                await CopyDefaultServiceLinksAsync();
                break;
            case RecognitionHistoryCommandId.MoveUp:
                MoveSelected(-1);
                break;
            case RecognitionHistoryCommandId.MoveDown:
                MoveSelected(1);
                break;
            case RecognitionHistoryCommandId.Delete:
                DeleteSelected();
                break;
        }
    }

    private RecognitionHistoryRow[] SelectedRows() =>
        HistoryList.SelectedItems.OfType<RecognitionHistoryRow>().ToArray();

    private void CopySelectedDescriptions()
    {
        var selected = SelectedRows();
        if (selected.Length == 0)
        {
            HistoryStatus.Announce("Brak wybranego wpisu");
            return;
        }
        var text = string.Join(
            Environment.NewLine + Environment.NewLine,
            selected.Select(row => row.CopyText));
        if (!ClipboardRetry.TrySetText(text, out var error))
        {
            HistoryStatus.Announce(error);
            return;
        }
        HistoryStatus.Announce(selected.Length == 1
            ? "Skopiowano opis"
            : $"Skopiowano opisy: {selected.Length}");
    }

    private void DeleteSelected()
    {
        var selected = SelectedRows();
        if (selected.Length == 0)
        {
            HistoryStatus.Announce("Brak wpisu do usunięcia");
            return;
        }
        var index = HistoryList.SelectedIndex;
        var ids = selected.Select(row => row.Entry.Id).ToHashSet(StringComparer.Ordinal);
        _entries.RemoveAll(entry => ids.Contains(entry.Id));
        Changed = true;
        RefreshStationFilters();
        RefreshRows(fallbackIndex: index);
        FocusSelectedRow();
        HistoryStatus.Announce(selected.Length == 1
            ? "Usunięto wpis z historii rozpoznawania"
            : $"Usunięto wpisy z historii rozpoznawania: {selected.Length}");
    }

    private async Task RequestSelectedStreamingActionAsync(RecognitionHistoryRequestKind kind)
    {
        if (HistoryList.SelectedItem is not RecognitionHistoryRow row)
        {
            HistoryStatus.Announce("Brak wybranego wpisu");
            return;
        }
        await RequestStreamingActionAsync(row, _defaultService, kind);
    }

    private async Task RequestStreamingActionAsync(
        RecognitionHistoryRow row,
        RecognizedTrackStreamingService service,
        RecognitionHistoryRequestKind kind)
    {
        var resolution = await ResolveAsync(row.Entry, service);
        if (resolution is null) return;
        if (kind == RecognitionHistoryRequestKind.OpenAlbum && resolution.Album is null)
        {
            HistoryStatus.Announce("Dopasowany utwór nie zawiera dostępnego albumu");
            return;
        }
        if (kind == RecognitionHistoryRequestKind.OpenArtist && resolution.Artist is null)
        {
            HistoryStatus.Announce("Dopasowany utwór nie zawiera dostępnego wykonawcy");
            return;
        }
        if (kind == RecognitionHistoryRequestKind.OpenAlbumInOriginalApplication
            && resolution.Album is null)
        {
            HistoryStatus.Announce("Dopasowany utwór nie zawiera dostępnego albumu");
            return;
        }
        RequestedAction = new RecognitionHistoryRequest(kind, row.Entry, resolution, null);
        Close();
    }

    private async Task<RecognitionResolutionResult?> ResolveAsync(
        RadioRecognizedTrackSettings entry,
        RecognizedTrackStreamingService service)
    {
        if (_streamingResolver is null)
        {
            HistoryStatus.Announce("Integracja z usługami strumieniowymi nie jest dostępna");
            return null;
        }
        _busy = true;
        try
        {
            if (!_streamingResolver.HasCachedMatch(entry, service))
                HistoryStatus.Announce($"Szukam utworu w {RecognizedTrackStreamingServiceRules.GetLabel(service)}");
            var result = await _streamingResolver.ResolveAsync(
                entry, service, _lifetimeCancellation.Token);
            Changed |= result.CacheChanged;
            return result;
        }
        catch (OperationCanceledException) when (_lifetimeCancellation.IsCancellationRequested)
        {
            return null;
        }
        catch (Exception exception) when (exception is InvalidOperationException
                                           or IOException
                                           or HttpRequestException
                                           or JsonException)
        {
            HistoryStatus.Announce(exception.Message);
            return null;
        }
        finally
        {
            _busy = false;
        }
    }

    private async Task CopyDefaultServiceLinksAsync()
    {
        var selected = SelectedRows();
        if (selected.Length == 0)
        {
            HistoryStatus.Announce("Brak wybranego wpisu");
            return;
        }
        var links = new List<string>();
        foreach (var row in selected)
        {
            var resolution = await ResolveAsync(row.Entry, _defaultService);
            if (resolution is null) return;
            if (!string.IsNullOrWhiteSpace(resolution.Track.PublicUri))
                links.Add(resolution.Track.PublicUri);
        }
        if (links.Count == 0)
        {
            HistoryStatus.Announce("Nie znaleziono łącza do utworu");
            return;
        }
        if (!ClipboardRetry.TrySetText(string.Join(Environment.NewLine, links), out var error))
        {
            HistoryStatus.Announce(error);
            return;
        }
        HistoryStatus.Announce(links.Count == 1
            ? $"Skopiowano łącze do utworu w {RecognizedTrackStreamingServiceRules.GetLabel(_defaultService)}"
            : $"Skopiowano łącza do utworów: {links.Count}");
    }

    private void AnnounceQuickInformation()
    {
        if (HistoryList.SelectedItem is not RecognitionHistoryRow row)
        {
            HistoryStatus.Announce("Brak wybranego wpisu");
            return;
        }
        HistoryStatus.Announce(row.QuickInformation);
    }

    private void ShowActionsMenu(RecognitionActionMenuScope scope)
    {
        if (HistoryList.SelectedItem is not RecognitionHistoryRow row)
        {
            HistoryStatus.Announce("Brak wybranego wpisu");
            return;
        }

        var actions = BuildRecognitionActions(row, scope);
        if (actions.Count == 0)
        {
            HistoryStatus.Announce("Brak dostępnych działań dla tego utworu");
            return;
        }

        var menu = new ContextMenu
        {
            PlacementTarget = HistoryList,
            Placement = System.Windows.Controls.Primitives.PlacementMode.Relative,
            HorizontalOffset = 24,
            VerticalOffset = Math.Max(0, HistoryList.ActualHeight / 3)
        };
        AutomationProperties.SetName(menu, scope == RecognitionActionMenuScope.Quick
            ? $"Najważniejsze działania dla utworu {row.Entry.Title}"
            : $"Wszystkie działania dla utworu {row.Entry.Title}");
        foreach (var action in actions)
            menu.Items.Add(CreateRecognitionActionMenuItem(row, action));
        menu.PreviewKeyDown += RecognitionActionsMenu_PreviewKeyDown;
        menu.Opened += (_, _) =>
        {
            if (menu.Items[0] is MenuItem first)
            {
                first.Focus();
                Keyboard.Focus(first);
            }
        };
        menu.Closed += (_, _) =>
        {
            if (IsVisible)
                Dispatcher.BeginInvoke(FocusSelectedRow, DispatcherPriority.ContextIdle);
        };
        MenuAccessibility.UpdateVisibleItemSetMetadata(menu);
        menu.IsOpen = true;
    }

    internal IReadOnlyList<RecognitionMenuAction> BuildRecognitionActions(
        RecognitionHistoryRow row,
        RecognitionActionMenuScope scope)
    {
        var actions = new List<RecognitionMenuAction>();
        if (scope == RecognitionActionMenuScope.Quick)
        {
            AddQuickRecognitionActions(actions, row);
            return actions;
        }

        foreach (var service in ServicesInMenuOrder())
        {
            if (_streamingResolver is null || !_streamingResolver.IsAvailable(service))
            {
                continue;
            }
            var serviceLabel = RecognizedTrackStreamingServiceRules.GetLabel(service);
            actions.Add(new RecognitionMenuAction(
                service == RecognizedTrackStreamingService.Tidal
                    ? "TIDAL — odtwórz w oryginalnej aplikacji"
                    : "Spotify — pokaż utwór w AMC",
                service,
                service == RecognizedTrackStreamingService.Tidal
                    ? RecognitionHistoryRequestKind.PlayTrack
                    : RecognitionHistoryRequestKind.ShowTrackInAmc,
                null));
            if (service == RecognizedTrackStreamingService.Tidal)
            {
                actions.Add(new RecognitionMenuAction(
                    "TIDAL — pokaż utwór w AMC",
                    service, RecognitionHistoryRequestKind.ShowTrackInAmc, null));
            }
            var albumLabel = string.IsNullOrWhiteSpace(row.Entry.Album)
                ? "Album utworu"
                : row.Entry.Album;
            actions.Add(new RecognitionMenuAction(
                $"{albumLabel} — album w {serviceLabel}",
                service, RecognitionHistoryRequestKind.OpenAlbum, null));
            if (!string.IsNullOrWhiteSpace(row.Entry.Artist))
            {
                actions.Add(new RecognitionMenuAction(
                    $"{row.Entry.Artist} — wykonawca w {serviceLabel}",
                    service, RecognitionHistoryRequestKind.OpenArtist, null));
            }
            if (service == RecognizedTrackStreamingService.Spotify)
            {
                actions.Add(new RecognitionMenuAction(
                    "Spotify — utwór w oryginalnej aplikacji",
                    service, RecognitionHistoryRequestKind.OpenTrackInOriginalApplication, null));
                actions.Add(new RecognitionMenuAction(
                    $"{albumLabel} — album w oryginalnej aplikacji Spotify",
                    service, RecognitionHistoryRequestKind.OpenAlbumInOriginalApplication, null));
            }
        }

        actions.Add(new RecognitionMenuAction(
            "Apple Music — utwór (strona lub aplikacja)",
            null, RecognitionHistoryRequestKind.OpenExternal, null,
            AppleMusicRecognitionTarget.Track));
        var appleAlbumLabel = string.IsNullOrWhiteSpace(row.Entry.Album)
            ? "Album utworu"
            : row.Entry.Album;
        actions.Add(new RecognitionMenuAction(
            $"{appleAlbumLabel} — album w Apple Music (strona lub aplikacja)",
            null, RecognitionHistoryRequestKind.OpenExternal, null,
            AppleMusicRecognitionTarget.Album));
        AddExternalAction(
            actions,
            "Apple Music — wyszukaj w przeglądarce",
            RecognitionLinks.AppleMusicSearch(row.Entry));
        AddExternalAction(actions, "Shazam — wynik rozpoznawania", row.Entry.ProviderUri);
        AddExternalAction(actions, "YouTube Music — wyszukaj", RecognitionLinks.YouTubeMusic(row.Entry));
        AddExternalAction(actions, "Discogs — wyszukaj", RecognitionLinks.Discogs(row.Entry));
        AddExternalAction(actions, "MusicBrainz — wyszukaj", RecognitionLinks.MusicBrainz(row.Entry));
        return actions;
    }

    private void AddQuickRecognitionActions(
        ICollection<RecognitionMenuAction> actions,
        RecognitionHistoryRow row)
    {
        var defaultAvailable = _streamingResolver?.IsAvailable(_defaultService) == true;
        var defaultLabel = RecognizedTrackStreamingServiceRules.GetLabel(_defaultService);
        if (defaultAvailable && !string.IsNullOrWhiteSpace(row.Entry.Artist))
        {
            actions.Add(new RecognitionMenuAction(
                $"{row.Entry.Artist} — wykonawca w {defaultLabel}",
                _defaultService, RecognitionHistoryRequestKind.OpenArtist, null));
        }
        if (defaultAvailable)
        {
            var albumLabel = string.IsNullOrWhiteSpace(row.Entry.Album)
                ? "Album utworu"
                : row.Entry.Album;
            actions.Add(new RecognitionMenuAction(
                $"{albumLabel} — album w {defaultLabel}",
                _defaultService, RecognitionHistoryRequestKind.OpenAlbum, null));
        }
        if (_streamingResolver?.IsAvailable(RecognizedTrackStreamingService.Spotify) == true)
        {
            actions.Add(new RecognitionMenuAction(
                "Spotify — pokaż utwór w AMC",
                RecognizedTrackStreamingService.Spotify,
                RecognitionHistoryRequestKind.ShowTrackInAmc,
                null));
            actions.Add(new RecognitionMenuAction(
                "Spotify — utwór w oryginalnej aplikacji",
                RecognizedTrackStreamingService.Spotify,
                RecognitionHistoryRequestKind.OpenTrackInOriginalApplication,
                null));
        }
        actions.Add(new RecognitionMenuAction(
            "Apple Music — utwór (strona lub aplikacja)",
            null, RecognitionHistoryRequestKind.OpenExternal, null,
            AppleMusicRecognitionTarget.Track));
        if (_streamingResolver?.IsAvailable(RecognizedTrackStreamingService.Tidal) == true)
        {
            actions.Add(new RecognitionMenuAction(
                "TIDAL — pokaż utwór w AMC",
                RecognizedTrackStreamingService.Tidal,
                RecognitionHistoryRequestKind.ShowTrackInAmc,
                null));
            actions.Add(new RecognitionMenuAction(
                "TIDAL — odtwórz w oryginalnej aplikacji",
                RecognizedTrackStreamingService.Tidal,
                RecognitionHistoryRequestKind.PlayTrack,
                null));
        }
    }

    private MenuItem CreateRecognitionActionMenuItem(
        RecognitionHistoryRow row,
        RecognitionMenuAction action)
    {
        var item = new MenuItem { Header = action.Label, Tag = action };
        AutomationProperties.SetName(item, action.Label);
        AutomationProperties.SetHelpText(
            item,
            "Enter otwiera. Ctrl+C kopiuje nazwę. Ctrl+Shift+C kopiuje łącze.");
        item.Click += async (_, _) => await ActivateMenuActionAsync(row, action);
        return item;
    }

    private async void RecognitionActionsMenu_PreviewKeyDown(object sender, KeyEventArgs e)
    {
        if (Keyboard.FocusedElement is not MenuItem item
            || item.Tag is not RecognitionMenuAction action
            || HistoryList.SelectedItem is not RecognitionHistoryRow row)
        {
            return;
        }
        if (e.Key == Key.C && Keyboard.Modifiers == ModifierKeys.Control)
        {
            e.Handled = true;
            CopyText(action.Label, "Skopiowano nazwę");
        }
        else if (e.Key == Key.C
                 && Keyboard.Modifiers == (ModifierKeys.Control | ModifierKeys.Shift))
        {
            e.Handled = true;
            await CopyMenuActionLinkAsync(row, action);
        }
    }

    private IEnumerable<RecognizedTrackStreamingService> ServicesInMenuOrder()
    {
        yield return _defaultService;
        yield return _defaultService == RecognizedTrackStreamingService.Spotify
            ? RecognizedTrackStreamingService.Tidal
            : RecognizedTrackStreamingService.Spotify;
    }

    private static void AddExternalAction(
        ICollection<RecognitionMenuAction> actions,
        string label,
        string? uri)
    {
        if (Uri.TryCreate(uri, UriKind.Absolute, out var parsed)
            && parsed.Scheme is "http" or "https")
        {
            actions.Add(new RecognitionMenuAction(
                label, null, RecognitionHistoryRequestKind.OpenExternal, parsed.AbsoluteUri));
        }
    }

    private async Task ActivateMenuActionAsync(
        RecognitionHistoryRow row,
        RecognitionMenuAction action)
    {
        if (action.AppleMusicTarget is { } appleTarget)
        {
            var link = await ResolveAppleMusicLinkAsync(row.Entry, appleTarget);
            if (link is null) return;
            RequestedAction = new RecognitionHistoryRequest(
                RecognitionHistoryRequestKind.OpenExternal, row.Entry, null, link);
            Close();
            return;
        }
        if (action.Kind == RecognitionHistoryRequestKind.OpenExternal)
        {
            RequestedAction = new RecognitionHistoryRequest(
                action.Kind, row.Entry, null, action.Link);
            Close();
            return;
        }
        if (action.Service is { } service)
            await RequestStreamingActionAsync(row, service, action.Kind);
    }

    private async Task CopyMenuActionLinkAsync(
        RecognitionHistoryRow row,
        RecognitionMenuAction action)
    {
        var link = action.Link;
        if (action.AppleMusicTarget is { } appleTarget)
        {
            link = await ResolveAppleMusicLinkAsync(row.Entry, appleTarget);
            if (link is null) return;
        }
        else if (action.Service is { } service)
        {
            var resolution = await ResolveAsync(row.Entry, service);
            if (resolution is null) return;
            link = action.Kind switch
            {
                RecognitionHistoryRequestKind.PlayTrack => resolution.Track.PublicUri,
                RecognitionHistoryRequestKind.ShowTrackInAmc => resolution.Track.PublicUri,
                RecognitionHistoryRequestKind.OpenAlbum => resolution.Album?.PublicUri,
                RecognitionHistoryRequestKind.OpenArtist => resolution.Artist?.PublicUri,
                RecognitionHistoryRequestKind.OpenTrackInOriginalApplication =>
                    resolution.Track.PublicUri,
                RecognitionHistoryRequestKind.OpenAlbumInOriginalApplication =>
                    resolution.Album?.PublicUri,
                _ => null
            };
        }
        if (string.IsNullOrWhiteSpace(link))
        {
            HistoryStatus.Announce("Ta pozycja nie ma dostępnego łącza");
            return;
        }
        CopyText(link, "Skopiowano łącze");
    }

    private async Task<string?> ResolveAppleMusicLinkAsync(
        RadioRecognizedTrackSettings entry,
        AppleMusicRecognitionTarget target)
    {
        if (_appleMusicLinkResolver is null)
        {
            HistoryStatus.Announce("Wyszukiwanie łączy Apple Music nie jest dostępne");
            return null;
        }
        _busy = true;
        try
        {
            if (!_appleMusicLinkResolver.HasCachedMatch(entry))
                HistoryStatus.Announce("Szukam utworu w Apple Music");
            var result = await _appleMusicLinkResolver.ResolveAsync(
                entry, _lifetimeCancellation.Token);
            Changed |= result.CacheChanged;
            var link = target == AppleMusicRecognitionTarget.Track
                ? result.TrackLink
                : result.AlbumLink;
            if (string.IsNullOrWhiteSpace(link))
            {
                HistoryStatus.Announce(target == AppleMusicRecognitionTarget.Album
                    ? "Dopasowany utwór nie zawiera dostępnego łącza do albumu w Apple Music"
                    : "Nie znaleziono łącza do utworu w Apple Music");
                return null;
            }
            return link;
        }
        catch (OperationCanceledException) when (_lifetimeCancellation.IsCancellationRequested)
        {
            return null;
        }
        catch (Exception exception) when (exception is InvalidOperationException
                                           or IOException
                                           or HttpRequestException
                                           or JsonException)
        {
            HistoryStatus.Announce(exception.Message);
            return null;
        }
        finally
        {
            _busy = false;
        }
    }

    private void CopyText(string text, string message)
    {
        if (!ClipboardRetry.TrySetText(text, out var error))
        {
            HistoryStatus.Announce(error);
            return;
        }
        HistoryStatus.Announce(message);
    }

    private void MoveSelected(int direction)
    {
        var selectedRows = SelectedRows();
        if (selectedRows.Length == 0)
        {
            HistoryStatus.Announce("Brak wybranego wpisu");
            return;
        }
        var focusedId = (HistoryList.SelectedItem as RecognitionHistoryRow)?.Entry.Id;
        var selectedIds = selectedRows.Select(row => row.Entry.Id).ToHashSet(StringComparer.Ordinal);
        var reorderedVisible = _rows.ToList();
        RecognitionHistoryRow? neighbor = null;
        if (direction < 0)
        {
            for (var index = 1; index < reorderedVisible.Count; index++)
            {
                if (!selectedIds.Contains(reorderedVisible[index].Entry.Id)
                    || selectedIds.Contains(reorderedVisible[index - 1].Entry.Id)) continue;
                neighbor ??= reorderedVisible[index - 1];
                (reorderedVisible[index - 1], reorderedVisible[index]) =
                    (reorderedVisible[index], reorderedVisible[index - 1]);
            }
        }
        else
        {
            for (var index = reorderedVisible.Count - 2; index >= 0; index--)
            {
                if (!selectedIds.Contains(reorderedVisible[index].Entry.Id)
                    || selectedIds.Contains(reorderedVisible[index + 1].Entry.Id)) continue;
                neighbor ??= reorderedVisible[index + 1];
                (reorderedVisible[index], reorderedVisible[index + 1]) =
                    (reorderedVisible[index + 1], reorderedVisible[index]);
            }
        }
        if (neighbor is null)
        {
            HistoryStatus.Announce(direction < 0 ? "To już pierwszy wpis" : "To już ostatni wpis");
            return;
        }

        var visiblePositions = _entries
            .Select((entry, index) => (entry, index))
            .Where(pair => _rows.Any(row => ReferenceEquals(row.Entry, pair.entry)))
            .Select(pair => pair.index)
            .ToArray();
        for (var index = 0; index < visiblePositions.Length; index++)
            _entries[visiblePositions[index]] = reorderedVisible[index].Entry;

        Changed = true;
        RefreshRows(focusedId);
        HistoryList.UnselectAll();
        foreach (var item in HistoryList.Items.OfType<RecognitionHistoryRow>())
        {
            if (selectedIds.Contains(item.Entry.Id)) HistoryList.SelectedItems.Add(item);
        }
        FocusSelectedRow();
        HistoryStatus.Announce(direction < 0
            ? $"Nad {neighbor.Label}"
            : $"Pod {neighbor.Label}");
    }

    private void Export()
    {
        if (_entries.Count == 0)
        {
            HistoryStatus.Announce("Historia jest pusta");
            return;
        }
        var dialog = new SaveFileDialog
        {
            Title = "Eksportuj rozpoznane utwory",
            Filter = "Plik JSON (*.json)|*.json|Plik CSV (*.csv)|*.csv",
            DefaultExt = ".json",
            AddExtension = true,
            FileName = $"AMC - rozpoznane utwory - {DateTime.Now:yyyy-MM-dd}"
        };
        if (dialog.ShowDialog(this) != true)
        {
            FocusSelectedRow();
            return;
        }
        try
        {
            var ordered = _entries.ToArray();
            if (string.Equals(Path.GetExtension(dialog.FileName), ".csv", StringComparison.OrdinalIgnoreCase))
            {
                var lines = new List<string>
                {
                    "data;stacja;tytuł;wykonawca;album;wydanie;Spotify;TIDAL;Apple Music;YouTube Music;Discogs;MusicBrainz"
                };
                lines.AddRange(ordered.Select(entry => string.Join(';', new[]
                {
                    new DateTime(entry.RecognizedUtcTicks, DateTimeKind.Utc).ToLocalTime().ToString("yyyy-MM-dd HH:mm:ss"),
                    entry.StationName,
                    entry.Title,
                    entry.Artist,
                    entry.Album,
                    entry.ReleaseDate,
                    RecognitionLinks.SpotifyTrackOrSearch(entry),
                    RecognitionLinks.TidalTrackOrSearch(entry),
                    RecognitionLinks.AppleMusicTrackOrSearch(entry),
                    RecognitionLinks.YouTubeMusic(entry),
                    RecognitionLinks.Discogs(entry),
                    RecognitionLinks.MusicBrainz(entry)
                }.Select(Csv))));
                File.WriteAllLines(dialog.FileName, lines, new UTF8Encoding(encoderShouldEmitUTF8Identifier: true));
            }
            else
            {
                var export = ordered.Select(entry => new
                {
                    recognizedAt = new DateTime(entry.RecognizedUtcTicks, DateTimeKind.Utc).ToLocalTime(),
                    station = entry.StationName,
                    title = entry.Title,
                    artist = entry.Artist,
                    album = entry.Album,
                    releaseDate = entry.ReleaseDate,
                    recognitionProviderUrl = entry.ProviderUri,
                    serviceSearch = new
                    {
                        spotify = RecognitionLinks.SpotifyTrackOrSearch(entry),
                        tidal = RecognitionLinks.TidalTrackOrSearch(entry),
                        appleMusic = RecognitionLinks.AppleMusicTrackOrSearch(entry),
                        youtubeMusic = RecognitionLinks.YouTubeMusic(entry)
                    },
                    catalogueSearch = new
                    {
                        discogs = RecognitionLinks.Discogs(entry),
                        musicBrainz = RecognitionLinks.MusicBrainz(entry)
                    }
                });
                File.WriteAllText(
                    dialog.FileName,
                    JsonSerializer.Serialize(export, new JsonSerializerOptions { WriteIndented = true }),
                    new UTF8Encoding(encoderShouldEmitUTF8Identifier: true));
            }
            HistoryStatus.Announce($"Wyeksportowano historię: {Path.GetFileName(dialog.FileName)}");
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException)
        {
            HistoryStatus.Announce($"Nie udało się zapisać pliku: {exception.Message}");
        }
        FocusSelectedRow();
    }

    private static string Csv(string value) => $"\"{value.Replace("\"", "\"\"")}\"";

    private void Copy_Click(object sender, RoutedEventArgs e) => CopySelectedDescriptions();
    private async void CopyTrackLink_Click(object sender, RoutedEventArgs e) =>
        await CopyDefaultServiceLinksAsync();
    private async void OpenTrack_Click(object sender, RoutedEventArgs e) =>
        await RequestSelectedStreamingActionAsync(RecognitionHistoryRequestKind.PlayTrack);
    private async void OpenAlbum_Click(object sender, RoutedEventArgs e) =>
        await RequestSelectedStreamingActionAsync(RecognitionHistoryRequestKind.OpenAlbum);
    private void MoveUp_Click(object sender, RoutedEventArgs e) => MoveSelected(-1);
    private void MoveDown_Click(object sender, RoutedEventArgs e) => MoveSelected(1);
    private void Export_Click(object sender, RoutedEventArgs e) => Export();
    private void Delete_Click(object sender, RoutedEventArgs e) => DeleteSelected();

    private void HistoryContextMenu_Opened(object sender, RoutedEventArgs e)
    {
        var selectedRow = HistoryList.SelectedItem as RecognitionHistoryRow;
        var hasSelection = selectedRow is not null;
        var hasDefaultService = selectedRow is not null
            && _streamingResolver is not null
            && _streamingResolver.IsAvailable(_defaultService);
        var canCopyDefaultLink = hasDefaultService
            || selectedRow is not null
            && _streamingResolver is not null
            && _streamingResolver.HasCachedMatch(selectedRow.Entry, _defaultService);
        var service = RecognizedTrackStreamingServiceRules.GetLabel(_defaultService);
        SetMenuItem(OpenTrackMenuItem, $"_Odtwórz utwór w {service}",
            RecognitionHistoryCommandCatalog.Shortcut(RecognitionHistoryCommandId.OpenTrack), hasDefaultService);
        SetMenuItem(OpenAlbumMenuItem, $"_Pokaż album w {service}",
            RecognitionHistoryCommandCatalog.Shortcut(RecognitionHistoryCommandId.OpenAlbum),
            hasDefaultService);
        ShowActionsMenuItem.Header = "_Usługi, łącza i powiązania";
        ShowActionsMenuItem.InputGestureText = string.Empty;
        ShowActionsMenuItem.IsEnabled = hasSelection;
        ShowActionsMenuItem.Items.Clear();
        if (selectedRow is not null)
        {
            foreach (var action in BuildRecognitionActions(
                         selectedRow, RecognitionActionMenuScope.Full))
            {
                ShowActionsMenuItem.Items.Add(
                    CreateRecognitionActionMenuItem(selectedRow, action));
            }
        }
        AutomationProperties.SetName(ShowActionsMenuItem, "Usługi, łącza i powiązania");
        AutomationProperties.SetAcceleratorKey(ShowActionsMenuItem, string.Empty);
        AutomationProperties.SetHelpText(
            ShowActionsMenuItem,
            "Rozwiń, aby wybrać pełną listę usług i publicznych łączy.");
        SetMenuItem(CopyDescriptionMenuItem, "_Kopiuj opis",
            RecognitionHistoryCommandCatalog.Shortcut(RecognitionHistoryCommandId.CopyDescription), hasSelection);
        SetMenuItem(CopyTrackLinkMenuItem, $"Kopiuj łą_cze do utworu w {service}",
            RecognitionHistoryCommandCatalog.Shortcut(RecognitionHistoryCommandId.CopyTrackLink), canCopyDefaultLink);
        SetMenuItem(MoveUpMenuItem, "Przenieś _wyżej",
            RecognitionHistoryCommandCatalog.Shortcut(RecognitionHistoryCommandId.MoveUp),
            hasSelection && HistoryList.SelectedIndex > 0);
        SetMenuItem(MoveDownMenuItem, "Przenieś _niżej",
            RecognitionHistoryCommandCatalog.Shortcut(RecognitionHistoryCommandId.MoveDown),
            hasSelection && HistoryList.SelectedIndex >= 0
            && HistoryList.SelectedIndex < _rows.Count - 1);
        SetMenuItem(DeleteMenuItem, "_Usuń",
            RecognitionHistoryCommandCatalog.Shortcut(RecognitionHistoryCommandId.Delete), hasSelection);
        MenuAccessibility.UpdateVisibleItemSetMetadata(HistoryContextMenu);
    }

    private static void SetMenuItem(
        MenuItem item,
        string header,
        string gesture,
        bool enabled)
    {
        item.Header = header;
        item.InputGestureText = gesture;
        item.IsEnabled = enabled;
        var name = header.Replace("_", string.Empty);
        AutomationProperties.SetName(item, name);
        AutomationProperties.SetHelpText(item, $"Skrót: {gesture}");
        AutomationProperties.SetAcceleratorKey(item, gesture);
    }

    private void Window_Closed(object? sender, EventArgs e)
    {
        _lifetimeCancellation.Cancel();
        _lifetimeCancellation.Dispose();
    }
}

internal sealed record RecognitionStationFilter(string? Key, string Label)
{
    public string NavigationText => Label;

    public static string KeyFor(RadioRecognizedTrackSettings entry) =>
        string.IsNullOrWhiteSpace(entry.StationId)
            ? $"name:{entry.StationName.Trim()}"
            : $"id:{entry.StationId.Trim()}";

    public override string ToString() => Label;
}

internal sealed class RecognitionHistoryRow(RadioRecognizedTrackSettings entry)
{
    public RadioRecognizedTrackSettings Entry { get; } = entry;
    private DateTime LocalTime => new DateTime(Entry.RecognizedUtcTicks, DateTimeKind.Utc).ToLocalTime();
    private string Track => string.Join(" — ", new[] { Entry.Title, Entry.Artist }
        .Where(value => !string.IsNullOrWhiteSpace(value)));

    public string Label => $"{Track}, {Entry.StationName}, {LocalTime:yyyy-MM-dd HH:mm}";
    public string NavigationText => $"{Entry.Title} {Entry.Artist} {Entry.Album} {Entry.StationName}";
    public string CopyText => string.Join(Environment.NewLine, new[]
    {
        $"Tytuł: {Entry.Title}",
        $"Wykonawca: {Entry.Artist}",
        string.IsNullOrWhiteSpace(Entry.Album) ? null : $"Album: {Entry.Album}",
        string.IsNullOrWhiteSpace(Entry.ReleaseDate) ? null : $"Wydanie: {Entry.ReleaseDate}",
        $"Stacja: {Entry.StationName}",
        $"Rozpoznano: {LocalTime:yyyy-MM-dd HH:mm:ss}",
        $"Apple Music: {RecognitionLinks.AppleMusicTrackOrSearch(Entry)}",
        $"Spotify: {RecognitionLinks.SpotifyTrackOrSearch(Entry)}",
        $"TIDAL: {RecognitionLinks.TidalTrackOrSearch(Entry)}",
        $"YouTube Music: {RecognitionLinks.YouTubeMusic(Entry)}",
        $"Discogs: {RecognitionLinks.Discogs(Entry)}",
        $"MusicBrainz: {RecognitionLinks.MusicBrainz(Entry)}"
    }.Where(line => line is not null));

    public string QuickInformation => string.Join(", ", new[]
    {
        $"Tytuł: {Entry.Title}",
        string.IsNullOrWhiteSpace(Entry.Artist) ? null : $"Wykonawca: {Entry.Artist}",
        string.IsNullOrWhiteSpace(Entry.Album) ? null : $"Album: {Entry.Album}",
        $"Stacja: {Entry.StationName}"
    }.Where(value => value is not null));

    public override string ToString() => Label;
}

internal static class RecognitionLinks
{
    private static string Query(RadioRecognizedTrackSettings entry) =>
        Uri.EscapeDataString(string.Join(' ', new[] { entry.Artist, entry.Title }
            .Where(value => !string.IsNullOrWhiteSpace(value))));

    public static string SpotifySearch(RadioRecognizedTrackSettings entry) =>
        $"https://open.spotify.com/search/{Query(entry)}";

    public static string TidalSearch(RadioRecognizedTrackSettings entry) =>
        $"https://listen.tidal.com/search?q={Query(entry)}";

    public static string SpotifyTrackOrSearch(RadioRecognizedTrackSettings entry) =>
        ValidPublicUri(entry.SpotifyMatch?.TrackPublicUri) ?? SpotifySearch(entry);

    public static string TidalTrackOrSearch(RadioRecognizedTrackSettings entry) =>
        ValidPublicUri(entry.TidalMatch?.TrackPublicUri) ?? TidalSearch(entry);

    public static string AppleMusicSearch(RadioRecognizedTrackSettings entry) =>
        $"https://music.apple.com/search?term={Query(entry)}";

    public static string AppleMusicTrackOrSearch(RadioRecognizedTrackSettings entry) =>
        ValidPublicUri(entry.AppleMusicMatch?.TrackPublicUri) ?? AppleMusicSearch(entry);

    public static string YouTubeMusic(RadioRecognizedTrackSettings entry) =>
        $"https://music.youtube.com/search?q={Query(entry)}";

    public static string Discogs(RadioRecognizedTrackSettings entry) =>
        $"https://www.discogs.com/search/?q={Query(entry)}&type=all";

    public static string MusicBrainz(RadioRecognizedTrackSettings entry) =>
        $"https://musicbrainz.org/search?query={Query(entry)}&type=recording&method=indexed";

    private static string? ValidPublicUri(string? value) =>
        Uri.TryCreate(value, UriKind.Absolute, out var uri)
        && uri.Scheme is "http" or "https"
            ? uri.AbsoluteUri
            : null;
}

internal enum RecognitionHistoryRequestKind
{
    PlayTrack,
    ShowTrackInAmc,
    OpenAlbum,
    OpenArtist,
    OpenTrackInOriginalApplication,
    OpenAlbumInOriginalApplication,
    OpenExternal
}

internal enum AppleMusicRecognitionTarget
{
    Track,
    Album
}

internal enum RecognitionActionMenuScope
{
    Quick,
    Full
}

internal sealed record RecognitionHistoryRequest(
    RecognitionHistoryRequestKind Kind,
    RadioRecognizedTrackSettings Entry,
    RecognitionResolutionResult? Resolution,
    string? ExternalUri);

internal sealed record RecognitionMenuAction(
    string Label,
    RecognizedTrackStreamingService? Service,
    RecognitionHistoryRequestKind Kind,
    string? Link,
    AppleMusicRecognitionTarget? AppleMusicTarget = null);

internal static class RecognitionHistoryCommandCatalog
{
    private static readonly IReadOnlyDictionary<(Key, ModifierKeys), RecognitionHistoryCommandId>
        KeyMap = new Dictionary<(Key, ModifierKeys), RecognitionHistoryCommandId>
        {
            [(Key.Enter, ModifierKeys.None)] = RecognitionHistoryCommandId.OpenTrack,
            [(Key.Enter, ModifierKeys.Control)] = RecognitionHistoryCommandId.OpenAlbum,
            [(Key.Right, ModifierKeys.None)] = RecognitionHistoryCommandId.ShowActions,
            [(Key.Left, ModifierKeys.None)] = RecognitionHistoryCommandId.QuickInformation,
            [(Key.C, ModifierKeys.Control)] = RecognitionHistoryCommandId.CopyDescription,
            [(Key.C, ModifierKeys.Control | ModifierKeys.Shift)] = RecognitionHistoryCommandId.CopyTrackLink,
            [(Key.Up, ModifierKeys.Alt)] = RecognitionHistoryCommandId.MoveUp,
            [(Key.Down, ModifierKeys.Alt)] = RecognitionHistoryCommandId.MoveDown,
            [(Key.Delete, ModifierKeys.None)] = RecognitionHistoryCommandId.Delete
        };

    public static RecognitionHistoryCommandSpec? Resolve(Key key, ModifierKeys modifiers) =>
        KeyMap.TryGetValue((key, modifiers), out var id)
            ? RecognitionHistoryCommands.Definitions.First(definition => definition.Id == id)
            : null;

    public static string Shortcut(RecognitionHistoryCommandId id) =>
        RecognitionHistoryCommands.Definitions.First(definition => definition.Id == id).Shortcut;

    public static string Instructions(RecognizedTrackStreamingService defaultService)
    {
        var service = RecognizedTrackStreamingServiceRules.GetLabel(defaultService);
        return string.Join(". ", RecognitionHistoryCommands.Definitions.Select(command =>
            command.Id switch
            {
                RecognitionHistoryCommandId.OpenTrack =>
                    $"{command.Shortcut}: odtwórz w {service}",
                RecognitionHistoryCommandId.OpenAlbum =>
                    $"{command.Shortcut}: pokaż album w {service} w AMC i ustaw fokus na rozpoznanym utworze",
                RecognitionHistoryCommandId.ShowActions =>
                    $"{command.Shortcut}: pokaż najważniejsze działania",
                _ => $"{command.Shortcut}: {command.Name.ToLowerInvariant()}"
            })) + ".";
    }
}
