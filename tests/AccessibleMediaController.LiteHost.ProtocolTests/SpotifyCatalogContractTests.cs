using System.Text.Json;
using AccessibleMediaController.Core.Sessions;
using AccessibleMediaController.LiteHost.Protocol;

namespace AccessibleMediaController.LiteHost.ProtocolTests;

internal static class SpotifyCatalogContractTests
{
    public static void Run()
    {
        CapabilitiesDescribeOneReadOnlySession();
        PlaybackRequestAcceptsOnlyTracksAndEpisodes();
        AccountStatusKeepsCatalogueAndPlaybackSeparate();
        MissingClientIdIsAnExplicitSafeState();
        CollectionRootContainsOnlyUserFacingCategories();
        CollectionViewRequestUsesSafeCumulativePageSizes();
        CollectionViewsKeepUnavailableSavedItems();
        CollectionViewsPageAfterFilteringAndKeepSourceOrder();
        SearchRowsHaveExplicitAccessibleLabelsWithoutPrivateHandles();
        ContainerRequestAcceptsOnlyMatchingSpotifyIdentity();
        ContainerResultNeverUsesIdentifiersInItsHeading();
        ContainerKeepsRepeatedPlaylistOccurrencesDistinct();
        CoordinatorDoesNotAuthenticateForStatusOrCapabilities();
        CoordinatorRedactsCredentialProbeFailure();
        CoordinatorUsesCachedCollectionWithoutAConnection();
        CoordinatorUsesPopulatedCacheImmediatelyWhenConnected();
        CoordinatorRedactsBackendFailures();
        CoordinatorSearchesExactlyOnceWithoutMutatingAnything();
    }

    private static void CapabilitiesDescribeOneReadOnlySession()
    {
        var json = LiteJson.Serialize(LiteSpotifyCatalogContract.CreateCapabilities());
        using var document = JsonDocument.Parse(json);
        var root = document.RootElement;
        Check(root.GetProperty("sessionId").GetString() == "spotify",
            "kontrakt nie wskazuje jednej kanonicznej sesji spotify");
        Check(root.GetProperty("readOnly").GetBoolean(),
            "pierwsza warstwa Spotify nie jest oznaczona jako tylko do odczytu");
        Check(root.GetProperty("oneSession").GetBoolean(),
            "kontrakt nie deklaruje jednej sesji");
        Check(!root.GetProperty("collectionWrite").GetBoolean()
            && !root.GetProperty("login").GetBoolean()
            && root.GetProperty("playback").GetBoolean(),
            "kontrakt nie rozdziela odtwarzania od mutacji i logowania");
        Check(!json.Contains("spotifyLibrespot", StringComparison.OrdinalIgnoreCase),
            "historyczna druga sesja wyciekła do kontraktu");
    }

    private static void PlaybackRequestAcceptsOnlyTracksAndEpisodes()
    {
        using var good = JsonDocument.Parse("""
        {
          "itemId":"spotify:track:abc123:occurrence:2",
          "externalId":"abc123",
          "title":"Utwór\r\npróby",
          "artist":"Wykonawca",
          "kind":"track",
          "volume":41,
          "positionSeconds":12.5,
          "token":"nie może przejść"
        }
        """);
        var request = LiteSpotifyPlaybackContract.ReadPlay(good.RootElement);
        Check(request.Item.Kind == MediaItemKind.Track
            && request.Item.ExternalId == "abc123"
            && request.Item.Source == "spotify:track:abc123"
            && request.Item.Title == "Utwórpróby"
            && request.Volume == 41
            && request.Position == TimeSpan.FromSeconds(12.5),
            "poprawny utwór nie został bezpiecznie przygotowany do Librespota");

        using var container = JsonDocument.Parse("""
        {"itemId":"album","externalId":"abc123","title":"Album","kind":"album"}
        """);
        try
        {
            LiteSpotifyPlaybackContract.ReadPlay(container.RootElement);
            throw new InvalidOperationException("kontener Spotify trafił do odtwarzania");
        }
        catch (LiteRequestException exception)
        {
            Check(exception.Message.Contains("utwór albo odcinek", StringComparison.Ordinal),
                "odmowa kontenera nie podpowiada właściwego działania");
        }
    }

