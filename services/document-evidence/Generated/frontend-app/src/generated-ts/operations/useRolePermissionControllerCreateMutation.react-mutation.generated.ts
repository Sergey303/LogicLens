// ------------------------------------------------------------------------------
// GENERATED FILE - source: rolepermissions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedMutation } from "../runtime/reactQueryRuntime";
import type { GeneratedMutationOptions } from "../runtime/reactQueryTypes";
import { rolePermissionControllerCreateMutation } from "./rolePermissionControllerCreateMutation.mutation.generated";
import type { CreateRolePermissionRequest } from "../rolepermissions/types/CreateRolePermissionRequest.generated";
import type { RolePermissionDto } from "../rolepermissions/types/RolePermissionDto.generated";

export function useRolePermissionControllerCreateMutation(
  options?: GeneratedMutationOptions<CreateRolePermissionRequest, RolePermissionDto>,
  _config?: unknown,
) {
  return useGeneratedMutation(rolePermissionControllerCreateMutation, options);
}
