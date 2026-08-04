// ------------------------------------------------------------------------------
// GENERATED FILE - source: permissions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedMutation } from "../runtime/reactQueryRuntime";
import type { GeneratedMutationOptions } from "../runtime/reactQueryTypes";
import { permissionControllerCreateMutation } from "./permissionControllerCreateMutation.mutation.generated";
import type { CreatePermissionRequest } from "../permissions/types/CreatePermissionRequest.generated";
import type { PermissionDto } from "../permissions/types/PermissionDto.generated";

export function usePermissionControllerCreateMutation(
  options?: GeneratedMutationOptions<CreatePermissionRequest, PermissionDto>,
  _config?: unknown,
) {
  return useGeneratedMutation(permissionControllerCreateMutation, options);
}