    private static void AccountStatusKeepsCatalogueAndPlaybackSeparate()
    {
        var result = LiteSpotifyCatalogContract.CreateAccountStatus(
            new LiteSpotifyAccountProbe(
                true, true, "Konto\r\nPróby", "premium", false));
        var json = LiteJson.Serialize(result);
        using var document = JsonDocument.Parse(json);
        var root = document.RootElement;
        Check(root.GetProperty("catalog").GetProperty("state").GetString() == "connected",
            "połączony katalog nie ma właściwego stanu");
        Check(root.GetProperty("playback").GetProperty("state").GetString() == "disconnected",
            "osobny stan odtwarzania został utożsamiony z katalogiem");
        Check(root.GetProperty("catalog").GetProperty("accountPlan").GetString() == "Premium",
            "techniczna wartość planu nie została zamieniona na etykietę");
        Check(!json.Contains('\r') && !json.Contains('\n'),
            "znaki sterujące weszły do etykiety konta");
        Check(!json.Contains("token", StringComparison.OrdinalIgnoreCase)
            && !json.Contains("refresh", StringComparison.OrdinalIgnoreCase)
            && !json.Contains("spotifyLibrespot", StringComparison.OrdinalIgnoreCase),
            "status konta zawiera prywatne albo historyczne pole");
    }

    private static void MissingClientIdIsAnExplicitSafeState()
    {
        var result = LiteSpotifyCatalogContract.CreateAccountStatus(
            new LiteSpotifyAccountProbe(false, false, string.Empty, string.Empty, true));
        Check(result.Catalog.State == "notConfigured" && !result.Catalog.Configured,
            "brak ClientId nie daje jawnego stanu notConfigured");
        Check(result.Playback.State == "connected",
            "osobny zapis odtwarzania zniknął przy braku konfiguracji katalogu");
    }

    private static void CollectionRootContainsOnlyUserFacingCategories()
    {
        var result = LiteSpotifyCatalogContract.CreateCollectionRoot();
        Check(result.Views.Select(view => view.View).SequenceEqual(
            new[] { "liked", "albums", "artists", "playlists", "podcasts", "episodes" }),
            "korzeń biblioteki ma nieoczekiwaną kolejność albo zakres");
        Check(result.Views.All(view => !view.Label.Contains("spotify:", StringComparison.OrdinalIgnoreCase)),
            "identyfikator usługi trafił do etykiety kategorii");
    }

    private static void CollectionViewsKeepUnavailableSavedItems()
    {
        var unavailable = Item(
            MediaItemKind.Track,
            "track123",
            "Wycofany utwór",
            favorite: true,
            available: false);
        var album = Item(
            MediaItemKind.Album,
            "album123",
            "Album",
            library: true);
        var result = LiteSpotifyCatalogContract.CreateCollectionViewResult(
            "liked", [unavailable, album]);
        Check(result.Items.Count == 1,
            "widok polubionych zgubił niedostępny zapis albo przyjął album");
        Check(!result.Items[0].IsAvailable
            && result.Items[0].AccessibleLabel.EndsWith(", niedostępny", StringComparison.Ordinal),
            "niedostępna zapisana pozycja nie ma uczciwej etykiety");
    }

    private static void CollectionViewRequestUsesSafeCumulativePageSizes()
    {
        using var missing = JsonDocument.Parse("""{"view":"liked"}""");
        using var tooSmall = JsonDocument.Parse(
            """{"view":"liked","loadedCount":3}""");
        using var nextPage = JsonDocument.Parse(
            """{"view":"liked","loadedCount":300}""");

        Check(LiteSpotifyCatalogContract.ReadCollectionLoadedCount(missing.RootElement)
                == LiteSpotifyCatalogContract.CollectionPageSize
            && LiteSpotifyCatalogContract.ReadCollectionLoadedCount(tooSmall.RootElement)
                == LiteSpotifyCatalogContract.CollectionPageSize
            && LiteSpotifyCatalogContract.ReadCollectionLoadedCount(nextPage.RootElement) == 300,
            "rozmiar porcji kolekcji nie ma bezpiecznego domyślnego minimum");
    }

