using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;

namespace AccessibleMediaController.LiteHost;

internal sealed class LiteFrontierSmartPinStore(string releaseProfile)
{
    private const uint GenericCredential = 1;
    private const uint PersistLocalMachine = 2;
    private const int ErrorNotFound = 1168;
    private readonly string profile = SafeProfile(releaseProfile);

    internal string TargetName(string deviceId)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(deviceId);
        var identity = profile + ":" + deviceId.Trim();
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(identity));
        return "AccessibleMediaController.FrontierSmartPin." + Convert.ToHexString(bytes);
    }

    public bool TryRead(string deviceId, out string pin)
    {
        pin = string.Empty;
        if (!CredRead(TargetName(deviceId), GenericCredential, 0, out var pointer))
            return false;
        try
        {
            var credential = Marshal.PtrToStructure<NativeCredential>(pointer);
            if (credential.CredentialBlob == IntPtr.Zero || credential.CredentialBlobSize == 0)
                return false;
            var bytes = new byte[credential.CredentialBlobSize];
            Marshal.Copy(credential.CredentialBlob, bytes, 0, bytes.Length);
            try
            {
                pin = Encoding.UTF8.GetString(bytes);
                return IsValidPin(pin);
            }
            finally
            {
                CryptographicOperations.ZeroMemory(bytes);
            }
        }
        finally
        {
            CredFree(pointer);
        }
    }

    public void Write(string deviceId, string pin)
    {
        if (!IsValidPin(pin))
            throw new ArgumentException(
                "PIN urządzenia musi zawierać od 1 do 16 cyfr.", nameof(pin));
        var bytes = Encoding.UTF8.GetBytes(pin);
        var pointer = Marshal.AllocCoTaskMem(bytes.Length);
        try
        {
            Marshal.Copy(bytes, 0, pointer, bytes.Length);
            var credential = new NativeCredential
            {
                Type = GenericCredential,
                TargetName = TargetName(deviceId),
                CredentialBlobSize = (uint)bytes.Length,
                CredentialBlob = pointer,
                Persist = PersistLocalMachine,
                UserName = Environment.UserName
            };
            if (!CredWrite(ref credential, 0))
            {
                throw new Win32Exception(
                    Marshal.GetLastWin32Error(),
                    "Nie udało się bezpiecznie zapisać PIN-u urządzenia.");
            }
        }
        finally
        {
            CryptographicOperations.ZeroMemory(bytes);
            Marshal.FreeCoTaskMem(pointer);
        }
    }

    public void Delete(string deviceId)
    {
        var deleted = CredDelete(TargetName(deviceId), GenericCredential, 0);
        var errorCode = deleted ? 0 : Marshal.GetLastWin32Error();
        ThrowIfDeleteFailed(deleted, errorCode);
    }

    internal static void ThrowIfDeleteFailed(bool deleted, int errorCode)
    {
        if (deleted || errorCode == ErrorNotFound)
            return;
        throw new Win32Exception(
            errorCode,
            "Nie udało się bezpiecznie usunąć PIN-u urządzenia.");
    }

    private static string SafeProfile(string value)
    {
        var result = string.IsNullOrWhiteSpace(value) ? "test" : value.Trim().ToLowerInvariant();
        return result.All(character => char.IsAsciiLetterOrDigit(character) || character is '-' or '_')
            ? result
            : "test";
    }

    private static bool IsValidPin(string? pin) =>
        !string.IsNullOrWhiteSpace(pin)
        && pin.Length <= 16
        && pin.All(char.IsAsciiDigit);

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct NativeCredential
    {
        public uint Flags;
        public uint Type;
        public string TargetName;
        public string? Comment;
        public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
        public uint CredentialBlobSize;
        public IntPtr CredentialBlob;
        public uint Persist;
        public uint AttributeCount;
        public IntPtr Attributes;
        public string? TargetAlias;
        public string UserName;
    }

    [DllImport("advapi32.dll", EntryPoint = "CredReadW", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool CredRead(
        string target, uint type, uint flags, out IntPtr credential);

    [DllImport("advapi32.dll", EntryPoint = "CredWriteW", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool CredWrite(ref NativeCredential credential, uint flags);

    [DllImport("advapi32.dll", EntryPoint = "CredDeleteW", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool CredDelete(string target, uint type, uint flags);

    [DllImport("advapi32.dll")]
    private static extern void CredFree(IntPtr credential);
}
