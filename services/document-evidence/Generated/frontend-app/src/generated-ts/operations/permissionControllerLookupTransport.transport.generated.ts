import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/permissionControllerLookupTransport.metadata.generated.json";
import type { LookupPermissionRequest } from "../permissions/types/LookupPermissionRequest.generated";import type { PermissionLookupDto } from "../permissions/types/PermissionLookupDto.generated";
export const permissionControllerLookupTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const permissionControllerLookupTransport = defineEndpointTransport<{ request: LookupPermissionRequest; }, PermissionLookupDto[]>(permissionControllerLookupTransportMetadata);
