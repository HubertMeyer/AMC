using System.Windows;
using System.Windows.Automation;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Threading;
using AccessibleMediaController.Core.Commands;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Input;
using AccessibleMediaController.Core.Podcasts;
using AccessibleMediaController.Core.Presentation;
using AccessibleMediaController.Windows;
using AccessibleMediaController.Windows.Services;

internal static class PodcastSourceWindowTests
{
    private const string SourceAddress = "https://www.youtube.com/@WieniawskiSociety";
    private const string NormalizedAddress = "https://www.youtube.com/%40WieniawskiSociety/videos";
    private const string ChannelId = "UCpFEKtbJxKnsOcraylnuNsA";

    internal static void Run() => OnSta(RunSta);

    private static void RunSta()
    {
        var fetchCount = 0;
        Uri? requestedAddress = null;
        Exception? dialogFailure = null;
        TaskCompletionSource<YouTubeCollectionDocument>? pendingCollection = null;
        var window = new PodcastSourceWindow(
            (address, _) => address.Host.Equals("example.test", StringComparison.OrdinalIgnoreCase)
                ? Task.FromException<PodcastFeedDocument>(new HttpRequestException("Próbny błąd połączenia."))
                : throw new InvalidOperationException("Test kanału YouTube nie może wejść do klienta RSS."),
            (address, _) =>
            {
                fetchCount++;
                requestedAddress = address;
                return pendingCollection?.Task
                    ?? throw new InvalidOperationException("Test nie przygotował odpowiedzi kanału YouTube.");
            },
            (_, _) => throw new InvalidOperationException("Kanał YouTube nie może zostać potraktowany jak pojedynczy materiał."));

        window.Loaded += (_, _) =>
        {
            try
            {
                var address = (TextBox)window.FindName("FeedBox");
                var status = (TextBlock)window.FindName("StatusText");
                var add = (Button)window.FindName("AddButton");

                Check(ReferenceEquals(Keyboard.FocusedElement, address),
                    "Po otwarciu fokus nie stoi na polu adresu.");
                Check(window.FindName("CheckButton") is null,
                    "Okno nadal pokazuje osobny przycisk Sprawdź.");
                Check(add.IsDefault && add.IsEnabled,
                    "Enter od początku nie uruchamia jednoetapowego przycisku Dodaj.");
                Check(AutomationProperties.GetName(add) == "Dodaj źródło",
                    "Przycisk Dodaj nie ma jednoznacznej etykiety dla NVDA.");
                Check(AutomationProperties.GetLiveSetting(status) == AutomationLiveSetting.Assertive,
                    "Stan dodawania nie jest pilnym regionem dla NVDA.");
                Check(AutomationProperties.GetName(status) == "Stan dodawania źródła",
                    "Region komunikatów ma nieaktualną etykietę sprawdzania.");

                address.Text = "niepełny-adres";
                add.RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
                Check(fetchCount == 0 && add.IsDefault && add.IsEnabled,
                    "Nieprawidłowy adres uruchomił sieć albo zablokował ponowną próbę.");
                Check(status.Text.Contains("pełny adres HTTP lub HTTPS", StringComparison.Ordinal)
                      && ReferenceEquals(Keyboard.FocusedElement, address)
                      && address.SelectionLength == address.Text.Length,
                    "Błąd adresu nie został ogłoszony ani przygotowany do poprawienia.");

                address.Text = "https://example.test/feed.xml";
                add.RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
                Check(add.IsDefault && add.IsEnabled
                      && status.Text.Contains("Nie można odczytać kanału", StringComparison.Ordinal)
                      && ReferenceEquals(Keyboard.FocusedElement, address)
                      && address.SelectionLength == address.Text.Length,
                    "Błąd pobierania nie pozostawia aktywnego, dostępnego okna do ponownej próby.");

                pendingCollection = new TaskCompletionSource<YouTubeCollectionDocument>(
                    TaskCreationOptions.RunContinuationsAsynchronously);
                address.Text = SourceAddress;
                add.RaiseEvent(new RoutedEventArgs(Button.ClickEvent));

                Check(fetchCount == 1 && requestedAddress?.AbsoluteUri == NormalizedAddress,
                    "Okno nie przekazało klientowi znormalizowanego adresu kanału YouTube.");
                Check(!add.IsEnabled && !add.IsDefault && !address.IsEnabled,
                    "Podczas sprawdzania przycisk lub pole adresu nadal przyjmuje kolejne polecenia.");
                Check(status.Text.Contains("Sprawdzanie adresu i dodawanie", StringComparison.Ordinal),
                    "NVDA nie otrzymuje komunikatu o jednoetapowym dodawaniu.");
                add.RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
                Check(fetchCount == 1,
                    "Drugi Enter podczas sprawdzania uruchomił drugi import.");

                window.Dispatcher.BeginInvoke(
                    new Action(() => pendingCollection.SetResult(CreateCollection(requestedAddress!))),
                    DispatcherPriority.Background);
            }
            catch (Exception exception)
            {
                dialogFailure = exception;
                window.Close();
            }
        };

        var accepted = window.ShowDialog();
        if (dialogFailure is not null) throw dialogFailure;
        Check(accepted == true && fetchCount == 1,
            "Jedno Dodaj nie sprawdziło i nie zamknęło okna z wynikiem pozytywnym.");
        Check(window.Feed is { Episodes.Count: 1 }
              && window.SourceKind == PodcastSourceKind.YouTubeChannel,
            "Jednoetapowe dodanie utraciło sprawdzony kanał YouTube.");

        VerifyPersistence(window.Feed!);
        VerifyReopeningStartsClean();
        VerifyCommandSurfacesDescribeYouTube();
        Console.WriteLine("OK: Ctrl+N Podcasty i YouTube — jeden Enter sprawdza, dodaje i zapisuje");
    }

