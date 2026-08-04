import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/roleControllerGetTransport.metadata.generated.json";
import type { RoleDto } from "../roles/types/RoleDto.generated";
export const roleControllerGetTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const roleControllerGetTransport = defineEndpointTransport<{ id: string; }, RoleDto>(roleControllerGetTransportMetadata);
