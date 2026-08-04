// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositionroles/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedMutation } from "../runtime/reactQueryRuntime";
import type { GeneratedMutationOptions } from "../runtime/reactQueryTypes";
import { staffPositionRoleControllerUpdateMutation } from "./staffPositionRoleControllerUpdateMutation.mutation.generated";
import type { StaffPositionRoleDto } from "../staffpositionroles/types/StaffPositionRoleDto.generated";
import type { UpdateStaffPositionRoleRequest } from "../staffpositionroles/types/UpdateStaffPositionRoleRequest.generated";

export function useStaffPositionRoleControllerUpdateMutation(
  options?: GeneratedMutationOptions<{ id: string; body: UpdateStaffPositionRoleRequest; }, StaffPositionRoleDto>,
  _config?: unknown,
) {
  return useGeneratedMutation(staffPositionRoleControllerUpdateMutation, options);
}
