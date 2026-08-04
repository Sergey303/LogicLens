// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { staffPositionControllerGetQuery } from "./staffPositionControllerGetQuery.query.generated";
import type { StaffPositionDto } from "../staffpositions/types/StaffPositionDto.generated";

export function useStaffPositionControllerGetQuery(
  input: GeneratedEndpointInput<{ id: string; }>,
  options?: GeneratedQueryOptions<StaffPositionDto>,
  _config?: unknown,
) {
  return useGeneratedQuery(staffPositionControllerGetQuery, input, options);
}
