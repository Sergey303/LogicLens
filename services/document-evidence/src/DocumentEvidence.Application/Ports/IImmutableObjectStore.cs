using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

public interface IImmutableObjectStore
{
    Task<StoredObjectReference> PutAsync(
        Stream content,
        CancellationToken cancellationToken
    );

    Task<Stream> OpenReadAsync(
        string sha256,
        CancellationToken cancellationToken
    );
}
