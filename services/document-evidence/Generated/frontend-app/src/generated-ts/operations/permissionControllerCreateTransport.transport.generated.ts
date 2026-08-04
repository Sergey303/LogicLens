import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/permissionControllerCreateTransport.metadata.generated.json";
import type { CreatePermissionRequest } from "../permissions/types/CreatePermissionRequest.generated";import type { PermissionDto } from "../permissions/types/PermissionDto.generated";
export const permissionControllerCreateTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const permissionControllerCreateTransport = defineEndpointTransport<CreatePermissionRequest, PermissionDto>(permissionControllerCreateTransportMetadata);
