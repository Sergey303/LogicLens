// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositionassignments/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import type { ListStaffPositionAssignmentFilter } from "./ListStaffPositionAssignmentFilter.generated";
import type { ListStaffPositionAssignmentSort } from "./ListStaffPositionAssignmentSort.generated";

export interface ListStaffPositionAssignmentRequest {
  "filters": ListStaffPositionAssignmentFilter[];
  "page": number;
  "pageSize": number;
  "sort": ListStaffPositionAssignmentSort[];
}
export const ListStaffPositionAssignmentRequestTypeKey = "LogicLens.DocumentEvidence.Generated.Api.Contracts.ListStaffPositionAssignmentRequest" as const;

