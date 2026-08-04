// ------------------------------------------------------------------------------
// GENERATED FILE - source: roles/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import type { ListRoleFilter } from "./ListRoleFilter.generated";
import type { ListRoleSort } from "./ListRoleSort.generated";

export interface ListRoleRequest {
  "filters": ListRoleFilter[];
  "page": number;
  "pageSize": number;
  "sort": ListRoleSort[];
}
export const ListRoleRequestTypeKey = "LogicLens.DocumentEvidence.Generated.Api.Contracts.ListRoleRequest" as const;

