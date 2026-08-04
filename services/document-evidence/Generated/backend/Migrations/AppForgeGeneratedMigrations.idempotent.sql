CREATE TABLE IF NOT EXISTS "__EFMigrationsHistory" (
    "MigrationId" character varying(150) NOT NULL,
    "ProductVersion" character varying(32) NOT NULL,
    CONSTRAINT "PK___EFMigrationsHistory" PRIMARY KEY ("MigrationId")
);

START TRANSACTION;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE TABLE "__AppForgeSeedHistory" (
        "Id" uuid NOT NULL,
        "ModelId" character varying(200) NOT NULL,
        "ModelVersion" character varying(100) NOT NULL,
        "SeedSetName" character varying(200) NOT NULL,
        "TableName" character varying(200) NOT NULL,
        "SourceMdHash" character varying(128) NOT NULL,
        "SeedHash" character varying(128) NOT NULL,
        "AppliedAt" timestamp with time zone NOT NULL,
        CONSTRAINT "PK___AppForgeSeedHistory" PRIMARY KEY ("Id")
    );
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE TABLE "AccountRecoveryAttempts" (
        "Id" uuid NOT NULL,
        "EmailHash" character varying(128) NOT NULL,
        "IpHash" character varying(128) NOT NULL,
        "CreatedAtUtc" timestamp with time zone NOT NULL,
        CONSTRAINT "PK_AccountRecoveryAttempts" PRIMARY KEY ("Id")
    );
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE TABLE "AppUserRoles" (
        "Id" uuid NOT NULL,
        "AppUserId" uuid NOT NULL,
        "RoleId" uuid NOT NULL,
        CONSTRAINT "PK_AppUserRoles" PRIMARY KEY ("Id")
    );
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE TABLE "AppUsers" (
        "Id" uuid NOT NULL,
        "Email" character varying(320) NOT NULL,
        "UserName" character varying(200) NOT NULL,
        "PasswordHash" character varying(1000) NOT NULL,
        "EmailConfirmed" boolean NOT NULL,
        "IsActive" boolean NOT NULL,
        "MustChangePassword" boolean NOT NULL,
        "CreatedAtUtc" timestamp with time zone NOT NULL,
        "UpdatedAtUtc" timestamp with time zone NOT NULL,
        CONSTRAINT "PK_AppUsers" PRIMARY KEY ("Id")
    );
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE TABLE "AppUserSessions" (
        "Id" uuid NOT NULL,
        "AppUserId" uuid NOT NULL,
        "AccessTokenHash" character varying(128) NOT NULL,
        "RefreshTokenHash" character varying(128) NOT NULL,
        "AccessTokenExpiresAtUtc" timestamp with time zone NOT NULL,
        "RefreshTokenExpiresAtUtc" timestamp with time zone NOT NULL,
        "RevokedAtUtc" timestamp with time zone,
        "CreatedAtUtc" timestamp with time zone NOT NULL,
        CONSTRAINT "PK_AppUserSessions" PRIMARY KEY ("Id")
    );
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE TABLE "AuthLoginAttempts" (
        "Id" uuid NOT NULL,
        "LoginHash" character varying(128) NOT NULL,
        "IpHash" character varying(128) NOT NULL,
        "Succeeded" boolean NOT NULL,
        "CreatedAtUtc" timestamp with time zone NOT NULL,
        CONSTRAINT "PK_AuthLoginAttempts" PRIMARY KEY ("Id")
    );
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE TABLE "EmailConfirmationTokens" (
        "Id" uuid NOT NULL,
        "AppUserId" uuid NOT NULL,
        "TokenHash" character varying(128) NOT NULL,
        "ExpiresAtUtc" timestamp with time zone NOT NULL,
        "UsedAtUtc" timestamp with time zone,
        "CreatedAtUtc" timestamp with time zone NOT NULL,
        CONSTRAINT "PK_EmailConfirmationTokens" PRIMARY KEY ("Id")
    );
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE TABLE "IdentityAuditLogs" (
        "Id" uuid NOT NULL,
        "CreatedAtUtc" timestamp with time zone NOT NULL,
        "Action" character varying(120) NOT NULL,
        "ActorUserId" uuid,
        "ActorEmail" character varying(320) NOT NULL,
        "TargetUserId" uuid,
        "TargetEmail" character varying(320) NOT NULL,
        "Details" character varying(1000) NOT NULL,
        CONSTRAINT "PK_IdentityAuditLogs" PRIMARY KEY ("Id")
    );
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE TABLE "PasswordResetTokens" (
        "Id" uuid NOT NULL,
        "AppUserId" uuid NOT NULL,
        "TokenHash" character varying(128) NOT NULL,
        "ExpiresAtUtc" timestamp with time zone NOT NULL,
        "UsedAtUtc" timestamp with time zone,
        "CreatedAtUtc" timestamp with time zone NOT NULL,
        CONSTRAINT "PK_PasswordResetTokens" PRIMARY KEY ("Id")
    );
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE TABLE "Permissions" (
        "Id" uuid NOT NULL,
        "Code" character varying(200) NOT NULL,
        "Name" character varying(200) NOT NULL,
        CONSTRAINT "PK_Permissions" PRIMARY KEY ("Id")
    );
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE TABLE "PublicRegistrationAttempts" (
        "Id" uuid NOT NULL,
        "EmailHash" character varying(128) NOT NULL,
        "IpHash" character varying(128) NOT NULL,
        "Succeeded" boolean NOT NULL,
        "CreatedAtUtc" timestamp with time zone NOT NULL,
        CONSTRAINT "PK_PublicRegistrationAttempts" PRIMARY KEY ("Id")
    );
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE TABLE "Roles" (
        "Id" uuid NOT NULL,
        "Code" character varying(128) NOT NULL,
        "Name" character varying(200) NOT NULL,
        CONSTRAINT "PK_Roles" PRIMARY KEY ("Id")
    );
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE TABLE "StaffPositions" (
        "Id" uuid NOT NULL,
        "Code" character varying(128) NOT NULL,
        "Name" character varying(200) NOT NULL,
        "Description" character varying(1000),
        "ParentPositionId" uuid,
        "IsActive" boolean NOT NULL,
        CONSTRAINT "PK_StaffPositions" PRIMARY KEY ("Id"),
        CONSTRAINT "FK_StaffPositions_StaffPositions_ParentPositionId" FOREIGN KEY ("ParentPositionId") REFERENCES "StaffPositions" ("Id")
    );
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE TABLE "UserInvitations" (
        "Id" uuid NOT NULL,
        "Email" character varying(320) NOT NULL,
        "TokenHash" character varying(128) NOT NULL,
        "RoleCodes" character varying(1000) NOT NULL,
        "ExpiresAtUtc" timestamp with time zone NOT NULL,
        "AcceptedAtUtc" timestamp with time zone,
        "CreatedAtUtc" timestamp with time zone NOT NULL,
        CONSTRAINT "PK_UserInvitations" PRIMARY KEY ("Id")
    );
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE TABLE "RolePermissions" (
        "Id" uuid NOT NULL,
        "RoleId" uuid NOT NULL,
        "PermissionId" uuid NOT NULL,
        CONSTRAINT "PK_RolePermissions" PRIMARY KEY ("Id"),
        CONSTRAINT "FK_RolePermissions_Permissions_PermissionId" FOREIGN KEY ("PermissionId") REFERENCES "Permissions" ("Id") ON DELETE CASCADE,
        CONSTRAINT "FK_RolePermissions_Roles_RoleId" FOREIGN KEY ("RoleId") REFERENCES "Roles" ("Id") ON DELETE CASCADE
    );
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE TABLE "Documents" (
        "Id" uuid NOT NULL,
        "WorkspaceId" uuid NOT NULL,
        "DisplayName" character varying(260) NOT NULL,
        "MediaType" character varying(120) NOT NULL,
        "SourceKind" character varying(40) NOT NULL,
        "State" character varying(40) NOT NULL,
        "CurrentRevisionNumber" integer NOT NULL,
        "IsRevoked" boolean NOT NULL,
        "CreationTime" timestamp with time zone NOT NULL,
        "CreatorId" uuid,
        "CreatorPositionId" uuid,
        "LastModificationTime" timestamp with time zone,
        "LastModifierId" uuid,
        "LastModifierPositionId" uuid,
        "IsDeleted" boolean NOT NULL DEFAULT FALSE,
        "DeletionTime" timestamp with time zone,
        "DeleterId" uuid,
        "DeleterPositionId" uuid,
        "DisplayNameSearch" character varying(260) NOT NULL,
        "MediaTypeSearch" character varying(120) NOT NULL,
        "SourceKindSearch" character varying(40) NOT NULL,
        "StateSearch" character varying(40) NOT NULL,
        CONSTRAINT "PK_Documents" PRIMARY KEY ("Id"),
        CONSTRAINT "FK_Documents_StaffPositions_CreatorPositionId" FOREIGN KEY ("CreatorPositionId") REFERENCES "StaffPositions" ("Id"),
        CONSTRAINT "FK_Documents_StaffPositions_DeleterPositionId" FOREIGN KEY ("DeleterPositionId") REFERENCES "StaffPositions" ("Id"),
        CONSTRAINT "FK_Documents_StaffPositions_LastModifierPositionId" FOREIGN KEY ("LastModifierPositionId") REFERENCES "StaffPositions" ("Id")
    );
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE TABLE "StaffPositionAssignments" (
        "Id" uuid NOT NULL,
        "StaffPositionId" uuid NOT NULL,
        "UserId" uuid NOT NULL,
        "AssignmentKind" character varying(32) NOT NULL,
        "StartsAt" timestamp with time zone NOT NULL,
        "EndsAt" timestamp with time zone,
        "StartsAtUtc" timestamp with time zone NOT NULL,
        "EndsAtUtc" timestamp with time zone,
        "IsActive" boolean NOT NULL,
        "Reason" character varying(500),
        CONSTRAINT "PK_StaffPositionAssignments" PRIMARY KEY ("Id"),
        CONSTRAINT "FK_StaffPositionAssignments_StaffPositions_StaffPositionId" FOREIGN KEY ("StaffPositionId") REFERENCES "StaffPositions" ("Id") ON DELETE CASCADE
    );
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE TABLE "StaffPositionRoles" (
        "Id" uuid NOT NULL,
        "StaffPositionId" uuid NOT NULL,
        "RoleId" uuid NOT NULL,
        CONSTRAINT "PK_StaffPositionRoles" PRIMARY KEY ("Id"),
        CONSTRAINT "FK_StaffPositionRoles_Roles_RoleId" FOREIGN KEY ("RoleId") REFERENCES "Roles" ("Id") ON DELETE CASCADE,
        CONSTRAINT "FK_StaffPositionRoles_StaffPositions_StaffPositionId" FOREIGN KEY ("StaffPositionId") REFERENCES "StaffPositions" ("Id") ON DELETE CASCADE
    );
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE TABLE "StoredObjects" (
        "Id" uuid NOT NULL,
        "Sha256" character varying(64) NOT NULL,
        "StorageKey" character varying(512) NOT NULL,
        "SizeBytes" bigint NOT NULL,
        "MediaType" character varying(120) NOT NULL,
        "CreationTime" timestamp with time zone NOT NULL,
        "CreatorId" uuid,
        "CreatorPositionId" uuid,
        "LastModificationTime" timestamp with time zone,
        "LastModifierId" uuid,
        "LastModifierPositionId" uuid,
        "IsDeleted" boolean NOT NULL DEFAULT FALSE,
        "DeletionTime" timestamp with time zone,
        "DeleterId" uuid,
        "DeleterPositionId" uuid,
        "Sha256Search" character varying(64) NOT NULL,
        "StorageKeySearch" character varying(512) NOT NULL,
        "MediaTypeSearch" character varying(120) NOT NULL,
        CONSTRAINT "PK_StoredObjects" PRIMARY KEY ("Id"),
        CONSTRAINT "FK_StoredObjects_StaffPositions_CreatorPositionId" FOREIGN KEY ("CreatorPositionId") REFERENCES "StaffPositions" ("Id"),
        CONSTRAINT "FK_StoredObjects_StaffPositions_DeleterPositionId" FOREIGN KEY ("DeleterPositionId") REFERENCES "StaffPositions" ("Id"),
        CONSTRAINT "FK_StoredObjects_StaffPositions_LastModifierPositionId" FOREIGN KEY ("LastModifierPositionId") REFERENCES "StaffPositions" ("Id")
    );
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE TABLE "DocumentRevisions" (
        "Id" uuid NOT NULL,
        "DocumentId" uuid NOT NULL,
        "StoredObjectId" uuid NOT NULL,
        "RevisionNumber" integer NOT NULL,
        "State" character varying(40) NOT NULL,
        "Adapter" character varying(120),
        "AdapterVersion" character varying(80),
        "ManifestHash" character varying(64),
        "CreationTime" timestamp with time zone NOT NULL,
        "CreatorId" uuid,
        "CreatorPositionId" uuid,
        "LastModificationTime" timestamp with time zone,
        "LastModifierId" uuid,
        "LastModifierPositionId" uuid,
        "IsDeleted" boolean NOT NULL DEFAULT FALSE,
        "DeletionTime" timestamp with time zone,
        "DeleterId" uuid,
        "DeleterPositionId" uuid,
        "StateSearch" character varying(40) NOT NULL,
        "AdapterSearch" character varying(120) NOT NULL,
        "AdapterVersionSearch" character varying(80) NOT NULL,
        "ManifestHashSearch" character varying(64) NOT NULL,
        CONSTRAINT "PK_DocumentRevisions" PRIMARY KEY ("Id"),
        CONSTRAINT "FK_DocumentRevisions_Documents_DocumentId" FOREIGN KEY ("DocumentId") REFERENCES "Documents" ("Id") ON DELETE CASCADE,
        CONSTRAINT "FK_DocumentRevisions_StaffPositions_CreatorPositionId" FOREIGN KEY ("CreatorPositionId") REFERENCES "StaffPositions" ("Id"),
        CONSTRAINT "FK_DocumentRevisions_StaffPositions_DeleterPositionId" FOREIGN KEY ("DeleterPositionId") REFERENCES "StaffPositions" ("Id"),
        CONSTRAINT "FK_DocumentRevisions_StaffPositions_LastModifierPositionId" FOREIGN KEY ("LastModifierPositionId") REFERENCES "StaffPositions" ("Id"),
        CONSTRAINT "FK_DocumentRevisions_StoredObjects_StoredObjectId" FOREIGN KEY ("StoredObjectId") REFERENCES "StoredObjects" ("Id") ON DELETE CASCADE
    );
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE TABLE "DocumentFragments" (
        "Id" uuid NOT NULL,
        "DocumentRevisionId" uuid NOT NULL,
        "Sequence" integer NOT NULL,
        "Kind" character varying(40) NOT NULL,
        "AnchorJson" character varying(2000) NOT NULL,
        "Text" character varying(8000) NOT NULL,
        "ContentHash" character varying(64) NOT NULL,
        "CreationTime" timestamp with time zone NOT NULL,
        "CreatorId" uuid,
        "CreatorPositionId" uuid,
        "LastModificationTime" timestamp with time zone,
        "LastModifierId" uuid,
        "LastModifierPositionId" uuid,
        "IsDeleted" boolean NOT NULL DEFAULT FALSE,
        "DeletionTime" timestamp with time zone,
        "DeleterId" uuid,
        "DeleterPositionId" uuid,
        "KindSearch" character varying(40) NOT NULL,
        "AnchorJsonSearch" character varying(2000) NOT NULL,
        "TextSearch" character varying(8000) NOT NULL,
        "ContentHashSearch" character varying(64) NOT NULL,
        CONSTRAINT "PK_DocumentFragments" PRIMARY KEY ("Id"),
        CONSTRAINT "FK_DocumentFragments_DocumentRevisions_DocumentRevisionId" FOREIGN KEY ("DocumentRevisionId") REFERENCES "DocumentRevisions" ("Id") ON DELETE CASCADE,
        CONSTRAINT "FK_DocumentFragments_StaffPositions_CreatorPositionId" FOREIGN KEY ("CreatorPositionId") REFERENCES "StaffPositions" ("Id"),
        CONSTRAINT "FK_DocumentFragments_StaffPositions_DeleterPositionId" FOREIGN KEY ("DeleterPositionId") REFERENCES "StaffPositions" ("Id"),
        CONSTRAINT "FK_DocumentFragments_StaffPositions_LastModifierPositionId" FOREIGN KEY ("LastModifierPositionId") REFERENCES "StaffPositions" ("Id")
    );
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE TABLE "ProcessingJobs" (
        "Id" uuid NOT NULL,
        "DocumentRevisionId" uuid NOT NULL,
        "Kind" character varying(80) NOT NULL,
        "State" character varying(40) NOT NULL,
        "Attempt" integer NOT NULL,
        "IdempotencyKey" character varying(160) NOT NULL,
        "LeaseUntil" timestamp with time zone,
        "LastErrorCode" character varying(120),
        "CreationTime" timestamp with time zone NOT NULL,
        "CreatorId" uuid,
        "CreatorPositionId" uuid,
        "LastModificationTime" timestamp with time zone,
        "LastModifierId" uuid,
        "LastModifierPositionId" uuid,
        "IsDeleted" boolean NOT NULL DEFAULT FALSE,
        "DeletionTime" timestamp with time zone,
        "DeleterId" uuid,
        "DeleterPositionId" uuid,
        "KindSearch" character varying(80) NOT NULL,
        "StateSearch" character varying(40) NOT NULL,
        "IdempotencyKeySearch" character varying(160) NOT NULL,
        "LastErrorCodeSearch" character varying(120) NOT NULL,
        CONSTRAINT "PK_ProcessingJobs" PRIMARY KEY ("Id"),
        CONSTRAINT "FK_ProcessingJobs_DocumentRevisions_DocumentRevisionId" FOREIGN KEY ("DocumentRevisionId") REFERENCES "DocumentRevisions" ("Id") ON DELETE CASCADE,
        CONSTRAINT "FK_ProcessingJobs_StaffPositions_CreatorPositionId" FOREIGN KEY ("CreatorPositionId") REFERENCES "StaffPositions" ("Id"),
        CONSTRAINT "FK_ProcessingJobs_StaffPositions_DeleterPositionId" FOREIGN KEY ("DeleterPositionId") REFERENCES "StaffPositions" ("Id"),
        CONSTRAINT "FK_ProcessingJobs_StaffPositions_LastModifierPositionId" FOREIGN KEY ("LastModifierPositionId") REFERENCES "StaffPositions" ("Id")
    );
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE UNIQUE INDEX "IX___AppForgeSeedHistory_Model_SeedSet_Table" ON "__AppForgeSeedHistory" ("ModelId", "ModelVersion", "SeedSetName", "TableName");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_AccountRecoveryAttempts_CreatedAtUtc" ON "AccountRecoveryAttempts" ("CreatedAtUtc");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_AccountRecoveryAttempts_EmailHash" ON "AccountRecoveryAttempts" ("EmailHash");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_AccountRecoveryAttempts_IpHash" ON "AccountRecoveryAttempts" ("IpHash");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE UNIQUE INDEX "IX_AppUserRoles_AppUserId_RoleId" ON "AppUserRoles" ("AppUserId", "RoleId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE UNIQUE INDEX "IX_AppUsers_Email" ON "AppUsers" ("Email");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE UNIQUE INDEX "IX_AppUsers_UserName" ON "AppUsers" ("UserName");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE UNIQUE INDEX "IX_AppUserSessions_AccessTokenHash" ON "AppUserSessions" ("AccessTokenHash");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_AppUserSessions_AppUserId" ON "AppUserSessions" ("AppUserId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE UNIQUE INDEX "IX_AppUserSessions_RefreshTokenHash" ON "AppUserSessions" ("RefreshTokenHash");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_AuthLoginAttempts_CreatedAtUtc" ON "AuthLoginAttempts" ("CreatedAtUtc");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_AuthLoginAttempts_IpHash" ON "AuthLoginAttempts" ("IpHash");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_AuthLoginAttempts_LoginHash" ON "AuthLoginAttempts" ("LoginHash");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_DocumentFragments_AnchorJsonSearch" ON "DocumentFragments" ("AnchorJsonSearch");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_DocumentFragments_ContentHash" ON "DocumentFragments" ("ContentHash");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_DocumentFragments_ContentHashSearch" ON "DocumentFragments" ("ContentHashSearch");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_DocumentFragments_CreatorPositionId" ON "DocumentFragments" ("CreatorPositionId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_DocumentFragments_DeleterPositionId" ON "DocumentFragments" ("DeleterPositionId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_DocumentFragments_IsDeleted" ON "DocumentFragments" ("IsDeleted");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_DocumentFragments_KindSearch" ON "DocumentFragments" ("KindSearch");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_DocumentFragments_LastModifierPositionId" ON "DocumentFragments" ("LastModifierPositionId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_DocumentFragments_TextSearch" ON "DocumentFragments" ("TextSearch");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE UNIQUE INDEX "UX_DocumentFragments_Revision_Sequence" ON "DocumentFragments" ("DocumentRevisionId", "Sequence");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_DocumentRevisions_AdapterSearch" ON "DocumentRevisions" ("AdapterSearch");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_DocumentRevisions_AdapterVersionSearch" ON "DocumentRevisions" ("AdapterVersionSearch");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_DocumentRevisions_CreatorPositionId" ON "DocumentRevisions" ("CreatorPositionId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_DocumentRevisions_DeleterPositionId" ON "DocumentRevisions" ("DeleterPositionId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_DocumentRevisions_IsDeleted" ON "DocumentRevisions" ("IsDeleted");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_DocumentRevisions_LastModifierPositionId" ON "DocumentRevisions" ("LastModifierPositionId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_DocumentRevisions_ManifestHashSearch" ON "DocumentRevisions" ("ManifestHashSearch");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_DocumentRevisions_StateSearch" ON "DocumentRevisions" ("StateSearch");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_DocumentRevisions_StoredObjectId" ON "DocumentRevisions" ("StoredObjectId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE UNIQUE INDEX "UX_DocumentRevisions_DocumentId_RevisionNumber" ON "DocumentRevisions" ("DocumentId", "RevisionNumber");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_Documents_CreatorPositionId" ON "Documents" ("CreatorPositionId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_Documents_DeleterPositionId" ON "Documents" ("DeleterPositionId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_Documents_DisplayNameSearch" ON "Documents" ("DisplayNameSearch");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_Documents_IsDeleted" ON "Documents" ("IsDeleted");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_Documents_LastModifierPositionId" ON "Documents" ("LastModifierPositionId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_Documents_MediaTypeSearch" ON "Documents" ("MediaTypeSearch");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_Documents_SourceKindSearch" ON "Documents" ("SourceKindSearch");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_Documents_StateSearch" ON "Documents" ("StateSearch");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_Documents_WorkspaceId_DisplayName" ON "Documents" ("WorkspaceId", "DisplayName");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_Documents_WorkspaceId_State" ON "Documents" ("WorkspaceId", "State");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_EmailConfirmationTokens_AppUserId" ON "EmailConfirmationTokens" ("AppUserId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE UNIQUE INDEX "IX_EmailConfirmationTokens_TokenHash" ON "EmailConfirmationTokens" ("TokenHash");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_IdentityAuditLogs_Action" ON "IdentityAuditLogs" ("Action");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_IdentityAuditLogs_ActorUserId" ON "IdentityAuditLogs" ("ActorUserId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_IdentityAuditLogs_CreatedAtUtc" ON "IdentityAuditLogs" ("CreatedAtUtc");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_IdentityAuditLogs_TargetUserId" ON "IdentityAuditLogs" ("TargetUserId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_PasswordResetTokens_AppUserId" ON "PasswordResetTokens" ("AppUserId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE UNIQUE INDEX "IX_PasswordResetTokens_TokenHash" ON "PasswordResetTokens" ("TokenHash");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE UNIQUE INDEX "IX_Permissions_Code" ON "Permissions" ("Code");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_ProcessingJobs_CreatorPositionId" ON "ProcessingJobs" ("CreatorPositionId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_ProcessingJobs_DeleterPositionId" ON "ProcessingJobs" ("DeleterPositionId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_ProcessingJobs_DocumentRevisionId" ON "ProcessingJobs" ("DocumentRevisionId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_ProcessingJobs_IdempotencyKeySearch" ON "ProcessingJobs" ("IdempotencyKeySearch");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_ProcessingJobs_IsDeleted" ON "ProcessingJobs" ("IsDeleted");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_ProcessingJobs_KindSearch" ON "ProcessingJobs" ("KindSearch");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_ProcessingJobs_LastErrorCodeSearch" ON "ProcessingJobs" ("LastErrorCodeSearch");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_ProcessingJobs_LastModifierPositionId" ON "ProcessingJobs" ("LastModifierPositionId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_ProcessingJobs_State_LeaseUntil" ON "ProcessingJobs" ("State", "LeaseUntil");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_ProcessingJobs_StateSearch" ON "ProcessingJobs" ("StateSearch");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE UNIQUE INDEX "UX_ProcessingJobs_IdempotencyKey" ON "ProcessingJobs" ("IdempotencyKey");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_PublicRegistrationAttempts_CreatedAtUtc" ON "PublicRegistrationAttempts" ("CreatedAtUtc");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_PublicRegistrationAttempts_EmailHash" ON "PublicRegistrationAttempts" ("EmailHash");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_PublicRegistrationAttempts_IpHash" ON "PublicRegistrationAttempts" ("IpHash");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_RolePermissions_PermissionId" ON "RolePermissions" ("PermissionId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE UNIQUE INDEX "IX_RolePermissions_RoleId_PermissionId" ON "RolePermissions" ("RoleId", "PermissionId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE UNIQUE INDEX "IX_Roles_Code" ON "Roles" ("Code");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_StaffPositionAssignments_IsActive" ON "StaffPositionAssignments" ("IsActive");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_StaffPositionAssignments_StaffPositionId" ON "StaffPositionAssignments" ("StaffPositionId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_StaffPositionAssignments_UserId" ON "StaffPositionAssignments" ("UserId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_StaffPositionAssignments_UserId_StaffPositionId_IsActive" ON "StaffPositionAssignments" ("UserId", "StaffPositionId", "IsActive");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_StaffPositionRoles_RoleId" ON "StaffPositionRoles" ("RoleId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE UNIQUE INDEX "IX_StaffPositionRoles_StaffPositionId_RoleId" ON "StaffPositionRoles" ("StaffPositionId", "RoleId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE UNIQUE INDEX "IX_StaffPositions_Code" ON "StaffPositions" ("Code");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_StaffPositions_IsActive" ON "StaffPositions" ("IsActive");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_StaffPositions_ParentPositionId" ON "StaffPositions" ("ParentPositionId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_StoredObjects_CreatorPositionId" ON "StoredObjects" ("CreatorPositionId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_StoredObjects_DeleterPositionId" ON "StoredObjects" ("DeleterPositionId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_StoredObjects_IsDeleted" ON "StoredObjects" ("IsDeleted");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_StoredObjects_LastModifierPositionId" ON "StoredObjects" ("LastModifierPositionId");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_StoredObjects_MediaTypeSearch" ON "StoredObjects" ("MediaTypeSearch");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_StoredObjects_Sha256Search" ON "StoredObjects" ("Sha256Search");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_StoredObjects_StorageKeySearch" ON "StoredObjects" ("StorageKeySearch");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE UNIQUE INDEX "UX_StoredObjects_Sha256" ON "StoredObjects" ("Sha256");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE INDEX "IX_UserInvitations_Email" ON "UserInvitations" ("Email");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    CREATE UNIQUE INDEX "IX_UserInvitations_TokenHash" ON "UserInvitations" ("TokenHash");
    END IF;
END $EF$;

DO $EF$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM "__EFMigrationsHistory" WHERE "MigrationId" = '20260804123319_AppForgeGeneratedInitial') THEN
    INSERT INTO "__EFMigrationsHistory" ("MigrationId", "ProductVersion")
    VALUES ('20260804123319_AppForgeGeneratedInitial', '10.0.0');
    END IF;
END $EF$;
COMMIT;
