namespace AccessibleMediaController.SonosBroker;

internal static class Program
{
    public static Task Main(string[] args) => SonosBrokerApplication.Build(args).RunAsync();
}
