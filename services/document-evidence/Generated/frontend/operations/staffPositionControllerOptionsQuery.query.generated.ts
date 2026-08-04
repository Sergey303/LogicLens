import { defineQueryBinding } from "../runtime/queryRuntime";
import { staffPositionControllerOptionsTransportMetadata } from "./staffPositionControllerOptionsTransport.transport.generated";
import type { StaffPositionOptionDto } from "../staffpositions/types/StaffPositionOptionDto.generated";
export const staffPositionControllerOptionsQuery = defineQueryBinding<{ field: string; }, StaffPositionOptionDto[]>({
  endpointKey: "get:/api/staffpositions/options/{field}",
  transportMetadata: staffPositionControllerOptionsTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StaffPosition.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
