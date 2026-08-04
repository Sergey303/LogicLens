// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositionassignments/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedMutation } from "../runtime/reactQueryRuntime";
import type { GeneratedMutationOptions } from "../runtime/reactQueryTypes";
import { staffPositionAssignmentControllerUpdateMutation } from "./staffPositionAssignmentControllerUpdateMutation.mutation.generated";
import type { StaffPositionAssignmentDto } from "../staffpositionassignments/types/StaffPositionAssignmentDto.generated";
import type { UpdateStaffPositionAssignmentRequest } from "../staffpositionassignments/types/UpdateStaffPositionAssignmentRequest.generated";

export function useStaffPositionAssignmentControllerUpdateMutation(
  options?: GeneratedMutationOptions<{ id: string; body: UpdateStaffPositionAssignmentRequest; }, StaffPositionAssignmentDto>,
  _config?: unknown,
) {
  return useGeneratedMutation(staffPositionAssignmentControllerUpdateMutation, options);
}
