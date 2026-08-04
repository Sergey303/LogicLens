import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/staffPositionRoleControllerGetTransport.metadata.generated.json";
import type { StaffPositionRoleDto } from "../staffpositionroles/types/StaffPositionRoleDto.generated";
export const staffPositionRoleControllerGetTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const staffPositionRoleControllerGetTransport = defineEndpointTransport<{ id: string; }, StaffPositionRoleDto>(staffPositionRoleControllerGetTransportMetadata);
