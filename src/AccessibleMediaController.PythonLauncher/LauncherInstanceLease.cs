namespace AccessibleMediaController.PythonLauncher;

/// <summary>
/// Keeps the launcher alive as the single owner for the whole lifetime of the
/// Python frontend.  The launcher, not a transient wx object, is the stable
/// process that every ordinary AMC.exe start goes through.
/// </summary>
internal sealed class LauncherInstanceLease : IDisposable
{
    internal const string DefaultMutexName =
        @"Local\AccessibleMultimediaController.PythonLauncher.SingleInstance";

    private readonly Mutex _mutex;
    private bool _ownsMutex;

    private LauncherInstanceLease(Mutex mutex, bool ownsMutex)
    {
        _mutex = mutex;
        _ownsMutex = ownsMutex;
    }

    internal bool IsOwner => _ownsMutex;

    internal static LauncherInstanceLease TryAcquire(string? mutexName = null)
    {
        var mutex = new Mutex(false, mutexName ?? DefaultMutexName);
        var ownsMutex = false;
        try
        {
            ownsMutex = mutex.WaitOne(0);
        }
        catch (AbandonedMutexException)
        {
            // Poprzedni launcher zakończył się awaryjnie. System przekazał
            // blokadę tej instancji, więc można bezpiecznie kontynuować.
            ownsMutex = true;
        }
        return new LauncherInstanceLease(mutex, ownsMutex);
    }

    public void Dispose()
    {
        if (_ownsMutex)
        {
            _mutex.ReleaseMutex();
            _ownsMutex = false;
        }
        _mutex.Dispose();
    }
}
