import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/roleControllerOptionsTransport.metadata.generated.json";
import type { RoleOptionDto } from "../roles/types/RoleOptionDto.generated";
export const roleControllerOptionsTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const roleControllerOptionsTransport = defineEndpointTransport<{ field: string; }, RoleOptionDto[]>(roleControllerOptionsTransportMetadata);