    private static YouTubeCollectionDocument CreateCollection(Uri address)
    {
        var episode = new PodcastFeedEpisode(
            "youtube-video:test",
            "test-video",
            "Próbny materiał",
            "Wieniawski Society",
            "Opis próbnego materiału.",
            DateTimeOffset.Parse("2026-10-22T12:00:00+00:00"),
            TimeSpan.FromMinutes(3),
            new Uri("https://www.youtube.com/watch?v=test-video"),
            new Uri("https://www.youtube.com/watch?v=test-video"),
            "audio/webm",
            null);
        var feed = new PodcastFeedDocument(
            $"youtube-channel:{ChannelId}",
            "Wieniawski Society - Videos",
            "Wieniawski Society",
            "Publiczny kanał YouTube.",
            address,
            new Uri(SourceAddress),
            [episode]);
        return new YouTubeCollectionDocument(feed, PodcastSourceKind.YouTubeChannel);
    }

    private static void VerifyPersistence(PodcastFeedDocument feed)
    {
        var directory = Path.Combine(Path.GetTempPath(), $"amc-podcast-source-{Guid.NewGuid():N}");
        Directory.CreateDirectory(directory);
        try
        {
            var store = new ConfigurationStore(
                Path.Combine(directory, "state.json"),
                Path.Combine(directory, "library.db"),
                Path.Combine(directory, "podcasts.db"));
            var state = store.LoadOrCreate();
            PodcastLibraryUpdater.Apply(
                state.Podcasts,
                feed,
                null,
                DateTime.UtcNow,
                state.Bookmarks,
                PodcastSourceKind.YouTubeChannel,
                addToLibrary: true);

            var queue = new StatePersistenceQueue(store);
            queue.Queue(state);
            Check(queue.WaitForIdle(TimeSpan.FromSeconds(10), out var failure),
                $"Zapis kanału w kolejce nie zakończył się: {failure?.Message ?? "brak wyniku"}.");

            var reopened = store.LoadOrCreate();
            var saved = reopened.Podcasts.Subscriptions.SingleOrDefault(subscription =>
                subscription.FeedUrl == NormalizedAddress);
            Check(saved is { IsInLibrary: true, SourceKind: PodcastSourceKind.YouTubeChannel },
                "Po ponownym odczycie bazy nie ma dodanego kanału YouTube w Bibliotece.");
            Check(reopened.Podcasts.Episodes.Any(episode => episode.SubscriptionId == saved!.Id),
                "Po ponownym odczycie bazy kanał nie ma zapisanego materiału.");
        }
        finally
        {
            if (Directory.Exists(directory)) Directory.Delete(directory, recursive: true);
        }
    }

