// ------------------------------------------------------------------------------
// GENERATED FILE - source: storedobjects/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import type { ListStoredObjectFilter } from "./ListStoredObjectFilter.generated";
import type { ListStoredObjectSort } from "./ListStoredObjectSort.generated";

export interface ListStoredObjectRequest {
  "filters": ListStoredObjectFilter[];
  "page": number;
  "pageSize": number;
  "sort": ListStoredObjectSort[];
}
export const ListStoredObjectRequestTypeKey = "LogicLens.DocumentEvidence.Generated.Api.Contracts.ListStoredObjectRequest" as const;

