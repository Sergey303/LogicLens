using System.Security.Cryptography;
using System.Text;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.ContractTests;

internal static class UploadServiceContractTests
{
    private static readonly StoredObjectReference StoredObject = new(
        new string('a', 64),
        12,
        $"sha256/aa/aa/{new string('a', 64)}",
        true
    );

    public static async Task ReplayAvoidsObjectWriteAsync()
    {
        var command = CreateCommand();
        var existing = new UploadCompletionResult(
            command.WorkspaceId,
            command.DocumentId,
            Guid.NewGuid(),
            1,
            Guid.NewGuid(),
            Guid.NewGuid(),
            new string('b', 64),
            false
        );
        var store = new RecordingImmutableObjectStore(StoredObject);
        var repository = new RecordingLifecycleRepository { Existing = existing };
        var service = new DocumentUploadService(store, repository);

        var result = await service.CompleteAsync(command);

        Assert(result.Replayed, "Existing completion was not marked as replayed.");
        Assert(store.PutCount == 0, "Replay read or stored upload bytes.");
        Assert(repository.CommitCount == 0, "Replay created another revision/job transaction.");
    }

    public static async Task NewUploadBuildsDeterministicManifestAsync()
    {
        var command = CreateCommand();
        var store = new RecordingImmutableObjectStore(StoredObject);
        var repository = new RecordingLifecycleRepository();
        var service = new DocumentUploadService(store, repository);

        var result = await service.CompleteAsync(command);
        var commit = repository.LastCommit
            ?? throw new InvalidOperationException("Upload commit was not recorded.");
        var expectedJson =
            $"{{\"formatVersion\":1,\"objectSha256\":\"{StoredObject.Sha256}\"," +
            "\"sizeBytes\":12,\"mediaType\":\"application/pdf\"," +
            "\"sourceKind\":\"Upload\",\"adapter\":\"pypdf\"," +
            "\"adapterVersion\":\"1.0.0\"}";
        var expectedHash = Convert.ToHexString(
            SHA256.HashData(Encoding.UTF8.GetBytes(expectedJson))
        ).ToLowerInvariant();

        Assert(store.PutCount == 1, "New upload did not store bytes exactly once.");
        Assert(repository.CommitCount == 1, "New upload did not use one lifecycle transaction.");
        Assert(commit.Manifest.CanonicalJson == expectedJson, "Revision manifest is not canonical.");
        Assert(commit.Manifest.Sha256 == expectedHash, "Revision manifest hash is incorrect.");
        Assert(result.ManifestSha256 == expectedHash, "Committed result changed manifest identity.");
        Assert(!result.Replayed, "First completion was incorrectly marked as replayed.");
    }

    public static async Task ConflictingCommitResultIsRejectedAsync()
    {
        var command = CreateCommand();
        var store = new RecordingImmutableObjectStore(StoredObject);
        var repository = new RecordingLifecycleRepository
        {
            CommitResult = commit => UploadTestData.Result(commit, replayed: true) with
            {
                ManifestSha256 = new string('c', 64),
            },
        };
        var service = new DocumentUploadService(store, repository);

        await AssertThrowsAsync<InvalidDataException>(
            () => service.CompleteAsync(command),
            "Idempotency race silently accepted different content."
        );
    }

    private static CompleteUploadCommand CreateCommand()
    {
        return new CompleteUploadCommand(
            Guid.NewGuid(),
            Guid.NewGuid(),
            $"upload:{Guid.NewGuid():N}",
            "application/pdf",
            "Upload",
            "pypdf",
            "1.0.0",
            new MemoryStream(Encoding.UTF8.GetBytes("upload bytes"), writable: false)
        );
    }

    private static void Assert(bool condition, string message)
    {
        if (!condition)
        {
            throw new InvalidOperationException(message);
        }
    }

    private static async Task AssertThrowsAsync<TException>(Func<Task> action, string message)
        where TException : Exception
    {
        try
        {
            await action();
        }
        catch (TException)
        {
            return;
        }
        throw new InvalidOperationException(message);
    }
}
