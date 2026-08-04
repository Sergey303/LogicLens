import { defineQueryBinding } from "../runtime/queryRuntime";
import { documentRevisionControllerGetTransportMetadata } from "./documentRevisionControllerGetTransport.transport.generated";
import type { DocumentRevisionDto } from "../documentrevisions/types/DocumentRevisionDto.generated";
export const documentRevisionControllerGetQuery = defineQueryBinding<{ id: string; }, DocumentRevisionDto>({
  endpointKey: "get:/api/documentrevisions/{id}",
  transportMetadata: documentRevisionControllerGetTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["DocumentRevision.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["document.revision.not_found"],
});
