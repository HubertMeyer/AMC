using AccessibleMediaController.LiteHost.Protocol;

namespace AccessibleMediaController.LiteHost;

/// <summary>
/// Wartości obliczane przez właściciela wykonania, które Ustawienia pokazują
/// jako pełne ścieżki. Frontend nie zgaduje przekierowanego lub
/// zlokalizowanego systemowego folderu Muzyka.
/// </summary>
internal static class LiteGeneralSettingsCoordinator
{
    internal const string DefaultsOperation = "settings.defaults";

    internal static IReadOnlyDictionary<string, Func<LiteRequest, LiteEventSink, object?>>
        Handlers() =>
        new Dictionary<string, Func<LiteRequest, LiteEventSink, object?>>(StringComparer.Ordinal)
        {
            [DefaultsOperation] = (_, _) =>
            {
                var music = Environment.GetFolderPath(Environment.SpecialFolder.MyMusic);
                return new
                {
                    radioRecordingsFolder = Path.Combine(music, "AMC — Nagrania radia"),
                    podcastDownloadsFolder = Path.Combine(music, "AMC — Pobrane podcasty")
                };
            }
        };
}
