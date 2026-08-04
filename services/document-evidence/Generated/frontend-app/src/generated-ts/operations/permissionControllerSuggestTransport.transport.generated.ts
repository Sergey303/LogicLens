import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/permissionControllerSuggestTransport.metadata.generated.json";
import type { PermissionSuggestionDto } from "../permissions/types/PermissionSuggestionDto.generated";import type { SuggestPermissionRequest } from "../permissions/types/SuggestPermissionRequest.generated";
export const permissionControllerSuggestTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const permissionControllerSuggestTransport = defineEndpointTransport<{ field: string; request: SuggestPermissionRequest; }, PermissionSuggestionDto[]>(permissionControllerSuggestTransportMetadata);
