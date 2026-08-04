import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/staffPositionRoleControllerCreateTransport.metadata.generated.json";
import type { CreateStaffPositionRoleRequest } from "../staffpositionroles/types/CreateStaffPositionRoleRequest.generated";import type { StaffPositionRoleDto } from "../staffpositionroles/types/StaffPositionRoleDto.generated";
export const staffPositionRoleControllerCreateTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const staffPositionRoleControllerCreateTransport = defineEndpointTransport<CreateStaffPositionRoleRequest, StaffPositionRoleDto>(staffPositionRoleControllerCreateTransportMetadata);
