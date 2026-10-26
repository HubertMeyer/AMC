using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;

namespace AccessibleMediaController.Windows.Services;

internal sealed record AppleMusicCredentials(
    string DeveloperToken,
    string? MusicUserToken,
    string Storefront);

/// <summary>
/// Tokeny Apple Music pozostają w Menedżerze poświadczeń Windows. Klucz
/// prywatny Media Services (.p8) nigdy nie trafia do klienta AMC.
/// </summary>
internal static class AppleMusicCredentialStore
{
    private const string TargetName = "AccessibleMediaController/AppleMusic";
    private const uint CredentialTypeGeneric = 1;
    private const uint CredentialPersistLocalMachine = 2;
    private const int ErrorNotFound = 1168;

    public static bool TryRead(out AppleMusicCredentials? credentials)
    {
        credentials = null;
        if (!CredRead(TargetName, CredentialTypeGeneric, 0, out var pointer))
        {
            var error = Marshal.GetLastWin32Error();
            if (error == ErrorNotFound) return false;
            throw new Win32Exception(error,
                "Nie udało się odczytać poświadczeń Apple Music.");
        }
        try
        {
            var native = Marshal.PtrToStructure<NativeCredential>(pointer);
            if (native.CredentialBlob == IntPtr.Zero || native.CredentialBlobSize == 0) return false;
            var bytes = new byte[native.CredentialBlobSize];
            Marshal.Copy(native.CredentialBlob, bytes, 0, bytes.Length);
            credentials = JsonSerializer.Deserialize<AppleMusicCredentials>(Encoding.UTF8.GetString(bytes));
            return credentials is not null
                   && IsDeveloperToken(credentials.DeveloperToken)
                   && IsStorefront(credentials.Storefront);
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

    public static void Write(AppleMusicCredentials credentials)
    {
        ArgumentNullException.ThrowIfNull(credentials);
        if (!IsDeveloperToken(credentials.DeveloperToken))
            throw new InvalidOperationException("Token deweloperski Apple Music ma nieprawidłowy format.");
        if (!IsStorefront(credentials.Storefront))
            throw new InvalidOperationException("Kod katalogu Apple Music musi mieć dwie litery, na przykład pl.");

        var normalized = credentials with
        {
            DeveloperToken = credentials.DeveloperToken.Trim(),
            MusicUserToken = string.IsNullOrWhiteSpace(credentials.MusicUserToken)
                ? null
                : credentials.MusicUserToken.Trim(),
            Storefront = credentials.Storefront.Trim().ToLowerInvariant()
        };
        var bytes = Encoding.UTF8.GetBytes(JsonSerializer.Serialize(normalized));
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
                UserName = "Apple Music"
            };
            if (!CredWrite(ref native, 0))
            {
                throw new Win32Exception(
                    Marshal.GetLastWin32Error(),
                    "Nie udało się bezpiecznie zapisać poświadczeń Apple Music.");
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
            throw new Win32Exception(error, "Nie udało się usunąć poświadczeń Apple Music.");
    }

    internal static bool IsDeveloperToken(string? value) =>
        !string.IsNullOrWhiteSpace(value)
        && value.Trim().Split('.').Length == 3
        && value.Trim().Length <= 4096;

    internal static bool IsStorefront(string? value) =>
        value?.Trim() is { Length: 2 } code && code.All(char.IsLetter);

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
