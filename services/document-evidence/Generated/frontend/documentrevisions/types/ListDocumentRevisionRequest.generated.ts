// ------------------------------------------------------------------------------
// GENERATED FILE - source: documentrevisions/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import type { ListDocumentRevisionFilter } from "./ListDocumentRevisionFilter.generated";
import type { ListDocumentRevisionSort } from "./ListDocumentRevisionSort.generated";

export interface ListDocumentRevisionRequest {
  "filters": ListDocumentRevisionFilter[];
  "page": number;
  "pageSize": number;
  "sort": ListDocumentRevisionSort[];
}
export const ListDocumentRevisionRequestTypeKey = "LogicLens.DocumentEvidence.Generated.Api.Contracts.ListDocumentRevisionRequest" as const;

