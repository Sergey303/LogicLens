// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositionroles/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedMutation } from "../runtime/reactQueryRuntime";
import type { GeneratedMutationOptions } from "../runtime/reactQueryTypes";
import { staffPositionRoleControllerCreateMutation } from "./staffPositionRoleControllerCreateMutation.mutation.generated";
import type { CreateStaffPositionRoleRequest } from "../staffpositionroles/types/CreateStaffPositionRoleRequest.generated";
import type { StaffPositionRoleDto } from "../staffpositionroles/types/StaffPositionRoleDto.generated";

export function useStaffPositionRoleControllerCreateMutation(
  options?: GeneratedMutationOptions<CreateStaffPositionRoleRequest, StaffPositionRoleDto>,
  _config?: unknown,
) {
  return useGeneratedMutation(staffPositionRoleControllerCreateMutation, options);
}
