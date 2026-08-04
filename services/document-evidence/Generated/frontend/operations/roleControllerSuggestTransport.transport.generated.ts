import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/roleControllerSuggestTransport.metadata.generated.json";
import type { RoleSuggestionDto } from "../roles/types/RoleSuggestionDto.generated";import type { SuggestRoleRequest } from "../roles/types/SuggestRoleRequest.generated";
export const roleControllerSuggestTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const roleControllerSuggestTransport = defineEndpointTransport<{ field: string; request: SuggestRoleRequest; }, RoleSuggestionDto[]>(roleControllerSuggestTransportMetadata);
