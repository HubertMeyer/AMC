namespace AccessibleMediaController.AppleMusicTokenBroker;

internal static class Program
{
    public static Task Main(string[] args) =>
        AppleMusicTokenBrokerApplication.Build(args).RunAsync();
}
