# Document Evidence Operational Model
AppForge input for the replaceable operational/admin contour. Trusted storage, parsing, provenance,
capsules, and Prolog decisions remain handwritten.

## Entity Document
Table: Documents
Namespace: LogicLens.DocumentEvidence.Generated
| Property | Type | Required | Key | MaxLength |
|---|---|---:|---:|---:|
| Id | Guid | true | true | |
| WorkspaceId | Guid | true | false | |
| DisplayName | string | true | false | 260 |
| MediaType | string | true | false | 120 |
| SourceKind | string | true | false | 40 |
| State | string | true | false | 40 |
| CurrentRevisionNumber | int | true | false | |
| IsRevoked | bool | true | false | |

| Name | Properties | Unique |
|---|---|---:|
| IX_Documents_WorkspaceId_DisplayName | WorkspaceId, DisplayName | false |
| IX_Documents_WorkspaceId_State | WorkspaceId, State | false |

## Entity StoredObject
Table: StoredObjects
Namespace: LogicLens.DocumentEvidence.Generated
| Property | Type | Required | Key | MaxLength |
|---|---|---:|---:|---:|
| Id | Guid | true | true | |
| Sha256 | string | true | false | 64 |
| StorageKey | string | true | false | 512 |
| SizeBytes | long | true | false | |
| MediaType | string | true | false | 120 |

| Name | Properties | Unique |
|---|---|---:|
| UX_StoredObjects_Sha256 | Sha256 | true |

## Entity DocumentRevision
Table: DocumentRevisions
Namespace: LogicLens.DocumentEvidence.Generated
| Property | Type | Required | Key | MaxLength |
|---|---|---:|---:|---:|
| Id | Guid | true | true | |
| DocumentId | Guid | true | false | |
| StoredObjectId | Guid | true | false | |
| RevisionNumber | int | true | false | |
| State | string | true | false | 40 |
| Adapter | string | false | false | 120 |
| AdapterVersion | string | false | false | 80 |
| ManifestHash | string | false | false | 64 |
| ManifestJson | string | false | false | 8000 |

| Navigation | Target | ForeignKey | Required | Inverse |
|---|---|---|---:|---|
| Document | Document | DocumentId | true | Revisions |
| StoredObject | StoredObject | StoredObjectId | true | Revisions |

| Name | Properties | Unique |
|---|---|---:|
| UX_DocumentRevisions_DocumentId_RevisionNumber | DocumentId, RevisionNumber | true |

## Entity ProcessingJob
Table: ProcessingJobs
Namespace: LogicLens.DocumentEvidence.Generated
| Property | Type | Required | Key | MaxLength |
|---|---|---:|---:|---:|
| Id | Guid | true | true | |
| DocumentRevisionId | Guid | true | false | |
| Kind | string | true | false | 80 |
| State | string | true | false | 40 |
| Attempt | int | true | false | |
| MaxAttempts | int | true | false | |
| IdempotencyKey | string | true | false | 160 |
| AvailableAt | DateTime | true | false | |
| LeaseToken | Guid | false | false | |
| LeaseUntil | DateTime | false | false | |
| LastErrorCode | string | false | false | 120 |
| LastError | string | false | false | 2000 |

| Navigation | Target | ForeignKey | Required | Inverse |
|---|---|---|---:|---|
| DocumentRevision | DocumentRevision | DocumentRevisionId | true | ProcessingJobs |

| Name | Properties | Unique |
|---|---|---:|
| UX_ProcessingJobs_IdempotencyKey | IdempotencyKey | true |
| IX_ProcessingJobs_State_LeaseUntil | State, LeaseUntil | false |

## Entity DocumentFragment
Table: DocumentFragments
Namespace: LogicLens.DocumentEvidence.Generated
| Property | Type | Required | Key | MaxLength |
|---|---|---:|---:|---:|
| Id | Guid | true | true | |
| DocumentRevisionId | Guid | true | false | |
| Sequence | int | true | false | |
| Kind | string | true | false | 40 |
| AnchorJson | string | true | false | 2000 |
| Text | string | true | false | 8000 |
| ContentHash | string | true | false | 64 |

| Navigation | Target | ForeignKey | Required | Inverse |
|---|---|---|---:|---|
| DocumentRevision | DocumentRevision | DocumentRevisionId | true | Fragments |

| Name | Properties | Unique |
|---|---|---:|
| UX_DocumentFragments_Revision_Sequence | DocumentRevisionId, Sequence | true |
| IX_DocumentFragments_ContentHash | ContentHash | false |

## Security: Document
| Operation | Roles | Scope | OwnerField |
|---|---|---|---|
| Read | DocumentEvidenceAdmin | All | |
| Create | DocumentEvidenceAdmin | All | |
| Update | DocumentEvidenceAdmin | All | |
| Delete | DocumentEvidenceAdmin | All | |
## Security: StoredObject
| Operation | Roles | Scope | OwnerField |
|---|---|---|---|
| Read | DocumentEvidenceAdmin | All | |
| Create | DocumentEvidenceAdmin | All | |
| Update | DocumentEvidenceAdmin | All | |
| Delete | DocumentEvidenceAdmin | All | |
## Security: DocumentRevision
| Operation | Roles | Scope | OwnerField |
|---|---|---|---|
| Read | DocumentEvidenceAdmin | All | |
| Create | DocumentEvidenceAdmin | All | |
| Update | DocumentEvidenceAdmin | All | |
| Delete | DocumentEvidenceAdmin | All | |
## Security: ProcessingJob
| Operation | Roles | Scope | OwnerField |
|---|---|---|---|
| Read | DocumentEvidenceAdmin | All | |
| Create | DocumentEvidenceAdmin | All | |
| Update | DocumentEvidenceAdmin | All | |
| Delete | DocumentEvidenceAdmin | All | |
## Security: DocumentFragment
| Operation | Roles | Scope | OwnerField |
|---|---|---|---|
| Read | DocumentEvidenceAdmin | All | |
| Create | DocumentEvidenceAdmin | All | |
| Update | DocumentEvidenceAdmin | All | |
| Delete | DocumentEvidenceAdmin | All | |