    private static void VerifyReopeningStartsClean()
    {
        Exception? failure = null;
        var window = new PodcastSourceWindow(
            (_, _) => throw new InvalidOperationException(),
            (_, _) => throw new InvalidOperationException(),
            (_, _) => throw new InvalidOperationException());
        window.Loaded += (_, _) =>
        {
            try
            {
                var address = (TextBox)window.FindName("FeedBox");
                var add = (Button)window.FindName("AddButton");
                Check(ReferenceEquals(Keyboard.FocusedElement, address),
                    "Po ponownym otwarciu fokus nie wraca do adresu.");
                Check(window.FindName("CheckButton") is null
                      && add.IsDefault
                      && add.IsEnabled
                      && window.Feed is null,
                    "Ponowne otwarcie nie zaczyna od jednoetapowego Dodaj i pustego stanu.");
            }
            catch (Exception exception)
            {
                failure = exception;
            }
            finally
            {
                window.Close();
            }
        };
        window.ShowDialog();
        if (failure is not null) throw failure;
    }

    private static void VerifyCommandSurfacesDescribeYouTube()
    {
        var commandName = CommandCatalog.GetDisplayName(CommandIds.AddPodcast);
        Check(commandName.Contains("YouTube", StringComparison.Ordinal),
            "Wspólny opis polecenia Ctrl+N pomija YouTube.");

        var help = ShortcutHelpCatalog.Create(KeyboardProfile.CreateDefault(), new AppSettings())
            .SelectMany(section => section.Entries)
            .Single(entry => entry.CommandId == CommandIds.AddPodcast);
        Check(help.DisplayName == commandName
              && help.Shortcut.Contains("Ctrl+N", StringComparison.Ordinal)
              && help.Context.Contains("Podcasty i YouTube", StringComparison.Ordinal),
            "Pomoc klawiatury nie korzysta ze wspólnego opisu Ctrl+N dla Podcastów i YouTube.");

        var palette = CommandPaletteSearch.CreateEntries(
                KeyboardProfile.CreateDefault(),
                new AppSettings(),
                includeCommandPalette: true)
            .Single(entry => entry.CommandId == CommandIds.AddPodcast);
        Check(palette.DisplayName == commandName
              && palette.LocalShortcut?.Contains("Ctrl+N", StringComparison.Ordinal) == true,
            "Paleta poleceń nie korzysta ze wspólnego opisu Ctrl+N dla Podcastów i YouTube.");
    }

    private static void OnSta(Action action)
    {
        Exception? failure = null;
        var thread = new Thread(() =>
        {
            SynchronizationContext.SetSynchronizationContext(new DispatcherSynchronizationContext());
            try
            {
                action();
            }
            catch (Exception exception)
            {
                failure = exception;
            }
            finally
            {
                Dispatcher.CurrentDispatcher.InvokeShutdown();
            }
        }) { IsBackground = true };
        thread.SetApartmentState(ApartmentState.STA);
        thread.Start();
        if (!thread.Join(TimeSpan.FromSeconds(30)))
            throw new TimeoutException("Próba okna dodawania kanału przekroczyła 30 sekund.");
        if (failure is not null) throw new InvalidOperationException("Okno dodawania Podcastów i YouTube", failure);
    }

    private static void Check(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
}