    private static void CollectionViewsPageAfterFilteringAndKeepSourceOrder()
    {
        var items = Enumerable.Range(0, 152)
            .Select(index => Item(
                MediaItemKind.Track,
                $"track{index}",
                $"Utwór {index}",
                favorite: true))
            .ToList();
        items.Insert(1, Item(
            MediaItemKind.Album,
            "albumIgnored",
            "Album pomijany",
            library: true));
        items.Insert(2, Item(
            MediaItemKind.Track,
            "track0",
            "Duplikat pomijany",
            favorite: true));

        var first = LiteSpotifyCatalogContract.CreateCollectionViewResult(
            "liked", items, loadedCount: 150);
        var second = LiteSpotifyCatalogContract.CreateCollectionViewResult(
            "liked", items, loadedCount: 300);

        Check(first.Items.Count == 150 && first.HasMore,
            "pierwsza porcja kolekcji nie ma 150 elementów albo zgubiła hasMore");
        Check(first.Items[0].Title == "Utwór 0"
            && first.Items[149].Title == "Utwór 149",
            "filtrowanie lub usuwanie duplikatów zmieniło kolejność przed stronicowaniem");
        Check(second.Items.Count == 152 && !second.HasMore
            && second.Items[^1].Title == "Utwór 151",
            "druga porcja nie odsłoniła reszty w tej samej kolejności");
    }

    private static void SearchRowsHaveExplicitAccessibleLabelsWithoutPrivateHandles()
    {
        var item = Item(MediaItemKind.Track, "abc123", "Utwór", artist: "Wykonawca");
        item.Source = "Bearer sekret spotify:track:abc123";
        item.PublicUri = "https://open.spotify.com/track/abc123";
        item.RelatedAlbumExternalId = "album987";
        item.RelatedAlbumTitle = "Album";
        var result = LiteSpotifyCatalogContract.CreateSearchResult([item]);
        var json = LiteJson.Serialize(result);
        var row = result.Items.Single();
        Check(row.AccessibleLabel == "Utwór, Wykonawca, utwór",
            "wiersz nie ma jednoznacznej etykiety dostępnościowej");
        Check(!row.AccessibleLabel.Contains("abc123", StringComparison.Ordinal)
            && !row.AccessibleLabel.Contains("open.spotify.com", StringComparison.OrdinalIgnoreCase),
            "ID albo URI weszło do etykiety dostępnościowej");
        Check(!json.Contains("Bearer sekret", StringComparison.Ordinal)
            && !json.Contains("\"source\"", StringComparison.OrdinalIgnoreCase),
            "prywatny uchwyt odtwarzania wyciekł do DTO");
        Check(row.PublicUri == "https://open.spotify.com/track/abc123",
            "jawny publiczny adres nie pozostał oddzielnym polem modelu");
    }

    private static void ContainerRequestAcceptsOnlyMatchingSpotifyIdentity()
    {
        using var good = JsonDocument.Parse("""
        {
          "externalId":"spotify:album:album123",
          "title":"Album próby",
          "artist":"Wykonawca",
          "kind":"album",
          "token":"sekret",
          "source":"prywatny uchwyt"
        }
        """);
        var request = LiteSpotifyCatalogContract.ReadContainerRequest(good.RootElement);
        Check(request.ExternalId == "album123" && request.Kind == MediaItemKind.Album,
            "poprawny kontener nie został znormalizowany");

        using var wrong = JsonDocument.Parse("""
        {"externalId":"spotify:track:track123","title":"Nie album","kind":"album"}
        """);
        try
        {
            LiteSpotifyCatalogContract.ReadContainerRequest(wrong.RootElement);
            throw new InvalidOperationException("przyjęto album z identyfikatorem utworu");
        }
        catch (LiteRequestException exception)
        {
            Check(exception.Message.Contains("tożsamość", StringComparison.Ordinal),
                "odmowa nie ma użytkowego komunikatu");
        }
    }

    private static void ContainerResultNeverUsesIdentifiersInItsHeading()
    {
        var request = new LiteSpotifyContainerRequest(
            MediaItemKind.Artist, "artist123", "Wykonawca", string.Empty, "tracks");
        var result = LiteSpotifyCatalogContract.CreateContainerResult(
            request,
            [Item(MediaItemKind.Track, "track123", "Utwór")],
            available: true,
            hasMore: true);
        Check(result.Heading == "Utwory wykonawcy, Wykonawca",
            "nagłówek kontenera nie jest użytkowy");
        Check(!result.Heading.Contains("artist123", StringComparison.Ordinal)
            && result.HasMore,
            "ID weszło do nagłówka albo zgubiono informację o dalszych wynikach");
    }

