// ------------------------------------------------------------------------------
// GENERATED FILE - source: roles/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedMutation } from "../runtime/reactQueryRuntime";
import type { GeneratedMutationOptions } from "../runtime/reactQueryTypes";
import { roleControllerUpdateMutation } from "./roleControllerUpdateMutation.mutation.generated";
import type { RoleDto } from "../roles/types/RoleDto.generated";
import type { UpdateRoleRequest } from "../roles/types/UpdateRoleRequest.generated";

export function useRoleControllerUpdateMutation(
  options?: GeneratedMutationOptions<{ id: string; body: UpdateRoleRequest; }, RoleDto>,
  _config?: unknown,
) {
  return useGeneratedMutation(roleControllerUpdateMutation, options);
}
