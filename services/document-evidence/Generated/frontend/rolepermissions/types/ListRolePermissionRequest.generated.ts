// ------------------------------------------------------------------------------
// GENERATED FILE - source: rolepermissions/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import type { ListRolePermissionFilter } from "./ListRolePermissionFilter.generated";
import type { ListRolePermissionSort } from "./ListRolePermissionSort.generated";

export interface ListRolePermissionRequest {
  "filters": ListRolePermissionFilter[];
  "page": number;
  "pageSize": number;
  "sort": ListRolePermissionSort[];
}
export const ListRolePermissionRequestTypeKey = "LogicLens.DocumentEvidence.Generated.Api.Contracts.ListRolePermissionRequest" as const;