    private static void ContainerKeepsRepeatedPlaylistOccurrencesDistinct()
    {
        var request = new LiteSpotifyContainerRequest(
            MediaItemKind.Playlist, "playlist123", "Playlista", string.Empty, null);
        var first = Item(MediaItemKind.Track, "track123", "Powtórzony utwór");
        var second = Item(MediaItemKind.Track, "track123", "Powtórzony utwór");
        var result = LiteSpotifyCatalogContract.CreateContainerResult(
            request, [first, second], available: true);
        Check(result.Items.Count == 2 && result.Items[0].Id != result.Items[1].Id,
            "powtórne wystąpienie na playliście zostało zgubione albo ma ten sam klucz wiersza");
        Check(result.Items[0].ExternalId == result.Items[1].ExternalId,
            "tożsamość zasobu zmieniła się przy rozróżnianiu wystąpień");
    }

    private static void CoordinatorDoesNotAuthenticateForStatusOrCapabilities()
    {
        using var backend = new FakeBackend();
        using var coordinator = new LiteSpotifyCatalogCoordinator(backend);
        _ = coordinator.Capabilities();
        _ = coordinator.AccountStatus();
        _ = coordinator.CollectionRoot();
        Check(backend.RefreshCalls == 0
            && backend.SearchCalls == 0
            && backend.ContainerCalls == 0,
            "status albo możliwości uruchomiły operację katalogową");
    }

    private static void CoordinatorRedactsCredentialProbeFailure()
    {
        const string secret = "credential target and token must stay private";
        using var backend = new FakeBackend
        {
            AccountFailure = new InvalidOperationException(secret)
        };
        using var coordinator = new LiteSpotifyCatalogCoordinator(backend);
        var status = (LiteSpotifyAccountStatusResult)coordinator.AccountStatus();
        var json = LiteJson.Serialize(status);
        Check(status.Catalog.State == "unavailable"
            && status.Playback.State == "unavailable",
            "awaria odczytu poświadczeń nie daje bezpiecznego stanu unavailable");
        Check(!json.Contains(secret, StringComparison.Ordinal),
            "szczegóły awarii poświadczeń wyciekły do statusu konta");
    }

    private static void CoordinatorUsesCachedCollectionWithoutAConnection()
    {
        using var backend = new FakeBackend
        {
            Account = new LiteSpotifyAccountProbe(
                true, false, string.Empty, string.Empty, false),
            Cached = [Item(MediaItemKind.Album, "album123", "Zapisany album", library: true)]
        };
        using var coordinator = new LiteSpotifyCatalogCoordinator(backend);
        using var args = JsonDocument.Parse("""{"view":"albums"}""");
        var result = (LiteSpotifyItemsResult)coordinator.CollectionView(args.RootElement);
        Check(result.Items.Count == 1 && backend.RefreshCalls == 0,
            "widok bez połączenia nie użył cache albo próbował wejść do sieci");
        Check(result.Warning.Contains("Pokazano ostatni zapis", StringComparison.Ordinal),
            "fallback cache nie jest jawny dla użytkownika");
    }

    private static void CoordinatorUsesPopulatedCacheImmediatelyWhenConnected()
    {
        using var backend = new FakeBackend
        {
            Cached = [Item(MediaItemKind.Album, "cached", "Album z zapisu", library: true)],
            RefreshedItems = [Item(MediaItemKind.Album, "network", "Album z sieci", library: true)]
        };
        using var coordinator = new LiteSpotifyCatalogCoordinator(backend);
        using var args = JsonDocument.Parse("""{"view":"albums"}""");

        var result = (LiteSpotifyItemsResult)coordinator.CollectionView(args.RootElement);

        Check(backend.RefreshCalls == 0,
            "otwarcie zapisanej kolekcji uruchomiło pełną synchronizację przed pokazaniem listy");
        Check(result.Items.Count == 1 && result.Items[0].Title == "Album z zapisu",
            "widok nie zwrócił od razu istniejącego zapisu kolekcji");
    }

