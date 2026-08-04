using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application;

public sealed class ProcessingCompletionService
{
    private readonly IProcessingCompletionRepository _repository;

    public ProcessingCompletionService(IProcessingCompletionRepository repository)
    {
        _repository = repository ?? throw new ArgumentNullException(nameof(repository));
    }

    public async Task CompleteAsync(
        ProcessingJobSnapshot expectedJob,
        ProcessingCompletionPayload completion,
        CancellationToken cancellationToken = default
    )
    {
        Validate(expectedJob, completion);
        if (!await _repository.TryCompleteAsync(expectedJob, completion, cancellationToken))
        {
            throw new InvalidOperationException(
                "Processing completion lost its lease or conflicted with persisted output."
            );
        }
    }

    private static void Validate(
        ProcessingJobSnapshot expectedJob,
        ProcessingCompletionPayload completion
    )
    {
        ArgumentNullException.ThrowIfNull(expectedJob);
        ArgumentNullException.ThrowIfNull(completion);
        if (expectedJob.State != ProcessingJobState.Leased
            || expectedJob.LeaseToken is null
            || expectedJob.LeaseUntil is null
            || completion.CompletedAt > expectedJob.LeaseUntil)
        {
            throw new InvalidOperationException("A live processing lease is required for completion.");
        }
        ValidateHash(completion.Manifest.ConfigurationSha256, "configuration");
        ValidateHash(completion.Manifest.ArtifactSha256, "artifact");
        ValidateHash(completion.Manifest.IrSha256, "IR");
        ValidateHash(completion.Manifest.ManifestSha256, "manifest");
        if (string.IsNullOrWhiteSpace(completion.Manifest.Adapter)
            || string.IsNullOrWhiteSpace(completion.Manifest.AdapterVersion)
            || string.IsNullOrWhiteSpace(completion.Manifest.ManifestJson))
        {
            throw new InvalidDataException("Processing manifest is incomplete.");
        }

        var ids = new HashSet<Guid>();
        for (var index = 0; index < completion.Fragments.Count; index++)
        {
            var fragment = completion.Fragments[index];
            if (fragment.RevisionId != completion.RevisionId
                || fragment.Sequence != index + 1
                || !ids.Add(fragment.FragmentId)
                || string.IsNullOrWhiteSpace(fragment.AnchorJson)
                || string.IsNullOrWhiteSpace(fragment.Text))
            {
                throw new InvalidDataException("Processing fragments are not canonical and contiguous.");
            }
            ValidateHash(fragment.ContentHash, "fragment content");
        }
        if (completion.Fragments.Count == 0)
        {
            throw new InvalidDataException("Processing completion must contain at least one fragment.");
        }
    }

    private static void ValidateHash(string value, string name)
    {
        if (value.Length != 64 || value.Any(character =>
            character is not (>= '0' and <= '9') and not (>= 'a' and <= 'f')))
        {
            throw new InvalidDataException($"The {name} SHA-256 must be lowercase hexadecimal.");
        }
    }
}
