import { defineQueryBinding } from "../runtime/queryRuntime";
import { documentRevisionControllerOptionsTransportMetadata } from "./documentRevisionControllerOptionsTransport.transport.generated";
import type { DocumentRevisionOptionDto } from "../documentrevisions/types/DocumentRevisionOptionDto.generated";
export const documentRevisionControllerOptionsQuery = defineQueryBinding<{ field: string; }, DocumentRevisionOptionDto[]>({
  endpointKey: "get:/api/documentrevisions/options/{field}",
  transportMetadata: documentRevisionControllerOptionsTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["DocumentRevision.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
