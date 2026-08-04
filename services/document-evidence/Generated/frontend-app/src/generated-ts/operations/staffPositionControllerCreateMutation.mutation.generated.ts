import { defineMutationBinding } from "../runtime/mutationRuntime";
import { staffPositionControllerCreateTransportMetadata } from "./staffPositionControllerCreateTransport.transport.generated";
import type { CreateStaffPositionRequest } from "../staffpositions/types/CreateStaffPositionRequest.generated";import type { StaffPositionDto } from "../staffpositions/types/StaffPositionDto.generated";
export const staffPositionControllerCreateMutation = defineMutationBinding<CreateStaffPositionRequest, StaffPositionDto>({
  endpointKey: "post:/api/staffpositions",
  transportMetadata: staffPositionControllerCreateTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/staffpositions", "get:/api/staffpositions/lookup", "get:/api/staffpositions/options/{field}", "get:/api/staffpositions/suggest/{field}", "get:/api/staffpositions/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StaffPosition.Create"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["staff.position.validation_failed"],
});
