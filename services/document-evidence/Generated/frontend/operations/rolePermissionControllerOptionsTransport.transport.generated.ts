import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/rolePermissionControllerOptionsTransport.metadata.generated.json";
import type { RolePermissionOptionDto } from "../rolepermissions/types/RolePermissionOptionDto.generated";
export const rolePermissionControllerOptionsTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const rolePermissionControllerOptionsTransport = defineEndpointTransport<{ field: string; }, RolePermissionOptionDto[]>(rolePermissionControllerOptionsTransportMetadata);
