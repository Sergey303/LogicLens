import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/rolePermissionControllerUpdateTransport.metadata.generated.json";
import type { RolePermissionDto } from "../rolepermissions/types/RolePermissionDto.generated";import type { UpdateRolePermissionRequest } from "../rolepermissions/types/UpdateRolePermissionRequest.generated";
export const rolePermissionControllerUpdateTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const rolePermissionControllerUpdateTransport = defineEndpointTransport<{ id: string; body: UpdateRolePermissionRequest; }, RolePermissionDto>(rolePermissionControllerUpdateTransportMetadata);
