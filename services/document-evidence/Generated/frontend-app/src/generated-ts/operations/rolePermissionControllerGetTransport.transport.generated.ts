import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/rolePermissionControllerGetTransport.metadata.generated.json";
import type { RolePermissionDto } from "../rolepermissions/types/RolePermissionDto.generated";
export const rolePermissionControllerGetTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const rolePermissionControllerGetTransport = defineEndpointTransport<{ id: string; }, RolePermissionDto>(rolePermissionControllerGetTransportMetadata);
