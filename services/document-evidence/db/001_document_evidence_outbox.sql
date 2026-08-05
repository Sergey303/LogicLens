CREATE TABLE IF NOT EXISTS "DocumentEvidenceOutbox" (
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
    "LastError" varchar(2000) NULL,
    CONSTRAINT "CK_DocumentEvidenceOutbox_Attempt" CHECK ("Attempt" >= 0),
    CONSTRAINT "CK_DocumentEvidenceOutbox_Lease" CHECK (
        ("LeaseToken" IS NULL AND "LeaseUntil" IS NULL)
        OR ("LeaseToken" IS NOT NULL AND "LeaseUntil" IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS "IX_DocumentEvidenceOutbox_Dispatch"
    ON "DocumentEvidenceOutbox" ("DispatchedAt", "AvailableAt", "LeaseUntil");
