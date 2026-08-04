import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/roleControllerListTransport.metadata.generated.json";
import type { ListRoleRequest } from "../roles/types/ListRoleRequest.generated";import type { ListRoleResult } from "../roles/types/ListRoleResult.generated";
export const roleControllerListTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const roleControllerListTransport = defineEndpointTransport<{ request: ListRoleRequest; }, ListRoleResult>(roleControllerListTransportMetadata);
