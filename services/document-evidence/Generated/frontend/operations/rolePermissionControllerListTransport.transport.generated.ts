import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/rolePermissionControllerListTransport.metadata.generated.json";
import type { ListRolePermissionRequest } from "../rolepermissions/types/ListRolePermissionRequest.generated";import type { ListRolePermissionResult } from "../rolepermissions/types/ListRolePermissionResult.generated";
export const rolePermissionControllerListTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const rolePermissionControllerListTransport = defineEndpointTransport<{ request: ListRolePermissionRequest; }, ListRolePermissionResult>(rolePermissionControllerListTransportMetadata);
