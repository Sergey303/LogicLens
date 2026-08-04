// ------------------------------------------------------------------------------
// GENERATED FILE - source: documentfragments/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import type { ListDocumentFragmentFilter } from "./ListDocumentFragmentFilter.generated";
import type { ListDocumentFragmentSort } from "./ListDocumentFragmentSort.generated";

export interface ListDocumentFragmentRequest {
  "filters": ListDocumentFragmentFilter[];
  "page": number;
  "pageSize": number;
  "sort": ListDocumentFragmentSort[];
}
export const ListDocumentFragmentRequestTypeKey = "LogicLens.DocumentEvidence.Generated.Api.Contracts.ListDocumentFragmentRequest" as const;

