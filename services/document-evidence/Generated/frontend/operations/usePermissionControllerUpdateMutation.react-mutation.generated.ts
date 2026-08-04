// ------------------------------------------------------------------------------
// GENERATED FILE - source: permissions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedMutation } from "../runtime/reactQueryRuntime";
import type { GeneratedMutationOptions } from "../runtime/reactQueryTypes";
import { permissionControllerUpdateMutation } from "./permissionControllerUpdateMutation.mutation.generated";
import type { PermissionDto } from "../permissions/types/PermissionDto.generated";
import type { UpdatePermissionRequest } from "../permissions/types/UpdatePermissionRequest.generated";

export function usePermissionControllerUpdateMutation(
  options?: GeneratedMutationOptions<{ id: string; body: UpdatePermissionRequest; }, PermissionDto>,
  _config?: unknown,
) {
  return useGeneratedMutation(permissionControllerUpdateMutation, options);
}
