import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/roleControllerCreateTransport.metadata.generated.json";
import type { CreateRoleRequest } from "../roles/types/CreateRoleRequest.generated";import type { RoleDto } from "../roles/types/RoleDto.generated";
export const roleControllerCreateTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const roleControllerCreateTransport = defineEndpointTransport<CreateRoleRequest, RoleDto>(roleControllerCreateTransportMetadata);
