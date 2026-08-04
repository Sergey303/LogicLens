import { defineQueryBinding } from "../runtime/queryRuntime";
import { documentControllerGetTransportMetadata } from "./documentControllerGetTransport.transport.generated";
import type { DocumentDto } from "../documents/types/DocumentDto.generated";
export const documentControllerGetQuery = defineQueryBinding<{ id: string; }, DocumentDto>({
  endpointKey: "get:/api/documents/{id}",
  transportMetadata: documentControllerGetTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["Document.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["document.not_found"],
});
