import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/rolePermissionControllerSuggestTransport.metadata.generated.json";
import type { RolePermissionSuggestionDto } from "../rolepermissions/types/RolePermissionSuggestionDto.generated";import type { SuggestRolePermissionRequest } from "../rolepermissions/types/SuggestRolePermissionRequest.generated";
export const rolePermissionControllerSuggestTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const rolePermissionControllerSuggestTransport = defineEndpointTransport<{ field: string; request: SuggestRolePermissionRequest; }, RolePermissionSuggestionDto[]>(rolePermissionControllerSuggestTransportMetadata);
