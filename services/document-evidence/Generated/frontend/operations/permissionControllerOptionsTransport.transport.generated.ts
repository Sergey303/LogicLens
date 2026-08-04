import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/permissionControllerOptionsTransport.metadata.generated.json";
import type { PermissionOptionDto } from "../permissions/types/PermissionOptionDto.generated";
export const permissionControllerOptionsTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const permissionControllerOptionsTransport = defineEndpointTransport<{ field: string; }, PermissionOptionDto[]>(permissionControllerOptionsTransportMetadata);
