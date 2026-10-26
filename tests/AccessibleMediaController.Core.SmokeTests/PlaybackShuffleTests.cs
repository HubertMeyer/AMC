using AccessibleMediaController.Core.Commands;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Input;
using AccessibleMediaController.Core.Playback;
using AccessibleMediaController.Core.Presentation;
using AccessibleMediaController.Core.Sessions;

internal static class PlaybackShuffleTests
{
    public static void Run()
    {
        PolicyIsLimitedToRequestedSessions();
        ShuffleKeepsCurrentAndRestoresOriginalOrder();
        ManualAndAutomaticNavigationUseShuffledOrder();
        QueueKeepsPriorityOverShuffle();
        SessionSettingPersistsAndIsNormalized();
        CommandSurfacesStayInParity();
        Console.WriteLine(
            "OK: odtwarzanie losowe działa w lokalnych, podcastach i Spotify; kolejka ma pierwszeństwo, a R jest w pomocy");
    }

    private static void PolicyIsLimitedToRequestedSessions()
    {
        Assert(PlaybackShufflePolicy.SupportsSession("local"), "Brak losowania w plikach lokalnych.");
        Assert(PlaybackShufflePolicy.SupportsSession("podcasts"), "Brak losowania w podcastach.");
        Assert(PlaybackShufflePolicy.SupportsSession("spotify"), "Brak losowania w Spotify.");
        Assert(!PlaybackShufflePolicy.SupportsSession("radio"), "R w Radiu nie może utracić nagrywania.");
        Assert(!PlaybackShufflePolicy.SupportsSession("wiim"), "R w WiiM nie może utracić trybu powtarzania.");
        Assert(!PlaybackShufflePolicy.SupportsSession("appleMusic"), "Prototyp Apple Music nie może reklamować niepodpiętego losowania.");
    }

    private static void ShuffleKeepsCurrentAndRestoresOriginalOrder()
    {
        var items = CreateItems();
        var original = items.Select(item => item.Id).ToArray();
        var session = new DemoMediaSession("local", "Pliki lokalne", items, shuffleRandom: new Random(1729));
        session.Play(items[2]);

        Assert(session.SetShuffleEnabled(true), "Włączenie losowania nie zmieniło stanu sesji.");
        Assert(session.PlaybackContextItemIds[0] == items[2].Id,
            "Bieżący element nie pozostał pierwszy po włączeniu losowania.");
        Assert(session.PlaybackContextItemIds.Count == original.Length
               && session.PlaybackContextItemIds.Distinct(StringComparer.Ordinal).Count() == original.Length
               && session.PlaybackContextItemIds.ToHashSet(StringComparer.Ordinal).SetEquals(original),
            "Losowanie zgubiło albo powieliło element kontekstu.");

        session.SetShuffleEnabled(false);
        Assert(session.PlaybackContextItemIds.SequenceEqual(original, StringComparer.Ordinal),
            "Wyłączenie losowania nie przywróciło pierwotnej kolejności.");
    }

    private static void ManualAndAutomaticNavigationUseShuffledOrder()
    {
        var items = CreateItems();
        var manual = new DemoMediaSession("podcasts", "Podcasty", items, shuffleRandom: new Random(42));
        manual.Play(items[0]);
        manual.SetShuffleEnabled(true);
        var expectedManualNext = manual.PlaybackContextItemIds[1];
        Assert(manual.PlayRelative(1) && manual.CurrentItem.Id == expectedManualNext,
            "Page Down nie przeszedł do następnego elementu w kolejności losowej.");
        Assert(manual.PlayRelative(-1) && manual.CurrentItem.Id == items[0].Id,
            "Page Up nie wrócił do poprzedniego elementu w kolejności losowej.");

        var automatic = new DemoMediaSession("spotify", "Spotify", CreateItems(), shuffleRandom: new Random(42));
        automatic.Play(automatic.Items[0]);
        automatic.SetShuffleEnabled(true);
        var expectedAutomaticNext = automatic.PlaybackContextItemIds[1];
        var next = automatic.ContinueAfterPlaybackEnded(automatic.CurrentItem);
        Assert(next?.Id == expectedAutomaticNext,
            "Automatyczne zakończenie nie przeszło do następnego elementu w kolejności losowej.");
    }

    private static void QueueKeepsPriorityOverShuffle()
    {
        var items = CreateItems();
        var session = new DemoMediaSession("local", "Pliki lokalne", items, shuffleRandom: new Random(7));
        session.Play(items[0]);
        session.SetShuffleEnabled(true);
        var queued = items[^1];
        queued.IsPlayNext = true;
        queued.IsInQueue = true;
        session.SetQueueOrder([queued.Id]);

        var next = session.ContinueAfterPlaybackEnded(items[0]);
        Assert(next?.Id == queued.Id,
            "Element Odtwórz jako następne nie zachował pierwszeństwa przed kolejnością losową.");
    }

    private static void SessionSettingPersistsAndIsNormalized()
    {
        var settings = new AppSettings();
        var manager = new SessionManager(settings);
        var local = manager.AddOrUpdateTransientSession(
            "local",
            "Pliki lokalne",
            CreateItems(),
            output: null,
            preferredSlot: 1).Session;
        manager.SelectSession(local.Id);
        Assert(manager.ToggleCurrentSessionShuffle() == true
               && settings.ShuffleEnabledBySession.GetValueOrDefault("local"),
            "Menedżer sesji nie zapisał włączenia losowania.");

        var directory = Path.Combine(Path.GetTempPath(), $"amc-shuffle-{Guid.NewGuid():N}");
        Directory.CreateDirectory(directory);
        try
        {
            var store = new ConfigurationStore(Path.Combine(directory, "state.json"));
            var state = ConfigurationStore.CreateDefaultState();
            state.Settings.ShuffleEnabledBySession["local"] = true;
            store.Save(state);
            var loaded = store.LoadOrCreate();
            Assert(loaded.Settings.ShuffleEnabledBySession.GetValueOrDefault("local"),
                "Ustawienie losowania nie przetrwało zapisu konfiguracji.");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    private static void CommandSurfacesStayInParity()
    {
        Assert(CommandCatalog.GetDisplayName(CommandIds.ToggleShuffle)
               == "Włącz lub wyłącz odtwarzanie losowe",
            "Katalog poleceń nie ma użytkowej nazwy losowania.");
        var palette = CommandPaletteSearch.CreateEntries(
            KeyboardProfile.CreateDefault(),
            new AppSettings(),
            includeCommandPalette: true);
        var entry = palette.Single(candidate => candidate.CommandId == CommandIds.ToggleShuffle);
        Assert(entry.LocalShortcut == "R (odtwarzacz lokalny, podcasty lub Spotify)",
            "Paleta poleceń nie podaje kontekstu skrótu R.");
        var help = ShortcutHelpCatalog.Create(KeyboardProfile.CreateDefault(), new AppSettings());
        Assert(help.SelectMany(section => section.Entries).Any(candidate =>
                candidate.CommandId == CommandIds.ToggleShuffle
                && candidate.Shortcut == "R"
                && candidate.Context.Contains("Spotify", StringComparison.Ordinal)),
            "Pełna pomoc klawiatury nie zawiera kontekstowego skrótu R.");
    }

    private static List<MediaItem> CreateItems() =>
        Enumerable.Range(1, 6)
            .Select(index => new MediaItem
            {
                Id = $"item-{index}",
                Title = $"Element {index}",
                Duration = TimeSpan.FromMinutes(index)
            })
            .ToList();

    private static void Assert(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
}
