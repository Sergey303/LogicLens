#nullable enable

using LogicLens.DocumentEvidence.Generated;
using Microsoft.EntityFrameworkCore;

namespace LogicLens.DocumentEvidence.Generated.Persistence;

internal static class PreviewSeedData
{
    public static async Task SeedAsync(
        DocumentEvidenceOperationalModelDbContext db,
        CancellationToken cancellationToken = default)
    {
        var roleDocumentEvidenceAdmin = new Role
        {
            Id = Guid.Parse("8c22fcbe-2728-5859-8169-7372a95003a9"),
            Code = "DocumentEvidenceAdmin",
            Name = "DocumentEvidenceAdmin",
        };

        var permissionDocumentRead = new Permission
        {
            Id = Guid.Parse("5afbe086-2802-589e-8c85-54f14b6d4132"),
            Code = "Document.Read",
            Name = "Document Read",
        };

        var permissionDocumentCreate = new Permission
        {
            Id = Guid.Parse("5256fd35-5e6b-5895-a2e8-e70ae96126c1"),
            Code = "Document.Create",
            Name = "Document Create",
        };

        var permissionDocumentUpdate = new Permission
        {
            Id = Guid.Parse("78e9dff4-3b2e-5dcf-b1c7-b7db5bbad620"),
            Code = "Document.Update",
            Name = "Document Update",
        };

        var permissionDocumentDelete = new Permission
        {
            Id = Guid.Parse("4fe0c517-096d-526b-b459-0b52a6ae9b72"),
            Code = "Document.Delete",
            Name = "Document Delete",
        };

        var permissionStoredObjectRead = new Permission
        {
            Id = Guid.Parse("ccefc7db-7bf6-598e-ae00-936ba09998bf"),
            Code = "StoredObject.Read",
            Name = "StoredObject Read",
        };

        var permissionStoredObjectCreate = new Permission
        {
            Id = Guid.Parse("ebe2da39-b553-59a9-9138-b93f84c659d1"),
            Code = "StoredObject.Create",
            Name = "StoredObject Create",
        };

        var permissionStoredObjectUpdate = new Permission
        {
            Id = Guid.Parse("c6b5aa38-eedf-58de-ab3e-78dd157fb752"),
            Code = "StoredObject.Update",
            Name = "StoredObject Update",
        };

        var permissionStoredObjectDelete = new Permission
        {
            Id = Guid.Parse("41bc5136-23ab-5bf8-bcce-c8337fe362e3"),
            Code = "StoredObject.Delete",
            Name = "StoredObject Delete",
        };

        var permissionDocumentRevisionRead = new Permission
        {
            Id = Guid.Parse("11e68fd1-49c3-5623-965b-1c88a43da3a4"),
            Code = "DocumentRevision.Read",
            Name = "DocumentRevision Read",
        };

        var permissionDocumentRevisionCreate = new Permission
        {
            Id = Guid.Parse("f721c0b4-eeef-5e38-a874-197b06572eb3"),
            Code = "DocumentRevision.Create",
            Name = "DocumentRevision Create",
        };

        var permissionDocumentRevisionUpdate = new Permission
        {
            Id = Guid.Parse("c0139d58-3281-51d0-ad07-c41a0d0e48c1"),
            Code = "DocumentRevision.Update",
            Name = "DocumentRevision Update",
        };

        var permissionDocumentRevisionDelete = new Permission
        {
            Id = Guid.Parse("5a987fbb-eede-5a6f-aaf5-7d1b1a1cadbf"),
            Code = "DocumentRevision.Delete",
            Name = "DocumentRevision Delete",
        };

        var permissionProcessingJobRead = new Permission
        {
            Id = Guid.Parse("08fc8e8f-f7a5-58ee-9173-aeb6a5cf2fc1"),
            Code = "ProcessingJob.Read",
            Name = "ProcessingJob Read",
        };

        var permissionProcessingJobCreate = new Permission
        {
            Id = Guid.Parse("0bb5c1b3-70a7-5cff-9086-56f791b64cb8"),
            Code = "ProcessingJob.Create",
            Name = "ProcessingJob Create",
        };

        var permissionProcessingJobUpdate = new Permission
        {
            Id = Guid.Parse("8314043c-f6fa-5ede-bb00-1e2660a4fd97"),
            Code = "ProcessingJob.Update",
            Name = "ProcessingJob Update",
        };

        var permissionProcessingJobDelete = new Permission
        {
            Id = Guid.Parse("ad5bb88e-e72b-5f7c-8074-62ab601ccf3a"),
            Code = "ProcessingJob.Delete",
            Name = "ProcessingJob Delete",
        };

        var permissionDocumentFragmentRead = new Permission
        {
            Id = Guid.Parse("e54e309e-d29f-5427-aa9e-506ba9e28f5c"),
            Code = "DocumentFragment.Read",
            Name = "DocumentFragment Read",
        };

        var permissionDocumentFragmentCreate = new Permission
        {
            Id = Guid.Parse("6abb07b0-0c88-56db-8fc1-604e1c8393ee"),
            Code = "DocumentFragment.Create",
            Name = "DocumentFragment Create",
        };

        var permissionDocumentFragmentUpdate = new Permission
        {
            Id = Guid.Parse("e59ab66e-cc03-5745-bb2e-dd7b23c2061f"),
            Code = "DocumentFragment.Update",
            Name = "DocumentFragment Update",
        };

        var permissionDocumentFragmentDelete = new Permission
        {
            Id = Guid.Parse("e9f3cf0c-3a78-5773-8a72-5c31c37af08d"),
            Code = "DocumentFragment.Delete",
            Name = "DocumentFragment Delete",
        };

        var rolePermissionDocumentEvidenceAdminDocumentRead = new RolePermission
        {
            Id = Guid.Parse("b3b19c6a-7cd1-56c2-a708-499e9052c650"),
            RoleId = Guid.Parse("8c22fcbe-2728-5859-8169-7372a95003a9"),
            PermissionId = Guid.Parse("5afbe086-2802-589e-8c85-54f14b6d4132"),
        };

        var rolePermissionDocumentEvidenceAdminDocumentCreate = new RolePermission
        {
            Id = Guid.Parse("8c172387-5d7e-5e9c-bbb4-a8b0c89ada8c"),
            RoleId = Guid.Parse("8c22fcbe-2728-5859-8169-7372a95003a9"),
            PermissionId = Guid.Parse("5256fd35-5e6b-5895-a2e8-e70ae96126c1"),
        };

        var rolePermissionDocumentEvidenceAdminDocumentUpdate = new RolePermission
        {
            Id = Guid.Parse("1260d6c0-ff3c-517b-8861-8b83b657b43e"),
            RoleId = Guid.Parse("8c22fcbe-2728-5859-8169-7372a95003a9"),
            PermissionId = Guid.Parse("78e9dff4-3b2e-5dcf-b1c7-b7db5bbad620"),
        };

        var rolePermissionDocumentEvidenceAdminDocumentDelete = new RolePermission
        {
            Id = Guid.Parse("691421f3-ad8c-5715-9a1a-80c7a6ef5e5b"),
            RoleId = Guid.Parse("8c22fcbe-2728-5859-8169-7372a95003a9"),
            PermissionId = Guid.Parse("4fe0c517-096d-526b-b459-0b52a6ae9b72"),
        };

        var rolePermissionDocumentEvidenceAdminStoredObjectRead = new RolePermission
        {
            Id = Guid.Parse("a32dbd11-43c6-59ba-a3e1-95731dbd9310"),
            RoleId = Guid.Parse("8c22fcbe-2728-5859-8169-7372a95003a9"),
            PermissionId = Guid.Parse("ccefc7db-7bf6-598e-ae00-936ba09998bf"),
        };

        var rolePermissionDocumentEvidenceAdminStoredObjectCreate = new RolePermission
        {
            Id = Guid.Parse("2c458fa6-803e-5dac-8586-27defe278bc0"),
            RoleId = Guid.Parse("8c22fcbe-2728-5859-8169-7372a95003a9"),
            PermissionId = Guid.Parse("ebe2da39-b553-59a9-9138-b93f84c659d1"),
        };

        var rolePermissionDocumentEvidenceAdminStoredObjectUpdate = new RolePermission
        {
            Id = Guid.Parse("ae68b79b-7be2-5796-842c-b11c80b0137f"),
            RoleId = Guid.Parse("8c22fcbe-2728-5859-8169-7372a95003a9"),
            PermissionId = Guid.Parse("c6b5aa38-eedf-58de-ab3e-78dd157fb752"),
        };

        var rolePermissionDocumentEvidenceAdminStoredObjectDelete = new RolePermission
        {
            Id = Guid.Parse("4f5dc843-a572-5640-8761-21ba89e1abca"),
            RoleId = Guid.Parse("8c22fcbe-2728-5859-8169-7372a95003a9"),
            PermissionId = Guid.Parse("41bc5136-23ab-5bf8-bcce-c8337fe362e3"),
        };

        var rolePermissionDocumentEvidenceAdminDocumentRevisionRead = new RolePermission
        {
            Id = Guid.Parse("583fa121-6195-5489-8de1-cf7483f1d1bf"),
            RoleId = Guid.Parse("8c22fcbe-2728-5859-8169-7372a95003a9"),
            PermissionId = Guid.Parse("11e68fd1-49c3-5623-965b-1c88a43da3a4"),
        };

        var rolePermissionDocumentEvidenceAdminDocumentRevisionCreate = new RolePermission
        {
            Id = Guid.Parse("2127f17b-7111-57ae-8087-2a2385f040a8"),
            RoleId = Guid.Parse("8c22fcbe-2728-5859-8169-7372a95003a9"),
            PermissionId = Guid.Parse("f721c0b4-eeef-5e38-a874-197b06572eb3"),
        };

        var rolePermissionDocumentEvidenceAdminDocumentRevisionUpdate = new RolePermission
        {
            Id = Guid.Parse("d5fbb199-0f23-505b-b8d8-deece39a051e"),
            RoleId = Guid.Parse("8c22fcbe-2728-5859-8169-7372a95003a9"),
            PermissionId = Guid.Parse("c0139d58-3281-51d0-ad07-c41a0d0e48c1"),
        };

        var rolePermissionDocumentEvidenceAdminDocumentRevisionDelete = new RolePermission
        {
            Id = Guid.Parse("c73976f3-59e9-570f-be92-da9190864f14"),
            RoleId = Guid.Parse("8c22fcbe-2728-5859-8169-7372a95003a9"),
            PermissionId = Guid.Parse("5a987fbb-eede-5a6f-aaf5-7d1b1a1cadbf"),
        };

        var rolePermissionDocumentEvidenceAdminProcessingJobRead = new RolePermission
        {
            Id = Guid.Parse("76d2aa3f-4c9e-5c2e-ae83-1a24487857b0"),
            RoleId = Guid.Parse("8c22fcbe-2728-5859-8169-7372a95003a9"),
            PermissionId = Guid.Parse("08fc8e8f-f7a5-58ee-9173-aeb6a5cf2fc1"),
        };

        var rolePermissionDocumentEvidenceAdminProcessingJobCreate = new RolePermission
        {
            Id = Guid.Parse("9cbe2c76-1b88-516e-ae11-19ac04b7ae8c"),
            RoleId = Guid.Parse("8c22fcbe-2728-5859-8169-7372a95003a9"),
            PermissionId = Guid.Parse("0bb5c1b3-70a7-5cff-9086-56f791b64cb8"),
        };

        var rolePermissionDocumentEvidenceAdminProcessingJobUpdate = new RolePermission
        {
            Id = Guid.Parse("ee3e2afd-20ad-53f4-903e-39b304231575"),
            RoleId = Guid.Parse("8c22fcbe-2728-5859-8169-7372a95003a9"),
            PermissionId = Guid.Parse("8314043c-f6fa-5ede-bb00-1e2660a4fd97"),
        };

        var rolePermissionDocumentEvidenceAdminProcessingJobDelete = new RolePermission
        {
            Id = Guid.Parse("417a4e10-2acc-5337-b2ca-979585684540"),
            RoleId = Guid.Parse("8c22fcbe-2728-5859-8169-7372a95003a9"),
            PermissionId = Guid.Parse("ad5bb88e-e72b-5f7c-8074-62ab601ccf3a"),
        };

        var rolePermissionDocumentEvidenceAdminDocumentFragmentRead = new RolePermission
        {
            Id = Guid.Parse("056d1bca-cc2e-5a82-b079-0c6f4842c93d"),
            RoleId = Guid.Parse("8c22fcbe-2728-5859-8169-7372a95003a9"),
            PermissionId = Guid.Parse("e54e309e-d29f-5427-aa9e-506ba9e28f5c"),
        };

        var rolePermissionDocumentEvidenceAdminDocumentFragmentCreate = new RolePermission
        {
            Id = Guid.Parse("25949b3f-737e-54bc-a386-6bc5c14ce138"),
            RoleId = Guid.Parse("8c22fcbe-2728-5859-8169-7372a95003a9"),
            PermissionId = Guid.Parse("6abb07b0-0c88-56db-8fc1-604e1c8393ee"),
        };

        var rolePermissionDocumentEvidenceAdminDocumentFragmentUpdate = new RolePermission
        {
            Id = Guid.Parse("69cc8700-fdd9-5cda-9c4e-60291fb3c185"),
            RoleId = Guid.Parse("8c22fcbe-2728-5859-8169-7372a95003a9"),
            PermissionId = Guid.Parse("e59ab66e-cc03-5745-bb2e-dd7b23c2061f"),
        };

        var rolePermissionDocumentEvidenceAdminDocumentFragmentDelete = new RolePermission
        {
            Id = Guid.Parse("32072f6b-9fe4-586f-9fad-9e3da79cd437"),
            RoleId = Guid.Parse("8c22fcbe-2728-5859-8169-7372a95003a9"),
            PermissionId = Guid.Parse("e9f3cf0c-3a78-5773-8a72-5c31c37af08d"),
        };


        var document = new Document
        {
            Id = Guid.Parse("c791c94e-c6fb-50f6-950f-af73892638b4"),
            WorkspaceId = Guid.Parse("be697a2a-90aa-58f6-8e4c-977dad799858"),
            DisplayName = "Document DisplayName",
            MediaType = "Document MediaType",
            SourceKind = "Document SourceKind",
            State = "Document State",
            CurrentRevisionNumber = 1,
            IsRevoked = false,
            CreationTime = new DateTime(2026, 1, 1, 0, 0, 0, DateTimeKind.Utc),
            CreatorId = null,
            LastModificationTime = null,
            LastModifierId = null,
            IsDeleted = false,
            DeletionTime = null,
            DeleterId = null,
            DisplayNameSearch = NormalizeSearchValue("Document DisplayName"),
            MediaTypeSearch = NormalizeSearchValue("Document MediaType"),
            SourceKindSearch = NormalizeSearchValue("Document SourceKind"),
            StateSearch = NormalizeSearchValue("Document State"),
        };

        var storedObject = new StoredObject
        {
            Id = Guid.Parse("3c9456db-b91a-5305-adfd-0cd000db2501"),
            Sha256 = "StoredObject Sha256",
            StorageKey = "StoredObject StorageKey",
            SizeBytes = 2,
            MediaType = "StoredObject MediaType",
            CreationTime = new DateTime(2026, 1, 2, 0, 0, 0, DateTimeKind.Utc),
            CreatorId = null,
            LastModificationTime = null,
            LastModifierId = null,
            IsDeleted = false,
            DeletionTime = null,
            DeleterId = null,
            Sha256Search = NormalizeSearchValue("StoredObject Sha256"),
            StorageKeySearch = NormalizeSearchValue("StoredObject StorageKey"),
            MediaTypeSearch = NormalizeSearchValue("StoredObject MediaType"),
        };

        var documentRevision = new DocumentRevision
        {
            Id = Guid.Parse("712dee60-251c-5818-9c1b-e6f9a231c821"),
            DocumentId = Guid.Parse("c791c94e-c6fb-50f6-950f-af73892638b4"),
            StoredObjectId = Guid.Parse("3c9456db-b91a-5305-adfd-0cd000db2501"),
            RevisionNumber = 3,
            State = "DocumentRevision State",
            Adapter = "DocumentRevision Adapter",
            AdapterVersion = "DocumentRevision AdapterVersion",
            ManifestHash = "DocumentRevision ManifestHash",
            CreationTime = new DateTime(2026, 1, 3, 0, 0, 0, DateTimeKind.Utc),
            CreatorId = null,
            LastModificationTime = null,
            LastModifierId = null,
            IsDeleted = false,
            DeletionTime = null,
            DeleterId = null,
            StateSearch = NormalizeSearchValue("DocumentRevision State"),
            AdapterSearch = NormalizeSearchValue("DocumentRevision Adapter"),
            AdapterVersionSearch = NormalizeSearchValue("DocumentRevision AdapterVersion"),
            ManifestHashSearch = NormalizeSearchValue("DocumentRevision ManifestHash"),
        };

        var processingJob = new ProcessingJob
        {
            Id = Guid.Parse("3d5f2be7-c4ed-5022-a214-a5ea3bfdcba5"),
            DocumentRevisionId = Guid.Parse("712dee60-251c-5818-9c1b-e6f9a231c821"),
            Kind = "ProcessingJob Kind",
            State = "ProcessingJob State",
            Attempt = 4,
            IdempotencyKey = "ProcessingJob IdempotencyKey",
            LeaseUntil = default,
            LastErrorCode = "ProcessingJob LastErrorCode",
            CreationTime = new DateTime(2026, 1, 4, 0, 0, 0, DateTimeKind.Utc),
            CreatorId = null,
            LastModificationTime = null,
            LastModifierId = null,
            IsDeleted = false,
            DeletionTime = null,
            DeleterId = null,
            KindSearch = NormalizeSearchValue("ProcessingJob Kind"),
            StateSearch = NormalizeSearchValue("ProcessingJob State"),
            IdempotencyKeySearch = NormalizeSearchValue("ProcessingJob IdempotencyKey"),
            LastErrorCodeSearch = NormalizeSearchValue("ProcessingJob LastErrorCode"),
        };

        var documentFragment = new DocumentFragment
        {
            Id = Guid.Parse("6e5803b9-ff68-565d-917d-2a3a68f0097c"),
            DocumentRevisionId = Guid.Parse("712dee60-251c-5818-9c1b-e6f9a231c821"),
            Sequence = 5,
            Kind = "DocumentFragment Kind",
            AnchorJson = "DocumentFragment AnchorJson",
            Text = "DocumentFragment Text",
            ContentHash = "DocumentFragment ContentHash",
            CreationTime = new DateTime(2026, 1, 5, 0, 0, 0, DateTimeKind.Utc),
            CreatorId = null,
            LastModificationTime = null,
            LastModifierId = null,
            IsDeleted = false,
            DeletionTime = null,
            DeleterId = null,
            KindSearch = NormalizeSearchValue("DocumentFragment Kind"),
            AnchorJsonSearch = NormalizeSearchValue("DocumentFragment AnchorJson"),
            TextSearch = NormalizeSearchValue("DocumentFragment Text"),
            ContentHashSearch = NormalizeSearchValue("DocumentFragment ContentHash"),
        };

        if (!await db.Roles.AnyAsync(x => x.Code == "DocumentEvidenceAdmin", cancellationToken))
        {
            db.Roles.Add(roleDocumentEvidenceAdmin);
        }

        if (!await db.Permissions.AnyAsync(x => x.Code == "Document.Read", cancellationToken))
        {
            db.Permissions.Add(permissionDocumentRead);
        }

        if (!await db.Permissions.AnyAsync(x => x.Code == "Document.Create", cancellationToken))
        {
            db.Permissions.Add(permissionDocumentCreate);
        }

        if (!await db.Permissions.AnyAsync(x => x.Code == "Document.Update", cancellationToken))
        {
            db.Permissions.Add(permissionDocumentUpdate);
        }

        if (!await db.Permissions.AnyAsync(x => x.Code == "Document.Delete", cancellationToken))
        {
            db.Permissions.Add(permissionDocumentDelete);
        }

        if (!await db.Permissions.AnyAsync(x => x.Code == "StoredObject.Read", cancellationToken))
        {
            db.Permissions.Add(permissionStoredObjectRead);
        }

        if (!await db.Permissions.AnyAsync(x => x.Code == "StoredObject.Create", cancellationToken))
        {
            db.Permissions.Add(permissionStoredObjectCreate);
        }

        if (!await db.Permissions.AnyAsync(x => x.Code == "StoredObject.Update", cancellationToken))
        {
            db.Permissions.Add(permissionStoredObjectUpdate);
        }

        if (!await db.Permissions.AnyAsync(x => x.Code == "StoredObject.Delete", cancellationToken))
        {
            db.Permissions.Add(permissionStoredObjectDelete);
        }

        if (!await db.Permissions.AnyAsync(x => x.Code == "DocumentRevision.Read", cancellationToken))
        {
            db.Permissions.Add(permissionDocumentRevisionRead);
        }

        if (!await db.Permissions.AnyAsync(x => x.Code == "DocumentRevision.Create", cancellationToken))
        {
            db.Permissions.Add(permissionDocumentRevisionCreate);
        }

        if (!await db.Permissions.AnyAsync(x => x.Code == "DocumentRevision.Update", cancellationToken))
        {
            db.Permissions.Add(permissionDocumentRevisionUpdate);
        }

        if (!await db.Permissions.AnyAsync(x => x.Code == "DocumentRevision.Delete", cancellationToken))
        {
            db.Permissions.Add(permissionDocumentRevisionDelete);
        }

        if (!await db.Permissions.AnyAsync(x => x.Code == "ProcessingJob.Read", cancellationToken))
        {
            db.Permissions.Add(permissionProcessingJobRead);
        }

        if (!await db.Permissions.AnyAsync(x => x.Code == "ProcessingJob.Create", cancellationToken))
        {
            db.Permissions.Add(permissionProcessingJobCreate);
        }

        if (!await db.Permissions.AnyAsync(x => x.Code == "ProcessingJob.Update", cancellationToken))
        {
            db.Permissions.Add(permissionProcessingJobUpdate);
        }

        if (!await db.Permissions.AnyAsync(x => x.Code == "ProcessingJob.Delete", cancellationToken))
        {
            db.Permissions.Add(permissionProcessingJobDelete);
        }

        if (!await db.Permissions.AnyAsync(x => x.Code == "DocumentFragment.Read", cancellationToken))
        {
            db.Permissions.Add(permissionDocumentFragmentRead);
        }

        if (!await db.Permissions.AnyAsync(x => x.Code == "DocumentFragment.Create", cancellationToken))
        {
            db.Permissions.Add(permissionDocumentFragmentCreate);
        }

        if (!await db.Permissions.AnyAsync(x => x.Code == "DocumentFragment.Update", cancellationToken))
        {
            db.Permissions.Add(permissionDocumentFragmentUpdate);
        }

        if (!await db.Permissions.AnyAsync(x => x.Code == "DocumentFragment.Delete", cancellationToken))
        {
            db.Permissions.Add(permissionDocumentFragmentDelete);
        }

        if (!await db.RolePermissions.AnyAsync(x => x.RoleId == rolePermissionDocumentEvidenceAdminDocumentRead.RoleId && x.PermissionId == rolePermissionDocumentEvidenceAdminDocumentRead.PermissionId, cancellationToken))
        {
            db.RolePermissions.Add(rolePermissionDocumentEvidenceAdminDocumentRead);
        }

        if (!await db.RolePermissions.AnyAsync(x => x.RoleId == rolePermissionDocumentEvidenceAdminDocumentCreate.RoleId && x.PermissionId == rolePermissionDocumentEvidenceAdminDocumentCreate.PermissionId, cancellationToken))
        {
            db.RolePermissions.Add(rolePermissionDocumentEvidenceAdminDocumentCreate);
        }

        if (!await db.RolePermissions.AnyAsync(x => x.RoleId == rolePermissionDocumentEvidenceAdminDocumentUpdate.RoleId && x.PermissionId == rolePermissionDocumentEvidenceAdminDocumentUpdate.PermissionId, cancellationToken))
        {
            db.RolePermissions.Add(rolePermissionDocumentEvidenceAdminDocumentUpdate);
        }

        if (!await db.RolePermissions.AnyAsync(x => x.RoleId == rolePermissionDocumentEvidenceAdminDocumentDelete.RoleId && x.PermissionId == rolePermissionDocumentEvidenceAdminDocumentDelete.PermissionId, cancellationToken))
        {
            db.RolePermissions.Add(rolePermissionDocumentEvidenceAdminDocumentDelete);
        }

        if (!await db.RolePermissions.AnyAsync(x => x.RoleId == rolePermissionDocumentEvidenceAdminStoredObjectRead.RoleId && x.PermissionId == rolePermissionDocumentEvidenceAdminStoredObjectRead.PermissionId, cancellationToken))
        {
            db.RolePermissions.Add(rolePermissionDocumentEvidenceAdminStoredObjectRead);
        }

        if (!await db.RolePermissions.AnyAsync(x => x.RoleId == rolePermissionDocumentEvidenceAdminStoredObjectCreate.RoleId && x.PermissionId == rolePermissionDocumentEvidenceAdminStoredObjectCreate.PermissionId, cancellationToken))
        {
            db.RolePermissions.Add(rolePermissionDocumentEvidenceAdminStoredObjectCreate);
        }

        if (!await db.RolePermissions.AnyAsync(x => x.RoleId == rolePermissionDocumentEvidenceAdminStoredObjectUpdate.RoleId && x.PermissionId == rolePermissionDocumentEvidenceAdminStoredObjectUpdate.PermissionId, cancellationToken))
        {
            db.RolePermissions.Add(rolePermissionDocumentEvidenceAdminStoredObjectUpdate);
        }

        if (!await db.RolePermissions.AnyAsync(x => x.RoleId == rolePermissionDocumentEvidenceAdminStoredObjectDelete.RoleId && x.PermissionId == rolePermissionDocumentEvidenceAdminStoredObjectDelete.PermissionId, cancellationToken))
        {
            db.RolePermissions.Add(rolePermissionDocumentEvidenceAdminStoredObjectDelete);
        }

        if (!await db.RolePermissions.AnyAsync(x => x.RoleId == rolePermissionDocumentEvidenceAdminDocumentRevisionRead.RoleId && x.PermissionId == rolePermissionDocumentEvidenceAdminDocumentRevisionRead.PermissionId, cancellationToken))
        {
            db.RolePermissions.Add(rolePermissionDocumentEvidenceAdminDocumentRevisionRead);
        }

        if (!await db.RolePermissions.AnyAsync(x => x.RoleId == rolePermissionDocumentEvidenceAdminDocumentRevisionCreate.RoleId && x.PermissionId == rolePermissionDocumentEvidenceAdminDocumentRevisionCreate.PermissionId, cancellationToken))
        {
            db.RolePermissions.Add(rolePermissionDocumentEvidenceAdminDocumentRevisionCreate);
        }

        if (!await db.RolePermissions.AnyAsync(x => x.RoleId == rolePermissionDocumentEvidenceAdminDocumentRevisionUpdate.RoleId && x.PermissionId == rolePermissionDocumentEvidenceAdminDocumentRevisionUpdate.PermissionId, cancellationToken))
        {
            db.RolePermissions.Add(rolePermissionDocumentEvidenceAdminDocumentRevisionUpdate);
        }

        if (!await db.RolePermissions.AnyAsync(x => x.RoleId == rolePermissionDocumentEvidenceAdminDocumentRevisionDelete.RoleId && x.PermissionId == rolePermissionDocumentEvidenceAdminDocumentRevisionDelete.PermissionId, cancellationToken))
        {
            db.RolePermissions.Add(rolePermissionDocumentEvidenceAdminDocumentRevisionDelete);
        }

        if (!await db.RolePermissions.AnyAsync(x => x.RoleId == rolePermissionDocumentEvidenceAdminProcessingJobRead.RoleId && x.PermissionId == rolePermissionDocumentEvidenceAdminProcessingJobRead.PermissionId, cancellationToken))
        {
            db.RolePermissions.Add(rolePermissionDocumentEvidenceAdminProcessingJobRead);
        }

        if (!await db.RolePermissions.AnyAsync(x => x.RoleId == rolePermissionDocumentEvidenceAdminProcessingJobCreate.RoleId && x.PermissionId == rolePermissionDocumentEvidenceAdminProcessingJobCreate.PermissionId, cancellationToken))
        {
            db.RolePermissions.Add(rolePermissionDocumentEvidenceAdminProcessingJobCreate);
        }

        if (!await db.RolePermissions.AnyAsync(x => x.RoleId == rolePermissionDocumentEvidenceAdminProcessingJobUpdate.RoleId && x.PermissionId == rolePermissionDocumentEvidenceAdminProcessingJobUpdate.PermissionId, cancellationToken))
        {
            db.RolePermissions.Add(rolePermissionDocumentEvidenceAdminProcessingJobUpdate);
        }

        if (!await db.RolePermissions.AnyAsync(x => x.RoleId == rolePermissionDocumentEvidenceAdminProcessingJobDelete.RoleId && x.PermissionId == rolePermissionDocumentEvidenceAdminProcessingJobDelete.PermissionId, cancellationToken))
        {
            db.RolePermissions.Add(rolePermissionDocumentEvidenceAdminProcessingJobDelete);
        }

        if (!await db.RolePermissions.AnyAsync(x => x.RoleId == rolePermissionDocumentEvidenceAdminDocumentFragmentRead.RoleId && x.PermissionId == rolePermissionDocumentEvidenceAdminDocumentFragmentRead.PermissionId, cancellationToken))
        {
            db.RolePermissions.Add(rolePermissionDocumentEvidenceAdminDocumentFragmentRead);
        }

        if (!await db.RolePermissions.AnyAsync(x => x.RoleId == rolePermissionDocumentEvidenceAdminDocumentFragmentCreate.RoleId && x.PermissionId == rolePermissionDocumentEvidenceAdminDocumentFragmentCreate.PermissionId, cancellationToken))
        {
            db.RolePermissions.Add(rolePermissionDocumentEvidenceAdminDocumentFragmentCreate);
        }

        if (!await db.RolePermissions.AnyAsync(x => x.RoleId == rolePermissionDocumentEvidenceAdminDocumentFragmentUpdate.RoleId && x.PermissionId == rolePermissionDocumentEvidenceAdminDocumentFragmentUpdate.PermissionId, cancellationToken))
        {
            db.RolePermissions.Add(rolePermissionDocumentEvidenceAdminDocumentFragmentUpdate);
        }

        if (!await db.RolePermissions.AnyAsync(x => x.RoleId == rolePermissionDocumentEvidenceAdminDocumentFragmentDelete.RoleId && x.PermissionId == rolePermissionDocumentEvidenceAdminDocumentFragmentDelete.PermissionId, cancellationToken))
        {
            db.RolePermissions.Add(rolePermissionDocumentEvidenceAdminDocumentFragmentDelete);
        }

        if (!await db.Documents.AnyAsync(cancellationToken))
        {
            db.Documents.Add(document);
            db.StoredObjects.Add(storedObject);
            db.DocumentRevisions.Add(documentRevision);
            db.ProcessingJobs.Add(processingJob);
            db.DocumentFragments.Add(documentFragment);
        }
        await db.SaveChangesAsync(cancellationToken);
    }

    private static async Task UpsertSeedHistoryAsync(
        DocumentEvidenceOperationalModelDbContext db,
        AppForgeSeedHistory entry,
        CancellationToken cancellationToken)
    {
        var existing = await db.AppForgeSeedHistory.FirstOrDefaultAsync(
            x => x.ModelId == entry.ModelId
                && x.ModelVersion == entry.ModelVersion
                && x.SeedSetName == entry.SeedSetName
                && x.TableName == entry.TableName,
            cancellationToken);

        if (existing is null)
        {
            db.AppForgeSeedHistory.Add(entry);
            return;
        }

        existing.SourceMdHash = entry.SourceMdHash;
        existing.SeedHash = entry.SeedHash;
        existing.AppliedAt = entry.AppliedAt;
    }

    private static string NormalizeSearchValue(string? value)
    {
        return value?.Trim().ToUpperInvariant() ?? string.Empty;
    }
}
