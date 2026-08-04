// ------------------------------------------------------------------------------
// GENERATED FILE - source: permissions/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import type { PermissionDto } from "./PermissionDto.generated";

export interface ListPermissionResult {
  "items": PermissionDto[];
  "page": number;
  "pageSize": number;
  "totalCount": number;
}
export const ListPermissionResultTypeKey = "LogicLens.DocumentEvidence.Generated.Api.Contracts.ListPermissionResult" as const;

