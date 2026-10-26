using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Net.Http;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Sessions;
using AccessibleMediaController.Core.Spotify;
using AccessibleMediaController.Windows.Services;

namespace AccessibleMediaController.Windows;

public partial class MainWindow
{
    private IRecognitionStreamingResolver CreateRecognitionStreamingResolver() =>
        new RecognitionStreamingResolver(
            IsRecognitionServiceAvailable,
            SearchRecognitionServiceAsync);

    private bool IsRecognitionServiceAvailable(RecognizedTrackStreamingService service) =>
        service switch
        {
            RecognizedTrackStreamingService.Spotify =>
                _spotifyIntegration.IsConfigured && _spotifyIntegration.HasStoredLogin,
            RecognizedTrackStreamingService.Tidal =>
                _tidalIntegration.IsConfigured && _tidalIntegration.HasStoredLogin,
            _ => false
        };

    private Task<IReadOnlyList<MediaItem>> SearchRecognitionServiceAsync(
        RecognizedTrackStreamingService service,
        string query,
        CancellationToken cancellationToken) => service switch
    {
        RecognizedTrackStreamingService.Spotify =>
            _spotifyIntegration.SearchAsync(query, cancellationToken),
        RecognizedTrackStreamingService.Tidal =>
            _tidalIntegration.SearchAsync(query, cancellationToken),
        _ => Task.FromResult<IReadOnlyList<MediaItem>>([])
    };

    private async Task ExecuteRecognitionHistoryRequestAsync(RecognitionHistoryRequest request)
    {
        try
        {
            if (request.Kind == RecognitionHistoryRequestKind.OpenExternal)
            {
                OpenRecognitionExternalUri(request.ExternalUri);
                return;
            }
            if (request.Resolution is not { } resolution) return;

            if (request.Kind is RecognitionHistoryRequestKind.OpenTrackInOriginalApplication
                or RecognitionHistoryRequestKind.OpenAlbumInOriginalApplication)
            {
                OpenRecognitionInOriginalApplication(request.Kind, resolution);
                return;
            }

            var sessionId = resolution.Service == RecognizedTrackStreamingService.Spotify
                ? SpotifyPlaybackSettingsResolver.SessionId
                : "tidal";
            var session = _sessions.FindSession(sessionId);
            if (session is null)
            {
                Announce($"Sesja {RecognizedTrackStreamingServiceRules.GetLabel(resolution.Service)} nie jest dostępna");
                return;
            }

            session.AddItemsById(new[] { resolution.Track, resolution.Album, resolution.Artist }
                .Where(item => item is not null)
                .Select(item => item!));
            Activate();

            switch (request.Kind)
            {
                case RecognitionHistoryRequestKind.PlayTrack:
                    PlayRecognizedTrack(session, resolution.Track);
                    break;
                case RecognitionHistoryRequestKind.ShowTrackInAmc:
                    ShowRecognizedTrackInAmc(session, resolution.Track);
                    break;
                case RecognitionHistoryRequestKind.OpenAlbum when resolution.Album is not null:
                    SelectSessionBrowserItem(sessionId, resolution.Album.Id);
                    if (resolution.Service == RecognizedTrackStreamingService.Spotify)
                    {
                        await OpenSpotifyContainerAsync(
                            resolution.Album, preferredExternalId: resolution.Track.ExternalId);
                    }
                    else
                    {
                        await OpenTidalContainerAsync(
                            resolution.Album, preferredExternalId: resolution.Track.ExternalId);
                    }
                    break;
                case RecognitionHistoryRequestKind.OpenArtist when resolution.Artist is not null:
                    SelectSessionBrowserItem(sessionId, resolution.Artist.Id);
                    if (resolution.Service == RecognizedTrackStreamingService.Spotify)
                        await OpenSpotifyContainerAsync(resolution.Artist);
                    else
                        await OpenTidalContainerAsync(resolution.Artist);
                    break;
            }
        }
        catch (Exception exception) when (exception is InvalidOperationException
                                           or IOException
                                           or HttpRequestException)
        {
            Announce($"Nie udało się wykonać działania dla rozpoznanego utworu. {exception.Message}");
        }
    }

    private void PlayRecognizedTrack(DemoMediaSession session, MediaItem track)
    {
        SelectSessionBrowserItem(session.Id, track.Id);
        if (TryPlayTrackInTidalDesktop(session, track, [track], "Rozpoznane utwory"))
            return;

        InvalidatePendingSpotifyPresetPlaybackForUserIntent();
        session.SetPlaybackContext([track.Id]);
        session.Play(track);
        RecordPlayback(session, track);
        RefreshPlaybackIndicators();
        ShowPlayerView();
    }

    private void ShowRecognizedTrackInAmc(DemoMediaSession session, MediaItem track)
    {
        SelectSessionBrowserItem(session.Id, track.Id);
        RestoreMediaListFocusAfterRefresh();
    }

    private void OpenRecognitionExternalUri(string? uri)
    {
        if (!Uri.TryCreate(uri, UriKind.Absolute, out var parsed)
            || parsed.Scheme is not ("http" or "https"))
        {
            Announce("To działanie nie zawiera poprawnego łącza");
            return;
        }
        try
        {
            Process.Start(new ProcessStartInfo(parsed.AbsoluteUri) { UseShellExecute = true });
        }
        catch (Exception exception) when (exception is InvalidOperationException or Win32Exception)
        {
            Announce("Nie udało się otworzyć łącza w przeglądarce");
        }
    }

    private void OpenRecognitionInOriginalApplication(
        RecognitionHistoryRequestKind kind,
        RecognitionResolutionResult resolution)
    {
        var item = kind == RecognitionHistoryRequestKind.OpenTrackInOriginalApplication
            ? resolution.Track
            : resolution.Album;
        if (item is null)
        {
            Announce("To działanie nie ma dostępnego celu");
            return;
        }

        if (resolution.Service != RecognizedTrackStreamingService.Spotify
            || string.IsNullOrWhiteSpace(item.ExternalId)
            || !item.ExternalId.All(character => char.IsLetterOrDigit(character)))
        {
            OpenRecognitionExternalUri(item.PublicUri);
            return;
        }

        var kindSegment = item.Kind == MediaItemKind.Album ? "album" : "track";
        var spotifyUri = $"spotify:{kindSegment}:{item.ExternalId}";
        try
        {
            Process.Start(new ProcessStartInfo(spotifyUri) { UseShellExecute = true });
        }
        catch (Exception exception) when (exception is InvalidOperationException or Win32Exception)
        {
            OpenRecognitionExternalUri(item.PublicUri);
        }
    }
}
