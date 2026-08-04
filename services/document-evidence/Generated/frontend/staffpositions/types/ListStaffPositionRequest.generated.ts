// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositions/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import type { ListStaffPositionFilter } from "./ListStaffPositionFilter.generated";
import type { ListStaffPositionSort } from "./ListStaffPositionSort.generated";

export interface ListStaffPositionRequest {
  "filters": ListStaffPositionFilter[];
  "page": number;
  "pageSize": number;
  "sort": ListStaffPositionSort[];
}
export const ListStaffPositionRequestTypeKey = "LogicLens.DocumentEvidence.Generated.Api.Contracts.ListStaffPositionRequest" as const;

