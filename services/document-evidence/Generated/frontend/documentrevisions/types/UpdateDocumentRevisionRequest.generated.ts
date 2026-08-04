// ------------------------------------------------------------------------------
// GENERATED FILE - source: documentrevisions/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

export interface UpdateDocumentRevisionRequest {
  "adapter"?: string | null;
  "adapterVersion"?: string | null;
  "documentId": string;
  "manifestHash"?: string | null;
  "revisionNumber": number;
  "state": string;
  "storedObjectId": string;
}
export const UpdateDocumentRevisionRequestTypeKey = "LogicLens.DocumentEvidence.Generated.Api.Contracts.UpdateDocumentRevisionRequest" as const;

