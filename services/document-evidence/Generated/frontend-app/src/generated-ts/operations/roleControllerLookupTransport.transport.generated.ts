import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/roleControllerLookupTransport.metadata.generated.json";
import type { LookupRoleRequest } from "../roles/types/LookupRoleRequest.generated";import type { RoleLookupDto } from "../roles/types/RoleLookupDto.generated";
export const roleControllerLookupTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const roleControllerLookupTransport = defineEndpointTransport<{ request: LookupRoleRequest; }, RoleLookupDto[]>(roleControllerLookupTransportMetadata);
