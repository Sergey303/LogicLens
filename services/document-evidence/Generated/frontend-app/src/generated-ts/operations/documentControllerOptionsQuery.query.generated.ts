import { defineQueryBinding } from "../runtime/queryRuntime";
import { documentControllerOptionsTransportMetadata } from "./documentControllerOptionsTransport.transport.generated";
import type { DocumentOptionDto } from "../documents/types/DocumentOptionDto.generated";
export const documentControllerOptionsQuery = defineQueryBinding<{ field: string; }, DocumentOptionDto[]>({
  endpointKey: "get:/api/documents/options/{field}",
  transportMetadata: documentControllerOptionsTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["Document.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
