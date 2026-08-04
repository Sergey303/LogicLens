DROP TABLE IF EXISTS "DocumentEvidenceOutbox";
DROP TABLE IF EXISTS "ProcessingJobs";
DROP TABLE IF EXISTS "DocumentRevisions";
DROP TABLE IF EXISTS "StoredObjects";
DROP TABLE IF EXISTS "Documents";

CREATE TABLE "Documents" (
    "Id" uuid PRIMARY KEY,
    "WorkspaceId" uuid NOT NULL,
    "DisplayName" varchar(260) NOT NULL,
    "MediaType" varchar(120) NOT NULL,
    "SourceKind" varchar(40) NOT NULL,
    "State" varchar(40) NOT NULL,
    "CurrentRevisionNumber" integer NOT NULL,
    "IsRevoked" boolean NOT NULL
);

CREATE TABLE "StoredObjects" (
    "Id" uuid PRIMARY KEY,
    "Sha256" varchar(64) NOT NULL UNIQUE,
    "StorageKey" varchar(512) NOT NULL,
    "SizeBytes" bigint NOT NULL,
    "MediaType" varchar(120) NOT NULL
);

CREATE TABLE "DocumentRevisions" (
    "Id" uuid PRIMARY KEY,
    "DocumentId" uuid NOT NULL REFERENCES "Documents" ("Id"),
    "StoredObjectId" uuid NOT NULL REFERENCES "StoredObjects" ("Id"),
    "RevisionNumber" integer NOT NULL,
    "State" varchar(40) NOT NULL,
    "Adapter" varchar(120) NULL,
    "AdapterVersion" varchar(80) NULL,
    "ManifestHash" varchar(64) NULL,
    "ManifestJson" varchar(8000) NULL,
    UNIQUE ("DocumentId", "RevisionNumber")
);

CREATE TABLE "ProcessingJobs" (
    "Id" uuid PRIMARY KEY,
    "DocumentRevisionId" uuid NOT NULL REFERENCES "DocumentRevisions" ("Id"),
    "Kind" varchar(80) NOT NULL,
    "State" varchar(40) NOT NULL,
    "Attempt" integer NOT NULL,
    "MaxAttempts" integer NOT NULL,
    "IdempotencyKey" varchar(160) NOT NULL UNIQUE,
    "AvailableAt" timestamptz NOT NULL,
    "LeaseToken" uuid NULL,
    "LeaseUntil" timestamptz NULL,
    "LastErrorCode" varchar(120) NULL,
    "LastError" varchar(2000) NULL
);

CREATE TABLE "DocumentEvidenceOutbox" (
    "Id" uuid PRIMARY KEY,
    "EventKey" varchar(200) NOT NULL UNIQUE,
    "EventType" varchar(120) NOT NULL,
    "AggregateId" uuid NOT NULL,
    "PayloadJson" jsonb NOT NULL,
    "CreatedAt" timestamptz NOT NULL,
    "AvailableAt" timestamptz NOT NULL,
    "Attempt" integer NOT NULL DEFAULT 0,
    "LeaseToken" uuid NULL,
    "LeaseUntil" timestamptz NULL,
    "DispatchedAt" timestamptz NULL,
    "LastError" varchar(2000) NULL
);
