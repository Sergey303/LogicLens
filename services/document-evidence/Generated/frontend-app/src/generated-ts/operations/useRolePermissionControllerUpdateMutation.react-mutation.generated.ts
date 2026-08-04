// ------------------------------------------------------------------------------
// GENERATED FILE - source: rolepermissions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedMutation } from "../runtime/reactQueryRuntime";
import type { GeneratedMutationOptions } from "../runtime/reactQueryTypes";
import { rolePermissionControllerUpdateMutation } from "./rolePermissionControllerUpdateMutation.mutation.generated";
import type { RolePermissionDto } from "../rolepermissions/types/RolePermissionDto.generated";
import type { UpdateRolePermissionRequest } from "../rolepermissions/types/UpdateRolePermissionRequest.generated";

export function useRolePermissionControllerUpdateMutation(
  options?: GeneratedMutationOptions<{ id: string; body: UpdateRolePermissionRequest; }, RolePermissionDto>,
  _config?: unknown,
) {
  return useGeneratedMutation(rolePermissionControllerUpdateMutation, options);
}
