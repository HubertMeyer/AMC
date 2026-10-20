using System.ComponentModel;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using AccessibleMediaController.Core.YouTube;

namespace AccessibleMediaController.Windows.Services;

/// <summary>
/// Profilowo rozdzielony magazyn tokenów YouTube w Menedżerze poświadczeń
/// Windows. Tokeny nie trafiają do state.json, migawki AMC Test → AMC,
/// argumentów procesu ani protokołu Python–C#.
/// </summary>
internal sealed class YouTubeCredentialStore : IYouTubeCredentialStore
{
    private const uint CredentialTypeGeneric = 1;
    private const uint CredentialPersistLocalMachine = 2;
    private const int ErrorNotFound = 1168;
    private const int MaxBlobBytes = 2560;
    private readonly string _targetName;

    internal YouTubeCredentialStore(string targetName)
    {
        if (string.IsNullOrWhiteSpace(targetName) || targetName.Length > 256)
            throw new ArgumentException("Nieprawidłowy magazyn logowania YouTube.", nameof(targetName));
        _targetName = targetName;
    }

    internal string TargetName => _targetName;

    internal static YouTubeCredentialStore ForReleaseProfile(string releaseProfile) =>
        new(TargetNameForReleaseProfile(releaseProfile));

    internal static string TargetNameForReleaseProfile(string releaseProfile) =>
        releaseProfile?.Trim().ToLowerInvariant() switch
        {
            "test" => "AccessibleMediaController/test/YouTube",
            "public" => "AccessibleMediaController/public/YouTube",
            _ => throw new InvalidOperationException(
                "Nie można wybrać magazynu logowania YouTube dla nieznanego profilu AMC.")
        };

    public bool TryRead(out YouTubeTokenSet? tokens)
    {
        tokens = null;
        if (!CredRead(_targetName, CredentialTypeGeneric, 0, out var pointer))
        {
            var error = Marshal.GetLastWin32Error();
            if (error == ErrorNotFound) return false;
            throw new Win32Exception(error, "Nie udało się odczytać logowania YouTube.");
        }

        byte[]? plaintext = null;
        try
        {
            var credential = Marshal.PtrToStructure<NativeCredential>(pointer);
            if (credential.CredentialBlob == IntPtr.Zero
                || credential.CredentialBlobSize is 0 or > MaxBlobBytes)
                return false;
            plaintext = new byte[credential.CredentialBlobSize];
            Marshal.Copy(credential.CredentialBlob, plaintext, 0, plaintext.Length);
            return TryDeserialize(plaintext, out tokens);
        }
        finally
        {
            if (plaintext is not null) CryptographicOperations.ZeroMemory(plaintext);
            CredFree(pointer);
        }
    }

    public void Write(YouTubeTokenSet tokens)
    {
        ArgumentNullException.ThrowIfNull(tokens);
        var bytes = Serialize(tokens);
        var blob = Marshal.AllocCoTaskMem(bytes.Length);
        try
        {
            Marshal.Copy(bytes, 0, blob, bytes.Length);
            var credential = new NativeCredential
            {
                Type = CredentialTypeGeneric,
                TargetName = _targetName,
                CredentialBlobSize = (uint)bytes.Length,
                CredentialBlob = blob,
                Persist = CredentialPersistLocalMachine,
                UserName = "YouTube OAuth"
            };
            if (!CredWrite(ref credential, 0))
                throw new Win32Exception(Marshal.GetLastWin32Error(),
                    "Nie udało się bezpiecznie zapisać logowania YouTube.");
        }
        finally
        {
            for (var index = 0; index < bytes.Length; index++) Marshal.WriteByte(blob, index, 0);
            Marshal.FreeCoTaskMem(blob);
            CryptographicOperations.ZeroMemory(bytes);
        }
    }

    public void Delete()
    {
        if (CredDelete(_targetName, CredentialTypeGeneric, 0)) return;
        var error = Marshal.GetLastWin32Error();
        if (error != ErrorNotFound)
            throw new Win32Exception(error, "Nie udało się usunąć logowania YouTube.");
    }

    internal static byte[] Serialize(YouTubeTokenSet tokens)
    {
        if (!IsValid(tokens))
            throw new InvalidDataException("Dane logowania YouTube są niepełne.");
        var bytes = JsonSerializer.SerializeToUtf8Bytes(tokens);
        if (bytes.Length is 0 or > MaxBlobBytes)
        {
            CryptographicOperations.ZeroMemory(bytes);
            throw new InvalidDataException("Dane logowania YouTube są zbyt duże, aby je bezpiecznie zapisać.");
        }
        return bytes;
    }

    internal static bool TryDeserialize(ReadOnlySpan<byte> bytes, out YouTubeTokenSet? tokens)
    {
        tokens = null;
        if (bytes.Length is 0 or > MaxBlobBytes) return false;
        try
        {
            var parsed = JsonSerializer.Deserialize<YouTubeTokenSet>(bytes);
            if (!IsValid(parsed)) return false;
            tokens = parsed;
            return true;
        }
        catch (JsonException)
        {
            return false;
        }
    }

    private static bool IsValid(YouTubeTokenSet? tokens) =>
        tokens is not null
        && tokens.AccessToken is { Length: > 0 and <= 2048 }
        && tokens.RefreshToken is { Length: > 0 and <= 2048 }
        && tokens.Scope is { Length: > 0 and <= 1024 }
        && tokens.ClientId is { Length: > 20 and <= 512 }
        && tokens.ClientId.EndsWith(".apps.googleusercontent.com", StringComparison.Ordinal)
        && tokens.ExpiresAtUtc > DateTimeOffset.UnixEpoch;

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
    private static extern bool CredRead(string target, uint type, uint flags, out IntPtr credential);

    [DllImport("advapi32.dll", EntryPoint = "CredWriteW", CharSet = CharSet.Unicode, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool CredWrite(ref NativeCredential credential, uint flags);

    [DllImport("advapi32.dll", EntryPoint = "CredDeleteW", CharSet = CharSet.Unicode, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool CredDelete(string target, uint type, uint flags);

    [DllImport("advapi32.dll")]
    private static extern void CredFree(IntPtr buffer);
}
