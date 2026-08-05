using KnowledgePilot.LogicLens.DocumentEvidence.Application;
using KnowledgePilot.LogicLens.DocumentEvidence.Security;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Security.ContractTests;

internal sealed class SecureUploadTestFixture
{
    public List<string> Events { get; } = [];
    public RecordingAuditSink Audit { get; } = new();
    public RecordingLifecycleRepository Repository { get; }
    public RecordingObjectStore Store { get; }

    public SecureUploadTestFixture()
    {
        Repository = new RecordingLifecycleRepository(Events);
        Store = new RecordingObjectStore(Events);
    }

    public SecureDocumentUploadService CreateService(
        bool denyAuthorization = false,
        bool denyRequestQuota = false,
        bool denyByteQuota = false,
        SecureUploadOptions? options = null
    )
    {
        var inner = new DocumentUploadService(Store, Repository);
        return new SecureDocumentUploadService(
            inner,
            new RecordingAuthorization(Events, denyAuthorization),
            new RecordingQuotaGate(Events, denyRequestQuota, denyByteQuota),
            Audit,
            options,
            new FixedTimeProvider()
        );
    }

    public static SecureUploadCommand Command(
        Stream content,
        string displayName = @"C:\incoming\  demo   evidence.pdf ",
        string mediaType = UploadMediaSignature.Pdf,
        long? declaredLength = null
    ) => new(
        Guid.Parse("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        Guid.Parse("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        Guid.Parse("cccccccc-cccc-cccc-cccc-cccccccccccc"),
        displayName,
        "demo-upload-001",
        mediaType,
        "Upload",
        "poppler",
        "24.02.0",
        declaredLength,
        content
    );

    public static byte[] PdfBytes() => "%PDF-1.4\ncontract fixture"u8.ToArray();

    private sealed class FixedTimeProvider : TimeProvider
    {
        public override DateTimeOffset GetUtcNow() =>
            new(2026, 8, 5, 7, 30, 0, TimeSpan.Zero);
    }
}
