import { defineQueryBinding } from "../runtime/queryRuntime";
import { staffPositionControllerGetTransportMetadata } from "./staffPositionControllerGetTransport.transport.generated";
import type { StaffPositionDto } from "../staffpositions/types/StaffPositionDto.generated";
export const staffPositionControllerGetQuery = defineQueryBinding<{ id: string; }, StaffPositionDto>({
  endpointKey: "get:/api/staffpositions/{id}",
  transportMetadata: staffPositionControllerGetTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StaffPosition.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["staff.position.not_found"],
});
