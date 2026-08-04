import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/roleControllerUpdateTransport.metadata.generated.json";
import type { RoleDto } from "../roles/types/RoleDto.generated";import type { UpdateRoleRequest } from "../roles/types/UpdateRoleRequest.generated";
export const roleControllerUpdateTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const roleControllerUpdateTransport = defineEndpointTransport<{ id: string; body: UpdateRoleRequest; }, RoleDto>(roleControllerUpdateTransportMetadata);
