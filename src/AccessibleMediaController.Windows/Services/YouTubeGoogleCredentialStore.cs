using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;

namespace AccessibleMediaController.Windows.Services;

internal sealed record YouTubeGoogleCredentialSet(
    string ClientId,
    string? AccessToken,
    string? RefreshToken,
    DateTimeOffset ExpiresAtUtc,
    string Scope,
    string AccountDisplayName)
{
    public bool HasLogin => !string.IsNullOrWhiteSpace(AccessToken)
        && !string.IsNullOrWhiteSpace(RefreshToken);
}

/// <summary>
/// Trzyma identyfikator publicznego klienta desktopowego oraz tokeny Google w
/// Menedżerze poświadczeń Windows. Hasło Google, sekret klienta i ciasteczka
/// przeglądarki nigdy nie przechodzą przez AMC.
/// </summary>
internal static class YouTubeGoogleCredentialStore
{
    private const string TargetName = "AccessibleMediaController/YouTubeGoogle";
    private const uint CredentialTypeGeneric = 1;
    private const uint CredentialPersistLocalMachine = 2;
    private const int ErrorNotFound = 1168;
    private const int MaximumCredentialBlobBytes = 2560;

    public static bool TryRead(out YouTubeGoogleCredentialSet? credentials)
    {
        credentials = null;
        if (!CredRead(TargetName, CredentialTypeGeneric, 0, out var pointer))
        {
            var error = Marshal.GetLastWin32Error();
            if (error == ErrorNotFound) return false;
            throw new Win32Exception(
                error,
                "Nie udało się odczytać logowania YouTube z Menedżera poświadczeń Windows.");
        }

        try
        {
            var native = Marshal.PtrToStructure<NativeCredential>(pointer);
            if (native.CredentialBlob == IntPtr.Zero || native.CredentialBlobSize == 0) return false;
            var bytes = new byte[native.CredentialBlobSize];
            Marshal.Copy(native.CredentialBlob, bytes, 0, bytes.Length);
            credentials = JsonSerializer.Deserialize<YouTubeGoogleCredentialSet>(Encoding.UTF8.GetString(bytes));
            return credentials is not null && IsValidClientId(credentials.ClientId);
        }
        catch (JsonException)
        {
            Delete();
            return false;
        }
        finally
        {
            CredFree(pointer);
        }
    }

    public static void Write(YouTubeGoogleCredentialSet credentials)
    {
        ArgumentNullException.ThrowIfNull(credentials);
        if (!IsValidClientId(credentials.ClientId))
        {
            throw new InvalidOperationException(
                "Identyfikator klienta Google powinien kończyć się na .apps.googleusercontent.com.");
        }

        var bytes = Encoding.UTF8.GetBytes(JsonSerializer.Serialize(credentials));
        if (bytes.Length > MaximumCredentialBlobBytes)
        {
            throw new InvalidOperationException(
                "Dane logowania Google są zbyt duże dla Menedżera poświadczeń Windows. Odłącz konto i zaloguj je ponownie.");
        }

        var blob = Marshal.AllocCoTaskMem(bytes.Length);
        try
        {
            Marshal.Copy(bytes, 0, blob, bytes.Length);
            var native = new NativeCredential
            {
                Type = CredentialTypeGeneric,
                TargetName = TargetName,
                CredentialBlobSize = (uint)bytes.Length,
                CredentialBlob = blob,
                Persist = CredentialPersistLocalMachine,
                UserName = "YouTube Google OAuth"
            };
            if (!CredWrite(ref native, 0))
            {
                throw new Win32Exception(
                    Marshal.GetLastWin32Error(),
                    "Nie udało się bezpiecznie zapisać logowania YouTube.");
            }
        }
        finally
        {
            Marshal.FreeCoTaskMem(blob);
        }
    }

    public static void Delete()
    {
        if (CredDelete(TargetName, CredentialTypeGeneric, 0)) return;
        var error = Marshal.GetLastWin32Error();
        if (error != ErrorNotFound)
            throw new Win32Exception(error, "Nie udało się usunąć logowania YouTube.");
    }

    internal static bool IsValidClientId(string? clientId)
    {
        if (string.IsNullOrWhiteSpace(clientId)) return false;
        var value = clientId.Trim();
        return value.Length is >= 30 and <= 300
            && value.EndsWith(".apps.googleusercontent.com", StringComparison.OrdinalIgnoreCase)
            && value.All(character => char.IsAsciiLetterOrDigit(character)
                || character is '-' or '_' or '.');
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct NativeCredential
    {
        public uint Flags;
        public uint Type;
        [MarshalAs(UnmanagedType.LPWStr)] public string TargetName;
        [MarshalAs(UnmanagedType.LPWStr)] public string? Comment;
        public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
        public uint CredentialBlobSize;
        public IntPtr CredentialBlob;
        public uint Persist;
        public uint AttributeCount;
        public IntPtr Attributes;
        [MarshalAs(UnmanagedType.LPWStr)] public string? TargetAlias;
        [MarshalAs(UnmanagedType.LPWStr)] public string UserName;
    }

    [DllImport("advapi32.dll", EntryPoint = "CredReadW", CharSet = CharSet.Unicode, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool CredRead(string target, uint type, uint reservedFlag, out IntPtr credentialPtr);

    [DllImport("advapi32.dll", EntryPoint = "CredWriteW", CharSet = CharSet.Unicode, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool CredWrite(ref NativeCredential credential, uint flags);

    [DllImport("advapi32.dll", EntryPoint = "CredDeleteW", CharSet = CharSet.Unicode, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool CredDelete(string target, uint type, uint flags);

    [DllImport("advapi32.dll")]
    private static extern void CredFree(IntPtr buffer);
}
