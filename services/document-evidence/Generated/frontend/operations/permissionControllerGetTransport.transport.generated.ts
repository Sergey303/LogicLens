import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/permissionControllerGetTransport.metadata.generated.json";
import type { PermissionDto } from "../permissions/types/PermissionDto.generated";
export const permissionControllerGetTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const permissionControllerGetTransport = defineEndpointTransport<{ id: string; }, PermissionDto>(permissionControllerGetTransportMetadata);