    private static void CoordinatorRedactsBackendFailures()
    {
        const string secret = "Bearer tajny-token spotify:track:sekret123";
        using var backend = new FakeBackend
        {
            SearchFailure = new InvalidOperationException(secret),
            RefreshFailure = new InvalidOperationException(secret)
        };
        using var coordinator = new LiteSpotifyCatalogCoordinator(backend);
        using var searchArgs = JsonDocument.Parse("""{"query":"muzyka"}""");
        try
        {
            coordinator.Search(searchArgs.RootElement);
            throw new InvalidOperationException("awaria backendu nie została zgłoszona");
        }
        catch (LiteRequestException exception)
        {
            Check(!exception.Message.Contains(secret, StringComparison.Ordinal)
                && exception.Message == "Nie udało się wyszukać w Spotify.",
                "surowy błąd backendu wyciekł do protokołu");
        }

        using var viewArgs = JsonDocument.Parse("""{"view":"liked"}""");
        var view = (LiteSpotifyItemsResult)coordinator.CollectionView(viewArgs.RootElement);
        Check(!view.Warning.Contains(secret, StringComparison.Ordinal)
            && view.Warning.Contains("Pokazano ostatni zapis", StringComparison.Ordinal),
            "surowy błąd odświeżenia wyciekł do ostrzeżenia");
    }

    private static void CoordinatorSearchesExactlyOnceWithoutMutatingAnything()
    {
        using var backend = new FakeBackend
        {
            SearchItems = [Item(MediaItemKind.Artist, "artist123", "Wykonawca")]
        };
        using var coordinator = new LiteSpotifyCatalogCoordinator(backend);
        using var args = JsonDocument.Parse("""{"query":" Wykonawca ","add":true}""");
        var result = (LiteSpotifyItemsResult)coordinator.Search(args.RootElement);
        Check(backend.SearchCalls == 1 && backend.LastQuery == "Wykonawca",
            "wyszukiwanie nie wykonało dokładnie jednego oczyszczonego odczytu");
        Check(result.Items.Single().Kind == "artist" && backend.MutationCalls == 0,
            "wynik zmienił rodzaj albo wyszukiwanie wykonało mutację");
    }

    private static MediaItem Item(
        MediaItemKind kind,
        string externalId,
        string title,
        string artist = "",
        bool favorite = false,
        bool library = false,
        bool available = true) => new()
    {
        Kind = kind,
        ExternalId = externalId,
        Title = title,
        Artist = artist,
        IsFavorite = favorite,
        IsInLibrary = library,
        IsAvailable = available
    };

    private static void Check(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }

    private sealed class FakeBackend : ILiteSpotifyReadOnlyBackend
    {
        public LiteSpotifyAccountProbe Account { get; set; } = new(
            true, true, "Konto", "premium", false);
        public IReadOnlyList<MediaItem> Cached { get; set; } = [];
        public IReadOnlyList<MediaItem> SearchItems { get; set; } = [];
        public IReadOnlyList<MediaItem> RefreshedItems { get; set; } = [];
        public IReadOnlyList<MediaItem> ContainerItems { get; set; } = [];
        public Exception? SearchFailure { get; set; }
        public Exception? RefreshFailure { get; set; }
        public Exception? ContainerFailure { get; set; }
        public Exception? AccountFailure { get; set; }
        public int RefreshCalls { get; private set; }
        public int SearchCalls { get; private set; }
        public int ContainerCalls { get; private set; }
        public int MutationCalls => 0;
        public string LastQuery { get; private set; } = string.Empty;

        public IReadOnlyList<MediaItem> CachedCollection => Cached;

        public LiteSpotifyAccountProbe ReadAccountStatus()
        {
            if (AccountFailure is not null) throw AccountFailure;
            return Account;
        }

        public Task<LiteSpotifyCollectionRefresh> RefreshCollectionAsync(
            CancellationToken cancellationToken)
        {
            RefreshCalls++;
            if (RefreshFailure is not null) throw RefreshFailure;
            return Task.FromResult(new LiteSpotifyCollectionRefresh(RefreshedItems, false));
        }

        public Task<IReadOnlyList<MediaItem>> SearchAsync(
            string query,
            CancellationToken cancellationToken)
        {
            SearchCalls++;
            LastQuery = query;
            if (SearchFailure is not null) throw SearchFailure;
            return Task.FromResult(SearchItems);
        }

        public Task<LiteSpotifyContainerBackendResult> GetContainerItemsAsync(
            LiteSpotifyContainerRequest request,
            CancellationToken cancellationToken)
        {
            ContainerCalls++;
            if (ContainerFailure is not null) throw ContainerFailure;
            return Task.FromResult(
                new LiteSpotifyContainerBackendResult(ContainerItems, true));
        }

        public void Dispose()
        {
        }
    }
}
