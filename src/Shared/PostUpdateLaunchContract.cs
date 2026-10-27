namespace AccessibleMediaController.ReleaseProfiles;

internal sealed record PostUpdateLaunchArguments(
    bool ActivateAfterStart,
    string[] ForwardedArguments);

/// <summary>
/// Internal handoff between the updater and launcher. The switch is consumed
/// before shell arguments reach the Python frontend.
/// </summary>
internal static class PostUpdateLaunchContract
{
    internal const string ActivateAfterUpdateSwitch = "--activate-after-update";

    internal static PostUpdateLaunchArguments Parse(IReadOnlyList<string> arguments)
    {
        var activate = false;
        var forwarded = new List<string>(arguments.Count);
        foreach (var argument in arguments)
        {
            if (string.Equals(
                    argument,
                    ActivateAfterUpdateSwitch,
                    StringComparison.OrdinalIgnoreCase))
            {
                activate = true;
                continue;
            }
            forwarded.Add(argument);
        }
        return new PostUpdateLaunchArguments(activate, forwarded.ToArray());
    }
}
