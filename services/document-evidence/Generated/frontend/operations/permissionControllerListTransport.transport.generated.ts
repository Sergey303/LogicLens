import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/permissionControllerListTransport.metadata.generated.json";
import type { ListPermissionRequest } from "../permissions/types/ListPermissionRequest.generated";import type { ListPermissionResult } from "../permissions/types/ListPermissionResult.generated";
export const permissionControllerListTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const permissionControllerListTransport = defineEndpointTransport<{ request: ListPermissionRequest; }, ListPermissionResult>(permissionControllerListTransportMetadata);
