using System.ComponentModel;
using System.Runtime.InteropServices;

namespace KnowledgePilot.LogicLens.DocumentEvidence.LocalStorage;

internal static class AtomicFilePromotion
{
    private const int UnixAlreadyExists = 17;
    private const int WindowsAlreadyExists = 183;
    private const int WindowsFileExists = 80;

    public static bool TryCreateHardLink(string stagingPath, string objectPath)
    {
        if (OperatingSystem.IsWindows())
        {
            return TryCreateWindowsHardLink(stagingPath, objectPath);
        }
        return TryCreateUnixHardLink(stagingPath, objectPath);
    }

    private static bool TryCreateUnixHardLink(string stagingPath, string objectPath)
    {
        if (UnixLink(stagingPath, objectPath) == 0)
        {
            return true;
        }

        var error = Marshal.GetLastPInvokeError();
        if (error == UnixAlreadyExists)
        {
            return false;
        }
        throw NativeFailure("link", error);
    }

    private static bool TryCreateWindowsHardLink(string stagingPath, string objectPath)
    {
        if (CreateHardLink(objectPath, stagingPath, IntPtr.Zero))
        {
            return true;
        }

        var error = Marshal.GetLastPInvokeError();
        if (error is WindowsAlreadyExists or WindowsFileExists)
        {
            return false;
        }
        throw NativeFailure("CreateHardLinkW", error);
    }

    private static IOException NativeFailure(string operation, int error)
    {
        var detail = new Win32Exception(error).Message;
        return new IOException($"Atomic object promotion via {operation} failed: {detail}");
    }

    [DllImport("libc", EntryPoint = "link", SetLastError = true)]
    private static extern int UnixLink(
        [MarshalAs(UnmanagedType.LPUTF8Str)] string existingPath,
        [MarshalAs(UnmanagedType.LPUTF8Str)] string newPath
    );

    [DllImport("Kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool CreateHardLink(
        string fileName,
        string existingFileName,
        IntPtr securityAttributes
    );
}
