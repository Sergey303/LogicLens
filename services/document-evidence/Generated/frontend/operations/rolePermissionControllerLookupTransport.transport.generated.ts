import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/rolePermissionControllerLookupTransport.metadata.generated.json";
import type { LookupRolePermissionRequest } from "../rolepermissions/types/LookupRolePermissionRequest.generated";import type { RolePermissionLookupDto } from "../rolepermissions/types/RolePermissionLookupDto.generated";
export const rolePermissionControllerLookupTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const rolePermissionControllerLookupTransport = defineEndpointTransport<{ request: LookupRolePermissionRequest; }, RolePermissionLookupDto[]>(rolePermissionControllerLookupTransportMetadata);
