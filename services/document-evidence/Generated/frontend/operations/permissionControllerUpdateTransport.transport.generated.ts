import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/permissionControllerUpdateTransport.metadata.generated.json";
import type { PermissionDto } from "../permissions/types/PermissionDto.generated";import type { UpdatePermissionRequest } from "../permissions/types/UpdatePermissionRequest.generated";
export const permissionControllerUpdateTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const permissionControllerUpdateTransport = defineEndpointTransport<{ id: string; body: UpdatePermissionRequest; }, PermissionDto>(permissionControllerUpdateTransportMetadata);
