import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/staffPositionRoleControllerOptionsTransport.metadata.generated.json";
import type { StaffPositionRoleOptionDto } from "../staffpositionroles/types/StaffPositionRoleOptionDto.generated";
export const staffPositionRoleControllerOptionsTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const staffPositionRoleControllerOptionsTransport = defineEndpointTransport<{ field: string; }, StaffPositionRoleOptionDto[]>(staffPositionRoleControllerOptionsTransportMetadata);
