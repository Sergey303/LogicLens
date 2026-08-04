using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace DocumentEvidenceOperationalModel.Migrations
{
    /// <inheritdoc />
    public partial class AppForgeGeneratedInitial : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "__AppForgeSeedHistory",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    ModelId = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    ModelVersion = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    SeedSetName = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    TableName = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    SourceMdHash = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: false),
                    SeedHash = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: false),
                    AppliedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK___AppForgeSeedHistory", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "AccountRecoveryAttempts",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    EmailHash = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: false),
                    IpHash = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: false),
                    CreatedAtUtc = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_AccountRecoveryAttempts", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "AppUserRoles",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    AppUserId = table.Column<Guid>(type: "uuid", nullable: false),
                    RoleId = table.Column<Guid>(type: "uuid", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_AppUserRoles", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "AppUsers",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    Email = table.Column<string>(type: "character varying(320)", maxLength: 320, nullable: false),
                    UserName = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    PasswordHash = table.Column<string>(type: "character varying(1000)", maxLength: 1000, nullable: false),
                    EmailConfirmed = table.Column<bool>(type: "boolean", nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    MustChangePassword = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAtUtc = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAtUtc = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_AppUsers", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "AppUserSessions",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    AppUserId = table.Column<Guid>(type: "uuid", nullable: false),
                    AccessTokenHash = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: false),
                    RefreshTokenHash = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: false),
                    AccessTokenExpiresAtUtc = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    RefreshTokenExpiresAtUtc = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    RevokedAtUtc = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    CreatedAtUtc = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_AppUserSessions", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "AuthLoginAttempts",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    LoginHash = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: false),
                    IpHash = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: false),
                    Succeeded = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAtUtc = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_AuthLoginAttempts", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "EmailConfirmationTokens",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    AppUserId = table.Column<Guid>(type: "uuid", nullable: false),
                    TokenHash = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: false),
                    ExpiresAtUtc = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UsedAtUtc = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    CreatedAtUtc = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_EmailConfirmationTokens", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "IdentityAuditLogs",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    CreatedAtUtc = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    Action = table.Column<string>(type: "character varying(120)", maxLength: 120, nullable: false),
                    ActorUserId = table.Column<Guid>(type: "uuid", nullable: true),
                    ActorEmail = table.Column<string>(type: "character varying(320)", maxLength: 320, nullable: false),
                    TargetUserId = table.Column<Guid>(type: "uuid", nullable: true),
                    TargetEmail = table.Column<string>(type: "character varying(320)", maxLength: 320, nullable: false),
                    Details = table.Column<string>(type: "character varying(1000)", maxLength: 1000, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_IdentityAuditLogs", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "PasswordResetTokens",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    AppUserId = table.Column<Guid>(type: "uuid", nullable: false),
                    TokenHash = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: false),
                    ExpiresAtUtc = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UsedAtUtc = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    CreatedAtUtc = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_PasswordResetTokens", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "Permissions",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    Code = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    Name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Permissions", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "PublicRegistrationAttempts",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    EmailHash = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: false),
                    IpHash = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: false),
                    Succeeded = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAtUtc = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_PublicRegistrationAttempts", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "Roles",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    Code = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: false),
                    Name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Roles", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "StaffPositions",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    Code = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: false),
                    Name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    Description = table.Column<string>(type: "character varying(1000)", maxLength: 1000, nullable: true),
                    ParentPositionId = table.Column<Guid>(type: "uuid", nullable: true),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_StaffPositions", x => x.Id);
                    table.ForeignKey(
                        name: "FK_StaffPositions_StaffPositions_ParentPositionId",
                        column: x => x.ParentPositionId,
                        principalTable: "StaffPositions",
                        principalColumn: "Id");
                });

            migrationBuilder.CreateTable(
                name: "UserInvitations",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    Email = table.Column<string>(type: "character varying(320)", maxLength: 320, nullable: false),
                    TokenHash = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: false),
                    RoleCodes = table.Column<string>(type: "character varying(1000)", maxLength: 1000, nullable: false),
                    ExpiresAtUtc = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    AcceptedAtUtc = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    CreatedAtUtc = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_UserInvitations", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "RolePermissions",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    RoleId = table.Column<Guid>(type: "uuid", nullable: false),
                    PermissionId = table.Column<Guid>(type: "uuid", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_RolePermissions", x => x.Id);
                    table.ForeignKey(
                        name: "FK_RolePermissions_Permissions_PermissionId",
                        column: x => x.PermissionId,
                        principalTable: "Permissions",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_RolePermissions_Roles_RoleId",
                        column: x => x.RoleId,
                        principalTable: "Roles",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Documents",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    WorkspaceId = table.Column<Guid>(type: "uuid", nullable: false),
                    DisplayName = table.Column<string>(type: "character varying(260)", maxLength: 260, nullable: false),
                    MediaType = table.Column<string>(type: "character varying(120)", maxLength: 120, nullable: false),
                    SourceKind = table.Column<string>(type: "character varying(40)", maxLength: 40, nullable: false),
                    State = table.Column<string>(type: "character varying(40)", maxLength: 40, nullable: false),
                    CurrentRevisionNumber = table.Column<int>(type: "integer", nullable: false),
                    IsRevoked = table.Column<bool>(type: "boolean", nullable: false),
                    CreationTime = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    CreatorId = table.Column<Guid>(type: "uuid", nullable: true),
                    CreatorPositionId = table.Column<Guid>(type: "uuid", nullable: true),
                    LastModificationTime = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    LastModifierId = table.Column<Guid>(type: "uuid", nullable: true),
                    LastModifierPositionId = table.Column<Guid>(type: "uuid", nullable: true),
                    IsDeleted = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                    DeletionTime = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    DeleterId = table.Column<Guid>(type: "uuid", nullable: true),
                    DeleterPositionId = table.Column<Guid>(type: "uuid", nullable: true),
                    DisplayNameSearch = table.Column<string>(type: "character varying(260)", maxLength: 260, nullable: false),
                    MediaTypeSearch = table.Column<string>(type: "character varying(120)", maxLength: 120, nullable: false),
                    SourceKindSearch = table.Column<string>(type: "character varying(40)", maxLength: 40, nullable: false),
                    StateSearch = table.Column<string>(type: "character varying(40)", maxLength: 40, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Documents", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Documents_StaffPositions_CreatorPositionId",
                        column: x => x.CreatorPositionId,
                        principalTable: "StaffPositions",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_Documents_StaffPositions_DeleterPositionId",
                        column: x => x.DeleterPositionId,
                        principalTable: "StaffPositions",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_Documents_StaffPositions_LastModifierPositionId",
                        column: x => x.LastModifierPositionId,
                        principalTable: "StaffPositions",
                        principalColumn: "Id");
                });

            migrationBuilder.CreateTable(
                name: "StaffPositionAssignments",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    StaffPositionId = table.Column<Guid>(type: "uuid", nullable: false),
                    UserId = table.Column<Guid>(type: "uuid", nullable: false),
                    AssignmentKind = table.Column<string>(type: "character varying(32)", maxLength: 32, nullable: false),
                    StartsAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    EndsAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    StartsAtUtc = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    EndsAtUtc = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    Reason = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_StaffPositionAssignments", x => x.Id);
                    table.ForeignKey(
                        name: "FK_StaffPositionAssignments_StaffPositions_StaffPositionId",
                        column: x => x.StaffPositionId,
                        principalTable: "StaffPositions",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "StaffPositionRoles",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    StaffPositionId = table.Column<Guid>(type: "uuid", nullable: false),
                    RoleId = table.Column<Guid>(type: "uuid", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_StaffPositionRoles", x => x.Id);
                    table.ForeignKey(
                        name: "FK_StaffPositionRoles_Roles_RoleId",
                        column: x => x.RoleId,
                        principalTable: "Roles",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_StaffPositionRoles_StaffPositions_StaffPositionId",
                        column: x => x.StaffPositionId,
                        principalTable: "StaffPositions",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "StoredObjects",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    Sha256 = table.Column<string>(type: "character varying(64)", maxLength: 64, nullable: false),
                    StorageKey = table.Column<string>(type: "character varying(512)", maxLength: 512, nullable: false),
                    SizeBytes = table.Column<long>(type: "bigint", nullable: false),
                    MediaType = table.Column<string>(type: "character varying(120)", maxLength: 120, nullable: false),
                    CreationTime = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    CreatorId = table.Column<Guid>(type: "uuid", nullable: true),
                    CreatorPositionId = table.Column<Guid>(type: "uuid", nullable: true),
                    LastModificationTime = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    LastModifierId = table.Column<Guid>(type: "uuid", nullable: true),
                    LastModifierPositionId = table.Column<Guid>(type: "uuid", nullable: true),
                    IsDeleted = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                    DeletionTime = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    DeleterId = table.Column<Guid>(type: "uuid", nullable: true),
                    DeleterPositionId = table.Column<Guid>(type: "uuid", nullable: true),
                    Sha256Search = table.Column<string>(type: "character varying(64)", maxLength: 64, nullable: false),
                    StorageKeySearch = table.Column<string>(type: "character varying(512)", maxLength: 512, nullable: false),
                    MediaTypeSearch = table.Column<string>(type: "character varying(120)", maxLength: 120, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_StoredObjects", x => x.Id);
                    table.ForeignKey(
                        name: "FK_StoredObjects_StaffPositions_CreatorPositionId",
                        column: x => x.CreatorPositionId,
                        principalTable: "StaffPositions",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_StoredObjects_StaffPositions_DeleterPositionId",
                        column: x => x.DeleterPositionId,
                        principalTable: "StaffPositions",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_StoredObjects_StaffPositions_LastModifierPositionId",
                        column: x => x.LastModifierPositionId,
                        principalTable: "StaffPositions",
                        principalColumn: "Id");
                });

            migrationBuilder.CreateTable(
                name: "DocumentRevisions",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    DocumentId = table.Column<Guid>(type: "uuid", nullable: false),
                    StoredObjectId = table.Column<Guid>(type: "uuid", nullable: false),
                    RevisionNumber = table.Column<int>(type: "integer", nullable: false),
                    State = table.Column<string>(type: "character varying(40)", maxLength: 40, nullable: false),
                    Adapter = table.Column<string>(type: "character varying(120)", maxLength: 120, nullable: true),
                    AdapterVersion = table.Column<string>(type: "character varying(80)", maxLength: 80, nullable: true),
                    ManifestHash = table.Column<string>(type: "character varying(64)", maxLength: 64, nullable: true),
                    CreationTime = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    CreatorId = table.Column<Guid>(type: "uuid", nullable: true),
                    CreatorPositionId = table.Column<Guid>(type: "uuid", nullable: true),
                    LastModificationTime = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    LastModifierId = table.Column<Guid>(type: "uuid", nullable: true),
                    LastModifierPositionId = table.Column<Guid>(type: "uuid", nullable: true),
                    IsDeleted = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                    DeletionTime = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    DeleterId = table.Column<Guid>(type: "uuid", nullable: true),
                    DeleterPositionId = table.Column<Guid>(type: "uuid", nullable: true),
                    StateSearch = table.Column<string>(type: "character varying(40)", maxLength: 40, nullable: false),
                    AdapterSearch = table.Column<string>(type: "character varying(120)", maxLength: 120, nullable: false),
                    AdapterVersionSearch = table.Column<string>(type: "character varying(80)", maxLength: 80, nullable: false),
                    ManifestHashSearch = table.Column<string>(type: "character varying(64)", maxLength: 64, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_DocumentRevisions", x => x.Id);
                    table.ForeignKey(
                        name: "FK_DocumentRevisions_Documents_DocumentId",
                        column: x => x.DocumentId,
                        principalTable: "Documents",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_DocumentRevisions_StaffPositions_CreatorPositionId",
                        column: x => x.CreatorPositionId,
                        principalTable: "StaffPositions",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_DocumentRevisions_StaffPositions_DeleterPositionId",
                        column: x => x.DeleterPositionId,
                        principalTable: "StaffPositions",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_DocumentRevisions_StaffPositions_LastModifierPositionId",
                        column: x => x.LastModifierPositionId,
                        principalTable: "StaffPositions",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_DocumentRevisions_StoredObjects_StoredObjectId",
                        column: x => x.StoredObjectId,
                        principalTable: "StoredObjects",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "DocumentFragments",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    DocumentRevisionId = table.Column<Guid>(type: "uuid", nullable: false),
                    Sequence = table.Column<int>(type: "integer", nullable: false),
                    Kind = table.Column<string>(type: "character varying(40)", maxLength: 40, nullable: false),
                    AnchorJson = table.Column<string>(type: "character varying(2000)", maxLength: 2000, nullable: false),
                    Text = table.Column<string>(type: "character varying(8000)", maxLength: 8000, nullable: false),
                    ContentHash = table.Column<string>(type: "character varying(64)", maxLength: 64, nullable: false),
                    CreationTime = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    CreatorId = table.Column<Guid>(type: "uuid", nullable: true),
                    CreatorPositionId = table.Column<Guid>(type: "uuid", nullable: true),
                    LastModificationTime = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    LastModifierId = table.Column<Guid>(type: "uuid", nullable: true),
                    LastModifierPositionId = table.Column<Guid>(type: "uuid", nullable: true),
                    IsDeleted = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                    DeletionTime = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    DeleterId = table.Column<Guid>(type: "uuid", nullable: true),
                    DeleterPositionId = table.Column<Guid>(type: "uuid", nullable: true),
                    KindSearch = table.Column<string>(type: "character varying(40)", maxLength: 40, nullable: false),
                    AnchorJsonSearch = table.Column<string>(type: "character varying(2000)", maxLength: 2000, nullable: false),
                    TextSearch = table.Column<string>(type: "character varying(8000)", maxLength: 8000, nullable: false),
                    ContentHashSearch = table.Column<string>(type: "character varying(64)", maxLength: 64, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_DocumentFragments", x => x.Id);
                    table.ForeignKey(
                        name: "FK_DocumentFragments_DocumentRevisions_DocumentRevisionId",
                        column: x => x.DocumentRevisionId,
                        principalTable: "DocumentRevisions",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_DocumentFragments_StaffPositions_CreatorPositionId",
                        column: x => x.CreatorPositionId,
                        principalTable: "StaffPositions",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_DocumentFragments_StaffPositions_DeleterPositionId",
                        column: x => x.DeleterPositionId,
                        principalTable: "StaffPositions",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_DocumentFragments_StaffPositions_LastModifierPositionId",
                        column: x => x.LastModifierPositionId,
                        principalTable: "StaffPositions",
                        principalColumn: "Id");
                });

            migrationBuilder.CreateTable(
                name: "ProcessingJobs",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    DocumentRevisionId = table.Column<Guid>(type: "uuid", nullable: false),
                    Kind = table.Column<string>(type: "character varying(80)", maxLength: 80, nullable: false),
                    State = table.Column<string>(type: "character varying(40)", maxLength: 40, nullable: false),
                    Attempt = table.Column<int>(type: "integer", nullable: false),
                    IdempotencyKey = table.Column<string>(type: "character varying(160)", maxLength: 160, nullable: false),
                    LeaseUntil = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    LastErrorCode = table.Column<string>(type: "character varying(120)", maxLength: 120, nullable: true),
                    CreationTime = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    CreatorId = table.Column<Guid>(type: "uuid", nullable: true),
                    CreatorPositionId = table.Column<Guid>(type: "uuid", nullable: true),
                    LastModificationTime = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    LastModifierId = table.Column<Guid>(type: "uuid", nullable: true),
                    LastModifierPositionId = table.Column<Guid>(type: "uuid", nullable: true),
                    IsDeleted = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                    DeletionTime = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    DeleterId = table.Column<Guid>(type: "uuid", nullable: true),
                    DeleterPositionId = table.Column<Guid>(type: "uuid", nullable: true),
                    KindSearch = table.Column<string>(type: "character varying(80)", maxLength: 80, nullable: false),
                    StateSearch = table.Column<string>(type: "character varying(40)", maxLength: 40, nullable: false),
                    IdempotencyKeySearch = table.Column<string>(type: "character varying(160)", maxLength: 160, nullable: false),
                    LastErrorCodeSearch = table.Column<string>(type: "character varying(120)", maxLength: 120, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ProcessingJobs", x => x.Id);
                    table.ForeignKey(
                        name: "FK_ProcessingJobs_DocumentRevisions_DocumentRevisionId",
                        column: x => x.DocumentRevisionId,
                        principalTable: "DocumentRevisions",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_ProcessingJobs_StaffPositions_CreatorPositionId",
                        column: x => x.CreatorPositionId,
                        principalTable: "StaffPositions",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_ProcessingJobs_StaffPositions_DeleterPositionId",
                        column: x => x.DeleterPositionId,
                        principalTable: "StaffPositions",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_ProcessingJobs_StaffPositions_LastModifierPositionId",
                        column: x => x.LastModifierPositionId,
                        principalTable: "StaffPositions",
                        principalColumn: "Id");
                });

            migrationBuilder.CreateIndex(
                name: "IX___AppForgeSeedHistory_Model_SeedSet_Table",
                table: "__AppForgeSeedHistory",
                columns: new[] { "ModelId", "ModelVersion", "SeedSetName", "TableName" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_AccountRecoveryAttempts_CreatedAtUtc",
                table: "AccountRecoveryAttempts",
                column: "CreatedAtUtc");

            migrationBuilder.CreateIndex(
                name: "IX_AccountRecoveryAttempts_EmailHash",
                table: "AccountRecoveryAttempts",
                column: "EmailHash");

            migrationBuilder.CreateIndex(
                name: "IX_AccountRecoveryAttempts_IpHash",
                table: "AccountRecoveryAttempts",
                column: "IpHash");

            migrationBuilder.CreateIndex(
                name: "IX_AppUserRoles_AppUserId_RoleId",
                table: "AppUserRoles",
                columns: new[] { "AppUserId", "RoleId" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_AppUsers_Email",
                table: "AppUsers",
                column: "Email",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_AppUsers_UserName",
                table: "AppUsers",
                column: "UserName",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_AppUserSessions_AccessTokenHash",
                table: "AppUserSessions",
                column: "AccessTokenHash",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_AppUserSessions_AppUserId",
                table: "AppUserSessions",
                column: "AppUserId");

            migrationBuilder.CreateIndex(
                name: "IX_AppUserSessions_RefreshTokenHash",
                table: "AppUserSessions",
                column: "RefreshTokenHash",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_AuthLoginAttempts_CreatedAtUtc",
                table: "AuthLoginAttempts",
                column: "CreatedAtUtc");

            migrationBuilder.CreateIndex(
                name: "IX_AuthLoginAttempts_IpHash",
                table: "AuthLoginAttempts",
                column: "IpHash");

            migrationBuilder.CreateIndex(
                name: "IX_AuthLoginAttempts_LoginHash",
                table: "AuthLoginAttempts",
                column: "LoginHash");

            migrationBuilder.CreateIndex(
                name: "IX_DocumentFragments_AnchorJsonSearch",
                table: "DocumentFragments",
                column: "AnchorJsonSearch");

            migrationBuilder.CreateIndex(
                name: "IX_DocumentFragments_ContentHash",
                table: "DocumentFragments",
                column: "ContentHash");

            migrationBuilder.CreateIndex(
                name: "IX_DocumentFragments_ContentHashSearch",
                table: "DocumentFragments",
                column: "ContentHashSearch");

            migrationBuilder.CreateIndex(
                name: "IX_DocumentFragments_CreatorPositionId",
                table: "DocumentFragments",
                column: "CreatorPositionId");

            migrationBuilder.CreateIndex(
                name: "IX_DocumentFragments_DeleterPositionId",
                table: "DocumentFragments",
                column: "DeleterPositionId");

            migrationBuilder.CreateIndex(
                name: "IX_DocumentFragments_IsDeleted",
                table: "DocumentFragments",
                column: "IsDeleted");

            migrationBuilder.CreateIndex(
                name: "IX_DocumentFragments_KindSearch",
                table: "DocumentFragments",
                column: "KindSearch");

            migrationBuilder.CreateIndex(
                name: "IX_DocumentFragments_LastModifierPositionId",
                table: "DocumentFragments",
                column: "LastModifierPositionId");

            migrationBuilder.CreateIndex(
                name: "IX_DocumentFragments_TextSearch",
                table: "DocumentFragments",
                column: "TextSearch");

            migrationBuilder.CreateIndex(
                name: "UX_DocumentFragments_Revision_Sequence",
                table: "DocumentFragments",
                columns: new[] { "DocumentRevisionId", "Sequence" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_DocumentRevisions_AdapterSearch",
                table: "DocumentRevisions",
                column: "AdapterSearch");

            migrationBuilder.CreateIndex(
                name: "IX_DocumentRevisions_AdapterVersionSearch",
                table: "DocumentRevisions",
                column: "AdapterVersionSearch");

            migrationBuilder.CreateIndex(
                name: "IX_DocumentRevisions_CreatorPositionId",
                table: "DocumentRevisions",
                column: "CreatorPositionId");

            migrationBuilder.CreateIndex(
                name: "IX_DocumentRevisions_DeleterPositionId",
                table: "DocumentRevisions",
                column: "DeleterPositionId");

            migrationBuilder.CreateIndex(
                name: "IX_DocumentRevisions_IsDeleted",
                table: "DocumentRevisions",
                column: "IsDeleted");

            migrationBuilder.CreateIndex(
                name: "IX_DocumentRevisions_LastModifierPositionId",
                table: "DocumentRevisions",
                column: "LastModifierPositionId");

            migrationBuilder.CreateIndex(
                name: "IX_DocumentRevisions_ManifestHashSearch",
                table: "DocumentRevisions",
                column: "ManifestHashSearch");

            migrationBuilder.CreateIndex(
                name: "IX_DocumentRevisions_StateSearch",
                table: "DocumentRevisions",
                column: "StateSearch");

            migrationBuilder.CreateIndex(
                name: "IX_DocumentRevisions_StoredObjectId",
                table: "DocumentRevisions",
                column: "StoredObjectId");

            migrationBuilder.CreateIndex(
                name: "UX_DocumentRevisions_DocumentId_RevisionNumber",
                table: "DocumentRevisions",
                columns: new[] { "DocumentId", "RevisionNumber" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Documents_CreatorPositionId",
                table: "Documents",
                column: "CreatorPositionId");

            migrationBuilder.CreateIndex(
                name: "IX_Documents_DeleterPositionId",
                table: "Documents",
                column: "DeleterPositionId");

            migrationBuilder.CreateIndex(
                name: "IX_Documents_DisplayNameSearch",
                table: "Documents",
                column: "DisplayNameSearch");

            migrationBuilder.CreateIndex(
                name: "IX_Documents_IsDeleted",
                table: "Documents",
                column: "IsDeleted");

            migrationBuilder.CreateIndex(
                name: "IX_Documents_LastModifierPositionId",
                table: "Documents",
                column: "LastModifierPositionId");

            migrationBuilder.CreateIndex(
                name: "IX_Documents_MediaTypeSearch",
                table: "Documents",
                column: "MediaTypeSearch");

            migrationBuilder.CreateIndex(
                name: "IX_Documents_SourceKindSearch",
                table: "Documents",
                column: "SourceKindSearch");

            migrationBuilder.CreateIndex(
                name: "IX_Documents_StateSearch",
                table: "Documents",
                column: "StateSearch");

            migrationBuilder.CreateIndex(
                name: "IX_Documents_WorkspaceId_DisplayName",
                table: "Documents",
                columns: new[] { "WorkspaceId", "DisplayName" });

            migrationBuilder.CreateIndex(
                name: "IX_Documents_WorkspaceId_State",
                table: "Documents",
                columns: new[] { "WorkspaceId", "State" });

            migrationBuilder.CreateIndex(
                name: "IX_EmailConfirmationTokens_AppUserId",
                table: "EmailConfirmationTokens",
                column: "AppUserId");

            migrationBuilder.CreateIndex(
                name: "IX_EmailConfirmationTokens_TokenHash",
                table: "EmailConfirmationTokens",
                column: "TokenHash",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_IdentityAuditLogs_Action",
                table: "IdentityAuditLogs",
                column: "Action");

            migrationBuilder.CreateIndex(
                name: "IX_IdentityAuditLogs_ActorUserId",
                table: "IdentityAuditLogs",
                column: "ActorUserId");

            migrationBuilder.CreateIndex(
                name: "IX_IdentityAuditLogs_CreatedAtUtc",
                table: "IdentityAuditLogs",
                column: "CreatedAtUtc");

            migrationBuilder.CreateIndex(
                name: "IX_IdentityAuditLogs_TargetUserId",
                table: "IdentityAuditLogs",
                column: "TargetUserId");

            migrationBuilder.CreateIndex(
                name: "IX_PasswordResetTokens_AppUserId",
                table: "PasswordResetTokens",
                column: "AppUserId");

            migrationBuilder.CreateIndex(
                name: "IX_PasswordResetTokens_TokenHash",
                table: "PasswordResetTokens",
                column: "TokenHash",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Permissions_Code",
                table: "Permissions",
                column: "Code",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_ProcessingJobs_CreatorPositionId",
                table: "ProcessingJobs",
                column: "CreatorPositionId");

            migrationBuilder.CreateIndex(
                name: "IX_ProcessingJobs_DeleterPositionId",
                table: "ProcessingJobs",
                column: "DeleterPositionId");

            migrationBuilder.CreateIndex(
                name: "IX_ProcessingJobs_DocumentRevisionId",
                table: "ProcessingJobs",
                column: "DocumentRevisionId");

            migrationBuilder.CreateIndex(
                name: "IX_ProcessingJobs_IdempotencyKeySearch",
                table: "ProcessingJobs",
                column: "IdempotencyKeySearch");

            migrationBuilder.CreateIndex(
                name: "IX_ProcessingJobs_IsDeleted",
                table: "ProcessingJobs",
                column: "IsDeleted");

            migrationBuilder.CreateIndex(
                name: "IX_ProcessingJobs_KindSearch",
                table: "ProcessingJobs",
                column: "KindSearch");

            migrationBuilder.CreateIndex(
                name: "IX_ProcessingJobs_LastErrorCodeSearch",
                table: "ProcessingJobs",
                column: "LastErrorCodeSearch");

            migrationBuilder.CreateIndex(
                name: "IX_ProcessingJobs_LastModifierPositionId",
                table: "ProcessingJobs",
                column: "LastModifierPositionId");

            migrationBuilder.CreateIndex(
                name: "IX_ProcessingJobs_State_LeaseUntil",
                table: "ProcessingJobs",
                columns: new[] { "State", "LeaseUntil" });

            migrationBuilder.CreateIndex(
                name: "IX_ProcessingJobs_StateSearch",
                table: "ProcessingJobs",
                column: "StateSearch");

            migrationBuilder.CreateIndex(
                name: "UX_ProcessingJobs_IdempotencyKey",
                table: "ProcessingJobs",
                column: "IdempotencyKey",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_PublicRegistrationAttempts_CreatedAtUtc",
                table: "PublicRegistrationAttempts",
                column: "CreatedAtUtc");

            migrationBuilder.CreateIndex(
                name: "IX_PublicRegistrationAttempts_EmailHash",
                table: "PublicRegistrationAttempts",
                column: "EmailHash");

            migrationBuilder.CreateIndex(
                name: "IX_PublicRegistrationAttempts_IpHash",
                table: "PublicRegistrationAttempts",
                column: "IpHash");

            migrationBuilder.CreateIndex(
                name: "IX_RolePermissions_PermissionId",
                table: "RolePermissions",
                column: "PermissionId");

            migrationBuilder.CreateIndex(
                name: "IX_RolePermissions_RoleId_PermissionId",
                table: "RolePermissions",
                columns: new[] { "RoleId", "PermissionId" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Roles_Code",
                table: "Roles",
                column: "Code",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_StaffPositionAssignments_IsActive",
                table: "StaffPositionAssignments",
                column: "IsActive");

            migrationBuilder.CreateIndex(
                name: "IX_StaffPositionAssignments_StaffPositionId",
                table: "StaffPositionAssignments",
                column: "StaffPositionId");

            migrationBuilder.CreateIndex(
                name: "IX_StaffPositionAssignments_UserId",
                table: "StaffPositionAssignments",
                column: "UserId");

            migrationBuilder.CreateIndex(
                name: "IX_StaffPositionAssignments_UserId_StaffPositionId_IsActive",
                table: "StaffPositionAssignments",
                columns: new[] { "UserId", "StaffPositionId", "IsActive" });

            migrationBuilder.CreateIndex(
                name: "IX_StaffPositionRoles_RoleId",
                table: "StaffPositionRoles",
                column: "RoleId");

            migrationBuilder.CreateIndex(
                name: "IX_StaffPositionRoles_StaffPositionId_RoleId",
                table: "StaffPositionRoles",
                columns: new[] { "StaffPositionId", "RoleId" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_StaffPositions_Code",
                table: "StaffPositions",
                column: "Code",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_StaffPositions_IsActive",
                table: "StaffPositions",
                column: "IsActive");

            migrationBuilder.CreateIndex(
                name: "IX_StaffPositions_ParentPositionId",
                table: "StaffPositions",
                column: "ParentPositionId");

            migrationBuilder.CreateIndex(
                name: "IX_StoredObjects_CreatorPositionId",
                table: "StoredObjects",
                column: "CreatorPositionId");

            migrationBuilder.CreateIndex(
                name: "IX_StoredObjects_DeleterPositionId",
                table: "StoredObjects",
                column: "DeleterPositionId");

            migrationBuilder.CreateIndex(
                name: "IX_StoredObjects_IsDeleted",
                table: "StoredObjects",
                column: "IsDeleted");

            migrationBuilder.CreateIndex(
                name: "IX_StoredObjects_LastModifierPositionId",
                table: "StoredObjects",
                column: "LastModifierPositionId");

            migrationBuilder.CreateIndex(
                name: "IX_StoredObjects_MediaTypeSearch",
                table: "StoredObjects",
                column: "MediaTypeSearch");

            migrationBuilder.CreateIndex(
                name: "IX_StoredObjects_Sha256Search",
                table: "StoredObjects",
                column: "Sha256Search");

            migrationBuilder.CreateIndex(
                name: "IX_StoredObjects_StorageKeySearch",
                table: "StoredObjects",
                column: "StorageKeySearch");

            migrationBuilder.CreateIndex(
                name: "UX_StoredObjects_Sha256",
                table: "StoredObjects",
                column: "Sha256",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_UserInvitations_Email",
                table: "UserInvitations",
                column: "Email");

            migrationBuilder.CreateIndex(
                name: "IX_UserInvitations_TokenHash",
                table: "UserInvitations",
                column: "TokenHash",
                unique: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "__AppForgeSeedHistory");

            migrationBuilder.DropTable(
                name: "AccountRecoveryAttempts");

            migrationBuilder.DropTable(
                name: "AppUserRoles");

            migrationBuilder.DropTable(
                name: "AppUsers");

            migrationBuilder.DropTable(
                name: "AppUserSessions");

            migrationBuilder.DropTable(
                name: "AuthLoginAttempts");

            migrationBuilder.DropTable(
                name: "DocumentFragments");

            migrationBuilder.DropTable(
                name: "EmailConfirmationTokens");

            migrationBuilder.DropTable(
                name: "IdentityAuditLogs");

            migrationBuilder.DropTable(
                name: "PasswordResetTokens");

            migrationBuilder.DropTable(
                name: "ProcessingJobs");

            migrationBuilder.DropTable(
                name: "PublicRegistrationAttempts");

            migrationBuilder.DropTable(
                name: "RolePermissions");

            migrationBuilder.DropTable(
                name: "StaffPositionAssignments");

            migrationBuilder.DropTable(
                name: "StaffPositionRoles");

            migrationBuilder.DropTable(
                name: "UserInvitations");

            migrationBuilder.DropTable(
                name: "DocumentRevisions");

            migrationBuilder.DropTable(
                name: "Permissions");

            migrationBuilder.DropTable(
                name: "Roles");

            migrationBuilder.DropTable(
                name: "Documents");

            migrationBuilder.DropTable(
                name: "StoredObjects");

            migrationBuilder.DropTable(
                name: "StaffPositions");
        }
    }
}
