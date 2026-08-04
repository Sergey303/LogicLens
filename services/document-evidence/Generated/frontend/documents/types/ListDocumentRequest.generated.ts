// ------------------------------------------------------------------------------
// GENERATED FILE - source: documents/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import type { ListDocumentFilter } from "./ListDocumentFilter.generated";
import type { ListDocumentSort } from "./ListDocumentSort.generated";

export interface ListDocumentRequest {
  "filters": ListDocumentFilter[];
  "page": number;
  "pageSize": number;
  "sort": ListDocumentSort[];
}
export const ListDocumentRequestTypeKey = "LogicLens.DocumentEvidence.Generated.Api.Contracts.ListDocumentRequest" as const;

