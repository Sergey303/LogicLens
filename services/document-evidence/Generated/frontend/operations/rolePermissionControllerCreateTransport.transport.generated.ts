import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/rolePermissionControllerCreateTransport.metadata.generated.json";
import type { CreateRolePermissionRequest } from "../rolepermissions/types/CreateRolePermissionRequest.generated";import type { RolePermissionDto } from "../rolepermissions/types/RolePermissionDto.generated";
export const rolePermissionControllerCreateTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const rolePermissionControllerCreateTransport = defineEndpointTransport<CreateRolePermissionRequest, RolePermissionDto>(rolePermissionControllerCreateTransportMetadata);
