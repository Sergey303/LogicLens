// ------------------------------------------------------------------------------
// GENERATED FILE - source: documentrevisions/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

export interface CreateDocumentRevisionRequest {
  "adapter"?: string | null;
  "adapterVersion"?: string | null;
  "documentId": string;
  "manifestHash"?: string | null;
  "revisionNumber": number;
  "state": string;
  "storedObjectId": string;
}
export const CreateDocumentRevisionRequestTypeKey = "LogicLens.DocumentEvidence.Generated.Api.Contracts.CreateDocumentRevisionRequest" as const;

