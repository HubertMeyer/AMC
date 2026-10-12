using System.Text.Json;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Sessions;
using AccessibleMediaController.LiteHost.Protocol;
using AccessibleMediaController.Windows.Services;

namespace AccessibleMediaController.LiteHost;

/// <summary>
/// Rozpoznaje dźwięk już odbierany przez Radio lub nagrywanie w tle. Do
/// adaptera trafia próbka PCM, a do Pythona tylko celowe pola wyniku.
/// </summary>
internal sealed class LiteRadioRecognitionCoordinator
{
    public const string Operation = "radio.recognition.run";
    private static readonly TimeSpan SampleDuration = TimeSpan.FromSeconds(12);

    private readonly RadioMediaOutput _radio;
    private readonly Func<MediaItem?> _currentStation;
    private readonly LiteRadioRecordingCoordinator _recordings;
    private readonly ITrackRecognitionService _service;
    private int _inProgress;

    public LiteRadioRecognitionCoordinator(
        RadioMediaOutput radio,
        Func<MediaItem?> currentStation,
        LiteRadioRecordingCoordinator recordings,
        ITrackRecognitionService? service = null)
    {
        _radio = radio ?? throw new ArgumentNullException(nameof(radio));
        _currentStation = currentStation ?? throw new ArgumentNullException(nameof(currentStation));
        _recordings = recordings ?? throw new ArgumentNullException(nameof(recordings));
        _service = service ?? new ShazamTrackRecognitionService();
    }

    public object Run(JsonElement args)
    {
        if (Interlocked.CompareExchange(ref _inProgress, 1, 0) != 0)
            throw new LiteRequestException("Rozpoznawanie już trwa.");
        try
        {
            var scopeText = LiteArgs.ReadText(args, "scope")
                ?? nameof(RadioRecognitionScope.CurrentStation);
            if (!Enum.TryParse<RadioRecognitionScope>(scopeText, true, out var scope)
                || !Enum.IsDefined(scope))
            {
                throw new LiteRequestException("Nieznany zakres rozpoznawania utworów.");
            }

            var inputs = CaptureInputs(scope);
            if (inputs.Count == 0)
            {
                return new
                {
                    requested = 0,
                    recognized = Array.Empty<object>(),
                    failures = Array.Empty<object>(),
                    message = "Brak wystarczającej próbki dźwięku. Poczekaj kilka sekund i spróbuj ponownie."
                };
            }

            var recognized = new List<object>();
            var failures = new List<object>();
            var lastFailure = "Nie rozpoznano utworu";
            foreach (var input in inputs)
            {
                var result = _service.RecognizeAsync(input.Snapshot, CancellationToken.None)
                    .GetAwaiter().GetResult();
                if (!result.Success)
                {
                    lastFailure = result.Error ?? "Nie rozpoznano utworu";
                    failures.Add(new
                    {
                        stationId = input.StationId,
                        stationName = input.StationName,
                        message = lastFailure
                    });
                    continue;
                }
                recognized.Add(new
                {
                    stationId = input.StationId,
                    stationName = input.StationName,
                    title = result.Title,
                    artist = result.Artist,
                    album = result.Album,
                    releaseDate = result.ReleaseDate,
                    providerUri = result.ProviderUri,
                    recognizedUtcTicks = DateTime.UtcNow.Ticks
                });
            }
            return new
            {
                requested = inputs.Count,
                recognized = recognized.ToArray(),
                failures = failures.ToArray(),
                message = recognized.Count > 0 ? string.Empty : lastFailure
            };
        }
        finally
        {
            Interlocked.Exchange(ref _inProgress, 0);
        }
    }

    private IReadOnlyList<LiteRadioRecognitionInput> CaptureInputs(
        RadioRecognitionScope scope)
    {
        var result = new List<LiteRadioRecognitionInput>();
        var keys = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        if (RadioRecognitionScopeRules.IncludesCurrentStation(scope))
        {
            var station = _currentStation();
            if (station is not null
                && _radio.TryGetRecentPlaybackAudio(SampleDuration, out var snapshot)
                && snapshot is not null)
            {
                Add(result, keys, new LiteRadioRecognitionInput(
                    station.Id,
                    station.Title,
                    station.Source ?? station.PublicUri ?? string.Empty,
                    snapshot));
            }
        }
        if (RadioRecognitionScopeRules.IncludesRecordingStations(scope))
        {
            foreach (var input in _recordings.CaptureRecognitionInputs(SampleDuration))
                Add(result, keys, input);
        }
        return result;
    }

    private static void Add(
        ICollection<LiteRadioRecognitionInput> result,
        ISet<string> keys,
        LiteRadioRecognitionInput input)
    {
        var key = string.IsNullOrWhiteSpace(input.StationId)
            ? "url:" + input.StreamUrl.Trim()
            : "id:" + input.StationId.Trim();
        if (!keys.Add(key)) return;
        result.Add(input with
        {
            StationId = input.StationId.Trim(),
            StationName = string.IsNullOrWhiteSpace(input.StationName)
                ? "Nieznana stacja"
                : input.StationName.Trim()
        });
    }
}
