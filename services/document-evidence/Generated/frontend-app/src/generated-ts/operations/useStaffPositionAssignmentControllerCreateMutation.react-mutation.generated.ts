// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositionassignments/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedMutation } from "../runtime/reactQueryRuntime";
import type { GeneratedMutationOptions } from "../runtime/reactQueryTypes";
import { staffPositionAssignmentControllerCreateMutation } from "./staffPositionAssignmentControllerCreateMutation.mutation.generated";
import type { CreateStaffPositionAssignmentRequest } from "../staffpositionassignments/types/CreateStaffPositionAssignmentRequest.generated";
import type { StaffPositionAssignmentDto } from "../staffpositionassignments/types/StaffPositionAssignmentDto.generated";

export function useStaffPositionAssignmentControllerCreateMutation(
  options?: GeneratedMutationOptions<CreateStaffPositionAssignmentRequest, StaffPositionAssignmentDto>,
  _config?: unknown,
) {
  return useGeneratedMutation(staffPositionAssignmentControllerCreateMutation, options);
}
