// ------------------------------------------------------------------------------
// GENERATED FILE - source: roles/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedMutation } from "../runtime/reactQueryRuntime";
import type { GeneratedMutationOptions } from "../runtime/reactQueryTypes";
import { roleControllerCreateMutation } from "./roleControllerCreateMutation.mutation.generated";
import type { CreateRoleRequest } from "../roles/types/CreateRoleRequest.generated";
import type { RoleDto } from "../roles/types/RoleDto.generated";

export function useRoleControllerCreateMutation(
  options?: GeneratedMutationOptions<CreateRoleRequest, RoleDto>,
  _config?: unknown,
) {
  return useGeneratedMutation(roleControllerCreateMutation, options);
}
