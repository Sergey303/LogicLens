namespace KnowledgePilot.LogicLens.DocumentEvidence.LocalStorage.ContractTests;

internal sealed class TemporaryStorageRoot : IDisposable
{
    public TemporaryStorageRoot()
    {
        RootPath = Path.Combine(Path.GetTempPath(), $"logiclens-storage-{Guid.NewGuid():N}");
        Directory.CreateDirectory(RootPath);
    }

    public string RootPath { get; }

    public string ResolveObjectKey(string objectKey)
    {
        var parts = objectKey.Split('/', StringSplitOptions.RemoveEmptyEntries);
        return Path.Combine([RootPath, .. parts]);
    }

    public void Dispose()
    {
        if (Directory.Exists(RootPath))
        {
            Directory.Delete(RootPath, recursive: true);
        }
    }
}
