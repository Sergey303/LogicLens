namespace LogicLens.State;

public abstract class RuntimeStateException : Exception
{
    protected RuntimeStateException(string message)
        : base(message)
    {
    }

    protected RuntimeStateException(string message, Exception innerException)
        : base(message, innerException)
    {
    }
}

public sealed class RuntimeRevisionConflictException : RuntimeStateException
{
    public RuntimeRevisionConflictException(long expectedRevision, long currentRevision)
        : base(
            $"Expected revision {expectedRevision}, but current revision is " +
            $"{currentRevision}.")
    {
        ExpectedRevision = expectedRevision;
        CurrentRevision = currentRevision;
    }

    public long ExpectedRevision { get; }

    public long CurrentRevision { get; }
}

public sealed class RuntimeCommandConflictException : RuntimeStateException
{
    public RuntimeCommandConflictException(string commandId)
        : base($"CommandId '{commandId}' was already used for different content.")
    {
        CommandId = commandId;
    }

    public string CommandId { get; }
}

public sealed class RuntimeStateCorruptionException : RuntimeStateException
{
    public RuntimeStateCorruptionException(string message)
        : base(message)
    {
    }

    public RuntimeStateCorruptionException(string message, Exception innerException)
        : base(message, innerException)
    {
    }
}

public sealed class RuntimeStateInUseException : RuntimeStateException
{
    public RuntimeStateInUseException(string path, Exception innerException)
        : base($"Runtime state is already open or unavailable: {path}", innerException)
    {
        Path = path;
    }

    public string Path { get; }
}

public sealed class RuntimeStateFaultedException : RuntimeStateException
{
    public RuntimeStateFaultedException()
        : base("Runtime state store is faulted and must be reopened.")
    {
    }
}

public sealed class RuntimeStateStoreOptions
{
    public TimeProvider TimeProvider { get; init; } = TimeProvider.System;

    public int MaxOperationsPerCommand { get; init; } = 10_000;

    public int MaxRecordBytes { get; init; } = 16 * 1024 * 1024;

    internal IRuntimeStateFaultInjector? FaultInjector { get; init; }

    internal void Validate()
    {
        ArgumentNullException.ThrowIfNull(TimeProvider);
        if (MaxOperationsPerCommand <= 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(MaxOperationsPerCommand),
                MaxOperationsPerCommand,
                "Operation limit must be positive.");
        }
        if (MaxRecordBytes < 1024)
        {
            throw new ArgumentOutOfRangeException(
                nameof(MaxRecordBytes),
                MaxRecordBytes,
                "Record limit must be at least 1024 bytes.");
        }
    }
}

internal enum RuntimeStateFaultPoint
{
    AfterHeader,
    AfterPayload,
    AfterChecksum,
    AfterDurableFlush
}

internal interface IRuntimeStateFaultInjector
{
    void OnFaultPoint(RuntimeStateFaultPoint point);
}

internal sealed class DelegateRuntimeStateFaultInjector(
    Action<RuntimeStateFaultPoint> callback)
    : IRuntimeStateFaultInjector
{
    public void OnFaultPoint(RuntimeStateFaultPoint point) => callback(point);
}
