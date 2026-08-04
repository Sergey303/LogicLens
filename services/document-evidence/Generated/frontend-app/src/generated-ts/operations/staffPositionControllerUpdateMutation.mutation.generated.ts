import { defineMutationBinding } from "../runtime/mutationRuntime";
import { staffPositionControllerUpdateTransportMetadata } from "./staffPositionControllerUpdateTransport.transport.generated";
import type { StaffPositionDto } from "../staffpositions/types/StaffPositionDto.generated";import type { UpdateStaffPositionRequest } from "../staffpositions/types/UpdateStaffPositionRequest.generated";
export const staffPositionControllerUpdateMutation = defineMutationBinding<{ id: string; body: UpdateStaffPositionRequest; }, StaffPositionDto>({
  endpointKey: "put:/api/staffpositions/{id}",
  transportMetadata: staffPositionControllerUpdateTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/staffpositions", "get:/api/staffpositions/lookup", "get:/api/staffpositions/options/{field}", "get:/api/staffpositions/suggest/{field}", "get:/api/staffpositions/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StaffPosition.Update"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["staff.position.not_found", "staff.position.validation_failed"],
});
