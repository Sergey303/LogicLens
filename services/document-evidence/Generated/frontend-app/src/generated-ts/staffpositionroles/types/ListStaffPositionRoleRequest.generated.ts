// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositionroles/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import type { ListStaffPositionRoleFilter } from "./ListStaffPositionRoleFilter.generated";
import type { ListStaffPositionRoleSort } from "./ListStaffPositionRoleSort.generated";

export interface ListStaffPositionRoleRequest {
  "filters": ListStaffPositionRoleFilter[];
  "page": number;
  "pageSize": number;
  "sort": ListStaffPositionRoleSort[];
}
export const ListStaffPositionRoleRequestTypeKey = "LogicLens.DocumentEvidence.Generated.Api.Contracts.ListStaffPositionRoleRequest" as const;

