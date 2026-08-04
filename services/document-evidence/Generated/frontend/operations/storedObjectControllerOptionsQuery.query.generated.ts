import { defineQueryBinding } from "../runtime/queryRuntime";
import { storedObjectControllerOptionsTransportMetadata } from "./storedObjectControllerOptionsTransport.transport.generated";
import type { StoredObjectOptionDto } from "../storedobjects/types/StoredObjectOptionDto.generated";
export const storedObjectControllerOptionsQuery = defineQueryBinding<{ field: string; }, StoredObjectOptionDto[]>({
  endpointKey: "get:/api/storedobjects/options/{field}",
  transportMetadata: storedObjectControllerOptionsTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StoredObject.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
